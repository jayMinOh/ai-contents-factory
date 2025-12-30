"use client";

import { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { useRouter, useParams } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  Clock,
  Image as ImageIcon,
  Layers,
  Smartphone,
  Megaphone,
  BookOpen,
  Sparkles,
  Loader2,
  AlertCircle,
  RefreshCw,
  Download,
  ExternalLink,
  ChevronLeft,
  ChevronRight,
  Trash2,
} from "lucide-react";
import { imageProjectApi, type ImageProject, type GeneratedImage } from "@/lib/api";
import { toast } from "sonner";
import { formatDistanceToNow } from "date-fns";
import { ko, enUS } from "date-fns/locale";

// i18n translations
const translations = {
  ko: {
    contentType: {
      single: "단일 이미지",
      carousel: "캐러셀",
      story: "세로형",
    },
    purpose: {
      ad: "광고/홍보",
      info: "정보성",
      lifestyle: "일상/감성",
    },
    status: {
      draft: "준비 중",
      generating: "생성 중",
      completed: "완료",
      failed: "실패",
    },
    ui: {
      untitled: "제목 없음",
      projectNotFound: "프로젝트를 찾을 수 없습니다",
      backToHistory: "히스토리로 돌아가기",
      refresh: "새로고침",
      downloadStarted: "다운로드가 시작되었습니다",
      downloadFailed: "다운로드에 실패했습니다",
      noImagesYet: "아직 생성된 이미지가 없습니다",
      imagesWillAppear: "이미지 생성이 완료되면 여기에 표시됩니다",
      generatingImages: "이미지 생성 중...",
      processingSlide: "슬라이드 {current}/{total} 처리 중",
      pleaseWait: "AI가 이미지를 생성하고 있습니다. 잠시만 기다려주세요.",
      storyboardSlides: "스토리보드 슬라이드",
      visualPrompt: "비주얼 프롬프트",
      generatedImages: "생성된 이미지",
      slide: "슬라이드",
      waitingGeneration: "생성 대기 중...",
      generating: "생성 중...",
      noImagesForSlide: "이 슬라이드에 이미지가 없습니다",
      variant: "변형",
      selected: "선택됨",
      allGeneratedImages: "전체 생성 이미지",
      projectDetails: "프로젝트 상세",
      contentTypeLabel: "콘텐츠 유형",
      purposeLabel: "목적",
      methodLabel: "방식",
      reference: "레퍼런스",
      prompt: "프롬프트",
      aspectRatio: "비율",
      totalSlides: "전체 슬라이드",
      imagesGenerated: "생성된 이미지 수",
      created: "생성일",
      statusLabel: "상태",
      mainPrompt: "메인 프롬프트",
      retryGeneration: "다시 생성",
      retryStarted: "이미지 생성이 다시 시작되었습니다",
      retryFailed: "다시 생성에 실패했습니다",
      generationStopped: "생성이 중단되었거나 오류가 발생했습니다",
      deleteProject: "삭제",
      deleteConfirm: "이 프로젝트를 삭제하시겠습니까?",
      deleteSuccess: "프로젝트가 삭제되었습니다",
      deleteFailed: "삭제에 실패했습니다",
    },
  },
  en: {
    contentType: {
      single: "Single Image",
      carousel: "Carousel",
      story: "Story",
    },
    purpose: {
      ad: "Ad/Promo",
      info: "Information",
      lifestyle: "Lifestyle",
    },
    status: {
      draft: "Preparing",
      generating: "Generating",
      completed: "Completed",
      failed: "Failed",
    },
    ui: {
      untitled: "Untitled",
      projectNotFound: "Project not found",
      backToHistory: "Back to History",
      refresh: "Refresh",
      downloadStarted: "Download started",
      downloadFailed: "Download failed",
      noImagesYet: "No images generated yet",
      imagesWillAppear: "Images will appear here once generation is complete",
      generatingImages: "Generating images...",
      processingSlide: "Processing slide {current}/{total}",
      pleaseWait: "Please wait while AI generates your images.",
      storyboardSlides: "Storyboard Slides",
      visualPrompt: "Visual Prompt",
      generatedImages: "Generated Images",
      slide: "Slide",
      waitingGeneration: "Waiting for generation...",
      generating: "Generating...",
      noImagesForSlide: "No images for this slide",
      variant: "Variant",
      selected: "Selected",
      allGeneratedImages: "All Generated Images",
      projectDetails: "Project Details",
      contentTypeLabel: "Content Type",
      purposeLabel: "Purpose",
      methodLabel: "Method",
      reference: "Reference",
      prompt: "Prompt",
      aspectRatio: "Aspect Ratio",
      totalSlides: "Total Slides",
      imagesGenerated: "Images Generated",
      created: "Created",
      statusLabel: "Status",
      mainPrompt: "Main Prompt",
      retryGeneration: "Retry Generation",
      retryStarted: "Image generation restarted",
      retryFailed: "Failed to retry generation",
      generationStopped: "Generation stopped or encountered an error",
      deleteProject: "Delete",
      deleteConfirm: "Are you sure you want to delete this project?",
      deleteSuccess: "Project deleted",
      deleteFailed: "Failed to delete project",
    },
  },
};

type Lang = "ko" | "en";

function getLocale(lang: Lang) {
  return lang === "ko" ? ko : enUS;
}

export default function HistoryDetailPage() {
  const router = useRouter();
  const params = useParams();
  const projectId = params.id as string;
  const [selectedSlide, setSelectedSlide] = useState<number>(1);
  const [lang, setLang] = useState<Lang>("ko");
  const [isRetrying, setIsRetrying] = useState(false);

  // Detect browser language
  useEffect(() => {
    const browserLang = navigator.language.toLowerCase();
    if (browserLang.startsWith("ko")) {
      setLang("ko");
    } else {
      setLang("en");
    }
  }, []);

  const t = translations[lang];

  // Fetch project details with polling for generating projects
  const { data: project, isLoading, error, refetch } = useQuery({
    queryKey: ["imageProject", projectId],
    queryFn: () => imageProjectApi.get(projectId),
    refetchInterval: (query) => {
      const data = query.state.data;
      return data?.status === "generating" ? 3000 : false;
    },
  });

  // Format date (backend sends UTC, append Z to parse correctly)
  const formatDate = (dateString?: string) => {
    if (!dateString) return "";
    try {
      // Append 'Z' if not present to indicate UTC
      const utcDateString = dateString.endsWith('Z') ? dateString : dateString + 'Z';
      return formatDistanceToNow(new Date(utcDateString), { addSuffix: true, locale: getLocale(lang) });
    } catch {
      return dateString;
    }
  };

  // Group images by slide
  const getImagesBySlide = (slideNumber: number): GeneratedImage[] => {
    return project?.generated_images?.filter((img) => img.slide_number === slideNumber) || [];
  };

  // Get all unique slide numbers
  const getSlideNumbers = (): number[] => {
    if (!project?.generated_images) return [];
    const slides = Array.from(new Set(project.generated_images.map((img) => img.slide_number)));
    return slides.sort((a, b) => a - b);
  };

  // Download image with project aspect ratio
  const handleDownload = async (imageId: string) => {
    try {
      await imageProjectApi.downloadImage(imageId);
      toast.success(t.ui.downloadStarted);
    } catch (error) {
      console.error("Download failed:", error);
      toast.error(t.ui.downloadFailed);
    }
  };

  // Retry generation
  const handleRetryGeneration = async () => {
    if (!project) return;

    setIsRetrying(true);
    try {
      await imageProjectApi.startBackgroundGeneration(project.id);
      toast.success(t.ui.retryStarted);
      refetch();
    } catch (error) {
      console.error("Retry failed:", error);
      toast.error(t.ui.retryFailed);
    } finally {
      setIsRetrying(false);
    }
  };

  // Delete project
  const handleDeleteProject = async () => {
    if (!project) return;

    if (!confirm(t.ui.deleteConfirm)) return;

    try {
      await imageProjectApi.delete(project.id);
      toast.success(t.ui.deleteSuccess);
      router.push("/history");
    } catch (error) {
      console.error("Delete failed:", error);
      toast.error(t.ui.deleteFailed);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-accent-500" />
      </div>
    );
  }

  if (error || !project) {
    return (
      <div className="min-h-screen bg-background flex flex-col items-center justify-center gap-4">
        <AlertCircle className="w-12 h-12 text-red-500" />
        <p className="text-foreground font-medium">{t.ui.projectNotFound}</p>
        <Link href="/history" className="btn-secondary">
          {t.ui.backToHistory}
        </Link>
      </div>
    );
  }

  const contentTypeLabels = {
    single: { label: t.contentType.single, icon: ImageIcon, gradient: "from-accent-500 to-accent-600" },
    carousel: { label: t.contentType.carousel, icon: Layers, gradient: "from-violet-500 to-purple-600" },
    story: { label: t.contentType.story, icon: Smartphone, gradient: "from-cyan-500 to-blue-600" },
  };

  const purposeLabels = {
    ad: { label: t.purpose.ad, icon: Megaphone },
    info: { label: t.purpose.info, icon: BookOpen },
    lifestyle: { label: t.purpose.lifestyle, icon: Sparkles },
  };

  const statusLabels: Record<string, { label: string; color: string; bgColor: string }> = {
    draft: { label: t.status.draft, color: "text-slate-500", bgColor: "bg-slate-500/10" },
    generating: { label: t.status.generating, color: "text-amber-500", bgColor: "bg-amber-500/10" },
    completed: { label: t.status.completed, color: "text-emerald-500", bgColor: "bg-emerald-500/10" },
    failed: { label: t.status.failed, color: "text-red-500", bgColor: "bg-red-500/10" },
  };

  const contentType = contentTypeLabels[project.content_type];
  const purpose = purposeLabels[project.purpose];
  const status = statusLabels[project.status] || statusLabels.draft;
  const ContentIcon = contentType.icon;
  const PurposeIcon = purpose.icon;
  const slides = project.storyboard_data?.slides || [];
  const slideNumbers = getSlideNumbers();
  const currentSlideData = slides.find((s) => s.slide_number === selectedSlide);
  const currentSlideImages = getImagesBySlide(selectedSlide);

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <div className="border-b border-default bg-card/50 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button
                onClick={() => router.push("/history")}
                className="p-2 hover:bg-muted rounded-lg transition-colors"
              >
                <ArrowLeft className="w-5 h-5 text-muted" />
              </button>
              <div>
                <h1 className="text-xl font-bold text-foreground">
                  {project.title || t.ui.untitled}
                </h1>
                <div className="flex items-center gap-3 mt-1 text-sm text-muted">
                  <div className="flex items-center gap-1">
                    <ContentIcon className="w-4 h-4" />
                    <span>{contentType.label}</span>
                  </div>
                  <span className="text-border">|</span>
                  <div className="flex items-center gap-1">
                    <PurposeIcon className="w-4 h-4" />
                    <span>{purpose.label}</span>
                  </div>
                  <span className="text-border">|</span>
                  <span>{formatDate(project.created_at)}</span>
                </div>
              </div>
            </div>
            <div className="flex items-center gap-3">
              {/* Status Badge */}
              <div className={`px-3 py-1.5 rounded-lg text-sm font-medium ${status.bgColor} ${status.color} flex items-center gap-2`}>
                {project.status === "generating" && (
                  <Loader2 className="w-4 h-4 animate-spin" />
                )}
                {status.label}
                {project.status === "generating" && project.current_slide && slides.length > 0 && (
                  <span>({project.current_slide}/{slides.length})</span>
                )}
              </div>
              <button
                onClick={handleRetryGeneration}
                disabled={isRetrying || project.status === "generating"}
                className="flex items-center gap-2 px-3 py-2 hover:bg-muted rounded-lg transition-colors disabled:opacity-50"
                title={t.ui.retryGeneration}
              >
                {isRetrying ? (
                  <Loader2 className="w-4 h-4 animate-spin text-muted" />
                ) : (
                  <RefreshCw className="w-4 h-4 text-muted" />
                )}
                <span className="text-sm text-muted">{t.ui.retryGeneration}</span>
              </button>
              <button
                onClick={handleDeleteProject}
                className="flex items-center gap-2 px-3 py-2 hover:bg-red-500/10 rounded-lg transition-colors text-muted hover:text-red-500"
                title={t.ui.deleteProject}
              >
                <Trash2 className="w-4 h-4" />
                <span className="text-sm">{t.ui.deleteProject}</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Progress Bar for Generating */}
      {project.status === "generating" && slides.length > 0 && (
        <div className="h-1 bg-muted">
          <div
            className="h-full bg-accent-500 transition-all duration-500"
            style={{
              width: `${((project.current_slide || 0) / slides.length) * 100}%`
            }}
          />
        </div>
      )}

      {/* Main Content */}
      <div className="max-w-6xl mx-auto px-6 py-8">
        {/* No Images Yet */}
        {(project.generated_images?.length ?? 0) === 0 && project.status !== "generating" && (
          <div className="text-center py-16 bg-card border border-default rounded-2xl">
            <ImageIcon className="w-16 h-16 text-muted mx-auto mb-4" />
            <p className="text-foreground font-medium mb-2">{t.ui.noImagesYet}</p>
            <p className="text-muted text-sm mb-6">{t.ui.imagesWillAppear}</p>

            {/* Always show Retry Button */}
            {slides.length > 0 && (
              <button
                onClick={handleRetryGeneration}
                disabled={isRetrying}
                className="btn-primary flex items-center gap-2 mx-auto"
              >
                {isRetrying ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <RefreshCw className="w-4 h-4" />
                )}
                {t.ui.retryGeneration}
              </button>
            )}
          </div>
        )}

        {/* Generating State */}
        {project.status === "generating" && (project.generated_images?.length ?? 0) === 0 && (
          <div className="text-center py-16 bg-card border border-default rounded-2xl">
            <Loader2 className="w-16 h-16 text-accent-500 animate-spin mx-auto mb-4" />
            <p className="text-foreground font-medium mb-2">{t.ui.generatingImages}</p>
            <p className="text-muted text-sm mb-6">
              {project.current_slide && slides.length > 0
                ? t.ui.processingSlide.replace("{current}", String(project.current_slide)).replace("{total}", String(slides.length))
                : t.ui.pleaseWait}
            </p>

            {/* Always show Retry button */}
            <button
              onClick={handleRetryGeneration}
              disabled={isRetrying}
              className="btn-secondary flex items-center gap-2 mx-auto"
            >
              {isRetrying ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <RefreshCw className="w-4 h-4" />
              )}
              {t.ui.retryGeneration}
            </button>
          </div>
        )}

        {/* Images Gallery */}
        {((project.generated_images?.length ?? 0) > 0 || (project.status === "generating" && slideNumbers.length > 0)) && (
          <div className="space-y-6">
            {/* Slide Navigation (for carousel/story) */}
            {slides.length > 1 && (
              <div className="bg-card border border-default rounded-2xl p-4">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="font-semibold text-foreground">{t.ui.storyboardSlides}</h2>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => setSelectedSlide((prev) => Math.max(1, prev - 1))}
                      disabled={selectedSlide === 1}
                      className="p-1.5 rounded-lg hover:bg-muted disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                      <ChevronLeft className="w-5 h-5" />
                    </button>
                    <span className="text-sm font-medium px-3">
                      {selectedSlide} / {slides.length}
                    </span>
                    <button
                      onClick={() => setSelectedSlide((prev) => Math.min(slides.length, prev + 1))}
                      disabled={selectedSlide === slides.length}
                      className="p-1.5 rounded-lg hover:bg-muted disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                      <ChevronRight className="w-5 h-5" />
                    </button>
                  </div>
                </div>

                {/* Slide Thumbnails */}
                <div className="flex gap-2 overflow-x-auto pb-2">
                  {slides.map((slide) => {
                    const slideImages = getImagesBySlide(slide.slide_number);
                    const isSelected = selectedSlide === slide.slide_number;
                    const hasImages = slideImages.length > 0;

                    return (
                      <button
                        key={slide.slide_number}
                        onClick={() => setSelectedSlide(slide.slide_number)}
                        className={`flex-shrink-0 w-24 h-16 rounded-lg border-2 overflow-hidden transition-all ${
                          isSelected
                            ? "border-accent-500 ring-2 ring-accent-500/20"
                            : "border-default hover:border-accent-500/50"
                        }`}
                      >
                        {hasImages ? (
                          <img
                            src={slideImages[0].image_url.startsWith('http') ? slideImages[0].image_url : `http://localhost:8000${slideImages[0].image_url}`}
                            alt={`${t.ui.slide} ${slide.slide_number}`}
                            className="w-full h-full object-cover"
                          />
                        ) : (
                          <div className="w-full h-full bg-muted/50 flex items-center justify-center">
                            {project.status === "generating" && project.current_slide === slide.slide_number ? (
                              <Loader2 className="w-4 h-4 animate-spin text-accent-500" />
                            ) : (
                              <span className="text-xs text-muted">{slide.slide_number}</span>
                            )}
                          </div>
                        )}
                      </button>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Current Slide Info */}
            {currentSlideData && (
              <div className="bg-card border border-default rounded-2xl p-6">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <span className="text-xs font-medium text-accent-500 uppercase tracking-wide">
                      {currentSlideData.section_type}
                    </span>
                    <h3 className="text-lg font-semibold text-foreground mt-1">
                      {currentSlideData.title}
                    </h3>
                  </div>
                </div>

                {currentSlideData.description && (
                  <p className="text-muted text-sm mb-4">{currentSlideData.description}</p>
                )}

                {(currentSlideData.visual_prompt_display || currentSlideData.visual_prompt) && (
                  <div className="bg-muted/30 rounded-lg p-3 text-sm">
                    <span className="text-xs font-medium text-muted uppercase tracking-wide block mb-1">
                      {t.ui.visualPrompt}
                    </span>
                    <p className="text-foreground">{currentSlideData.visual_prompt_display || currentSlideData.visual_prompt}</p>
                  </div>
                )}
              </div>
            )}

            {/* Generated Images for Current Slide */}
            <div className="bg-card border border-default rounded-2xl p-6">
              <h3 className="font-semibold text-foreground mb-4">
                {t.ui.generatedImages}
                {slides.length > 1 && ` - ${t.ui.slide} ${selectedSlide}`}
              </h3>

              {currentSlideImages.length === 0 ? (
                <div className="text-center py-8">
                  {project.status === "generating" && (project.current_slide || 0) < selectedSlide ? (
                    <>
                      <Clock className="w-8 h-8 text-muted mx-auto mb-2" />
                      <p className="text-muted text-sm">{t.ui.waitingGeneration}</p>
                    </>
                  ) : project.status === "generating" && project.current_slide === selectedSlide ? (
                    <>
                      <Loader2 className="w-8 h-8 text-accent-500 animate-spin mx-auto mb-2" />
                      <p className="text-muted text-sm">{t.ui.generating}</p>
                    </>
                  ) : (
                    <>
                      <ImageIcon className="w-8 h-8 text-muted mx-auto mb-2" />
                      <p className="text-muted text-sm">{t.ui.noImagesForSlide}</p>
                    </>
                  )}
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {currentSlideImages.map((image, index) => (
                    <div
                      key={image.id}
                      className="group relative aspect-square rounded-xl overflow-hidden border border-default"
                    >
                      <img
                        src={image.image_url.startsWith('http') ? image.image_url : `http://localhost:8000${image.image_url}`}
                        alt={`Generated ${index + 1}`}
                        className="w-full h-full object-cover"
                      />

                      {/* Overlay Actions */}
                      <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-3">
                        <button
                          onClick={() => handleDownload(image.id)}
                          className="p-3 bg-white/20 rounded-full hover:bg-white/30 transition-colors"
                          title="Download"
                        >
                          <Download className="w-5 h-5 text-white" />
                        </button>
                        <a
                          href={image.image_url.startsWith('http') ? image.image_url : `http://localhost:8000${image.image_url}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="p-3 bg-white/20 rounded-full hover:bg-white/30 transition-colors"
                          title="Open in new tab"
                        >
                          <ExternalLink className="w-5 h-5 text-white" />
                        </a>
                      </div>

                      {/* Variant Badge */}
                      <div className="absolute top-2 left-2 px-2 py-1 bg-black/50 rounded text-xs text-white font-medium">
                        {t.ui.variant} {image.variant_index + 1}
                      </div>

                      {/* Selected Badge */}
                      {image.is_selected && (
                        <div className="absolute top-2 right-2 px-2 py-1 bg-accent-500 rounded text-xs text-white font-medium">
                          {t.ui.selected}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* All Images (Single view for single image type) */}
            {slides.length <= 1 && project.generated_images && project.generated_images.length > currentSlideImages.length && (
              <div className="bg-card border border-default rounded-2xl p-6">
                <h3 className="font-semibold text-foreground mb-4">{t.ui.allGeneratedImages}</h3>
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                  {project.generated_images.map((image, index) => (
                    <div
                      key={image.id}
                      className="group relative aspect-square rounded-xl overflow-hidden border border-default"
                    >
                      <img
                        src={image.image_url.startsWith('http') ? image.image_url : `http://localhost:8000${image.image_url}`}
                        alt={`Generated ${index + 1}`}
                        className="w-full h-full object-cover"
                      />
                      <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                        <button
                          onClick={() => handleDownload(image.id)}
                          className="p-2 bg-white/20 rounded-full hover:bg-white/30 transition-colors"
                        >
                          <Download className="w-4 h-4 text-white" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Project Info */}
        <div className="mt-8 bg-card border border-default rounded-2xl p-6">
          <h3 className="font-semibold text-foreground mb-4">{t.ui.projectDetails}</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <span className="text-muted block mb-1">{t.ui.contentTypeLabel}</span>
              <span className="text-foreground font-medium">{contentType.label}</span>
            </div>
            <div>
              <span className="text-muted block mb-1">{t.ui.purposeLabel}</span>
              <span className="text-foreground font-medium">{purpose.label}</span>
            </div>
            <div>
              <span className="text-muted block mb-1">{t.ui.methodLabel}</span>
              <span className="text-foreground font-medium">
                {project.method === "reference" ? t.ui.reference : t.ui.prompt}
              </span>
            </div>
            <div>
              <span className="text-muted block mb-1">{t.ui.aspectRatio}</span>
              <span className="text-foreground font-medium">{project.aspect_ratio}</span>
            </div>
            <div>
              <span className="text-muted block mb-1">{t.ui.totalSlides}</span>
              <span className="text-foreground font-medium">{slides.length || 1}</span>
            </div>
            <div>
              <span className="text-muted block mb-1">{t.ui.imagesGenerated}</span>
              <span className="text-foreground font-medium">{project.generated_images?.length || 0}</span>
            </div>
            <div>
              <span className="text-muted block mb-1">{t.ui.created}</span>
              <span className="text-foreground font-medium">{formatDate(project.created_at)}</span>
            </div>
            <div>
              <span className="text-muted block mb-1">{t.ui.statusLabel}</span>
              <span className={`font-medium ${status.color}`}>{status.label}</span>
            </div>
          </div>

          {(project.storyboard_data?.slides?.[0]?.visual_prompt_display || project.prompt) && (
            <div className="mt-4 pt-4 border-t border-default">
              <span className="text-muted block mb-1 text-sm">{t.ui.mainPrompt}</span>
              <p className="text-foreground text-sm">
                {project.storyboard_data?.slides?.[0]?.visual_prompt_display || project.prompt}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
