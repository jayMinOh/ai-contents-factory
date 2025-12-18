"use client";

/**
 * LayerPanel Component
 * TAG-FE-003: Layer Management System
 *
 * Provides layer management controls:
 * - Add/remove text layers
 * - Layer ordering (bring to front, send to back)
 * - Layer visibility toggle
 * - Layer selection and editing
 * - Multi-layer support
 */

import React, { useCallback } from "react";
import {
  Plus,
  Trash2,
  Copy,
  Eye,
  EyeOff,
  Lock,
  Unlock,
  ChevronUp,
  ChevronDown,
  ChevronsUp,
  ChevronsDown,
  Type,
  GripVertical,
} from "lucide-react";
import type { TextLayer } from "@/types/canvas";

interface LayerPanelProps {
  layers: TextLayer[];
  selectedLayerId: string | null;
  onSelectLayer: (layerId: string | null) => void;
  onAddLayer: () => void;
  onRemoveLayer: (layerId: string) => void;
  onDuplicateLayer: (layerId: string) => void;
  onMoveLayerUp: (layerId: string) => void;
  onMoveLayerDown: (layerId: string) => void;
  onBringToFront: (layerId: string) => void;
  onSendToBack: (layerId: string) => void;
  onToggleVisibility: (layerId: string) => void;
  onToggleLock: (layerId: string) => void;
  onUpdateLayerName: (layerId: string, name: string) => void;
  className?: string;
}

export default function LayerPanel({
  layers,
  selectedLayerId,
  onSelectLayer,
  onAddLayer,
  onRemoveLayer,
  onDuplicateLayer,
  onMoveLayerUp,
  onMoveLayerDown,
  onBringToFront,
  onSendToBack,
  onToggleVisibility,
  onToggleLock,
  onUpdateLayerName,
  className = "",
}: LayerPanelProps) {
  const [editingLayerId, setEditingLayerId] = React.useState<string | null>(null);
  const [editingName, setEditingName] = React.useState("");

  const handleStartEditing = useCallback((layer: TextLayer) => {
    setEditingLayerId(layer.id);
    setEditingName(layer.name);
  }, []);

  const handleFinishEditing = useCallback(() => {
    if (editingLayerId && editingName.trim()) {
      onUpdateLayerName(editingLayerId, editingName.trim());
    }
    setEditingLayerId(null);
    setEditingName("");
  }, [editingLayerId, editingName, onUpdateLayerName]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Enter") {
        handleFinishEditing();
      } else if (e.key === "Escape") {
        setEditingLayerId(null);
        setEditingName("");
      }
    },
    [handleFinishEditing]
  );

  // Reverse layers for display (top layer first)
  const displayLayers = [...layers].reverse();

  return (
    <div className={`flex flex-col h-full ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between p-3 border-b border-default">
        <h3 className="font-semibold text-foreground text-sm">레이어</h3>
        <button
          onClick={onAddLayer}
          className="flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-lg bg-accent-500 text-white hover:bg-accent-600 transition-colors"
          title="텍스트 레이어 추가"
        >
          <Plus className="w-3.5 h-3.5" />
          추가
        </button>
      </div>

      {/* Layer List */}
      <div className="flex-1 overflow-y-auto">
        {displayLayers.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center p-4">
            <div className="w-12 h-12 rounded-xl bg-muted flex items-center justify-center mb-3">
              <Type className="w-6 h-6 text-muted-foreground" />
            </div>
            <p className="text-sm text-muted-foreground mb-2">
              레이어가 없습니다
            </p>
            <button
              onClick={onAddLayer}
              className="text-xs text-accent-500 hover:text-accent-600 font-medium"
            >
              + 텍스트 추가
            </button>
          </div>
        ) : (
          <div className="p-2 space-y-1">
            {displayLayers.map((layer, index) => {
              const isSelected = layer.id === selectedLayerId;
              const isEditing = layer.id === editingLayerId;
              const actualIndex = layers.length - 1 - index;

              return (
                <div
                  key={layer.id}
                  className={`group relative flex items-center gap-2 p-2 rounded-lg cursor-pointer transition-colors ${
                    isSelected
                      ? "bg-accent-500/10 border border-accent-500/30"
                      : "hover:bg-muted border border-transparent"
                  } ${!layer.visible ? "opacity-50" : ""}`}
                  onClick={() => !layer.locked && onSelectLayer(layer.id)}
                >
                  {/* Drag Handle */}
                  <div className="text-muted-foreground cursor-grab">
                    <GripVertical className="w-4 h-4" />
                  </div>

                  {/* Layer Icon */}
                  <div
                    className={`w-8 h-8 rounded-lg flex items-center justify-center text-xs font-bold ${
                      isSelected
                        ? "bg-accent-500 text-white"
                        : "bg-muted text-muted-foreground"
                    }`}
                  >
                    <Type className="w-4 h-4" />
                  </div>

                  {/* Layer Name */}
                  <div className="flex-1 min-w-0">
                    {isEditing ? (
                      <input
                        type="text"
                        value={editingName}
                        onChange={(e) => setEditingName(e.target.value)}
                        onBlur={handleFinishEditing}
                        onKeyDown={handleKeyDown}
                        className="w-full bg-transparent border-b border-accent-500 outline-none text-sm py-0.5"
                        autoFocus
                      />
                    ) : (
                      <div
                        className="text-sm font-medium text-foreground truncate"
                        onDoubleClick={() => handleStartEditing(layer)}
                        title={layer.name}
                      >
                        {layer.name}
                      </div>
                    )}
                    <div className="text-xs text-muted-foreground truncate">
                      {layer.text.substring(0, 20)}
                      {layer.text.length > 20 ? "..." : ""}
                    </div>
                  </div>

                  {/* Layer Controls */}
                  <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onToggleVisibility(layer.id);
                      }}
                      className="p-1 rounded hover:bg-muted-foreground/10 transition-colors"
                      title={layer.visible ? "숨기기" : "보이기"}
                    >
                      {layer.visible ? (
                        <Eye className="w-3.5 h-3.5 text-muted-foreground" />
                      ) : (
                        <EyeOff className="w-3.5 h-3.5 text-muted-foreground" />
                      )}
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onToggleLock(layer.id);
                      }}
                      className="p-1 rounded hover:bg-muted-foreground/10 transition-colors"
                      title={layer.locked ? "잠금 해제" : "잠금"}
                    >
                      {layer.locked ? (
                        <Lock className="w-3.5 h-3.5 text-muted-foreground" />
                      ) : (
                        <Unlock className="w-3.5 h-3.5 text-muted-foreground" />
                      )}
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Layer Actions */}
      {selectedLayerId && (
        <div className="border-t border-default p-3">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-muted-foreground">레이어 작업</span>
          </div>

          {/* Ordering Controls */}
          <div className="flex items-center gap-1 mb-2">
            <button
              onClick={() => onBringToFront(selectedLayerId)}
              className="flex-1 flex items-center justify-center gap-1 px-2 py-1.5 text-xs rounded-lg bg-muted hover:bg-muted-foreground/10 transition-colors"
              title="맨 앞으로"
            >
              <ChevronsUp className="w-3.5 h-3.5" />
              맨 앞
            </button>
            <button
              onClick={() => onMoveLayerUp(selectedLayerId)}
              className="flex-1 flex items-center justify-center gap-1 px-2 py-1.5 text-xs rounded-lg bg-muted hover:bg-muted-foreground/10 transition-colors"
              title="앞으로"
            >
              <ChevronUp className="w-3.5 h-3.5" />
              앞으로
            </button>
            <button
              onClick={() => onMoveLayerDown(selectedLayerId)}
              className="flex-1 flex items-center justify-center gap-1 px-2 py-1.5 text-xs rounded-lg bg-muted hover:bg-muted-foreground/10 transition-colors"
              title="뒤로"
            >
              <ChevronDown className="w-3.5 h-3.5" />
              뒤로
            </button>
            <button
              onClick={() => onSendToBack(selectedLayerId)}
              className="flex-1 flex items-center justify-center gap-1 px-2 py-1.5 text-xs rounded-lg bg-muted hover:bg-muted-foreground/10 transition-colors"
              title="맨 뒤로"
            >
              <ChevronsDown className="w-3.5 h-3.5" />
              맨 뒤
            </button>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => onDuplicateLayer(selectedLayerId)}
              className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 text-xs font-medium rounded-lg bg-muted hover:bg-muted-foreground/10 transition-colors"
              title="복제"
            >
              <Copy className="w-3.5 h-3.5" />
              복제
            </button>
            <button
              onClick={() => {
                onRemoveLayer(selectedLayerId);
                onSelectLayer(null);
              }}
              className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 text-xs font-medium rounded-lg bg-red-500/10 text-red-500 hover:bg-red-500/20 transition-colors"
              title="삭제"
            >
              <Trash2 className="w-3.5 h-3.5" />
              삭제
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
