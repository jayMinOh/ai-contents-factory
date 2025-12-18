/**
 * Canvas Text Editor Types
 * Phase 5: SPEC-CONTENT-FACTORY-001
 */

import type { Object as FabricObject, TOptions } from "fabric";

// Text layer configuration
export interface TextLayer {
  id: string;
  name: string;
  text: string;
  fontFamily: string;
  fontSize: number;
  fontWeight: "normal" | "bold";
  fontStyle: "normal" | "italic";
  textAlign: "left" | "center" | "right";
  fill: string;
  backgroundColor: string;
  shadow: TextShadow | null;
  position: Position;
  rotation: number;
  scaleX: number;
  scaleY: number;
  visible: boolean;
  locked: boolean;
  opacity: number;
  underline: boolean;
  linethrough: boolean;
  charSpacing: number;
  lineHeight: number;
}

export interface TextShadow {
  color: string;
  blur: number;
  offsetX: number;
  offsetY: number;
}

export interface Position {
  x: number;
  y: number;
}

// Canvas state for persistence
export interface CanvasState {
  version: string;
  width: number;
  height: number;
  backgroundColor: string;
  backgroundImage: string | null;
  layers: TextLayer[];
  objects: object[];
}

// History state for undo/redo
export interface HistoryState {
  past: CanvasState[];
  present: CanvasState | null;
  future: CanvasState[];
}

// Font configuration
export interface FontOption {
  name: string;
  family: string;
  category: "system" | "google" | "custom";
  weights: number[];
}

// Predefined fonts
export const SYSTEM_FONTS: FontOption[] = [
  { name: "Arial", family: "Arial, sans-serif", category: "system", weights: [400, 700] },
  { name: "Helvetica", family: "Helvetica, sans-serif", category: "system", weights: [400, 700] },
  { name: "Georgia", family: "Georgia, serif", category: "system", weights: [400, 700] },
  { name: "Times New Roman", family: "Times New Roman, serif", category: "system", weights: [400, 700] },
  { name: "Courier New", family: "Courier New, monospace", category: "system", weights: [400, 700] },
  { name: "Impact", family: "Impact, sans-serif", category: "system", weights: [400] },
];

export const GOOGLE_FONTS: FontOption[] = [
  { name: "Noto Sans KR", family: "Noto Sans KR, sans-serif", category: "google", weights: [400, 500, 700] },
  { name: "Pretendard", family: "Pretendard, sans-serif", category: "google", weights: [400, 500, 600, 700] },
  { name: "Roboto", family: "Roboto, sans-serif", category: "google", weights: [400, 500, 700] },
  { name: "Open Sans", family: "Open Sans, sans-serif", category: "google", weights: [400, 600, 700] },
  { name: "Montserrat", family: "Montserrat, sans-serif", category: "google", weights: [400, 500, 600, 700] },
  { name: "Poppins", family: "Poppins, sans-serif", category: "google", weights: [400, 500, 600, 700] },
  { name: "Lato", family: "Lato, sans-serif", category: "google", weights: [400, 700] },
  { name: "Playfair Display", family: "Playfair Display, serif", category: "google", weights: [400, 700] },
];

export const ALL_FONTS: FontOption[] = [...SYSTEM_FONTS, ...GOOGLE_FONTS];

// Export format options
export type ExportFormat = "png" | "jpeg" | "json";

export interface ExportOptions {
  format: ExportFormat;
  quality?: number; // 0-1 for jpeg
  multiplier?: number; // Scale factor for high-res export
}

// Canvas tool modes
export type CanvasToolMode = "select" | "text" | "pan";

// Layer action types
export type LayerAction =
  | "add"
  | "remove"
  | "duplicate"
  | "moveUp"
  | "moveDown"
  | "toFront"
  | "toBack"
  | "toggleVisibility"
  | "toggleLock";

// Canvas event callbacks
export interface CanvasCallbacks {
  onLayerSelect?: (layer: TextLayer | null) => void;
  onLayerUpdate?: (layer: TextLayer) => void;
  onHistoryChange?: (canUndo: boolean, canRedo: boolean) => void;
  onCanvasReady?: () => void;
}

// Default text layer configuration
export const DEFAULT_TEXT_LAYER: Omit<TextLayer, "id" | "name"> = {
  text: "텍스트 입력",
  fontFamily: "Noto Sans KR, sans-serif",
  fontSize: 32,
  fontWeight: "normal",
  fontStyle: "normal",
  textAlign: "center",
  fill: "#ffffff",
  backgroundColor: "transparent",
  shadow: null,
  position: { x: 0, y: 0 },
  rotation: 0,
  scaleX: 1,
  scaleY: 1,
  visible: true,
  locked: false,
  opacity: 1,
  underline: false,
  linethrough: false,
  charSpacing: 0,
  lineHeight: 1.2,
};

// Canvas size presets
export interface CanvasSizePreset {
  name: string;
  width: number;
  height: number;
  aspectRatio: string;
}

export const CANVAS_SIZE_PRESETS: CanvasSizePreset[] = [
  { name: "Instagram 정사각형", width: 1080, height: 1080, aspectRatio: "1:1" },
  { name: "Instagram 세로", width: 1080, height: 1350, aspectRatio: "4:5" },
  { name: "Instagram 스토리", width: 1080, height: 1920, aspectRatio: "9:16" },
  { name: "Facebook 게시물", width: 1200, height: 630, aspectRatio: "1.91:1" },
  { name: "Twitter 게시물", width: 1200, height: 675, aspectRatio: "16:9" },
  { name: "YouTube 썸네일", width: 1280, height: 720, aspectRatio: "16:9" },
];

// TAG-EX-001: Platform-Specific Dimension Presets
// Social media platform categories for export
export type PlatformCategory =
  | "instagram"
  | "facebook"
  | "pinterest"
  | "twitter"
  | "youtube"
  | "linkedin";

// Platform export preset configuration
export interface PlatformExportPreset {
  id: string;
  platform: PlatformCategory;
  name: string;
  description: string;
  width: number;
  height: number;
  aspectRatio: string;
  icon: string;
}

// Platform configuration with brand colors
export interface PlatformConfig {
  id: PlatformCategory;
  name: string;
  brandColor: string;
  presets: PlatformExportPreset[];
}

// TAG-EX-002: Export quality options
export type ImageExportFormat = "png" | "jpeg" | "webp";

export interface ImageExportOptions {
  format: ImageExportFormat;
  quality: number; // 1-100 percentage
  multiplier: 1 | 2 | 3; // Resolution multiplier for retina
  transparentBackground: boolean; // PNG only
}

// TAG-EX-003: Batch export configuration
export interface BatchExportItem {
  preset: PlatformExportPreset;
  selected: boolean;
}

export interface BatchExportConfig {
  items: BatchExportItem[];
  exportOptions: ImageExportOptions;
}

export interface BatchExportProgress {
  current: number;
  total: number;
  currentPreset: string;
  status: "idle" | "exporting" | "zipping" | "complete" | "error";
  error?: string;
}

export interface ExportedImage {
  filename: string;
  blob: Blob;
  preset: PlatformExportPreset;
}

// Platform presets data
export const PLATFORM_EXPORT_PRESETS: PlatformConfig[] = [
  {
    id: "instagram",
    name: "Instagram",
    brandColor: "#E4405F",
    presets: [
      {
        id: "ig-feed",
        platform: "instagram",
        name: "Feed",
        description: "정사각형 피드 게시물",
        width: 1080,
        height: 1080,
        aspectRatio: "1:1",
        icon: "square",
      },
      {
        id: "ig-portrait",
        platform: "instagram",
        name: "Portrait",
        description: "세로형 피드 게시물",
        width: 1080,
        height: 1350,
        aspectRatio: "4:5",
        icon: "rectangle-vertical",
      },
      {
        id: "ig-landscape",
        platform: "instagram",
        name: "Landscape",
        description: "가로형 피드 게시물",
        width: 1080,
        height: 566,
        aspectRatio: "1.91:1",
        icon: "rectangle-horizontal",
      },
      {
        id: "ig-story",
        platform: "instagram",
        name: "Story/Reels",
        description: "스토리 및 릴스",
        width: 1080,
        height: 1920,
        aspectRatio: "9:16",
        icon: "smartphone",
      },
    ],
  },
  {
    id: "facebook",
    name: "Facebook",
    brandColor: "#1877F2",
    presets: [
      {
        id: "fb-link",
        platform: "facebook",
        name: "Link",
        description: "링크 공유 이미지",
        width: 1200,
        height: 628,
        aspectRatio: "1.91:1",
        icon: "link",
      },
      {
        id: "fb-share",
        platform: "facebook",
        name: "Share",
        description: "공유 이미지",
        width: 1200,
        height: 630,
        aspectRatio: "1.91:1",
        icon: "share-2",
      },
      {
        id: "fb-post",
        platform: "facebook",
        name: "Post",
        description: "정사각형 게시물",
        width: 1080,
        height: 1080,
        aspectRatio: "1:1",
        icon: "square",
      },
    ],
  },
  {
    id: "pinterest",
    name: "Pinterest",
    brandColor: "#E60023",
    presets: [
      {
        id: "pin-standard",
        platform: "pinterest",
        name: "Pin",
        description: "표준 핀 이미지",
        width: 1000,
        height: 1500,
        aspectRatio: "2:3",
        icon: "bookmark",
      },
      {
        id: "pin-square",
        platform: "pinterest",
        name: "Square",
        description: "정사각형 핀",
        width: 1000,
        height: 1000,
        aspectRatio: "1:1",
        icon: "square",
      },
    ],
  },
  {
    id: "twitter",
    name: "Twitter/X",
    brandColor: "#000000",
    presets: [
      {
        id: "tw-link",
        platform: "twitter",
        name: "Link",
        description: "링크 카드 이미지",
        width: 1600,
        height: 900,
        aspectRatio: "16:9",
        icon: "link",
      },
      {
        id: "tw-summary",
        platform: "twitter",
        name: "Summary",
        description: "요약 카드 이미지",
        width: 1200,
        height: 675,
        aspectRatio: "16:9",
        icon: "file-text",
      },
    ],
  },
  {
    id: "youtube",
    name: "YouTube",
    brandColor: "#FF0000",
    presets: [
      {
        id: "yt-thumbnail",
        platform: "youtube",
        name: "Thumbnail",
        description: "영상 썸네일",
        width: 1280,
        height: 720,
        aspectRatio: "16:9",
        icon: "play",
      },
    ],
  },
  {
    id: "linkedin",
    name: "LinkedIn",
    brandColor: "#0A66C2",
    presets: [
      {
        id: "li-link",
        platform: "linkedin",
        name: "Link",
        description: "링크 공유 이미지",
        width: 1200,
        height: 627,
        aspectRatio: "1.91:1",
        icon: "link",
      },
      {
        id: "li-image",
        platform: "linkedin",
        name: "Image",
        description: "이미지 게시물",
        width: 1104,
        height: 736,
        aspectRatio: "3:2",
        icon: "image",
      },
    ],
  },
];

// Default export options
export const DEFAULT_IMAGE_EXPORT_OPTIONS: ImageExportOptions = {
  format: "png",
  quality: 92,
  multiplier: 1,
  transparentBackground: false,
};
