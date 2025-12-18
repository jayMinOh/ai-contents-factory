"use client";

import { useState, useEffect, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  ChevronLeft,
  ChevronRight,
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
} from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { brandApi } from "@/lib/api";
import { toast } from "sonner";

// Content types
type ContentType = "single" | "carousel" | "story";
type Purpose = "ad" | "info" | "lifestyle";
type GenerationMethod = "reference" | "prompt";

interface ContentConfig {
  type: ContentType;
  purpose: Purpose;
  brandId?: string;
  productId?: string;
  method: GenerationMethod;
  referenceId?: string;
  prompt?: string;
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
    label: "스토리",
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
  const [config, setConfig] = useState<ContentConfig>({
    type: (searchParams.get("type") as ContentType) || "single",
    purpose: "ad",
    method: "prompt",
  });

  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedImages, setGeneratedImages] = useState<string[]>([]);
  const [selectedImageIndex, setSelectedImageIndex] = useState<number | null>(null);

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

  const selectedBrand = brands.find((b) => b.id === config.brandId);
  const products = selectedBrandDetails?.products || [];

  // Update type from URL params
  useEffect(() => {
    const typeParam = searchParams.get("type") as ContentType;
    if (typeParam && ["single", "carousel", "story"].includes(typeParam)) {
      setConfig((prev) => ({ ...prev, type: typeParam }));
    }
  }, [searchParams]);

  const handleNext = () => {
    if (step < 6) setStep(step + 1);
  };

  const handleBack = () => {
    if (step > 1) setStep(step - 1);
  };

  const handleGenerate = async () => {
    setIsGenerating(true);
    toast.info("AI가 이미지를 생성하고 있습니다...");

    await new Promise((resolve) => setTimeout(resolve, 3000));

    setGeneratedImages([
      "/placeholder-1.jpg",
      "/placeholder-2.jpg",
      "/placeholder-3.jpg",
      "/placeholder-4.jpg",
    ]);

    setIsGenerating(false);
    toast.success("이미지 생성이 완료되었습니다!");
    setStep(5);
  };

  const handleSelectImage = (index: number) => {
    setSelectedImageIndex(index);
  };

  const handleProceedToEdit = () => {
    if (selectedImageIndex !== null) {
      router.push(`/create/edit/temp-${selectedImageIndex}`);
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
                    setConfig((prev) => ({ ...prev, type: item.type }));
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
                    if (item.purpose !== "ad") {
                      handleNext();
                    }
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
          </div>
        )}

        {/* Step 3: Generation Method */}
        {step === 3 && (
          <div className="space-y-8">
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

            {/* Reference Selection */}
            {config.method === "reference" && (
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
              </div>
            )}

            {/* Prompt Input */}
            {config.method === "prompt" && (
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

        {/* Step 4: Generate */}
        {step === 4 && (
          <div className="space-y-8">
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
                  {config.type === "single" && "단일 이미지"}
                  {config.type === "carousel" && "캐러셀"}
                  {config.type === "story" && "스토리"}
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
              onClick={handleGenerate}
              disabled={isGenerating}
              className="btn-primary w-full py-4 text-base disabled:opacity-50 flex items-center justify-center gap-3"
            >
              {isGenerating ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  생성 중...
                </>
              ) : (
                <>
                  <Wand2 className="w-5 h-5" />
                  이미지 생성하기
                </>
              )}
            </button>
          </div>
        )}

        {/* Step 5: Select Generated Image */}
        {step === 5 && (
          <div className="space-y-8">
            <div className="text-center">
              <h2 className="font-display text-2xl font-bold text-foreground mb-2">
                이미지 선택
              </h2>
              <p className="text-muted">마음에 드는 이미지를 선택하세요</p>
            </div>

            <div className="grid grid-cols-2 gap-4">
              {generatedImages.length > 0 ? (
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
                    <div className="w-full h-full bg-muted flex items-center justify-center">
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
                onClick={() => setStep(4)}
                className="btn-secondary flex-1 flex items-center justify-center gap-2"
              >
                <RefreshCw className="w-4 h-4" />
                다시 생성
              </button>
              <button
                onClick={handleProceedToEdit}
                disabled={selectedImageIndex === null}
                className="btn-primary flex-1 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                편집하기 <ArrowRight className="w-4 h-4 ml-2 inline" />
              </button>
            </div>
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
