"use client";

/**
 * CanvasTextEditor Component
 * Phase 5: Canvas Text Editor - Main Component
 *
 * Integrates all canvas components:
 * - FabricCanvas (TAG-FE-001)
 * - TextToolbar (TAG-FE-002)
 * - LayerPanel (TAG-FE-003)
 * - CanvasExportPanel (TAG-FE-004)
 */

import React, { useRef, useState, useCallback, useEffect } from "react";
import {
  Undo2,
  Redo2,
  ZoomIn,
  ZoomOut,
  Maximize2,
  RotateCcw,
} from "lucide-react";
import { toast } from "sonner";
import FabricCanvas, { FabricCanvasRef } from "./FabricCanvas";
import TextToolbar from "./TextToolbar";
import LayerPanel from "./LayerPanel";
import CanvasExportPanel from "./CanvasExportPanel";
import type { TextLayer, CanvasState, CanvasSizePreset, ExportOptions, PlatformExportPreset, ImageExportOptions } from "@/types/canvas";
import { CANVAS_SIZE_PRESETS } from "@/types/canvas";
import { performBatchExport } from "@/lib/canvas/platformPresets";

interface CanvasTextEditorProps {
  initialWidth?: number;
  initialHeight?: number;
  backgroundColor?: string;
  backgroundImage?: string;
  onSave?: (state: CanvasState) => void;
  className?: string;
}

export default function CanvasTextEditor({
  initialWidth = 1080,
  initialHeight = 1080,
  backgroundColor = "#1a1f2e",
  backgroundImage,
  onSave,
  className = "",
}: CanvasTextEditorProps) {
  const canvasRef = useRef<FabricCanvasRef>(null);

  const [canvasSize, setCanvasSize] = useState({
    width: initialWidth,
    height: initialHeight,
  });
  const [layers, setLayers] = useState<TextLayer[]>([]);
  const [selectedLayer, setSelectedLayer] = useState<TextLayer | null>(null);
  const [canUndo, setCanUndo] = useState(false);
  const [canRedo, setCanRedo] = useState(false);
  const [showSizePresets, setShowSizePresets] = useState(false);

  // Sync layers from canvas
  const syncLayers = useCallback(() => {
    if (canvasRef.current) {
      const currentLayers = canvasRef.current.getLayers();
      setLayers(currentLayers);
    }
  }, []);

  // Handle layer selection from canvas
  const handleLayerSelect = useCallback((layer: TextLayer | null) => {
    setSelectedLayer(layer);
  }, []);

  // Handle layer update from canvas
  const handleLayerUpdate = useCallback((layer: TextLayer) => {
    setLayers((prev) =>
      prev.map((l) => (l.id === layer.id ? layer : l))
    );
    setSelectedLayer((prev) => (prev?.id === layer.id ? layer : prev));
  }, []);

  // Handle history change
  const handleHistoryChange = useCallback(
    (undo: boolean, redo: boolean) => {
      setCanUndo(undo);
      setCanRedo(redo);
    },
    []
  );

  // Handle canvas ready
  const handleCanvasReady = useCallback(() => {
    syncLayers();
  }, [syncLayers]);

  // Canvas callbacks
  const callbacks = {
    onLayerSelect: handleLayerSelect,
    onLayerUpdate: handleLayerUpdate,
    onHistoryChange: handleHistoryChange,
    onCanvasReady: handleCanvasReady,
  };

  // Add text layer
  const handleAddLayer = useCallback(() => {
    if (canvasRef.current) {
      const newLayer = canvasRef.current.addTextLayer();
      setLayers((prev) => [...prev, newLayer]);
      setSelectedLayer(newLayer);
      toast.success("텍스트 레이어가 추가되었습니다");
    }
  }, []);

  // Remove layer
  const handleRemoveLayer = useCallback((layerId: string) => {
    if (canvasRef.current) {
      canvasRef.current.removeLayer(layerId);
      setLayers((prev) => prev.filter((l) => l.id !== layerId));
      setSelectedLayer(null);
      toast.success("레이어가 삭제되었습니다");
    }
  }, []);

  // Duplicate layer
  const handleDuplicateLayer = useCallback((layerId: string) => {
    if (canvasRef.current) {
      const newLayer = canvasRef.current.duplicateLayer(layerId);
      if (newLayer) {
        setLayers((prev) => [...prev, newLayer]);
        setSelectedLayer(newLayer);
        toast.success("레이어가 복제되었습니다");
      }
    }
  }, []);

  // Update layer
  const handleUpdateLayer = useCallback((updates: Partial<TextLayer>) => {
    if (canvasRef.current && selectedLayer) {
      canvasRef.current.updateLayer(selectedLayer.id, updates);
      const updatedLayer = { ...selectedLayer, ...updates };
      setSelectedLayer(updatedLayer);
      setLayers((prev) =>
        prev.map((l) => (l.id === selectedLayer.id ? updatedLayer : l))
      );
    }
  }, [selectedLayer]);

  // Update layer name
  const handleUpdateLayerName = useCallback(
    (layerId: string, name: string) => {
      if (canvasRef.current) {
        canvasRef.current.updateLayer(layerId, { name });
        setLayers((prev) =>
          prev.map((l) => (l.id === layerId ? { ...l, name } : l))
        );
        if (selectedLayer?.id === layerId) {
          setSelectedLayer((prev) => (prev ? { ...prev, name } : null));
        }
      }
    },
    [selectedLayer]
  );

  // Select layer
  const handleSelectLayer = useCallback((layerId: string | null) => {
    if (canvasRef.current) {
      canvasRef.current.selectLayer(layerId);
      if (layerId) {
        const layer = canvasRef.current.getSelectedLayer();
        setSelectedLayer(layer);
      } else {
        setSelectedLayer(null);
      }
    }
  }, []);

  // Layer ordering
  const handleMoveLayerUp = useCallback((layerId: string) => {
    canvasRef.current?.moveLayerUp(layerId);
    syncLayers();
  }, [syncLayers]);

  const handleMoveLayerDown = useCallback((layerId: string) => {
    canvasRef.current?.moveLayerDown(layerId);
    syncLayers();
  }, [syncLayers]);

  const handleBringToFront = useCallback((layerId: string) => {
    canvasRef.current?.bringToFront(layerId);
    syncLayers();
  }, [syncLayers]);

  const handleSendToBack = useCallback((layerId: string) => {
    canvasRef.current?.sendToBack(layerId);
    syncLayers();
  }, [syncLayers]);

  const handleToggleVisibility = useCallback((layerId: string) => {
    canvasRef.current?.toggleLayerVisibility(layerId);
    syncLayers();
  }, [syncLayers]);

  const handleToggleLock = useCallback((layerId: string) => {
    canvasRef.current?.toggleLayerLock(layerId);
    syncLayers();
  }, [syncLayers]);

  // Undo/Redo
  const handleUndo = useCallback(() => {
    if (canvasRef.current) {
      canvasRef.current.undo();
      syncLayers();
    }
  }, [syncLayers]);

  const handleRedo = useCallback(() => {
    if (canvasRef.current) {
      canvasRef.current.redo();
      syncLayers();
    }
  }, [syncLayers]);

  // Clear canvas
  const handleClearCanvas = useCallback(() => {
    if (canvasRef.current) {
      if (confirm("캔버스를 초기화하시겠습니까? 모든 레이어가 삭제됩니다.")) {
        canvasRef.current.clearCanvas();
        setLayers([]);
        setSelectedLayer(null);
        toast.success("캔버스가 초기화되었습니다");
      }
    }
  }, []);

  // Change canvas size
  const handleSizeChange = useCallback((preset: CanvasSizePreset) => {
    setCanvasSize({ width: preset.width, height: preset.height });
    setShowSizePresets(false);
    toast.success(`캔버스 크기가 ${preset.name}(으)로 변경되었습니다`);
  }, []);

  // Export functions
  const handleExportImage = useCallback(
    (options: ExportOptions) => {
      if (canvasRef.current) {
        return canvasRef.current.exportAsImage(options);
      }
      return "";
    },
    []
  );

  const handleDownloadImage = useCallback(
    (filename: string, options: ExportOptions) => {
      canvasRef.current?.downloadImage(filename, options);
    },
    []
  );

  const handleDownloadJson = useCallback((filename: string) => {
    canvasRef.current?.downloadJson(filename);
  }, []);

  const handleLoadState = useCallback((state: CanvasState) => {
    if (canvasRef.current) {
      canvasRef.current.loadCanvasState(state);
      setCanvasSize({ width: state.width, height: state.height });
      setLayers(state.layers);
      setSelectedLayer(null);
    }
  }, []);

  const handleSetBackgroundImage = useCallback(async (imageUrl: string) => {
    if (canvasRef.current) {
      await canvasRef.current.setBackgroundImage(imageUrl);
    }
  }, []);

  const getCanvasState = useCallback(() => {
    if (canvasRef.current) {
      return canvasRef.current.getCanvasState();
    }
    return {
      version: "1.0.0",
      width: canvasSize.width,
      height: canvasSize.height,
      backgroundColor,
      backgroundImage: null,
      layers: [],
      objects: [],
    };
  }, [canvasSize, backgroundColor]);

  // Batch export handler
  const handleBatchExport = useCallback(
    async (presets: PlatformExportPreset[], options: ImageExportOptions) => {
      if (!canvasRef.current) {
        toast.error("캔버스가 준비되지 않았습니다");
        return;
      }

      const canvasExportFn = (width: number, height: number, opts: ImageExportOptions) => {
        return canvasRef.current!.exportAsImage({
          format: opts.format,
          quality: opts.quality / 100,
          multiplier: opts.multiplier,
        });
      };

      await performBatchExport(canvasExportFn, presets, options);
    },
    []
  );

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Check if we're in an input field
      if (
        e.target instanceof HTMLInputElement ||
        e.target instanceof HTMLTextAreaElement
      ) {
        return;
      }

      // Undo: Cmd/Ctrl + Z
      if ((e.metaKey || e.ctrlKey) && e.key === "z" && !e.shiftKey) {
        e.preventDefault();
        handleUndo();
      }

      // Redo: Cmd/Ctrl + Shift + Z or Cmd/Ctrl + Y
      if (
        ((e.metaKey || e.ctrlKey) && e.key === "z" && e.shiftKey) ||
        ((e.metaKey || e.ctrlKey) && e.key === "y")
      ) {
        e.preventDefault();
        handleRedo();
      }

      // Delete selected layer: Delete or Backspace
      if (
        (e.key === "Delete" || e.key === "Backspace") &&
        selectedLayer &&
        !selectedLayer.locked
      ) {
        e.preventDefault();
        handleRemoveLayer(selectedLayer.id);
      }

      // Duplicate: Cmd/Ctrl + D
      if ((e.metaKey || e.ctrlKey) && e.key === "d" && selectedLayer) {
        e.preventDefault();
        handleDuplicateLayer(selectedLayer.id);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [handleUndo, handleRedo, handleRemoveLayer, handleDuplicateLayer, selectedLayer]);

  return (
    <div className={`flex flex-col h-full ${className}`}>
      {/* Top Toolbar */}
      <div className="flex items-center justify-between p-3 border-b border-default bg-card">
        {/* Left Controls */}
        <div className="flex items-center gap-2">
          {/* Undo/Redo */}
          <div className="flex items-center gap-1">
            <button
              onClick={handleUndo}
              disabled={!canUndo}
              className="p-2 rounded-lg hover:bg-muted disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              title="실행 취소 (Cmd+Z)"
            >
              <Undo2 className="w-4 h-4" />
            </button>
            <button
              onClick={handleRedo}
              disabled={!canRedo}
              className="p-2 rounded-lg hover:bg-muted disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              title="다시 실행 (Cmd+Shift+Z)"
            >
              <Redo2 className="w-4 h-4" />
            </button>
          </div>

          <div className="w-px h-6 bg-border" />

          {/* Canvas Size */}
          <div className="relative">
            <button
              onClick={() => setShowSizePresets(!showSizePresets)}
              className="flex items-center gap-2 px-3 py-1.5 text-sm rounded-lg hover:bg-muted transition-colors"
            >
              <Maximize2 className="w-4 h-4" />
              {canvasSize.width} x {canvasSize.height}
            </button>

            {showSizePresets && (
              <div className="absolute top-full left-0 mt-2 w-56 py-2 rounded-xl bg-card border border-default shadow-lg z-[100] animate-fade-in">
                {CANVAS_SIZE_PRESETS.map((preset) => (
                  <button
                    key={preset.name}
                    onClick={() => handleSizeChange(preset)}
                    className={`w-full px-4 py-2 text-left text-sm hover:bg-muted transition-colors ${
                      canvasSize.width === preset.width &&
                      canvasSize.height === preset.height
                        ? "text-accent-500 font-medium"
                        : "text-foreground"
                    }`}
                  >
                    <span>{preset.name}</span>
                    <span className="text-xs text-muted-foreground ml-2">
                      ({preset.width}x{preset.height})
                    </span>
                  </button>
                ))}
              </div>
            )}
          </div>

          <div className="w-px h-6 bg-border" />

          {/* Clear Canvas */}
          <button
            onClick={handleClearCanvas}
            className="flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-lg hover:bg-red-500/10 text-red-500 transition-colors"
            title="캔버스 초기화"
          >
            <RotateCcw className="w-4 h-4" />
            초기화
          </button>
        </div>

        {/* Right Controls */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-muted-foreground">
            레이어: {layers.length}개
          </span>
        </div>
      </div>

      {/* Text Toolbar */}
      <div className="border-b border-default bg-card/50 relative z-40 overflow-visible">
        <TextToolbar
          selectedLayer={selectedLayer}
          onUpdate={handleUpdateLayer}
        />
      </div>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden min-h-0">
        {/* Canvas Area */}
        <div className="flex-1 flex items-center justify-center bg-muted/30 p-4 overflow-hidden">
          <div className="relative w-full h-full flex items-center justify-center">
            <div className="shadow-2xl rounded-lg overflow-hidden max-w-full max-h-full">
              <FabricCanvas
                ref={canvasRef}
                width={canvasSize.width}
                height={canvasSize.height}
                backgroundColor={backgroundColor}
                backgroundImage={backgroundImage}
                callbacks={callbacks}
                className="max-w-full max-h-full"
              />
            </div>
          </div>
        </div>

        {/* Right Sidebar */}
        <div className="w-72 border-l border-default bg-card flex flex-col">
          {/* Layer Panel */}
          <div className="flex-1 overflow-hidden">
            <LayerPanel
              layers={layers}
              selectedLayerId={selectedLayer?.id || null}
              onSelectLayer={handleSelectLayer}
              onAddLayer={handleAddLayer}
              onRemoveLayer={handleRemoveLayer}
              onDuplicateLayer={handleDuplicateLayer}
              onMoveLayerUp={handleMoveLayerUp}
              onMoveLayerDown={handleMoveLayerDown}
              onBringToFront={handleBringToFront}
              onSendToBack={handleSendToBack}
              onToggleVisibility={handleToggleVisibility}
              onToggleLock={handleToggleLock}
              onUpdateLayerName={handleUpdateLayerName}
            />
          </div>

          {/* Export Panel */}
          <div className="border-t border-default p-3">
            <CanvasExportPanel
              onExportImage={handleExportImage}
              onDownloadImage={handleDownloadImage}
              onDownloadJson={handleDownloadJson}
              onLoadState={handleLoadState}
              onSetBackgroundImage={handleSetBackgroundImage}
              getCanvasState={getCanvasState}
              onBatchExport={handleBatchExport}
              canvasWidth={canvasSize.width}
              canvasHeight={canvasSize.height}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
