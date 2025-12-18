/**
 * Platform Export Presets Utility Functions
 * TAG-EX-001: Platform-Specific Dimension Presets
 * TAG-EX-002: Image Export with Quality Options
 * TAG-EX-003: Batch Export with ZIP Download
 *
 * Provides utilities for exporting canvas to multiple platform dimensions
 * with quality options and batch ZIP download functionality.
 */

import type {
  PlatformConfig,
  PlatformCategory,
  PlatformExportPreset,
  ImageExportOptions,
  ExportedImage,
  BatchExportProgress,
  BatchExportItem,
} from "@/types/canvas";
import { PLATFORM_EXPORT_PRESETS, DEFAULT_IMAGE_EXPORT_OPTIONS } from "@/types/canvas";
import JSZip from "jszip";
import { saveAs } from "file-saver";

/**
 * Get all presets for a specific platform
 */
export function getPresetsForPlatform(platformId: PlatformCategory): PlatformExportPreset[] {
  const platform = PLATFORM_EXPORT_PRESETS.find((p) => p.id === platformId);
  return platform?.presets || [];
}

/**
 * Get a single platform configuration by ID
 */
export function getPlatformConfig(platformId: PlatformCategory): PlatformConfig | undefined {
  return PLATFORM_EXPORT_PRESETS.find((p) => p.id === platformId);
}

/**
 * Get all preset IDs across all platforms
 */
export function getAllPresetIds(): string[] {
  return PLATFORM_EXPORT_PRESETS.flatMap((platform) =>
    platform.presets.map((preset) => preset.id)
  );
}

/**
 * Get a preset by its ID
 */
export function getPresetById(presetId: string): PlatformExportPreset | undefined {
  for (const platform of PLATFORM_EXPORT_PRESETS) {
    const preset = platform.presets.find((p) => p.id === presetId);
    if (preset) return preset;
  }
  return undefined;
}

/**
 * Get the file extension for the export format
 */
export function getFileExtension(format: ImageExportOptions["format"]): string {
  switch (format) {
    case "jpeg":
      return "jpg";
    case "webp":
      return "webp";
    case "png":
    default:
      return "png";
  }
}

/**
 * Get MIME type for the export format
 */
export function getMimeType(format: ImageExportOptions["format"]): string {
  switch (format) {
    case "jpeg":
      return "image/jpeg";
    case "webp":
      return "image/webp";
    case "png":
    default:
      return "image/png";
  }
}

/**
 * Generate a descriptive filename for the exported image
 */
export function generateExportFilename(
  preset: PlatformExportPreset,
  options: ImageExportOptions,
  baseFilename: string = "export"
): string {
  const extension = getFileExtension(options.format);
  const multiplierSuffix = options.multiplier > 1 ? `@${options.multiplier}x` : "";
  const sanitizedBasename = baseFilename.replace(/[^a-zA-Z0-9-_]/g, "_");

  return `${sanitizedBasename}_${preset.platform}_${preset.name.toLowerCase().replace(/\s+/g, "-")}${multiplierSuffix}.${extension}`;
}

/**
 * Calculate the actual export dimensions based on preset and multiplier
 */
export function calculateExportDimensions(
  preset: PlatformExportPreset,
  multiplier: 1 | 2 | 3 = 1
): { width: number; height: number } {
  return {
    width: preset.width * multiplier,
    height: preset.height * multiplier,
  };
}

/**
 * Estimate file size for an export (rough approximation)
 * Returns size in bytes
 */
export function estimateFileSize(
  preset: PlatformExportPreset,
  options: ImageExportOptions
): number {
  const { width, height } = calculateExportDimensions(preset, options.multiplier);
  const pixelCount = width * height;

  // Rough estimates based on format and quality
  let bytesPerPixel: number;

  switch (options.format) {
    case "png":
      // PNG typically 2-4 bytes per pixel after compression
      bytesPerPixel = options.transparentBackground ? 3.5 : 2.5;
      break;
    case "jpeg":
      // JPEG varies greatly with quality
      bytesPerPixel = 0.1 + (options.quality / 100) * 0.8;
      break;
    case "webp":
      // WebP is typically more efficient than JPEG
      bytesPerPixel = 0.08 + (options.quality / 100) * 0.6;
      break;
    default:
      bytesPerPixel = 2;
  }

  return Math.round(pixelCount * bytesPerPixel);
}

/**
 * Format file size in human-readable format
 */
export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

/**
 * Estimate total batch export size
 */
export function estimateBatchExportSize(
  presets: PlatformExportPreset[],
  options: ImageExportOptions
): string {
  const totalBytes = presets.reduce(
    (sum, preset) => sum + estimateFileSize(preset, options),
    0
  );
  return formatFileSize(totalBytes);
}

/**
 * Initialize batch export items from all presets (all unselected by default)
 */
export function initializeBatchExportItems(): BatchExportItem[] {
  return PLATFORM_EXPORT_PRESETS.flatMap((platform) =>
    platform.presets.map((preset) => ({
      preset,
      selected: false,
    }))
  );
}

/**
 * Get selected presets from batch export items
 */
export function getSelectedPresets(items: BatchExportItem[]): PlatformExportPreset[] {
  return items.filter((item) => item.selected).map((item) => item.preset);
}

/**
 * Toggle preset selection in batch export items
 */
export function togglePresetSelection(
  items: BatchExportItem[],
  presetId: string
): BatchExportItem[] {
  return items.map((item) =>
    item.preset.id === presetId ? { ...item, selected: !item.selected } : item
  );
}

/**
 * Select all presets for a specific platform
 */
export function selectAllForPlatform(
  items: BatchExportItem[],
  platformId: PlatformCategory
): BatchExportItem[] {
  return items.map((item) =>
    item.preset.platform === platformId ? { ...item, selected: true } : item
  );
}

/**
 * Deselect all presets for a specific platform
 */
export function deselectAllForPlatform(
  items: BatchExportItem[],
  platformId: PlatformCategory
): BatchExportItem[] {
  return items.map((item) =>
    item.preset.platform === platformId ? { ...item, selected: false } : item
  );
}

/**
 * Count selected presets for a platform
 */
export function countSelectedForPlatform(
  items: BatchExportItem[],
  platformId: PlatformCategory
): number {
  return items.filter(
    (item) => item.preset.platform === platformId && item.selected
  ).length;
}

/**
 * Check if all presets for a platform are selected
 */
export function isAllSelectedForPlatform(
  items: BatchExportItem[],
  platformId: PlatformCategory
): boolean {
  const platformItems = items.filter((item) => item.preset.platform === platformId);
  return platformItems.length > 0 && platformItems.every((item) => item.selected);
}

/**
 * Convert data URL to Blob
 */
export async function dataUrlToBlob(dataUrl: string): Promise<Blob> {
  const response = await fetch(dataUrl);
  return response.blob();
}

/**
 * Export a single image from canvas with specified preset
 * This function should be called with a canvas export function
 */
export async function exportSingleImage(
  canvasExportFn: (
    width: number,
    height: number,
    options: ImageExportOptions
  ) => string,
  preset: PlatformExportPreset,
  options: ImageExportOptions,
  baseFilename: string = "export"
): Promise<ExportedImage> {
  const { width, height } = calculateExportDimensions(preset, options.multiplier);
  const dataUrl = canvasExportFn(width, height, options);
  const blob = await dataUrlToBlob(dataUrl);
  const filename = generateExportFilename(preset, options, baseFilename);

  return {
    filename,
    blob,
    preset,
  };
}

/**
 * Create and download a ZIP file containing all exported images
 */
export async function createAndDownloadZip(
  images: ExportedImage[],
  zipFilename: string = "canvas-exports"
): Promise<void> {
  const zip = new JSZip();

  // Organize images by platform folder
  images.forEach((image) => {
    const folderName = image.preset.platform;
    zip.file(`${folderName}/${image.filename}`, image.blob);
  });

  // Generate the zip file
  const content = await zip.generateAsync({
    type: "blob",
    compression: "DEFLATE",
    compressionOptions: { level: 6 },
  });

  // Download the zip file
  saveAs(content, `${zipFilename}.zip`);
}

/**
 * Perform batch export of canvas to multiple platform sizes
 * This is the main export function that orchestrates the entire process
 */
export async function performBatchExport(
  canvasExportFn: (
    width: number,
    height: number,
    options: ImageExportOptions
  ) => string,
  presets: PlatformExportPreset[],
  options: ImageExportOptions,
  onProgress?: (progress: BatchExportProgress) => void,
  baseFilename: string = "canvas"
): Promise<void> {
  if (presets.length === 0) {
    throw new Error("No presets selected for export");
  }

  const totalPresets = presets.length;
  const exportedImages: ExportedImage[] = [];

  // Report initial progress
  onProgress?.({
    current: 0,
    total: totalPresets,
    currentPreset: presets[0].name,
    status: "exporting",
  });

  // Export each preset
  for (let i = 0; i < presets.length; i++) {
    const preset = presets[i];

    // Update progress
    onProgress?.({
      current: i,
      total: totalPresets,
      currentPreset: preset.name,
      status: "exporting",
    });

    try {
      const exportedImage = await exportSingleImage(
        canvasExportFn,
        preset,
        options,
        baseFilename
      );
      exportedImages.push(exportedImage);
    } catch (error) {
      console.error(`Failed to export preset ${preset.name}:`, error);
      onProgress?.({
        current: i,
        total: totalPresets,
        currentPreset: preset.name,
        status: "error",
        error: `Failed to export ${preset.name}`,
      });
      throw error;
    }
  }

  // Update progress for zipping
  onProgress?.({
    current: totalPresets,
    total: totalPresets,
    currentPreset: "Creating ZIP file",
    status: "zipping",
  });

  // Create and download the ZIP file
  const timestamp = new Date().toISOString().replace(/[:.]/g, "-").slice(0, 19);
  await createAndDownloadZip(exportedImages, `${baseFilename}-${timestamp}`);

  // Report completion
  onProgress?.({
    current: totalPresets,
    total: totalPresets,
    currentPreset: "",
    status: "complete",
  });
}

/**
 * Validate export options
 */
export function validateExportOptions(options: Partial<ImageExportOptions>): ImageExportOptions {
  return {
    format: options.format || DEFAULT_IMAGE_EXPORT_OPTIONS.format,
    quality: Math.max(1, Math.min(100, options.quality ?? DEFAULT_IMAGE_EXPORT_OPTIONS.quality)),
    multiplier: ([1, 2, 3] as const).includes(options.multiplier as 1 | 2 | 3)
      ? (options.multiplier as 1 | 2 | 3)
      : DEFAULT_IMAGE_EXPORT_OPTIONS.multiplier,
    transparentBackground:
      options.transparentBackground ?? DEFAULT_IMAGE_EXPORT_OPTIONS.transparentBackground,
  };
}

/**
 * Get platform brand color
 */
export function getPlatformBrandColor(platformId: PlatformCategory): string {
  const platform = getPlatformConfig(platformId);
  return platform?.brandColor || "#666666";
}

/**
 * Get total preset count across all platforms
 */
export function getTotalPresetCount(): number {
  return PLATFORM_EXPORT_PRESETS.reduce(
    (sum, platform) => sum + platform.presets.length,
    0
  );
}

/**
 * Check if format supports transparency
 */
export function supportsTransparency(format: ImageExportOptions["format"]): boolean {
  return format === "png" || format === "webp";
}

/**
 * Check if format supports quality setting
 */
export function supportsQualitySetting(format: ImageExportOptions["format"]): boolean {
  return format === "jpeg" || format === "webp";
}
