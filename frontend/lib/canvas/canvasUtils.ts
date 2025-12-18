/**
 * Canvas Utility Functions
 * TAG-FE-004: Canvas State Persistence
 */

import type {
  CanvasState,
  TextLayer,
  ExportOptions,
  ExportFormat,
  ImageExportOptions,
  ImageExportFormat,
  PlatformExportPreset,
  ExportedImage,
  BatchExportProgress,
} from "@/types/canvas";
import JSZip from "jszip";
import { saveAs } from "file-saver";

/**
 * Generate a unique layer ID
 */
export function generateLayerId(): string {
  return `layer_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
}

/**
 * Generate a layer name based on existing layers
 */
export function generateLayerName(existingLayers: TextLayer[]): string {
  const textLayerCount = existingLayers.filter((l) =>
    l.name.startsWith("텍스트")
  ).length;
  return `텍스트 ${textLayerCount + 1}`;
}

/**
 * Serialize canvas state to JSON string
 */
export function serializeCanvasState(state: CanvasState): string {
  return JSON.stringify(state, null, 2);
}

/**
 * Parse JSON string to canvas state
 */
export function parseCanvasState(json: string): CanvasState | null {
  try {
    const parsed = JSON.parse(json);
    // Validate required fields
    if (
      parsed.version &&
      typeof parsed.width === "number" &&
      typeof parsed.height === "number" &&
      Array.isArray(parsed.layers)
    ) {
      return parsed as CanvasState;
    }
    return null;
  } catch (error) {
    console.error("Failed to parse canvas state:", error);
    return null;
  }
}

/**
 * Save canvas state to local storage
 */
export function saveCanvasToLocalStorage(
  key: string,
  state: CanvasState
): boolean {
  try {
    const serialized = serializeCanvasState(state);
    localStorage.setItem(key, serialized);
    return true;
  } catch (error) {
    console.error("Failed to save canvas to local storage:", error);
    return false;
  }
}

/**
 * Load canvas state from local storage
 */
export function loadCanvasFromLocalStorage(key: string): CanvasState | null {
  try {
    const serialized = localStorage.getItem(key);
    if (!serialized) return null;
    return parseCanvasState(serialized);
  } catch (error) {
    console.error("Failed to load canvas from local storage:", error);
    return null;
  }
}

/**
 * Download canvas state as JSON file
 */
export function downloadCanvasAsJson(
  state: CanvasState,
  filename: string = "canvas"
): void {
  const json = serializeCanvasState(state);
  const blob = new Blob([json], { type: "application/json" });
  const url = URL.createObjectURL(blob);

  const link = document.createElement("a");
  link.href = url;
  link.download = `${filename}.json`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

/**
 * Export canvas as image data URL
 */
export function exportCanvasToDataUrl(
  canvasElement: HTMLCanvasElement,
  options: ExportOptions
): string {
  const { format, quality = 0.92, multiplier = 1 } = options;

  if (multiplier !== 1) {
    // Create a temporary canvas for high-res export
    const tempCanvas = document.createElement("canvas");
    tempCanvas.width = canvasElement.width * multiplier;
    tempCanvas.height = canvasElement.height * multiplier;
    const ctx = tempCanvas.getContext("2d");

    if (ctx) {
      ctx.scale(multiplier, multiplier);
      ctx.drawImage(canvasElement, 0, 0);
      return tempCanvas.toDataURL(
        `image/${format}`,
        format === "jpeg" ? quality : undefined
      );
    }
  }

  return canvasElement.toDataURL(
    `image/${format}`,
    format === "jpeg" ? quality : undefined
  );
}

/**
 * Download canvas as image file
 */
export function downloadCanvasAsImage(
  dataUrl: string,
  filename: string,
  format: ExportFormat
): void {
  const link = document.createElement("a");
  link.href = dataUrl;
  link.download = `${filename}.${format}`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

/**
 * Load an image file and return as data URL
 */
export function loadImageFile(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    if (!file.type.startsWith("image/")) {
      reject(new Error("Invalid file type. Please select an image file."));
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      const result = e.target?.result;
      if (typeof result === "string") {
        resolve(result);
      } else {
        reject(new Error("Failed to read file"));
      }
    };
    reader.onerror = () => reject(new Error("Failed to read file"));
    reader.readAsDataURL(file);
  });
}

/**
 * Clamp a value between min and max
 */
export function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}

/**
 * Convert hex color to RGBA
 */
export function hexToRgba(hex: string, alpha: number = 1): string {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  if (!result) return hex;

  const r = parseInt(result[1], 16);
  const g = parseInt(result[2], 16);
  const b = parseInt(result[3], 16);

  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

/**
 * Check if a color string is transparent
 */
export function isTransparent(color: string): boolean {
  return (
    !color ||
    color === "transparent" ||
    color === "rgba(0,0,0,0)" ||
    color === "rgba(0, 0, 0, 0)"
  );
}

/**
 * Create initial canvas state
 */
export function createInitialCanvasState(
  width: number,
  height: number,
  backgroundColor: string = "#1a1f2e"
): CanvasState {
  return {
    version: "1.0.0",
    width,
    height,
    backgroundColor,
    backgroundImage: null,
    layers: [],
    objects: [],
  };
}
