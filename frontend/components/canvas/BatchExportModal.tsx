"use client";

/**
 * BatchExportModal Component
 * TAG-EX-003: Batch Export with ZIP Download
 *
 * Provides batch export functionality with progress indicator,
 * quality options, and ZIP file generation.
 */

import React, { useState, useCallback, useMemo, useEffect } from "react";
import {
  X,
  Download,
  Archive,
  Loader2,
  Check,
  AlertCircle,
  Image as ImageIcon,
  Settings,
} from "lucide-react";
import type {
  PlatformExportPreset,
  BatchExportItem,
  BatchExportProgress,
  ImageExportOptions,
  ImageExportFormat,
} from "@/types/canvas";
import {
  PLATFORM_EXPORT_PRESETS,
  DEFAULT_IMAGE_EXPORT_OPTIONS,
} from "@/types/canvas";
import PlatformPresets from "./PlatformPresets";

interface BatchExportModalProps {
  isOpen: boolean;
  onClose: () => void;
  onExport: (
    presets: PlatformExportPreset[],
    options: ImageExportOptions
  ) => Promise<void>;
  canvasWidth: number;
  canvasHeight: number;
}

export default function BatchExportModal({
  isOpen,
  onClose,
  onExport,
  canvasWidth,
  canvasHeight,
}: BatchExportModalProps) {
  // Initialize all presets as unselected
  const initialBatchItems = useMemo<BatchExportItem[]>(() => {
    return PLATFORM_EXPORT_PRESETS.flatMap((platform) =>
      platform.presets.map((preset) => ({
        preset,
        selected: false,
      }))
    );
  }, []);

  const [selectedPresets, setSelectedPresets] = useState<BatchExportItem[]>(initialBatchItems);
  const [exportOptions, setExportOptions] = useState<ImageExportOptions>(
    DEFAULT_IMAGE_EXPORT_OPTIONS
  );
  const [showOptions, setShowOptions] = useState(false);
  const [progress, setProgress] = useState<BatchExportProgress>({
    current: 0,
    total: 0,
    currentPreset: "",
    status: "idle",
  });

  // Reset state when modal opens
  useEffect(() => {
    if (isOpen) {
      setProgress({
        current: 0,
        total: 0,
        currentPreset: "",
        status: "idle",
      });
    }
  }, [isOpen]);

  // Toggle preset selection
  const handlePresetToggle = useCallback((preset: PlatformExportPreset) => {
    setSelectedPresets((prev) =>
      prev.map((item) =>
        item.preset.id === preset.id
          ? { ...item, selected: !item.selected }
          : item
      )
    );
  }, []);

  // Select all presets for a platform
  const handleSelectAll = useCallback((platformId: string) => {
    setSelectedPresets((prev) =>
      prev.map((item) =>
        item.preset.platform === platformId ? { ...item, selected: true } : item
      )
    );
  }, []);

  // Deselect all presets for a platform
  const handleDeselectAll = useCallback((platformId: string) => {
    setSelectedPresets((prev) =>
      prev.map((item) =>
        item.preset.platform === platformId ? { ...item, selected: false } : item
      )
    );
  }, []);

  // Get selected presets
  const selectedPresetsList = useMemo(() => {
    return selectedPresets.filter((item) => item.selected).map((item) => item.preset);
  }, [selectedPresets]);

  // Handle export
  const handleExport = useCallback(async () => {
    if (selectedPresetsList.length === 0) return;

    setProgress({
      current: 0,
      total: selectedPresetsList.length,
      currentPreset: selectedPresetsList[0].name,
      status: "exporting",
    });

    try {
      await onExport(selectedPresetsList, exportOptions);
      setProgress((prev) => ({
        ...prev,
        status: "complete",
      }));
    } catch (error) {
      setProgress((prev) => ({
        ...prev,
        status: "error",
        error: error instanceof Error ? error.message : "Export failed",
      }));
    }
  }, [selectedPresetsList, exportOptions, onExport]);

  // Update export option
  const updateExportOption = useCallback(
    <K extends keyof ImageExportOptions>(key: K, value: ImageExportOptions[K]) => {
      setExportOptions((prev) => ({ ...prev, [key]: value }));
    },
    []
  );

  // Calculate estimated file size (rough estimate)
  const estimatedTotalSize = useMemo(() => {
    const bytesPerPixel = exportOptions.format === "png" ? 4 : 1;
    const qualityFactor = exportOptions.format === "png" ? 0.5 : exportOptions.quality / 100;
    const multiplierSquared = exportOptions.multiplier * exportOptions.multiplier;

    let totalBytes = 0;
    selectedPresetsList.forEach((preset) => {
      totalBytes +=
        preset.width *
        preset.height *
        bytesPerPixel *
        qualityFactor *
        multiplierSquared;
    });

    if (totalBytes < 1024) return `${Math.round(totalBytes)} B`;
    if (totalBytes < 1024 * 1024) return `${Math.round(totalBytes / 1024)} KB`;
    return `${(totalBytes / (1024 * 1024)).toFixed(1)} MB`;
  }, [selectedPresetsList, exportOptions]);

  if (!isOpen) return null;

  const isExporting = progress.status === "exporting" || progress.status === "zipping";
  const isComplete = progress.status === "complete";
  const isError = progress.status === "error";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={!isExporting ? onClose : undefined}
      />

      {/* Modal */}
      <div className="relative w-full max-w-2xl max-h-[90vh] bg-background border border-default rounded-xl shadow-2xl overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-default">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-accent-500/10 flex items-center justify-center">
              <Archive className="w-5 h-5 text-accent-500" />
            </div>
            <div>
              <h2 className="text-lg font-semibold">일괄 내보내기</h2>
              <p className="text-sm text-muted-foreground">
                여러 플랫폼에 맞는 크기로 한번에 내보내기
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            disabled={isExporting}
            className="p-2 rounded-lg hover:bg-muted transition-colors disabled:opacity-50"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {/* Export Options Toggle */}
          <button
            onClick={() => setShowOptions(!showOptions)}
            className="flex items-center gap-2 text-sm text-accent-500 hover:text-accent-600 transition-colors"
          >
            <Settings className="w-4 h-4" />
            {showOptions ? "옵션 숨기기" : "내보내기 옵션"}
          </button>

          {/* Export Options */}
          {showOptions && (
            <div className="p-4 rounded-lg bg-muted/30 border border-default space-y-4">
              {/* Format Selection */}
              <div>
                <label className="block text-sm font-medium mb-2">포맷</label>
                <div className="flex gap-2">
                  {(["png", "jpeg", "webp"] as ImageExportFormat[]).map((format) => (
                    <button
                      key={format}
                      onClick={() => updateExportOption("format", format)}
                      className={`flex-1 px-3 py-2 text-sm font-medium rounded-lg transition-colors uppercase ${
                        exportOptions.format === format
                          ? "bg-accent-500 text-white"
                          : "bg-muted hover:bg-muted-foreground/10"
                      }`}
                    >
                      {format}
                    </button>
                  ))}
                </div>
                {exportOptions.format === "png" && (
                  <p className="text-xs text-muted-foreground mt-2">
                    PNG는 투명 배경을 지원합니다
                  </p>
                )}
              </div>

              {/* Quality Slider (JPEG/WebP only) */}
              {exportOptions.format !== "png" && (
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <label className="text-sm font-medium">품질</label>
                    <span className="text-sm text-muted-foreground">
                      {exportOptions.quality}%
                    </span>
                  </div>
                  <input
                    type="range"
                    min="1"
                    max="100"
                    value={exportOptions.quality}
                    onChange={(e) =>
                      updateExportOption("quality", parseInt(e.target.value))
                    }
                    className="w-full accent-accent-500"
                  />
                  <div className="flex justify-between text-xs text-muted-foreground mt-1">
                    <span>낮은 품질 (작은 파일)</span>
                    <span>높은 품질 (큰 파일)</span>
                  </div>
                </div>
              )}

              {/* Resolution Multiplier */}
              <div>
                <label className="block text-sm font-medium mb-2">
                  해상도 배율
                </label>
                <div className="flex gap-2">
                  {([1, 2, 3] as const).map((multiplier) => (
                    <button
                      key={multiplier}
                      onClick={() => updateExportOption("multiplier", multiplier)}
                      className={`flex-1 px-3 py-2 rounded-lg transition-colors ${
                        exportOptions.multiplier === multiplier
                          ? "bg-accent-500 text-white"
                          : "bg-muted hover:bg-muted-foreground/10"
                      }`}
                    >
                      <div className="text-sm font-medium">{multiplier}x</div>
                      <div className="text-xs opacity-70">
                        {multiplier === 1 && "표준"}
                        {multiplier === 2 && "레티나"}
                        {multiplier === 3 && "초고해상도"}
                      </div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Transparent Background (PNG only) */}
              {exportOptions.format === "png" && (
                <div className="flex items-center justify-between">
                  <label className="text-sm font-medium">투명 배경</label>
                  <button
                    onClick={() =>
                      updateExportOption(
                        "transparentBackground",
                        !exportOptions.transparentBackground
                      )
                    }
                    className={`relative w-11 h-6 rounded-full transition-colors ${
                      exportOptions.transparentBackground
                        ? "bg-accent-500"
                        : "bg-muted"
                    }`}
                  >
                    <div
                      className={`absolute top-1 w-4 h-4 rounded-full bg-white transition-transform ${
                        exportOptions.transparentBackground
                          ? "translate-x-6"
                          : "translate-x-1"
                      }`}
                    />
                  </button>
                </div>
              )}
            </div>
          )}

          {/* Platform Presets */}
          <PlatformPresets
            selectedPresets={selectedPresets}
            onPresetToggle={handlePresetToggle}
            onSelectAll={handleSelectAll}
            onDeselectAll={handleDeselectAll}
          />

          {/* Progress */}
          {isExporting && (
            <div className="p-4 rounded-lg bg-accent-500/10 border border-accent-500/20">
              <div className="flex items-center gap-3 mb-3">
                <Loader2 className="w-5 h-5 text-accent-500 animate-spin" />
                <div className="flex-1">
                  <div className="text-sm font-medium">
                    {progress.status === "zipping"
                      ? "ZIP 파일 생성 중..."
                      : `내보내는 중: ${progress.currentPreset}`}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {progress.current} / {progress.total}
                  </div>
                </div>
              </div>
              <div className="w-full h-2 bg-muted rounded-full overflow-hidden">
                <div
                  className="h-full bg-accent-500 transition-all duration-300"
                  style={{
                    width: `${(progress.current / progress.total) * 100}%`,
                  }}
                />
              </div>
            </div>
          )}

          {/* Success */}
          {isComplete && (
            <div className="p-4 rounded-lg bg-green-500/10 border border-green-500/20 flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-green-500/20 flex items-center justify-center">
                <Check className="w-5 h-5 text-green-500" />
              </div>
              <div>
                <div className="text-sm font-medium text-green-600">
                  내보내기 완료
                </div>
                <div className="text-xs text-muted-foreground">
                  {selectedPresetsList.length}개의 이미지가 ZIP 파일로 다운로드되었습니다
                </div>
              </div>
            </div>
          )}

          {/* Error */}
          {isError && (
            <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/20 flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-red-500/20 flex items-center justify-center">
                <AlertCircle className="w-5 h-5 text-red-500" />
              </div>
              <div>
                <div className="text-sm font-medium text-red-600">
                  내보내기 실패
                </div>
                <div className="text-xs text-muted-foreground">
                  {progress.error || "알 수 없는 오류가 발생했습니다"}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-default bg-muted/30">
          <div className="flex items-center justify-between mb-3">
            <div className="text-sm text-muted-foreground">
              <span className="font-medium text-foreground">
                {selectedPresetsList.length}
              </span>
              개 선택됨
              {selectedPresetsList.length > 0 && (
                <span className="ml-2">
                  (예상 크기: ~{estimatedTotalSize})
                </span>
              )}
            </div>
          </div>

          <div className="flex gap-3">
            <button
              onClick={onClose}
              disabled={isExporting}
              className="flex-1 px-4 py-2.5 text-sm font-medium rounded-lg bg-muted hover:bg-muted-foreground/10 transition-colors disabled:opacity-50"
            >
              {isComplete ? "닫기" : "취소"}
            </button>
            <button
              onClick={handleExport}
              disabled={selectedPresetsList.length === 0 || isExporting}
              className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 text-sm font-medium rounded-lg bg-accent-500 text-white hover:bg-accent-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isExporting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  처리 중...
                </>
              ) : (
                <>
                  <Download className="w-4 h-4" />
                  ZIP으로 다운로드
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// Export progress update callback type
export type BatchExportProgressCallback = (
  current: number,
  total: number,
  currentPreset: string,
  status: BatchExportProgress["status"]
) => void;
