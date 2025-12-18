"use client";

import { useState, useRef, useCallback, useEffect, useMemo } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import Image from "next/image";
import {
  ChevronRight,
  ChevronUp,
  ChevronDown,
  Check,
  Building2,
  Package,
  Video,
  Upload,
  LayoutGrid,
  Wand2,
  Play,
  Clock,
  Eye,
  Image as ImageIcon,
  RefreshCw,
  Sparkles,
  X,
  Loader2,
  Plus,
  Trash2,
  Edit3,
  Save,
  Music,
  Type,
  FileText,
  Palette,
  ArrowRight,
  GripVertical,
  History,
} from "lucide-react";
import { brandApi, referenceApi, studioApi } from "@/lib/api";
import { toast } from "sonner";
import type {
  Brand,
  Product,
  AnalysisResult,
  TimelineSegment,
  VideoProject,
  SceneImage,
  Storyboard,
  Scene,
  SceneUpdateRequest,
  SceneCreateRequest,
  StoryboardGenerateRequest,
  VideoGenerationStatus,
  SceneVideoStatus,
  ExtendedVideoGenerationStatus,
  ExtendedVideoGenerationResponse,
} from "@/lib/api";

// Scene asset type for Step 3
interface SceneAsset {
  sceneIndex: number;
  id: string | null;  // Scene image ID from backend (after save)
  imageUrl: string | null;  // Preview URL (temp) or permanent URL (after save)
  source: "uploaded" | "ai_generated" | null;
  isGenerating: boolean;
  file?: File;
  // Temp data (before save to DB)
  temp_id?: string;
  filename?: string;
  generation_prompt?: string;
  generation_provider?: string;
  generation_duration_ms?: number;
}

// Transition effect options
const TRANSITION_EFFECTS = [
  { value: "cut", label: "Cut (즉시 전환)" },
  { value: "fade", label: "Fade (페이드)" },
  { value: "dissolve", label: "Dissolve (디졸브)" },
  { value: "wipe", label: "Wipe (와이프)" },
  { value: "slide", label: "Slide (슬라이드)" },
  { value: "zoom", label: "Zoom (줌)" },
  { value: "blur", label: "Blur (블러)" },
];

// Scene type options
const SCENE_TYPES = [
  { value: "hook", label: "Hook (후킹)" },
  { value: "intro", label: "Intro (인트로)" },
  { value: "problem", label: "Problem (문제 제기)" },
  { value: "solution", label: "Solution (해결책)" },
  { value: "product_showcase", label: "Product Showcase (제품 소개)" },
  { value: "feature", label: "Feature (기능 설명)" },
  { value: "benefit", label: "Benefit (효능/혜택)" },
  { value: "social_proof", label: "Social Proof (사회적 증거)" },
  { value: "testimonial", label: "Testimonial (고객 후기)" },
  { value: "demonstration", label: "Demonstration (시연)" },
  { value: "comparison", label: "Comparison (비교)" },
  { value: "cta", label: "CTA (행동 유도)" },
  { value: "outro", label: "Outro (아웃트로)" },
  { value: "transition", label: "Transition (전환)" },
  { value: "other", label: "Other (기타)" },
];

// Step definitions (5-step creative workflow)
const STEPS = [
  { id: 1, title: "브랜드/제품", icon: Building2, description: "브랜드와 제품 선택" },
  { id: 2, title: "레퍼런스", icon: Video, description: "참고 영상 + 포인트 선택" },
  { id: 3, title: "창작 입력", icon: Edit3, description: "컨셉 + 참고 이미지" },
  { id: 4, title: "스토리보드", icon: LayoutGrid, description: "AI 스토리보드 생성" },
  { id: 5, title: "영상 제작", icon: Play, description: "장면 편집 + 영상 생성" },
];

// Studio mode type
type StudioMode = null | "video" | "image";

// Image production state types
interface ImageAnalysis {
  detected_type: string;
  is_realistic: boolean;
  description: string;
  elements: string[];
}

interface UploadedImage {
  id: string;
  file: File;
  previewUrl: string;
  tempId?: string;  // Server-side temp ID for API calls
  isUploading: boolean;
  analysis?: ImageAnalysis;  // Analysis result from backend
}

// Selected reference points for storyboard generation
interface SelectedReferencePoints {
  useStructure: boolean;  // Use the overall structure/framework
  useFlow: boolean;  // Use the flow sequence
  selectedHookPoints: number[];  // Indices of selected hook points
  selectedSegments: number[];  // Indices of selected segments to reference
  selectedSellingPoints: number[];  // Indices of selected selling points
  useCTAStyle: boolean;  // Use CTA style
  selectedEmotionalTriggers: number[];  // Indices of selected emotional triggers
}

// Creative input for Step 3
interface ReferenceImage {
  id: string;
  file: File;
  previewUrl: string;
  type: "product" | "background" | "mood" | "other";
  tempId?: string;
  isUploading: boolean;
}

interface CreativeInput {
  concept: string;  // User's creative concept/request
  targetDuration: number;  // Target video duration in seconds
  mood: string;  // Video mood/atmosphere
  style: string;  // Visual style
  additionalNotes: string;  // Any additional notes
}

// Mood options for video
const MOOD_OPTIONS = [
  { value: "energetic", label: "에너지틱/활기찬" },
  { value: "calm", label: "차분한/평화로운" },
  { value: "luxurious", label: "럭셔리/고급스러운" },
  { value: "friendly", label: "친근한/따뜻한" },
  { value: "professional", label: "전문적인/신뢰감" },
  { value: "playful", label: "재미있는/유쾌한" },
  { value: "emotional", label: "감성적인/감동적인" },
  { value: "minimal", label: "미니멀/깔끔한" },
];

// Style options for video
const STYLE_OPTIONS = [
  { value: "cinematic", label: "시네마틱" },
  { value: "documentary", label: "다큐멘터리" },
  { value: "commercial", label: "광고/커머셜" },
  { value: "social_media", label: "SNS/숏폼" },
  { value: "tutorial", label: "튜토리얼/가이드" },
  { value: "storytelling", label: "스토리텔링" },
  { value: "product_focus", label: "제품 중심" },
  { value: "lifestyle", label: "라이프스타일" },
];

export default function StudioPage() {
  // Studio mode selection state
  const [studioMode, setStudioMode] = useState<StudioMode>(null);

  // Video production state (existing)
  const [currentStep, setCurrentStep] = useState(1);
  const [selectedBrandId, setSelectedBrandId] = useState<string | null>(null);
  const [selectedProductId, setSelectedProductId] = useState<string | null>(null);
  const [selectedReferenceId, setSelectedReferenceId] = useState<string | null>(null);
  const [selectedReferencePoints, setSelectedReferencePoints] = useState<SelectedReferencePoints>({
    useStructure: true,
    useFlow: true,
    selectedHookPoints: [],
    selectedSegments: [],
    selectedSellingPoints: [],
    useCTAStyle: true,
    selectedEmotionalTriggers: [],
  });

  // Creative input state (Step 3)
  const [creativeInput, setCreativeInput] = useState<CreativeInput>({
    concept: "",
    targetDuration: 30,
    mood: "professional",
    style: "commercial",
    additionalNotes: "",
  });
  const [referenceImages, setReferenceImages] = useState<ReferenceImage[]>([]);
  const referenceImageInputRef = useRef<HTMLInputElement | null>(null);

  const [sceneAssets, setSceneAssets] = useState<SceneAsset[]>([]);
  const [projectId, setProjectId] = useState<string | null>(null);
  const [isCreatingProject, setIsCreatingProject] = useState(false);
  const fileInputRefs = useRef<{ [key: number]: HTMLInputElement | null }>({});
  const queryClient = useQueryClient();

  // Storyboard state (Step 4)
  const [storyboard, setStoryboard] = useState<Storyboard | null>(null);
  const [selectedSceneNumber, setSelectedSceneNumber] = useState<number | null>(null);
  const [isGeneratingStoryboard, setIsGeneratingStoryboard] = useState(false);
  const [isProcessingNext, setIsProcessingNext] = useState(false);
  const [showGenerateModal, setShowGenerateModal] = useState(false);
  const [showAddSceneModal, setShowAddSceneModal] = useState(false);
  const [editingField, setEditingField] = useState<string | null>(null);
  const [pendingUpdates, setPendingUpdates] = useState<SceneUpdateRequest>({});
  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Image production state (new)
  const [uploadedImages, setUploadedImages] = useState<UploadedImage[]>([]);
  const [imagePrompt, setImagePrompt] = useState("");
  const [generatedImageUrl, setGeneratedImageUrl] = useState<string | null>(null);
  const [isAnalyzingImages, setIsAnalyzingImages] = useState(false);
  const [isGeneratingImage, setIsGeneratingImage] = useState(false);
  const [showLightbox, setShowLightbox] = useState(false);
  const imageInputRef = useRef<HTMLInputElement | null>(null);

  // Video generation state (Step 5)
  const [videoGenerationStatus, setVideoGenerationStatus] = useState<VideoGenerationStatus | null>(null);
  const [isGeneratingVideo, setIsGeneratingVideo] = useState(false);
  const [generatedVideoUrl, setGeneratedVideoUrl] = useState<string | null>(null);
  const videoPollingRef = useRef<NodeJS.Timeout | null>(null);

  // Per-scene video generation state (Step 5) - fallback mode
  const [sceneVideos, setSceneVideos] = useState<SceneVideoStatus[]>([]);
  const [concatenationStatus, setConcatenationStatus] = useState<"idle" | "processing" | "completed" | "failed">("idle");
  const [isConcatenating, setIsConcatenating] = useState(false);
  const sceneVideoPollingRefs = useRef<{ [key: number]: NodeJS.Timeout | null }>({});

  // Extended video generation state (Scene Extension - primary mode)
  const [extendedVideoStatus, setExtendedVideoStatus] = useState<ExtendedVideoGenerationResponse | null>(null);
  const [useExtendedMode, setUseExtendedMode] = useState(true); // Default to Scene Extension mode
  const extendedVideoPollingRef = useRef<NodeJS.Timeout | null>(null);

  // Fetch brands
  const { data: brands = [], isLoading: brandsLoading } = useQuery({
    queryKey: ["brands"],
    queryFn: brandApi.list,
  });

  // Fetch products for selected brand
  const { data: products = [], isLoading: productsLoading } = useQuery({
    queryKey: ["products", selectedBrandId],
    queryFn: () => brandApi.listProducts(selectedBrandId!),
    enabled: !!selectedBrandId,
  });

  // Fetch reference analyses
  const { data: references = [], isLoading: referencesLoading } = useQuery({
    queryKey: ["references"],
    queryFn: referenceApi.listAnalyses,
  });

  const selectedBrand = brands.find((b) => b.id === selectedBrandId);
  const selectedProduct = products.find((p) => p.id === selectedProductId);
  const selectedReference = references.find((r) => r.analysis_id === selectedReferenceId);

  const canProceedToStep2 = selectedBrandId && selectedProductId;
  const canProceedToStep3 = canProceedToStep2 && selectedReferenceId;
  const canProceedToStep4 = canProceedToStep3 && creativeInput.concept.trim().length > 0;
  const canProceedToStep5 = canProceedToStep4 && storyboard && storyboard.scenes.length > 0;

  // Selected scene from storyboard
  const selectedScene = useMemo(() => {
    if (!storyboard || selectedSceneNumber === null) return null;
    return storyboard.scenes.find((s) => s.scene_number === selectedSceneNumber) || null;
  }, [storyboard, selectedSceneNumber]);

  // Total duration calculation
  const totalDuration = useMemo(() => {
    if (!storyboard) return 0;
    return storyboard.scenes.reduce((sum, scene) => sum + (scene.duration_seconds || 0), 0);
  }, [storyboard]);

  // Get image URL for a scene from sceneAssets (by array index, not scene_number)
  const getSceneImageUrl = useCallback((sceneNumber: number) => {
    const sceneIndex = storyboard?.scenes.findIndex((s) => s.scene_number === sceneNumber) ?? -1;
    if (sceneIndex < 0) return null;
    return sceneAssets[sceneIndex]?.imageUrl || null;
  }, [sceneAssets, storyboard]);

  // Fetch storyboard when project is available
  const { data: fetchedStoryboard, refetch: refetchStoryboard } = useQuery({
    queryKey: ["storyboard", projectId],
    queryFn: () => studioApi.getStoryboard(projectId!),
    enabled: !!projectId && currentStep >= 4,
    retry: false,
    staleTime: 0,
  });

  // Update storyboard state when fetched
  useEffect(() => {
    if (fetchedStoryboard) {
      setStoryboard(fetchedStoryboard);
      if (fetchedStoryboard.scenes.length > 0 && selectedSceneNumber === null) {
        setSelectedSceneNumber(fetchedStoryboard.scenes[0].scene_number);
      }
    }
  }, [fetchedStoryboard, selectedSceneNumber]);

  // Generate storyboard mutation
  const generateStoryboardMutation = useMutation({
    mutationFn: (mode: "reference_structure" | "ai_optimized") =>
      studioApi.generateStoryboard(projectId!, {
        mode,
        // Creative input from Step 3
        concept: creativeInput.concept,
        target_duration: creativeInput.targetDuration,
        mood: creativeInput.mood,
        style: creativeInput.style,
        additional_notes: creativeInput.additionalNotes,
        // Selected reference points from Step 2
        reference_points: {
          use_structure: selectedReferencePoints.useStructure,
          use_flow: selectedReferencePoints.useFlow,
          use_cta_style: selectedReferencePoints.useCTAStyle,
          selected_hook_indices: selectedReferencePoints.selectedHookPoints,
          selected_segment_indices: selectedReferencePoints.selectedSegments,
          selected_selling_indices: selectedReferencePoints.selectedSellingPoints,
        },
        // Reference images (temp IDs)
        reference_image_ids: referenceImages.map(img => img.tempId).filter(Boolean) as string[],
      }),
    onSuccess: (data) => {
      setStoryboard(data);
      setShowGenerateModal(false);
      if (data.scenes.length > 0) {
        setSelectedSceneNumber(data.scenes[0].scene_number);
      }
    },
  });

  // Update scene mutation
  const updateSceneMutation = useMutation({
    mutationFn: ({ sceneNumber, data }: { sceneNumber: number; data: SceneUpdateRequest }) =>
      studioApi.updateScene(projectId!, sceneNumber, data),
    onSuccess: (data) => {
      setStoryboard(data);
    },
  });

  // Add scene mutation
  const addSceneMutation = useMutation({
    mutationFn: (data: SceneCreateRequest) => studioApi.addScene(projectId!, data),
    onSuccess: (data) => {
      setStoryboard(data);
      setShowAddSceneModal(false);
    },
  });

  // Delete scene mutation
  const deleteSceneMutation = useMutation({
    mutationFn: (sceneNumber: number) => studioApi.deleteScene(projectId!, sceneNumber),
    onSuccess: (data) => {
      setStoryboard(data);
      if (selectedSceneNumber !== null && !data.scenes.find((s) => s.scene_number === selectedSceneNumber)) {
        setSelectedSceneNumber(data.scenes.length > 0 ? data.scenes[0].scene_number : null);
      }
    },
  });

  // Reorder scenes mutation
  const reorderScenesMutation = useMutation({
    mutationFn: (sceneOrder: number[]) => studioApi.reorderScenes(projectId!, sceneOrder),
    onSuccess: (data) => {
      setStoryboard(data);
    },
  });

  // Handle storyboard generation
  const handleGenerateStoryboard = useCallback(async (mode: "reference_structure" | "ai_optimized") => {
    if (!projectId) return;
    setIsGeneratingStoryboard(true);
    try {
      await generateStoryboardMutation.mutateAsync(mode);
    } finally {
      setIsGeneratingStoryboard(false);
    }
  }, [projectId, generateStoryboardMutation]);

  // Handle scene field update with debounce
  const handleSceneFieldUpdate = useCallback((field: keyof SceneUpdateRequest, value: string | number) => {
    setPendingUpdates((prev) => ({ ...prev, [field]: value }));

    // Clear existing timer
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }

    // Set new timer for auto-save
    debounceTimerRef.current = setTimeout(() => {
      if (selectedSceneNumber !== null) {
        const updates = { ...pendingUpdates, [field]: value };
        updateSceneMutation.mutate({ sceneNumber: selectedSceneNumber, data: updates });
        setPendingUpdates({});
      }
    }, 1000);
  }, [selectedSceneNumber, pendingUpdates, updateSceneMutation]);

  // Save pending updates immediately
  const savePendingUpdates = useCallback(() => {
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }
    if (selectedSceneNumber !== null && Object.keys(pendingUpdates).length > 0) {
      updateSceneMutation.mutate({ sceneNumber: selectedSceneNumber, data: pendingUpdates });
      setPendingUpdates({});
    }
  }, [selectedSceneNumber, pendingUpdates, updateSceneMutation]);

  // Handle scene move up/down
  const handleMoveScene = useCallback((sceneNumber: number, direction: "up" | "down") => {
    if (!storyboard) return;
    const currentIndex = storyboard.scenes.findIndex((s) => s.scene_number === sceneNumber);
    if (currentIndex === -1) return;

    const newIndex = direction === "up" ? currentIndex - 1 : currentIndex + 1;
    if (newIndex < 0 || newIndex >= storyboard.scenes.length) return;

    const newOrder = storyboard.scenes.map((s) => s.scene_number);
    [newOrder[currentIndex], newOrder[newIndex]] = [newOrder[newIndex], newOrder[currentIndex]];
    reorderScenesMutation.mutate(newOrder);
  }, [storyboard, reorderScenesMutation]);

  // Handle scene deletion
  const handleDeleteScene = useCallback((sceneNumber: number) => {
    if (!window.confirm("이 장면을 삭제하시겠습니까?")) return;
    deleteSceneMutation.mutate(sceneNumber);
  }, [deleteSceneMutation]);

  // Initialize scene assets when reference is selected
  const initializeSceneAssets = useCallback((segments: TimelineSegment[]) => {
    const assets: SceneAsset[] = segments.map((_, index) => ({
      sceneIndex: index,
      id: null,
      imageUrl: null,
      source: null,
      isGenerating: false,
    }));
    setSceneAssets(assets);
  }, []);

  // Create project when moving to Step 3
  const createProject = useCallback(async () => {
    if (!selectedBrandId || !selectedProductId || !selectedReference) return null;

    setIsCreatingProject(true);
    try {
      const project = await studioApi.createProject({
        title: `${selectedBrand?.name} - ${selectedProduct?.name} 영상`,
        brand_id: selectedBrandId,
        product_id: selectedProductId,
        reference_analysis_id: selectedReference.analysis_id,
      });
      setProjectId(project.id);
      return project;
    } catch (error) {
      console.error("Failed to create project:", error);
      return null;
    } finally {
      setIsCreatingProject(false);
    }
  }, [selectedBrandId, selectedProductId, selectedReference, selectedBrand, selectedProduct]);

  // Handle file upload for a scene (temp upload for preview)
  const handleFileUpload = useCallback(async (sceneIndex: number, file: File, segment: TimelineSegment) => {
    if (!projectId) return;

    // Show local preview immediately
    const localPreviewUrl = URL.createObjectURL(file);
    setSceneAssets((prev) =>
      prev.map((asset) =>
        asset.sceneIndex === sceneIndex
          ? { ...asset, imageUrl: localPreviewUrl, source: "uploaded" as const, isGenerating: true }
          : asset
      )
    );

    try {
      // Upload to temp storage (NOT saved to DB yet)
      const tempResult = await studioApi.uploadTempImage(projectId, file);

      setSceneAssets((prev) =>
        prev.map((asset) =>
          asset.sceneIndex === sceneIndex
            ? {
                ...asset,
                id: null,  // Not saved to DB yet
                imageUrl: tempResult.preview_url,
                source: "uploaded" as const,
                isGenerating: false,
                temp_id: tempResult.temp_id,
                filename: tempResult.filename,
              }
            : asset
        )
      );
    } catch (error) {
      console.error("Failed to upload image:", error);
      // Revert on error
      setSceneAssets((prev) =>
        prev.map((asset) =>
          asset.sceneIndex === sceneIndex
            ? { ...asset, imageUrl: null, source: null, isGenerating: false }
            : asset
        )
      );
    }
  }, [projectId]);

  // Handle AI image generation for a scene (temp, NOT saved to DB)
  const handleAIGenerate = useCallback(async (sceneIndex: number, segment: TimelineSegment) => {
    if (!projectId) return;

    setSceneAssets((prev) =>
      prev.map((asset) =>
        asset.sceneIndex === sceneIndex ? { ...asset, isGenerating: true } : asset
      )
    );

    try {
      // Use actual scene_number from storyboard if available, otherwise use sceneIndex + 1
      const actualSceneNumber = storyboard?.scenes[sceneIndex]?.scene_number ?? (sceneIndex + 1);

      const tempResult = await studioApi.generateSceneImage(projectId, {
        scene_number: actualSceneNumber,
        prompt: segment.visual_description,
        scene_segment_type: segment.segment_type,
        scene_description: segment.visual_description,
        duration_seconds: segment.end_time - segment.start_time,
        provider: "gemini_imagen", // Use Gemini Imagen 4 for AI image generation
      });

      setSceneAssets((prev) =>
        prev.map((asset) =>
          asset.sceneIndex === sceneIndex
            ? {
                ...asset,
                id: null,
                imageUrl: tempResult.preview_url,
                source: "ai_generated" as const,
                isGenerating: false,
                temp_id: tempResult.temp_id,
                filename: tempResult.filename,
                generation_prompt: tempResult.generation_prompt,
                generation_provider: tempResult.generation_provider,
                generation_duration_ms: tempResult.generation_time_ms,
              }
            : asset
        )
      );
    } catch (error) {
      console.error("Failed to generate image:", error);
      setSceneAssets((prev) =>
        prev.map((asset) =>
          asset.sceneIndex === sceneIndex ? { ...asset, isGenerating: false } : asset
        )
      );
    }
  }, [projectId, storyboard]);

  // Remove image from a scene
  const handleRemoveImage = useCallback(async (sceneIndex: number) => {
    const asset = sceneAssets.find((a) => a.sceneIndex === sceneIndex);
    if (!projectId || !asset?.id) {
      // Just clear local state if no backend ID
      setSceneAssets((prev) =>
        prev.map((a) =>
          a.sceneIndex === sceneIndex
            ? { ...a, id: null, imageUrl: null, source: null, file: undefined }
            : a
        )
      );
      return;
    }

    try {
      await studioApi.deleteSceneImage(projectId, asset.id);
      setSceneAssets((prev) =>
        prev.map((a) =>
          a.sceneIndex === sceneIndex
            ? { ...a, id: null, imageUrl: null, source: null, file: undefined }
            : a
        )
      );
    } catch (error) {
      console.error("Failed to delete image:", error);
    }
  }, [projectId, sceneAssets]);

  // Generate all missing images
  const handleGenerateAll = useCallback(async () => {
    const segments = selectedReference?.segments || [];
    const missingScenes = sceneAssets.filter((s) => !s.imageUrl);

    for (const scene of missingScenes) {
      await handleAIGenerate(scene.sceneIndex, segments[scene.sceneIndex]);
    }
  }, [sceneAssets, selectedReference, handleAIGenerate]);

  // Save all temporary scene images to permanent storage
  const saveAllSceneImages = useCallback(async () => {
    if (!projectId || !selectedReference?.segments) return true;

    const assetsToSave = sceneAssets.filter(
      (asset) => asset.temp_id && asset.filename && asset.imageUrl && !asset.id
    );

    if (assetsToSave.length === 0) return true;

    try {
      for (const asset of assetsToSave) {
        const segment = selectedReference.segments[asset.sceneIndex];
        if (!segment) continue;

        // Use actual scene_number from storyboard if available, otherwise use sceneIndex + 1
        const actualSceneNumber = storyboard?.scenes[asset.sceneIndex]?.scene_number ?? (asset.sceneIndex + 1);

        const savedImage = await studioApi.saveSceneImage(projectId, {
          scene_number: actualSceneNumber,
          temp_id: asset.temp_id!,
          filename: asset.filename!,
          source: asset.source || "uploaded",
          scene_segment_type: segment.segment_type,
          scene_description: segment.visual_description,
          duration_seconds: segment.end_time - segment.start_time,
          generation_prompt: asset.generation_prompt,
          generation_provider: asset.generation_provider,
          generation_duration_ms: asset.generation_duration_ms,
        });

        // Update asset with permanent data
        setSceneAssets((prev) =>
          prev.map((a) =>
            a.sceneIndex === asset.sceneIndex
              ? {
                  ...a,
                  id: savedImage.id,
                  imageUrl: savedImage.image_url,
                  temp_id: undefined,
                  filename: undefined,
                }
              : a
          )
        );
      }
      return true;
    } catch (error) {
      console.error("Failed to save scene images:", error);
      alert("이미지 저장에 실패했습니다. 다시 시도해주세요.");
      return false;
    }
  }, [projectId, sceneAssets, selectedReference, storyboard]);

  // Extended Video Generation Handler (Scene Extension - primary mode)
  const handleGenerateExtendedVideo = useCallback(async () => {
    if (!projectId || !storyboard) {
      alert("프로젝트와 스토리보드가 필요합니다.");
      return;
    }

    // Save all temporary scene images to DB before video generation
    const saved = await saveAllSceneImages();
    if (!saved) {
      console.warn("Some scene images may not have been saved");
    }

    // Reset state
    setIsGeneratingVideo(true);
    setGeneratedVideoUrl(null);
    setExtendedVideoStatus({
      status: "processing",
      extension_hops_completed: 0,
      scenes_processed: 0,
    });

    try {
      const result = await studioApi.generateExtendedVideo(projectId, {
        target_duration_seconds: creativeInput.targetDuration || 30,
        aspect_ratio: "16:9",
        provider: "veo",
      });

      if (result.status === "processing" && result.operation_id) {
        // Start polling for status
        pollExtendedVideoStatus(result.operation_id);
      } else if (result.status === "completed" && result.video_url) {
        setGeneratedVideoUrl(result.video_url);
        setExtendedVideoStatus(result);
        setIsGeneratingVideo(false);
      } else if (result.status === "failed") {
        setExtendedVideoStatus(result);
        setIsGeneratingVideo(false);
        alert(`영상 생성 실패: ${result.error_message || "알 수 없는 오류"}`);
      }
    } catch (error) {
      console.error("Extended video generation failed:", error);
      setExtendedVideoStatus({
        status: "failed",
        extension_hops_completed: 0,
        scenes_processed: 0,
        error_message: "영상 생성에 실패했습니다. 다시 시도해주세요.",
      });
      setIsGeneratingVideo(false);
      alert("영상 생성에 실패했습니다. 다시 시도해주세요.");
    }
  }, [projectId, storyboard, saveAllSceneImages, creativeInput.targetDuration]);

  // Poll for extended video generation status
  const pollExtendedVideoStatus = useCallback(
    (operationId: string) => {
      if (!projectId) return;

      // Clear any existing polling
      if (extendedVideoPollingRef.current) {
        clearInterval(extendedVideoPollingRef.current);
      }

      const poll = async () => {
        try {
          const result = await studioApi.getExtendedVideoStatus(projectId, operationId);
          setExtendedVideoStatus(result);

          if (result.status === "completed" && result.video_url) {
            setGeneratedVideoUrl(result.video_url);
            setIsGeneratingVideo(false);
            if (extendedVideoPollingRef.current) {
              clearInterval(extendedVideoPollingRef.current);
              extendedVideoPollingRef.current = null;
            }
          } else if (result.status === "failed") {
            setIsGeneratingVideo(false);
            if (extendedVideoPollingRef.current) {
              clearInterval(extendedVideoPollingRef.current);
              extendedVideoPollingRef.current = null;
            }
          }
        } catch (error) {
          console.error("Failed to poll extended video status:", error);
        }
      };

      // Poll every 5 seconds
      extendedVideoPollingRef.current = setInterval(poll, 5000);
      // Run immediately
      poll();
    },
    [projectId]
  );

  // Cleanup extended video polling on unmount
  useEffect(() => {
    return () => {
      if (extendedVideoPollingRef.current) {
        clearInterval(extendedVideoPollingRef.current);
      }
    };
  }, []);

  // Per-scene Video Generation Handler (fallback mode)
  const handleGenerateVideoPerScene = useCallback(async () => {
    if (!projectId || !storyboard) {
      alert("프로젝트와 스토리보드가 필요합니다.");
      return;
    }

    // Save all temporary scene images to DB before video generation
    // This ensures images generated in Step 4/5 are also saved
    const saved = await saveAllSceneImages();
    if (!saved) {
      console.warn("Some scene images may not have been saved");
    }

    // Initialize scene videos state for all scenes
    const initialSceneVideos: SceneVideoStatus[] = storyboard.scenes.map((scene) => ({
      scene_number: scene.scene_number,
      status: "pending" as const,
      scene_segment_type: scene.scene_type,
    }));
    setSceneVideos(initialSceneVideos);
    setIsGeneratingVideo(true);
    setConcatenationStatus("idle");
    setGeneratedVideoUrl(null);

    // Helper function to wait
    const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

    // Generate videos for each scene sequentially with delay to avoid rate limits
    for (let i = 0; i < storyboard.scenes.length; i++) {
      const scene = storyboard.scenes[i];

      // Update status to processing for this scene
      setSceneVideos((prev) =>
        prev.map((sv) =>
          sv.scene_number === scene.scene_number
            ? { ...sv, status: "processing" as const }
            : sv
        )
      );

      try {
        const result = await studioApi.generateSceneVideo(projectId, scene.scene_number, {
          provider: "veo",
          aspect_ratio: "16:9",
        });

        if (result.status === "processing" && result.operation_id) {
          // Poll for this scene's status
          await pollSceneVideoStatus(scene.scene_number, result.operation_id);
        } else if (result.status === "completed") {
          // Immediately update
          setSceneVideos((prev) =>
            prev.map((sv) =>
              sv.scene_number === scene.scene_number
                ? { ...sv, ...result }
                : sv
            )
          );
        } else if (result.status === "failed") {
          setSceneVideos((prev) =>
            prev.map((sv) =>
              sv.scene_number === scene.scene_number
                ? { ...sv, status: "failed" as const, error_message: result.error_message }
                : sv
            )
          );
        }
      } catch (error) {
        console.error(`Failed to generate video for scene ${scene.scene_number}:`, error);
        setSceneVideos((prev) =>
          prev.map((sv) =>
            sv.scene_number === scene.scene_number
              ? { ...sv, status: "failed" as const, error_message: "영상 생성에 실패했습니다." }
              : sv
          )
        );
      }

      // No delay between scenes - generate as fast as possible
      // Note: May hit rate limits if generating many scenes quickly
    }

    setIsGeneratingVideo(false);
  }, [projectId, storyboard, saveAllSceneImages]);

  // Poll for individual scene video status
  const pollSceneVideoStatus = useCallback(
    (sceneNumber: number, operationId: string): Promise<void> => {
      return new Promise((resolve) => {
        if (!projectId) {
          resolve();
          return;
        }

        const poll = async () => {
          try {
            const result = await studioApi.getSceneVideoStatus(projectId, sceneNumber);

            setSceneVideos((prev) =>
              prev.map((sv) =>
                sv.scene_number === sceneNumber ? { ...sv, ...result } : sv
              )
            );

            if (result.status === "completed" || result.status === "failed") {
              if (sceneVideoPollingRefs.current[sceneNumber]) {
                clearInterval(sceneVideoPollingRefs.current[sceneNumber]!);
                sceneVideoPollingRefs.current[sceneNumber] = null;
              }
              resolve();
            }
          } catch (error) {
            console.error(`Failed to poll scene ${sceneNumber} status:`, error);
          }
        };

        // Poll every 5 seconds
        sceneVideoPollingRefs.current[sceneNumber] = setInterval(poll, 5000);
        // Run immediately
        poll();
      });
    },
    [projectId]
  );

  // Main video generation handler - decides between extended and per-scene mode
  const handleGenerateVideo = useCallback(() => {
    if (useExtendedMode) {
      handleGenerateExtendedVideo();
    } else {
      handleGenerateVideoPerScene();
    }
  }, [useExtendedMode, handleGenerateExtendedVideo, handleGenerateVideoPerScene]);

  // Regenerate video for a single scene
  const handleRegenerateSceneVideo = useCallback(
    async (sceneNumber: number) => {
      if (!projectId) return;

      // Update status to processing
      setSceneVideos((prev) =>
        prev.map((sv) =>
          sv.scene_number === sceneNumber
            ? { ...sv, status: "processing" as const, error_message: undefined }
            : sv
        )
      );

      try {
        const result = await studioApi.generateSceneVideo(projectId, sceneNumber, {
          provider: "veo",
          aspect_ratio: "16:9",
        });

        if (result.status === "processing" && result.operation_id) {
          await pollSceneVideoStatus(sceneNumber, result.operation_id);
        } else {
          setSceneVideos((prev) =>
            prev.map((sv) =>
              sv.scene_number === sceneNumber ? { ...sv, ...result } : sv
            )
          );
        }
      } catch (error) {
        console.error(`Failed to regenerate video for scene ${sceneNumber}:`, error);
        setSceneVideos((prev) =>
          prev.map((sv) =>
            sv.scene_number === sceneNumber
              ? { ...sv, status: "failed" as const, error_message: "영상 재생성에 실패했습니다." }
              : sv
          )
        );
      }
    },
    [projectId, pollSceneVideoStatus]
  );

  // Concatenate all scene videos into final video
  const handleConcatenateVideos = useCallback(async () => {
    if (!projectId) return;

    setIsConcatenating(true);
    setConcatenationStatus("processing");

    try {
      const result = await studioApi.concatenateVideos(projectId, {
        transition_type: "dissolve",
        include_audio: true,
      });

      if (result.status === "completed" && result.final_video_url) {
        setGeneratedVideoUrl(result.final_video_url);
        setConcatenationStatus("completed");
      } else if (result.status === "processing" && result.operation_id) {
        // Poll for concatenation status
        pollVideoStatus(result.operation_id);
      } else if (result.status === "failed") {
        setConcatenationStatus("failed");
        alert(`영상 병합 실패: ${result.error_message || "알 수 없는 오류"}`);
      }
    } catch (error) {
      console.error("Video concatenation failed:", error);
      setConcatenationStatus("failed");
      alert("영상 병합에 실패했습니다. 다시 시도해주세요.");
    } finally {
      setIsConcatenating(false);
    }
  }, [projectId]);

  // Poll for final video concatenation status
  const pollVideoStatus = useCallback((operationId: string) => {
    if (!projectId) return;

    const poll = async () => {
      try {
        const result = await studioApi.getVideoStatus(projectId, operationId);
        setVideoGenerationStatus(result);

        if (result.status === "completed" && result.video_url) {
          setGeneratedVideoUrl(result.video_url);
          setConcatenationStatus("completed");
          setIsConcatenating(false);
          if (videoPollingRef.current) {
            clearInterval(videoPollingRef.current);
            videoPollingRef.current = null;
          }
        } else if (result.status === "failed") {
          setConcatenationStatus("failed");
          setIsConcatenating(false);
          if (videoPollingRef.current) {
            clearInterval(videoPollingRef.current);
            videoPollingRef.current = null;
          }
          alert(`영상 생성 실패: ${result.error_message || "알 수 없는 오류"}`);
        }
      } catch (error) {
        console.error("Failed to poll video status:", error);
      }
    };

    // Poll every 10 seconds
    videoPollingRef.current = setInterval(poll, 10000);
    // Also run immediately
    poll();
  }, [projectId]);

  // Computed values for scene videos
  const completedSceneVideos = useMemo(
    () => sceneVideos.filter((sv) => sv.status === "completed"),
    [sceneVideos]
  );
  const processingSceneVideos = useMemo(
    () => sceneVideos.filter((sv) => sv.status === "processing"),
    [sceneVideos]
  );
  const failedSceneVideos = useMemo(
    () => sceneVideos.filter((sv) => sv.status === "failed"),
    [sceneVideos]
  );
  const allScenesCompleted = useMemo(
    () =>
      sceneVideos.length > 0 &&
      sceneVideos.every((sv) => sv.status === "completed"),
    [sceneVideos]
  );

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (videoPollingRef.current) {
        clearInterval(videoPollingRef.current);
      }
      // Cleanup scene video polling refs
      Object.values(sceneVideoPollingRefs.current).forEach((ref) => {
        if (ref) clearInterval(ref);
      });
    };
  }, []);

  const handleNext = async () => {
    if (currentStep < 5) {
      setIsProcessingNext(true);

      try {
        // Create project and initialize scene assets when moving to Step 3
        if (currentStep === 2 && selectedReference?.segments) {
          const project = await createProject();
          if (!project) {
            alert("프로젝트 생성에 실패했습니다. 다시 시도해주세요.");
            return;
          }
          initializeSceneAssets(selectedReference.segments);
        }

        // Save all temp images when moving from Step 3 to Step 4, or Step 4 to Step 5
        if (currentStep === 3 || currentStep === 4) {
          const saved = await saveAllSceneImages();
          if (!saved && currentStep === 3) return;  // Only block on Step 3->4

          // Auto-generate storyboard when moving to Step 4
          if (projectId && !storyboard) {
            setIsGeneratingStoryboard(true);
            try {
              // Use ai_optimized mode with creative input
              await generateStoryboardMutation.mutateAsync("ai_optimized");
            } catch (error) {
              console.error("Failed to auto-generate storyboard:", error);
              // Continue to Step 4 even if generation fails - user can retry there
            } finally {
              setIsGeneratingStoryboard(false);
            }
          }
        }

        setCurrentStep(currentStep + 1);
      } finally {
        setIsProcessingNext(false);
      }
    }
  };

  const handlePrev = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const goToStep = (step: number) => {
    // Only allow going to completed steps or current step
    if (step <= currentStep) {
      setCurrentStep(step);
    }
  };

  // ============================================
  // Image Production Handlers (New)
  // ============================================

  // Handle back to studio selection
  const handleBackToSelection = () => {
    setStudioMode(null);
    // Reset video production state
    setCurrentStep(1);
    setSelectedBrandId(null);
    setSelectedProductId(null);
    setSelectedReferenceId(null);
    setSceneAssets([]);
    setProjectId(null);
    setStoryboard(null);
    // Reset image production state
    setUploadedImages([]);
    setImagePrompt("");
    setGeneratedImageUrl(null);
  };

  // Handle image upload for image production
  const handleImageUpload = useCallback(async (files: FileList | null) => {
    if (!files || files.length === 0) return;

    const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50MB
    const validFiles: File[] = [];

    // Check file sizes
    Array.from(files).forEach((file) => {
      if (file.size > MAX_FILE_SIZE) {
        toast.error(`파일 크기 초과: ${file.name}`, {
          description: `최대 50MB까지 업로드 가능합니다. (현재: ${(file.size / 1024 / 1024).toFixed(1)}MB)`,
        });
      } else {
        validFiles.push(file);
      }
    });

    if (validFiles.length === 0) return;

    const newImages: UploadedImage[] = validFiles.map((file) => ({
      id: `img-${Date.now()}-${Math.random().toString(36).substring(2, 11)}`,
      file,
      previewUrl: URL.createObjectURL(file),
      isUploading: true,
    }));

    setUploadedImages((prev) => [...prev, ...newImages]);

    // Upload each image to get temp_id
    for (const image of newImages) {
      try {
        const formData = new FormData();
        formData.append("file", image.file);

        const response = await studioApi.analyzeMarketingImage(formData);

        setUploadedImages((prev) =>
          prev.map((img) =>
            img.id === image.id
              ? {
                  ...img,
                  isUploading: false,
                  tempId: response.temp_id,
                  analysis: {
                    detected_type: response.detected_type,
                    is_realistic: response.is_realistic,
                    description: response.description,
                    elements: response.elements,
                  },
                }
              : img
          )
        );
      } catch (error) {
        console.error("Failed to upload image:", error);
        setUploadedImages((prev) =>
          prev.map((img) =>
            img.id === image.id ? { ...img, isUploading: false } : img
          )
        );
      }
    }
  }, []);

  // Handle image removal
  const handleRemoveUploadedImage = useCallback((imageId: string) => {
    setUploadedImages((prev) => {
      const image = prev.find((img) => img.id === imageId);
      if (image) {
        URL.revokeObjectURL(image.previewUrl);
      }
      return prev.filter((img) => img.id !== imageId);
    });
  }, []);

  // Handle marketing image generation
  const handleGenerateMarketingImage = useCallback(async () => {
    if (uploadedImages.length === 0 || !imagePrompt.trim()) return;

    // Get all valid image temp IDs
    const validImages = uploadedImages.filter(img => img.tempId);
    if (validImages.length === 0) return;

    setIsGeneratingImage(true);
    setGeneratedImageUrl(null);

    try {
      // Check if any uploaded image is realistic
      const hasRealisticImage = uploadedImages.some(img => img.analysis?.is_realistic);
      let finalPrompt = imagePrompt;
      if (hasRealisticImage) {
        finalPrompt = `${imagePrompt}. photorealistic, physically plausible`;
      }

      // Collect all image temp IDs
      const imageTempIds = validImages.map(img => img.tempId!);
      console.log(`Sending ${imageTempIds.length} images to API:`, imageTempIds);

      const response = await studioApi.editImageWithProduct({
        image_temp_ids: imageTempIds,
        prompt: finalPrompt,
      });

      setGeneratedImageUrl(response.image_url);
    } catch (error) {
      console.error("Failed to generate marketing image:", error);
      alert("이미지 생성에 실패했습니다. 다시 시도해주세요.");
    } finally {
      setIsGeneratingImage(false);
    }
  }, [uploadedImages, imagePrompt]);

  // Reset image production for new generation
  const handleResetImageProduction = useCallback(() => {
    uploadedImages.forEach((img) => URL.revokeObjectURL(img.previewUrl));
    setUploadedImages([]);
    setImagePrompt("");
    setGeneratedImageUrl(null);
  }, [uploadedImages]);

  // Download generated image (clean, without watermark)
  const handleDownloadImage = useCallback(async () => {
    if (!generatedImageUrl) return;

    try {
      const response = await fetch(generatedImageUrl);
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);

      const link = document.createElement('a');
      link.href = url;
      link.download = `generated-image-${Date.now()}.png`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Download failed:', error);
      // Fallback: open in new tab
      window.open(generatedImageUrl, '_blank');
    }
  }, [generatedImageUrl]);

  // ============================================
  // Render
  // ============================================

  // Studio Mode Selection Screen
  if (studioMode === null) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-4xl mx-auto px-4 py-16">
          <div className="text-center mb-12">
            <h1 className="text-3xl font-bold text-gray-900 mb-4">스튜디오</h1>
            <p className="text-gray-600 text-lg">
              제작하고 싶은 콘텐츠 유형을 선택하세요
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-6">
            {/* Image Production Card */}
            <button
                onClick={() => setStudioMode("image")}
                className="group p-8 bg-white rounded-2xl border-2 border-gray-200 hover:border-purple-500 hover:shadow-lg transition-all text-left"
            >
              <div className="w-16 h-16 rounded-2xl bg-purple-100 text-purple-600 flex items-center justify-center mb-6 group-hover:bg-purple-500 group-hover:text-white transition-colors">
                <ImageIcon className="w-8 h-8" />
              </div>
              <h2 className="text-xl font-bold text-gray-900 mb-2">이미지 제작</h2>
              <p className="text-gray-600 mb-4">
                이미지를 업로드하고 프롬프트로 마케팅 이미지를 생성합니다
              </p>
              <div className="flex flex-wrap gap-2">
                <span className="px-3 py-1 bg-gray-100 text-gray-600 text-sm rounded-full">
                  이미지 업로드
                </span>
                <span className="px-3 py-1 bg-gray-100 text-gray-600 text-sm rounded-full">
                  AI 분석
                </span>
                <span className="px-3 py-1 bg-gray-100 text-gray-600 text-sm rounded-full">
                  AI 이미지 생성
                </span>
              </div>
            </button>
            {/* Video Production Card */}
            <button
              onClick={() => setStudioMode("video")}
              className="group p-8 bg-white rounded-2xl border-2 border-gray-200 hover:border-primary-500 hover:shadow-lg transition-all text-left"
            >
              <div className="w-16 h-16 rounded-2xl bg-primary-100 text-primary-600 flex items-center justify-center mb-6 group-hover:bg-primary-500 group-hover:text-white transition-colors">
                <Video className="w-8 h-8" />
              </div>
              <h2 className="text-xl font-bold text-gray-900 mb-2">영상 제작</h2>
              <p className="text-gray-600 mb-4">
                레퍼런스 영상을 분석하고, AI로 마케팅 영상을 제작합니다
              </p>
              <div className="flex flex-wrap gap-2">
                <span className="px-3 py-1 bg-gray-100 text-gray-600 text-sm rounded-full">
                  브랜드/제품 선택
                </span>
                <span className="px-3 py-1 bg-gray-100 text-gray-600 text-sm rounded-full">
                  레퍼런스 분석
                </span>
                <span className="px-3 py-1 bg-gray-100 text-gray-600 text-sm rounded-full">
                  AI 영상 생성
                </span>
              </div>
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Image Production Mode
  if (studioMode === "image") {
    return (
      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <div className="bg-white border-b sticky top-0 z-10">
          <div className="max-w-7xl mx-auto px-4 py-4">
            <div className="flex items-center gap-4">
              <button
                onClick={handleBackToSelection}
                className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <ChevronRight className="w-5 h-5 rotate-180" />
              </button>
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-lg bg-purple-100 text-purple-600 flex items-center justify-center">
                  <ImageIcon className="w-4 h-4" />
                </div>
                <h1 className="text-lg font-semibold text-gray-900">이미지 제작</h1>
              </div>
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="max-w-7xl mx-auto px-4 py-8">
          <div className="grid lg:grid-cols-2 gap-8">
            {/* Left Panel: Upload & Prompt */}
            <div className="space-y-6">
              {/* Image Upload Section */}
              <div className="card p-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                    <Upload className="w-5 h-5 text-purple-500" />
                    이미지 업로드
                  </h2>
                  {uploadedImages.length > 0 && (
                    <button
                      onClick={handleResetImageProduction}
                      className="text-sm text-gray-500 hover:text-gray-700"
                    >
                      모두 지우기
                    </button>
                  )}
                </div>

                {/* Drop Zone */}
                <div
                  onClick={() => imageInputRef.current?.click()}
                  onDragOver={(e) => {
                    e.preventDefault();
                    e.stopPropagation();
                  }}
                  onDrop={(e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    handleImageUpload(e.dataTransfer.files);
                  }}
                  className="border-2 border-dashed border-gray-300 rounded-xl p-8 text-center cursor-pointer hover:border-purple-400 hover:bg-purple-50 transition-colors"
                >
                  <input
                    ref={imageInputRef}
                    type="file"
                    accept="image/jpeg,image/png,image/webp"
                    multiple
                    className="hidden"
                    onChange={(e) => {
                      handleImageUpload(e.target.files);
                      e.target.value = "";
                    }}
                  />
                  <Upload className="w-10 h-10 text-gray-400 mx-auto mb-3" />
                  <p className="text-gray-600 mb-1">
                    클릭하거나 이미지를 드래그하세요
                  </p>
                  <p className="text-sm text-gray-400">
                    배경, 제품, 레퍼런스 이미지 등 자유롭게 업로드
                  </p>
                </div>

                {/* Uploaded Images Grid */}
                {uploadedImages.length > 0 && (
                  <div className="mt-4 grid grid-cols-2 sm:grid-cols-3 gap-3">
                    {uploadedImages.map((image) => (
                      <div
                        key={image.id}
                        className="relative group aspect-square bg-gray-100 rounded-lg overflow-hidden"
                      >
                        <Image
                          src={image.previewUrl}
                          alt="Uploaded"
                          fill
                          className="object-cover"
                          sizes="150px"
                        />

                        {/* Uploading Overlay */}
                        {image.isUploading && (
                          <div className="absolute inset-0 bg-black/50 flex items-center justify-center">
                            <div className="text-center text-white">
                              <Loader2 className="w-6 h-6 animate-spin mx-auto mb-1" />
                              <span className="text-xs">업로드 중...</span>
                            </div>
                          </div>
                        )}

                        {/* Remove Button */}
                        <button
                          onClick={() => handleRemoveUploadedImage(image.id)}
                          className="absolute top-1 right-1 p-1 bg-red-500 text-white rounded-full opacity-0 group-hover:opacity-100 transition-opacity"
                        >
                          <X className="w-3 h-3" />
                        </button>

                        {/* Analysis Badge */}
                        {image.analysis && !image.isUploading && (
                          <div className="absolute bottom-1 left-1 right-1 flex gap-1">
                            <span className={`px-1.5 py-0.5 text-[10px] font-medium rounded ${
                              image.analysis.detected_type === 'product' ? 'bg-blue-500 text-white' :
                              image.analysis.detected_type === 'background' ? 'bg-green-500 text-white' :
                              image.analysis.detected_type === 'person' ? 'bg-orange-500 text-white' :
                              'bg-gray-500 text-white'
                            }`}>
                              {image.analysis.detected_type === 'product' ? '제품' :
                               image.analysis.detected_type === 'background' ? '배경' :
                               image.analysis.detected_type === 'person' ? '인물' :
                               image.analysis.detected_type === 'reference' ? '참조' : '기타'}
                            </span>
                            <span className={`px-1.5 py-0.5 text-[10px] font-medium rounded ${
                              image.analysis.is_realistic ? 'bg-purple-500 text-white' : 'bg-pink-500 text-white'
                            }`}>
                              {image.analysis.is_realistic ? '실사' : '일러스트'}
                            </span>
                          </div>
                        )}

                        {/* Hover Description Tooltip */}
                        {image.analysis?.description && !image.isUploading && (
                          <div className="absolute inset-0 bg-black/80 opacity-0 group-hover:opacity-100 transition-opacity p-2 flex items-center justify-center pointer-events-none">
                            <p className="text-white text-[10px] leading-tight line-clamp-6 text-center">
                              {image.analysis.description}
                            </p>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}

                {/* Detailed Analysis Section */}
                {uploadedImages.some(img => img.analysis?.description) && (
                  <div className="mt-4 p-3 bg-gray-50 rounded-lg">
                    <h3 className="text-xs font-semibold text-gray-700 mb-2">AI 이미지 분석</h3>
                    <div className="space-y-2">
                      {uploadedImages.filter(img => img.analysis?.description).map((image, idx) => (
                        <div key={image.id} className="text-xs">
                          <div className="flex items-center gap-2 mb-1">
                            <span className={`px-1.5 py-0.5 text-[10px] font-medium rounded ${
                              image.analysis?.detected_type === 'product' ? 'bg-blue-500 text-white' :
                              image.analysis?.detected_type === 'background' ? 'bg-green-500 text-white' :
                              'bg-gray-500 text-white'
                            }`}>
                              이미지 {idx + 1}
                            </span>
                            {image.analysis?.is_realistic ? (
                              <span className="text-purple-600 text-[10px]">실사 → 물리적 제약 적용</span>
                            ) : (
                              <span className="text-pink-600 text-[10px]">일러스트 → 창작 자유도 높음</span>
                            )}
                          </div>
                          <p className="text-gray-600 leading-relaxed">{image.analysis?.description}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

              </div>

              {/* Prompt Section */}
              <div className="card p-6">
                <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2 mb-4">
                  <Wand2 className="w-5 h-5 text-purple-500" />
                  프롬프트 입력
                </h2>

                <textarea
                  value={imagePrompt}
                  onChange={(e) => setImagePrompt(e.target.value)}
                  placeholder="원하는 이미지를 설명해주세요...&#10;&#10;예시:&#10;- 이 배경에 제품이 가득 차게 배치해줘&#10;- 고급스러운 느낌의 제품 광고 이미지 만들어줘&#10;- 이 스타일로 제품을 보여주는 마케팅 이미지 생성해줘"
                  className="w-full h-32 p-4 border border-gray-300 rounded-xl resize-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />

                <button
                  onClick={handleGenerateMarketingImage}
                  disabled={uploadedImages.length === 0 || !imagePrompt.trim() || isGeneratingImage || uploadedImages.some((img) => img.isUploading)}
                  className="w-full mt-4 btn-primary py-3 flex items-center justify-center gap-2 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
                >
                  {isGeneratingImage ? (
                    <>
                      <Loader2 className="w-5 h-5 animate-spin" />
                      이미지 생성 중...
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-5 h-5" />
                      이미지 생성
                    </>
                  )}
                </button>
              </div>
            </div>

            {/* Right Panel: Result */}
            <div className="card p-6">
              <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2 mb-4">
                <ImageIcon className="w-5 h-5 text-purple-500" />
                생성 결과
              </h2>

              <div className="aspect-square bg-gray-100 rounded-xl overflow-hidden relative">
                {isGeneratingImage ? (
                  <div className="absolute inset-0 flex flex-col items-center justify-center">
                    <Loader2 className="w-12 h-12 text-purple-500 animate-spin mb-4" />
                    <p className="text-gray-600">AI가 이미지를 생성하고 있습니다...</p>
                    <p className="text-sm text-gray-400 mt-1">잠시만 기다려주세요</p>
                  </div>
                ) : generatedImageUrl ? (
                  <>
                    <Image
                      src={generatedImageUrl}
                      alt="Generated"
                      fill
                      className="object-contain cursor-pointer hover:opacity-90 transition-opacity"
                      sizes="(max-width: 768px) 100vw, 50vw"
                      onClick={() => setShowLightbox(true)}
                    />
                    {/* AI Disclosure Label - Transparency Requirement */}
                    <div className="absolute top-2 left-2 bg-black/70 text-white text-[10px] px-2 py-1 rounded flex items-center gap-1">
                      <svg className="w-3 h-3" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/>
                      </svg>
                      AI 생성
                    </div>
                    <div className="absolute top-2 right-2 text-xs text-gray-500 bg-white/80 px-2 py-1 rounded">
                      클릭하여 크게 보기
                    </div>
                    <div className="absolute bottom-4 right-4 flex gap-2">
                      <button
                        onClick={handleDownloadImage}
                        className="px-4 py-2 bg-white text-gray-700 rounded-lg shadow-lg hover:bg-gray-50 flex items-center gap-2"
                      >
                        <Upload className="w-4 h-4 rotate-180" />
                        다운로드
                      </button>
                      <button
                        onClick={handleGenerateMarketingImage}
                        className="px-4 py-2 bg-purple-600 text-white rounded-lg shadow-lg hover:bg-purple-700 flex items-center gap-2"
                      >
                        <RefreshCw className="w-4 h-4" />
                        재생성
                      </button>
                    </div>
                  </>
                ) : (
                  <div className="absolute inset-0 flex flex-col items-center justify-center">
                    <ImageIcon className="w-16 h-16 text-gray-300 mb-4" />
                    <p className="text-gray-500">이미지를 업로드하고</p>
                    <p className="text-gray-500">프롬프트를 입력한 후</p>
                    <p className="text-gray-500">생성 버튼을 눌러주세요</p>
                  </div>
                )}
              </div>

              {/* Tips */}
              {!generatedImageUrl && !isGeneratingImage && (
                <div className="mt-6 p-4 bg-gray-50 rounded-lg">
                  <h3 className="text-sm font-medium text-gray-700 mb-2">사용 팁</h3>
                  <ul className="text-sm text-gray-500 space-y-1">
                    <li>• 배경 이미지와 제품 이미지를 함께 업로드하면 합성됩니다</li>
                    <li>• 레퍼런스 이미지로 스타일을 참고할 수 있습니다</li>
                    <li>• 프롬프트는 구체적일수록 좋은 결과를 얻습니다</li>
                  </ul>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Lightbox Modal */}
        {showLightbox && generatedImageUrl && (
          <div
            className="fixed inset-0 bg-black/90 z-50 flex items-center justify-center p-4"
            onClick={() => setShowLightbox(false)}
          >
            <div className="relative max-w-[90vw] max-h-[90vh]">
              <img
                src={generatedImageUrl}
                alt="Generated - Full Size"
                className="max-w-full max-h-[85vh] object-contain rounded-lg"
                onClick={(e) => e.stopPropagation()}
              />
              {/* AI Disclosure Label - Transparency Requirement */}
              <div className="absolute top-4 left-4 bg-black/70 text-white text-sm px-3 py-1.5 rounded flex items-center gap-2">
                <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/>
                </svg>
                AI 생성 이미지
              </div>
              <div className="absolute bottom-4 left-1/2 -translate-x-1/2 flex gap-3">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDownloadImage();
                  }}
                  className="px-4 py-2 bg-white text-gray-700 rounded-lg shadow-lg hover:bg-gray-100 flex items-center gap-2"
                >
                  <Upload className="w-4 h-4 rotate-180" />
                  다운로드
                </button>
                <button
                  onClick={() => setShowLightbox(false)}
                  className="px-4 py-2 bg-gray-800 text-white rounded-lg shadow-lg hover:bg-gray-700 flex items-center gap-2"
                >
                  <X className="w-4 h-4" />
                  닫기
                </button>
              </div>
            </div>
            <button
              onClick={() => setShowLightbox(false)}
              className="absolute top-4 right-4 p-2 bg-white/20 hover:bg-white/30 rounded-full transition-colors"
            >
              <X className="w-6 h-6 text-white" />
            </button>
          </div>
        )}
      </div>
    );
  }

  // Video Production Mode (existing flow)
  return (
    <div className="min-h-screen bg-gray-50 relative">
      {/* Full Screen Loading Overlay */}
      {isProcessingNext && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center">
          <div className="bg-white rounded-2xl p-8 shadow-2xl flex flex-col items-center gap-4 max-w-sm mx-4">
            <div className="relative">
              <div className="w-16 h-16 border-4 border-purple-200 rounded-full animate-spin border-t-purple-600" />
              <Sparkles className="w-6 h-6 text-purple-600 absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2" />
            </div>
            <div className="text-center">
              <h3 className="text-lg font-semibold text-gray-900">처리 중...</h3>
              <p className="text-sm text-gray-500 mt-1">
                {currentStep === 2 ? "스토리보드를 생성하고 있습니다" :
                 currentStep === 3 ? "데이터를 저장하고 있습니다" :
                 "다음 단계를 준비하고 있습니다"}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Progress Steps */}
      <div className="bg-white border-b sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center gap-4">
            {/* Back Button */}
            <button
              onClick={handleBackToSelection}
              className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors flex-shrink-0"
              title="스튜디오 선택으로 돌아가기"
            >
              <ChevronRight className="w-5 h-5 rotate-180" />
            </button>
            <div className="flex items-center justify-between overflow-x-auto flex-1">
            {STEPS.map((step, index) => {
              const Icon = step.icon;
              const isCompleted = currentStep > step.id;
              const isCurrent = currentStep === step.id;
              const isClickable = step.id <= currentStep;

              return (
                <div key={step.id} className="flex items-center">
                  <button
                    onClick={() => goToStep(step.id)}
                    disabled={!isClickable}
                    className={`flex flex-col items-center min-w-[80px] transition-all ${
                      isClickable ? "cursor-pointer" : "cursor-not-allowed opacity-50"
                    }`}
                  >
                    <div
                      className={`w-10 h-10 rounded-full flex items-center justify-center transition-all ${
                        isCompleted
                          ? "bg-green-500 text-white"
                          : isCurrent
                          ? "bg-primary-500 text-white ring-4 ring-primary-100"
                          : "bg-gray-200 text-gray-500"
                      }`}
                    >
                      {isCompleted ? <Check className="w-5 h-5" /> : <Icon className="w-5 h-5" />}
                    </div>
                    <span
                      className={`text-xs mt-1 font-medium whitespace-nowrap ${
                        isCurrent ? "text-primary-600" : isCompleted ? "text-green-600" : "text-gray-500"
                      }`}
                    >
                      {step.title}
                    </span>
                  </button>
                  {index < STEPS.length - 1 && (
                    <ChevronRight
                      className={`w-4 h-4 mx-1 flex-shrink-0 ${
                        isCompleted ? "text-green-500" : "text-gray-300"
                      }`}
                    />
                  )}
                </div>
              );
            })}
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Step 1: Brand/Product Selection */}
        {currentStep === 1 && (
          <div className="space-y-6 animate-fadeIn">
            <div className="text-center mb-8">
              <h1 className="text-2xl font-bold text-gray-900">브랜드와 제품을 선택하세요</h1>
              <p className="text-gray-600 mt-2">영상에 사용할 브랜드와 제품 정보를 선택합니다</p>
            </div>

            <div className="grid md:grid-cols-2 gap-6">
              {/* Brand Selection */}
              <div className="card p-6">
                <div className="flex items-center gap-2 mb-4">
                  <Building2 className="w-5 h-5 text-primary-500" />
                  <h2 className="text-lg font-semibold">브랜드 선택</h2>
                </div>

                {brandsLoading ? (
                  <div className="space-y-3">
                    {[1, 2, 3].map((i) => (
                      <div key={i} className="skeleton h-16 rounded-lg" />
                    ))}
                  </div>
                ) : brands.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    <Building2 className="w-12 h-12 mx-auto mb-2 opacity-50" />
                    <p>등록된 브랜드가 없습니다</p>
                    <a href="/brands" className="text-primary-500 hover:underline text-sm">
                      브랜드 등록하기 →
                    </a>
                  </div>
                ) : (
                  <div className="space-y-2 max-h-[400px] overflow-y-auto">
                    {brands.map((brand) => (
                      <button
                        key={brand.id}
                        onClick={() => {
                          setSelectedBrandId(brand.id);
                          setSelectedProductId(null);
                        }}
                        className={`w-full text-left p-4 rounded-lg border-2 transition-all ${
                          selectedBrandId === brand.id
                            ? "border-primary-500 bg-primary-50"
                            : "border-gray-200 hover:border-gray-300"
                        }`}
                      >
                        <div className="font-medium">{brand.name}</div>
                        {brand.industry && (
                          <div className="text-sm text-gray-500">{brand.industry}</div>
                        )}
                        <div className="text-xs text-gray-400 mt-1">
                          제품 {brand.product_count || 0}개
                        </div>
                      </button>
                    ))}
                  </div>
                )}
              </div>

              {/* Product Selection */}
              <div className="card p-6">
                <div className="flex items-center gap-2 mb-4">
                  <Package className="w-5 h-5 text-primary-500" />
                  <h2 className="text-lg font-semibold">제품 선택</h2>
                </div>

                {!selectedBrandId ? (
                  <div className="text-center py-8 text-gray-500">
                    <Package className="w-12 h-12 mx-auto mb-2 opacity-50" />
                    <p>먼저 브랜드를 선택하세요</p>
                  </div>
                ) : productsLoading ? (
                  <div className="space-y-3">
                    {[1, 2, 3].map((i) => (
                      <div key={i} className="skeleton h-16 rounded-lg" />
                    ))}
                  </div>
                ) : products.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    <Package className="w-12 h-12 mx-auto mb-2 opacity-50" />
                    <p>등록된 제품이 없습니다</p>
                    <a href="/brands" className="text-primary-500 hover:underline text-sm">
                      제품 등록하기 →
                    </a>
                  </div>
                ) : (
                  <div className="space-y-2 max-h-[400px] overflow-y-auto">
                    {products.map((product) => (
                      <button
                        key={product.id}
                        onClick={() => {
                          // Reset project if product changes (to ensure correct product is used)
                          if (selectedProductId !== product.id && projectId) {
                            setProjectId(null);
                            setStoryboard(null);
                            setSceneAssets([]);
                          }
                          setSelectedProductId(product.id);
                        }}
                        className={`w-full text-left p-4 rounded-lg border-2 transition-all ${
                          selectedProductId === product.id
                            ? "border-primary-500 bg-primary-50"
                            : "border-gray-200 hover:border-gray-300"
                        }`}
                      >
                        <div className="font-medium">{product.name}</div>
                        {product.product_category && (
                          <div className="text-sm text-gray-500">{product.product_category}</div>
                        )}
                        {product.price_range && (
                          <div className="text-xs text-gray-400 mt-1">{product.price_range}</div>
                        )}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Selected Summary */}
            {selectedBrand && selectedProduct && (
              <div className="card p-4 bg-green-50 border-green-200">
                <div className="flex items-center gap-2 text-green-700">
                  <Check className="w-5 h-5" />
                  <span className="font-medium">
                    {selectedBrand.name} - {selectedProduct.name}
                  </span>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Step 2: Reference Selection */}
        {currentStep === 2 && (
          <div className="space-y-6 animate-fadeIn">
            <div className="text-center mb-8">
              <h1 className="text-2xl font-bold text-gray-900">레퍼런스 분석 결과를 선택하세요</h1>
              <p className="text-gray-600 mt-2">
                참고할 영상의 구조와 기법을 스토리보드에 반영합니다
              </p>
            </div>

            {referencesLoading ? (
              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                {[1, 2, 3, 4, 5, 6].map((i) => (
                  <div key={i} className="skeleton h-48 rounded-lg" />
                ))}
              </div>
            ) : references.filter((r) => r.status === "completed").length === 0 ? (
              <div className="text-center py-16 text-gray-500">
                <Video className="w-16 h-16 mx-auto mb-4 opacity-50" />
                <p className="text-lg">분석 완료된 레퍼런스가 없습니다</p>
                <a href="/" className="text-primary-500 hover:underline">
                  레퍼런스 분석하기 →
                </a>
              </div>
            ) : (
              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                {references
                  .filter((r) => r.status === "completed")
                  .map((ref) => (
                    <button
                      key={ref.analysis_id}
                      onClick={() => {
                        setSelectedReferenceId(ref.analysis_id);
                        // Reset and initialize reference points with all items selected by default
                        setSelectedReferencePoints({
                          useStructure: true,
                          useFlow: true,
                          selectedHookPoints: ref.hook_points?.map((_, i) => i) || [],
                          selectedSegments: ref.segments?.map((_, i) => i) || [],
                          selectedSellingPoints: ref.selling_points?.map((_, i) => i) || [],
                          useCTAStyle: true,
                          selectedEmotionalTriggers: ref.emotional_triggers?.map((_, i) => i) || [],
                        });
                      }}
                      className={`text-left p-4 rounded-xl border-2 transition-all ${
                        selectedReferenceId === ref.analysis_id
                          ? "border-primary-500 bg-primary-50 ring-4 ring-primary-100"
                          : "border-gray-200 hover:border-gray-300 bg-white"
                      }`}
                    >
                      <div className="flex items-start justify-between mb-3">
                        <div className="font-medium text-gray-900 line-clamp-2">
                          {ref.title || "제목 없음"}
                        </div>
                        {selectedReferenceId === ref.analysis_id && (
                          <Check className="w-5 h-5 text-primary-500 flex-shrink-0" />
                        )}
                      </div>

                      <div className="space-y-2 text-sm">
                        {ref.duration && (
                          <div className="flex items-center gap-1 text-gray-500">
                            <Clock className="w-4 h-4" />
                            <span>{Math.round(ref.duration)}초</span>
                          </div>
                        )}

                        {ref.structure_pattern && typeof ref.structure_pattern === "object" && ref.structure_pattern.framework && (
                          <div className="inline-flex items-center px-2 py-1 bg-purple-100 text-purple-700 rounded text-xs font-medium">
                            {ref.structure_pattern.framework}
                          </div>
                        )}

                        <div className="flex flex-wrap gap-1 mt-2">
                          {ref.segments && (
                            <span className="badge badge-blue">{ref.segments.length} 세그먼트</span>
                          )}
                          {ref.hook_points && ref.hook_points.length > 0 && (
                            <span className="badge badge-yellow">{ref.hook_points.length} 후킹</span>
                          )}
                        </div>
                      </div>

                      <div className="mt-3 pt-3 border-t text-xs text-gray-400 truncate">
                        {ref.source_url}
                      </div>
                    </button>
                  ))}
              </div>
            )}

            {/* Selected Reference Preview */}
            {selectedReference && (
              <div className="card p-6 bg-primary-50 border-primary-200">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2 text-primary-700">
                    <Check className="w-5 h-5" />
                    <span className="font-medium">선택된 레퍼런스</span>
                  </div>
                  <button
                    onClick={() => window.open(`/?id=${selectedReference.analysis_id}`, "_blank")}
                    className="text-sm text-primary-600 hover:underline flex items-center gap-1"
                  >
                    <Eye className="w-4 h-4" />
                    상세 보기
                  </button>
                </div>

                <div className="grid md:grid-cols-3 gap-4 text-sm">
                  <div>
                    <div className="text-gray-500 mb-1">구조 패턴</div>
                    <div className="font-medium">
                      {(typeof selectedReference.structure_pattern === "object" && selectedReference.structure_pattern?.framework) || "분석 필요"}
                    </div>
                  </div>
                  <div>
                    <div className="text-gray-500 mb-1">세그먼트</div>
                    <div className="font-medium">{selectedReference.segments?.length || 0}개</div>
                  </div>
                  <div>
                    <div className="text-gray-500 mb-1">영상 길이</div>
                    <div className="font-medium">
                      {selectedReference.duration
                        ? `${Math.round(selectedReference.duration)}초`
                        : "-"}
                    </div>
                  </div>
                </div>

                {typeof selectedReference.structure_pattern === "object" && selectedReference.structure_pattern?.flow && (
                  <div className="mt-4 pt-4 border-t border-primary-200">
                    <div className="text-gray-500 text-sm mb-2">영상 흐름</div>
                    <div className="flex flex-wrap gap-2">
                      {selectedReference.structure_pattern.flow.map((item, idx) => (
                        <span
                          key={idx}
                          className="inline-flex items-center px-2 py-1 bg-white rounded text-xs"
                        >
                          {idx + 1}. {item}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Reference Points Selection */}
            {selectedReference && (
              <div className="card p-6 border-2 border-gray-200">
                <div className="flex items-center gap-2 mb-4">
                  <Sparkles className="w-5 h-5 text-purple-600" />
                  <h3 className="font-semibold text-gray-900">참고할 포인트 선택</h3>
                  <span className="text-sm text-gray-500">(스토리보드 생성에 반영됩니다)</span>
                </div>

                <div className="space-y-6">
                  {/* Structure & Flow */}
                  <div className="space-y-3">
                    <h4 className="text-sm font-medium text-gray-700 border-b pb-2">구조 및 흐름</h4>
                    <div className="flex flex-wrap gap-4">
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={selectedReferencePoints.useStructure}
                          onChange={(e) => setSelectedReferencePoints(prev => ({
                            ...prev,
                            useStructure: e.target.checked
                          }))}
                          className="w-4 h-4 text-primary-600 rounded"
                        />
                        <span className="text-sm">
                          구조 프레임워크
                          {typeof selectedReference.structure_pattern === "object" && selectedReference.structure_pattern?.framework && (
                            <span className="ml-1 text-purple-600">({selectedReference.structure_pattern.framework})</span>
                          )}
                        </span>
                      </label>
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={selectedReferencePoints.useFlow}
                          onChange={(e) => setSelectedReferencePoints(prev => ({
                            ...prev,
                            useFlow: e.target.checked
                          }))}
                          className="w-4 h-4 text-primary-600 rounded"
                        />
                        <span className="text-sm">영상 흐름 순서</span>
                      </label>
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={selectedReferencePoints.useCTAStyle}
                          onChange={(e) => setSelectedReferencePoints(prev => ({
                            ...prev,
                            useCTAStyle: e.target.checked
                          }))}
                          className="w-4 h-4 text-primary-600 rounded"
                        />
                        <span className="text-sm">CTA 스타일</span>
                      </label>
                    </div>
                  </div>

                  {/* Hook Points */}
                  {selectedReference.hook_points && selectedReference.hook_points.length > 0 && (
                    <div className="space-y-3">
                      <div className="flex items-center justify-between border-b pb-2">
                        <h4 className="text-sm font-medium text-gray-700">후킹 포인트</h4>
                        <button
                          onClick={() => {
                            const allIndices = selectedReference.hook_points.map((_, i) => i);
                            const allSelected = allIndices.every(i => selectedReferencePoints.selectedHookPoints.includes(i));
                            setSelectedReferencePoints(prev => ({
                              ...prev,
                              selectedHookPoints: allSelected ? [] : allIndices
                            }));
                          }}
                          className="text-xs text-primary-600 hover:underline"
                        >
                          {selectedReference.hook_points.every((_, i) => selectedReferencePoints.selectedHookPoints.includes(i)) ? '전체 해제' : '전체 선택'}
                        </button>
                      </div>
                      <div className="grid md:grid-cols-2 gap-2">
                        {selectedReference.hook_points.map((hook, idx) => (
                          <label
                            key={idx}
                            className={`flex items-start gap-2 p-2 rounded-lg cursor-pointer transition-colors ${
                              selectedReferencePoints.selectedHookPoints.includes(idx)
                                ? 'bg-yellow-50 border border-yellow-200'
                                : 'bg-gray-50 border border-transparent hover:bg-gray-100'
                            }`}
                          >
                            <input
                              type="checkbox"
                              checked={selectedReferencePoints.selectedHookPoints.includes(idx)}
                              onChange={(e) => {
                                setSelectedReferencePoints(prev => ({
                                  ...prev,
                                  selectedHookPoints: e.target.checked
                                    ? [...prev.selectedHookPoints, idx]
                                    : prev.selectedHookPoints.filter(i => i !== idx)
                                }));
                              }}
                              className="w-4 h-4 mt-0.5 text-yellow-600 rounded"
                            />
                            <div className="flex-1 min-w-0">
                              <div className="text-sm font-medium text-gray-800">{hook.hook_type}</div>
                              {hook.description && (
                                <div className="text-xs text-gray-500 line-clamp-2">{hook.description}</div>
                              )}
                            </div>
                          </label>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Segments */}
                  {selectedReference.segments && selectedReference.segments.length > 0 && (
                    <div className="space-y-3">
                      <div className="flex items-center justify-between border-b pb-2">
                        <h4 className="text-sm font-medium text-gray-700">세그먼트 (장면 구성)</h4>
                        <button
                          onClick={() => {
                            const allIndices = selectedReference.segments.map((_, i) => i);
                            const allSelected = allIndices.every(i => selectedReferencePoints.selectedSegments.includes(i));
                            setSelectedReferencePoints(prev => ({
                              ...prev,
                              selectedSegments: allSelected ? [] : allIndices
                            }));
                          }}
                          className="text-xs text-primary-600 hover:underline"
                        >
                          {selectedReference.segments.every((_, i) => selectedReferencePoints.selectedSegments.includes(i)) ? '전체 해제' : '전체 선택'}
                        </button>
                      </div>
                      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-2">
                        {selectedReference.segments.map((segment, idx) => (
                          <label
                            key={idx}
                            className={`flex items-start gap-2 p-2 rounded-lg cursor-pointer transition-colors ${
                              selectedReferencePoints.selectedSegments.includes(idx)
                                ? 'bg-blue-50 border border-blue-200'
                                : 'bg-gray-50 border border-transparent hover:bg-gray-100'
                            }`}
                          >
                            <input
                              type="checkbox"
                              checked={selectedReferencePoints.selectedSegments.includes(idx)}
                              onChange={(e) => {
                                setSelectedReferencePoints(prev => ({
                                  ...prev,
                                  selectedSegments: e.target.checked
                                    ? [...prev.selectedSegments, idx]
                                    : prev.selectedSegments.filter(i => i !== idx)
                                }));
                              }}
                              className="w-4 h-4 mt-0.5 text-blue-600 rounded"
                            />
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2">
                                <span className="text-xs font-mono text-gray-400">#{idx + 1}</span>
                                <span className="text-sm font-medium text-gray-800 capitalize">
                                  {segment.segment_type.replace(/_/g, ' ')}
                                </span>
                              </div>
                              <div className="text-xs text-gray-500 line-clamp-1">{segment.visual_description}</div>
                            </div>
                          </label>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Selling Points */}
                  {selectedReference.selling_points && selectedReference.selling_points.length > 0 && (
                    <div className="space-y-3">
                      <div className="flex items-center justify-between border-b pb-2">
                        <h4 className="text-sm font-medium text-gray-700">셀링 포인트</h4>
                        <button
                          onClick={() => {
                            const allIndices = selectedReference.selling_points.map((_, i) => i);
                            const allSelected = allIndices.every(i => selectedReferencePoints.selectedSellingPoints.includes(i));
                            setSelectedReferencePoints(prev => ({
                              ...prev,
                              selectedSellingPoints: allSelected ? [] : allIndices
                            }));
                          }}
                          className="text-xs text-primary-600 hover:underline"
                        >
                          {selectedReference.selling_points.every((_, i) => selectedReferencePoints.selectedSellingPoints.includes(i)) ? '전체 해제' : '전체 선택'}
                        </button>
                      </div>
                      <div className="grid md:grid-cols-2 gap-2">
                        {selectedReference.selling_points.map((sp, idx) => (
                          <label
                            key={idx}
                            className={`flex items-start gap-2 p-2 rounded-lg cursor-pointer transition-colors ${
                              selectedReferencePoints.selectedSellingPoints.includes(idx)
                                ? 'bg-green-50 border border-green-200'
                                : 'bg-gray-50 border border-transparent hover:bg-gray-100'
                            }`}
                          >
                            <input
                              type="checkbox"
                              checked={selectedReferencePoints.selectedSellingPoints.includes(idx)}
                              onChange={(e) => {
                                setSelectedReferencePoints(prev => ({
                                  ...prev,
                                  selectedSellingPoints: e.target.checked
                                    ? [...prev.selectedSellingPoints, idx]
                                    : prev.selectedSellingPoints.filter(i => i !== idx)
                                }));
                              }}
                              className="w-4 h-4 mt-0.5 text-green-600 rounded"
                            />
                            <div className="flex-1 min-w-0">
                              <div className="text-sm font-medium text-gray-800">{sp.claim}</div>
                              <div className="text-xs text-gray-500">{sp.persuasion_technique}</div>
                            </div>
                          </label>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                {/* Summary */}
                <div className="mt-6 pt-4 border-t bg-gray-50 -mx-6 -mb-6 px-6 pb-6 rounded-b-lg">
                  <div className="text-sm text-gray-600">
                    <span className="font-medium">선택된 포인트: </span>
                    {selectedReferencePoints.useStructure && <span className="badge badge-purple mr-1">구조</span>}
                    {selectedReferencePoints.useFlow && <span className="badge badge-purple mr-1">흐름</span>}
                    {selectedReferencePoints.useCTAStyle && <span className="badge badge-purple mr-1">CTA</span>}
                    {selectedReferencePoints.selectedHookPoints.length > 0 && (
                      <span className="badge badge-yellow mr-1">후킹 {selectedReferencePoints.selectedHookPoints.length}개</span>
                    )}
                    {selectedReferencePoints.selectedSegments.length > 0 && (
                      <span className="badge badge-blue mr-1">세그먼트 {selectedReferencePoints.selectedSegments.length}개</span>
                    )}
                    {selectedReferencePoints.selectedSellingPoints.length > 0 && (
                      <span className="badge badge-green mr-1">셀링 {selectedReferencePoints.selectedSellingPoints.length}개</span>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Step 3: Creative Input */}
        {currentStep === 3 && (
          <div className="space-y-6 animate-fadeIn">
            <div className="text-center mb-8">
              <h1 className="text-2xl font-bold text-gray-900">영상 컨셉을 입력하세요</h1>
              <p className="text-gray-600 mt-2">
                원하는 영상의 컨셉과 참고 이미지를 제공하면 AI가 스토리보드를 생성합니다
              </p>
            </div>

            <div className="grid lg:grid-cols-2 gap-6">
              {/* Left Column: Concept & Settings */}
              <div className="space-y-6">
                {/* Concept Input */}
                <div className="card p-6">
                  <label className="block mb-2">
                    <span className="text-sm font-medium text-gray-700">영상 컨셉 / 요청사항</span>
                    <span className="text-red-500 ml-1">*</span>
                  </label>
                  <textarea
                    value={creativeInput.concept}
                    onChange={(e) => setCreativeInput(prev => ({ ...prev, concept: e.target.value }))}
                    placeholder="예: 20대 여성 타겟의 수분 세럼 광고영상. 깨끗하고 촉촉한 피부를 강조하며, 제품의 수분감을 시각적으로 표현해주세요. 후반부에 사용 전후 비교 장면을 넣어주세요."
                    className="w-full h-32 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 resize-none"
                  />
                  <p className="text-xs text-gray-500 mt-2">
                    구체적으로 작성할수록 더 정확한 스토리보드가 생성됩니다
                  </p>
                </div>

                {/* Duration & Style Settings */}
                <div className="card p-6 space-y-4">
                  <h3 className="font-medium text-gray-900">영상 설정</h3>

                  {/* Target Duration */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      목표 영상 길이
                    </label>
                    <div className="flex items-center gap-4">
                      <input
                        type="range"
                        min="15"
                        max="120"
                        step="5"
                        value={creativeInput.targetDuration}
                        onChange={(e) => setCreativeInput(prev => ({ ...prev, targetDuration: parseInt(e.target.value) }))}
                        className="flex-1"
                      />
                      <span className="text-sm font-medium text-gray-900 w-16 text-right">
                        {creativeInput.targetDuration}초
                      </span>
                    </div>
                    <div className="flex justify-between text-xs text-gray-400 mt-1">
                      <span>15초</span>
                      <span>60초</span>
                      <span>120초</span>
                    </div>
                  </div>

                  {/* Mood Selection */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      영상 분위기
                    </label>
                    <div className="grid grid-cols-2 gap-2">
                      {MOOD_OPTIONS.map((mood) => (
                        <button
                          key={mood.value}
                          onClick={() => setCreativeInput(prev => ({ ...prev, mood: mood.value }))}
                          className={`px-3 py-2 text-sm rounded-lg border transition-all ${
                            creativeInput.mood === mood.value
                              ? 'border-primary-500 bg-primary-50 text-primary-700'
                              : 'border-gray-200 hover:border-gray-300 text-gray-700'
                          }`}
                        >
                          {mood.label}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Style Selection */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      영상 스타일
                    </label>
                    <div className="grid grid-cols-2 gap-2">
                      {STYLE_OPTIONS.map((style) => (
                        <button
                          key={style.value}
                          onClick={() => setCreativeInput(prev => ({ ...prev, style: style.value }))}
                          className={`px-3 py-2 text-sm rounded-lg border transition-all ${
                            creativeInput.style === style.value
                              ? 'border-primary-500 bg-primary-50 text-primary-700'
                              : 'border-gray-200 hover:border-gray-300 text-gray-700'
                          }`}
                        >
                          {style.label}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Additional Notes */}
                <div className="card p-6">
                  <label className="block mb-2">
                    <span className="text-sm font-medium text-gray-700">추가 메모 (선택사항)</span>
                  </label>
                  <textarea
                    value={creativeInput.additionalNotes}
                    onChange={(e) => setCreativeInput(prev => ({ ...prev, additionalNotes: e.target.value }))}
                    placeholder="예: 배경음악은 밝고 경쾌한 느낌으로, 자막은 한글로 표시해주세요."
                    className="w-full h-20 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 resize-none"
                  />
                </div>
              </div>

              {/* Right Column: Reference Images */}
              <div className="space-y-6">
                <div className="card p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="font-medium text-gray-900">참고 이미지</h3>
                    <span className="text-sm text-gray-500">{referenceImages.length}개 업로드됨</span>
                  </div>

                  {/* Upload Area */}
                  <div
                    onClick={() => referenceImageInputRef.current?.click()}
                    className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center cursor-pointer hover:border-primary-400 hover:bg-primary-50 transition-all"
                  >
                    <Upload className="w-10 h-10 mx-auto text-gray-400 mb-3" />
                    <p className="text-sm font-medium text-gray-700">이미지를 드래그하거나 클릭하여 업로드</p>
                    <p className="text-xs text-gray-500 mt-1">제품 이미지, 배경 이미지, 무드보드 등</p>
                    <input
                      ref={referenceImageInputRef}
                      type="file"
                      accept="image/jpeg,image/png,image/webp"
                      multiple
                      className="hidden"
                      onChange={(e) => {
                        const files = Array.from(e.target.files || []);
                        files.forEach(file => {
                          const id = Math.random().toString(36).substring(7);
                          const previewUrl = URL.createObjectURL(file);
                          setReferenceImages(prev => [...prev, {
                            id,
                            file,
                            previewUrl,
                            type: "other",
                            isUploading: false,
                          }]);
                        });
                        e.target.value = "";
                      }}
                    />
                  </div>

                  {/* Uploaded Images Grid */}
                  {referenceImages.length > 0 && (
                    <div className="grid grid-cols-2 gap-3 mt-4">
                      {referenceImages.map((img) => (
                        <div key={img.id} className="relative group">
                          <div className="aspect-video bg-gray-100 rounded-lg overflow-hidden">
                            <Image
                              src={img.previewUrl}
                              alt="Reference"
                              fill
                              className="object-cover"
                              sizes="(max-width: 768px) 50vw, 25vw"
                            />
                          </div>
                          {/* Type Selector */}
                          <select
                            value={img.type}
                            onChange={(e) => {
                              setReferenceImages(prev => prev.map(i =>
                                i.id === img.id ? { ...i, type: e.target.value as ReferenceImage["type"] } : i
                              ));
                            }}
                            className="absolute bottom-2 left-2 px-2 py-1 text-xs bg-white/90 rounded border border-gray-200"
                          >
                            <option value="product">제품</option>
                            <option value="background">배경</option>
                            <option value="mood">무드보드</option>
                            <option value="other">기타</option>
                          </select>
                          {/* Remove Button */}
                          <button
                            onClick={() => {
                              URL.revokeObjectURL(img.previewUrl);
                              setReferenceImages(prev => prev.filter(i => i.id !== img.id));
                            }}
                            className="absolute top-2 right-2 p-1 bg-red-100 text-red-600 rounded opacity-0 group-hover:opacity-100 transition-opacity"
                          >
                            <X className="w-4 h-4" />
                          </button>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Tips */}
                  <div className="mt-4 p-3 bg-blue-50 rounded-lg">
                    <p className="text-sm font-medium text-blue-800 mb-1">팁</p>
                    <ul className="text-xs text-blue-700 space-y-1">
                      <li>• 제품 이미지: 영상에 등장할 제품 사진</li>
                      <li>• 배경 이미지: 원하는 배경이나 장소</li>
                      <li>• 무드보드: 참고할 분위기나 색감</li>
                    </ul>
                  </div>
                </div>

                {/* Summary Card */}
                <div className="card p-6 bg-gradient-to-br from-primary-50 to-purple-50">
                  <h3 className="font-medium text-gray-900 mb-3">입력 요약</h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600">브랜드/제품</span>
                      <span className="font-medium text-gray-900">
                        {selectedProduct ? selectedProduct.name : selectedBrand ? brands.find(b => b.id === selectedBrandId)?.name : "-"}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">레퍼런스</span>
                      <span className="font-medium text-gray-900">
                        {selectedReference?.title || "-"}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">선택 포인트</span>
                      <span className="font-medium text-gray-900">
                        {[
                          selectedReferencePoints.useStructure && "구조",
                          selectedReferencePoints.selectedHookPoints.length > 0 && `후킹 ${selectedReferencePoints.selectedHookPoints.length}`,
                          selectedReferencePoints.selectedSegments.length > 0 && `세그먼트 ${selectedReferencePoints.selectedSegments.length}`,
                        ].filter(Boolean).join(", ") || "-"}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">목표 길이</span>
                      <span className="font-medium text-gray-900">{creativeInput.targetDuration}초</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">분위기/스타일</span>
                      <span className="font-medium text-gray-900">
                        {MOOD_OPTIONS.find(m => m.value === creativeInput.mood)?.label} / {STYLE_OPTIONS.find(s => s.value === creativeInput.style)?.label}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">참고 이미지</span>
                      <span className="font-medium text-gray-900">{referenceImages.length}개</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Step 4: Storyboard Editor */}
        {currentStep === 4 && (
          <div className="space-y-6 animate-fadeIn">
            <div className="text-center mb-8">
              <h1 className="text-2xl font-bold text-gray-900">스토리보드 편집</h1>
              <p className="text-gray-600 mt-2">
                장면별 스크립트와 시간, 전환 효과를 편집하세요
              </p>
            </div>

            {/* Storyboard Header */}
            <div className="card p-4 bg-gray-50 flex flex-wrap items-center justify-between gap-4">
              <div className="flex items-center gap-4">
                {!storyboard ? (
                  <button
                    onClick={() => setShowGenerateModal(true)}
                    disabled={isGeneratingStoryboard}
                    className="btn-primary px-4 py-2 flex items-center gap-2"
                  >
                    {isGeneratingStoryboard ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        생성 중...
                      </>
                    ) : (
                      <>
                        <Sparkles className="w-4 h-4" />
                        스토리보드 생성
                      </>
                    )}
                  </button>
                ) : (
                  <>
                    <div className="flex items-center gap-2 text-sm text-gray-600">
                      <Clock className="w-4 h-4" />
                      <span>
                        총 <span className="font-semibold text-gray-900">{totalDuration.toFixed(1)}초</span>
                      </span>
                    </div>
                    <div className="flex items-center gap-2 text-sm text-gray-600">
                      <LayoutGrid className="w-4 h-4" />
                      <span>
                        <span className="font-semibold text-gray-900">{storyboard.scenes.length}</span>개 장면
                      </span>
                    </div>
                    <div className="flex items-center gap-2 text-sm text-gray-500">
                      <History className="w-4 h-4" />
                      <span>버전 {storyboard.version}</span>
                    </div>
                  </>
                )}
              </div>
              {storyboard && (
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setShowAddSceneModal(true)}
                    className="btn-secondary px-3 py-1.5 text-sm flex items-center gap-1"
                  >
                    <Plus className="w-4 h-4" />
                    장면 추가
                  </button>
                  <button
                    onClick={() => setShowGenerateModal(true)}
                    disabled={isGeneratingStoryboard}
                    className="btn-secondary px-3 py-1.5 text-sm flex items-center gap-1"
                  >
                    <RefreshCw className="w-4 h-4" />
                    재생성
                  </button>
                </div>
              )}
            </div>

            {/* No Storyboard State */}
            {!storyboard && !isGeneratingStoryboard && (
              <div className="text-center py-16">
                <div className="w-20 h-20 rounded-full bg-gray-100 flex items-center justify-center mx-auto mb-4">
                  <LayoutGrid className="w-10 h-10 text-gray-400" />
                </div>
                <h2 className="text-xl font-semibold text-gray-700 mb-2">스토리보드가 없습니다</h2>
                <p className="text-gray-500 mb-4">스토리보드를 생성하여 영상 구조를 설계하세요</p>
                <button
                  onClick={() => setShowGenerateModal(true)}
                  className="btn-primary px-6 py-2 flex items-center gap-2 mx-auto"
                >
                  <Sparkles className="w-4 h-4" />
                  스토리보드 생성하기
                </button>
              </div>
            )}

            {/* Generating State */}
            {isGeneratingStoryboard && (
              <div className="text-center py-16">
                <Loader2 className="w-12 h-12 text-primary-500 animate-spin mx-auto mb-4" />
                <h2 className="text-xl font-semibold text-gray-700 mb-2">스토리보드 생성 중...</h2>
                <p className="text-gray-500">AI가 최적의 영상 구조를 설계하고 있습니다</p>
              </div>
            )}

            {/* Storyboard Editor */}
            {storyboard && storyboard.scenes.length > 0 && !isGeneratingStoryboard && (
              <div className="grid lg:grid-cols-3 gap-6">
                {/* Timeline View (Left) */}
                <div className="lg:col-span-1 space-y-4">
                  <h3 className="font-semibold text-gray-700 flex items-center gap-2">
                    <LayoutGrid className="w-4 h-4" />
                    타임라인
                  </h3>
                  <div className="space-y-2 max-h-[600px] overflow-y-auto pr-2">
                    {storyboard.scenes.map((scene, index) => {
                      const imageUrl = getSceneImageUrl(scene.scene_number);
                      const isSelected = selectedSceneNumber === scene.scene_number;

                      return (
                        <div
                          key={scene.scene_number}
                          onClick={() => {
                            savePendingUpdates();
                            setSelectedSceneNumber(scene.scene_number);
                          }}
                          className={`p-3 rounded-lg border-2 cursor-pointer transition-all ${
                            isSelected
                              ? "border-primary-500 bg-primary-50"
                              : "border-gray-200 hover:border-gray-300 bg-white"
                          }`}
                        >
                          <div className="flex gap-3">
                            {/* Thumbnail */}
                            <div className="w-20 h-14 bg-gray-100 rounded overflow-hidden flex-shrink-0 relative">
                              {imageUrl ? (
                                <Image
                                  src={imageUrl}
                                  alt={`Scene ${scene.scene_number + 1}`}
                                  fill
                                  className="object-cover"
                                  sizes="80px"
                                />
                              ) : (
                                <div className="w-full h-full flex items-center justify-center">
                                  <ImageIcon className="w-6 h-6 text-gray-300" />
                                </div>
                              )}
                            </div>

                            {/* Scene Info */}
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2 mb-1">
                                <span className="w-5 h-5 rounded-full bg-primary-100 text-primary-700 text-xs font-bold flex items-center justify-center flex-shrink-0">
                                  {index + 1}
                                </span>
                                <span className="text-xs text-gray-500 capitalize truncate">
                                  {scene.scene_type.replace(/_/g, " ")}
                                </span>
                              </div>
                              <p className="text-sm font-medium text-gray-800 line-clamp-1">
                                {scene.title || "제목 없음"}
                              </p>
                              <p className="text-xs text-gray-400 mt-0.5">
                                {scene.duration_seconds.toFixed(1)}초
                              </p>
                            </div>

                            {/* Actions */}
                            <div className="flex flex-col gap-1 flex-shrink-0">
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleMoveScene(scene.scene_number, "up");
                                }}
                                disabled={index === 0}
                                className="p-1 text-gray-400 hover:text-gray-600 disabled:opacity-30"
                              >
                                <ChevronUp className="w-4 h-4" />
                              </button>
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleMoveScene(scene.scene_number, "down");
                                }}
                                disabled={index === storyboard.scenes.length - 1}
                                className="p-1 text-gray-400 hover:text-gray-600 disabled:opacity-30"
                              >
                                <ChevronDown className="w-4 h-4" />
                              </button>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Scene Detail Panel (Right) */}
                <div className="lg:col-span-2">
                  {selectedScene ? (
                    <div className="card p-6 space-y-6">
                      {/* Scene Header */}
                      <div className="flex items-center justify-between pb-4 border-b">
                        <div className="flex items-center gap-3">
                          <span className="w-8 h-8 rounded-full bg-primary-100 text-primary-700 text-sm font-bold flex items-center justify-center">
                            {storyboard.scenes.findIndex((s) => s.scene_number === selectedSceneNumber) + 1}
                          </span>
                          <div>
                            <h3 className="font-semibold text-gray-900">
                              {selectedScene.title || "제목 없음"}
                            </h3>
                            <p className="text-sm text-gray-500 capitalize">
                              {selectedScene.scene_type.replace(/_/g, " ")}
                            </p>
                          </div>
                        </div>
                        <button
                          onClick={() => handleDeleteScene(selectedScene.scene_number)}
                          className="p-2 text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                        >
                          <Trash2 className="w-5 h-5" />
                        </button>
                      </div>

                      {/* Scene Image */}
                      <div className="aspect-video bg-gray-100 rounded-lg overflow-hidden relative group">
                        {(() => {
                          const sceneIndex = storyboard.scenes.findIndex((s) => s.scene_number === selectedSceneNumber);
                          const asset = sceneAssets[sceneIndex];
                          const isGenerating = asset?.isGenerating || false;

                          if (isGenerating) {
                            return (
                              <div className="absolute inset-0 flex flex-col items-center justify-center bg-gray-100">
                                <RefreshCw className="w-10 h-10 text-primary-500 animate-spin mb-2" />
                                <span className="text-sm text-gray-500">AI 이미지 생성 중...</span>
                              </div>
                            );
                          }

                          if (getSceneImageUrl(selectedScene.scene_number)) {
                            return (
                              <>
                                <Image
                                  src={getSceneImageUrl(selectedScene.scene_number)!}
                                  alt={`Scene ${selectedScene.scene_number + 1}`}
                                  fill
                                  className="object-cover"
                                  sizes="(max-width: 768px) 100vw, 50vw"
                                  priority
                                />
                                {/* Overlay buttons on hover */}
                                <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-3">
                                  <input
                                    type="file"
                                    accept="image/jpeg,image/png,image/webp"
                                    className="hidden"
                                    id={`step4-scene-upload-${selectedScene.scene_number}`}
                                    onChange={(e) => {
                                      const file = e.target.files?.[0];
                                      if (file && sceneIndex >= 0) {
                                        const mockSegment = {
                                          start_time: 0,
                                          end_time: selectedScene.duration_seconds || 3,
                                          segment_type: selectedScene.scene_type || "scene",
                                          visual_description: selectedScene.description || "",
                                          engagement_score: 0,
                                          techniques: [],
                                        };
                                        handleFileUpload(sceneIndex, file, mockSegment);
                                      }
                                      e.target.value = "";
                                    }}
                                  />
                                  <button
                                    onClick={() => document.getElementById(`step4-scene-upload-${selectedScene.scene_number}`)?.click()}
                                    className="px-3 py-2 bg-white text-gray-800 rounded-lg text-sm font-medium hover:bg-gray-100 flex items-center gap-2"
                                  >
                                    <Upload className="w-4 h-4" />
                                    변경
                                  </button>
                                  <button
                                    onClick={() => {
                                      if (sceneIndex >= 0) {
                                        const mockSegment = {
                                          start_time: 0,
                                          end_time: selectedScene.duration_seconds || 3,
                                          segment_type: selectedScene.scene_type || "scene",
                                          visual_description: `${selectedBrand?.name || ""} ${selectedProduct?.name || ""} - ${selectedScene.description || selectedScene.visual_direction || selectedScene.title || ""}`.trim(),
                                          engagement_score: 0,
                                          techniques: [],
                                        };
                                        handleAIGenerate(sceneIndex, mockSegment);
                                      }
                                    }}
                                    className="px-3 py-2 bg-primary-500 text-white rounded-lg text-sm font-medium hover:bg-primary-600 flex items-center gap-2"
                                  >
                                    <Wand2 className="w-4 h-4" />
                                    AI 재생성
                                  </button>
                                  <button
                                    onClick={() => sceneIndex >= 0 && handleRemoveImage(sceneIndex)}
                                    className="px-3 py-2 bg-red-500 text-white rounded-lg text-sm font-medium hover:bg-red-600 flex items-center gap-2"
                                  >
                                    <X className="w-4 h-4" />
                                    삭제
                                  </button>
                                </div>
                              </>
                            );
                          }

                          return (
                            <div className="w-full h-full flex flex-col items-center justify-center">
                              <ImageIcon className="w-12 h-12 text-gray-300 mb-3" />
                              <p className="text-sm text-gray-400 mb-4">이미지 없음</p>
                              <div className="flex gap-2">
                                <input
                                  type="file"
                                  accept="image/jpeg,image/png,image/webp"
                                  className="hidden"
                                  id={`step4-scene-upload-empty-${selectedScene.scene_number}`}
                                  onChange={(e) => {
                                    const file = e.target.files?.[0];
                                    if (file && sceneIndex >= 0) {
                                      const mockSegment = {
                                        start_time: 0,
                                        end_time: selectedScene.duration_seconds || 3,
                                        segment_type: selectedScene.scene_type || "scene",
                                        visual_description: selectedScene.description || "",
                                        engagement_score: 0,
                                        techniques: [],
                                      };
                                      handleFileUpload(sceneIndex, file, mockSegment);
                                    }
                                    e.target.value = "";
                                  }}
                                />
                                <button
                                  onClick={() => document.getElementById(`step4-scene-upload-empty-${selectedScene.scene_number}`)?.click()}
                                  className="px-3 py-2 btn-secondary text-sm flex items-center gap-2"
                                >
                                  <Upload className="w-4 h-4" />
                                  업로드
                                </button>
                                <button
                                  onClick={() => {
                                    if (sceneIndex >= 0) {
                                      const mockSegment = {
                                        start_time: 0,
                                        end_time: selectedScene.duration_seconds || 3,
                                        segment_type: selectedScene.scene_type || "scene",
                                        visual_description: `${selectedBrand?.name || ""} ${selectedProduct?.name || ""} - ${selectedScene.description || selectedScene.visual_direction || selectedScene.title || ""}`.trim(),
                                        engagement_score: 0,
                                        techniques: [],
                                      };
                                      handleAIGenerate(sceneIndex, mockSegment);
                                    }
                                  }}
                                  className="px-3 py-2 btn-primary text-sm flex items-center gap-2"
                                >
                                  <Wand2 className="w-4 h-4" />
                                  AI 생성
                                </button>
                              </div>
                            </div>
                          );
                        })()}
                      </div>

                      {/* Edit Fields */}
                      <div className="grid md:grid-cols-2 gap-4">
                        {/* Title */}
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            <Type className="w-4 h-4 inline mr-1" />
                            제목
                          </label>
                          <input
                            type="text"
                            value={pendingUpdates.title ?? selectedScene.title}
                            onChange={(e) => handleSceneFieldUpdate("title", e.target.value)}
                            className="input w-full"
                            placeholder="장면 제목"
                          />
                        </div>

                        {/* Duration */}
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            <Clock className="w-4 h-4 inline mr-1" />
                            시간 (초)
                          </label>
                          <input
                            type="number"
                            value={pendingUpdates.duration_seconds ?? selectedScene.duration_seconds}
                            onChange={(e) => handleSceneFieldUpdate("duration_seconds", parseFloat(e.target.value) || 0)}
                            className="input w-full"
                            min="0.5"
                            step="0.5"
                          />
                        </div>
                      </div>

                      {/* Description */}
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          <Palette className="w-4 h-4 inline mr-1" />
                          비주얼 설명 (이미지 생성용)
                        </label>
                        <textarea
                          value={pendingUpdates.description ?? selectedScene.description}
                          onChange={(e) => handleSceneFieldUpdate("description", e.target.value)}
                          className="input w-full h-20 resize-none"
                          placeholder="이 장면의 시각적 요소를 설명하세요..."
                        />
                      </div>

                      {/* Narration Script */}
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          <FileText className="w-4 h-4 inline mr-1" />
                          나레이션 스크립트
                        </label>
                        <textarea
                          value={pendingUpdates.narration_script ?? selectedScene.narration_script ?? ""}
                          onChange={(e) => handleSceneFieldUpdate("narration_script", e.target.value)}
                          className="input w-full h-24 resize-none"
                          placeholder="이 장면에서 들려줄 나레이션 스크립트..."
                        />
                      </div>

                      {/* Visual Direction */}
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          <Eye className="w-4 h-4 inline mr-1" />
                          연출 방향
                        </label>
                        <textarea
                          value={pendingUpdates.visual_direction ?? selectedScene.visual_direction ?? ""}
                          onChange={(e) => handleSceneFieldUpdate("visual_direction", e.target.value)}
                          className="input w-full h-16 resize-none"
                          placeholder="카메라 앵글, 효과, 움직임 등..."
                        />
                      </div>

                      <div className="grid md:grid-cols-2 gap-4">
                        {/* Transition Effect */}
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            <ArrowRight className="w-4 h-4 inline mr-1" />
                            전환 효과
                          </label>
                          <select
                            value={pendingUpdates.transition_effect ?? selectedScene.transition_effect ?? "cut"}
                            onChange={(e) => handleSceneFieldUpdate("transition_effect", e.target.value)}
                            className="input w-full"
                          >
                            {TRANSITION_EFFECTS.map((effect) => (
                              <option key={effect.value} value={effect.value}>
                                {effect.label}
                              </option>
                            ))}
                          </select>
                        </div>

                        {/* Background Music Suggestion */}
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            <Music className="w-4 h-4 inline mr-1" />
                            배경 음악 제안
                          </label>
                          <input
                            type="text"
                            value={pendingUpdates.background_music_suggestion ?? selectedScene.background_music_suggestion ?? ""}
                            onChange={(e) => handleSceneFieldUpdate("background_music_suggestion", e.target.value)}
                            className="input w-full"
                            placeholder="분위기, 장르, 템포 등..."
                          />
                        </div>
                      </div>

                      {/* Subtitle Text */}
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          <Type className="w-4 h-4 inline mr-1" />
                          자막 텍스트
                        </label>
                        <textarea
                          value={pendingUpdates.subtitle_text ?? selectedScene.subtitle_text ?? ""}
                          onChange={(e) => handleSceneFieldUpdate("subtitle_text", e.target.value)}
                          className="input w-full h-16 resize-none"
                          placeholder="화면에 표시될 자막..."
                        />
                      </div>

                      {/* Save Button */}
                      {Object.keys(pendingUpdates).length > 0 && (
                        <div className="flex justify-end pt-4 border-t">
                          <button
                            onClick={savePendingUpdates}
                            disabled={updateSceneMutation.isPending}
                            className="btn-primary px-4 py-2 flex items-center gap-2"
                          >
                            {updateSceneMutation.isPending ? (
                              <Loader2 className="w-4 h-4 animate-spin" />
                            ) : (
                              <Save className="w-4 h-4" />
                            )}
                            저장
                          </button>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="card p-6 text-center text-gray-500">
                      <LayoutGrid className="w-12 h-12 mx-auto mb-2 opacity-50" />
                      <p>왼쪽에서 장면을 선택하세요</p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Generate Storyboard Modal */}
            {showGenerateModal && (
              <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                <div className="bg-white rounded-xl shadow-xl max-w-lg w-full mx-4 p-6 max-h-[90vh] overflow-y-auto">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold">AI 스토리보드 생성</h3>
                    <button
                      onClick={() => setShowGenerateModal(false)}
                      className="p-1 text-gray-400 hover:text-gray-600"
                    >
                      <X className="w-5 h-5" />
                    </button>
                  </div>

                  {/* Input Summary */}
                  <div className="bg-gray-50 rounded-lg p-4 mb-6 space-y-3">
                    <h4 className="font-medium text-gray-900 text-sm">입력 내용 확인</h4>

                    <div className="space-y-2 text-sm">
                      <div>
                        <span className="text-gray-500">컨셉: </span>
                        <span className="text-gray-900">{creativeInput.concept || "-"}</span>
                      </div>
                      <div className="flex gap-4">
                        <span>
                          <span className="text-gray-500">길이: </span>
                          <span className="text-gray-900">{creativeInput.targetDuration}초</span>
                        </span>
                        <span>
                          <span className="text-gray-500">분위기: </span>
                          <span className="text-gray-900">{MOOD_OPTIONS.find(m => m.value === creativeInput.mood)?.label}</span>
                        </span>
                      </div>
                      <div className="flex gap-4">
                        <span>
                          <span className="text-gray-500">스타일: </span>
                          <span className="text-gray-900">{STYLE_OPTIONS.find(s => s.value === creativeInput.style)?.label}</span>
                        </span>
                        <span>
                          <span className="text-gray-500">참고 이미지: </span>
                          <span className="text-gray-900">{referenceImages.length}개</span>
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-500">레퍼런스 포인트: </span>
                        <span className="text-gray-900">
                          {[
                            selectedReferencePoints.useStructure && "구조",
                            selectedReferencePoints.useFlow && "흐름",
                            selectedReferencePoints.selectedHookPoints.length > 0 && `후킹 ${selectedReferencePoints.selectedHookPoints.length}`,
                            selectedReferencePoints.selectedSegments.length > 0 && `세그먼트 ${selectedReferencePoints.selectedSegments.length}`,
                          ].filter(Boolean).join(", ") || "없음"}
                        </span>
                      </div>
                    </div>
                  </div>

                  <p className="text-gray-600 mb-4 text-sm">
                    스토리보드 생성 방식을 선택하세요
                  </p>

                  <div className="space-y-3">
                    <button
                      onClick={() => handleGenerateStoryboard("reference_structure")}
                      disabled={isGeneratingStoryboard}
                      className="w-full p-4 border-2 border-gray-200 rounded-lg text-left hover:border-primary-300 hover:bg-primary-50 transition-all disabled:opacity-50"
                    >
                      <div className="font-medium text-gray-900 mb-1">레퍼런스 구조 + 내 컨셉</div>
                      <p className="text-sm text-gray-500">
                        선택한 레퍼런스의 구조/흐름을 따르면서 입력한 컨셉을 반영합니다
                      </p>
                    </button>

                    <button
                      onClick={() => handleGenerateStoryboard("ai_optimized")}
                      disabled={isGeneratingStoryboard}
                      className="w-full p-4 border-2 border-gray-200 rounded-lg text-left hover:border-primary-300 hover:bg-primary-50 transition-all disabled:opacity-50"
                    >
                      <div className="font-medium text-gray-900 mb-1 flex items-center gap-2">
                        AI 최적화 (창작)
                        <span className="px-2 py-0.5 bg-purple-100 text-purple-700 text-xs rounded-full">
                          추천
                        </span>
                      </div>
                      <p className="text-sm text-gray-500">
                        입력한 컨셉을 기반으로 AI가 최적의 구조로 새롭게 스토리보드를 생성합니다
                      </p>
                    </button>
                  </div>

                  {isGeneratingStoryboard && (
                    <div className="mt-4 flex items-center justify-center gap-2 text-primary-600">
                      <Loader2 className="w-5 h-5 animate-spin" />
                      <span className="text-sm">스토리보드 생성 중...</span>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Add Scene Modal */}
            {showAddSceneModal && (
              <AddSceneModal
                onClose={() => setShowAddSceneModal(false)}
                onAdd={(data) => addSceneMutation.mutate(data)}
                isLoading={addSceneMutation.isPending}
                lastSceneNumber={storyboard?.scenes[storyboard.scenes.length - 1]?.scene_number ?? -1}
              />
            )}
          </div>
        )}

        {/* Step 5: Scene Images & Video Generation */}
        {currentStep === 5 && (
          <div className="space-y-6 animate-fadeIn">
            <div className="text-center mb-8">
              <h1 className="text-2xl font-bold text-gray-900">장면별 영상 제작</h1>
              <p className="text-gray-600 mt-2">
                각 장면의 영상을 개별 생성하고 최종 영상으로 합칩니다
              </p>
            </div>

            {/* Storyboard Summary */}
            {storyboard && (
              <div className="card p-4 bg-gradient-to-r from-primary-50 to-purple-50">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <LayoutGrid className="w-5 h-5 text-primary-600" />
                    <span className="font-medium text-gray-900">스토리보드 요약</span>
                  </div>
                  <button
                    onClick={() => setCurrentStep(4)}
                    className="text-sm text-primary-600 hover:underline flex items-center gap-1"
                  >
                    <Edit3 className="w-3 h-3" />
                    편집하기
                  </button>
                </div>
                <div className="flex gap-6 text-sm">
                  <span className="text-gray-600">
                    장면: <span className="font-semibold text-gray-900">{storyboard.scenes.length}개</span>
                  </span>
                  <span className="text-gray-600">
                    총 길이: <span className="font-semibold text-gray-900">{totalDuration.toFixed(1)}초</span>
                  </span>
                  <span className="text-gray-600">
                    버전: <span className="font-semibold text-gray-900">{storyboard.version}</span>
                  </span>
                </div>
              </div>
            )}

            {/* Overall Progress */}
            {sceneVideos.length > 0 && (
              <div className="card p-4 bg-blue-50 border border-blue-200">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    {isGeneratingVideo ? (
                      <RefreshCw className="w-5 h-5 text-blue-600 animate-spin" />
                    ) : allScenesCompleted ? (
                      <Check className="w-5 h-5 text-green-600" />
                    ) : (
                      <Video className="w-5 h-5 text-blue-600" />
                    )}
                    <span className="font-medium text-blue-900">
                      {isGeneratingVideo
                        ? `장면 ${processingSceneVideos[0]?.scene_number || 1} / ${storyboard?.scenes.length || 0} 영상 생성 중...`
                        : allScenesCompleted
                        ? "모든 장면 영상 생성 완료"
                        : `장면 영상 생성 진행률`}
                    </span>
                  </div>
                  <span className="text-sm text-blue-700">
                    {completedSceneVideos.length}/{sceneVideos.length} 완료
                  </span>
                </div>
                <div className="w-full bg-blue-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full transition-all ${
                      allScenesCompleted ? "bg-green-500" : "bg-blue-600"
                    }`}
                    style={{
                      width: `${(completedSceneVideos.length / sceneVideos.length) * 100}%`,
                    }}
                  />
                </div>
                {failedSceneVideos.length > 0 && (
                  <p className="text-sm text-red-600 mt-2">
                    {failedSceneVideos.length}개 장면 생성 실패 - 재생성 버튼을 클릭하여 다시 시도하세요
                  </p>
                )}
              </div>
            )}

            {/* Scene Video Grid */}
            {storyboard && storyboard.scenes.length > 0 && (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="font-medium text-gray-900">장면별 영상</h3>
                  <div className="flex items-center gap-4 text-sm">
                    {sceneVideos.length > 0 && (
                      <>
                        <span className="text-green-600">
                          완료 <span className="font-semibold">{completedSceneVideos.length}</span>
                        </span>
                        {processingSceneVideos.length > 0 && (
                          <span className="text-blue-600">
                            생성중 <span className="font-semibold">{processingSceneVideos.length}</span>
                          </span>
                        )}
                        {failedSceneVideos.length > 0 && (
                          <span className="text-red-600">
                            실패 <span className="font-semibold">{failedSceneVideos.length}</span>
                          </span>
                        )}
                      </>
                    )}
                    <button
                      onClick={() => setCurrentStep(4)}
                      className="btn-secondary px-3 py-1.5 text-sm flex items-center gap-1"
                    >
                      <Edit3 className="w-4 h-4" />
                      스토리보드 편집
                    </button>
                  </div>
                </div>

                <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {storyboard.scenes.map((scene, index) => {
                    const asset = sceneAssets[index] || {
                      sceneIndex: index,
                      id: null,
                      imageUrl: null,
                      source: null,
                      isGenerating: false,
                    };
                    const sceneVideo = sceneVideos.find(
                      (sv) => sv.scene_number === scene.scene_number
                    );

                    // Scene type color mapping
                    const getSceneTypeColor = (type: string | undefined) => {
                      switch (type) {
                        case "hook":
                          return "bg-red-100 text-red-700";
                        case "problem":
                          return "bg-orange-100 text-orange-700";
                        case "solution":
                          return "bg-green-100 text-green-700";
                        case "product_showcase":
                          return "bg-blue-100 text-blue-700";
                        case "feature":
                          return "bg-indigo-100 text-indigo-700";
                        case "benefit":
                          return "bg-purple-100 text-purple-700";
                        case "cta":
                          return "bg-pink-100 text-pink-700";
                        case "outro":
                          return "bg-gray-100 text-gray-700";
                        default:
                          return "bg-gray-100 text-gray-600";
                      }
                    };

                    return (
                      <div
                        key={scene.scene_number}
                        className={`card p-4 border-2 transition-all ${
                          sceneVideo?.status === "completed"
                            ? "border-green-300 bg-green-50/30"
                            : sceneVideo?.status === "processing"
                            ? "border-blue-300 bg-blue-50/30"
                            : sceneVideo?.status === "failed"
                            ? "border-red-300 bg-red-50/30"
                            : "border-gray-200 hover:border-gray-300"
                        }`}
                      >
                        {/* Scene Header */}
                        <div className="flex items-center justify-between mb-3">
                          <div className="flex items-center gap-2">
                            <span className="w-6 h-6 rounded-full bg-primary-100 text-primary-700 text-xs font-bold flex items-center justify-center">
                              {scene.scene_number}
                            </span>
                            <span
                              className={`px-2 py-0.5 rounded text-xs font-medium capitalize ${getSceneTypeColor(
                                scene.scene_type
                              )}`}
                            >
                              {scene.scene_type?.replace(/_/g, " ") || "장면"}
                            </span>
                          </div>
                          <div className="flex items-center gap-2">
                            <span className="text-xs text-gray-400">
                              {scene.duration_seconds?.toFixed(1) || "3.0"}초
                            </span>
                            {sceneVideo?.status === "completed" && (
                              <Check className="w-4 h-4 text-green-600" />
                            )}
                            {sceneVideo?.status === "processing" && (
                              <RefreshCw className="w-4 h-4 text-blue-600 animate-spin" />
                            )}
                            {sceneVideo?.status === "failed" && (
                              <X className="w-4 h-4 text-red-600" />
                            )}
                          </div>
                        </div>

                        {/* Video/Image Area */}
                        <div className="aspect-video bg-gray-100 rounded-lg overflow-hidden relative mb-3">
                          {sceneVideo?.status === "completed" && sceneVideo.video_url ? (
                            <video
                              src={sceneVideo.video_url}
                              controls
                              muted
                              className="w-full h-full object-cover"
                            />
                          ) : sceneVideo?.status === "processing" ? (
                            <div className="absolute inset-0 flex flex-col items-center justify-center bg-blue-50">
                              <RefreshCw className="w-10 h-10 text-blue-500 animate-spin mb-2" />
                              <span className="text-sm text-blue-700 font-medium">
                                영상 생성 중...
                              </span>
                              <span className="text-xs text-blue-500 mt-1">
                                잠시만 기다려주세요
                              </span>
                            </div>
                          ) : sceneVideo?.status === "failed" ? (
                            <div className="absolute inset-0 flex flex-col items-center justify-center bg-red-50">
                              <X className="w-10 h-10 text-red-400 mb-2" />
                              <span className="text-sm text-red-700 font-medium">
                                생성 실패
                              </span>
                              <span className="text-xs text-red-500 mt-1 px-4 text-center">
                                {sceneVideo.error_message || "알 수 없는 오류"}
                              </span>
                            </div>
                          ) : asset.imageUrl ? (
                            <Image
                              src={asset.imageUrl}
                              alt={`Scene ${scene.scene_number}`}
                              fill
                              className="object-cover"
                              sizes="(max-width: 768px) 50vw, 25vw"
                            />
                          ) : (
                            <div className="absolute inset-0 flex flex-col items-center justify-center">
                              <ImageIcon className="w-10 h-10 text-gray-300 mb-2" />
                              <span className="text-sm text-gray-400">미리보기 없음</span>
                            </div>
                          )}
                        </div>

                        {/* Scene Description */}
                        <p className="text-xs text-gray-500 line-clamp-2 mb-3">
                          {scene.description || scene.visual_direction || "시각적 설명 없음"}
                        </p>

                        {/* Regenerate Button */}
                        {sceneVideo?.status === "completed" || sceneVideo?.status === "failed" ? (
                          <button
                            onClick={() => handleRegenerateSceneVideo(scene.scene_number)}
                            disabled={isGeneratingVideo}
                            className={`w-full py-2 text-sm rounded-lg flex items-center justify-center gap-2 transition-colors ${
                              sceneVideo?.status === "failed"
                                ? "bg-red-100 text-red-700 hover:bg-red-200"
                                : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                            } disabled:opacity-50`}
                          >
                            <RefreshCw className="w-4 h-4" />
                            {sceneVideo?.status === "failed" ? "다시 생성" : "재생성"}
                          </button>
                        ) : sceneVideo?.status === "processing" ? (
                          <div className="w-full py-2 text-sm text-blue-600 text-center">
                            생성 진행 중...
                          </div>
                        ) : (
                          <div className="w-full py-2 text-sm text-gray-400 text-center">
                            영상 생성 대기 중
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Video Generation Section */}
            <div className="card p-6 bg-gray-50">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-full bg-primary-100 flex items-center justify-center">
                  <Play className="w-5 h-5 text-primary-600" />
                </div>
                <div>
                  <h3 className="font-medium text-gray-900">영상 생성 및 병합</h3>
                  <p className="text-sm text-gray-500">
                    모든 장면 영상을 생성한 후 하나의 영상으로 합칩니다
                  </p>
                </div>
              </div>

              {/* Generated Final Video Preview - Extended mode or Concatenation mode */}
              {generatedVideoUrl && (concatenationStatus === "completed" || (extendedVideoStatus?.status === "completed")) && (
                <div className="mb-6">
                  <div className="flex items-center gap-2 mb-3">
                    <Check className="w-5 h-5 text-green-600" />
                    <span className="font-medium text-green-700">최종 영상 완성</span>
                  </div>
                  <div className="aspect-video bg-black rounded-lg overflow-hidden mb-3">
                    <video
                      src={generatedVideoUrl}
                      controls
                      className="w-full h-full object-contain"
                    />
                  </div>
                  {/* Video info for extended mode */}
                  {extendedVideoStatus?.status === "completed" && (
                    <div className="mb-3 p-3 bg-gray-100 rounded-lg">
                      <div className="grid grid-cols-2 gap-2 text-sm">
                        {extendedVideoStatus.final_duration_seconds && (
                          <div>
                            <span className="text-gray-500">영상 길이:</span>{" "}
                            <span className="font-medium">
                              {Math.round(extendedVideoStatus.final_duration_seconds)}초
                            </span>
                          </div>
                        )}
                        {extendedVideoStatus.scenes_processed > 0 && (
                          <div>
                            <span className="text-gray-500">처리된 장면:</span>{" "}
                            <span className="font-medium">
                              {extendedVideoStatus.scenes_processed}개
                            </span>
                          </div>
                        )}
                        {extendedVideoStatus.generation_time_ms && (
                          <div>
                            <span className="text-gray-500">생성 시간:</span>{" "}
                            <span className="font-medium">
                              {Math.round(extendedVideoStatus.generation_time_ms / 1000)}초
                            </span>
                          </div>
                        )}
                        {extendedVideoStatus.extension_hops_completed > 0 && (
                          <div>
                            <span className="text-gray-500">Extension hops:</span>{" "}
                            <span className="font-medium">
                              {extendedVideoStatus.extension_hops_completed}
                            </span>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                  <div className="flex gap-2">
                    <a
                      href={generatedVideoUrl}
                      download="marketing-video.mp4"
                      className="flex-1 btn-primary py-2 flex items-center justify-center gap-2"
                    >
                      <ArrowRight className="w-4 h-4" />
                      영상 다운로드
                    </a>
                    <button
                      onClick={() => {
                        setGeneratedVideoUrl(null);
                        setConcatenationStatus("idle");
                        setSceneVideos([]);
                        setVideoGenerationStatus(null);
                        setExtendedVideoStatus(null);
                      }}
                      className="btn-secondary py-2 px-4"
                    >
                      처음부터 다시
                    </button>
                  </div>
                </div>
              )}

              {/* Extended Video Generation Progress */}
              {useExtendedMode && extendedVideoStatus && (isGeneratingVideo || extendedVideoStatus.status === "failed") && (
                <div className={`mb-6 p-4 rounded-lg border ${
                  extendedVideoStatus.status === "failed"
                    ? "bg-red-50 border-red-200"
                    : "bg-blue-50 border-blue-200"
                }`}>
                  <div className="flex items-center gap-3 mb-3">
                    {extendedVideoStatus.status === "failed" ? (
                      <X className="w-5 h-5 text-red-600" />
                    ) : (
                      <RefreshCw className="w-5 h-5 text-blue-600 animate-spin" />
                    )}
                    <span className={`font-medium ${
                      extendedVideoStatus.status === "failed" ? "text-red-900" : "text-blue-900"
                    }`}>
                      {extendedVideoStatus.status === "failed"
                        ? "Scene Extension 영상 생성 실패"
                        : "Scene Extension 영상 생성 중..."}
                    </span>
                  </div>
                  <div className="space-y-2">
                    <div className={`flex justify-between text-sm ${
                      extendedVideoStatus.status === "failed" ? "text-red-700" : "text-blue-700"
                    }`}>
                      <span>처리된 장면</span>
                      <span>
                        {extendedVideoStatus.scenes_processed || 0}/{storyboard?.scenes.length || 0}
                      </span>
                    </div>
                    <div className={`w-full rounded-full h-2 ${
                      extendedVideoStatus.status === "failed" ? "bg-red-200" : "bg-blue-200"
                    }`}>
                      <div
                        className={`h-2 rounded-full transition-all duration-500 ${
                          extendedVideoStatus.status === "failed" ? "bg-red-600" : "bg-blue-600"
                        }`}
                        style={{
                          width: `${
                            storyboard?.scenes.length
                              ? ((extendedVideoStatus.scenes_processed || 0) /
                                  storyboard.scenes.length) *
                                100
                              : 0
                          }%`,
                        }}
                      />
                    </div>
                    {extendedVideoStatus.extension_hops_completed > 0 && (
                      <p className={`text-xs ${
                        extendedVideoStatus.status === "failed" ? "text-red-600" : "text-blue-600"
                      }`}>
                        Extension hops: {extendedVideoStatus.extension_hops_completed}
                      </p>
                    )}
                  </div>

                  {/* Error message and retry button */}
                  {extendedVideoStatus.status === "failed" && extendedVideoStatus.error_message && (
                    <div className="mt-3 p-3 bg-red-100 rounded-lg">
                      <p className="text-xs text-red-800 font-mono break-all">
                        {extendedVideoStatus.error_message}
                      </p>
                    </div>
                  )}

                  {extendedVideoStatus.status === "failed" ? (
                    <button
                      onClick={handleGenerateVideo}
                      className="mt-3 w-full btn-primary py-2 flex items-center justify-center gap-2"
                    >
                      <RefreshCw className="w-4 h-4" />
                      다시 생성하기
                    </button>
                  ) : (
                    <p className="text-sm text-blue-700 mt-3">
                      AI가 모든 장면을 하나의 연속된 영상으로 생성합니다.
                      이 작업은 영상 길이에 따라 수 분이 소요될 수 있습니다.
                    </p>
                  )}
                </div>
              )}

              {/* Concatenation Progress (fallback mode) */}
              {isConcatenating && !useExtendedMode && (
                <div className="mb-6 p-4 bg-purple-50 rounded-lg border border-purple-200">
                  <div className="flex items-center gap-3 mb-3">
                    <RefreshCw className="w-5 h-5 text-purple-600 animate-spin" />
                    <span className="font-medium text-purple-900">영상 병합 중...</span>
                  </div>
                  <p className="text-sm text-purple-700">
                    모든 장면 영상을 하나의 영상으로 합치고 있습니다.
                    이 작업은 몇 분 정도 소요될 수 있습니다.
                  </p>
                </div>
              )}

              {storyboard && !generatedVideoUrl && (
                <div className="space-y-4">
                  {/* Mode Selection Toggle */}
                  {!isGeneratingVideo && sceneVideos.length === 0 && (
                    <div className="p-3 bg-gray-50 rounded-lg border">
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <p className="text-sm font-medium text-gray-700">
                            생성 모드
                          </p>
                          <p className="text-xs text-gray-500">
                            {useExtendedMode
                              ? "Scene Extension: 모든 장면을 하나의 연속 영상으로 생성 (권장)"
                              : "장면별 생성: 각 장면을 개별 생성 후 병합"}
                          </p>
                        </div>
                        <button
                          onClick={() => setUseExtendedMode(!useExtendedMode)}
                          className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                            useExtendedMode ? "bg-primary-600" : "bg-gray-300"
                          }`}
                        >
                          <span
                            className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                              useExtendedMode ? "translate-x-6" : "translate-x-1"
                            }`}
                          />
                        </button>
                      </div>
                    </div>
                  )}

                  {/* Image Status */}
                  {!isGeneratingVideo && sceneVideos.length === 0 && (
                    <div className="flex items-center gap-3 mb-4">
                      <div className="flex-1 bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-primary-500 h-2 rounded-full transition-all"
                          style={{
                            width: `${
                              (sceneAssets.filter((s) => s.imageUrl).length /
                                storyboard.scenes.length) *
                              100
                            }%`,
                          }}
                        />
                      </div>
                      <span className="text-sm text-gray-600">
                        이미지 {sceneAssets.filter((s) => s.imageUrl).length}/
                        {storyboard.scenes.length}
                      </span>
                    </div>
                  )}

                  {/* Start Generation Button */}
                  {!isGeneratingVideo && sceneVideos.length === 0 && (
                    <>
                      <button
                        onClick={handleGenerateVideo}
                        disabled={
                          sceneAssets.some((s) => s.isGenerating) || isGeneratingVideo
                        }
                        className="w-full btn-primary py-3 flex items-center justify-center gap-2 disabled:opacity-50"
                      >
                        <Play className="w-5 h-5" />
                        {useExtendedMode ? "영상 생성 시작" : "장면별 영상 생성 시작"}
                      </button>
                      {sceneAssets.filter((s) => s.imageUrl).length <
                        storyboard.scenes.length && (
                        <p className="text-center text-sm text-gray-400">
                          이미지가 없는 장면은 AI가 텍스트 기반으로 영상을 생성합니다
                        </p>
                      )}
                    </>
                  )}

                  {/* Per-scene fallback mode: Combine Videos Button - Shows when all scenes completed */}
                  {!useExtendedMode && allScenesCompleted && !isConcatenating && (
                    <div className="p-4 bg-green-50 rounded-lg border border-green-200">
                      <div className="flex items-center gap-2 mb-3">
                        <Check className="w-5 h-5 text-green-600" />
                        <span className="font-medium text-green-700">
                          모든 장면 영상 생성 완료!
                        </span>
                      </div>
                      <p className="text-sm text-green-600 mb-4">
                        {completedSceneVideos.length}개의 장면 영상이 준비되었습니다.
                        이제 하나의 영상으로 합칠 수 있습니다.
                      </p>
                      <button
                        onClick={handleConcatenateVideos}
                        className="w-full btn-primary py-3 flex items-center justify-center gap-2"
                      >
                        <Video className="w-5 h-5" />
                        영상 합치기
                      </button>
                    </div>
                  )}

                  {/* Per-scene fallback mode: In Progress - Show status */}
                  {!useExtendedMode && sceneVideos.length > 0 && !allScenesCompleted && !isGeneratingVideo && (
                    <div className="p-4 bg-yellow-50 rounded-lg border border-yellow-200">
                      <div className="flex items-center gap-2 mb-2">
                        <Clock className="w-5 h-5 text-yellow-600" />
                        <span className="font-medium text-yellow-700">
                          일부 장면 영상 생성 필요
                        </span>
                      </div>
                      <p className="text-sm text-yellow-600 mb-3">
                        {storyboard.scenes.length - completedSceneVideos.length}개 장면의
                        영상이 아직 생성되지 않았습니다.
                      </p>
                      <button
                        onClick={handleGenerateVideoPerScene}
                        disabled={isGeneratingVideo}
                        className="w-full btn-secondary py-2 flex items-center justify-center gap-2"
                      >
                        <RefreshCw className="w-4 h-4" />
                        남은 장면 영상 생성
                      </button>
                    </div>
                  )}

                  {/* Extended mode: Error state - Now handled in progress section above */}
                </div>
              )}

              {!storyboard && (
                <div className="text-center py-8 text-gray-500">
                  <LayoutGrid className="w-12 h-12 mx-auto mb-3 opacity-50" />
                  <p>먼저 스토리보드를 생성해주세요</p>
                  <button
                    onClick={() => setCurrentStep(4)}
                    className="text-primary-600 hover:underline mt-2 text-sm"
                  >
                    스토리보드 생성하기
                  </button>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Navigation Buttons */}
        <div className="flex justify-between mt-8 pt-6 border-t">
          <button
            onClick={handlePrev}
            disabled={currentStep === 1}
            className={`btn-secondary px-6 py-2 ${
              currentStep === 1 ? "opacity-50 cursor-not-allowed" : ""
            }`}
          >
            이전
          </button>

          <button
            onClick={handleNext}
            disabled={
              isProcessingNext ||
              (currentStep === 1 && !canProceedToStep2) ||
              (currentStep === 2 && !canProceedToStep3) ||
              (currentStep === 3 && !canProceedToStep4) ||
              (currentStep === 4 && !canProceedToStep5) ||
              currentStep === 5
            }
            className={`btn-primary px-6 py-2 flex items-center gap-2 ${
              (isProcessingNext ||
                (currentStep === 1 && !canProceedToStep2) ||
                (currentStep === 2 && !canProceedToStep3) ||
                (currentStep === 3 && !canProceedToStep4) ||
                (currentStep === 4 && !canProceedToStep5) ||
                currentStep === 5) &&
              "opacity-50 cursor-not-allowed"
            }`}
          >
            {isProcessingNext ? "처리중..." : currentStep === 5 ? "영상 생성" : "다음"}
            {!isProcessingNext && <ChevronRight className="w-4 h-4" />}
          </button>
        </div>
      </div>
    </div>
  );
}

// Add Scene Modal Component
interface AddSceneModalProps {
  onClose: () => void;
  onAdd: (data: SceneCreateRequest) => void;
  isLoading: boolean;
  lastSceneNumber: number;
}

function AddSceneModal({ onClose, onAdd, isLoading, lastSceneNumber }: AddSceneModalProps) {
  const [formData, setFormData] = useState<SceneCreateRequest>({
    scene_type: "product_showcase",
    title: "",
    description: "",
    insert_after: lastSceneNumber,
    duration_seconds: 3,
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.title.trim() || !formData.description.trim()) return;
    onAdd(formData);
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-xl max-w-lg w-full mx-4 p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">새 장면 추가</h3>
          <button
            onClick={onClose}
            className="p-1 text-gray-400 hover:text-gray-600"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Scene Type */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              장면 유형
            </label>
            <select
              value={formData.scene_type}
              onChange={(e) => setFormData({ ...formData, scene_type: e.target.value })}
              className="input w-full"
            >
              {SCENE_TYPES.map((type) => (
                <option key={type.value} value={type.value}>
                  {type.label}
                </option>
              ))}
            </select>
          </div>

          {/* Title */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              제목 *
            </label>
            <input
              type="text"
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              className="input w-full"
              placeholder="장면 제목을 입력하세요"
              required
            />
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              비주얼 설명 *
            </label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="input w-full h-24 resize-none"
              placeholder="이 장면의 시각적 요소를 설명하세요..."
              required
            />
          </div>

          {/* Duration */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              시간 (초)
            </label>
            <input
              type="number"
              value={formData.duration_seconds}
              onChange={(e) => setFormData({ ...formData, duration_seconds: parseFloat(e.target.value) || 3 })}
              className="input w-full"
              min="0.5"
              step="0.5"
            />
          </div>

          {/* Narration Script (optional) */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              나레이션 스크립트 (선택)
            </label>
            <textarea
              value={formData.narration_script || ""}
              onChange={(e) => setFormData({ ...formData, narration_script: e.target.value })}
              className="input w-full h-20 resize-none"
              placeholder="이 장면의 나레이션 스크립트..."
            />
          </div>

          {/* Transition Effect */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              전환 효과
            </label>
            <select
              value={formData.transition_effect || "cut"}
              onChange={(e) => setFormData({ ...formData, transition_effect: e.target.value })}
              className="input w-full"
            >
              {TRANSITION_EFFECTS.map((effect) => (
                <option key={effect.value} value={effect.value}>
                  {effect.label}
                </option>
              ))}
            </select>
          </div>

          {/* Buttons */}
          <div className="flex justify-end gap-3 pt-4 border-t">
            <button
              type="button"
              onClick={onClose}
              className="btn-secondary px-4 py-2"
            >
              취소
            </button>
            <button
              type="submit"
              disabled={isLoading || !formData.title.trim() || !formData.description.trim()}
              className="btn-primary px-4 py-2 flex items-center gap-2"
            >
              {isLoading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Plus className="w-4 h-4" />
              )}
              추가
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
