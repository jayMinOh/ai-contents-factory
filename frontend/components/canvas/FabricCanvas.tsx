"use client";

/**
 * FabricCanvas Component
 * TAG-FE-001: Fabric.js Canvas Component Setup
 *
 * Reusable canvas component with Fabric.js integration
 * Handles canvas initialization, cleanup, and responsive sizing
 */

import React, {
  useRef,
  useEffect,
  useState,
  useCallback,
  forwardRef,
  useImperativeHandle,
} from "react";
import { Canvas, IText, FabricImage, Shadow } from "fabric";
import type {
  TextLayer,
  CanvasState,
  CanvasCallbacks,
  ExportOptions,
} from "@/types/canvas";
import {
  generateLayerId,
  generateLayerName,
  createInitialCanvasState,
  exportCanvasToDataUrl,
  downloadCanvasAsImage,
  downloadCanvasAsJson,
} from "@/lib/canvas/canvasUtils";
import { useCanvasHistory } from "@/lib/canvas/useCanvasHistory";
import { DEFAULT_TEXT_LAYER } from "@/types/canvas";

export interface FabricCanvasRef {
  addTextLayer: () => TextLayer;
  removeLayer: (layerId: string) => void;
  duplicateLayer: (layerId: string) => TextLayer | null;
  updateLayer: (layerId: string, updates: Partial<TextLayer>) => void;
  selectLayer: (layerId: string | null) => void;
  moveLayerUp: (layerId: string) => void;
  moveLayerDown: (layerId: string) => void;
  bringToFront: (layerId: string) => void;
  sendToBack: (layerId: string) => void;
  toggleLayerVisibility: (layerId: string) => void;
  toggleLayerLock: (layerId: string) => void;
  getCanvasState: () => CanvasState;
  loadCanvasState: (state: CanvasState) => void;
  exportAsImage: (options: ExportOptions) => string;
  downloadImage: (filename: string, options: ExportOptions) => void;
  downloadJson: (filename: string) => void;
  undo: () => void;
  redo: () => void;
  canUndo: boolean;
  canRedo: boolean;
  clearCanvas: () => void;
  setBackgroundImage: (imageUrl: string) => Promise<void>;
  setBackgroundColor: (color: string) => void;
  getLayers: () => TextLayer[];
  getSelectedLayer: () => TextLayer | null;
}

interface FabricCanvasProps {
  width: number;
  height: number;
  backgroundColor?: string;
  backgroundImage?: string;
  callbacks?: CanvasCallbacks;
  className?: string;
}

const FabricCanvas = forwardRef<FabricCanvasRef, FabricCanvasProps>(
  (
    {
      width,
      height,
      backgroundColor = "#1a1f2e",
      backgroundImage,
      callbacks,
      className = "",
    },
    ref
  ) => {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const containerRef = useRef<HTMLDivElement>(null);
    const fabricRef = useRef<Canvas | null>(null);
    const layersRef = useRef<Map<string, IText>>(new Map());
    const layerDataRef = useRef<Map<string, TextLayer>>(new Map());

    const [layers, setLayers] = useState<TextLayer[]>([]);
    const [selectedLayerId, setSelectedLayerId] = useState<string | null>(null);
    const [isCanvasReady, setIsCanvasReady] = useState(false);
    const [scale, setScale] = useState(1);

    const history = useCanvasHistory(
      createInitialCanvasState(width, height, backgroundColor)
    );

    // Fabric object to layer data conversion
    const fabricObjectToLayerData = useCallback(
      (obj: IText, existingLayer?: TextLayer): Partial<TextLayer> => {
        const shadow = obj.shadow as Shadow | null;
        return {
          text: obj.text || "",
          fontFamily: obj.fontFamily || "Noto Sans KR, sans-serif",
          fontSize: obj.fontSize || 32,
          fontWeight: (obj.fontWeight as "normal" | "bold") || "normal",
          fontStyle: (obj.fontStyle as "normal" | "italic") || "normal",
          textAlign: (obj.textAlign as "left" | "center" | "right") || "center",
          fill: (obj.fill as string) || "#ffffff",
          backgroundColor: (obj.backgroundColor as string) || "transparent",
          shadow: shadow
            ? {
                color: shadow.color || "#000000",
                blur: shadow.blur || 0,
                offsetX: shadow.offsetX || 0,
                offsetY: shadow.offsetY || 0,
              }
            : null,
          position: {
            x: obj.left || 0,
            y: obj.top || 0,
          },
          rotation: obj.angle || 0,
          scaleX: obj.scaleX || 1,
          scaleY: obj.scaleY || 1,
          opacity: obj.opacity || 1,
          underline: obj.underline || false,
          linethrough: obj.linethrough || false,
          charSpacing: obj.charSpacing || 0,
          lineHeight: obj.lineHeight || 1.2,
        };
      },
      []
    );

    // Update layer data from fabric object
    const syncLayerFromFabric = useCallback(
      (layerId: string) => {
        const fabricObj = layersRef.current.get(layerId);
        const existingData = layerDataRef.current.get(layerId);

        if (fabricObj && existingData) {
          const updates = fabricObjectToLayerData(fabricObj, existingData);
          const updatedLayer = { ...existingData, ...updates };
          layerDataRef.current.set(layerId, updatedLayer);

          setLayers((prev) =>
            prev.map((l) => (l.id === layerId ? updatedLayer : l))
          );

          callbacks?.onLayerUpdate?.(updatedLayer);
        }
      },
      [fabricObjectToLayerData, callbacks]
    );

    // Save current state to history
    const saveToHistory = useCallback(() => {
      const state = getCanvasStateInternal();
      history.pushState(state);
      callbacks?.onHistoryChange?.(history.canUndo, history.canRedo);
    }, [history, callbacks]);

    // Get canvas state (internal)
    const getCanvasStateInternal = useCallback((): CanvasState => {
      const canvas = fabricRef.current;
      const currentLayers = Array.from(layerDataRef.current.values());

      return {
        version: "1.0.0",
        width,
        height,
        backgroundColor:
          (canvas?.backgroundColor as string) || backgroundColor,
        backgroundImage: backgroundImage || null,
        layers: currentLayers,
        objects: canvas ? canvas.toJSON().objects : [],
      };
    }, [width, height, backgroundColor, backgroundImage]);

    // Initialize canvas
    useEffect(() => {
      if (!canvasRef.current || fabricRef.current) return;

      const canvas = new Canvas(canvasRef.current, {
        width,
        height,
        backgroundColor,
        selection: true,
        preserveObjectStacking: true,
      });

      fabricRef.current = canvas;

      // Set up event listeners
      canvas.on("selection:created", (e) => {
        const selected = e.selected?.[0];
        if (selected) {
          const layerId = (selected as IText & { layerId?: string }).layerId;
          if (layerId) {
            setSelectedLayerId(layerId);
            const layer = layerDataRef.current.get(layerId);
            callbacks?.onLayerSelect?.(layer || null);
          }
        }
      });

      canvas.on("selection:updated", (e) => {
        const selected = e.selected?.[0];
        if (selected) {
          const layerId = (selected as IText & { layerId?: string }).layerId;
          if (layerId) {
            setSelectedLayerId(layerId);
            const layer = layerDataRef.current.get(layerId);
            callbacks?.onLayerSelect?.(layer || null);
          }
        }
      });

      canvas.on("selection:cleared", () => {
        setSelectedLayerId(null);
        callbacks?.onLayerSelect?.(null);
      });

      canvas.on("object:modified", (e) => {
        const target = e.target as IText & { layerId?: string };
        if (target?.layerId) {
          syncLayerFromFabric(target.layerId);
          saveToHistory();
        }
      });

      canvas.on("text:changed", (e) => {
        const target = e.target as IText & { layerId?: string };
        if (target?.layerId) {
          syncLayerFromFabric(target.layerId);
        }
      });

      canvas.on("text:editing:exited", () => {
        saveToHistory();
      });

      setIsCanvasReady(true);
      callbacks?.onCanvasReady?.();

      return () => {
        canvas.dispose();
        fabricRef.current = null;
        layersRef.current.clear();
        layerDataRef.current.clear();
      };
    }, []);

    // Update canvas dimensions
    useEffect(() => {
      if (fabricRef.current && isCanvasReady) {
        fabricRef.current.setDimensions({ width, height });
        fabricRef.current.renderAll();
      }
    }, [width, height, isCanvasReady]);

    // Update background color
    useEffect(() => {
      if (fabricRef.current && isCanvasReady) {
        fabricRef.current.backgroundColor = backgroundColor;
        fabricRef.current.renderAll();
      }
    }, [backgroundColor, isCanvasReady]);

    // Load background image
    useEffect(() => {
      if (fabricRef.current && isCanvasReady && backgroundImage) {
        FabricImage.fromURL(backgroundImage).then((img) => {
          const canvas = fabricRef.current;
          if (!canvas) return;

          // Scale image to fit canvas
          const scaleX = width / (img.width || 1);
          const scaleY = height / (img.height || 1);
          const scale = Math.max(scaleX, scaleY);

          img.scale(scale);
          img.set({
            left: width / 2,
            top: height / 2,
            originX: "center",
            originY: "center",
          });

          canvas.backgroundImage = img;
          canvas.renderAll();
        });
      }
    }, [backgroundImage, width, height, isCanvasReady]);

    // Handle responsive scaling
    useEffect(() => {
      const updateScale = () => {
        if (!containerRef.current) return;

        const containerWidth = containerRef.current.clientWidth;
        const containerHeight = containerRef.current.clientHeight;

        const scaleX = containerWidth / width;
        const scaleY = containerHeight / height;
        const newScale = Math.min(scaleX, scaleY, 1);

        setScale(newScale);
      };

      updateScale();
      window.addEventListener("resize", updateScale);
      return () => window.removeEventListener("resize", updateScale);
    }, [width, height]);

    // Add text layer
    const addTextLayer = useCallback((): TextLayer => {
      const canvas = fabricRef.current;
      if (!canvas) throw new Error("Canvas not initialized");

      const existingLayers = Array.from(layerDataRef.current.values());
      const layerId = generateLayerId();
      const layerName = generateLayerName(existingLayers);

      const text = new IText(DEFAULT_TEXT_LAYER.text, {
        left: width / 2,
        top: height / 2,
        originX: "center",
        originY: "center",
        fontFamily: DEFAULT_TEXT_LAYER.fontFamily,
        fontSize: DEFAULT_TEXT_LAYER.fontSize,
        fontWeight: DEFAULT_TEXT_LAYER.fontWeight,
        fontStyle: DEFAULT_TEXT_LAYER.fontStyle,
        textAlign: DEFAULT_TEXT_LAYER.textAlign,
        fill: DEFAULT_TEXT_LAYER.fill,
        backgroundColor: DEFAULT_TEXT_LAYER.backgroundColor,
      });

      // Add custom property for layer tracking
      (text as IText & { layerId: string }).layerId = layerId;

      const layerData: TextLayer = {
        ...DEFAULT_TEXT_LAYER,
        id: layerId,
        name: layerName,
        position: { x: width / 2, y: height / 2 },
      };

      layersRef.current.set(layerId, text);
      layerDataRef.current.set(layerId, layerData);

      canvas.add(text);
      canvas.setActiveObject(text);
      canvas.renderAll();

      setLayers((prev) => [...prev, layerData]);
      setSelectedLayerId(layerId);
      saveToHistory();

      return layerData;
    }, [width, height, saveToHistory]);

    // Remove layer
    const removeLayer = useCallback(
      (layerId: string) => {
        const canvas = fabricRef.current;
        const fabricObj = layersRef.current.get(layerId);

        if (canvas && fabricObj) {
          canvas.remove(fabricObj);
          layersRef.current.delete(layerId);
          layerDataRef.current.delete(layerId);

          setLayers((prev) => prev.filter((l) => l.id !== layerId));

          if (selectedLayerId === layerId) {
            setSelectedLayerId(null);
            callbacks?.onLayerSelect?.(null);
          }

          canvas.renderAll();
          saveToHistory();
        }
      },
      [selectedLayerId, callbacks, saveToHistory]
    );

    // Duplicate layer
    const duplicateLayer = useCallback(
      (layerId: string): TextLayer | null => {
        const originalData = layerDataRef.current.get(layerId);
        if (!originalData) return null;

        const newLayerId = generateLayerId();
        const newLayerName = `${originalData.name} 복사본`;

        const newLayerData: TextLayer = {
          ...originalData,
          id: newLayerId,
          name: newLayerName,
          position: {
            x: originalData.position.x + 20,
            y: originalData.position.y + 20,
          },
        };

        const canvas = fabricRef.current;
        if (!canvas) return null;

        const text = new IText(newLayerData.text, {
          left: newLayerData.position.x,
          top: newLayerData.position.y,
          originX: "center",
          originY: "center",
          fontFamily: newLayerData.fontFamily,
          fontSize: newLayerData.fontSize,
          fontWeight: newLayerData.fontWeight,
          fontStyle: newLayerData.fontStyle,
          textAlign: newLayerData.textAlign,
          fill: newLayerData.fill,
          backgroundColor: newLayerData.backgroundColor,
          angle: newLayerData.rotation,
          scaleX: newLayerData.scaleX,
          scaleY: newLayerData.scaleY,
          opacity: newLayerData.opacity,
        });

        (text as IText & { layerId: string }).layerId = newLayerId;

        layersRef.current.set(newLayerId, text);
        layerDataRef.current.set(newLayerId, newLayerData);

        canvas.add(text);
        canvas.setActiveObject(text);
        canvas.renderAll();

        setLayers((prev) => [...prev, newLayerData]);
        setSelectedLayerId(newLayerId);
        saveToHistory();

        return newLayerData;
      },
      [saveToHistory]
    );

    // Update layer
    const updateLayer = useCallback(
      (layerId: string, updates: Partial<TextLayer>) => {
        const fabricObj = layersRef.current.get(layerId);
        const existingData = layerDataRef.current.get(layerId);

        if (!fabricObj || !existingData) return;

        // Update fabric object
        if (updates.text !== undefined) fabricObj.set("text", updates.text);
        if (updates.fontFamily !== undefined)
          fabricObj.set("fontFamily", updates.fontFamily);
        if (updates.fontSize !== undefined)
          fabricObj.set("fontSize", updates.fontSize);
        if (updates.fontWeight !== undefined)
          fabricObj.set("fontWeight", updates.fontWeight);
        if (updates.fontStyle !== undefined)
          fabricObj.set("fontStyle", updates.fontStyle);
        if (updates.textAlign !== undefined)
          fabricObj.set("textAlign", updates.textAlign);
        if (updates.fill !== undefined) fabricObj.set("fill", updates.fill);
        if (updates.backgroundColor !== undefined)
          fabricObj.set("backgroundColor", updates.backgroundColor);
        if (updates.rotation !== undefined)
          fabricObj.set("angle", updates.rotation);
        if (updates.scaleX !== undefined)
          fabricObj.set("scaleX", updates.scaleX);
        if (updates.scaleY !== undefined)
          fabricObj.set("scaleY", updates.scaleY);
        if (updates.opacity !== undefined)
          fabricObj.set("opacity", updates.opacity);
        if (updates.visible !== undefined)
          fabricObj.set("visible", updates.visible);
        if (updates.underline !== undefined)
          fabricObj.set("underline", updates.underline);
        if (updates.linethrough !== undefined)
          fabricObj.set("linethrough", updates.linethrough);
        if (updates.charSpacing !== undefined)
          fabricObj.set("charSpacing", updates.charSpacing);
        if (updates.lineHeight !== undefined)
          fabricObj.set("lineHeight", updates.lineHeight);

        if (updates.position !== undefined) {
          fabricObj.set("left", updates.position.x);
          fabricObj.set("top", updates.position.y);
        }

        if (updates.shadow !== undefined) {
          if (updates.shadow) {
            fabricObj.set(
              "shadow",
              new Shadow({
                color: updates.shadow.color,
                blur: updates.shadow.blur,
                offsetX: updates.shadow.offsetX,
                offsetY: updates.shadow.offsetY,
              })
            );
          } else {
            fabricObj.set("shadow", null);
          }
        }

        if (updates.locked !== undefined) {
          fabricObj.set("selectable", !updates.locked);
          fabricObj.set("evented", !updates.locked);
        }

        // Update layer data
        const updatedLayer = { ...existingData, ...updates };
        layerDataRef.current.set(layerId, updatedLayer);
        setLayers((prev) =>
          prev.map((l) => (l.id === layerId ? updatedLayer : l))
        );

        fabricRef.current?.renderAll();
        callbacks?.onLayerUpdate?.(updatedLayer);
      },
      [callbacks]
    );

    // Select layer
    const selectLayer = useCallback(
      (layerId: string | null) => {
        const canvas = fabricRef.current;
        if (!canvas) return;

        if (layerId) {
          const fabricObj = layersRef.current.get(layerId);
          if (fabricObj) {
            canvas.setActiveObject(fabricObj);
            canvas.renderAll();
            setSelectedLayerId(layerId);
            const layer = layerDataRef.current.get(layerId);
            callbacks?.onLayerSelect?.(layer || null);
          }
        } else {
          canvas.discardActiveObject();
          canvas.renderAll();
          setSelectedLayerId(null);
          callbacks?.onLayerSelect?.(null);
        }
      },
      [callbacks]
    );

    // Layer ordering functions
    const moveLayerUp = useCallback(
      (layerId: string) => {
        const canvas = fabricRef.current;
        const fabricObj = layersRef.current.get(layerId);
        if (canvas && fabricObj) {
          const objects = canvas.getObjects();
          const index = objects.indexOf(fabricObj);
          if (index < objects.length - 1) {
            canvas.moveObjectTo(fabricObj, index + 1);
            canvas.renderAll();
            saveToHistory();
          }
        }
      },
      [saveToHistory]
    );

    const moveLayerDown = useCallback(
      (layerId: string) => {
        const canvas = fabricRef.current;
        const fabricObj = layersRef.current.get(layerId);
        if (canvas && fabricObj) {
          const objects = canvas.getObjects();
          const index = objects.indexOf(fabricObj);
          if (index > 0) {
            canvas.moveObjectTo(fabricObj, index - 1);
            canvas.renderAll();
            saveToHistory();
          }
        }
      },
      [saveToHistory]
    );

    const bringToFront = useCallback(
      (layerId: string) => {
        const canvas = fabricRef.current;
        const fabricObj = layersRef.current.get(layerId);
        if (canvas && fabricObj) {
          canvas.bringObjectToFront(fabricObj);
          canvas.renderAll();
          saveToHistory();
        }
      },
      [saveToHistory]
    );

    const sendToBack = useCallback(
      (layerId: string) => {
        const canvas = fabricRef.current;
        const fabricObj = layersRef.current.get(layerId);
        if (canvas && fabricObj) {
          canvas.sendObjectToBack(fabricObj);
          canvas.renderAll();
          saveToHistory();
        }
      },
      [saveToHistory]
    );

    const toggleLayerVisibility = useCallback(
      (layerId: string) => {
        const data = layerDataRef.current.get(layerId);
        if (data) {
          updateLayer(layerId, { visible: !data.visible });
          saveToHistory();
        }
      },
      [updateLayer, saveToHistory]
    );

    const toggleLayerLock = useCallback(
      (layerId: string) => {
        const data = layerDataRef.current.get(layerId);
        if (data) {
          updateLayer(layerId, { locked: !data.locked });
          saveToHistory();
        }
      },
      [updateLayer, saveToHistory]
    );

    // Export functions
    const exportAsImage = useCallback(
      (options: ExportOptions): string => {
        const canvas = fabricRef.current;
        if (!canvas) return "";

        const dataUrl = canvas.toDataURL({
          format: options.format === "jpeg" ? "jpeg" : "png",
          quality: options.quality || 0.92,
          multiplier: options.multiplier || 1,
        });

        return dataUrl;
      },
      []
    );

    const downloadImage = useCallback(
      (filename: string, options: ExportOptions) => {
        const dataUrl = exportAsImage(options);
        downloadCanvasAsImage(dataUrl, filename, options.format);
      },
      [exportAsImage]
    );

    const downloadJson = useCallback(
      (filename: string) => {
        const state = getCanvasStateInternal();
        downloadCanvasAsJson(state, filename);
      },
      [getCanvasStateInternal]
    );

    // Load canvas state
    const loadCanvasState = useCallback(
      (state: CanvasState) => {
        const canvas = fabricRef.current;
        if (!canvas) return;

        // Clear existing objects
        canvas.clear();
        layersRef.current.clear();
        layerDataRef.current.clear();

        // Set background
        canvas.backgroundColor = state.backgroundColor;

        // Load background image if exists
        if (state.backgroundImage) {
          FabricImage.fromURL(state.backgroundImage).then((img) => {
            const scaleX = width / (img.width || 1);
            const scaleY = height / (img.height || 1);
            const scale = Math.max(scaleX, scaleY);

            img.scale(scale);
            img.set({
              left: width / 2,
              top: height / 2,
              originX: "center",
              originY: "center",
            });

            canvas.backgroundImage = img;
            canvas.renderAll();
          });
        }

        // Load layers
        state.layers.forEach((layerData) => {
          const text = new IText(layerData.text, {
            left: layerData.position.x,
            top: layerData.position.y,
            originX: "center",
            originY: "center",
            fontFamily: layerData.fontFamily,
            fontSize: layerData.fontSize,
            fontWeight: layerData.fontWeight,
            fontStyle: layerData.fontStyle,
            textAlign: layerData.textAlign,
            fill: layerData.fill,
            backgroundColor: layerData.backgroundColor,
            angle: layerData.rotation,
            scaleX: layerData.scaleX,
            scaleY: layerData.scaleY,
            opacity: layerData.opacity,
            visible: layerData.visible,
            selectable: !layerData.locked,
            evented: !layerData.locked,
            underline: layerData.underline,
            linethrough: layerData.linethrough,
            charSpacing: layerData.charSpacing,
            lineHeight: layerData.lineHeight,
          });

          if (layerData.shadow) {
            text.set(
              "shadow",
              new Shadow({
                color: layerData.shadow.color,
                blur: layerData.shadow.blur,
                offsetX: layerData.shadow.offsetX,
                offsetY: layerData.shadow.offsetY,
              })
            );
          }

          (text as IText & { layerId: string }).layerId = layerData.id;

          layersRef.current.set(layerData.id, text);
          layerDataRef.current.set(layerData.id, layerData);

          canvas.add(text);
        });

        setLayers(state.layers);
        canvas.renderAll();
      },
      [width, height]
    );

    // Undo/Redo
    const undo = useCallback(() => {
      const prevState = history.undo();
      if (prevState) {
        loadCanvasState(prevState);
        callbacks?.onHistoryChange?.(history.canUndo, history.canRedo);
      }
    }, [history, loadCanvasState, callbacks]);

    const redo = useCallback(() => {
      const nextState = history.redo();
      if (nextState) {
        loadCanvasState(nextState);
        callbacks?.onHistoryChange?.(history.canUndo, history.canRedo);
      }
    }, [history, loadCanvasState, callbacks]);

    // Clear canvas
    const clearCanvas = useCallback(() => {
      const canvas = fabricRef.current;
      if (!canvas) return;

      canvas.clear();
      canvas.backgroundColor = backgroundColor;
      layersRef.current.clear();
      layerDataRef.current.clear();
      setLayers([]);
      setSelectedLayerId(null);
      canvas.renderAll();
      saveToHistory();
    }, [backgroundColor, saveToHistory]);

    // Set background image
    const setBackgroundImage = useCallback(
      async (imageUrl: string) => {
        const canvas = fabricRef.current;
        if (!canvas) return;

        const img = await FabricImage.fromURL(imageUrl);
        const scaleX = width / (img.width || 1);
        const scaleY = height / (img.height || 1);
        const scale = Math.max(scaleX, scaleY);

        img.scale(scale);
        img.set({
          left: width / 2,
          top: height / 2,
          originX: "center",
          originY: "center",
        });

        canvas.backgroundImage = img;
        canvas.renderAll();
        saveToHistory();
      },
      [width, height, saveToHistory]
    );

    // Set background color
    const setBackgroundColorHandler = useCallback(
      (color: string) => {
        const canvas = fabricRef.current;
        if (!canvas) return;

        canvas.backgroundColor = color;
        canvas.renderAll();
        saveToHistory();
      },
      [saveToHistory]
    );

    // Expose methods via ref
    useImperativeHandle(
      ref,
      () => ({
        addTextLayer,
        removeLayer,
        duplicateLayer,
        updateLayer,
        selectLayer,
        moveLayerUp,
        moveLayerDown,
        bringToFront,
        sendToBack,
        toggleLayerVisibility,
        toggleLayerLock,
        getCanvasState: getCanvasStateInternal,
        loadCanvasState,
        exportAsImage,
        downloadImage,
        downloadJson,
        undo,
        redo,
        canUndo: history.canUndo,
        canRedo: history.canRedo,
        clearCanvas,
        setBackgroundImage,
        setBackgroundColor: setBackgroundColorHandler,
        getLayers: () => layers,
        getSelectedLayer: () =>
          selectedLayerId ? layerDataRef.current.get(selectedLayerId) || null : null,
      }),
      [
        addTextLayer,
        removeLayer,
        duplicateLayer,
        updateLayer,
        selectLayer,
        moveLayerUp,
        moveLayerDown,
        bringToFront,
        sendToBack,
        toggleLayerVisibility,
        toggleLayerLock,
        getCanvasStateInternal,
        loadCanvasState,
        exportAsImage,
        downloadImage,
        downloadJson,
        undo,
        redo,
        history.canUndo,
        history.canRedo,
        clearCanvas,
        setBackgroundImage,
        setBackgroundColorHandler,
        layers,
        selectedLayerId,
      ]
    );

    return (
      <div
        ref={containerRef}
        className={`relative flex items-center justify-center overflow-hidden ${className}`}
      >
        <div
          style={{
            transform: `scale(${scale})`,
            transformOrigin: "center center",
          }}
        >
          <canvas ref={canvasRef} />
        </div>
      </div>
    );
  }
);

FabricCanvas.displayName = "FabricCanvas";

export default FabricCanvas;
