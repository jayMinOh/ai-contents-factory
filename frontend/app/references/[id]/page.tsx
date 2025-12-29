"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import Image from "next/image";
import {
  ArrowLeft,
  ExternalLink,
  Zap,
  Target,
  Heart,
  AlertTriangle,
  TrendingUp,
  Megaphone,
  Lightbulb,
  BarChart3,
  Layers,
  RefreshCw,
  CheckCircle2,
  Clock,
  AlertCircle,
  ChevronRight,
  Sparkles,
  Image as ImageIcon,
  Trash2,
  Pencil,
  Check,
  X,
  Trophy,
} from "lucide-react";
import { toast } from "sonner";
import {
  referenceApi,
  AnalysisResult,
  HookPoint,
  EdgePoint,
  EmotionalTrigger,
  PainPoint,
  SellingPoint,
  CTAAnalysis,
  StructurePattern,
  Recommendation,
  TimelineSegment,
  OverallEvaluation,
} from "@/lib/api";

// Score breakdown item type
interface ScoreBreakdownItem {
  score: number;
  weight: string;
  reason: string;
}

interface ScoreBreakdown {
  [key: string]: ScoreBreakdownItem;
}

// Criterion name translation
const criterionLabels: Record<string, string> = {
  visual_impact: "시각적 임팩트",
  info_density: "정보 밀도",
  info_delivery: "정보 전달력",
  emotional_appeal: "감정적 호소",
  retention_power: "시청 유지력",
  scroll_stopping: "스크롤 스토핑",
  attention_grab: "주목도",
  curiosity_trigger: "궁금증 유발",
  memorability: "기억성",
  reusability: "재활용성",
  uniqueness: "독창성",
  brand_fit: "브랜드 적합성",
  scalability: "확장 가능성",
  emotional_depth: "감정 자극 깊이",
  trigger_clarity: "트리거 명확성",
  action_motivation: "행동 유도",
  claim_credibility: "주장 신뢰성",
  evidence_strength: "근거 설득력",
  conversion_potential: "전환 가능성",
  clarity: "명확성",
  urgency: "긴급성",
  barrier_removal: "장벽 제거",
  visual_prominence: "시각적 강조",
};

// Score indicator component with breakdown support
function ScoreBar({
  score,
  label,
  color,
  reasoning,
  scoreBreakdown,
  totalReason
}: {
  score: number;
  label: string;
  color: string;
  reasoning?: string;
  scoreBreakdown?: ScoreBreakdown;
  totalReason?: string;
}) {
  const percentage = Math.round(score * 100);
  const [showDetails, setShowDetails] = useState(false);

  // Get color classes for breakdown items
  const getBreakdownColor = (itemScore: number) => {
    if (itemScore >= 0.8) return 'text-emerald-600 dark:text-emerald-400';
    if (itemScore >= 0.6) return 'text-amber-600 dark:text-amber-400';
    return 'text-rose-600 dark:text-rose-400';
  };

  const getBreakdownBg = (itemScore: number) => {
    if (itemScore >= 0.8) return 'bg-emerald-500';
    if (itemScore >= 0.6) return 'bg-amber-500';
    return 'bg-rose-500';
  };

  return (
    <div className="space-y-1.5">
      <div className="flex justify-between items-center">
        <span className="text-xs font-medium text-gray-500 dark:text-gray-400">{label}</span>
        <div className="flex items-center gap-2">
          <span className={`text-xs font-bold ${color}`}>{percentage}%</span>
          {scoreBreakdown && Object.keys(scoreBreakdown).length > 0 && (
            <button
              onClick={() => setShowDetails(!showDetails)}
              className="text-[10px] px-1.5 py-0.5 rounded bg-gray-100 dark:bg-gray-800 text-blue-500 hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
            >
              {showDetails ? '접기' : '상세'}
            </button>
          )}
        </div>
      </div>
      <div className="h-2 bg-gray-100 dark:bg-gray-800 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-700 ease-out ${color.replace('text-', 'bg-')}`}
          style={{ width: `${percentage}%` }}
        />
      </div>

      {/* Score Breakdown Details */}
      {showDetails && scoreBreakdown && (
        <div className="mt-2 p-3 bg-gray-50 dark:bg-gray-800/50 rounded-lg space-y-2 border border-gray-100 dark:border-gray-700">
          <p className="text-[10px] font-medium text-gray-400 dark:text-gray-500 uppercase tracking-wider mb-2">평가 기준별 점수</p>
          {Object.entries(scoreBreakdown).map(([key, item]) => (
            <div key={key} className="space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-xs text-gray-600 dark:text-gray-300">
                  {criterionLabels[key] || key}
                  <span className="text-gray-400 ml-1">({item.weight})</span>
                </span>
                <span className={`text-xs font-semibold ${getBreakdownColor(item.score)}`}>
                  {Math.round(item.score * 100)}%
                </span>
              </div>
              <div className="h-1 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full ${getBreakdownBg(item.score)}`}
                  style={{ width: `${Math.round(item.score * 100)}%` }}
                />
              </div>
              <p className="text-[11px] text-gray-500 dark:text-gray-400 pl-1">{item.reason}</p>
            </div>
          ))}
        </div>
      )}

      {/* Total Reason (new format) or Reasoning (old format) */}
      {totalReason && (
        <p className="text-xs text-gray-600 dark:text-gray-300 mt-1.5 bg-gradient-to-r from-gray-50 to-transparent dark:from-gray-800/30 dark:to-transparent p-2 rounded border-l-2 border-violet-400">
          {totalReason}
        </p>
      )}
      {!totalReason && reasoning && (
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 italic">
          "{reasoning}"
        </p>
      )}
    </div>
  );
}

// Analysis card component
function AnalysisCard({
  icon: Icon,
  title,
  count,
  children,
  accentColor = "violet",
}: {
  icon: React.ElementType;
  title: string;
  count?: number;
  children: React.ReactNode;
  accentColor?: string;
}) {
  const colorMap: Record<string, string> = {
    violet: "from-violet-500 to-purple-600",
    amber: "from-amber-500 to-orange-600",
    rose: "from-rose-500 to-pink-600",
    emerald: "from-emerald-500 to-teal-600",
    blue: "from-blue-500 to-indigo-600",
    cyan: "from-cyan-500 to-sky-600",
  };

  return (
    <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 overflow-hidden hover:shadow-xl transition-shadow duration-300">
      <div className="p-5 border-b border-gray-100 dark:border-gray-800">
        <div className="flex items-center gap-3">
          <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${colorMap[accentColor]} flex items-center justify-center shadow-lg`}>
            <Icon className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="font-bold text-gray-900 dark:text-white">{title}</h3>
            {count !== undefined && (
              <p className="text-xs text-gray-500 dark:text-gray-400">{count}개 항목</p>
            )}
          </div>
        </div>
      </div>
      <div className="p-5 space-y-4 max-h-[400px] overflow-y-auto">
        {children}
      </div>
    </div>
  );
}

export default function ReferenceDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isReanalyzing, setIsReanalyzing] = useState(false);
  const [activeImageIndex, setActiveImageIndex] = useState(0);
  const [isEditingTitle, setIsEditingTitle] = useState(false);
  const [editedTitle, setEditedTitle] = useState("");
  const [isSavingTitle, setIsSavingTitle] = useState(false);
  const [isTimelineOpen, setIsTimelineOpen] = useState(false);
  const [expandedCriteria, setExpandedCriteria] = useState<string | null>(null);

  const analysisId = params.id as string;

  // Prevent body scroll when modal is open
  useEffect(() => {
    if (isTimelineOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [isTimelineOpen]);

  useEffect(() => {
    const loadAnalysis = async () => {
      try {
        setIsLoading(true);
        const result = await referenceApi.getAnalysis(analysisId);
        setAnalysis(result);
      } catch (error) {
        console.error("Failed to load analysis:", error);
        toast.error("분석 결과를 불러오는데 실패했습니다");
      } finally {
        setIsLoading(false);
      }
    };

    if (analysisId) {
      loadAnalysis();
    }
  }, [analysisId]);

  const handleReanalyze = async () => {
    if (!confirm("다시 분석하시겠습니까? 기존 분석 결과가 삭제되고 새로 분석됩니다.")) return;

    try {
      setIsReanalyzing(true);
      const result = await referenceApi.reanalyze(analysisId);
      toast.success("재분석을 시작했습니다");
      router.push("/references");
    } catch (error) {
      toast.error("재분석 요청 실패");
      setIsReanalyzing(false);
    }
  };

  const handleDelete = async () => {
    if (!confirm("정말 삭제하시겠습니까?")) return;

    try {
      await referenceApi.deleteAnalysis(analysisId);
      toast.success("삭제 완료");
      router.push("/references");
    } catch (error) {
      toast.error("삭제 실패");
    }
  };

  const handleStartEditTitle = () => {
    setEditedTitle(analysis?.title || "");
    setIsEditingTitle(true);
  };

  const handleCancelEditTitle = () => {
    setIsEditingTitle(false);
    setEditedTitle("");
  };

  const handleSaveTitle = async () => {
    if (!analysis) return;

    try {
      setIsSavingTitle(true);
      const updatedAnalysis = await referenceApi.updateAnalysis(analysisId, {
        title: editedTitle.trim() || undefined,
      });
      setAnalysis(updatedAnalysis);
      setIsEditingTitle(false);
      toast.success("제목이 저장되었습니다");
    } catch (error) {
      console.error("Failed to save title:", error);
      toast.error("제목 저장에 실패했습니다");
    } finally {
      setIsSavingTitle(false);
    }
  };

  const getStatusInfo = (status: string) => {
    const statusMap: Record<string, { icon: React.ElementType; text: string; color: string }> = {
      completed: { icon: CheckCircle2, text: "분석 완료", color: "text-emerald-500" },
      failed: { icon: AlertCircle, text: "분석 실패", color: "text-red-500" },
      pending: { icon: Clock, text: "대기중", color: "text-amber-500" },
      downloading: { icon: Clock, text: "다운로드중", color: "text-amber-500" },
      extracting: { icon: Clock, text: "추출중", color: "text-amber-500" },
      transcribing: { icon: Clock, text: "전사중", color: "text-amber-500" },
      analyzing: { icon: Clock, text: "분석중", color: "text-amber-500" },
    };
    return statusMap[status] || statusMap.pending;
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-950 flex items-center justify-center">
        <div className="text-center space-y-4">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center mx-auto animate-pulse">
            <Sparkles className="w-8 h-8 text-white" />
          </div>
          <p className="text-gray-500 dark:text-gray-400 font-medium">분석 결과 로딩중...</p>
        </div>
      </div>
    );
  }

  if (!analysis) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-950 flex items-center justify-center">
        <div className="text-center space-y-4">
          <div className="w-16 h-16 rounded-2xl bg-gray-200 dark:bg-gray-800 flex items-center justify-center mx-auto">
            <AlertCircle className="w-8 h-8 text-gray-400" />
          </div>
          <p className="text-gray-500 dark:text-gray-400 font-medium">분석 결과를 찾을 수 없습니다</p>
          <button
            onClick={() => router.back()}
            className="px-4 py-2 text-sm font-medium text-violet-600 hover:text-violet-700"
          >
            돌아가기
          </button>
        </div>
      </div>
    );
  }

  const statusInfo = getStatusInfo(analysis.status);
  const StatusIcon = statusInfo.icon;
  const structurePattern = analysis.structure_pattern as StructurePattern | undefined;
  const images = analysis.images || [];

  // Calculate Total Score
  const calculateTotalScore = () => {
    const scores: { name: string; score: number; weight: number; available: boolean }[] = [];

    // CTA Analysis: 25% weight
    if (analysis.cta_analysis?.effectiveness_score !== undefined) {
      scores.push({
        name: "CTA 효과성",
        score: analysis.cta_analysis.effectiveness_score,
        weight: 0.25,
        available: true,
      });
    } else {
      scores.push({ name: "CTA 효과성", score: 0, weight: 0.25, available: false });
    }

    // Hook Points: 25% weight (average of all effectiveness_score)
    if (analysis.hook_points && analysis.hook_points.length > 0) {
      const avgHook = analysis.hook_points.reduce((sum, hp) => sum + (hp.effectiveness_score || 0), 0) / analysis.hook_points.length;
      scores.push({ name: "후킹 포인트", score: avgHook, weight: 0.25, available: true });
    } else {
      scores.push({ name: "후킹 포인트", score: 0, weight: 0.25, available: false });
    }

    // Edge Points: 15% weight (average of all impact_score)
    if (analysis.edge_points && analysis.edge_points.length > 0) {
      const avgEdge = analysis.edge_points.reduce((sum, ep) => sum + (ep.impact_score || 0), 0) / analysis.edge_points.length;
      scores.push({ name: "엣지 포인트", score: avgEdge, weight: 0.15, available: true });
    } else {
      scores.push({ name: "엣지 포인트", score: 0, weight: 0.15, available: false });
    }

    // Emotional Triggers: 15% weight (average of all intensity)
    if (analysis.emotional_triggers && analysis.emotional_triggers.length > 0) {
      const avgEmotion = analysis.emotional_triggers.reduce((sum, et) => sum + (et.intensity || 0), 0) / analysis.emotional_triggers.length;
      scores.push({ name: "감정 트리거", score: avgEmotion, weight: 0.15, available: true });
    } else {
      scores.push({ name: "감정 트리거", score: 0, weight: 0.15, available: false });
    }

    // Selling Points: 20% weight (average of all effectiveness)
    if (analysis.selling_points && analysis.selling_points.length > 0) {
      const avgSelling = analysis.selling_points.reduce((sum, sp) => sum + (sp.effectiveness || 0), 0) / analysis.selling_points.length;
      scores.push({ name: "셀링 포인트", score: avgSelling, weight: 0.2, available: true });
    } else {
      scores.push({ name: "셀링 포인트", score: 0, weight: 0.2, available: false });
    }

    // Calculate weighted average only from available scores
    const availableScores = scores.filter((s) => s.available);
    const totalWeight = availableScores.reduce((sum, s) => sum + s.weight, 0);

    let totalScore = 0;
    if (totalWeight > 0) {
      totalScore = availableScores.reduce((sum, s) => sum + s.score * (s.weight / totalWeight), 0) * 100;
    }

    return { totalScore: Math.round(totalScore), breakdown: scores };
  };

  const { totalScore: calculatedScore, breakdown } = calculateTotalScore();

  // Use AI score if available, otherwise use calculated score
  const totalScore = analysis.overall_evaluation?.total_score
    ? Math.round(analysis.overall_evaluation.total_score * 100)
    : calculatedScore;

  // Get color based on total score
  const getScoreColor = (score: number) => {
    if (score >= 80) return { text: "text-emerald-500", bg: "bg-emerald-500", gradient: "from-emerald-500 to-teal-600" };
    if (score >= 60) return { text: "text-amber-500", bg: "bg-amber-500", gradient: "from-amber-500 to-orange-600" };
    return { text: "text-red-500", bg: "bg-red-500", gradient: "from-red-500 to-rose-600" };
  };

  const scoreColors = getScoreColor(totalScore);

  // Generate thumbnail URL (including YouTube support)
  const getThumbnailUrl = () => {
    if (analysis.thumbnail_url) return analysis.thumbnail_url;

    // For YouTube, generate thumbnail from URL
    const url = analysis.source_url || "";
    if (url.includes("youtube") || url.includes("youtu.be")) {
      const ytMatch = url.match(/(?:youtube\.com\/(?:watch\?v=|shorts\/|embed\/)|youtu\.be\/)([a-zA-Z0-9_-]+)/);
      if (ytMatch && ytMatch[1]) {
        return `https://img.youtube.com/vi/${ytMatch[1]}/hqdefault.jpg`;
      }
    }

    return "";
  };

  const thumbnailUrl = getThumbnailUrl();

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      {/* Header */}
      <header className="sticky top-0 z-30 bg-white/80 dark:bg-gray-900/80 backdrop-blur-xl border-b border-gray-200 dark:border-gray-800">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button
                onClick={() => router.back()}
                className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-xl transition-colors"
              >
                <ArrowLeft className="w-5 h-5 text-gray-600 dark:text-gray-400" />
              </button>
              <div>
                {isEditingTitle ? (
                  <div className="flex items-center gap-2">
                    <input
                      type="text"
                      value={editedTitle}
                      onChange={(e) => setEditedTitle(e.target.value)}
                      placeholder="레퍼런스 제목 입력..."
                      className="text-xl font-bold text-gray-900 dark:text-white bg-transparent border-b-2 border-violet-500 focus:outline-none px-1 py-0.5 min-w-[200px]"
                      autoFocus
                      onKeyDown={(e) => {
                        if (e.key === "Enter") handleSaveTitle();
                        if (e.key === "Escape") handleCancelEditTitle();
                      }}
                    />
                    <button
                      onClick={handleSaveTitle}
                      disabled={isSavingTitle}
                      className="p-1.5 hover:bg-emerald-100 dark:hover:bg-emerald-900/30 rounded-lg transition-colors disabled:opacity-50"
                      title="저장"
                    >
                      <Check className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
                    </button>
                    <button
                      onClick={handleCancelEditTitle}
                      disabled={isSavingTitle}
                      className="p-1.5 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors disabled:opacity-50"
                      title="취소"
                    >
                      <X className="w-4 h-4 text-gray-500" />
                    </button>
                  </div>
                ) : (
                  <div className="flex items-center gap-2 group">
                    <h1
                      className="text-xl font-bold text-gray-900 dark:text-white cursor-pointer hover:text-violet-600 dark:hover:text-violet-400 transition-colors"
                      onClick={handleStartEditTitle}
                    >
                      {analysis?.title || "제목 없음"}
                    </h1>
                    <button
                      onClick={handleStartEditTitle}
                      className="p-1.5 opacity-0 group-hover:opacity-100 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-all"
                      title="제목 편집"
                    >
                      <Pencil className="w-4 h-4 text-gray-500" />
                    </button>
                  </div>
                )}
                <p className="text-sm text-gray-500 dark:text-gray-400">레퍼런스 상세 분석</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full ${statusInfo.color} bg-gray-100 dark:bg-gray-800`}>
                <StatusIcon className="w-4 h-4" />
                <span className="text-sm font-medium">{statusInfo.text}</span>
              </div>
              <button
                onClick={handleReanalyze}
                disabled={isReanalyzing}
                className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-xl transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                title="다시 분석"
              >
                <RefreshCw className={`w-5 h-5 text-gray-600 dark:text-gray-400 ${isReanalyzing ? 'animate-spin' : ''}`} />
              </button>
              <button
                onClick={handleDelete}
                className="p-2 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-xl transition-colors"
                title="삭제"
              >
                <Trash2 className="w-5 h-5 text-red-500" />
              </button>
              {analysis.source_url && (
                <a
                  href={analysis.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-violet-600 to-purple-600 text-white rounded-xl hover:from-violet-700 hover:to-purple-700 transition-all font-medium text-sm"
                >
                  원본 보기
                  <ExternalLink className="w-4 h-4" />
                </a>
              )}
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Top section: Images + Overview */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-10">
          {/* Images */}
          <div className="lg:col-span-1">
            <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 p-4 sticky top-24">
              {/* Main Image */}
              <div className="aspect-square bg-gradient-to-br from-violet-600 via-indigo-600 to-purple-700 rounded-xl mb-4 relative overflow-hidden">
                {images[activeImageIndex] ? (
                  <img
                    src={images[activeImageIndex]}
                    alt={`Image ${activeImageIndex + 1}`}
                    className="w-full h-full object-cover rounded-xl"
                  />
                ) : thumbnailUrl ? (
                  <img
                    src={thumbnailUrl}
                    alt="Thumbnail"
                    className="w-full h-full object-cover rounded-xl"
                  />
                ) : (
                  <div className="w-full h-full flex flex-col items-center justify-center p-4">
                    <div className="w-16 h-16 rounded-xl bg-white/20 backdrop-blur-sm flex items-center justify-center mb-4">
                      {analysis?.duration ? (
                        <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                      ) : (analysis?.images?.length || 0) > 1 ? (
                        <Layers className="w-8 h-8 text-white" />
                      ) : (
                        <ImageIcon className="w-8 h-8 text-white" />
                      )}
                    </div>
                    <span className="text-white/90 text-sm font-semibold tracking-wide">AI Content</span>
                    <span className="text-white/70 text-xs font-medium">Factory</span>
                  </div>
                )}
              </div>

              {/* Image thumbnails */}
              {images.length > 1 && (
                <div className="flex gap-2 overflow-x-auto pb-2">
                  {images.map((img, idx) => (
                    <button
                      key={idx}
                      onClick={() => setActiveImageIndex(idx)}
                      className={`flex-shrink-0 w-16 h-16 rounded-lg overflow-hidden border-2 transition-all ${
                        idx === activeImageIndex
                          ? "border-violet-500 ring-2 ring-violet-500/30"
                          : "border-transparent hover:border-gray-300"
                      }`}
                    >
                      <img src={img} alt={`Thumb ${idx + 1}`} className="w-full h-full object-cover" />
                    </button>
                  ))}
                </div>
              )}

              <div className="mt-4 pt-4 border-t border-gray-100 dark:border-gray-800 text-sm text-gray-500 dark:text-gray-400 flex items-center justify-between">
                <span>
                  {images.length > 0 ? (
                    `총 ${images.length}개 이미지`
                  ) : analysis.source_url?.includes("youtube") || analysis.source_url?.includes("youtu.be") ? (
                    analysis.source_url?.includes("/shorts/") ? "YouTube 쇼츠" : "YouTube 영상"
                  ) : analysis.source_url?.includes("instagram") && analysis.source_url?.includes("/reel/") ? (
                    "Instagram 릴스"
                  ) : (
                    "미디어"
                  )}
                </span>
                {/* Timeline button */}
                {analysis.segments && analysis.segments.length > 0 && (
                  <button
                    onClick={() => setIsTimelineOpen(true)}
                    className="flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-medium text-violet-600 dark:text-violet-400 bg-violet-50 dark:bg-violet-900/20 hover:bg-violet-100 dark:hover:bg-violet-900/40 rounded-lg transition-colors"
                    title="타임라인 보기"
                  >
                    <Clock className="w-3.5 h-3.5" />
                    <span>타임라인</span>
                  </button>
                )}
              </div>
            </div>
          </div>

          {/* Overview cards */}
          <div className="lg:col-span-2 space-y-6">
            {/* Total Score */}
            <div className={`bg-gradient-to-br ${scoreColors.gradient} rounded-2xl p-6 text-white`}>
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-xl bg-white/20 flex items-center justify-center">
                  <Trophy className="w-5 h-5" />
                </div>
                <h2 className="text-lg font-bold">종합 점수</h2>
              </div>

              <div className="flex items-center gap-8">
                {/* Circular Progress Indicator */}
                <div className="relative w-32 h-32 flex-shrink-0">
                  <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
                    {/* Background circle */}
                    <circle
                      cx="50"
                      cy="50"
                      r="42"
                      fill="none"
                      stroke="rgba(255,255,255,0.2)"
                      strokeWidth="8"
                    />
                    {/* Progress circle */}
                    <circle
                      cx="50"
                      cy="50"
                      r="42"
                      fill="none"
                      stroke="white"
                      strokeWidth="8"
                      strokeLinecap="round"
                      strokeDasharray={`${totalScore * 2.64} 264`}
                      className="transition-all duration-1000 ease-out"
                    />
                  </svg>
                  <div className="absolute inset-0 flex flex-col items-center justify-center">
                    <span className="text-3xl font-bold">{totalScore}</span>
                    <span className="text-xs text-white/80">/ 100</span>
                  </div>
                </div>

                {/* Score Breakdown */}
                <div className="flex-1 space-y-2">
                  {breakdown.map((item, idx) => (
                    <div key={idx} className="flex items-center gap-3">
                      <div className="w-24 text-xs text-white/80">{item.name}</div>
                      <div className="flex-1 h-2 bg-white/20 rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full transition-all duration-700 ${item.available ? "bg-white" : "bg-white/30"}`}
                          style={{ width: `${item.available ? item.score * 100 : 0}%` }}
                        />
                      </div>
                      <div className="w-10 text-xs text-right">
                        {item.available ? `${Math.round(item.score * 100)}%` : "-"}
                      </div>
                      <div className="w-8 text-xs text-white/60">
                        ({Math.round(item.weight * 100)}%)
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Score Legend */}
              <div className="mt-4 pt-4 border-t border-white/20 flex gap-4 text-xs">
                <div className="flex items-center gap-1">
                  <div className="w-3 h-3 rounded-full bg-emerald-400" />
                  <span className="text-white/80">우수 (80+)</span>
                </div>
                <div className="flex items-center gap-1">
                  <div className="w-3 h-3 rounded-full bg-amber-400" />
                  <span className="text-white/80">양호 (60-79)</span>
                </div>
                <div className="flex items-center gap-1">
                  <div className="w-3 h-3 rounded-full bg-red-400" />
                  <span className="text-white/80">개선 필요 (60 미만)</span>
                </div>
              </div>

              {/* AI One-line Review */}
              {analysis.overall_evaluation?.one_line_review && (
                <div className="mt-4 pt-4 border-t border-white/20">
                  <p className="text-sm text-white/90 italic">
                    &quot;{analysis.overall_evaluation.one_line_review}&quot;
                  </p>
                </div>
              )}

              {/* Strengths & Weaknesses */}
              {analysis.overall_evaluation && (analysis.overall_evaluation.strengths?.length > 0 || analysis.overall_evaluation.weaknesses?.length > 0) && (
                <div className="mt-4 pt-4 border-t border-white/20 grid grid-cols-1 md:grid-cols-2 gap-4">
                  {analysis.overall_evaluation.strengths && analysis.overall_evaluation.strengths.length > 0 && (
                    <div className="bg-white/10 rounded-lg p-3">
                      <p className="text-xs font-semibold text-emerald-300 mb-2 flex items-center gap-1">
                        <CheckCircle2 className="w-3.5 h-3.5" /> 잘한 점
                      </p>
                      <ul className="space-y-1">
                        {analysis.overall_evaluation.strengths.map((s, i) => (
                          <li key={i} className="text-xs text-white/80 flex items-start gap-1.5">
                            <span className="text-emerald-400 mt-0.5">+</span>
                            <span>{s}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {analysis.overall_evaluation.weaknesses && analysis.overall_evaluation.weaknesses.length > 0 && (
                    <div className="bg-white/10 rounded-lg p-3">
                      <p className="text-xs font-semibold text-amber-300 mb-2 flex items-center gap-1">
                        <AlertCircle className="w-3.5 h-3.5" /> 개선점
                      </p>
                      <ul className="space-y-1">
                        {analysis.overall_evaluation.weaknesses.map((w, i) => (
                          <li key={i} className="text-xs text-white/80 flex items-start gap-1.5">
                            <span className="text-amber-400 mt-0.5">-</span>
                            <span>{w}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Recommendations - Moved to top */}
            {analysis.recommendations && analysis.recommendations.length > 0 && (
              <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 p-6">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500 to-sky-600 flex items-center justify-center">
                    <Lightbulb className="w-5 h-5 text-white" />
                  </div>
                  <div>
                    <h2 className="text-lg font-bold text-gray-900 dark:text-white">추천 사항</h2>
                    <p className="text-xs text-gray-500 dark:text-gray-400">{analysis.recommendations.length}개 항목</p>
                  </div>
                </div>
                <div className="space-y-3 max-h-[300px] overflow-y-auto">
                  {(analysis.recommendations as Recommendation[]).map((rec, idx) => (
                    <div key={idx} className="p-4 bg-gray-50 dark:bg-gray-800 rounded-xl space-y-2">
                      <div className="flex items-start gap-3">
                        {rec.priority && (
                          <span className={`flex-shrink-0 px-2 py-0.5 rounded text-xs font-bold ${
                            rec.priority === 1 ? "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300" :
                            rec.priority === 2 ? "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300" :
                            "bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300"
                          }`}>
                            P{rec.priority}
                          </span>
                        )}
                        <div className="flex-1">
                          <p className="text-sm font-medium text-gray-900 dark:text-white">{rec.action}</p>
                          {rec.reason && (
                            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{rec.reason}</p>
                          )}
                        </div>
                      </div>
                      {rec.example && (
                        <div className="pt-2 border-t border-gray-200 dark:border-gray-700 ml-8">
                          <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">예시</p>
                          <p className="text-xs text-gray-600 dark:text-gray-400 italic">"{rec.example}"</p>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* CTA Analysis */}
            {analysis.cta_analysis && (
              <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 p-6">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-rose-500 to-pink-600 flex items-center justify-center">
                    <Megaphone className="w-5 h-5 text-white" />
                  </div>
                  <h2 className="text-lg font-bold text-gray-900 dark:text-white">CTA 분석</h2>
                </div>
                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-xl">
                    <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">CTA 유형</p>
                    <p className="font-semibold text-gray-900 dark:text-white">{analysis.cta_analysis.cta_type}</p>
                  </div>
                  <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-xl">
                    <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">배치 위치</p>
                    <p className="font-semibold text-gray-900 dark:text-white">{analysis.cta_analysis.placement}</p>
                  </div>
                </div>
                <ScoreBar
                  score={analysis.cta_analysis.effectiveness_score}
                  label="CTA 효과성"
                  color="text-rose-500"
                  reasoning={analysis.cta_analysis.score_reasoning}
                  scoreBreakdown={analysis.cta_analysis.score_breakdown as ScoreBreakdown}
                  totalReason={analysis.cta_analysis.total_reason}
                />
                {analysis.cta_analysis.urgency_elements?.length > 0 && (
                  <div className="mt-4">
                    <p className="text-xs text-gray-500 dark:text-gray-400 mb-2">긴급성 요소</p>
                    <div className="flex flex-wrap gap-2">
                      {analysis.cta_analysis.urgency_elements.map((el, idx) => (
                        <span key={idx} className="px-2 py-1 bg-rose-100 dark:bg-rose-900/30 text-rose-700 dark:text-rose-300 rounded-lg text-xs">
                          {el}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Quick Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-4 text-center">
                <Zap className="w-6 h-6 text-amber-500 mx-auto mb-2" />
                <p className="text-2xl font-bold text-gray-900 dark:text-white">{analysis.hook_points?.length || 0}</p>
                <p className="text-xs text-gray-500 dark:text-gray-400">후킹 포인트</p>
              </div>
              <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-4 text-center">
                <Heart className="w-6 h-6 text-rose-500 mx-auto mb-2" />
                <p className="text-2xl font-bold text-gray-900 dark:text-white">{analysis.emotional_triggers?.length || 0}</p>
                <p className="text-xs text-gray-500 dark:text-gray-400">감정 트리거</p>
              </div>
              <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-4 text-center">
                <AlertTriangle className="w-6 h-6 text-orange-500 mx-auto mb-2" />
                <p className="text-2xl font-bold text-gray-900 dark:text-white">{analysis.pain_points?.length || 0}</p>
                <p className="text-xs text-gray-500 dark:text-gray-400">페인 포인트</p>
              </div>
              <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-4 text-center">
                <TrendingUp className="w-6 h-6 text-emerald-500 mx-auto mb-2" />
                <p className="text-2xl font-bold text-gray-900 dark:text-white">{analysis.selling_points?.length || 0}</p>
                <p className="text-xs text-gray-500 dark:text-gray-400">셀링 포인트</p>
              </div>
            </div>
          </div>
        </div>

        {/* Analysis Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Hook Points */}
          {analysis.hook_points && analysis.hook_points.length > 0 && (
            <AnalysisCard
              icon={Zap}
              title="후킹 포인트"
              count={analysis.hook_points.length}
              accentColor="amber"
            >
              {analysis.hook_points.map((hook, idx) => (
                <div key={idx} className="p-4 bg-gray-50 dark:bg-gray-800 rounded-xl space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="px-2 py-0.5 bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300 rounded text-xs font-medium">
                      {hook.hook_type}
                    </span>
                    <span className="text-xs text-gray-500">{hook.timestamp}</span>
                  </div>
                  <p className="text-sm text-gray-700 dark:text-gray-300">{hook.description}</p>
                  <ScoreBar score={hook.effectiveness_score} label="효과성" color="text-amber-500" reasoning={hook.score_reasoning} scoreBreakdown={hook.score_breakdown as ScoreBreakdown} totalReason={hook.total_reason} />
                  {hook.adaptable_template && (
                    <div className="pt-2 border-t border-gray-200 dark:border-gray-700">
                      <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">활용 템플릿</p>
                      <p className="text-xs text-gray-600 dark:text-gray-400 italic">"{hook.adaptable_template}"</p>
                    </div>
                  )}
                </div>
              ))}
            </AnalysisCard>
          )}

          {/* Edge Points */}
          {analysis.edge_points && analysis.edge_points.length > 0 && (
            <AnalysisCard
              icon={Target}
              title="엣지 포인트"
              count={analysis.edge_points.length}
              accentColor="blue"
            >
              {analysis.edge_points.map((edge, idx) => (
                <div key={idx} className="p-4 bg-gray-50 dark:bg-gray-800 rounded-xl space-y-2">
                  <span className="px-2 py-0.5 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded text-xs font-medium">
                    {edge.category}
                  </span>
                  <p className="text-sm text-gray-700 dark:text-gray-300">{edge.description}</p>
                  <ScoreBar score={edge.impact_score} label="임팩트" color="text-blue-500" reasoning={edge.score_reasoning} scoreBreakdown={edge.score_breakdown as ScoreBreakdown} totalReason={edge.total_reason} />
                  <div className="pt-2 border-t border-gray-200 dark:border-gray-700">
                    <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">적용 방법</p>
                    <p className="text-xs text-gray-600 dark:text-gray-400">{edge.how_to_apply}</p>
                  </div>
                </div>
              ))}
            </AnalysisCard>
          )}

          {/* Emotional Triggers */}
          {analysis.emotional_triggers && analysis.emotional_triggers.length > 0 && (
            <AnalysisCard
              icon={Heart}
              title="감정 트리거"
              count={analysis.emotional_triggers.length}
              accentColor="rose"
            >
              {analysis.emotional_triggers.map((trigger, idx) => (
                <div key={idx} className="p-4 bg-gray-50 dark:bg-gray-800 rounded-xl space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="px-2 py-0.5 bg-rose-100 dark:bg-rose-900/30 text-rose-700 dark:text-rose-300 rounded text-xs font-medium">
                      {trigger.trigger_type}
                    </span>
                    <span className="text-xs text-gray-500">{trigger.timestamp}</span>
                  </div>
                  <p className="text-sm text-gray-700 dark:text-gray-300">{trigger.description}</p>
                  <ScoreBar score={trigger.intensity} label="강도" color="text-rose-500" reasoning={trigger.score_reasoning} scoreBreakdown={trigger.score_breakdown as ScoreBreakdown} totalReason={trigger.total_reason} />
                </div>
              ))}
            </AnalysisCard>
          )}

          {/* Pain Points */}
          {analysis.pain_points && analysis.pain_points.length > 0 && (
            <AnalysisCard
              icon={AlertTriangle}
              title="페인 포인트"
              count={analysis.pain_points.length}
              accentColor="amber"
            >
              {analysis.pain_points.map((pain, idx) => (
                <div key={idx} className="p-4 bg-gray-50 dark:bg-gray-800 rounded-xl space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="px-2 py-0.5 bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-300 rounded text-xs font-medium">
                      {pain.pain_type}
                    </span>
                    <span className="text-xs text-gray-500">{pain.timestamp}</span>
                  </div>
                  <p className="text-sm text-gray-700 dark:text-gray-300">{pain.description}</p>
                  <div className="pt-2 border-t border-gray-200 dark:border-gray-700">
                    <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">공감 기법</p>
                    <p className="text-xs text-gray-600 dark:text-gray-400">{pain.empathy_technique}</p>
                  </div>
                </div>
              ))}
            </AnalysisCard>
          )}

          {/* Selling Points */}
          {analysis.selling_points && analysis.selling_points.length > 0 && (
            <AnalysisCard
              icon={TrendingUp}
              title="셀링 포인트"
              count={analysis.selling_points.length}
              accentColor="emerald"
            >
              {analysis.selling_points.map((sell, idx) => (
                <div key={idx} className="p-4 bg-gray-50 dark:bg-gray-800 rounded-xl space-y-2">
                  <span className="text-xs text-gray-500">{sell.timestamp}</span>
                  <p className="text-sm font-medium text-gray-900 dark:text-white">{sell.claim}</p>
                  <div className="flex gap-2">
                    <span className="px-2 py-0.5 bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300 rounded text-xs">
                      {sell.evidence_type}
                    </span>
                    <span className="px-2 py-0.5 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 rounded text-xs">
                      {sell.persuasion_technique}
                    </span>
                  </div>
                  {sell.effectiveness !== undefined && (
                    <ScoreBar score={sell.effectiveness} label="효과성" color="text-emerald-500" reasoning={sell.score_reasoning} scoreBreakdown={sell.score_breakdown as ScoreBreakdown} totalReason={sell.total_reason} />
                  )}
                </div>
              ))}
            </AnalysisCard>
          )}

        </div>

        {/* Error message if failed */}
        {analysis.status === "failed" && analysis.error_message && (
          <div className="mt-8 p-6 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-2xl">
            <div className="flex items-center gap-3 mb-2">
              <AlertCircle className="w-5 h-5 text-red-500" />
              <h3 className="font-bold text-red-700 dark:text-red-400">분석 실패</h3>
            </div>
            <p className="text-red-600 dark:text-red-300">{analysis.error_message}</p>
          </div>
        )}
      </main>

      {/* Timeline Modal */}
      {isTimelineOpen && analysis.segments && analysis.segments.length > 0 && (
        <div
          className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50"
          onClick={() => setIsTimelineOpen(false)}
        >
          <div
            className="bg-white dark:bg-gray-900 rounded-3xl w-full max-w-2xl max-h-[80vh] shadow-2xl border border-gray-200 dark:border-gray-800 animate-in fade-in zoom-in-95 duration-200 flex flex-col mx-4"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center">
                  <Clock className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-gray-900 dark:text-white">타임라인</h3>
                  <p className="text-xs text-gray-500 dark:text-gray-400">{analysis.segments.length}개 세그먼트</p>
                </div>
              </div>
              <button
                onClick={() => setIsTimelineOpen(false)}
                className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-xl transition-colors"
              >
                <X className="w-5 h-5 text-gray-500" />
              </button>
            </div>

            {/* Engagement Score Legend */}
            <div className="px-6 py-3 bg-gray-50 dark:bg-gray-800/50 border-b border-gray-200 dark:border-gray-700">
              <div className="flex items-center gap-2 mb-2">
                <BarChart3 className="w-4 h-4 text-amber-500" />
                <span className="text-xs font-semibold text-gray-700 dark:text-gray-300">참여도 평가 기준</span>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-[11px]">
                {/* 시각적 자극 */}
                <div>
                  <button
                    onClick={() => setExpandedCriteria(expandedCriteria === "visual" ? null : "visual")}
                    className="flex items-center gap-1 text-gray-500 dark:text-gray-400 hover:text-violet-600 dark:hover:text-violet-400 transition-colors"
                  >
                    <span className="w-2 h-2 rounded-full bg-violet-500"></span>
                    <span>시각적 자극 25%</span>
                    <ChevronRight className={`w-3 h-3 transition-transform ${expandedCriteria === "visual" ? "rotate-90" : ""}`} />
                  </button>
                  {expandedCriteria === "visual" && (
                    <p className="mt-1 ml-3 text-[10px] text-gray-400 dark:text-gray-500">
                      화면 움직임, 색상 대비, 줌인/아웃, 전환 효과
                    </p>
                  )}
                </div>
                {/* 정보 밀도 */}
                <div>
                  <button
                    onClick={() => setExpandedCriteria(expandedCriteria === "info" ? null : "info")}
                    className="flex items-center gap-1 text-gray-500 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
                  >
                    <span className="w-2 h-2 rounded-full bg-blue-500"></span>
                    <span>정보 밀도 25%</span>
                    <ChevronRight className={`w-3 h-3 transition-transform ${expandedCriteria === "info" ? "rotate-90" : ""}`} />
                  </button>
                  {expandedCriteria === "info" && (
                    <p className="mt-1 ml-3 text-[10px] text-gray-400 dark:text-gray-500">
                      새로운 정보 전달 속도, 시청자가 얻는 가치
                    </p>
                  )}
                </div>
                {/* 감정적 자극 */}
                <div>
                  <button
                    onClick={() => setExpandedCriteria(expandedCriteria === "emotion" ? null : "emotion")}
                    className="flex items-center gap-1 text-gray-500 dark:text-gray-400 hover:text-rose-600 dark:hover:text-rose-400 transition-colors"
                  >
                    <span className="w-2 h-2 rounded-full bg-rose-500"></span>
                    <span>감정적 자극 25%</span>
                    <ChevronRight className={`w-3 h-3 transition-transform ${expandedCriteria === "emotion" ? "rotate-90" : ""}`} />
                  </button>
                  {expandedCriteria === "emotion" && (
                    <p className="mt-1 ml-3 text-[10px] text-gray-400 dark:text-gray-500">
                      궁금증, 긴장감, 공감, 흥미 유발 정도
                    </p>
                  )}
                </div>
                {/* 시청 유지력 */}
                <div>
                  <button
                    onClick={() => setExpandedCriteria(expandedCriteria === "retention" ? null : "retention")}
                    className="flex items-center gap-1 text-gray-500 dark:text-gray-400 hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors"
                  >
                    <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                    <span>시청 유지력 25%</span>
                    <ChevronRight className={`w-3 h-3 transition-transform ${expandedCriteria === "retention" ? "rotate-90" : ""}`} />
                  </button>
                  {expandedCriteria === "retention" && (
                    <p className="mt-1 ml-3 text-[10px] text-gray-400 dark:text-gray-500">
                      다음 내용을 계속 보고 싶게 만드는 힘
                    </p>
                  )}
                </div>
              </div>
            </div>

            {/* Timeline Content */}
            <div className="flex-1 overflow-y-auto p-6">
              <div className="space-y-3">
                {analysis.segments.map((segment, index) => {
                  const formatTime = (seconds: number) => {
                    const mins = Math.floor(seconds / 60);
                    const secs = Math.floor(seconds % 60);
                    return `${mins}:${secs.toString().padStart(2, "0")}`;
                  };
                  const getSegmentColor = (type: string) => {
                    const colors: Record<string, string> = {
                      hook: "bg-rose-500",
                      intro: "bg-violet-500",
                      problem: "bg-amber-500",
                      solution: "bg-emerald-500",
                      benefit: "bg-cyan-500",
                      social_proof: "bg-blue-500",
                      cta: "bg-pink-500",
                      outro: "bg-slate-500",
                    };
                    return colors[type.toLowerCase()] || "bg-gray-500";
                  };
                  return (
                    <div
                      key={index}
                      className="group relative bg-gray-50 dark:bg-gray-800/50 rounded-xl p-4 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                    >
                      {/* Time and Type Header */}
                      <div className="flex items-center gap-3 mb-2">
                        <span className="text-sm font-mono font-semibold text-gray-900 dark:text-white">
                          {formatTime(segment.start_time)} - {formatTime(segment.end_time)}
                        </span>
                        <span className={`px-2 py-0.5 rounded text-xs font-medium text-white ${getSegmentColor(segment.segment_type)}`}>
                          {segment.segment_type}
                        </span>
                        {segment.engagement_score > 0 && (
                          <span className="ml-auto text-xs font-medium text-amber-600 dark:text-amber-400">
                            참여도 {Math.round(segment.engagement_score * 100)}%
                          </span>
                        )}
                      </div>

                      {/* Visual Description */}
                      <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
                        {segment.visual_description}
                      </p>

                      {/* Audio Transcript */}
                      {segment.audio_transcript && (
                        <div className="mt-2 pt-2 border-t border-gray-200 dark:border-gray-700">
                          <p className="text-xs text-gray-500 dark:text-gray-400 italic">
                            &quot;{segment.audio_transcript}&quot;
                          </p>
                        </div>
                      )}

                      {/* Text Overlay */}
                      {segment.text_overlay && (
                        <div className="mt-2 inline-block px-2 py-1 bg-violet-100 dark:bg-violet-900/30 rounded text-xs font-medium text-violet-700 dark:text-violet-300">
                          텍스트: {segment.text_overlay}
                        </div>
                      )}

                      {/* Techniques */}
                      {segment.techniques && segment.techniques.length > 0 && (
                        <div className="mt-2 flex flex-wrap gap-1">
                          {segment.techniques.map((tech, i) => (
                            <span
                              key={i}
                              className="px-1.5 py-0.5 bg-gray-200 dark:bg-gray-700 rounded text-xs text-gray-600 dark:text-gray-400"
                            >
                              {tech}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
