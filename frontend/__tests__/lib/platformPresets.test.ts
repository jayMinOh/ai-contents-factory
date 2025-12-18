/**
 * Platform Presets Utility Tests
 * TAG-EX-001/002/003: Platform Export Tests
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import {
  getPresetsForPlatform,
  getPlatformConfig,
  getAllPresetIds,
  getPresetById,
  getFileExtension,
  getMimeType,
  generateExportFilename,
  calculateExportDimensions,
  estimateFileSize,
  formatFileSize,
  estimateBatchExportSize,
  initializeBatchExportItems,
  getSelectedPresets,
  togglePresetSelection,
  selectAllForPlatform,
  deselectAllForPlatform,
  countSelectedForPlatform,
  isAllSelectedForPlatform,
  validateExportOptions,
  getPlatformBrandColor,
  getTotalPresetCount,
  supportsTransparency,
  supportsQualitySetting,
} from "@/lib/canvas/platformPresets";
import type {
  PlatformExportPreset,
  ImageExportOptions,
  BatchExportItem,
} from "@/types/canvas";
import { PLATFORM_EXPORT_PRESETS, DEFAULT_IMAGE_EXPORT_OPTIONS } from "@/types/canvas";

describe("platformPresets utilities", () => {
  describe("getPresetsForPlatform", () => {
    it("should return presets for Instagram platform", () => {
      const presets = getPresetsForPlatform("instagram");
      expect(presets.length).toBe(4);
      expect(presets[0].platform).toBe("instagram");
    });

    it("should return presets for Facebook platform", () => {
      const presets = getPresetsForPlatform("facebook");
      expect(presets.length).toBe(3);
      expect(presets.every((p) => p.platform === "facebook")).toBe(true);
    });

    it("should return empty array for invalid platform", () => {
      const presets = getPresetsForPlatform("invalid" as any);
      expect(presets).toEqual([]);
    });
  });

  describe("getPlatformConfig", () => {
    it("should return platform config for valid platform ID", () => {
      const config = getPlatformConfig("instagram");
      expect(config).toBeDefined();
      expect(config?.name).toBe("Instagram");
      expect(config?.brandColor).toBe("#E4405F");
    });

    it("should return undefined for invalid platform ID", () => {
      const config = getPlatformConfig("invalid" as any);
      expect(config).toBeUndefined();
    });
  });

  describe("getAllPresetIds", () => {
    it("should return all preset IDs across all platforms", () => {
      const ids = getAllPresetIds();
      expect(ids.length).toBeGreaterThan(0);
      expect(ids).toContain("ig-feed");
      expect(ids).toContain("fb-link");
      expect(ids).toContain("yt-thumbnail");
    });
  });

  describe("getPresetById", () => {
    it("should return preset for valid ID", () => {
      const preset = getPresetById("ig-feed");
      expect(preset).toBeDefined();
      expect(preset?.name).toBe("Feed");
      expect(preset?.width).toBe(1080);
      expect(preset?.height).toBe(1080);
    });

    it("should return undefined for invalid ID", () => {
      const preset = getPresetById("invalid-id");
      expect(preset).toBeUndefined();
    });
  });

  describe("getFileExtension", () => {
    it("should return correct extension for png", () => {
      expect(getFileExtension("png")).toBe("png");
    });

    it("should return jpg for jpeg format", () => {
      expect(getFileExtension("jpeg")).toBe("jpg");
    });

    it("should return webp for webp format", () => {
      expect(getFileExtension("webp")).toBe("webp");
    });
  });

  describe("getMimeType", () => {
    it("should return correct MIME type for png", () => {
      expect(getMimeType("png")).toBe("image/png");
    });

    it("should return correct MIME type for jpeg", () => {
      expect(getMimeType("jpeg")).toBe("image/jpeg");
    });

    it("should return correct MIME type for webp", () => {
      expect(getMimeType("webp")).toBe("image/webp");
    });
  });

  describe("generateExportFilename", () => {
    const mockPreset: PlatformExportPreset = {
      id: "ig-feed",
      platform: "instagram",
      name: "Feed",
      description: "Test",
      width: 1080,
      height: 1080,
      aspectRatio: "1:1",
      icon: "square",
    };

    it("should generate filename with correct format", () => {
      const options: ImageExportOptions = {
        format: "png",
        quality: 92,
        multiplier: 1,
        transparentBackground: false,
      };
      const filename = generateExportFilename(mockPreset, options, "test");
      expect(filename).toBe("test_instagram_feed.png");
    });

    it("should include multiplier suffix for retina exports", () => {
      const options: ImageExportOptions = {
        format: "jpeg",
        quality: 92,
        multiplier: 2,
        transparentBackground: false,
      };
      const filename = generateExportFilename(mockPreset, options, "export");
      expect(filename).toBe("export_instagram_feed@2x.jpg");
    });

    it("should sanitize base filename", () => {
      const options: ImageExportOptions = {
        format: "png",
        quality: 92,
        multiplier: 1,
        transparentBackground: false,
      };
      const filename = generateExportFilename(mockPreset, options, "test file@special!");
      expect(filename).toBe("test_file_special__instagram_feed.png");
    });
  });

  describe("calculateExportDimensions", () => {
    const mockPreset: PlatformExportPreset = {
      id: "ig-feed",
      platform: "instagram",
      name: "Feed",
      description: "Test",
      width: 1080,
      height: 1080,
      aspectRatio: "1:1",
      icon: "square",
    };

    it("should return original dimensions for 1x multiplier", () => {
      const dims = calculateExportDimensions(mockPreset, 1);
      expect(dims.width).toBe(1080);
      expect(dims.height).toBe(1080);
    });

    it("should double dimensions for 2x multiplier", () => {
      const dims = calculateExportDimensions(mockPreset, 2);
      expect(dims.width).toBe(2160);
      expect(dims.height).toBe(2160);
    });

    it("should triple dimensions for 3x multiplier", () => {
      const dims = calculateExportDimensions(mockPreset, 3);
      expect(dims.width).toBe(3240);
      expect(dims.height).toBe(3240);
    });
  });

  describe("estimateFileSize", () => {
    const mockPreset: PlatformExportPreset = {
      id: "ig-feed",
      platform: "instagram",
      name: "Feed",
      description: "Test",
      width: 100,
      height: 100,
      aspectRatio: "1:1",
      icon: "square",
    };

    it("should estimate larger size for PNG than JPEG", () => {
      const pngOptions: ImageExportOptions = {
        format: "png",
        quality: 92,
        multiplier: 1,
        transparentBackground: false,
      };
      const jpegOptions: ImageExportOptions = {
        format: "jpeg",
        quality: 92,
        multiplier: 1,
        transparentBackground: false,
      };

      const pngSize = estimateFileSize(mockPreset, pngOptions);
      const jpegSize = estimateFileSize(mockPreset, jpegOptions);

      expect(pngSize).toBeGreaterThan(jpegSize);
    });

    it("should estimate larger size for higher quality", () => {
      const lowQuality: ImageExportOptions = {
        format: "jpeg",
        quality: 20,
        multiplier: 1,
        transparentBackground: false,
      };
      const highQuality: ImageExportOptions = {
        format: "jpeg",
        quality: 100,
        multiplier: 1,
        transparentBackground: false,
      };

      const lowSize = estimateFileSize(mockPreset, lowQuality);
      const highSize = estimateFileSize(mockPreset, highQuality);

      expect(highSize).toBeGreaterThan(lowSize);
    });

    it("should estimate larger size for higher multiplier", () => {
      const options1x: ImageExportOptions = {
        format: "png",
        quality: 92,
        multiplier: 1,
        transparentBackground: false,
      };
      const options2x: ImageExportOptions = {
        format: "png",
        quality: 92,
        multiplier: 2,
        transparentBackground: false,
      };

      const size1x = estimateFileSize(mockPreset, options1x);
      const size2x = estimateFileSize(mockPreset, options2x);

      expect(size2x).toBeGreaterThan(size1x);
    });
  });

  describe("formatFileSize", () => {
    it("should format bytes", () => {
      expect(formatFileSize(500)).toBe("500 B");
    });

    it("should format kilobytes", () => {
      expect(formatFileSize(1024)).toBe("1 KB");
      expect(formatFileSize(2048)).toBe("2 KB");
    });

    it("should format megabytes", () => {
      expect(formatFileSize(1048576)).toBe("1.0 MB");
      expect(formatFileSize(2097152)).toBe("2.0 MB");
    });
  });

  describe("initializeBatchExportItems", () => {
    it("should create items for all presets", () => {
      const items = initializeBatchExportItems();
      const totalPresets = PLATFORM_EXPORT_PRESETS.reduce(
        (sum, p) => sum + p.presets.length,
        0
      );
      expect(items.length).toBe(totalPresets);
    });

    it("should initialize all items as unselected", () => {
      const items = initializeBatchExportItems();
      expect(items.every((item) => item.selected === false)).toBe(true);
    });
  });

  describe("getSelectedPresets", () => {
    it("should return only selected presets", () => {
      const items: BatchExportItem[] = [
        {
          preset: { id: "1", platform: "instagram" } as PlatformExportPreset,
          selected: true,
        },
        {
          preset: { id: "2", platform: "facebook" } as PlatformExportPreset,
          selected: false,
        },
        {
          preset: { id: "3", platform: "twitter" } as PlatformExportPreset,
          selected: true,
        },
      ];

      const selected = getSelectedPresets(items);
      expect(selected.length).toBe(2);
      expect(selected.map((p) => p.id)).toEqual(["1", "3"]);
    });

    it("should return empty array if none selected", () => {
      const items: BatchExportItem[] = [
        {
          preset: { id: "1", platform: "instagram" } as PlatformExportPreset,
          selected: false,
        },
      ];

      const selected = getSelectedPresets(items);
      expect(selected).toEqual([]);
    });
  });

  describe("togglePresetSelection", () => {
    it("should toggle preset selection state", () => {
      const items: BatchExportItem[] = [
        {
          preset: { id: "1", platform: "instagram" } as PlatformExportPreset,
          selected: false,
        },
        {
          preset: { id: "2", platform: "facebook" } as PlatformExportPreset,
          selected: true,
        },
      ];

      const toggled = togglePresetSelection(items, "1");
      expect(toggled[0].selected).toBe(true);
      expect(toggled[1].selected).toBe(true);

      const toggledAgain = togglePresetSelection(toggled, "1");
      expect(toggledAgain[0].selected).toBe(false);
    });
  });

  describe("selectAllForPlatform", () => {
    it("should select all presets for a platform", () => {
      const items: BatchExportItem[] = [
        {
          preset: { id: "1", platform: "instagram" } as PlatformExportPreset,
          selected: false,
        },
        {
          preset: { id: "2", platform: "instagram" } as PlatformExportPreset,
          selected: false,
        },
        {
          preset: { id: "3", platform: "facebook" } as PlatformExportPreset,
          selected: false,
        },
      ];

      const updated = selectAllForPlatform(items, "instagram");
      expect(updated[0].selected).toBe(true);
      expect(updated[1].selected).toBe(true);
      expect(updated[2].selected).toBe(false);
    });
  });

  describe("deselectAllForPlatform", () => {
    it("should deselect all presets for a platform", () => {
      const items: BatchExportItem[] = [
        {
          preset: { id: "1", platform: "instagram" } as PlatformExportPreset,
          selected: true,
        },
        {
          preset: { id: "2", platform: "instagram" } as PlatformExportPreset,
          selected: true,
        },
        {
          preset: { id: "3", platform: "facebook" } as PlatformExportPreset,
          selected: true,
        },
      ];

      const updated = deselectAllForPlatform(items, "instagram");
      expect(updated[0].selected).toBe(false);
      expect(updated[1].selected).toBe(false);
      expect(updated[2].selected).toBe(true);
    });
  });

  describe("countSelectedForPlatform", () => {
    it("should count selected presets for a platform", () => {
      const items: BatchExportItem[] = [
        {
          preset: { id: "1", platform: "instagram" } as PlatformExportPreset,
          selected: true,
        },
        {
          preset: { id: "2", platform: "instagram" } as PlatformExportPreset,
          selected: false,
        },
        {
          preset: { id: "3", platform: "facebook" } as PlatformExportPreset,
          selected: true,
        },
      ];

      expect(countSelectedForPlatform(items, "instagram")).toBe(1);
      expect(countSelectedForPlatform(items, "facebook")).toBe(1);
    });
  });

  describe("isAllSelectedForPlatform", () => {
    it("should return true when all presets for platform are selected", () => {
      const items: BatchExportItem[] = [
        {
          preset: { id: "1", platform: "instagram" } as PlatformExportPreset,
          selected: true,
        },
        {
          preset: { id: "2", platform: "instagram" } as PlatformExportPreset,
          selected: true,
        },
        {
          preset: { id: "3", platform: "facebook" } as PlatformExportPreset,
          selected: false,
        },
      ];

      expect(isAllSelectedForPlatform(items, "instagram")).toBe(true);
      expect(isAllSelectedForPlatform(items, "facebook")).toBe(false);
    });
  });

  describe("validateExportOptions", () => {
    it("should use default values for missing options", () => {
      const validated = validateExportOptions({});
      expect(validated.format).toBe(DEFAULT_IMAGE_EXPORT_OPTIONS.format);
      expect(validated.quality).toBe(DEFAULT_IMAGE_EXPORT_OPTIONS.quality);
      expect(validated.multiplier).toBe(DEFAULT_IMAGE_EXPORT_OPTIONS.multiplier);
    });

    it("should clamp quality to valid range", () => {
      expect(validateExportOptions({ quality: 0 }).quality).toBe(1);
      expect(validateExportOptions({ quality: 150 }).quality).toBe(100);
      expect(validateExportOptions({ quality: 50 }).quality).toBe(50);
    });

    it("should validate multiplier values", () => {
      expect(validateExportOptions({ multiplier: 1 }).multiplier).toBe(1);
      expect(validateExportOptions({ multiplier: 2 }).multiplier).toBe(2);
      expect(validateExportOptions({ multiplier: 3 }).multiplier).toBe(3);
      expect(validateExportOptions({ multiplier: 5 as any }).multiplier).toBe(
        DEFAULT_IMAGE_EXPORT_OPTIONS.multiplier
      );
    });
  });

  describe("getPlatformBrandColor", () => {
    it("should return correct brand color for Instagram", () => {
      expect(getPlatformBrandColor("instagram")).toBe("#E4405F");
    });

    it("should return correct brand color for Facebook", () => {
      expect(getPlatformBrandColor("facebook")).toBe("#1877F2");
    });

    it("should return default color for invalid platform", () => {
      expect(getPlatformBrandColor("invalid" as any)).toBe("#666666");
    });
  });

  describe("getTotalPresetCount", () => {
    it("should return total number of presets across all platforms", () => {
      const count = getTotalPresetCount();
      expect(count).toBeGreaterThan(0);
      // Instagram(4) + Facebook(3) + Pinterest(2) + Twitter(2) + YouTube(1) + LinkedIn(2) = 14
      expect(count).toBe(14);
    });
  });

  describe("supportsTransparency", () => {
    it("should return true for PNG", () => {
      expect(supportsTransparency("png")).toBe(true);
    });

    it("should return true for WebP", () => {
      expect(supportsTransparency("webp")).toBe(true);
    });

    it("should return false for JPEG", () => {
      expect(supportsTransparency("jpeg")).toBe(false);
    });
  });

  describe("supportsQualitySetting", () => {
    it("should return true for JPEG", () => {
      expect(supportsQualitySetting("jpeg")).toBe(true);
    });

    it("should return true for WebP", () => {
      expect(supportsQualitySetting("webp")).toBe(true);
    });

    it("should return false for PNG", () => {
      expect(supportsQualitySetting("png")).toBe(false);
    });
  });
});
