"use client";

import { useState, useEffect, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  ChevronLeft,
  ChevronRight,
  ChevronDown,
  ChevronUp,
  Image as ImageIcon,
  Layers,
  Smartphone,
  Megaphone,
  BookOpen,
  Sparkles,
  Link as LinkIcon,
  Edit3,
  Check,
  Loader2,
  RefreshCw,
  ArrowRight,
  Wand2,
  Search,
  Zap,
  Target,
  Heart,
  Star,
  Lightbulb,
  X,
  ZoomIn,
  Trash2,
  Upload,
  ImagePlus,
} from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { brandApi, referenceApi, storyboardApi, imageProjectApi, AnalysisResult, HookPoint, EdgePoint, EmotionalTrigger, SellingPoint, Recommendation, ContentStoryboard, StoryboardSlide, ImageProject, GeneratedImage, GenerateSingleSectionResponse, ConceptSuggestion } from "@/lib/api";
import { toast } from "sonner";

// Content types
type ContentType = "single" | "carousel" | "story";
type Purpose = "ad" | "info" | "lifestyle";
type GenerationMethod = "reference" | "prompt";
type GenerationMode = "step_by_step" | "bulk";

// Selected analysis items for storyboard generation
interface SelectedAnalysisItems {
  hookPoints: HookPoint[];
  edgePoints: EdgePoint[];
  triggers: EmotionalTrigger[];
  sellingPoints: SellingPoint[];
  recommendations: Recommendation[];
}

interface ContentConfig {
  type: ContentType;
  purpose: Purpose;
  brandId?: string;
  productId?: string;
  method: GenerationMethod;
  referenceId?: string;
  prompt?: string;
  selectedAnalysisItems?: SelectedAnalysisItems;
  // Reference images for single/story types (multiple allowed)
  uploadedReferenceImages?: Array<{ file: File; previewUrl: string; tempId?: string }>;
}

// Step data
const steps = [
  { num: 1, label: "유형", icon: Layers },
  { num: 2, label: "용도", icon: Megaphone },
  { num: 3, label: "방식", icon: Edit3 },
  { num: 4, label: "생성", icon: Wand2 },
  { num: 5, label: "선택", icon: Check },
  { num: 6, label: "편집", icon: ImageIcon },
];

const contentTypes = [
  {
    type: "single" as const,
    icon: ImageIcon,
    label: "단일 이미지",
    desc: "1:1, 4:5 비율의 정사각형 또는 세로형 이미지",
    gradient: "from-accent-500 to-accent-600",
  },
  {
    type: "carousel" as const,
    icon: Layers,
    label: "캐러셀",
    desc: "2~10장으로 구성된 슬라이드형 콘텐츠",
    gradient: "from-electric-500 to-electric-600",
  },
  {
    type: "story" as const,
    icon: Smartphone,
    label: "세로형",
    desc: "9:16 세로형 풀스크린 콘텐츠",
    gradient: "from-glow-500 to-glow-600",
  },
];

const purposes = [
  {
    purpose: "ad" as const,
    icon: Megaphone,
    label: "광고/홍보",
    desc: "브랜드 및 상품 홍보를 위한 콘텐츠",
    gradient: "from-accent-500 to-accent-600",
  },
  {
    purpose: "info" as const,
    icon: BookOpen,
    label: "정보성",
    desc: "팁, 노하우, 가이드 형식의 콘텐츠",
    gradient: "from-electric-500 to-electric-600",
  },
  {
    purpose: "lifestyle" as const,
    icon: Sparkles,
    label: "일상/감성",
    desc: "무드와 감성을 전달하는 콘텐츠",
    gradient: "from-glow-500 to-glow-600",
  },
];

function CreatePageContent() {
  const searchParams = useSearchParams();
  const router = useRouter();

  const [step, setStep] = useState(1);
  const initialType = (searchParams.get("type") as ContentType) || "single";
  const [config, setConfig] = useState<ContentConfig>({
    type: initialType,
    purpose: "ad",
    // Default method: carousel uses reference, single/story use prompt
    method: initialType === "carousel" ? "reference" : "prompt",
  });

  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedImages, setGeneratedImages] = useState<string[]>([]);
  const [selectedImageIndex, setSelectedImageIndex] = useState<number | null>(null);
  const [referenceSearch, setReferenceSearch] = useState("");

  // Storyboard state for carousel/story content types
  const [storyboard, setStoryboard] = useState<ContentStoryboard | null>(null);
  const [isGeneratingStoryboard, setIsGeneratingStoryboard] = useState(false);

  // Concept suggestion state for single/story with reference method
  const [conceptSuggestion, setConceptSuggestion] = useState<ConceptSuggestion | null>(null);
  const [isGeneratingConcept, setIsGeneratingConcept] = useState(false);

  // Section-based image generation state for carousel/story
  const [sectionImages, setSectionImages] = useState<Record<number, string[]>>({});
  const [selectedSectionImages, setSelectedSectionImages] = useState<Record<number, number>>({});
  const [currentGeneratingSection, setCurrentGeneratingSection] = useState<number | null>(null);
  const [generationProgress, setGenerationProgress] = useState<{ current: number; total: number }>({ current: 0, total: 0 });
  const [imageProjectId, setImageProjectId] = useState<string | null>(null);

  // Generation mode state for step-by-step vs bulk
  const [generationMode, setGenerationMode] = useState<GenerationMode>("step_by_step");
  const [currentSectionIndex, setCurrentSectionIndex] = useState<number>(0);
  const [referenceImageId, setReferenceImageId] = useState<string | null>(null);
  const [approvedSections, setApprovedSections] = useState<Set<number>>(new Set());
  const [isRegenerating, setIsRegenerating] = useState<number | null>(null);

  // Image preview modal state
  const [previewImage, setPreviewImage] = useState<{
    url: string;
    slideNumber: number;
    variantIndex: number;
  } | null>(null);

  // Visual prompt editing state
  const [editingSlideNumber, setEditingSlideNumber] = useState<number | null>(null);
  const [editingPrompt, setEditingPrompt] = useState<string>("");

  // State for selected analysis items (indices for checkbox tracking)
  const [selectedHookPointIndices, setSelectedHookPointIndices] = useState<number[]>([]);
  const [selectedEdgePointIndices, setSelectedEdgePointIndices] = useState<number[]>([]);
  const [selectedTriggerIndices, setSelectedTriggerIndices] = useState<number[]>([]);
  const [selectedSellingPointIndices, setSelectedSellingPointIndices] = useState<number[]>([]);
  const [selectedRecommendationIndices, setSelectedRecommendationIndices] = useState<number[]>([]);

  // State for accordion sections
  const [expandedSections, setExpandedSections] = useState<{
    hookPoints: boolean;
    edgePoints: boolean;
    triggers: boolean;
    sellingPoints: boolean;
    recommendations: boolean;
  }>({
    hookPoints: true,
    edgePoints: false,
    triggers: false,
    sellingPoints: false,
    recommendations: true,
  });

  // Fetch brands for ad/promo selection
  const { data: brands = [] } = useQuery({
    queryKey: ["brands"],
    queryFn: () => brandApi.list(),
    enabled: config.purpose === "ad",
  });

  // Fetch selected brand details to get products
  const { data: selectedBrandDetails } = useQuery({
    queryKey: ["brand", config.brandId],
    queryFn: () => brandApi.get(config.brandId!),
    enabled: config.purpose === "ad" && !!config.brandId,
  });

  // Fetch references for reference-based generation
  const { data: allReferences = [], isLoading: isLoadingReferences } = useQuery({
    queryKey: ["references"],
    queryFn: () => referenceApi.listAnalyses(),
  });

  // Fetch full analysis data when a reference is selected
  const { data: selectedReferenceAnalysis, isLoading: isLoadingAnalysis } = useQuery({
    queryKey: ["referenceAnalysis", config.referenceId],
    queryFn: () => referenceApi.getAnalysis(config.referenceId!),
    enabled: !!config.referenceId && config.method === "reference",
  });

  // Reset selected items when reference changes
  useEffect(() => {
    setSelectedHookPointIndices([]);
    setSelectedEdgePointIndices([]);
    setSelectedTriggerIndices([]);
    setSelectedSellingPointIndices([]);
    setSelectedRecommendationIndices([]);
  }, [config.referenceId]);

  // Filter to only show completed references
  const completedReferences = allReferences.filter(
    (ref: AnalysisResult) => ref.status === "completed"
  );

  // Filter completed references by search query
  const filteredReferences = completedReferences.filter((ref: AnalysisResult) => {
    if (!referenceSearch.trim()) return true;
    const title = ref.title || "";
    return title.toLowerCase().includes(referenceSearch.toLowerCase());
  });

  // Helper function to detect platform from URL
  const detectPlatform = (url: string): string => {
    if (url.includes("instagram")) return "Instagram";
    if (url.includes("facebook")) return "Facebook";
    if (url.includes("pinterest")) return "Pinterest";
    if (url.includes("youtube") || url.includes("youtu.be")) return "YouTube";
    return "Upload";
  };

  // Helper function to get thumbnail URL
  const getThumbnailUrl = (ref: AnalysisResult): string | null => {
    if (ref.thumbnail_url) return ref.thumbnail_url;
    if (ref.images && ref.images.length > 0) return ref.images[0];
    // For YouTube, generate thumbnail from URL
    if (ref.source_url) {
      const ytMatch = ref.source_url.match(
        /(?:youtube\.com\/(?:watch\?v=|shorts\/|embed\/)|youtu\.be\/)([a-zA-Z0-9_-]+)/
      );
      if (ytMatch && ytMatch[1]) {
        return `https://img.youtube.com/vi/${ytMatch[1]}/hqdefault.jpg`;
      }
    }
    return null;
  };

  // Helper function to get section type badge style
  const getSectionTypeBadge = (sectionType: string): { bg: string; text: string; label: string } => {
    const typeMap: Record<string, { bg: string; text: string; label: string }> = {
      hook: { bg: "bg-electric-500/20", text: "text-electric-600 dark:text-electric-400", label: "Hook" },
      problem: { bg: "bg-red-500/20", text: "text-red-600 dark:text-red-400", label: "Problem" },
      solution: { bg: "bg-green-500/20", text: "text-green-600 dark:text-green-400", label: "Solution" },
      benefit: { bg: "bg-accent-500/20", text: "text-accent-600 dark:text-accent-400", label: "Benefit" },
      social_proof: { bg: "bg-yellow-500/20", text: "text-yellow-600 dark:text-yellow-400", label: "Social Proof" },
      cta: { bg: "bg-glow-500/20", text: "text-glow-600 dark:text-glow-400", label: "CTA" },
      intro: { bg: "bg-blue-500/20", text: "text-blue-600 dark:text-blue-400", label: "Intro" },
      outro: { bg: "bg-purple-500/20", text: "text-purple-600 dark:text-purple-400", label: "Outro" },
    };
    return typeMap[sectionType] || { bg: "bg-muted/50", text: "text-muted", label: sectionType };
  };

  const selectedBrand = brands.find((b) => b.id === config.brandId);
  const products = selectedBrandDetails?.products || [];

  // Update type from URL params
  useEffect(() => {
    const typeParam = searchParams.get("type") as ContentType;
    if (typeParam && ["single", "carousel", "story"].includes(typeParam)) {
      setConfig((prev) => ({ ...prev, type: typeParam }));
    }
  }, [searchParams]);

  // Auto-generate concept when entering Step 4 with single/story (both reference and upload modes)
  useEffect(() => {
    if (
      step === 4 &&
      (config.type === "single" || config.type === "story") &&
      !conceptSuggestion &&
      !isGeneratingConcept
    ) {
      // For upload mode: need reference images or prompt
      // For reference mode (carousel only now): need referenceId
      const hasUploadedImages = config.uploadedReferenceImages && config.uploadedReferenceImages.length > 0;
      if (hasUploadedImages || config.prompt?.trim() || (config.method === "reference" && config.referenceId)) {
        handleGenerateConcept();
      }
    }
  }, [step, config.type, config.method, config.referenceId, config.uploadedReferenceImages, config.prompt]);

  const handleNext = () => {
    if (step < 6) setStep(step + 1);
  };

  const handleBack = () => {
    if (step > 1) setStep(step - 1);
  };

  const handleGenerateStoryboard = async () => {
    setIsGeneratingStoryboard(true);
    toast.info("AI가 스토리보드를 생성하고 있습니다...");

    try {
      const requestData = {
        content_type: config.type,
        purpose: config.purpose,
        method: config.method,
        prompt: config.prompt,
        brand_id: config.brandId,
        product_id: config.productId,
        reference_id: config.referenceId,
        selected_items: config.selectedAnalysisItems ? {
          hook_points: config.selectedAnalysisItems.hookPoints,
          edge_points: config.selectedAnalysisItems.edgePoints,
          triggers: config.selectedAnalysisItems.triggers,
          selling_points: config.selectedAnalysisItems.sellingPoints,
          recommendations: config.selectedAnalysisItems.recommendations,
        } : undefined,
      };

      const result = await storyboardApi.generate(requestData);
      setStoryboard(result);
      toast.success("스토리보드 생성이 완료되었습니다!");
    } catch (error) {
      console.error("Storyboard generation failed:", error);
      toast.error("스토리보드 생성에 실패했습니다. 다시 시도해주세요.");
    } finally {
      setIsGeneratingStoryboard(false);
    }
  };

  // Generate AI concept suggestion for single/story (supports both reference and upload modes)
  const handleGenerateConcept = async () => {
    // Determine generation mode
    const hasUploadedImages = config.uploadedReferenceImages && config.uploadedReferenceImages.length > 0;
    const hasPrompt = !!config.prompt?.trim();
    const isUploadMode = hasUploadedImages || hasPrompt;
    const isReferenceMode = !!config.referenceId;

    if (!isUploadMode && !isReferenceMode) {
      toast.error("참고 이미지를 업로드하거나 프롬프트를 입력해주세요.");
      return;
    }

    setIsGeneratingConcept(true);
    toast.info("AI가 컨셉을 제안하고 있습니다...");

    try {
      // Build request data based on mode
      const requestData: {
        content_type: "single" | "story";
        purpose: "ad" | "info" | "lifestyle";
        generation_mode: "reference" | "upload";
        reference_analysis_id?: string;
        reference_image_urls?: string[];
        user_prompt?: string;
        brand_id?: string;
        product_id?: string;
        selected_items?: {
          hook_points?: HookPoint[];
          edge_points?: EdgePoint[];
          triggers?: EmotionalTrigger[];
          selling_points?: SellingPoint[];
          recommendations?: Recommendation[];
        };
      } = {
        content_type: config.type as "single" | "story",
        purpose: config.purpose,
        generation_mode: isUploadMode ? "upload" : "reference",
        brand_id: config.brandId,
        product_id: config.productId,
      };

      if (isUploadMode) {
        // Upload mode: send reference images
        if (hasUploadedImages) {
          requestData.reference_image_urls = config.uploadedReferenceImages!.map(img => img.previewUrl);
        }
        if (config.prompt) {
          requestData.user_prompt = config.prompt;
        }
      } else {
        // Reference mode
        requestData.reference_analysis_id = config.referenceId;
        if (config.selectedAnalysisItems) {
          requestData.selected_items = {
            hook_points: config.selectedAnalysisItems.hookPoints,
            edge_points: config.selectedAnalysisItems.edgePoints,
            triggers: config.selectedAnalysisItems.triggers,
            selling_points: config.selectedAnalysisItems.sellingPoints,
            recommendations: config.selectedAnalysisItems.recommendations,
          };
        }
      }

      const result = await storyboardApi.generateConcept(requestData);
      setConceptSuggestion(result);
      toast.success("컨셉 제안이 완료되었습니다!");
    } catch (error) {
      console.error("Concept generation failed:", error);
      toast.error("컨셉 생성에 실패했습니다. 다시 시도해주세요.");
    } finally {
      setIsGeneratingConcept(false);
    }
  };

  // Confirm concept and proceed to image generation
  const handleConfirmConcept = async () => {
    if (!conceptSuggestion) return;

    // Use the visual_prompt from concept suggestion for image generation
    setConfig((prev) => ({
      ...prev,
      prompt: conceptSuggestion.visual_prompt,
    }));

    // Proceed to step 5 for image generation
    setStep(5);

    // Generate images using the concept's visual prompt
    await handleGenerateImagesWithPrompt(conceptSuggestion.visual_prompt);
  };

  // Regenerate concept suggestion
  const handleRegenerateConcept = async () => {
    setConceptSuggestion(null);
    await handleGenerateConcept();
  };

  // Generate images with a specific prompt (used by concept confirmation)
  const handleGenerateImagesWithPrompt = async (prompt: string) => {
    setIsGenerating(true);
    toast.info("AI가 이미지를 생성하고 있습니다...");

    try {
      // Create image project
      const project = await imageProjectApi.create({
        content_type: config.type,
        purpose: config.purpose,
        method: config.method,
        brand_id: config.brandId,
        product_id: config.productId,
        reference_analysis_id: config.referenceId,
        prompt: prompt,
        aspect_ratio: config.type === "story" ? "9:16" : "1:1",
      });
      setImageProjectId(project.id);

      // Generate images via API
      const result = await imageProjectApi.generateImages(project.id, {
        slide_number: 1,
        prompt: prompt,
        num_variants: 2,
        aspect_ratio: config.type === "story" ? "9:16" : "1:1",
      });

      // Extract image URLs
      const imageUrls = result.images.map((img) => img.image_url);
      setGeneratedImages(imageUrls);

      setIsGenerating(false);
      toast.success("이미지 생성이 완료되었습니다!");
    } catch (error) {
      console.error("Image generation failed:", error);
      setIsGenerating(false);
      toast.error("이미지 생성에 실패했습니다. 다시 시도해주세요.");
    }
  };

  const handleConfirmStoryboard = async (mode: GenerationMode) => {
    // Set the generation mode
    setGenerationMode(mode);

    // Reset state for new generation
    setSectionImages({});
    setSelectedSectionImages({});
    setApprovedSections(new Set());
    setCurrentSectionIndex(0);
    setReferenceImageId(null);

    // Proceed to Step 5 for section image generation
    setStep(5);

    // Start generating images based on mode
    if (storyboard && storyboard.slides.length > 0) {
      if (mode === "bulk") {
        await generateSectionImages(storyboard.slides);
      } else {
        // Step-by-step mode: generate first section only
        await generateSingleSection(0);
      }
    }
  };

  // Generate images for all sections in the storyboard (Bulk Mode)
  const generateSectionImages = async (slides: StoryboardSlide[]) => {
    setGenerationProgress({ current: 0, total: slides.length });

    try {
      // Create image project first
      const project = await imageProjectApi.create({
        content_type: config.type,
        purpose: config.purpose,
        method: config.method,
        brand_id: config.brandId,
        product_id: config.productId,
        reference_analysis_id: config.referenceId,
        storyboard_data: storyboard || undefined,
        aspect_ratio: config.type === "story" ? "9:16" : "1:1",
      });
      setImageProjectId(project.id);

      for (let i = 0; i < slides.length; i++) {
        const slide = slides[i];
        setCurrentGeneratingSection(slide.slide_number);
        setGenerationProgress({ current: i + 1, total: slides.length });

        // Build prompt from slide data - use visual_prompt first (optimized for image generation)
        const prompt = slide.visual_prompt || slide.visual_direction || slide.description || `${slide.title} - ${slide.section_type}`;

        // Generate images via API
        const result = await imageProjectApi.generateImages(project.id, {
          slide_number: slide.slide_number,
          prompt: prompt,
          num_variants: 2,
          aspect_ratio: config.type === "story" ? "9:16" : "1:1",
        });

        // Extract image URLs
        const imageUrls = result.images.map((img) => img.image_url);

        setSectionImages((prev) => ({
          ...prev,
          [slide.slide_number]: imageUrls,
        }));
      }

      setCurrentGeneratingSection(null);
      toast.success("모든 섹션의 이미지 생성이 완료되었습니다!");
    } catch (error) {
      console.error("Image generation failed:", error);
      setCurrentGeneratingSection(null);
      toast.error("이미지 생성에 실패했습니다. 다시 시도해주세요.");
    }
  };

  // Generate a single section for step-by-step mode
  const generateSingleSection = async (sectionIndex: number) => {
    if (!storyboard || sectionIndex >= storyboard.slides.length) return;

    const slide = storyboard.slides[sectionIndex];
    setCurrentGeneratingSection(slide.slide_number);
    setGenerationProgress({ current: sectionIndex + 1, total: storyboard.slides.length });

    try {
      let projectId = imageProjectId;

      // Create image project if not exists
      if (!projectId) {
        const project = await imageProjectApi.create({
          content_type: config.type,
          purpose: config.purpose,
          method: config.method,
          brand_id: config.brandId,
          product_id: config.productId,
          reference_analysis_id: config.referenceId,
          storyboard_data: storyboard || undefined,
          aspect_ratio: config.type === "story" ? "9:16" : "1:1",
        });
        projectId = project.id;
        setImageProjectId(project.id);
      }

      // Use generateSection API for step-by-step mode (supports reference image)
      const result: GenerateSingleSectionResponse = await imageProjectApi.generateSection(
        projectId,
        slide.slide_number,
        referenceImageId !== null // use reference if we have one
      );

      // Extract image URLs
      const imageUrls = result.images.map((img) => img.image_url);

      setSectionImages((prev) => ({
        ...prev,
        [slide.slide_number]: imageUrls,
      }));

      setCurrentGeneratingSection(null);
    } catch (error) {
      console.error("Section image generation failed:", error);
      setCurrentGeneratingSection(null);
      toast.error("이미지 생성에 실패했습니다. 다시 시도해주세요.");
    }
  };

  // Approve current section and proceed to next (Step-by-Step Mode)
  const handleApproveSection = async (selectedVariantIndex: number) => {
    if (!storyboard || !imageProjectId) return;

    const currentSlide = storyboard.slides[currentSectionIndex];
    const slideNumber = currentSlide.slide_number;
    const images = sectionImages[slideNumber];

    if (!images || images.length === 0) return;

    // Select the image
    setSelectedSectionImages((prev) => ({
      ...prev,
      [slideNumber]: selectedVariantIndex,
    }));

    // Mark section as approved
    setApprovedSections((prev) => new Set([...Array.from(prev), slideNumber]));

    // If this is the first section, set it as reference image
    if (currentSectionIndex === 0 && !referenceImageId) {
      try {
        // Get the image ID from the generated images
        const projectData = await imageProjectApi.get(imageProjectId);
        const selectedImage = projectData.generated_images.find(
          (img) => img.slide_number === slideNumber && img.variant_index === selectedVariantIndex
        );
        if (selectedImage) {
          await imageProjectApi.setReferenceImage(imageProjectId, selectedImage.id);
          setReferenceImageId(selectedImage.id);
          toast.success("첫 번째 이미지가 레퍼런스로 설정되었습니다");
        }
      } catch (error) {
        console.error("Failed to set reference image:", error);
      }
    }

    // Check if all sections are done
    if (currentSectionIndex >= storyboard.slides.length - 1) {
      toast.success("모든 섹션의 이미지 선택이 완료되었습니다!");
      return;
    }

    // Move to next section
    const nextIndex = currentSectionIndex + 1;
    setCurrentSectionIndex(nextIndex);

    // Generate next section
    await generateSingleSection(nextIndex);
  };

  // Regenerate current section (Step-by-Step Mode)
  const handleRegenerateCurrentSection = async () => {
    if (!storyboard || !imageProjectId) return;

    const currentSlide = storyboard.slides[currentSectionIndex];
    setCurrentGeneratingSection(currentSlide.slide_number);

    try {
      const result = await imageProjectApi.regenerateSection(imageProjectId, currentSlide.slide_number);

      const imageUrls = result.images.map((img) => img.image_url);

      setSectionImages((prev) => ({
        ...prev,
        [currentSlide.slide_number]: imageUrls,
      }));

      // Clear selection for this section
      setSelectedSectionImages((prev) => {
        const newState = { ...prev };
        delete newState[currentSlide.slide_number];
        return newState;
      });

      setCurrentGeneratingSection(null);
      toast.success("이미지가 다시 생성되었습니다");
    } catch (error) {
      console.error("Section regeneration failed:", error);
      setCurrentGeneratingSection(null);
      toast.error("이미지 재생성에 실패했습니다");
    }
  };

  // Regenerate a specific section (Bulk Mode)
  const handleRegenerateBulkSection = async (slideNumber: number) => {
    if (!imageProjectId) return;

    setIsRegenerating(slideNumber);

    try {
      const result = await imageProjectApi.regenerateSection(imageProjectId, slideNumber);

      const imageUrls = result.images.map((img) => img.image_url);

      setSectionImages((prev) => ({
        ...prev,
        [slideNumber]: imageUrls,
      }));

      // Clear selection for this section
      setSelectedSectionImages((prev) => {
        const newState = { ...prev };
        delete newState[slideNumber];
        return newState;
      });

      setIsRegenerating(null);
      toast.success(`슬라이드 ${slideNumber} 이미지가 다시 생성되었습니다`);
    } catch (error) {
      console.error("Section regeneration failed:", error);
      setIsRegenerating(null);
      toast.error("이미지 재생성에 실패했습니다");
    }
  };

  // Go to previous section (Step-by-Step Mode)
  const handlePreviousSection = () => {
    if (currentSectionIndex > 0) {
      setCurrentSectionIndex(currentSectionIndex - 1);
    }
  };

  // Handle selecting an image for a specific section
  const handleSelectSectionImage = (slideNumber: number, imageIndex: number) => {
    setSelectedSectionImages((prev) => ({
      ...prev,
      [slideNumber]: imageIndex,
    }));
  };

  // Start editing visual prompt for a slide
  const handleStartEditPrompt = (slideNumber: number, currentPrompt: string) => {
    setEditingSlideNumber(slideNumber);
    setEditingPrompt(currentPrompt);
  };

  // Save edited visual prompt
  const handleSavePrompt = () => {
    if (editingSlideNumber !== null && storyboard) {
      const updatedSlides = storyboard.slides.map((slide) =>
        slide.slide_number === editingSlideNumber
          ? {
              ...slide,
              visual_prompt_display: editingPrompt,
              // Also update visual_prompt if user edits it (they can type in English)
              visual_prompt: editingPrompt,
            }
          : slide
      );
      setStoryboard({ ...storyboard, slides: updatedSlides });
      setEditingSlideNumber(null);
      setEditingPrompt("");
      toast.success("비주얼 프롬프트가 수정되었습니다");
    }
  };

  // Cancel editing
  const handleCancelEdit = () => {
    setEditingSlideNumber(null);
    setEditingPrompt("");
  };

  // Delete a slide from storyboard
  const handleDeleteSlide = (slideNumber: number) => {
    if (storyboard && storyboard.slides.length > 1) {
      const updatedSlides = storyboard.slides
        .filter((slide) => slide.slide_number !== slideNumber)
        .map((slide, index) => ({
          ...slide,
          slide_number: index + 1, // Re-number slides
        }));
      setStoryboard({ ...storyboard, slides: updatedSlides });
      // Also update related state
      const newSectionImages: Record<number, string[]> = {};
      const newSelectedImages: Record<number, number> = {};
      updatedSlides.forEach((slide, index) => {
        const oldNumber = storyboard.slides[index]?.slide_number;
        if (oldNumber && sectionImages[oldNumber]) {
          newSectionImages[slide.slide_number] = sectionImages[oldNumber];
        }
        if (oldNumber && selectedSectionImages[oldNumber] !== undefined) {
          newSelectedImages[slide.slide_number] = selectedSectionImages[oldNumber];
        }
      });
      setSectionImages(newSectionImages);
      setSelectedSectionImages(newSelectedImages);
      toast.success("슬라이드가 삭제되었습니다");
    } else {
      toast.error("최소 1개의 슬라이드가 필요합니다");
    }
  };

  // Check if all sections have a selected image
  const allSectionsSelected = storyboard
    ? storyboard.slides.every((slide) => selectedSectionImages[slide.slide_number] !== undefined)
    : false;

  // Get count of selected sections
  const selectedSectionsCount = storyboard
    ? storyboard.slides.filter((slide) => selectedSectionImages[slide.slide_number] !== undefined).length
    : 0;

  // Proceed to edit with selected section images
  const handleProceedToEditWithSections = () => {
    if (allSectionsSelected && storyboard) {
      // Build the selected images data to pass to edit page
      const selectedImagesData = storyboard.slides.map((slide) => ({
        slideNumber: slide.slide_number,
        imageUrl: sectionImages[slide.slide_number]?.[selectedSectionImages[slide.slide_number]] || "",
      }));

      // Store selected images in sessionStorage for edit page
      sessionStorage.setItem("selectedSectionImages", JSON.stringify(selectedImagesData));
      sessionStorage.setItem("storyboardData", JSON.stringify(storyboard));

      // Navigate to edit page with storyboard ID as query param
      router.push(`/create/edit?storyboardId=${storyboard.storyboard_id}&projectId=${imageProjectId}`);
    }
  };

  const handleGenerateImages = async () => {
    setIsGenerating(true);
    toast.info("AI가 이미지를 생성하고 있습니다...");

    try {
      // Create image project
      const project = await imageProjectApi.create({
        content_type: config.type,
        purpose: config.purpose,
        method: config.method,
        brand_id: config.brandId,
        product_id: config.productId,
        reference_analysis_id: config.referenceId,
        prompt: config.prompt,
        aspect_ratio: config.type === "story" ? "9:16" : "1:1",
      });
      setImageProjectId(project.id);

      // Build prompt
      const prompt = config.prompt || "Professional marketing image";

      // Generate images via API
      const result = await imageProjectApi.generateImages(project.id, {
        slide_number: 1,
        prompt: prompt,
        num_variants: 2,
        aspect_ratio: config.type === "story" ? "9:16" : "1:1",
      });

      // Extract image URLs
      const imageUrls = result.images.map((img) => img.image_url);
      setGeneratedImages(imageUrls);

      setIsGenerating(false);
      toast.success("이미지 생성이 완료되었습니다!");
      setStep(5);
    } catch (error) {
      console.error("Image generation failed:", error);
      setIsGenerating(false);
      toast.error("이미지 생성에 실패했습니다. 다시 시도해주세요.");
    }
  };

  const handleGenerate = async () => {
    // Alias for handleGenerateImages
    await handleGenerateImages();
  };

  const handleSelectImage = (index: number) => {
    setSelectedImageIndex(index);
  };

  const handleProceedToEdit = () => {
    if (selectedImageIndex !== null && generatedImages.length > 0) {
      // Store selected image in sessionStorage
      sessionStorage.setItem("selectedImage", JSON.stringify({
        imageUrl: generatedImages[selectedImageIndex],
        imageIndex: selectedImageIndex,
      }));
      // Navigate with query params
      router.push(`/create/edit?type=${config.type}&projectId=${imageProjectId}`);
    }
  };

  return (
    <div className="max-w-4xl mx-auto animate-fade-in">
      {/* Progress Steps */}
      <div className="mb-10">
        <div className="flex items-center justify-between">
          {steps.map((s, i) => (
            <div key={s.num} className="flex items-center">
              <div className="flex flex-col items-center">
                <div
                  className={`step-indicator ${
                    step === s.num ? "active" : step > s.num ? "completed" : ""
                  }`}
                >
                  {step > s.num ? (
                    <Check className="w-5 h-5" />
                  ) : (
                    <s.icon className="w-5 h-5" />
                  )}
                </div>
                <span
                  className={`mt-2 text-xs font-medium ${
                    step >= s.num ? "text-foreground" : "text-muted"
                  }`}
                >
                  {s.label}
                </span>
              </div>
              {i < steps.length - 1 && (
                <div className={`step-line ${step > s.num ? "completed" : ""}`} />
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Step Content */}
      <div className="card">
        {/* Step 1: Content Type */}
        {step === 1 && (
          <div className="space-y-8">
            <div className="text-center">
              <h2 className="font-display text-2xl font-bold text-foreground mb-2">
                무엇을 만들까요?
              </h2>
              <p className="text-muted">콘텐츠 유형을 선택하세요</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {contentTypes.map((item) => (
                <button
                  key={item.type}
                  onClick={() => {
                    // Set method based on content type: carousel uses reference, others use prompt
                    const defaultMethod = item.type === "carousel" ? "reference" : "prompt";
                    setConfig((prev) => ({ ...prev, type: item.type, method: defaultMethod }));
                    handleNext();
                  }}
                  className={`selection-card text-center ${
                    config.type === item.type ? "selected" : ""
                  }`}
                >
                  <div
                    className={`w-16 h-16 mx-auto mb-4 rounded-2xl bg-gradient-to-br ${item.gradient} flex items-center justify-center shadow-lg`}
                  >
                    <item.icon className="w-8 h-8 text-white" />
                  </div>
                  <p className="font-semibold text-foreground mb-1">{item.label}</p>
                  <p className="text-sm text-muted">{item.desc}</p>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Step 2: Purpose */}
        {step === 2 && (
          <div className="space-y-8">
            <div className="text-center">
              <h2 className="font-display text-2xl font-bold text-foreground mb-2">
                어떤 용도인가요?
              </h2>
              <p className="text-muted">콘텐츠의 목적을 선택하세요</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {purposes.map((item) => (
                <button
                  key={item.purpose}
                  onClick={() => {
                    setConfig((prev) => ({ ...prev, purpose: item.purpose }));
                    // All purposes go to Step 3 (generation method & prompt)
                    // Only "ad" shows brand/product selection first
                  }}
                  className={`selection-card text-center ${
                    config.purpose === item.purpose ? "selected" : ""
                  }`}
                >
                  <div
                    className={`w-16 h-16 mx-auto mb-4 rounded-2xl bg-gradient-to-br ${item.gradient} flex items-center justify-center shadow-lg`}
                  >
                    <item.icon className="w-8 h-8 text-white" />
                  </div>
                  <p className="font-semibold text-foreground mb-1">{item.label}</p>
                  <p className="text-sm text-muted">{item.desc}</p>
                </button>
              ))}
            </div>

            {/* Brand/Product Selection for Ad */}
            {config.purpose === "ad" && (
              <div className="mt-8 p-6 rounded-2xl bg-muted/30 dark:bg-muted/10 border border-default space-y-4">
                <div>
                  <label className="block text-sm font-medium text-foreground mb-2">
                    브랜드 선택
                  </label>
                  <select
                    value={config.brandId || ""}
                    onChange={(e) =>
                      setConfig((prev) => ({
                        ...prev,
                        brandId: e.target.value,
                        productId: undefined,
                      }))
                    }
                    className="input"
                  >
                    <option value="">브랜드를 선택하세요</option>
                    {brands.map((brand) => (
                      <option key={brand.id} value={brand.id}>
                        {brand.name}
                      </option>
                    ))}
                  </select>
                </div>

                {config.brandId && products.length > 0 && (
                  <div>
                    <label className="block text-sm font-medium text-foreground mb-2">
                      상품 선택
                    </label>
                    <select
                      value={config.productId || ""}
                      onChange={(e) =>
                        setConfig((prev) => ({ ...prev, productId: e.target.value }))
                      }
                      className="input"
                    >
                      <option value="">상품을 선택하세요</option>
                      {products.map((product) => (
                        <option key={product.id} value={product.id}>
                          {product.name}
                        </option>
                      ))}
                    </select>
                  </div>
                )}

                <button
                  onClick={handleNext}
                  disabled={!config.brandId}
                  className="btn-primary w-full disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  다음으로 <ArrowRight className="w-4 h-4 ml-2 inline" />
                </button>
              </div>
            )}

            {/* Next button for non-ad purposes */}
            {config.purpose !== "ad" && (
              <div className="mt-8">
                <button
                  onClick={handleNext}
                  className="btn-primary w-full"
                >
                  다음으로 <ArrowRight className="w-4 h-4 ml-2 inline" />
                </button>
              </div>
            )}
          </div>
        )}

        {/* Step 3: Generation Method */}
        {step === 3 && (
          <div className="space-y-8">
            {/* Carousel: Show method selection */}
            {config.type === "carousel" ? (
              <>
                <div className="text-center">
                  <h2 className="font-display text-2xl font-bold text-foreground mb-2">
                    어떻게 만들까요?
                  </h2>
                  <p className="text-muted">생성 방식을 선택하세요</p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <button
                    onClick={() => setConfig((prev) => ({ ...prev, method: "reference" }))}
                    className={`selection-card text-left ${
                      config.method === "reference" ? "selected" : ""
                    }`}
                  >
                    <div className="w-14 h-14 mb-4 rounded-xl bg-gradient-to-br from-electric-500 to-electric-600 flex items-center justify-center">
                      <LinkIcon className="w-7 h-7 text-white" />
                    </div>
                    <p className="font-semibold text-lg text-foreground mb-2">레퍼런스 활용</p>
                    <p className="text-sm text-muted leading-relaxed">
                      저장된 레퍼런스의 스타일을 참고해서 비슷한 느낌으로 이미지를 생성합니다.
                    </p>
                  </button>

                  <button
                    onClick={() => setConfig((prev) => ({ ...prev, method: "prompt" }))}
                    className={`selection-card text-left ${
                      config.method === "prompt" ? "selected" : ""
                    }`}
                  >
                    <div className="w-14 h-14 mb-4 rounded-xl bg-gradient-to-br from-accent-500 to-accent-600 flex items-center justify-center">
                      <Edit3 className="w-7 h-7 text-white" />
                    </div>
                    <p className="font-semibold text-lg text-foreground mb-2">직접 만들기</p>
                    <p className="text-sm text-muted leading-relaxed">
                      프롬프트로 원하는 이미지를 직접 설명해서 생성합니다.
                    </p>
                  </button>
                </div>
              </>
            ) : (
              /* Single/Story: Show image upload UI */
              <>
                <div className="text-center">
                  <h2 className="font-display text-2xl font-bold text-foreground mb-2">
                    참고 이미지 및 프롬프트
                  </h2>
                  <p className="text-muted">참고할 이미지를 업로드하거나 프롬프트를 입력하세요</p>
                </div>

                {/* Reference Images Upload (Multiple) */}
                <div className="p-6 rounded-2xl bg-muted/30 dark:bg-muted/10 border border-default">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-electric-500 to-electric-600 flex items-center justify-center">
                      <ImagePlus className="w-5 h-5 text-white" />
                    </div>
                    <div>
                      <p className="font-medium text-foreground">참고 이미지 <span className="text-muted font-normal">(선택, 여러 장 가능)</span></p>
                      <p className="text-xs text-muted">스타일/배경 참고용 이미지</p>
                    </div>
                  </div>

                  <div className="flex flex-wrap gap-3">
                    {/* Uploaded Images */}
                    {config.uploadedReferenceImages?.map((img, index) => (
                      <div key={index} className="relative w-28 h-28">
                        <img
                          src={img.previewUrl}
                          alt={`참고 이미지 ${index + 1}`}
                          className="w-full h-full object-cover rounded-xl"
                        />
                        <button
                          onClick={() => {
                            URL.revokeObjectURL(img.previewUrl);
                            setConfig((prev) => ({
                              ...prev,
                              uploadedReferenceImages: prev.uploadedReferenceImages?.filter((_, i) => i !== index),
                            }));
                          }}
                          className="absolute -top-2 -right-2 w-6 h-6 bg-red-500 hover:bg-red-600 rounded-full flex items-center justify-center text-white transition-colors shadow-lg"
                        >
                          <X className="w-3 h-3" />
                        </button>
                      </div>
                    ))}

                    {/* Upload Button */}
                    <label className="block cursor-pointer">
                      <div className="w-28 h-28 border-2 border-dashed border-muted hover:border-electric-500 rounded-xl flex flex-col items-center justify-center transition-colors">
                        <Upload className="w-6 h-6 text-muted mb-1" />
                        <p className="text-xs text-muted">추가</p>
                      </div>
                      <input
                        type="file"
                        accept="image/*"
                        multiple
                        className="hidden"
                        onChange={(e) => {
                          const files = e.target.files;
                          if (files) {
                            const newImages = Array.from(files).map(file => ({
                              file,
                              previewUrl: URL.createObjectURL(file),
                            }));
                            setConfig((prev) => ({
                              ...prev,
                              uploadedReferenceImages: [
                                ...(prev.uploadedReferenceImages || []),
                                ...newImages,
                              ],
                            }));
                          }
                        }}
                      />
                    </label>
                  </div>
                </div>

                {/* Prompt Input */}
                <div className="p-6 rounded-2xl bg-muted/30 dark:bg-muted/10 border border-default">
                  <label className="block text-sm font-medium text-foreground mb-2">
                    프롬프트 <span className="text-muted font-normal">(참고 이미지 없이도 가능)</span>
                  </label>
                  <textarea
                    value={config.prompt || ""}
                    onChange={(e) =>
                      setConfig((prev) => ({ ...prev, prompt: e.target.value }))
                    }
                    placeholder="원하는 이미지 스타일을 설명하세요 (예: 밝은 조명, 고급스러운 느낌, 꽃 배경, 미니멀한 화이트 배경)"
                    className="input h-28 resize-none text-sm"
                  />
                </div>

                {/* Next Button */}
                <button
                  onClick={handleNext}
                  disabled={!(config.uploadedReferenceImages?.length) && !config.prompt?.trim()}
                  className="btn-primary w-full disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  다음으로 <ArrowRight className="w-4 h-4 ml-2 inline" />
                </button>
              </>
            )}

            {/* Reference Selection - Only for Carousel */}
            {config.type === "carousel" && config.method === "reference" && (
              <div className="p-6 rounded-2xl bg-muted/30 dark:bg-muted/10 border border-default">
                <div className="flex items-center justify-between mb-4">
                  <p className="font-medium text-foreground">레퍼런스 선택</p>
                  <Link
                    href="/references"
                    className="text-sm text-accent-500 hover:text-accent-600 dark:text-accent-400 dark:hover:text-accent-300 flex items-center gap-1"
                  >
                    + 새 레퍼런스 추가
                  </Link>
                </div>

                {isLoadingReferences ? (
                  <div className="text-center py-10">
                    <Loader2 className="w-8 h-8 animate-spin text-accent-500 mx-auto mb-3" />
                    <p className="text-muted">레퍼런스 불러오는 중...</p>
                  </div>
                ) : completedReferences.length === 0 ? (
                  <div className="text-center py-10">
                    <div className="w-14 h-14 rounded-xl bg-muted flex items-center justify-center mx-auto mb-3">
                      <LinkIcon className="w-7 h-7 text-muted" />
                    </div>
                    <p className="text-muted mb-2">저장된 레퍼런스가 없습니다</p>
                    <Link
                      href="/references"
                      className="text-accent-500 hover:text-accent-600 dark:text-accent-400 dark:hover:text-accent-300 text-sm"
                    >
                      레퍼런스 추가하기 →
                    </Link>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {/* Search Input */}
                    <div className="relative">
                      <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted" />
                      <input
                        type="text"
                        value={referenceSearch}
                        onChange={(e) => setReferenceSearch(e.target.value)}
                        placeholder="레퍼런스 검색..."
                        className="w-full pl-10 pr-4 py-2.5 bg-background border border-default rounded-xl text-foreground placeholder:text-muted focus:ring-2 focus:ring-accent-500 focus:border-transparent transition-all"
                      />
                    </div>

                    {filteredReferences.length === 0 ? (
                      <div className="text-center py-8">
                        <p className="text-muted">검색 결과가 없습니다</p>
                      </div>
                    ) : (
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-3 max-h-80 overflow-y-auto">
                      {filteredReferences.map((ref: AnalysisResult) => {
                        const thumbnailUrl = getThumbnailUrl(ref);
                        const platform = detectPlatform(ref.source_url || "");
                        const isSelected = config.referenceId === ref.analysis_id;

                        return (
                          <button
                            key={ref.analysis_id}
                            onClick={() =>
                              setConfig((prev) => ({
                                ...prev,
                                referenceId: ref.analysis_id,
                              }))
                            }
                            className={`relative rounded-xl overflow-hidden border-2 transition-all duration-200 ${
                              isSelected
                                ? "border-accent-500 shadow-glow-md ring-2 ring-accent-500/30"
                                : "border-default hover:border-muted"
                            }`}
                          >
                            {/* Thumbnail */}
                            <div className="aspect-square bg-gradient-to-br from-violet-600 via-indigo-600 to-purple-700 relative overflow-hidden">
                              {thumbnailUrl ? (
                                <img
                                  src={thumbnailUrl}
                                  alt={ref.title || "Reference"}
                                  className="absolute inset-0 w-full h-full object-cover"
                                />
                              ) : (
                                <div className="w-full h-full flex flex-col items-center justify-center p-2">
                                  <div className="w-10 h-10 rounded-lg bg-white/20 backdrop-blur-sm flex items-center justify-center mb-2">
                                    <ImageIcon className="w-5 h-5 text-white" />
                                  </div>
                                  <span className="text-white/80 text-xs font-medium">레퍼런스</span>
                                </div>
                              )}

                              {/* Platform badge */}
                              <div className="absolute top-2 left-2 px-2 py-0.5 bg-black/60 backdrop-blur-sm text-white text-xs font-medium rounded-md">
                                {platform}
                              </div>

                              {/* Selected indicator */}
                              {isSelected && (
                                <div className="absolute top-2 right-2 w-6 h-6 bg-accent-500 rounded-full flex items-center justify-center shadow-lg">
                                  <Check className="w-4 h-4 text-white" />
                                </div>
                              )}
                            </div>

                            {/* Title */}
                            <div className="p-2 bg-background">
                              <p className="text-xs font-medium text-foreground truncate">
                                {ref.title || "제목 없음"}
                              </p>
                            </div>
                          </button>
                        );
                      })}
                    </div>
                    )}

                    {/* Reference Analysis Selection */}
                    {config.referenceId && (
                      <div className="mt-6 space-y-3">
                        <div className="flex items-center justify-between">
                          <h4 className="font-medium text-foreground">분석 데이터 선택</h4>
                          {isLoadingAnalysis && (
                            <Loader2 className="w-4 h-4 animate-spin text-muted" />
                          )}
                        </div>

                        {selectedReferenceAnalysis && (
                          <div className="space-y-2">
                            {/* Section A: Analysis Info */}
                            <div className="text-xs font-medium text-muted uppercase tracking-wider mb-2">
                              분석 정보
                            </div>

                            {/* Hook Points Section */}
                            {selectedReferenceAnalysis.hook_points && selectedReferenceAnalysis.hook_points.length > 0 && (
                              <div className="border border-default rounded-xl overflow-hidden">
                                <button
                                  onClick={() => setExpandedSections(prev => ({ ...prev, hookPoints: !prev.hookPoints }))}
                                  className="w-full flex items-center justify-between p-3 bg-muted/30 hover:bg-muted/50 transition-colors"
                                >
                                  <div className="flex items-center gap-2">
                                    <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-electric-500 to-electric-600 flex items-center justify-center">
                                      <Zap className="w-4 h-4 text-white" />
                                    </div>
                                    <span className="font-medium text-foreground text-sm">Hook Points</span>
                                    <span className="text-xs text-muted">
                                      ({selectedHookPointIndices.length}/{selectedReferenceAnalysis.hook_points.length})
                                    </span>
                                  </div>
                                  {expandedSections.hookPoints ? (
                                    <ChevronUp className="w-4 h-4 text-muted" />
                                  ) : (
                                    <ChevronDown className="w-4 h-4 text-muted" />
                                  )}
                                </button>
                                {expandedSections.hookPoints && (
                                  <div className="p-3 space-y-2 bg-background">
                                    <div className="flex gap-2 mb-2">
                                      <button
                                        onClick={() => setSelectedHookPointIndices(
                                          selectedReferenceAnalysis.hook_points.map((_, i) => i)
                                        )}
                                        className="text-xs px-2 py-1 rounded bg-accent-500/10 text-accent-600 dark:text-accent-400 hover:bg-accent-500/20 transition-colors"
                                      >
                                        전체 선택
                                      </button>
                                      <button
                                        onClick={() => setSelectedHookPointIndices([])}
                                        className="text-xs px-2 py-1 rounded bg-muted/50 text-muted hover:bg-muted transition-colors"
                                      >
                                        선택 해제
                                      </button>
                                    </div>
                                    {selectedReferenceAnalysis.hook_points.map((hook, idx) => (
                                      <label
                                        key={idx}
                                        className="flex items-start gap-2 p-2 rounded-lg hover:bg-muted/30 cursor-pointer transition-colors"
                                      >
                                        <input
                                          type="checkbox"
                                          checked={selectedHookPointIndices.includes(idx)}
                                          onChange={(e) => {
                                            if (e.target.checked) {
                                              setSelectedHookPointIndices(prev => [...prev, idx]);
                                            } else {
                                              setSelectedHookPointIndices(prev => prev.filter(i => i !== idx));
                                            }
                                          }}
                                          className="mt-0.5 w-4 h-4 rounded border-muted text-accent-500 focus:ring-accent-500"
                                        />
                                        <div className="flex-1 min-w-0">
                                          <div className="flex items-center gap-2">
                                            <span className="text-xs font-medium text-accent-600 dark:text-accent-400">
                                              {hook.hook_type}
                                            </span>
                                            {hook.timestamp && (
                                              <span className="text-xs text-muted">{hook.timestamp}</span>
                                            )}
                                          </div>
                                          <p className="text-xs text-foreground/80 mt-0.5 line-clamp-2">
                                            {hook.description || hook.adaptable_template}
                                          </p>
                                        </div>
                                      </label>
                                    ))}
                                  </div>
                                )}
                              </div>
                            )}

                            {/* Edge Points Section */}
                            {selectedReferenceAnalysis.edge_points && selectedReferenceAnalysis.edge_points.length > 0 && (
                              <div className="border border-default rounded-xl overflow-hidden">
                                <button
                                  onClick={() => setExpandedSections(prev => ({ ...prev, edgePoints: !prev.edgePoints }))}
                                  className="w-full flex items-center justify-between p-3 bg-muted/30 hover:bg-muted/50 transition-colors"
                                >
                                  <div className="flex items-center gap-2">
                                    <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-accent-500 to-accent-600 flex items-center justify-center">
                                      <Target className="w-4 h-4 text-white" />
                                    </div>
                                    <span className="font-medium text-foreground text-sm">Edge Points</span>
                                    <span className="text-xs text-muted">
                                      ({selectedEdgePointIndices.length}/{selectedReferenceAnalysis.edge_points.length})
                                    </span>
                                  </div>
                                  {expandedSections.edgePoints ? (
                                    <ChevronUp className="w-4 h-4 text-muted" />
                                  ) : (
                                    <ChevronDown className="w-4 h-4 text-muted" />
                                  )}
                                </button>
                                {expandedSections.edgePoints && (
                                  <div className="p-3 space-y-2 bg-background">
                                    <div className="flex gap-2 mb-2">
                                      <button
                                        onClick={() => setSelectedEdgePointIndices(
                                          selectedReferenceAnalysis.edge_points.map((_, i) => i)
                                        )}
                                        className="text-xs px-2 py-1 rounded bg-accent-500/10 text-accent-600 dark:text-accent-400 hover:bg-accent-500/20 transition-colors"
                                      >
                                        전체 선택
                                      </button>
                                      <button
                                        onClick={() => setSelectedEdgePointIndices([])}
                                        className="text-xs px-2 py-1 rounded bg-muted/50 text-muted hover:bg-muted transition-colors"
                                      >
                                        선택 해제
                                      </button>
                                    </div>
                                    {selectedReferenceAnalysis.edge_points.map((edge, idx) => (
                                      <label
                                        key={idx}
                                        className="flex items-start gap-2 p-2 rounded-lg hover:bg-muted/30 cursor-pointer transition-colors"
                                      >
                                        <input
                                          type="checkbox"
                                          checked={selectedEdgePointIndices.includes(idx)}
                                          onChange={(e) => {
                                            if (e.target.checked) {
                                              setSelectedEdgePointIndices(prev => [...prev, idx]);
                                            } else {
                                              setSelectedEdgePointIndices(prev => prev.filter(i => i !== idx));
                                            }
                                          }}
                                          className="mt-0.5 w-4 h-4 rounded border-muted text-accent-500 focus:ring-accent-500"
                                        />
                                        <div className="flex-1 min-w-0">
                                          <div className="flex items-center gap-2">
                                            <span className="text-xs font-medium text-accent-600 dark:text-accent-400">
                                              {edge.category}
                                            </span>
                                          </div>
                                          <p className="text-xs text-foreground/80 mt-0.5 line-clamp-2">
                                            {edge.description}
                                          </p>
                                        </div>
                                      </label>
                                    ))}
                                  </div>
                                )}
                              </div>
                            )}

                            {/* Emotional Triggers Section */}
                            {selectedReferenceAnalysis.emotional_triggers && selectedReferenceAnalysis.emotional_triggers.length > 0 && (
                              <div className="border border-default rounded-xl overflow-hidden">
                                <button
                                  onClick={() => setExpandedSections(prev => ({ ...prev, triggers: !prev.triggers }))}
                                  className="w-full flex items-center justify-between p-3 bg-muted/30 hover:bg-muted/50 transition-colors"
                                >
                                  <div className="flex items-center gap-2">
                                    <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-glow-500 to-glow-600 flex items-center justify-center">
                                      <Heart className="w-4 h-4 text-white" />
                                    </div>
                                    <span className="font-medium text-foreground text-sm">Emotional Triggers</span>
                                    <span className="text-xs text-muted">
                                      ({selectedTriggerIndices.length}/{selectedReferenceAnalysis.emotional_triggers.length})
                                    </span>
                                  </div>
                                  {expandedSections.triggers ? (
                                    <ChevronUp className="w-4 h-4 text-muted" />
                                  ) : (
                                    <ChevronDown className="w-4 h-4 text-muted" />
                                  )}
                                </button>
                                {expandedSections.triggers && (
                                  <div className="p-3 space-y-2 bg-background">
                                    <div className="flex gap-2 mb-2">
                                      <button
                                        onClick={() => setSelectedTriggerIndices(
                                          selectedReferenceAnalysis.emotional_triggers.map((_, i) => i)
                                        )}
                                        className="text-xs px-2 py-1 rounded bg-accent-500/10 text-accent-600 dark:text-accent-400 hover:bg-accent-500/20 transition-colors"
                                      >
                                        전체 선택
                                      </button>
                                      <button
                                        onClick={() => setSelectedTriggerIndices([])}
                                        className="text-xs px-2 py-1 rounded bg-muted/50 text-muted hover:bg-muted transition-colors"
                                      >
                                        선택 해제
                                      </button>
                                    </div>
                                    {selectedReferenceAnalysis.emotional_triggers.map((trigger, idx) => (
                                      <label
                                        key={idx}
                                        className="flex items-start gap-2 p-2 rounded-lg hover:bg-muted/30 cursor-pointer transition-colors"
                                      >
                                        <input
                                          type="checkbox"
                                          checked={selectedTriggerIndices.includes(idx)}
                                          onChange={(e) => {
                                            if (e.target.checked) {
                                              setSelectedTriggerIndices(prev => [...prev, idx]);
                                            } else {
                                              setSelectedTriggerIndices(prev => prev.filter(i => i !== idx));
                                            }
                                          }}
                                          className="mt-0.5 w-4 h-4 rounded border-muted text-accent-500 focus:ring-accent-500"
                                        />
                                        <div className="flex-1 min-w-0">
                                          <div className="flex items-center gap-2">
                                            <span className="text-xs font-medium text-glow-600 dark:text-glow-400">
                                              {trigger.trigger_type}
                                            </span>
                                            {trigger.timestamp && (
                                              <span className="text-xs text-muted">{trigger.timestamp}</span>
                                            )}
                                          </div>
                                          <p className="text-xs text-foreground/80 mt-0.5 line-clamp-2">
                                            {trigger.description}
                                          </p>
                                        </div>
                                      </label>
                                    ))}
                                  </div>
                                )}
                              </div>
                            )}

                            {/* Selling Points Section */}
                            {selectedReferenceAnalysis.selling_points && selectedReferenceAnalysis.selling_points.length > 0 && (
                              <div className="border border-default rounded-xl overflow-hidden">
                                <button
                                  onClick={() => setExpandedSections(prev => ({ ...prev, sellingPoints: !prev.sellingPoints }))}
                                  className="w-full flex items-center justify-between p-3 bg-muted/30 hover:bg-muted/50 transition-colors"
                                >
                                  <div className="flex items-center gap-2">
                                    <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-yellow-500 to-orange-500 flex items-center justify-center">
                                      <Star className="w-4 h-4 text-white" />
                                    </div>
                                    <span className="font-medium text-foreground text-sm">Selling Points</span>
                                    <span className="text-xs text-muted">
                                      ({selectedSellingPointIndices.length}/{selectedReferenceAnalysis.selling_points.length})
                                    </span>
                                  </div>
                                  {expandedSections.sellingPoints ? (
                                    <ChevronUp className="w-4 h-4 text-muted" />
                                  ) : (
                                    <ChevronDown className="w-4 h-4 text-muted" />
                                  )}
                                </button>
                                {expandedSections.sellingPoints && (
                                  <div className="p-3 space-y-2 bg-background">
                                    <div className="flex gap-2 mb-2">
                                      <button
                                        onClick={() => setSelectedSellingPointIndices(
                                          selectedReferenceAnalysis.selling_points.map((_, i) => i)
                                        )}
                                        className="text-xs px-2 py-1 rounded bg-accent-500/10 text-accent-600 dark:text-accent-400 hover:bg-accent-500/20 transition-colors"
                                      >
                                        전체 선택
                                      </button>
                                      <button
                                        onClick={() => setSelectedSellingPointIndices([])}
                                        className="text-xs px-2 py-1 rounded bg-muted/50 text-muted hover:bg-muted transition-colors"
                                      >
                                        선택 해제
                                      </button>
                                    </div>
                                    {selectedReferenceAnalysis.selling_points.map((selling, idx) => (
                                      <label
                                        key={idx}
                                        className="flex items-start gap-2 p-2 rounded-lg hover:bg-muted/30 cursor-pointer transition-colors"
                                      >
                                        <input
                                          type="checkbox"
                                          checked={selectedSellingPointIndices.includes(idx)}
                                          onChange={(e) => {
                                            if (e.target.checked) {
                                              setSelectedSellingPointIndices(prev => [...prev, idx]);
                                            } else {
                                              setSelectedSellingPointIndices(prev => prev.filter(i => i !== idx));
                                            }
                                          }}
                                          className="mt-0.5 w-4 h-4 rounded border-muted text-accent-500 focus:ring-accent-500"
                                        />
                                        <div className="flex-1 min-w-0">
                                          <div className="flex items-center gap-2">
                                            <span className="text-xs font-medium text-yellow-600 dark:text-yellow-400">
                                              {selling.persuasion_technique}
                                            </span>
                                            {selling.timestamp && (
                                              <span className="text-xs text-muted">{selling.timestamp}</span>
                                            )}
                                          </div>
                                          <p className="text-xs text-foreground/80 mt-0.5 line-clamp-2">
                                            {selling.claim}
                                          </p>
                                        </div>
                                      </label>
                                    ))}
                                  </div>
                                )}
                              </div>
                            )}

                            {/* Section B: Recommendations */}
                            {selectedReferenceAnalysis.recommendations && selectedReferenceAnalysis.recommendations.length > 0 && (
                              <>
                                <div className="text-xs font-medium text-muted uppercase tracking-wider mt-4 mb-2">
                                  추천 사항
                                </div>
                                <div className="border border-default rounded-xl overflow-hidden">
                                  <button
                                    onClick={() => setExpandedSections(prev => ({ ...prev, recommendations: !prev.recommendations }))}
                                    className="w-full flex items-center justify-between p-3 bg-muted/30 hover:bg-muted/50 transition-colors"
                                  >
                                    <div className="flex items-center gap-2">
                                      <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-emerald-500 to-teal-500 flex items-center justify-center">
                                        <Lightbulb className="w-4 h-4 text-white" />
                                      </div>
                                      <span className="font-medium text-foreground text-sm">Recommendations</span>
                                      <span className="text-xs text-muted">
                                        ({selectedRecommendationIndices.length}/{selectedReferenceAnalysis.recommendations.length})
                                      </span>
                                    </div>
                                    {expandedSections.recommendations ? (
                                      <ChevronUp className="w-4 h-4 text-muted" />
                                    ) : (
                                      <ChevronDown className="w-4 h-4 text-muted" />
                                    )}
                                  </button>
                                  {expandedSections.recommendations && (
                                    <div className="p-3 space-y-2 bg-background">
                                      <div className="flex gap-2 mb-2">
                                        <button
                                          onClick={() => setSelectedRecommendationIndices(
                                            selectedReferenceAnalysis.recommendations.map((_, i) => i)
                                          )}
                                          className="text-xs px-2 py-1 rounded bg-accent-500/10 text-accent-600 dark:text-accent-400 hover:bg-accent-500/20 transition-colors"
                                        >
                                          전체 선택
                                        </button>
                                        <button
                                          onClick={() => setSelectedRecommendationIndices([])}
                                          className="text-xs px-2 py-1 rounded bg-muted/50 text-muted hover:bg-muted transition-colors"
                                        >
                                          선택 해제
                                        </button>
                                      </div>
                                      {selectedReferenceAnalysis.recommendations.map((rec, idx) => {
                                        // Handle both string and object recommendations
                                        const isStringRec = typeof rec === 'string';
                                        const recObj = isStringRec ? null : (rec as Recommendation);

                                        return (
                                          <label
                                            key={idx}
                                            className="flex items-start gap-2 p-2 rounded-lg hover:bg-muted/30 cursor-pointer transition-colors"
                                          >
                                            <input
                                              type="checkbox"
                                              checked={selectedRecommendationIndices.includes(idx)}
                                              onChange={(e) => {
                                                if (e.target.checked) {
                                                  setSelectedRecommendationIndices(prev => [...prev, idx]);
                                                } else {
                                                  setSelectedRecommendationIndices(prev => prev.filter(i => i !== idx));
                                                }
                                              }}
                                              className="mt-0.5 w-4 h-4 rounded border-muted text-accent-500 focus:ring-accent-500"
                                            />
                                            <div className="flex-1 min-w-0">
                                              {isStringRec ? (
                                                <p className="text-xs text-foreground/80 line-clamp-2">
                                                  {rec as string}
                                                </p>
                                              ) : (
                                                <>
                                                  <div className="flex items-center gap-2">
                                                    <span className={`text-xs font-medium px-1.5 py-0.5 rounded ${
                                                      recObj?.priority === 1
                                                        ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
                                                        : recObj?.priority === 2
                                                        ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400'
                                                        : 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
                                                    }`}>
                                                      P{recObj?.priority}
                                                    </span>
                                                  </div>
                                                  <p className="text-xs text-foreground/80 mt-0.5 line-clamp-2">
                                                    {recObj?.action}
                                                  </p>
                                                </>
                                              )}
                                            </div>
                                          </label>
                                        );
                                      })}
                                    </div>
                                  )}
                                </div>
                              </>
                            )}
                          </div>
                        )}
                      </div>
                    )}

                    {/* Additional prompt input for reference mode */}
                    <div className="mt-4 pt-4 border-t border-default">
                      <label className="block text-sm font-medium text-foreground mb-2">
                        추가 프롬프트 (선택사항)
                      </label>
                      <textarea
                        value={config.prompt || ""}
                        onChange={(e) =>
                          setConfig((prev) => ({ ...prev, prompt: e.target.value }))
                        }
                        placeholder="레퍼런스를 기반으로 추가하고 싶은 요소나 스타일을 입력하세요"
                        className="input h-24 resize-none text-sm"
                      />
                    </div>

                    <button
                      onClick={() => {
                        // Store selected analysis items in config before proceeding
                        if (selectedReferenceAnalysis) {
                          const selectedItems: SelectedAnalysisItems = {
                            hookPoints: selectedHookPointIndices.map(i => selectedReferenceAnalysis.hook_points[i]).filter(Boolean),
                            edgePoints: selectedEdgePointIndices.map(i => selectedReferenceAnalysis.edge_points[i]).filter(Boolean),
                            triggers: selectedTriggerIndices.map(i => selectedReferenceAnalysis.emotional_triggers[i]).filter(Boolean),
                            sellingPoints: selectedSellingPointIndices.map(i => selectedReferenceAnalysis.selling_points[i]).filter(Boolean),
                            recommendations: selectedRecommendationIndices.map(i => {
                              const rec = selectedReferenceAnalysis.recommendations[i];
                              // Convert string recommendations to Recommendation objects
                              if (typeof rec === 'string') {
                                return { priority: 3, action: rec, reason: '', example: '' } as Recommendation;
                              }
                              return rec as Recommendation;
                            }).filter(Boolean),
                          };
                          setConfig(prev => ({ ...prev, selectedAnalysisItems: selectedItems }));
                        }
                        handleNext();
                      }}
                      disabled={!config.referenceId}
                      className="btn-primary w-full disabled:opacity-50 disabled:cursor-not-allowed mt-4"
                    >
                      다음으로 <ArrowRight className="w-4 h-4 ml-2 inline" />
                    </button>
                  </div>
                )}
              </div>
            )}

            {/* Prompt Input - Only for Carousel */}
            {config.type === "carousel" && config.method === "prompt" && (
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-foreground mb-2">
                    프롬프트 입력
                  </label>
                  <textarea
                    value={config.prompt || ""}
                    onChange={(e) =>
                      setConfig((prev) => ({ ...prev, prompt: e.target.value }))
                    }
                    placeholder="예: 화이트 배경에 립스틱 제품이 중앙에 있고, 주변에 꽃잎이 흩날리는 고급스러운 느낌의 이미지"
                    className="input h-36 resize-none"
                  />
                </div>
                <button
                  onClick={handleNext}
                  disabled={!config.prompt?.trim()}
                  className="btn-primary w-full disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  다음으로 <ArrowRight className="w-4 h-4 ml-2 inline" />
                </button>
              </div>
            )}
          </div>
        )}

        {/* Step 4: Generate - Branches based on content type */}
        {step === 4 && (
          <div className="space-y-8">
            {/* Single Image or Story: Concept Suggestion (both upload and reference modes) */}
            {(config.type === "single" || config.type === "story") && (
              <>
                <div className="text-center">
                  <h2 className="font-display text-2xl font-bold text-foreground mb-2">
                    AI 컨셉 제안
                  </h2>
                  <p className="text-muted">
                    {config.uploadedReferenceImages?.length
                      ? "업로드한 이미지를 기반으로 최적의 비주얼 컨셉을 제안합니다"
                      : "입력한 프롬프트를 기반으로 최적의 비주얼 컨셉을 제안합니다"}
                  </p>
                </div>

                {/* Uploaded Images Preview */}
                {(config.uploadedReferenceImages?.length || config.prompt) && (
                  <div className="p-4 rounded-2xl bg-muted/30 dark:bg-muted/10 border border-default">
                    {config.uploadedReferenceImages && config.uploadedReferenceImages.length > 0 && (
                      <>
                        <p className="text-sm font-medium text-foreground mb-3">참고 이미지</p>
                        <div className="flex flex-wrap gap-3">
                          {config.uploadedReferenceImages.map((img, index) => (
                            <img
                              key={index}
                              src={img.previewUrl}
                              alt={`참고 이미지 ${index + 1}`}
                              className="w-20 h-20 object-cover rounded-xl"
                            />
                          ))}
                        </div>
                      </>
                    )}
                    {config.prompt && (
                      <div className={config.uploadedReferenceImages?.length ? "mt-3 pt-3 border-t border-default" : ""}>
                        <p className="text-xs text-muted mb-1">프롬프트</p>
                        <p className="text-sm text-foreground">{config.prompt}</p>
                      </div>
                    )}
                  </div>
                )}

                {/* Loading State */}
                {isGeneratingConcept && (
                  <div className="p-6 rounded-2xl bg-muted/30 dark:bg-muted/10 border border-default">
                    <div className="text-center py-8">
                      <Loader2 className="w-12 h-12 animate-spin text-accent-500 mx-auto mb-4" />
                      <p className="font-medium text-foreground mb-2">AI가 컨셉을 분석하고 있습니다...</p>
                      <p className="text-sm text-muted">잠시만 기다려주세요</p>
                    </div>
                  </div>
                )}

                {/* Concept Suggestion Display */}
                {conceptSuggestion && !isGeneratingConcept && (
                  <div className="space-y-6">
                    {/* Concept Cards */}
                    <div className="p-6 rounded-2xl border border-accent-500/30 bg-accent-500/5">
                      <h3 className="font-semibold text-foreground mb-4 flex items-center gap-2">
                        <Sparkles className="w-5 h-5 text-accent-500" />
                        AI 컨셉 제안
                      </h3>

                      <div className="space-y-4">
                        {/* Visual Concept */}
                        <div className="p-4 rounded-xl bg-muted/30">
                          <h4 className="text-sm font-medium text-foreground mb-2 flex items-center gap-2">
                            <ImageIcon className="w-4 h-4 text-electric-500" />
                            비주얼 컨셉
                          </h4>
                          <p className="text-sm text-foreground/80 leading-relaxed">
                            {conceptSuggestion.visual_concept}
                          </p>
                        </div>

                        {/* Copy Suggestion */}
                        <div className="p-4 rounded-xl bg-muted/30">
                          <h4 className="text-sm font-medium text-foreground mb-2 flex items-center gap-2">
                            <Edit3 className="w-4 h-4 text-glow-500" />
                            카피 제안
                          </h4>
                          <p className="text-sm text-foreground/80 leading-relaxed">
                            {conceptSuggestion.copy_suggestion}
                          </p>
                        </div>

                        {/* Style Recommendation */}
                        <div className="p-4 rounded-xl bg-muted/30">
                          <h4 className="text-sm font-medium text-foreground mb-2 flex items-center gap-2">
                            <Sparkles className="w-4 h-4 text-accent-500" />
                            스타일 제안
                          </h4>
                          <p className="text-sm text-foreground/80 leading-relaxed">
                            {conceptSuggestion.style_recommendation}
                          </p>
                        </div>

                        {/* Text Overlay Suggestion (if available) */}
                        {conceptSuggestion.text_overlay_suggestion && (
                          <div className="p-4 rounded-xl bg-muted/30">
                            <h4 className="text-sm font-medium text-foreground mb-2 flex items-center gap-2">
                              <Megaphone className="w-4 h-4 text-yellow-500" />
                              텍스트 오버레이 제안
                            </h4>
                            <p className="text-sm text-foreground/80 leading-relaxed font-medium">
                              &ldquo;{conceptSuggestion.text_overlay_suggestion}&rdquo;
                            </p>
                          </div>
                        )}
                      </div>

                      {/* Action Buttons */}
                      <div className="flex gap-4 mt-6">
                        <button
                          onClick={handleRegenerateConcept}
                          disabled={isGeneratingConcept}
                          className="btn-secondary flex-1 flex items-center justify-center gap-2"
                        >
                          <RefreshCw className={`w-4 h-4 ${isGeneratingConcept ? 'animate-spin' : ''}`} />
                          다시 제안받기
                        </button>
                        <button
                          onClick={handleConfirmConcept}
                          disabled={isGenerating}
                          className="btn-primary flex-1 flex items-center justify-center gap-2"
                        >
                          {isGenerating ? (
                            <>
                              <Loader2 className="w-4 h-4 animate-spin" />
                              이미지 생성 중...
                            </>
                          ) : (
                            <>
                              <Check className="w-4 h-4" />
                              컨셉 확정
                            </>
                          )}
                        </button>
                      </div>
                    </div>
                  </div>
                )}
              </>
            )}

            {/* Single Image or Story with Prompt Method: Direct image generation */}
            {(config.type === "single" || config.type === "story") && config.method === "prompt" && (
              <>
                <div className="text-center">
                  <h2 className="font-display text-2xl font-bold text-foreground mb-2">
                    이미지 생성
                  </h2>
                  <p className="text-muted">AI가 4개의 변형 이미지를 생성합니다</p>
                </div>

                {/* Summary */}
                <div className="p-6 rounded-2xl bg-muted/30 dark:bg-muted/10 border border-default space-y-3">
                  <div className="flex justify-between py-2 border-b border-default">
                    <span className="text-muted">콘텐츠 유형</span>
                    <span className="font-medium text-foreground">
                      {config.type === "single" ? "단일 이미지" : "세로형"}
                    </span>
                  </div>
                  <div className="flex justify-between py-2 border-b border-default">
                    <span className="text-muted">용도</span>
                    <span className="font-medium text-foreground">
                      {config.purpose === "ad" && "광고/홍보"}
                      {config.purpose === "info" && "정보성"}
                      {config.purpose === "lifestyle" && "일상/감성"}
                    </span>
                  </div>
                  <div className="flex justify-between py-2 border-b border-default">
                    <span className="text-muted">생성 방식</span>
                    <span className="font-medium text-foreground">직접 만들기</span>
                  </div>
                  {config.prompt && (
                    <div className="pt-2">
                      <span className="text-muted text-sm block mb-2">프롬프트</span>
                      <p className="text-sm text-foreground leading-relaxed bg-muted/50 p-3 rounded-lg">
                        {config.prompt}
                      </p>
                    </div>
                  )}
                </div>

                <button
                  onClick={handleGenerateImages}
                  disabled={isGenerating}
                  className="btn-primary w-full py-4 text-base disabled:opacity-50 flex items-center justify-center gap-3"
                >
                  {isGenerating ? (
                    <>
                      <Loader2 className="w-5 h-5 animate-spin" />
                      이미지 생성 중...
                    </>
                  ) : (
                    <>
                      <Wand2 className="w-5 h-5" />
                      이미지 생성하기
                    </>
                  )}
                </button>
              </>
            )}

            {/* Carousel only: Storyboard generation */}
            {config.type === "carousel" && (
              <>
                <div className="text-center">
                  <h2 className="font-display text-2xl font-bold text-foreground mb-2">
                    스토리보드 생성
                  </h2>
                  <p className="text-muted">
                    AI가 캐러셀 슬라이드 구성을 생성합니다
                  </p>
                </div>

                {/* Summary before storyboard generation */}
                {!storyboard && (
                  <>
                    <div className="p-6 rounded-2xl bg-muted/30 dark:bg-muted/10 border border-default space-y-3">
                      <div className="flex justify-between py-2 border-b border-default">
                        <span className="text-muted">콘텐츠 유형</span>
                        <span className="font-medium text-foreground">
                          {config.type === "carousel" ? "캐러셀" : "세로형"}
                        </span>
                      </div>
                      <div className="flex justify-between py-2 border-b border-default">
                        <span className="text-muted">용도</span>
                        <span className="font-medium text-foreground">
                          {config.purpose === "ad" && "광고/홍보"}
                          {config.purpose === "info" && "정보성"}
                          {config.purpose === "lifestyle" && "일상/감성"}
                        </span>
                      </div>
                      <div className="flex justify-between py-2 border-b border-default">
                        <span className="text-muted">생성 방식</span>
                        <span className="font-medium text-foreground">
                          {config.method === "reference" && "레퍼런스 활용"}
                          {config.method === "prompt" && "직접 만들기"}
                        </span>
                      </div>
                      {config.prompt && (
                        <div className="pt-2">
                          <span className="text-muted text-sm block mb-2">프롬프트</span>
                          <p className="text-sm text-foreground leading-relaxed bg-muted/50 p-3 rounded-lg">
                            {config.prompt}
                          </p>
                        </div>
                      )}
                    </div>

                    <button
                      onClick={handleGenerateStoryboard}
                      disabled={isGeneratingStoryboard}
                      className="btn-primary w-full py-4 text-base disabled:opacity-50 flex items-center justify-center gap-3"
                    >
                      {isGeneratingStoryboard ? (
                        <>
                          <Loader2 className="w-5 h-5 animate-spin" />
                          스토리보드 생성 중...
                        </>
                      ) : (
                        <>
                          <Wand2 className="w-5 h-5" />
                          스토리보드 생성하기
                        </>
                      )}
                    </button>
                  </>
                )}

                {/* Storyboard Display */}
                {storyboard && (
                  <div className="space-y-6">
                    {/* Storyline */}
                    <div className="p-4 rounded-xl bg-gradient-to-r from-accent-500/10 to-electric-500/10 border border-accent-500/20">
                      <h3 className="font-semibold text-foreground mb-2 flex items-center gap-2">
                        <Sparkles className="w-4 h-4 text-accent-500" />
                        스토리라인
                      </h3>
                      <p className="text-sm text-foreground/80 leading-relaxed">
                        {storyboard.storyline}
                      </p>
                    </div>

                    {/* Style Notes if available */}
                    {storyboard.style_notes && (
                      <div className="p-3 rounded-lg bg-muted/30 border border-default">
                        <p className="text-xs text-muted">
                          <span className="font-medium">스타일 노트:</span> {storyboard.style_notes}
                        </p>
                      </div>
                    )}

                    {/* Slide Cards Grid */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {storyboard.slides.map((slide) => {
                        const badge = getSectionTypeBadge(slide.section_type);
                        return (
                          <div
                            key={slide.slide_number}
                            className="p-4 rounded-xl border border-default bg-background hover:border-accent-500/50 transition-colors"
                          >
                            {/* Slide Header */}
                            <div className="flex items-start justify-between mb-3">
                              <div className="flex items-center gap-2">
                                <span className="w-7 h-7 rounded-lg bg-accent-500/20 flex items-center justify-center text-sm font-bold text-accent-600 dark:text-accent-400">
                                  {slide.slide_number}
                                </span>
                                <span className={`px-2 py-0.5 rounded-md text-xs font-medium ${badge.bg} ${badge.text}`}>
                                  {badge.label}
                                </span>
                              </div>
                              <div className="flex items-center gap-2">
                                {slide.duration_seconds && (
                                  <span className="text-xs text-muted">
                                    {slide.duration_seconds}s
                                  </span>
                                )}
                                <button
                                  onClick={() => handleDeleteSlide(slide.slide_number)}
                                  className="p-1 text-muted hover:text-red-500 hover:bg-red-500/10 rounded transition-colors"
                                  title="슬라이드 삭제"
                                >
                                  <Trash2 className="w-4 h-4" />
                                </button>
                              </div>
                            </div>

                            {/* Slide Title */}
                            <h4 className="font-medium text-foreground mb-2">
                              {slide.title}
                            </h4>

                            {/* Slide Description */}
                            <p className="text-sm text-muted leading-relaxed mb-3">
                              {slide.description}
                            </p>

                            {/* Text Overlay Preview */}
                            {slide.text_overlay && (
                              <div className="p-2 rounded-lg bg-muted/30 border border-dashed border-muted">
                                <p className="text-xs text-muted mb-1 font-medium">텍스트 오버레이</p>
                                <p className="text-sm text-foreground font-medium">
                                  &ldquo;{slide.text_overlay}&rdquo;
                                </p>
                              </div>
                            )}

                            {/* Visual Prompt - Editable */}
                            {(slide.visual_prompt_display || slide.visual_prompt || slide.visual_direction) && (
                              <div className="mt-2 pt-2 border-t border-default">
                                {editingSlideNumber === slide.slide_number ? (
                                  <div className="space-y-2">
                                    <p className="text-xs text-muted font-medium">비주얼 프롬프트 편집</p>
                                    <textarea
                                      value={editingPrompt}
                                      onChange={(e) => setEditingPrompt(e.target.value)}
                                      className="w-full p-2 text-sm rounded-lg bg-background border border-default focus:border-accent-500 focus:ring-1 focus:ring-accent-500 resize-none"
                                      rows={3}
                                      autoFocus
                                    />
                                    <div className="flex gap-2 justify-end">
                                      <button
                                        onClick={handleCancelEdit}
                                        className="px-2 py-1 text-xs text-muted hover:text-foreground"
                                      >
                                        취소
                                      </button>
                                      <button
                                        onClick={handleSavePrompt}
                                        className="px-2 py-1 text-xs bg-accent-500 text-white rounded hover:bg-accent-600"
                                      >
                                        저장
                                      </button>
                                    </div>
                                  </div>
                                ) : (
                                  <div
                                    className="group cursor-pointer"
                                    onDoubleClick={() => handleStartEditPrompt(
                                      slide.slide_number,
                                      slide.visual_prompt_display || slide.visual_prompt || slide.visual_direction || ""
                                    )}
                                  >
                                    <div className="flex items-start gap-2">
                                      <p className="text-xs text-muted flex-1">
                                        <span className="font-medium">비주얼 프롬프트:</span>{" "}
                                        {slide.visual_prompt_display || slide.visual_prompt || slide.visual_direction}
                                      </p>
                                      <button
                                        onClick={() => handleStartEditPrompt(
                                          slide.slide_number,
                                          slide.visual_prompt_display || slide.visual_prompt || slide.visual_direction || ""
                                        )}
                                        className="opacity-0 group-hover:opacity-100 transition-opacity p-1 hover:bg-muted/30 rounded"
                                        title="비주얼 프롬프트 편집"
                                      >
                                        <Edit3 className="w-3 h-3 text-muted" />
                                      </button>
                                    </div>
                                    <p className="text-[10px] text-muted/60 mt-1">더블클릭하여 편집</p>
                                  </div>
                                )}
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>

                    {/* Generation Mode Selection */}
                    <div className="p-4 rounded-xl bg-muted/30 border border-default">
                      <h4 className="font-medium text-foreground mb-3">이미지 생성 방식 선택</h4>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        {/* Bulk Generation Option - Only shown if purpose is "ad" AND product is selected */}
                        {config.purpose === "ad" && config.productId && (
                          <button
                            onClick={() => setGenerationMode("bulk")}
                            className={`p-4 rounded-xl border-2 text-left transition-all ${
                              generationMode === "bulk"
                                ? "border-accent-500 bg-accent-500/10"
                                : "border-default hover:border-muted"
                            }`}
                          >
                            <div className="flex items-center gap-3 mb-2">
                              <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-electric-500 to-electric-600 flex items-center justify-center">
                                <Layers className="w-5 h-5 text-white" />
                              </div>
                              <div>
                                <p className="font-semibold text-foreground">전체 생성</p>
                                <p className="text-xs text-muted">모든 섹션을 한번에 생성</p>
                              </div>
                            </div>
                            <p className="text-xs text-muted/80 leading-relaxed">
                              모든 슬라이드의 이미지를 자동으로 생성합니다. 생성 후 개별적으로 수정할 수 있습니다.
                            </p>
                          </button>
                        )}

                        {/* Step-by-Step Generation Option - Always available */}
                        <button
                          onClick={() => setGenerationMode("step_by_step")}
                          className={`p-4 rounded-xl border-2 text-left transition-all ${
                            generationMode === "step_by_step"
                              ? "border-accent-500 bg-accent-500/10"
                              : "border-default hover:border-muted"
                          }`}
                        >
                          <div className="flex items-center gap-3 mb-2">
                            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-glow-500 to-glow-600 flex items-center justify-center">
                              <Wand2 className="w-5 h-5 text-white" />
                            </div>
                            <div>
                              <p className="font-semibold text-foreground">단계별 생성</p>
                              <p className="text-xs text-muted">한 섹션씩 확인하며 생성</p>
                            </div>
                          </div>
                          <p className="text-xs text-muted/80 leading-relaxed">
                            첫 번째 이미지를 레퍼런스로 사용하여 일관된 스타일로 순차 생성합니다.
                          </p>
                        </button>
                      </div>
                    </div>

                    {/* Storyboard Actions */}
                    <div className="flex gap-4">
                      <button
                        onClick={() => {
                          setStoryboard(null);
                        }}
                        className="btn-secondary flex-1 flex items-center justify-center gap-2"
                      >
                        <RefreshCw className="w-4 h-4" />
                        다시 생성
                      </button>
                      <button
                        onClick={() => handleConfirmStoryboard(generationMode)}
                        className="btn-primary flex-1 flex items-center justify-center gap-2"
                      >
                        {generationMode === "step_by_step" ? "단계별 생성 시작" : "전체 생성 시작"}
                        <ArrowRight className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        )}

        {/* Step 5: Select Generated Image */}
        {step === 5 && (
          <div className="space-y-8">
            {/* Single Image or Story Selection (existing behavior) */}
            {(config.type === "single" || config.type === "story") && (
              <>
                <div className="text-center">
                  <h2 className="font-display text-2xl font-bold text-foreground mb-2">
                    이미지 선택
                  </h2>
                  <p className="text-muted">마음에 드는 이미지를 선택하세요</p>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  {isGenerating ? (
                    // Loading state while generating images
                    Array.from({ length: 2 }).map((_, i) => (
                      <div
                        key={i}
                        className="aspect-square rounded-2xl bg-muted/30 border border-default flex flex-col items-center justify-center animate-pulse"
                      >
                        <Loader2 className="w-10 h-10 animate-spin text-accent-500 mb-3" />
                        <p className="text-sm text-muted">이미지 생성 중...</p>
                      </div>
                    ))
                  ) : generatedImages.length > 0 ? (
                    generatedImages.map((img, i) => (
                      <button
                        key={i}
                        onClick={() => handleSelectImage(i)}
                        className={`aspect-square rounded-2xl overflow-hidden relative border-2 transition-all duration-300 ${
                          selectedImageIndex === i
                            ? "border-accent-500 shadow-glow-md"
                            : "border-default hover:border-muted"
                        }`}
                      >
                        {/* eslint-disable-next-line @next/next/no-img-element */}
                        <img
                          src={img}
                          alt={`Generated image variant ${i + 1}`}
                          className="w-full h-full object-cover"
                          onError={(e) => {
                            const target = e.target as HTMLImageElement;
                            target.style.display = 'none';
                            target.nextElementSibling?.classList.remove('hidden');
                          }}
                        />
                        <div className="hidden w-full h-full bg-muted flex items-center justify-center absolute inset-0">
                          <ImageIcon className="w-16 h-16 text-muted" />
                        </div>
                        {selectedImageIndex === i && (
                          <div className="absolute top-3 right-3 w-8 h-8 bg-accent-500 rounded-full flex items-center justify-center shadow-lg">
                            <Check className="w-5 h-5 text-white" />
                          </div>
                        )}
                        <div className="absolute bottom-3 left-3">
                          <span className="badge badge-accent">변형 {i + 1}</span>
                        </div>
                      </button>
                    ))
                  ) : (
                    <div className="col-span-2 text-center py-16 text-muted">
                      생성된 이미지가 없습니다
                    </div>
                  )}
                </div>

                <div className="flex gap-4">
                  <button
                    onClick={() => {
                      // Reset concept suggestion when going back to step 4 for reference method
                      if (config.method === "reference") {
                        setConceptSuggestion(null);
                      }
                      setStep(4);
                    }}
                    disabled={isGenerating}
                    className="btn-secondary flex-1 flex items-center justify-center gap-2 disabled:opacity-50"
                  >
                    <RefreshCw className="w-4 h-4" />
                    다시 생성
                  </button>
                  <button
                    onClick={handleProceedToEdit}
                    disabled={selectedImageIndex === null || isGenerating}
                    className="btn-primary flex-1 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    편집하기 <ArrowRight className="w-4 h-4 ml-2 inline" />
                  </button>
                </div>
              </>
            )}

            {/* Section-based Image Selection for Carousel only */}
            {config.type === "carousel" && storyboard && (
              <>
                {/* Step-by-Step Mode UI */}
                {generationMode === "step_by_step" && (
                  <>
                    <div className="text-center">
                      <h2 className="font-display text-2xl font-bold text-foreground mb-2">
                        단계별 이미지 생성
                      </h2>
                      <p className="text-muted">
                        섹션 {currentSectionIndex + 1}/{storyboard.slides.length} - 이미지를 선택하고 다음으로 진행하세요
                      </p>
                    </div>

                    {/* Progress Bar for Step-by-Step */}
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span className="text-muted">
                          {currentGeneratingSection !== null ? (
                            <>이미지 생성 중...</>
                          ) : (
                            <>완료: {approvedSections.size}/{storyboard.slides.length}</>
                          )}
                        </span>
                        <span className="text-accent-500 font-medium">
                          {Math.round((approvedSections.size / storyboard.slides.length) * 100)}%
                        </span>
                      </div>
                      <div className="h-2 bg-muted/30 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-gradient-to-r from-accent-500 to-electric-500 transition-all duration-500"
                          style={{ width: `${(approvedSections.size / storyboard.slides.length) * 100}%` }}
                        />
                      </div>
                    </div>

                    {/* Already Approved Sections Thumbnails */}
                    {approvedSections.size > 0 && (
                      <div className="p-4 rounded-xl bg-muted/20 border border-default">
                        <p className="text-xs text-muted font-medium mb-3">선택 완료된 섹션</p>
                        <div className="flex gap-2 overflow-x-auto pb-2">
                          {storyboard.slides.filter(s => approvedSections.has(s.slide_number)).map((slide) => {
                            const images = sectionImages[slide.slide_number] || [];
                            const selectedIdx = selectedSectionImages[slide.slide_number];
                            const selectedImg = selectedIdx !== undefined ? images[selectedIdx] : null;

                            return (
                              <div
                                key={slide.slide_number}
                                className="flex-shrink-0 w-16 h-16 rounded-lg overflow-hidden border-2 border-green-500/50 relative cursor-pointer"
                                onClick={() => setCurrentSectionIndex(storyboard.slides.findIndex(s => s.slide_number === slide.slide_number))}
                              >
                                {selectedImg ? (
                                  // eslint-disable-next-line @next/next/no-img-element
                                  <img src={selectedImg} alt={`Section ${slide.slide_number}`} className="w-full h-full object-cover" />
                                ) : (
                                  <div className="w-full h-full bg-muted flex items-center justify-center">
                                    <ImageIcon className="w-4 h-4 text-muted" />
                                  </div>
                                )}
                                <div className="absolute top-0.5 left-0.5 w-4 h-4 bg-green-500 rounded-full flex items-center justify-center text-[8px] text-white font-bold">
                                  {slide.slide_number}
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    )}

                    {/* Current Section Large Preview */}
                    {(() => {
                      const currentSlide = storyboard.slides[currentSectionIndex];
                      if (!currentSlide) return null;

                      const badge = getSectionTypeBadge(currentSlide.section_type);
                      const images = sectionImages[currentSlide.slide_number] || [];
                      const isGenerating = currentGeneratingSection === currentSlide.slide_number;
                      const selectedIdx = selectedSectionImages[currentSlide.slide_number];

                      return (
                        <div className="p-6 rounded-2xl border-2 border-accent-500/30 bg-accent-500/5">
                          {/* Current Section Header */}
                          <div className="flex items-center justify-between mb-4">
                            <div className="flex items-center gap-3">
                              <span className="w-10 h-10 rounded-xl bg-accent-500 flex items-center justify-center text-lg font-bold text-white">
                                {currentSlide.slide_number}
                              </span>
                              <div>
                                <div className="flex items-center gap-2 mb-1">
                                  <span className={`px-2 py-0.5 rounded-md text-xs font-medium ${badge.bg} ${badge.text}`}>
                                    {badge.label}
                                  </span>
                                  {currentSectionIndex === 0 && !referenceImageId && (
                                    <span className="px-2 py-0.5 rounded-md text-xs font-medium bg-electric-500/20 text-electric-600 dark:text-electric-400">
                                      레퍼런스 이미지
                                    </span>
                                  )}
                                </div>
                                <h4 className="font-semibold text-foreground text-lg">{currentSlide.title}</h4>
                              </div>
                            </div>
                          </div>

                          {/* Visual Prompt */}
                          {(currentSlide.visual_prompt_display || currentSlide.visual_prompt) && (
                            <div className="mb-4 p-3 rounded-lg bg-muted/30 border border-dashed border-muted">
                              <p className="text-xs text-muted font-medium mb-1">비주얼 프롬프트</p>
                              <p className="text-sm text-foreground/80">{currentSlide.visual_prompt_display || currentSlide.visual_prompt}</p>
                            </div>
                          )}

                          {/* Large Image Grid for Current Section */}
                          <div className="grid grid-cols-2 gap-4 mb-6">
                            {isGenerating ? (
                              Array.from({ length: 2 }).map((_, i) => (
                                <div
                                  key={i}
                                  className="aspect-square rounded-xl bg-muted/30 border border-default flex flex-col items-center justify-center animate-pulse"
                                >
                                  <Loader2 className="w-8 h-8 animate-spin text-accent-500 mb-2" />
                                  <p className="text-sm text-muted">이미지 생성 중...</p>
                                </div>
                              ))
                            ) : images.length > 0 ? (
                              images.map((img, i) => (
                                <button
                                  key={i}
                                  onClick={() => setPreviewImage({ url: img, slideNumber: currentSlide.slide_number, variantIndex: i })}
                                  className={`aspect-square rounded-xl overflow-hidden relative border-3 transition-all duration-300 group ${
                                    selectedIdx === i
                                      ? "border-accent-500 shadow-glow-md ring-2 ring-accent-500/30"
                                      : "border-default hover:border-muted"
                                  }`}
                                >
                                  {/* eslint-disable-next-line @next/next/no-img-element */}
                                  <img
                                    src={img}
                                    alt={`Variant ${i + 1}`}
                                    className="w-full h-full object-cover"
                                    onError={(e) => {
                                      const target = e.target as HTMLImageElement;
                                      target.style.display = 'none';
                                    }}
                                  />
                                  <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                                    <ZoomIn className="w-8 h-8 text-white" />
                                  </div>
                                  {selectedIdx === i && (
                                    <div className="absolute top-3 right-3 w-8 h-8 bg-accent-500 rounded-full flex items-center justify-center shadow-lg z-10">
                                      <Check className="w-5 h-5 text-white" />
                                    </div>
                                  )}
                                  <div className="absolute bottom-3 left-3 z-10">
                                    <span className="px-2 py-1 text-sm font-medium bg-black/60 text-white rounded-lg">
                                      변형 {i + 1}
                                    </span>
                                  </div>
                                </button>
                              ))
                            ) : (
                              <div className="col-span-2 text-center py-12 text-muted">
                                이미지를 생성 중입니다...
                              </div>
                            )}
                          </div>

                          {/* Step-by-Step Action Buttons */}
                          <div className="flex gap-3">
                            {currentSectionIndex > 0 && (
                              <button
                                onClick={handlePreviousSection}
                                className="btn-secondary px-4 py-3 flex items-center gap-2"
                              >
                                <ChevronLeft className="w-4 h-4" />
                                이전 섹션
                              </button>
                            )}
                            <button
                              onClick={handleRegenerateCurrentSection}
                              disabled={isGenerating}
                              className="btn-secondary flex-1 flex items-center justify-center gap-2 disabled:opacity-50"
                            >
                              <RefreshCw className={`w-4 h-4 ${isGenerating ? 'animate-spin' : ''}`} />
                              다시 생성
                            </button>
                            {selectedIdx !== undefined ? (
                              <button
                                onClick={() => handleApproveSection(selectedIdx)}
                                disabled={isGenerating}
                                className="btn-primary flex-1 flex items-center justify-center gap-2 disabled:opacity-50"
                              >
                                {currentSectionIndex >= storyboard.slides.length - 1 ? (
                                  <>
                                    <Check className="w-4 h-4" />
                                    완료
                                  </>
                                ) : (
                                  <>
                                    이 이미지로 선택
                                    <ArrowRight className="w-4 h-4" />
                                  </>
                                )}
                              </button>
                            ) : (
                              <div className="flex-1 text-center text-sm text-muted flex items-center justify-center">
                                이미지를 클릭하여 선택하세요
                              </div>
                            )}
                          </div>
                        </div>
                      );
                    })()}

                    {/* All Sections Complete - Proceed to Edit */}
                    {allSectionsSelected && (
                      <div className="flex gap-4 pt-4">
                        <button
                          onClick={() => {
                            setSectionImages({});
                            setSelectedSectionImages({});
                            setApprovedSections(new Set());
                            setCurrentSectionIndex(0);
                            setReferenceImageId(null);
                            setStep(4);
                          }}
                          className="btn-secondary flex-1 flex items-center justify-center gap-2"
                        >
                          <RefreshCw className="w-4 h-4" />
                          스토리보드 수정
                        </button>
                        <button
                          onClick={handleProceedToEditWithSections}
                          className="btn-primary flex-1 flex items-center justify-center gap-2"
                        >
                          편집하기 <ArrowRight className="w-4 h-4" />
                        </button>
                      </div>
                    )}
                  </>
                )}

                {/* Bulk Mode UI (existing behavior with regenerate button) */}
                {generationMode === "bulk" && (
                  <>
                    <div className="text-center">
                      <h2 className="font-display text-2xl font-bold text-foreground mb-2">
                        섹션별 이미지 선택
                      </h2>
                      <p className="text-muted">각 섹션에 사용할 이미지를 선택하세요</p>
                    </div>

                    {/* Progress Bar */}
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span className="text-muted">
                          {currentGeneratingSection !== null ? (
                            <>슬라이드 {generationProgress.current}/{generationProgress.total} 이미지 생성 중...</>
                          ) : (
                            <>선택 완료: {selectedSectionsCount}/{storyboard.slides.length}</>
                          )}
                        </span>
                        <span className="text-accent-500 font-medium">
                          {currentGeneratingSection !== null
                            ? `${Math.round((generationProgress.current / generationProgress.total) * 100)}%`
                            : `${Math.round((selectedSectionsCount / storyboard.slides.length) * 100)}%`}
                        </span>
                      </div>
                      <div className="h-2 bg-muted/30 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-gradient-to-r from-accent-500 to-electric-500 transition-all duration-500"
                          style={{
                            width: currentGeneratingSection !== null
                              ? `${(generationProgress.current / generationProgress.total) * 100}%`
                              : `${(selectedSectionsCount / storyboard.slides.length) * 100}%`,
                          }}
                        />
                      </div>
                    </div>

                    {/* Section Cards with Images */}
                    <div className="space-y-6">
                      {storyboard.slides.map((slide) => {
                        const badge = getSectionTypeBadge(slide.section_type);
                        const images = sectionImages[slide.slide_number] || [];
                        const isGenerating = currentGeneratingSection === slide.slide_number;
                        const isPending = currentGeneratingSection !== null && !sectionImages[slide.slide_number];
                        const selectedIndex = selectedSectionImages[slide.slide_number];
                        const isRegeneratingThis = isRegenerating === slide.slide_number;

                        return (
                          <div
                            key={slide.slide_number}
                            className="p-5 rounded-2xl border border-default bg-background"
                          >
                            {/* Section Header */}
                            <div className="flex items-start justify-between mb-4">
                              <div className="flex items-center gap-3">
                                <span className="w-9 h-9 rounded-xl bg-accent-500/20 flex items-center justify-center text-base font-bold text-accent-600 dark:text-accent-400">
                                  {slide.slide_number}
                                </span>
                                <div>
                                  <div className="flex items-center gap-2 mb-1">
                                    <span className={`px-2 py-0.5 rounded-md text-xs font-medium ${badge.bg} ${badge.text}`}>
                                      {badge.label}
                                    </span>
                                    {selectedIndex !== undefined && (
                                      <span className="px-2 py-0.5 rounded-md text-xs font-medium bg-green-500/20 text-green-600 dark:text-green-400">
                                        선택됨
                                      </span>
                                    )}
                                  </div>
                                  <h4 className="font-medium text-foreground">
                                    {slide.title}
                                  </h4>
                                </div>
                              </div>
                              <div className="flex items-center gap-2">
                                {/* Regenerate Button for Bulk Mode */}
                                {images.length > 0 && !isGenerating && !isRegeneratingThis && (
                                  <button
                                    onClick={() => handleRegenerateBulkSection(slide.slide_number)}
                                    className="p-1.5 text-muted hover:text-accent-500 hover:bg-accent-500/10 rounded-lg transition-colors"
                                    title="이미지 다시 생성"
                                  >
                                    <RefreshCw className="w-4 h-4" />
                                  </button>
                                )}
                                <button
                                  onClick={() => handleDeleteSlide(slide.slide_number)}
                                  className="p-1.5 text-muted hover:text-red-500 hover:bg-red-500/10 rounded-lg transition-colors"
                                  title="슬라이드 삭제"
                                >
                                  <Trash2 className="w-4 h-4" />
                                </button>
                              </div>
                            </div>

                            {/* Visual Prompt Preview - Editable */}
                            {(slide.visual_prompt_display || slide.visual_prompt) && (
                              <div className="mb-4 p-3 rounded-lg bg-muted/20 border border-dashed border-muted">
                                {editingSlideNumber === slide.slide_number ? (
                                  <div className="space-y-2">
                                    <p className="text-xs text-muted font-medium">비주얼 프롬프트 편집</p>
                                    <textarea
                                      value={editingPrompt}
                                      onChange={(e) => setEditingPrompt(e.target.value)}
                                      className="w-full p-2 text-xs rounded-lg bg-background border border-default focus:border-accent-500 focus:ring-1 focus:ring-accent-500 resize-none"
                                      rows={3}
                                      autoFocus
                                    />
                                    <div className="flex gap-2 justify-end">
                                      <button
                                        onClick={handleCancelEdit}
                                        className="px-2 py-1 text-xs text-muted hover:text-foreground"
                                      >
                                        취소
                                      </button>
                                      <button
                                        onClick={handleSavePrompt}
                                        className="px-2 py-1 text-xs bg-accent-500 text-white rounded hover:bg-accent-600"
                                      >
                                        저장
                                      </button>
                                    </div>
                                  </div>
                                ) : (
                                  <div
                                    className="group cursor-pointer"
                                    onDoubleClick={() => handleStartEditPrompt(
                                      slide.slide_number,
                                      slide.visual_prompt_display || slide.visual_prompt || ""
                                    )}
                                  >
                                    <div className="flex items-start justify-between gap-2">
                                      <div className="flex-1">
                                        <p className="text-xs text-muted font-medium mb-1">비주얼 프롬프트</p>
                                        <p className="text-xs text-foreground/70 line-clamp-2">
                                          {slide.visual_prompt_display || slide.visual_prompt}
                                        </p>
                                      </div>
                                      <button
                                        onClick={() => handleStartEditPrompt(
                                          slide.slide_number,
                                          slide.visual_prompt_display || slide.visual_prompt || ""
                                        )}
                                        className="opacity-0 group-hover:opacity-100 transition-opacity p-1 hover:bg-muted/30 rounded flex-shrink-0"
                                        title="비주얼 프롬프트 편집"
                                      >
                                        <Edit3 className="w-3 h-3 text-muted" />
                                      </button>
                                    </div>
                                    <p className="text-[10px] text-muted/60 mt-1">더블클릭하여 편집</p>
                                  </div>
                                )}
                              </div>
                            )}

                            {/* Image Grid */}
                            <div className="grid grid-cols-2 gap-3">
                              {isGenerating || isRegeneratingThis ? (
                                // Loading placeholders
                                Array.from({ length: 2 }).map((_, i) => (
                                  <div
                                    key={i}
                                    className="aspect-square rounded-xl bg-muted/30 border border-default flex items-center justify-center animate-pulse"
                                  >
                                    <Loader2 className="w-6 h-6 animate-spin text-accent-500" />
                                  </div>
                                ))
                              ) : isPending ? (
                                // Waiting placeholders
                                Array.from({ length: 2 }).map((_, i) => (
                                  <div
                                    key={i}
                                    className="aspect-square rounded-xl bg-muted/20 border border-dashed border-muted flex items-center justify-center"
                                  >
                                    <ImageIcon className="w-6 h-6 text-muted" />
                                  </div>
                                ))
                              ) : images.length > 0 ? (
                                // Generated images
                                images.map((img, i) => (
                                  <button
                                    key={i}
                                    onClick={() => setPreviewImage({ url: img, slideNumber: slide.slide_number, variantIndex: i })}
                                    className={`aspect-square rounded-xl overflow-hidden relative border-2 transition-all duration-300 group ${
                                      selectedIndex === i
                                        ? "border-accent-500 shadow-glow-sm ring-2 ring-accent-500/30"
                                        : "border-default hover:border-muted"
                                    }`}
                                  >
                                    {/* eslint-disable-next-line @next/next/no-img-element */}
                                    <img
                                      src={img}
                                      alt={`Generated image ${i + 1} for slide ${slide.slide_number}`}
                                      className="w-full h-full object-cover"
                                      onError={(e) => {
                                        const target = e.target as HTMLImageElement;
                                        target.style.display = 'none';
                                        target.nextElementSibling?.classList.remove('hidden');
                                      }}
                                    />
                                    <div className="hidden w-full h-full bg-muted flex items-center justify-center absolute inset-0">
                                      <ImageIcon className="w-8 h-8 text-muted" />
                                    </div>
                                    {/* Hover overlay with zoom icon */}
                                    <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                                      <ZoomIn className="w-6 h-6 text-white" />
                                    </div>
                                    {selectedIndex === i && (
                                      <div className="absolute top-2 right-2 w-6 h-6 bg-accent-500 rounded-full flex items-center justify-center shadow-lg z-10">
                                        <Check className="w-4 h-4 text-white" />
                                      </div>
                                    )}
                                    <div className="absolute bottom-2 left-2 z-10">
                                      <span className="px-1.5 py-0.5 text-[10px] font-medium bg-black/60 text-white rounded">
                                        {i + 1}
                                      </span>
                                    </div>
                                  </button>
                                ))
                              ) : null}
                            </div>
                          </div>
                        );
                      })}
                    </div>

                    {/* Actions */}
                    <div className="flex gap-4">
                      <button
                        onClick={() => {
                          // Reset and go back to storyboard
                          setSectionImages({});
                          setSelectedSectionImages({});
                          setCurrentGeneratingSection(null);
                          setGenerationProgress({ current: 0, total: 0 });
                          setStep(4);
                        }}
                        disabled={currentGeneratingSection !== null || isRegenerating !== null}
                        className="btn-secondary flex-1 flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        <RefreshCw className="w-4 h-4" />
                        스토리보드 수정
                      </button>
                      <button
                        onClick={handleProceedToEditWithSections}
                        disabled={!allSectionsSelected || currentGeneratingSection !== null || isRegenerating !== null}
                        className="btn-primary flex-1 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                      >
                        {currentGeneratingSection !== null || isRegenerating !== null ? (
                          <>
                            <Loader2 className="w-4 h-4 animate-spin" />
                            생성 중...
                          </>
                        ) : (
                          <>
                            편집하기 <ArrowRight className="w-4 h-4" />
                          </>
                        )}
                      </button>
                    </div>
                  </>
                )}
              </>
            )}
          </div>
        )}

        {/* Navigation */}
        {step > 1 && step < 5 && (
          <div className="mt-8 pt-6 border-t border-default">
            <button
              onClick={handleBack}
              className="btn-ghost flex items-center gap-2"
            >
              <ChevronLeft className="w-4 h-4" />
              이전으로
            </button>
          </div>
        )}
      </div>

      {/* Image Preview Modal */}
      {previewImage && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm"
          onClick={() => setPreviewImage(null)}
        >
          <div
            className="relative max-w-4xl max-h-[90vh] w-full mx-4"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Close button */}
            <button
              onClick={() => setPreviewImage(null)}
              className="absolute -top-12 right-0 p-2 text-white/70 hover:text-white transition-colors"
            >
              <X className="w-6 h-6" />
            </button>

            {/* Image */}
            <div className="bg-card rounded-2xl overflow-hidden shadow-2xl">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={previewImage.url}
                alt={`Preview image ${previewImage.variantIndex + 1} for slide ${previewImage.slideNumber}`}
                className="w-full h-auto max-h-[70vh] object-contain bg-black"
              />

              {/* Actions */}
              <div className="p-4 flex items-center justify-between border-t border-default">
                <div className="text-sm text-muted">
                  슬라이드 {previewImage.slideNumber} - 변형 {previewImage.variantIndex + 1}
                </div>
                <div className="flex gap-3">
                  <button
                    onClick={() => setPreviewImage(null)}
                    className="btn-secondary px-4 py-2"
                  >
                    닫기
                  </button>
                  <button
                    onClick={() => {
                      handleSelectSectionImage(previewImage.slideNumber, previewImage.variantIndex);
                      setPreviewImage(null);
                      toast.success(`슬라이드 ${previewImage.slideNumber}의 이미지가 선택되었습니다`);
                    }}
                    className="btn-primary px-4 py-2 flex items-center gap-2"
                  >
                    <Check className="w-4 h-4" />
                    이 이미지 선택
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function CreatePage() {
  return (
    <Suspense
      fallback={
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-8 h-8 animate-spin text-accent-500" />
        </div>
      }
    >
      <CreatePageContent />
    </Suspense>
  );
}
