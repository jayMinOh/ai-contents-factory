"use client";

import { useState, useRef } from "react";
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
  Filter,
  Trash2,
  ExternalLink,
} from "lucide-react";
import { toast } from "sonner";

// Reference types
type ReferenceType = "single" | "carousel" | "story";
type ReferenceSource = "instagram" | "facebook" | "upload";

interface Reference {
  id: string;
  type: ReferenceType;
  source: ReferenceSource;
  sourceUrl?: string;
  thumbnailUrl: string;
  analysis: {
    composition: string;
    colorScheme: string;
    style: string;
    elements: string[];
  };
  createdAt: string;
}

// Mock data
const mockReferences: Reference[] = [
  {
    id: "1",
    type: "carousel",
    source: "instagram",
    sourceUrl: "https://instagram.com/p/xxx",
    thumbnailUrl: "",
    analysis: {
      composition: "중앙 집중형",
      colorScheme: "따뜻한 톤, 베이지 계열",
      style: "미니멀, 클린",
      elements: ["제품", "텍스트", "배경"],
    },
    createdAt: "2024-12-18",
  },
];

export default function ReferencesPage() {
  const [references, setReferences] = useState<Reference[]>(mockReferences);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [linkInput, setLinkInput] = useState("");
  const [selectedReference, setSelectedReference] = useState<Reference | null>(null);
  const [filterType, setFilterType] = useState<ReferenceType | "all">("all");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleAddLink = async () => {
    if (!linkInput.trim()) {
      toast.error("링크를 입력해주세요");
      return;
    }

    setIsAnalyzing(true);
    toast.info("링크 분석 중...");

    // TODO: Call actual API to analyze SNS link
    await new Promise((resolve) => setTimeout(resolve, 2000));

    // Mock result
    const newReference: Reference = {
      id: `ref-${Date.now()}`,
      type: "carousel",
      source: linkInput.includes("instagram") ? "instagram" : "facebook",
      sourceUrl: linkInput,
      thumbnailUrl: "",
      analysis: {
        composition: "좌우 대칭형",
        colorScheme: "차가운 톤, 블루 계열",
        style: "모던, 세련됨",
        elements: ["제품", "모델", "텍스트"],
      },
      createdAt: new Date().toISOString().split("T")[0],
    };

    setReferences((prev) => [newReference, ...prev]);
    setLinkInput("");
    setIsAnalyzing(false);
    setIsModalOpen(false);
    toast.success("레퍼런스가 추가되었습니다!");
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    setIsAnalyzing(true);
    toast.info("이미지 분석 중...");

    // TODO: Call actual API to analyze uploaded image
    await new Promise((resolve) => setTimeout(resolve, 2000));

    // Mock result
    const newReference: Reference = {
      id: `ref-${Date.now()}`,
      type: "single",
      source: "upload",
      thumbnailUrl: URL.createObjectURL(files[0]),
      analysis: {
        composition: "중앙 배치",
        colorScheme: "자연색, 그린 계열",
        style: "자연스러움, 캐주얼",
        elements: ["제품", "배경"],
      },
      createdAt: new Date().toISOString().split("T")[0],
    };

    setReferences((prev) => [newReference, ...prev]);
    setIsAnalyzing(false);
    setIsModalOpen(false);
    toast.success("레퍼런스가 추가되었습니다!");

    // Reset file input
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const handleDelete = (id: string) => {
    setReferences((prev) => prev.filter((r) => r.id !== id));
    setSelectedReference(null);
    toast.success("레퍼런스가 삭제되었습니다");
  };

  const filteredReferences = filterType === "all"
    ? references
    : references.filter((r) => r.type === filterType);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">레퍼런스 라이브러리</h1>
          <p className="text-gray-500 mt-1">SNS 콘텐츠를 분석하고 스타일을 저장하세요</p>
        </div>
        <button
          onClick={() => setIsModalOpen(true)}
          className="flex items-center gap-2 bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700"
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
            placeholder="레퍼런스 검색..."
            className="w-full pl-10 pr-4 py-2 border rounded-lg"
          />
        </div>
        <select
          value={filterType}
          onChange={(e) => setFilterType(e.target.value as ReferenceType | "all")}
          className="px-4 py-2 border rounded-lg"
        >
          <option value="all">전체</option>
          <option value="single">단일 이미지</option>
          <option value="carousel">캐러셀</option>
          <option value="story">스토리</option>
        </select>
      </div>

      {/* References Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {filteredReferences.length === 0 ? (
          <div className="col-span-full text-center py-16 bg-white rounded-xl border">
            <ImageIcon className="w-12 h-12 mx-auto mb-3 text-gray-300" />
            <p className="text-gray-500">저장된 레퍼런스가 없습니다</p>
            <button
              onClick={() => setIsModalOpen(true)}
              className="text-primary-600 hover:underline mt-2"
            >
              첫 레퍼런스 추가하기
            </button>
          </div>
        ) : (
          filteredReferences.map((ref) => (
            <div
              key={ref.id}
              onClick={() => setSelectedReference(ref)}
              className={`bg-white rounded-lg border overflow-hidden cursor-pointer hover:shadow-md transition-shadow ${
                selectedReference?.id === ref.id ? "ring-2 ring-primary-500" : ""
              }`}
            >
              <div className="aspect-square bg-gray-100 relative">
                {ref.thumbnailUrl ? (
                  <Image
                    src={ref.thumbnailUrl}
                    alt="Reference"
                    fill
                    className="object-cover"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center">
                    {ref.type === "carousel" && <Layers className="w-8 h-8 text-gray-400" />}
                    {ref.type === "single" && <ImageIcon className="w-8 h-8 text-gray-400" />}
                    {ref.type === "story" && <Smartphone className="w-8 h-8 text-gray-400" />}
                  </div>
                )}
                <div className="absolute top-2 left-2 px-2 py-1 bg-black/50 text-white text-xs rounded">
                  {ref.source === "instagram" && "Instagram"}
                  {ref.source === "facebook" && "Facebook"}
                  {ref.source === "upload" && "업로드"}
                </div>
              </div>
              <div className="p-3">
                <p className="text-sm font-medium">
                  {ref.type === "carousel" && "캐러셀"}
                  {ref.type === "single" && "단일 이미지"}
                  {ref.type === "story" && "스토리"}
                </p>
                <p className="text-xs text-gray-500">{ref.createdAt}</p>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Reference Detail Panel */}
      {selectedReference && (
        <div className="fixed inset-y-0 right-0 w-96 bg-white shadow-xl border-l p-6 overflow-y-auto">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-semibold">레퍼런스 상세</h3>
            <button
              onClick={() => setSelectedReference(null)}
              className="p-1 hover:bg-gray-100 rounded"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          <div className="aspect-square bg-gray-100 rounded-lg mb-4 relative">
            {selectedReference.thumbnailUrl ? (
              <Image
                src={selectedReference.thumbnailUrl}
                alt="Reference"
                fill
                className="object-cover rounded-lg"
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center">
                <ImageIcon className="w-12 h-12 text-gray-400" />
              </div>
            )}
          </div>

          <div className="space-y-4">
            <div>
              <p className="text-sm text-gray-500">유형</p>
              <p className="font-medium">
                {selectedReference.type === "carousel" && "캐러셀"}
                {selectedReference.type === "single" && "단일 이미지"}
                {selectedReference.type === "story" && "스토리"}
              </p>
            </div>

            {selectedReference.sourceUrl && (
              <div>
                <p className="text-sm text-gray-500">원본 링크</p>
                <a
                  href={selectedReference.sourceUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary-600 hover:underline flex items-center gap-1"
                >
                  {selectedReference.source}
                  <ExternalLink className="w-4 h-4" />
                </a>
              </div>
            )}

            <div className="border-t pt-4">
              <p className="text-sm font-medium mb-2">분석 결과</p>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-500">구도</span>
                  <span>{selectedReference.analysis.composition}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">색감</span>
                  <span>{selectedReference.analysis.colorScheme}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">스타일</span>
                  <span>{selectedReference.analysis.style}</span>
                </div>
                <div>
                  <span className="text-gray-500">요소</span>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {selectedReference.analysis.elements.map((el) => (
                      <span key={el} className="px-2 py-1 bg-gray-100 rounded text-xs">
                        {el}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            <div className="flex gap-2 pt-4">
              <button
                onClick={() => handleDelete(selectedReference.id)}
                className="flex-1 py-2 border border-red-300 text-red-600 rounded-lg hover:bg-red-50 flex items-center justify-center gap-2"
              >
                <Trash2 className="w-4 h-4" />
                삭제
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Add Reference Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-full max-w-md">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-semibold">새 레퍼런스 추가</h3>
              <button
                onClick={() => setIsModalOpen(false)}
                className="p-1 hover:bg-gray-100 rounded"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-6">
              {/* Link Input */}
              <div>
                <label className="block text-sm font-medium mb-2">
                  <LinkIcon className="w-4 h-4 inline mr-1" />
                  SNS 링크
                </label>
                <div className="flex gap-2">
                  <input
                    type="url"
                    value={linkInput}
                    onChange={(e) => setLinkInput(e.target.value)}
                    placeholder="https://instagram.com/p/..."
                    className="flex-1 px-4 py-2 border rounded-lg"
                  />
                  <button
                    onClick={handleAddLink}
                    disabled={isAnalyzing || !linkInput.trim()}
                    className="px-4 py-2 bg-primary-600 text-white rounded-lg disabled:opacity-50"
                  >
                    {isAnalyzing ? (
                      <Loader2 className="w-5 h-5 animate-spin" />
                    ) : (
                      "분석"
                    )}
                  </button>
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  Instagram, Facebook 링크를 지원합니다
                </p>
              </div>

              <div className="relative">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t" />
                </div>
                <div className="relative flex justify-center text-sm">
                  <span className="px-2 bg-white text-gray-500">또는</span>
                </div>
              </div>

              {/* File Upload */}
              <div>
                <label className="block text-sm font-medium mb-2">
                  <Upload className="w-4 h-4 inline mr-1" />
                  이미지 업로드
                </label>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  onChange={handleFileUpload}
                  className="hidden"
                />
                <button
                  onClick={() => fileInputRef.current?.click()}
                  disabled={isAnalyzing}
                  className="w-full py-8 border-2 border-dashed rounded-lg hover:border-primary-300 hover:bg-primary-50 transition-colors"
                >
                  {isAnalyzing ? (
                    <Loader2 className="w-8 h-8 mx-auto animate-spin text-gray-400" />
                  ) : (
                    <>
                      <Upload className="w-8 h-8 mx-auto text-gray-400 mb-2" />
                      <p className="text-sm text-gray-500">클릭하여 이미지 업로드</p>
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
