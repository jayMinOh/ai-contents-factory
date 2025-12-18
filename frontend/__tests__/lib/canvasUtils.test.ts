import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import {
  generateLayerId,
  generateLayerName,
  serializeCanvasState,
  parseCanvasState,
  saveCanvasToLocalStorage,
  loadCanvasFromLocalStorage,
  clamp,
  hexToRgba,
  isTransparent,
  createInitialCanvasState,
} from "@/lib/canvas/canvasUtils";
import type { CanvasState, TextLayer } from "@/types/canvas";

describe("canvasUtils", () => {
  describe("generateLayerId", () => {
    it("should generate unique IDs", () => {
      const id1 = generateLayerId();
      const id2 = generateLayerId();

      expect(id1).not.toBe(id2);
      expect(id1).toMatch(/^layer_\d+_[a-z0-9]+$/);
    });

    it("should start with 'layer_' prefix", () => {
      const id = generateLayerId();
      expect(id.startsWith("layer_")).toBe(true);
    });
  });

  describe("generateLayerName", () => {
    it("should generate '텍스트 1' for empty array", () => {
      const name = generateLayerName([]);
      expect(name).toBe("텍스트 1");
    });

    it("should increment count based on existing text layers", () => {
      const existingLayers: TextLayer[] = [
        { name: "텍스트 1" } as TextLayer,
        { name: "텍스트 2" } as TextLayer,
      ];
      const name = generateLayerName(existingLayers);
      expect(name).toBe("텍스트 3");
    });

    it("should handle mixed layer names", () => {
      const existingLayers: TextLayer[] = [
        { name: "텍스트 1" } as TextLayer,
        { name: "Custom Layer" } as TextLayer,
      ];
      const name = generateLayerName(existingLayers);
      expect(name).toBe("텍스트 2");
    });
  });

  describe("serializeCanvasState", () => {
    it("should serialize canvas state to JSON string", () => {
      const state: CanvasState = {
        version: "1.0.0",
        width: 1080,
        height: 1080,
        backgroundColor: "#ffffff",
        backgroundImage: null,
        layers: [],
        objects: [],
      };

      const json = serializeCanvasState(state);
      expect(typeof json).toBe("string");
      expect(JSON.parse(json)).toEqual(state);
    });
  });

  describe("parseCanvasState", () => {
    it("should parse valid JSON to canvas state", () => {
      const validJson = JSON.stringify({
        version: "1.0.0",
        width: 1080,
        height: 1080,
        backgroundColor: "#ffffff",
        backgroundImage: null,
        layers: [],
        objects: [],
      });

      const state = parseCanvasState(validJson);
      expect(state).not.toBeNull();
      expect(state?.version).toBe("1.0.0");
      expect(state?.width).toBe(1080);
    });

    it("should return null for invalid JSON", () => {
      const invalidJson = "not valid json";
      const state = parseCanvasState(invalidJson);
      expect(state).toBeNull();
    });

    it("should return null for JSON missing required fields", () => {
      const incompleteJson = JSON.stringify({ width: 100 });
      const state = parseCanvasState(incompleteJson);
      expect(state).toBeNull();
    });
  });

  describe("localStorage functions", () => {
    const mockLocalStorage: Record<string, string> = {};

    beforeEach(() => {
      vi.spyOn(Storage.prototype, "setItem").mockImplementation(
        (key, value) => {
          mockLocalStorage[key] = value;
        }
      );
      vi.spyOn(Storage.prototype, "getItem").mockImplementation(
        (key) => mockLocalStorage[key] || null
      );
    });

    afterEach(() => {
      vi.restoreAllMocks();
    });

    it("should save canvas state to localStorage", () => {
      const state: CanvasState = {
        version: "1.0.0",
        width: 1080,
        height: 1080,
        backgroundColor: "#ffffff",
        backgroundImage: null,
        layers: [],
        objects: [],
      };

      const result = saveCanvasToLocalStorage("test-key", state);
      expect(result).toBe(true);
      expect(mockLocalStorage["test-key"]).toBeDefined();
    });

    it("should load canvas state from localStorage", () => {
      const state: CanvasState = {
        version: "1.0.0",
        width: 1080,
        height: 1080,
        backgroundColor: "#ffffff",
        backgroundImage: null,
        layers: [],
        objects: [],
      };

      saveCanvasToLocalStorage("test-key", state);
      const loaded = loadCanvasFromLocalStorage("test-key");

      expect(loaded).toEqual(state);
    });

    it("should return null for non-existent key", () => {
      const loaded = loadCanvasFromLocalStorage("non-existent-key");
      expect(loaded).toBeNull();
    });
  });

  describe("clamp", () => {
    it("should return value within bounds", () => {
      expect(clamp(5, 0, 10)).toBe(5);
    });

    it("should clamp to minimum", () => {
      expect(clamp(-5, 0, 10)).toBe(0);
    });

    it("should clamp to maximum", () => {
      expect(clamp(15, 0, 10)).toBe(10);
    });

    it("should handle edge cases", () => {
      expect(clamp(0, 0, 10)).toBe(0);
      expect(clamp(10, 0, 10)).toBe(10);
    });
  });

  describe("hexToRgba", () => {
    it("should convert hex to rgba", () => {
      expect(hexToRgba("#ffffff", 1)).toBe("rgba(255, 255, 255, 1)");
      expect(hexToRgba("#000000", 0.5)).toBe("rgba(0, 0, 0, 0.5)");
    });

    it("should handle hex without #", () => {
      expect(hexToRgba("ff0000", 1)).toBe("rgba(255, 0, 0, 1)");
    });

    it("should return original value for invalid hex", () => {
      expect(hexToRgba("invalid", 1)).toBe("invalid");
    });
  });

  describe("isTransparent", () => {
    it("should return true for transparent values", () => {
      expect(isTransparent("")).toBe(true);
      expect(isTransparent("transparent")).toBe(true);
      expect(isTransparent("rgba(0,0,0,0)")).toBe(true);
      expect(isTransparent("rgba(0, 0, 0, 0)")).toBe(true);
    });

    it("should return false for non-transparent values", () => {
      expect(isTransparent("#ffffff")).toBe(false);
      expect(isTransparent("rgba(0,0,0,1)")).toBe(false);
      expect(isTransparent("red")).toBe(false);
    });
  });

  describe("createInitialCanvasState", () => {
    it("should create initial state with default values", () => {
      const state = createInitialCanvasState(1080, 1080);

      expect(state.version).toBe("1.0.0");
      expect(state.width).toBe(1080);
      expect(state.height).toBe(1080);
      expect(state.backgroundColor).toBe("#1a1f2e");
      expect(state.backgroundImage).toBeNull();
      expect(state.layers).toEqual([]);
      expect(state.objects).toEqual([]);
    });

    it("should allow custom background color", () => {
      const state = createInitialCanvasState(1920, 1080, "#ffffff");

      expect(state.backgroundColor).toBe("#ffffff");
      expect(state.width).toBe(1920);
      expect(state.height).toBe(1080);
    });
  });
});
