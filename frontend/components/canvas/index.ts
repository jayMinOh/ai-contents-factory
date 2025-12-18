/**
 * Canvas Components Index
 * Phase 5 & 6: Canvas Text Editor and Platform Export for SPEC-CONTENT-FACTORY-001
 */

export { default as FabricCanvas } from "./FabricCanvas";
export { default as TextToolbar } from "./TextToolbar";
export { default as LayerPanel } from "./LayerPanel";
export { default as CanvasExportPanel } from "./CanvasExportPanel";
export { default as CanvasTextEditor } from "./CanvasTextEditor";

// Phase 6: Platform Export Components
export { default as PlatformPresets, PlatformPresetsCompact } from "./PlatformPresets";
export { default as BatchExportModal } from "./BatchExportModal";
export type { BatchExportProgressCallback } from "./BatchExportModal";

// Types
export type { FabricCanvasRef } from "./FabricCanvas";
