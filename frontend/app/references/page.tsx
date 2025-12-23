"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import Image from "next/image";
import {
  Plus,
  Link as LinkIcon,
  Upload,
  X,
  Loader2,
  Image as ImageIcon,
  Layers,
  Smartphone,
  Search,
  Trash2,
  ExternalLink,
  RefreshCw,
  CheckCircle2,
  Clock,
  AlertCircle,
  ChevronDown,
  Check,
} from "lucide-react";
import { toast } from "sonner";
import { useRouter } from "next/navigation";
import {
  studioApi,
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
} from "@/lib/api";

// Reference types
type ReferenceType = "single" | "carousel" | "story" | "video" | "shorts";
type ReferenceSource = "instagram" | "facebook" | "pinterest" | "youtube" | "upload";
type AnalysisStatus = "pending" | "downloading" | "extracting" | "transcribing" | "analyzing" | "completed" | "failed";

interface Reference {
  id: string;
  type: ReferenceType;
  source: ReferenceSource;
  sourceUrl?: string;
  title?: string;
  thumbnailUrl: string;
  images?: string[];
  status: AnalysisStatus;
  analysis: {
    composition: string;
    colorScheme: string;
    style: string;
    elements: string[];
  };
  // Full analysis data
  hookPoints?: HookPoint[];
  edgePoints?: EdgePoint[];
  emotionalTriggers?: EmotionalTrigger[];
  painPoints?: PainPoint[];
  sellingPoints?: SellingPoint[];
  ctaAnalysis?: CTAAnalysis;
  structurePattern?: StructurePattern | string;
  recommendations?: Recommendation[] | string[];
  segments?: TimelineSegment[];
  createdAt: string;
  errorMessage?: string;
}

export default function ReferencesPage() {
  const router = useRouter();
  const [references, setReferences] = useState<Reference[]>([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [linkInput, setLinkInput] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedPlatforms, setSelectedPlatforms] = useState<ReferenceSource[]>([]);
  const [isPlatformDropdownOpen, setIsPlatformDropdownOpen] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const pollingRef = useRef<Map<string, NodeJS.Timeout>>(new Map());
  const platformDropdownRef = useRef<HTMLDivElement>(null);

  // Platform options for the filter
  const platformOptions: { value: ReferenceSource; label: string; icon: React.ReactNode }[] = [
    {
      value: "youtube",
      label: "YouTube",
      icon: (
        <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
          <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/>
        </svg>
      )
    },
    {
      value: "instagram",
      label: "Instagram",
      icon: (
        <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"/>
        </svg>
      )
    },
    {
      value: "pinterest",
      label: "Pinterest",
      icon: (
        <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 0c-6.627 0-12 5.372-12 12 0 5.084 3.163 9.426 7.627 11.174-.105-.949-.2-2.405.042-3.441.218-.937 1.407-5.965 1.407-5.965s-.359-.719-.359-1.782c0-1.668.967-2.914 2.171-2.914 1.023 0 1.518.769 1.518 1.69 0 1.029-.655 2.568-.994 3.995-.283 1.194.599 2.169 1.777 2.169 2.133 0 3.772-2.249 3.772-5.495 0-2.873-2.064-4.882-5.012-4.882-3.414 0-5.418 2.561-5.418 5.207 0 1.031.397 2.138.893 2.738.098.119.112.224.083.345l-.333 1.36c-.053.22-.174.267-.402.161-1.499-.698-2.436-2.889-2.436-4.649 0-3.785 2.75-7.262 7.929-7.262 4.163 0 7.398 2.967 7.398 6.931 0 4.136-2.607 7.464-6.227 7.464-1.216 0-2.359-.631-2.75-1.378l-.748 2.853c-.271 1.043-1.002 2.35-1.492 3.146 1.124.347 2.317.535 3.554.535 6.627 0 12-5.373 12-12 0-6.628-5.373-12-12-12z"/>
        </svg>
      )
    },
    {
      value: "facebook",
      label: "Facebook",
      icon: (
        <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
          <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385h-3.047v-3.47h3.047v-2.642c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953h-1.514c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385c5.737-.9 10.125-5.864 10.125-11.854z"/>
        </svg>
      )
    },
    {
      value: "upload",
      label: "업로드",
      icon: <Upload className="w-4 h-4" />
    },
  ];

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (platformDropdownRef.current && !platformDropdownRef.current.contains(event.target as Node)) {
        setIsPlatformDropdownOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Toggle platform selection
  const togglePlatform = (platform: ReferenceSource) => {
    setSelectedPlatforms(prev =>
      prev.includes(platform)
        ? prev.filter(p => p !== platform)
        : [...prev, platform]
    );
  };

  // Get display text for platform filter button
  const getPlatformFilterText = () => {
    if (selectedPlatforms.length === 0 || selectedPlatforms.length === platformOptions.length) {
      return "전체";
    }
    if (selectedPlatforms.length === 1) {
      return platformOptions.find(p => p.value === selectedPlatforms[0])?.label || "전체";
    }
    return `${selectedPlatforms.length}개 선택`;
  };

  // Convert API result to Reference format
  const apiResultToReference = useCallback((result: AnalysisResult, overrideThumbnail?: string): Reference => {
    const imageCount = result.images?.length || 0;
    const hasVideo = result.duration != null && result.duration > 0;
    const url = result.source_url || "";

    // Detect source from URL
    let source: ReferenceSource = "upload";
    if (url.includes("instagram")) source = "instagram";
    else if (url.includes("facebook")) source = "facebook";
    else if (url.includes("pinterest")) source = "pinterest";
    else if (url.includes("youtube") || url.includes("youtu.be")) source = "youtube";

    // Determine reference type based on content
    let refType: ReferenceType = "single";

    if (source === "youtube") {
      // YouTube: shorts or video
      refType = url.includes("/shorts/") ? "shorts" : "video";
    } else if (source === "instagram" && url.includes("/reel/")) {
      // Instagram Reel
      refType = "video";
    } else if (hasVideo) {
      // Has duration = video content (Pinterest video, Facebook video, etc.)
      refType = "video";
    } else if (imageCount > 1) {
      // Multiple images = carousel
      refType = "carousel";
    } else {
      // Single image
      refType = "single";
    }

    // Extract analysis data
    const structurePattern = result.structure_pattern;
    const composition = typeof structurePattern === "string"
      ? structurePattern
      : structurePattern?.framework || "분석 대기중";

    const colorScheme = result.segments?.[0]?.visual_description || "분석 대기중";
    const style = result.tags?.join(", ") || "분석 대기중";
    const elements = result.segments?.map(s => s.segment_type).filter(Boolean) || [];

    // Use thumbnail from API or override, or generate for YouTube
    let thumbnailUrl = overrideThumbnail || result.thumbnail_url || "";

    // If no thumbnail and it's YouTube, generate from video ID
    if (!thumbnailUrl && source === "youtube" && url) {
      const ytMatch = url.match(/(?:youtube\.com\/(?:watch\?v=|shorts\/|embed\/)|youtu\.be\/)([a-zA-Z0-9_-]+)/);
      if (ytMatch && ytMatch[1]) {
        thumbnailUrl = `https://img.youtube.com/vi/${ytMatch[1]}/hqdefault.jpg`;
      }
    }

    return {
      id: result.analysis_id,
      type: refType,
      source,
      sourceUrl: result.source_url,
      title: result.title,
      thumbnailUrl,
      images: result.images || [],
      status: result.status as AnalysisStatus,
      analysis: {
        composition,
        colorScheme,
        style,
        elements,
      },
      // Full analysis data
      hookPoints: result.hook_points || [],
      edgePoints: result.edge_points || [],
      emotionalTriggers: result.emotional_triggers || [],
      painPoints: result.pain_points || [],
      sellingPoints: result.selling_points || [],
      ctaAnalysis: result.cta_analysis,
      structurePattern: result.structure_pattern,
      recommendations: result.recommendations || [],
      segments: result.segments || [],
      createdAt: new Date().toISOString().split("T")[0],
      errorMessage: result.error_message,
    };
  }, []);

  // Load references from API on mount
  useEffect(() => {
    const loadReferences = async () => {
      try {
        setIsLoading(true);
        const results = await referenceApi.listAnalyses();
        const refs = results.map(r => apiResultToReference(r));
        setReferences(refs);
      } catch (error) {
        console.error("Failed to load references:", error);
        toast.error("레퍼런스 목록을 불러오는데 실패했습니다");
      } finally {
        setIsLoading(false);
      }
    };
    loadReferences();
  }, [apiResultToReference]);

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      pollingRef.current.forEach(timer => clearTimeout(timer));
      pollingRef.current.clear();
    };
  }, []);

  // Poll for analysis completion
  const pollAnalysisStatus = useCallback(async (analysisId: string, thumbnailUrl: string) => {
    const maxAttempts = 60; // 5 minutes max
    let attempts = 0;

    const poll = async () => {
      attempts++;
      try {
        const result = await referenceApi.getAnalysis(analysisId);

        if (result.status === "completed" || result.status === "failed") {
          // Update reference with final result
          setReferences(prev => prev.map(ref =>
            ref.id === analysisId
              ? apiResultToReference(result, thumbnailUrl)
              : ref
          ));
          pollingRef.current.delete(analysisId);

          if (result.status === "completed") {
            toast.success("분석이 완료되었습니다!");
          } else {
            toast.error(result.error_message || "분석에 실패했습니다");
          }
          return;
        }

        // Update status
        setReferences(prev => prev.map(ref =>
          ref.id === analysisId
            ? { ...ref, status: result.status as AnalysisStatus }
            : ref
        ));

        // Continue polling if not done
        if (attempts < maxAttempts) {
          const timer = setTimeout(poll, 5000);
          pollingRef.current.set(analysisId, timer);
        }
      } catch (error: unknown) {
        console.error("Polling error:", error);

        // Check if it's a 404 error (record was deleted - no media found)
        const axiosError = error as { response?: { status?: number }; message?: string };
        const errorMsg = axiosError?.message?.toUpperCase() ?? "";
        const is404 = axiosError.response?.status === 404 || errorMsg.includes("404") || errorMsg.includes("NOT FOUND");

        if (is404) {
          pollingRef.current.delete(analysisId);
          setReferences(prev => prev.filter(ref => ref.id !== analysisId));
          toast.error("미디어를 찾을 수 없습니다. 이미지나 영상이 없는 링크입니다.");
          return;
        }

        if (attempts < maxAttempts) {
          const timer = setTimeout(poll, 5000);
          pollingRef.current.set(analysisId, timer);
        }
      }
    };

    poll();
  }, [apiResultToReference]);

  const handleAddLink = async () => {
    if (!linkInput.trim()) {
      toast.error("링크를 입력해주세요");
      return;
    }

    setIsAnalyzing(true);
    toast.info("링크 분석 중...");

    try {
      // Step 1: Parse SNS URL to validate and get platform info
      const parseResult = await studioApi.parseSNSUrl(linkInput);

      if (!parseResult.valid) {
        toast.error("지원하지 않는 링크입니다");
        setIsAnalyzing(false);
        return;
      }

      // Step 2: Get thumbnail
      let thumbnailUrl = "";

      // For YouTube, use YouTube's thumbnail service
      if (parseResult.platform === "youtube") {
        const videoId = parseResult.video_id;
        if (videoId) {
          thumbnailUrl = `https://img.youtube.com/vi/${videoId}/hqdefault.jpg`;
        }
      } else {
        // For other platforms, try to extract images
        try {
          const extractResult = await studioApi.extractSNSImages(linkInput);
          if (extractResult.success && extractResult.images?.length > 0) {
            thumbnailUrl = `data:image/jpeg;base64,${extractResult.images[0]}`;
          }
        } catch (extractError) {
          console.warn("Image extraction failed, continuing without thumbnail:", extractError);
        }
      }

      // Step 3: Submit for analysis (returns immediately with analysis_id)
      // Note: title is not passed - AI will generate it during analysis
      const analysisResponse = await referenceApi.analyze(linkInput);
      const analysisId = analysisResponse.analysis_id;

      // Determine source and type
      let source: ReferenceSource = "upload";
      let refType: ReferenceType = "single";

      if (parseResult.platform === "instagram") {
        source = "instagram";
        if (linkInput.includes("/reel/")) refType = "video";
      } else if (parseResult.platform === "facebook") {
        source = "facebook";
      } else if (parseResult.platform === "pinterest") {
        source = "pinterest";
      } else if (parseResult.platform === "youtube") {
        source = "youtube";
        if (linkInput.includes("/shorts/")) refType = "shorts";
        else refType = "video";
      }

      // Create initial reference with pending status
      const newReference: Reference = {
        id: analysisId,
        type: refType,
        source,
        sourceUrl: linkInput,
        title: undefined, // AI will generate the title
        thumbnailUrl,
        status: "pending",
        analysis: {
          composition: "분석 대기중",
          colorScheme: "분석 대기중",
          style: "분석 대기중",
          elements: [],
        },
        createdAt: new Date().toISOString().split("T")[0],
      };

      setReferences(prev => [newReference, ...prev]);
      setLinkInput("");
      setIsModalOpen(false);
      toast.success("분석이 시작되었습니다. 완료되면 알려드릴게요!");

      // Start polling for analysis completion
      pollAnalysisStatus(analysisId, thumbnailUrl);

    } catch (error) {
      console.error("Failed to add reference:", error);
      const errorMessage = error instanceof Error ? error.message : "알 수 없는 오류가 발생했습니다";
      toast.error(`레퍼런스 추가 실패: ${errorMessage}`);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    setIsAnalyzing(true);
    const fileCount = files.length;
    toast.info(`${fileCount}개 이미지 업로드 중...`);

    try {
      // Convert FileList to array
      const fileArray = Array.from(files);

      // Create thumbnail URLs for each file
      const thumbnailUrls = fileArray.map(file => URL.createObjectURL(file));

      // Upload all files to the API
      const uploadResponse = await referenceApi.uploadImages(fileArray);
      const analysisIds = uploadResponse.analysis_ids;

      // Create references for each uploaded file with pending status
      const newReferences: Reference[] = analysisIds.map((analysisId, index) => ({
        id: analysisId,
        type: "single" as ReferenceType,
        source: "upload" as ReferenceSource,
        thumbnailUrl: thumbnailUrls[index] || "",
        status: "pending" as AnalysisStatus,
        analysis: {
          composition: "분석 대기중",
          colorScheme: "분석 대기중",
          style: "분석 대기중",
          elements: [],
        },
        createdAt: new Date().toISOString().split("T")[0],
      }));

      setReferences(prev => [...newReferences, ...prev]);
      setIsModalOpen(false);
      toast.success(`${fileCount}개 이미지가 업로드되었습니다!`);

      // Start polling for each analysis
      analysisIds.forEach((analysisId, index) => {
        pollAnalysisStatus(analysisId, thumbnailUrls[index] || "");
      });

    } catch (error) {
      console.error("Failed to upload images:", error);
      toast.error("이미지 업로드에 실패했습니다");
    } finally {
      setIsAnalyzing(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await referenceApi.deleteAnalysis(id);
      setReferences(prev => prev.filter(r => r.id !== id));
      toast.success("레퍼런스가 삭제되었습니다");
    } catch (error) {
      console.error("Failed to delete reference:", error);
      toast.error("삭제에 실패했습니다");
    }
  };

  const handleRefresh = async (id: string) => {
    try {
      const result = await referenceApi.getAnalysis(id);
      const ref = references.find(r => r.id === id);
      setReferences(prev => prev.map(r =>
        r.id === id ? apiResultToReference(result, ref?.thumbnailUrl || "") : r
      ));
      toast.success("새로고침 완료");
    } catch (error) {
      toast.error("새로고침 실패");
    }
  };

  const getStatusIcon = (status: AnalysisStatus) => {
    switch (status) {
      case "completed":
        return <CheckCircle2 className="w-4 h-4 text-emerald-500" />;
      case "failed":
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      case "pending":
      case "downloading":
      case "extracting":
      case "transcribing":
      case "analyzing":
        return <Clock className="w-4 h-4 text-amber-500 animate-pulse" />;
      default:
        return null;
    }
  };

  const getStatusText = (status: AnalysisStatus) => {
    const statusMap: Record<AnalysisStatus, string> = {
      pending: "대기중",
      downloading: "다운로드중",
      extracting: "추출중",
      transcribing: "전사중",
      analyzing: "분석중",
      completed: "완료",
      failed: "실패",
    };
    return statusMap[status] || status;
  };

  const filteredReferences = references
    .filter(r => {
      // Platform filter: if no platforms selected or all selected, show all
      const platformMatch = selectedPlatforms.length === 0 ||
        selectedPlatforms.length === platformOptions.length ||
        selectedPlatforms.includes(r.source);

      // Search filter - search by reference title/name
      const searchMatch = searchQuery === "" ||
        r.title?.toLowerCase().includes(searchQuery.toLowerCase());

      return platformMatch && searchMatch;
    });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            레퍼런스 라이브러리
          </h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">
            SNS 콘텐츠를 분석하고 스타일을 저장하세요
          </p>
        </div>
        <button
          onClick={() => setIsModalOpen(true)}
          className="flex items-center gap-2 bg-gradient-to-r from-violet-600 to-indigo-600 text-white px-5 py-2.5 rounded-xl hover:from-violet-700 hover:to-indigo-700 transition-all shadow-lg shadow-violet-500/25 hover:shadow-violet-500/40 font-medium"
        >
          <Plus className="w-5 h-5" />
          새 레퍼런스
        </button>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="레퍼런스 이름 검색..."
            className="w-full pl-10 pr-4 py-2.5 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl text-gray-900 dark:text-white placeholder:text-gray-400 focus:ring-2 focus:ring-violet-500 focus:border-transparent transition-all"
          />
        </div>

        {/* Platform Multi-Select Dropdown */}
        <div className="relative" ref={platformDropdownRef}>
          <button
            onClick={() => setIsPlatformDropdownOpen(!isPlatformDropdownOpen)}
            className="flex items-center gap-2 px-4 py-2.5 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl text-gray-900 dark:text-white hover:border-violet-400 dark:hover:border-violet-500 focus:ring-2 focus:ring-violet-500 focus:border-transparent transition-all min-w-[140px]"
          >
            <span className="text-sm font-medium">{getPlatformFilterText()}</span>
            <ChevronDown className={`w-4 h-4 text-gray-500 transition-transform ${isPlatformDropdownOpen ? 'rotate-180' : ''}`} />
          </button>

          {isPlatformDropdownOpen && (
            <div className="absolute top-full left-0 mt-2 w-56 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl shadow-xl z-50 overflow-hidden animate-in fade-in slide-in-from-top-2 duration-200">
              <div className="p-2">
                {/* Select All / Clear All */}
                <div className="flex items-center justify-between px-3 py-2 border-b border-gray-100 dark:border-gray-700 mb-1">
                  <button
                    onClick={() => setSelectedPlatforms(platformOptions.map(p => p.value))}
                    className="text-xs font-medium text-violet-600 dark:text-violet-400 hover:text-violet-700 dark:hover:text-violet-300 transition-colors"
                  >
                    전체 선택
                  </button>
                  <button
                    onClick={() => setSelectedPlatforms([])}
                    className="text-xs font-medium text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 transition-colors"
                  >
                    선택 해제
                  </button>
                </div>

                {/* Platform Options */}
                {platformOptions.map((platform) => (
                  <button
                    key={platform.value}
                    onClick={() => togglePlatform(platform.value)}
                    className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700/50 transition-colors"
                  >
                    <div className={`w-5 h-5 rounded border-2 flex items-center justify-center transition-colors ${
                      selectedPlatforms.includes(platform.value)
                        ? 'bg-violet-600 border-violet-600'
                        : 'border-gray-300 dark:border-gray-600'
                    }`}>
                      {selectedPlatforms.includes(platform.value) && (
                        <Check className="w-3 h-3 text-white" />
                      )}
                    </div>
                    <span className="text-gray-600 dark:text-gray-400">
                      {platform.icon}
                    </span>
                    <span className="text-sm font-medium text-gray-900 dark:text-white">
                      {platform.label}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* References Grid */}
      {isLoading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-8 h-8 animate-spin text-violet-500" />
        </div>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {filteredReferences.length === 0 ? (
            <div className="col-span-full text-center py-16 bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700">
              <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-gray-100 dark:bg-gray-700 flex items-center justify-center">
                <ImageIcon className="w-8 h-8 text-gray-400" />
              </div>
              <p className="text-gray-500 dark:text-gray-400 font-medium">
                저장된 레퍼런스가 없습니다
              </p>
              <button
                onClick={() => setIsModalOpen(true)}
                className="text-violet-600 dark:text-violet-400 hover:underline mt-2 font-medium"
              >
                첫 레퍼런스 추가하기
              </button>
            </div>
          ) : (
            filteredReferences.map((ref) => {
              const isAnalyzing = ref.status !== "completed" && ref.status !== "failed";
              return (
              <div
                key={ref.id}
                onClick={() => {
                  if (isAnalyzing) {
                    toast.info("분석이 완료되면 확인할 수 있습니다");
                    return;
                  }
                  router.push(`/references/${ref.id}`);
                }}
                className={`group bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 overflow-hidden transition-all duration-300 ${
                  isAnalyzing
                    ? "cursor-not-allowed opacity-70"
                    : "cursor-pointer hover:shadow-xl hover:shadow-violet-500/10 hover:-translate-y-1"
                }`}
              >
                <div className="aspect-square bg-gradient-to-br from-violet-600 via-indigo-600 to-purple-700 relative overflow-hidden">
                  {ref.thumbnailUrl ? (
                    <img
                      src={ref.thumbnailUrl}
                      alt="Reference"
                      className="absolute inset-0 w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                    />
                  ) : (
                    <div className="w-full h-full flex flex-col items-center justify-center p-4">
                      <div className="w-12 h-12 rounded-xl bg-white/20 backdrop-blur-sm flex items-center justify-center mb-3">
                        {ref.type === "video" || ref.type === "shorts" ? (
                          <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                        ) : ref.type === "carousel" ? (
                          <Layers className="w-6 h-6 text-white" />
                        ) : (
                          <ImageIcon className="w-6 h-6 text-white" />
                        )}
                      </div>
                      <span className="text-white/90 text-xs font-semibold tracking-wide">AI Content</span>
                      <span className="text-white/70 text-[10px] font-medium">Factory</span>
                    </div>
                  )}
                  {/* Platform badge */}
                  <div className="absolute top-3 left-3 px-2.5 py-1 bg-black/60 dark:bg-white/20 backdrop-blur-sm text-white text-xs font-medium rounded-lg">
                    {ref.source === "instagram" && "Instagram"}
                    {ref.source === "facebook" && "Facebook"}
                    {ref.source === "pinterest" && "Pinterest"}
                    {ref.source === "youtube" && "YouTube"}
                    {ref.source === "upload" && "업로드"}
                  </div>
                  {/* Status badge */}
                  <div className="absolute top-3 right-3 flex items-center gap-1.5 px-2.5 py-1 bg-white/90 dark:bg-gray-900/90 backdrop-blur-sm rounded-lg">
                    {getStatusIcon(ref.status)}
                    <span className="text-xs font-medium text-gray-700 dark:text-gray-300">
                      {getStatusText(ref.status)}
                    </span>
                  </div>
                </div>
                <div className="p-4">
                  <div className="flex items-center justify-between">
                    <p className="text-sm font-semibold text-gray-900 dark:text-white truncate flex-1 mr-2">
                      {ref.title || "제목 없음"}
                    </p>
                    <span className="text-xs font-medium text-gray-500 dark:text-gray-400 whitespace-nowrap">
                      {ref.type === "carousel" && "캐러셀"}
                      {ref.type === "single" && "이미지"}
                      {ref.type === "story" && "세로형"}
                      {ref.type === "video" && "영상"}
                      {ref.type === "shorts" && "쇼츠"}
                    </span>
                  </div>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{ref.createdAt}</p>
                </div>
              </div>
            );})
          )}
        </div>
      )}

      {/* Add Reference Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50">
          <div
            className="bg-white dark:bg-gray-900 rounded-3xl p-8 w-full max-w-md shadow-2xl border border-gray-200 dark:border-gray-800 animate-in fade-in zoom-in-95 duration-200"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="flex items-center justify-between mb-8">
              <h3 className="text-xl font-bold text-gray-900 dark:text-white">새 레퍼런스 추가</h3>
              <button
                onClick={() => setIsModalOpen(false)}
                className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-xl transition-colors"
              >
                <X className="w-5 h-5 text-gray-500" />
              </button>
            </div>

            <div className="space-y-8">
              {/* Link Input */}
              <div>
                <label className="flex items-center gap-2 text-sm font-semibold text-gray-900 dark:text-white mb-3">
                  <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-500 to-indigo-500 flex items-center justify-center">
                    <LinkIcon className="w-4 h-4 text-white" />
                  </div>
                  링크로 추가
                </label>
                <div className="flex gap-3">
                  <input
                    type="url"
                    value={linkInput}
                    onChange={(e) => setLinkInput(e.target.value)}
                    placeholder="Instagram, Pinterest, YouTube 링크 입력..."
                    className="flex-1 px-4 py-3 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl text-gray-900 dark:text-white placeholder:text-gray-400 focus:ring-2 focus:ring-violet-500 focus:border-transparent transition-all"
                    onKeyDown={(e) => e.key === "Enter" && handleAddLink()}
                  />
                  <button
                    onClick={handleAddLink}
                    disabled={isAnalyzing || !linkInput.trim()}
                    className="px-5 py-3 bg-gradient-to-r from-violet-600 to-indigo-600 text-white rounded-xl disabled:opacity-50 disabled:cursor-not-allowed hover:from-violet-700 hover:to-indigo-700 transition-all font-medium shadow-lg shadow-violet-500/25"
                  >
                    {isAnalyzing ? (
                      <Loader2 className="w-5 h-5 animate-spin" />
                    ) : (
                      "분석"
                    )}
                  </button>
                </div>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                  Instagram, Facebook, Pinterest, YouTube 링크를 지원합니다
                </p>
              </div>

              {/* Divider */}
              <div className="relative">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-gray-200 dark:border-gray-700" />
                </div>
                <div className="relative flex justify-center">
                  <span className="px-4 bg-white dark:bg-gray-900 text-sm text-gray-500 dark:text-gray-400 font-medium">
                    또는
                  </span>
                </div>
              </div>

              {/* File Upload */}
              <div>
                <label className="flex items-center gap-2 text-sm font-semibold text-gray-900 dark:text-white mb-3">
                  <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-emerald-500 to-teal-500 flex items-center justify-center">
                    <Upload className="w-4 h-4 text-white" />
                  </div>
                  이미지 업로드
                </label>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  multiple
                  onChange={handleFileUpload}
                  className="hidden"
                />
                <button
                  onClick={() => fileInputRef.current?.click()}
                  disabled={isAnalyzing}
                  className="w-full py-10 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-2xl hover:border-violet-400 dark:hover:border-violet-500 hover:bg-violet-50 dark:hover:bg-violet-900/10 transition-all group"
                >
                  {isAnalyzing ? (
                    <Loader2 className="w-10 h-10 mx-auto animate-spin text-violet-500" />
                  ) : (
                    <>
                      <div className="w-14 h-14 mx-auto mb-3 rounded-2xl bg-gray-100 dark:bg-gray-800 flex items-center justify-center group-hover:bg-violet-100 dark:group-hover:bg-violet-900/30 transition-colors">
                        <Upload className="w-6 h-6 text-gray-400 group-hover:text-violet-500 transition-colors" />
                      </div>
                      <p className="text-sm text-gray-500 dark:text-gray-400 font-medium">
                        클릭하여 이미지 업로드
                      </p>
                      <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                        JPG, PNG, WEBP 지원
                      </p>
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
