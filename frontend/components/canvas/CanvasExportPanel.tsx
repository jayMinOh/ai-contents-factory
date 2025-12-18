"use client";

/**
 * CanvasExportPanel Component
 * TAG-FE-004: Canvas State Persistence
 * TAG-EX-001/002/003: Platform Export with Batch Export
 *
 * Provides export and save controls:
 * - Save canvas state to JSON
 * - Load canvas state from JSON
 * - Export canvas to image (PNG, JPEG, WebP)
 * - Platform-specific dimension presets
 * - Batch export with ZIP download
 */

import React, { useState, useRef, useCallback } from "react";
import {
  Download,
  Upload,
  Save,
  FileJson,
  Image as ImageIcon,
  FileImage,
  Loader2,
  Check,
  X,
  Archive,
  Layers,
} from "lucide-react";
import { toast } from "sonner";
import type {
  CanvasState,
  ExportFormat,
  ExportOptions,
  ImageExportOptions,
  ImageExportFormat,
  PlatformExportPreset,
} from "@/types/canvas";
import {
  serializeCanvasState,
  parseCanvasState,
  loadImageFile,
} from "@/lib/canvas/canvasUtils";
import BatchExportModal from "./BatchExportModal";

interface CanvasExportPanelProps {
  onExportImage: (options: ExportOptions) => string;
  onDownloadImage: (filename: string, options: ExportOptions) => void;
  onDownloadJson: (filename: string) => void;
  onLoadState: (state: CanvasState) => void;
  onSetBackgroundImage: (imageUrl: string) => Promise<void>;
  getCanvasState: () => CanvasState;
  onBatchExport: (
    presets: PlatformExportPreset[],
    options: ImageExportOptions
  ) => Promise<void>;
  canvasWidth: number;
  canvasHeight: number;
  className?: string;
}

export default function CanvasExportPanel({
  onExportImage,
  onDownloadImage,
  onDownloadJson,
  onLoadState,
  onSetBackgroundImage,
  getCanvasState,
  onBatchExport,
  canvasWidth,
  canvasHeight,
  className = "",
}: CanvasExportPanelProps) {
  const [isExporting, setIsExporting] = useState(false);
  const [exportFormat, setExportFormat] = useState<ImageExportFormat>("png");
  const [exportQuality, setExportQuality] = useState(92);
  const [exportScale, setExportScale] = useState<1 | 2 | 3>(1);
  const [showExportOptions, setShowExportOptions] = useState(false);
  const [showBatchExportModal, setShowBatchExportModal] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const imageInputRef = useRef<HTMLInputElement>(null);

  // Handle export image
  const handleExportImage = useCallback(async () => {
    setIsExporting(true);
    try {
      const options: ExportOptions = {
        format: exportFormat,
        quality: exportQuality / 100,
        multiplier: exportScale,
      };

      onDownloadImage(`canvas-export-${Date.now()}`, options);
      toast.success("이미지가 다운로드되었습니다");
    } catch (error) {
      toast.error("이미지 내보내기에 실패했습니다");
      console.error("Export error:", error);
    } finally {
      setIsExporting(false);
    }
  }, [exportFormat, exportQuality, exportScale, onDownloadImage]);

  // Handle export JSON
  const handleExportJson = useCallback(() => {
    try {
      onDownloadJson(`canvas-state-${Date.now()}`);
      toast.success("JSON 파일이 다운로드되었습니다");
    } catch (error) {
      toast.error("JSON 내보내기에 실패했습니다");
      console.error("Export JSON error:", error);
    }
  }, [onDownloadJson]);

  // Handle load JSON file
  const handleLoadJson = useCallback(
    async (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (!file) return;

      try {
        const text = await file.text();
        const state = parseCanvasState(text);

        if (state) {
          onLoadState(state);
          toast.success("캔버스 상태를 불러왔습니다");
        } else {
          toast.error("유효하지 않은 파일 형식입니다");
        }
      } catch (error) {
        toast.error("파일을 불러오는데 실패했습니다");
        console.error("Load JSON error:", error);
      }

      // Reset input
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    },
    [onLoadState]
  );

  // Handle load background image
  const handleLoadImage = useCallback(
    async (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (!file) return;

      try {
        const imageUrl = await loadImageFile(file);
        await onSetBackgroundImage(imageUrl);
        toast.success("배경 이미지가 설정되었습니다");
      } catch (error) {
        toast.error("이미지를 불러오는데 실패했습니다");
        console.error("Load image error:", error);
      }

      // Reset input
      if (imageInputRef.current) {
        imageInputRef.current.value = "";
      }
    },
    [onSetBackgroundImage]
  );

  // Copy to clipboard
  const handleCopyToClipboard = useCallback(async () => {
    try {
      const options: ExportOptions = {
        format: "png",
        multiplier: exportScale,
      };

      const dataUrl = onExportImage(options);

      // Convert data URL to blob
      const response = await fetch(dataUrl);
      const blob = await response.blob();

      await navigator.clipboard.write([
        new ClipboardItem({
          [blob.type]: blob,
        }),
      ]);

      toast.success("클립보드에 복사되었습니다");
    } catch (error) {
      toast.error("클립보드 복사에 실패했습니다");
      console.error("Copy to clipboard error:", error);
    }
  }, [exportScale, onExportImage]);

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Background Image Upload */}
      <div>
        <label className="block text-sm font-medium text-foreground mb-2">
          배경 이미지
        </label>
        <div className="flex gap-2">
          <button
            onClick={() => imageInputRef.current?.click()}
            className="flex-1 flex items-center justify-center gap-2 px-3 py-2 text-sm rounded-lg bg-muted hover:bg-muted-foreground/10 border border-default transition-colors"
          >
            <ImageIcon className="w-4 h-4" />
            이미지 업로드
          </button>
          <input
            ref={imageInputRef}
            type="file"
            accept="image/*"
            onChange={handleLoadImage}
            className="hidden"
          />
        </div>
      </div>

      {/* Divider */}
      <div className="divider" />

      {/* Save/Load State */}
      <div>
        <label className="block text-sm font-medium text-foreground mb-2">
          프로젝트 저장/불러오기
        </label>
        <div className="flex gap-2">
          <button
            onClick={handleExportJson}
            className="flex-1 flex items-center justify-center gap-2 px-3 py-2 text-sm rounded-lg bg-muted hover:bg-muted-foreground/10 border border-default transition-colors"
            title="JSON으로 저장"
          >
            <Save className="w-4 h-4" />
            저장
          </button>
          <button
            onClick={() => fileInputRef.current?.click()}
            className="flex-1 flex items-center justify-center gap-2 px-3 py-2 text-sm rounded-lg bg-muted hover:bg-muted-foreground/10 border border-default transition-colors"
            title="JSON 불러오기"
          >
            <Upload className="w-4 h-4" />
            불러오기
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept=".json"
            onChange={handleLoadJson}
            className="hidden"
          />
        </div>
      </div>

      {/* Divider */}
      <div className="divider" />

      {/* Export Options */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <label className="text-sm font-medium text-foreground">
            이미지 내보내기
          </label>
          <button
            onClick={() => setShowExportOptions(!showExportOptions)}
            className="text-xs text-accent-500 hover:text-accent-600"
          >
            {showExportOptions ? "옵션 닫기" : "옵션 열기"}
          </button>
        </div>

        {showExportOptions && (
          <div className="space-y-3 mb-3 p-3 rounded-lg bg-muted/50 border border-default">
            {/* Format Selection */}
            <div>
              <label className="block text-xs text-muted-foreground mb-1">
                포맷
              </label>
              <div className="flex gap-2">
                {(["png", "jpeg", "webp"] as ImageExportFormat[]).map(
                  (format) => (
                    <button
                      key={format}
                      onClick={() => setExportFormat(format)}
                      className={`flex-1 px-3 py-1.5 text-xs font-medium rounded-lg transition-colors uppercase ${
                        exportFormat === format
                          ? "bg-accent-500 text-white"
                          : "bg-muted hover:bg-muted-foreground/10"
                      }`}
                    >
                      {format}
                    </button>
                  )
                )}
              </div>
            </div>

            {/* Quality (JPEG/WebP only) */}
            {(exportFormat === "jpeg" || exportFormat === "webp") && (
              <div>
                <label className="block text-xs text-muted-foreground mb-1">
                  품질: {exportQuality}%
                </label>
                <input
                  type="range"
                  min="10"
                  max="100"
                  value={exportQuality}
                  onChange={(e) => setExportQuality(parseInt(e.target.value))}
                  className="w-full accent-accent-500"
                />
              </div>
            )}

            {/* Scale */}
            <div>
              <label className="block text-xs text-muted-foreground mb-1">
                해상도: {exportScale}x
              </label>
              <div className="flex gap-2">
                {([1, 2, 3] as const).map((scale) => (
                  <button
                    key={scale}
                    onClick={() => setExportScale(scale)}
                    className={`flex-1 px-3 py-1.5 text-xs font-medium rounded-lg transition-colors ${
                      exportScale === scale
                        ? "bg-accent-500 text-white"
                        : "bg-muted hover:bg-muted-foreground/10"
                    }`}
                  >
                    {scale}x
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Export Buttons */}
        <div className="flex gap-2">
          <button
            onClick={handleExportImage}
            disabled={isExporting}
            className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 text-sm font-medium rounded-lg bg-accent-500 text-white hover:bg-accent-600 transition-colors disabled:opacity-50"
          >
            {isExporting ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                내보내는 중...
              </>
            ) : (
              <>
                <Download className="w-4 h-4" />
                다운로드
              </>
            )}
          </button>
          <button
            onClick={handleCopyToClipboard}
            className="px-3 py-2.5 rounded-lg bg-muted hover:bg-muted-foreground/10 border border-default transition-colors"
            title="클립보드에 복사"
          >
            <FileImage className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Divider */}
      <div className="divider" />

      {/* Batch Export Section */}
      <div>
        <label className="block text-sm font-medium text-foreground mb-2">
          플랫폼별 내보내기
        </label>
        <button
          onClick={() => setShowBatchExportModal(true)}
          className="w-full flex items-center justify-center gap-2 px-4 py-2.5 text-sm font-medium rounded-lg bg-gradient-to-r from-accent-500 to-purple-500 text-white hover:from-accent-600 hover:to-purple-600 transition-all"
        >
          <Layers className="w-4 h-4" />
          일괄 내보내기
        </button>
        <p className="text-xs text-muted-foreground mt-2">
          Instagram, Facebook, Pinterest, Twitter, YouTube, LinkedIn 등
          다양한 플랫폼에 맞는 크기로 한번에 내보내기
        </p>
      </div>

      {/* Batch Export Modal */}
      <BatchExportModal
        isOpen={showBatchExportModal}
        onClose={() => setShowBatchExportModal(false)}
        onExport={onBatchExport}
        canvasWidth={canvasWidth}
        canvasHeight={canvasHeight}
      />
    </div>
  );
}
