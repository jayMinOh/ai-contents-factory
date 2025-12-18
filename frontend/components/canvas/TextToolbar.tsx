"use client";

/**
 * TextToolbar Component
 * TAG-FE-002: Text Overlay Tools
 *
 * Provides text editing controls:
 * - Font selection (system + web fonts)
 * - Font size slider (12-120px)
 * - Color picker (text color, background color)
 * - Text alignment (left, center, right)
 * - Font weight (normal, bold)
 * - Text shadow options
 */

import React, { useState, useEffect, useCallback } from "react";
import {
  Type,
  Bold,
  Italic,
  AlignLeft,
  AlignCenter,
  AlignRight,
  Underline,
  Strikethrough,
  Palette,
  Sun,
  Minus,
  Plus,
  ChevronDown,
} from "lucide-react";
import type { TextLayer, TextShadow, FontOption } from "@/types/canvas";
import { ALL_FONTS } from "@/types/canvas";

interface TextToolbarProps {
  selectedLayer: TextLayer | null;
  onUpdate: (updates: Partial<TextLayer>) => void;
  className?: string;
}

export default function TextToolbar({
  selectedLayer,
  onUpdate,
  className = "",
}: TextToolbarProps) {
  const [showFontDropdown, setShowFontDropdown] = useState(false);
  const [showColorPicker, setShowColorPicker] = useState<
    "text" | "background" | "shadow" | null
  >(null);
  const [showShadowPanel, setShowShadowPanel] = useState(false);

  // Close dropdowns when clicking outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      if (!target.closest(".toolbar-dropdown")) {
        setShowFontDropdown(false);
        setShowColorPicker(null);
        setShowShadowPanel(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleFontChange = useCallback(
    (font: FontOption) => {
      onUpdate({ fontFamily: font.family });
      setShowFontDropdown(false);
    },
    [onUpdate]
  );

  const handleFontSizeChange = useCallback(
    (delta: number) => {
      if (!selectedLayer) return;
      const newSize = Math.max(12, Math.min(120, selectedLayer.fontSize + delta));
      onUpdate({ fontSize: newSize });
    },
    [selectedLayer, onUpdate]
  );

  const handleFontSizeInput = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const value = parseInt(e.target.value) || 32;
      const newSize = Math.max(12, Math.min(120, value));
      onUpdate({ fontSize: newSize });
    },
    [onUpdate]
  );

  const toggleBold = useCallback(() => {
    if (!selectedLayer) return;
    onUpdate({
      fontWeight: selectedLayer.fontWeight === "bold" ? "normal" : "bold",
    });
  }, [selectedLayer, onUpdate]);

  const toggleItalic = useCallback(() => {
    if (!selectedLayer) return;
    onUpdate({
      fontStyle: selectedLayer.fontStyle === "italic" ? "normal" : "italic",
    });
  }, [selectedLayer, onUpdate]);

  const toggleUnderline = useCallback(() => {
    if (!selectedLayer) return;
    onUpdate({ underline: !selectedLayer.underline });
  }, [selectedLayer, onUpdate]);

  const toggleLinethrough = useCallback(() => {
    if (!selectedLayer) return;
    onUpdate({ linethrough: !selectedLayer.linethrough });
  }, [selectedLayer, onUpdate]);

  const handleAlignChange = useCallback(
    (align: "left" | "center" | "right") => {
      onUpdate({ textAlign: align });
    },
    [onUpdate]
  );

  const handleColorChange = useCallback(
    (color: string, type: "text" | "background" | "shadow") => {
      if (type === "text") {
        onUpdate({ fill: color });
      } else if (type === "background") {
        onUpdate({ backgroundColor: color === "" ? "transparent" : color });
      } else if (type === "shadow" && selectedLayer?.shadow) {
        onUpdate({
          shadow: { ...selectedLayer.shadow, color },
        });
      }
    },
    [selectedLayer, onUpdate]
  );

  const handleShadowChange = useCallback(
    (updates: Partial<TextShadow>) => {
      if (!selectedLayer) return;

      if (selectedLayer.shadow) {
        onUpdate({
          shadow: { ...selectedLayer.shadow, ...updates },
        });
      } else {
        onUpdate({
          shadow: {
            color: "#000000",
            blur: 4,
            offsetX: 2,
            offsetY: 2,
            ...updates,
          },
        });
      }
    },
    [selectedLayer, onUpdate]
  );

  const toggleShadow = useCallback(() => {
    if (!selectedLayer) return;

    if (selectedLayer.shadow) {
      onUpdate({ shadow: null });
    } else {
      onUpdate({
        shadow: {
          color: "#000000",
          blur: 4,
          offsetX: 2,
          offsetY: 2,
        },
      });
    }
  }, [selectedLayer, onUpdate]);

  const handleOpacityChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const value = parseInt(e.target.value) / 100;
      onUpdate({ opacity: value });
    },
    [onUpdate]
  );

  if (!selectedLayer) {
    return (
      <div
        className={`flex items-center justify-center py-4 px-6 text-muted text-sm ${className}`}
      >
        텍스트 레이어를 선택하세요
      </div>
    );
  }

  // Get current font name
  const currentFontName =
    ALL_FONTS.find((f) => f.family === selectedLayer.fontFamily)?.name ||
    "Noto Sans KR";

  // Predefined colors
  const colorPresets = [
    "#ffffff",
    "#000000",
    "#f97316",
    "#a855f7",
    "#06b6d4",
    "#22c55e",
    "#ef4444",
    "#eab308",
    "#3b82f6",
    "#ec4899",
    "#64748b",
    "#1e293b",
  ];

  return (
    <div className={`flex flex-wrap items-center gap-2 p-3 ${className}`}>
      {/* Font Family Selector */}
      <div className="relative toolbar-dropdown">
        <button
          onClick={() => setShowFontDropdown(!showFontDropdown)}
          className="flex items-center gap-2 px-3 py-2 rounded-lg bg-muted/50 hover:bg-muted border border-default text-sm font-medium transition-colors min-w-[140px]"
        >
          <Type className="w-4 h-4 text-muted-foreground" />
          <span className="truncate">{currentFontName}</span>
          <ChevronDown className="w-4 h-4 text-muted-foreground ml-auto" />
        </button>

        {showFontDropdown && (
          <div className="absolute top-full left-0 mt-2 w-56 max-h-64 overflow-y-auto rounded-xl bg-card border border-default shadow-lg z-50 animate-fade-in">
            <div className="p-2">
              <div className="text-xs font-medium text-muted-foreground px-2 py-1 mb-1">
                시스템 폰트
              </div>
              {ALL_FONTS.filter((f) => f.category === "system").map((font) => (
                <button
                  key={font.family}
                  onClick={() => handleFontChange(font)}
                  className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${
                    selectedLayer.fontFamily === font.family
                      ? "bg-accent-500/10 text-accent-500"
                      : "hover:bg-muted text-foreground"
                  }`}
                  style={{ fontFamily: font.family }}
                >
                  {font.name}
                </button>
              ))}

              <div className="divider my-2" />

              <div className="text-xs font-medium text-muted-foreground px-2 py-1 mb-1">
                웹 폰트
              </div>
              {ALL_FONTS.filter((f) => f.category === "google").map((font) => (
                <button
                  key={font.family}
                  onClick={() => handleFontChange(font)}
                  className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${
                    selectedLayer.fontFamily === font.family
                      ? "bg-accent-500/10 text-accent-500"
                      : "hover:bg-muted text-foreground"
                  }`}
                  style={{ fontFamily: font.family }}
                >
                  {font.name}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Divider */}
      <div className="w-px h-6 bg-border mx-1" />

      {/* Font Size */}
      <div className="flex items-center gap-1">
        <button
          onClick={() => handleFontSizeChange(-2)}
          className="p-2 rounded-lg hover:bg-muted transition-colors"
          title="글자 크기 줄이기"
        >
          <Minus className="w-4 h-4" />
        </button>
        <input
          type="number"
          value={selectedLayer.fontSize}
          onChange={handleFontSizeInput}
          min={12}
          max={120}
          className="w-14 text-center py-1.5 rounded-lg bg-muted/50 border border-default text-sm"
        />
        <button
          onClick={() => handleFontSizeChange(2)}
          className="p-2 rounded-lg hover:bg-muted transition-colors"
          title="글자 크기 늘리기"
        >
          <Plus className="w-4 h-4" />
        </button>
      </div>

      {/* Divider */}
      <div className="w-px h-6 bg-border mx-1" />

      {/* Text Style Buttons */}
      <div className="flex items-center gap-1">
        <button
          onClick={toggleBold}
          className={`p-2 rounded-lg transition-colors ${
            selectedLayer.fontWeight === "bold"
              ? "bg-accent-500/20 text-accent-500"
              : "hover:bg-muted"
          }`}
          title="굵게 (Bold)"
        >
          <Bold className="w-4 h-4" />
        </button>
        <button
          onClick={toggleItalic}
          className={`p-2 rounded-lg transition-colors ${
            selectedLayer.fontStyle === "italic"
              ? "bg-accent-500/20 text-accent-500"
              : "hover:bg-muted"
          }`}
          title="기울임 (Italic)"
        >
          <Italic className="w-4 h-4" />
        </button>
        <button
          onClick={toggleUnderline}
          className={`p-2 rounded-lg transition-colors ${
            selectedLayer.underline
              ? "bg-accent-500/20 text-accent-500"
              : "hover:bg-muted"
          }`}
          title="밑줄 (Underline)"
        >
          <Underline className="w-4 h-4" />
        </button>
        <button
          onClick={toggleLinethrough}
          className={`p-2 rounded-lg transition-colors ${
            selectedLayer.linethrough
              ? "bg-accent-500/20 text-accent-500"
              : "hover:bg-muted"
          }`}
          title="취소선 (Strikethrough)"
        >
          <Strikethrough className="w-4 h-4" />
        </button>
      </div>

      {/* Divider */}
      <div className="w-px h-6 bg-border mx-1" />

      {/* Text Alignment */}
      <div className="flex items-center gap-1">
        <button
          onClick={() => handleAlignChange("left")}
          className={`p-2 rounded-lg transition-colors ${
            selectedLayer.textAlign === "left"
              ? "bg-accent-500/20 text-accent-500"
              : "hover:bg-muted"
          }`}
          title="왼쪽 정렬"
        >
          <AlignLeft className="w-4 h-4" />
        </button>
        <button
          onClick={() => handleAlignChange("center")}
          className={`p-2 rounded-lg transition-colors ${
            selectedLayer.textAlign === "center"
              ? "bg-accent-500/20 text-accent-500"
              : "hover:bg-muted"
          }`}
          title="가운데 정렬"
        >
          <AlignCenter className="w-4 h-4" />
        </button>
        <button
          onClick={() => handleAlignChange("right")}
          className={`p-2 rounded-lg transition-colors ${
            selectedLayer.textAlign === "right"
              ? "bg-accent-500/20 text-accent-500"
              : "hover:bg-muted"
          }`}
          title="오른쪽 정렬"
        >
          <AlignRight className="w-4 h-4" />
        </button>
      </div>

      {/* Divider */}
      <div className="w-px h-6 bg-border mx-1" />

      {/* Text Color */}
      <div className="relative toolbar-dropdown">
        <button
          onClick={() =>
            setShowColorPicker(showColorPicker === "text" ? null : "text")
          }
          className="p-2 rounded-lg hover:bg-muted transition-colors flex items-center gap-1"
          title="글자 색상"
        >
          <Palette className="w-4 h-4" />
          <div
            className="w-4 h-4 rounded border border-default"
            style={{ backgroundColor: selectedLayer.fill }}
          />
        </button>

        {showColorPicker === "text" && (
          <div className="absolute top-full left-0 mt-2 p-3 rounded-xl bg-card border border-default shadow-lg z-50 animate-fade-in">
            <div className="text-xs font-medium text-muted-foreground mb-2">
              글자 색상
            </div>
            <div className="grid grid-cols-6 gap-1.5 mb-3">
              {colorPresets.map((color) => (
                <button
                  key={color}
                  onClick={() => handleColorChange(color, "text")}
                  className={`w-6 h-6 rounded border transition-transform hover:scale-110 ${
                    selectedLayer.fill === color
                      ? "ring-2 ring-accent-500 ring-offset-1"
                      : "border-default"
                  }`}
                  style={{ backgroundColor: color }}
                />
              ))}
            </div>
            <input
              type="color"
              value={selectedLayer.fill}
              onChange={(e) => handleColorChange(e.target.value, "text")}
              className="w-full h-8 rounded cursor-pointer"
            />
          </div>
        )}
      </div>

      {/* Background Color */}
      <div className="relative toolbar-dropdown">
        <button
          onClick={() =>
            setShowColorPicker(
              showColorPicker === "background" ? null : "background"
            )
          }
          className="p-2 rounded-lg hover:bg-muted transition-colors flex items-center gap-1"
          title="배경 색상"
        >
          <div
            className="w-5 h-5 rounded border border-default flex items-center justify-center"
            style={{
              backgroundColor:
                selectedLayer.backgroundColor === "transparent"
                  ? "transparent"
                  : selectedLayer.backgroundColor,
            }}
          >
            {selectedLayer.backgroundColor === "transparent" && (
              <span className="text-xs text-muted-foreground">-</span>
            )}
          </div>
        </button>

        {showColorPicker === "background" && (
          <div className="absolute top-full left-0 mt-2 p-3 rounded-xl bg-card border border-default shadow-lg z-50 animate-fade-in">
            <div className="text-xs font-medium text-muted-foreground mb-2">
              배경 색상
            </div>
            <div className="grid grid-cols-6 gap-1.5 mb-3">
              <button
                onClick={() => handleColorChange("", "background")}
                className={`w-6 h-6 rounded border transition-transform hover:scale-110 ${
                  selectedLayer.backgroundColor === "transparent"
                    ? "ring-2 ring-accent-500 ring-offset-1"
                    : "border-default"
                }`}
                title="투명"
              >
                <span className="text-xs text-muted-foreground">-</span>
              </button>
              {colorPresets.slice(0, 11).map((color) => (
                <button
                  key={color}
                  onClick={() => handleColorChange(color, "background")}
                  className={`w-6 h-6 rounded border transition-transform hover:scale-110 ${
                    selectedLayer.backgroundColor === color
                      ? "ring-2 ring-accent-500 ring-offset-1"
                      : "border-default"
                  }`}
                  style={{ backgroundColor: color }}
                />
              ))}
            </div>
            <input
              type="color"
              value={
                selectedLayer.backgroundColor === "transparent"
                  ? "#ffffff"
                  : selectedLayer.backgroundColor
              }
              onChange={(e) => handleColorChange(e.target.value, "background")}
              className="w-full h-8 rounded cursor-pointer"
            />
          </div>
        )}
      </div>

      {/* Divider */}
      <div className="w-px h-6 bg-border mx-1" />

      {/* Text Shadow */}
      <div className="relative toolbar-dropdown">
        <button
          onClick={() => setShowShadowPanel(!showShadowPanel)}
          className={`p-2 rounded-lg transition-colors ${
            selectedLayer.shadow
              ? "bg-accent-500/20 text-accent-500"
              : "hover:bg-muted"
          }`}
          title="그림자"
        >
          <Sun className="w-4 h-4" />
        </button>

        {showShadowPanel && (
          <div className="absolute top-full right-0 mt-2 p-4 w-64 rounded-xl bg-card border border-default shadow-lg z-50 animate-fade-in">
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm font-medium text-foreground">
                텍스트 그림자
              </span>
              <button
                onClick={toggleShadow}
                className={`px-3 py-1 text-xs rounded-full transition-colors ${
                  selectedLayer.shadow
                    ? "bg-accent-500 text-white"
                    : "bg-muted text-muted-foreground"
                }`}
              >
                {selectedLayer.shadow ? "ON" : "OFF"}
              </button>
            </div>

            {selectedLayer.shadow && (
              <div className="space-y-4">
                {/* Shadow Color */}
                <div>
                  <label className="text-xs text-muted-foreground mb-1 block">
                    색상
                  </label>
                  <div className="flex items-center gap-2">
                    <input
                      type="color"
                      value={selectedLayer.shadow.color}
                      onChange={(e) =>
                        handleShadowChange({ color: e.target.value })
                      }
                      className="w-8 h-8 rounded cursor-pointer"
                    />
                    <span className="text-xs text-muted-foreground">
                      {selectedLayer.shadow.color}
                    </span>
                  </div>
                </div>

                {/* Blur */}
                <div>
                  <label className="text-xs text-muted-foreground mb-1 block">
                    흐림: {selectedLayer.shadow.blur}px
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="50"
                    value={selectedLayer.shadow.blur}
                    onChange={(e) =>
                      handleShadowChange({ blur: parseInt(e.target.value) })
                    }
                    className="w-full accent-accent-500"
                  />
                </div>

                {/* Offset X */}
                <div>
                  <label className="text-xs text-muted-foreground mb-1 block">
                    가로 오프셋: {selectedLayer.shadow.offsetX}px
                  </label>
                  <input
                    type="range"
                    min="-50"
                    max="50"
                    value={selectedLayer.shadow.offsetX}
                    onChange={(e) =>
                      handleShadowChange({ offsetX: parseInt(e.target.value) })
                    }
                    className="w-full accent-accent-500"
                  />
                </div>

                {/* Offset Y */}
                <div>
                  <label className="text-xs text-muted-foreground mb-1 block">
                    세로 오프셋: {selectedLayer.shadow.offsetY}px
                  </label>
                  <input
                    type="range"
                    min="-50"
                    max="50"
                    value={selectedLayer.shadow.offsetY}
                    onChange={(e) =>
                      handleShadowChange({ offsetY: parseInt(e.target.value) })
                    }
                    className="w-full accent-accent-500"
                  />
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Divider */}
      <div className="w-px h-6 bg-border mx-1" />

      {/* Opacity */}
      <div className="flex items-center gap-2">
        <span className="text-xs text-muted-foreground">투명도</span>
        <input
          type="range"
          min="0"
          max="100"
          value={Math.round(selectedLayer.opacity * 100)}
          onChange={handleOpacityChange}
          className="w-20 accent-accent-500"
        />
        <span className="text-xs text-muted-foreground w-8">
          {Math.round(selectedLayer.opacity * 100)}%
        </span>
      </div>
    </div>
  );
}
