"use client";

/**
 * PlatformPresets Component
 * TAG-EX-001: Platform-Specific Dimension Presets
 *
 * Provides visual selection UI for social media platform export presets.
 * Supports Instagram, Facebook, Pinterest, Twitter/X, YouTube, and LinkedIn.
 */

import React, { useState, useCallback, useMemo } from "react";
import {
  Square,
  RectangleVertical,
  RectangleHorizontal,
  Smartphone,
  Link,
  Share2,
  Bookmark,
  FileText,
  Play,
  Image as ImageIcon,
  Check,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import type {
  PlatformConfig,
  PlatformExportPreset,
  PlatformCategory,
  BatchExportItem,
} from "@/types/canvas";
import { PLATFORM_EXPORT_PRESETS } from "@/types/canvas";

interface PlatformPresetsProps {
  selectedPresets: BatchExportItem[];
  onPresetToggle: (preset: PlatformExportPreset) => void;
  onSelectAll: (platform: PlatformCategory) => void;
  onDeselectAll: (platform: PlatformCategory) => void;
  className?: string;
}

// Icon mapping for preset icons
const getPresetIcon = (iconName: string): React.ReactNode => {
  const iconProps = { className: "w-4 h-4" };

  switch (iconName) {
    case "square":
      return <Square {...iconProps} />;
    case "rectangle-vertical":
      return <RectangleVertical {...iconProps} />;
    case "rectangle-horizontal":
      return <RectangleHorizontal {...iconProps} />;
    case "smartphone":
      return <Smartphone {...iconProps} />;
    case "link":
      return <Link {...iconProps} />;
    case "share-2":
      return <Share2 {...iconProps} />;
    case "bookmark":
      return <Bookmark {...iconProps} />;
    case "file-text":
      return <FileText {...iconProps} />;
    case "play":
      return <Play {...iconProps} />;
    case "image":
      return <ImageIcon {...iconProps} />;
    default:
      return <Square {...iconProps} />;
  }
};

// Platform icon component
const PlatformIcon: React.FC<{ platform: PlatformCategory; className?: string }> = ({
  platform,
  className = "",
}) => {
  const baseClass = `w-5 h-5 ${className}`;

  // Simple colored circles for platform icons
  const colors: Record<PlatformCategory, string> = {
    instagram: "bg-gradient-to-tr from-[#833AB4] via-[#FD1D1D] to-[#F77737]",
    facebook: "bg-[#1877F2]",
    pinterest: "bg-[#E60023]",
    twitter: "bg-black",
    youtube: "bg-[#FF0000]",
    linkedin: "bg-[#0A66C2]",
  };

  return (
    <div className={`${baseClass} rounded-full ${colors[platform]}`} />
  );
};

export default function PlatformPresets({
  selectedPresets,
  onPresetToggle,
  onSelectAll,
  onDeselectAll,
  className = "",
}: PlatformPresetsProps) {
  const [expandedPlatforms, setExpandedPlatforms] = useState<Set<PlatformCategory>>(
    new Set(["instagram"])
  );

  // Toggle platform expansion
  const togglePlatformExpansion = useCallback((platform: PlatformCategory) => {
    setExpandedPlatforms((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(platform)) {
        newSet.delete(platform);
      } else {
        newSet.add(platform);
      }
      return newSet;
    });
  }, []);

  // Check if a preset is selected
  const isPresetSelected = useCallback(
    (presetId: string): boolean => {
      return selectedPresets.some(
        (item) => item.preset.id === presetId && item.selected
      );
    },
    [selectedPresets]
  );

  // Get selected count for a platform
  const getSelectedCountForPlatform = useCallback(
    (platform: PlatformCategory): number => {
      return selectedPresets.filter(
        (item) => item.preset.platform === platform && item.selected
      ).length;
    },
    [selectedPresets]
  );

  // Check if all presets of a platform are selected
  const isAllPlatformSelected = useCallback(
    (platformConfig: PlatformConfig): boolean => {
      return platformConfig.presets.every((preset) => isPresetSelected(preset.id));
    },
    [isPresetSelected]
  );

  // Total selected count
  const totalSelectedCount = useMemo(() => {
    return selectedPresets.filter((item) => item.selected).length;
  }, [selectedPresets]);

  return (
    <div className={`space-y-3 ${className}`}>
      {/* Header with total count */}
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium text-foreground">
          플랫폼 선택
        </label>
        <span className="text-xs text-muted-foreground">
          {totalSelectedCount}개 선택됨
        </span>
      </div>

      {/* Platform list */}
      <div className="space-y-2">
        {PLATFORM_EXPORT_PRESETS.map((platformConfig) => {
          const isExpanded = expandedPlatforms.has(platformConfig.id);
          const selectedCount = getSelectedCountForPlatform(platformConfig.id);
          const totalCount = platformConfig.presets.length;
          const isAllSelected = isAllPlatformSelected(platformConfig);

          return (
            <div
              key={platformConfig.id}
              className="rounded-lg border border-default bg-muted/30 overflow-hidden"
            >
              {/* Platform header */}
              <button
                onClick={() => togglePlatformExpansion(platformConfig.id)}
                className="w-full flex items-center justify-between p-3 hover:bg-muted/50 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <PlatformIcon platform={platformConfig.id} />
                  <span className="font-medium text-sm">{platformConfig.name}</span>
                  {selectedCount > 0 && (
                    <span
                      className="px-2 py-0.5 text-xs rounded-full text-white"
                      style={{ backgroundColor: platformConfig.brandColor }}
                    >
                      {selectedCount}/{totalCount}
                    </span>
                  )}
                </div>
                {isExpanded ? (
                  <ChevronUp className="w-4 h-4 text-muted-foreground" />
                ) : (
                  <ChevronDown className="w-4 h-4 text-muted-foreground" />
                )}
              </button>

              {/* Platform presets */}
              {isExpanded && (
                <div className="border-t border-default">
                  {/* Select all / Deselect all */}
                  <div className="flex items-center justify-end gap-2 p-2 bg-muted/20">
                    <button
                      onClick={() => onSelectAll(platformConfig.id)}
                      className="text-xs text-accent-500 hover:text-accent-600 transition-colors"
                    >
                      전체 선택
                    </button>
                    <span className="text-muted-foreground">|</span>
                    <button
                      onClick={() => onDeselectAll(platformConfig.id)}
                      className="text-xs text-muted-foreground hover:text-foreground transition-colors"
                    >
                      전체 해제
                    </button>
                  </div>

                  {/* Preset items */}
                  <div className="p-2 space-y-1">
                    {platformConfig.presets.map((preset) => {
                      const isSelected = isPresetSelected(preset.id);

                      return (
                        <button
                          key={preset.id}
                          onClick={() => onPresetToggle(preset)}
                          className={`w-full flex items-center gap-3 p-2.5 rounded-lg transition-all ${
                            isSelected
                              ? "bg-accent-500/10 border border-accent-500"
                              : "bg-muted/30 border border-transparent hover:bg-muted/50"
                          }`}
                        >
                          {/* Checkbox indicator */}
                          <div
                            className={`w-5 h-5 rounded flex items-center justify-center flex-shrink-0 transition-colors ${
                              isSelected
                                ? "bg-accent-500 text-white"
                                : "bg-muted border border-default"
                            }`}
                          >
                            {isSelected && <Check className="w-3 h-3" />}
                          </div>

                          {/* Icon */}
                          <div className="text-muted-foreground">
                            {getPresetIcon(preset.icon)}
                          </div>

                          {/* Preset info */}
                          <div className="flex-1 text-left">
                            <div className="flex items-center gap-2">
                              <span className="text-sm font-medium">
                                {preset.name}
                              </span>
                              <span className="text-xs text-muted-foreground">
                                {preset.aspectRatio}
                              </span>
                            </div>
                            <div className="flex items-center gap-2 text-xs text-muted-foreground">
                              <span>
                                {preset.width} x {preset.height}
                              </span>
                              <span>-</span>
                              <span>{preset.description}</span>
                            </div>
                          </div>
                        </button>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

// Export a compact version for sidebar use
export function PlatformPresetsCompact({
  selectedPresets,
  onPresetToggle,
  className = "",
}: Omit<PlatformPresetsProps, "onSelectAll" | "onDeselectAll">) {
  const totalSelectedCount = useMemo(() => {
    return selectedPresets.filter((item) => item.selected).length;
  }, [selectedPresets]);

  // Group presets by platform
  const groupedPresets = useMemo(() => {
    const grouped: Record<PlatformCategory, PlatformExportPreset[]> = {} as Record<
      PlatformCategory,
      PlatformExportPreset[]
    >;

    PLATFORM_EXPORT_PRESETS.forEach((platform) => {
      grouped[platform.id] = platform.presets;
    });

    return grouped;
  }, []);

  return (
    <div className={`space-y-2 ${className}`}>
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium text-foreground">
          내보내기 크기
        </label>
        <span className="text-xs text-muted-foreground">
          {totalSelectedCount}개 선택
        </span>
      </div>

      <div className="grid grid-cols-2 gap-1.5">
        {PLATFORM_EXPORT_PRESETS.flatMap((platform) =>
          platform.presets.slice(0, 2).map((preset) => {
            const isSelected = selectedPresets.some(
              (item) => item.preset.id === preset.id && item.selected
            );

            return (
              <button
                key={preset.id}
                onClick={() => onPresetToggle(preset)}
                className={`p-2 rounded-lg text-left transition-all ${
                  isSelected
                    ? "bg-accent-500/10 border border-accent-500"
                    : "bg-muted/30 border border-transparent hover:bg-muted/50"
                }`}
              >
                <div className="flex items-center gap-1.5">
                  <PlatformIcon platform={platform.id} className="w-3 h-3" />
                  <span className="text-xs font-medium truncate">
                    {preset.name}
                  </span>
                </div>
                <div className="text-[10px] text-muted-foreground mt-0.5">
                  {preset.width}x{preset.height}
                </div>
              </button>
            );
          })
        )}
      </div>
    </div>
  );
}
