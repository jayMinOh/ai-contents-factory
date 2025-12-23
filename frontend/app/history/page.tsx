"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  Clock,
  CheckCircle2,
  Image as ImageIcon,
  Layers,
  Smartphone,
  Megaphone,
  BookOpen,
  Sparkles,
  ChevronRight,
  Loader2,
  AlertCircle,
  RefreshCw,
  Trash2,
  Play,
} from "lucide-react";
import { imageProjectApi, ImageProject } from "@/lib/api";
import { toast } from "sonner";
import { formatDistanceToNow } from "date-fns";
import { ko } from "date-fns/locale";

type TabType = "in_progress" | "completed";

const contentTypeConfig = {
  single: { label: "단일 이미지", icon: ImageIcon, gradient: "from-accent-500 to-accent-600" },
  carousel: { label: "캐러셀", icon: Layers, gradient: "from-violet-500 to-purple-600" },
  story: { label: "세로형", icon: Smartphone, gradient: "from-cyan-500 to-blue-600" },
};

const purposeConfig = {
  ad: { label: "광고/홍보", icon: Megaphone },
  info: { label: "정보성", icon: BookOpen },
  lifestyle: { label: "일상/감성", icon: Sparkles },
};

const statusConfig: Record<string, { label: string; color: string; bgColor: string }> = {
  draft: { label: "준비 중", color: "text-slate-500", bgColor: "bg-slate-500/10" },
  generating: { label: "생성 중", color: "text-amber-500", bgColor: "bg-amber-500/10" },
  completed: { label: "완료", color: "text-emerald-500", bgColor: "bg-emerald-500/10" },
  failed: { label: "실패", color: "text-red-500", bgColor: "bg-red-500/10" },
};

export default function HistoryPage() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<TabType>("in_progress");

  // Fetch all projects
  const { data: projects, isLoading, error, refetch } = useQuery({
    queryKey: ["imageProjects"],
    queryFn: () => imageProjectApi.list({ limit: 100 }),
  });

  // Filter projects by status
  const inProgressProjects = projects?.filter(
    (p) => p.status === "draft" || p.status === "generating"
  ) || [];

  const completedProjects = projects?.filter(
    (p) => p.status === "completed" || p.status === "failed"
  ) || [];

  const displayProjects = activeTab === "in_progress" ? inProgressProjects : completedProjects;

  // Handle continue project
  const handleContinueProject = (project: ImageProject) => {
    // Store project data in sessionStorage
    sessionStorage.setItem("resumeProject", JSON.stringify(project));

    // Navigate to create page with project context
    router.push(`/create?resume=${project.id}&type=${project.content_type}`);
  };

  // Handle delete project
  const handleDeleteProject = async (projectId: string, e: React.MouseEvent) => {
    e.stopPropagation();

    if (!confirm("이 프로젝트를 삭제하시겠습니까?")) return;

    try {
      await imageProjectApi.delete(projectId);
      toast.success("프로젝트가 삭제되었습니다");
      refetch();
    } catch (error) {
      toast.error("삭제에 실패했습니다");
    }
  };

  // Format date
  const formatDate = (dateString?: string) => {
    if (!dateString) return "";
    try {
      return formatDistanceToNow(new Date(dateString), { addSuffix: true, locale: ko });
    } catch {
      return dateString;
    }
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <div className="border-b border-default bg-card/50 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-6 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-foreground">콘텐츠 히스토리</h1>
              <p className="text-muted text-sm mt-1">생성 중이거나 완료된 프로젝트를 관리하세요</p>
            </div>
            <Link href="/create" className="btn-primary flex items-center gap-2">
              <Sparkles className="w-4 h-4" />
              새 콘텐츠 만들기
            </Link>
          </div>

          {/* Tabs */}
          <div className="flex gap-1 mt-6 p-1 bg-muted/50 rounded-xl w-fit">
            <button
              onClick={() => setActiveTab("in_progress")}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all ${
                activeTab === "in_progress"
                  ? "bg-background text-foreground shadow-sm"
                  : "text-muted hover:text-foreground"
              }`}
            >
              <Clock className="w-4 h-4" />
              진행 중
              {inProgressProjects.length > 0 && (
                <span className="px-2 py-0.5 text-xs bg-accent-500 text-white rounded-full">
                  {inProgressProjects.length}
                </span>
              )}
            </button>
            <button
              onClick={() => setActiveTab("completed")}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all ${
                activeTab === "completed"
                  ? "bg-background text-foreground shadow-sm"
                  : "text-muted hover:text-foreground"
              }`}
            >
              <CheckCircle2 className="w-4 h-4" />
              완료됨
              {completedProjects.length > 0 && (
                <span className="px-2 py-0.5 text-xs bg-emerald-500 text-white rounded-full">
                  {completedProjects.length}
                </span>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-6xl mx-auto px-6 py-8">
        {isLoading ? (
          <div className="flex flex-col items-center justify-center py-20">
            <Loader2 className="w-8 h-8 animate-spin text-accent-500 mb-4" />
            <p className="text-muted">프로젝트 불러오는 중...</p>
          </div>
        ) : error ? (
          <div className="flex flex-col items-center justify-center py-20">
            <AlertCircle className="w-12 h-12 text-red-500 mb-4" />
            <p className="text-muted mb-4">프로젝트를 불러오는데 실패했습니다</p>
            <button onClick={() => refetch()} className="btn-secondary flex items-center gap-2">
              <RefreshCw className="w-4 h-4" />
              다시 시도
            </button>
          </div>
        ) : displayProjects.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20">
            <div className="w-20 h-20 rounded-2xl bg-muted/50 flex items-center justify-center mb-6">
              {activeTab === "in_progress" ? (
                <Clock className="w-10 h-10 text-muted" />
              ) : (
                <CheckCircle2 className="w-10 h-10 text-muted" />
              )}
            </div>
            <p className="text-lg font-medium text-foreground mb-2">
              {activeTab === "in_progress" ? "진행 중인 프로젝트가 없습니다" : "완료된 프로젝트가 없습니다"}
            </p>
            <p className="text-muted text-sm mb-6">
              {activeTab === "in_progress"
                ? "새 콘텐츠를 만들어보세요"
                : "콘텐츠를 생성하면 여기에 표시됩니다"}
            </p>
            <Link href="/create" className="btn-primary">
              콘텐츠 만들기
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {displayProjects.map((project) => {
              const contentType = contentTypeConfig[project.content_type];
              const purpose = purposeConfig[project.purpose];
              const status = statusConfig[project.status] || statusConfig.draft;
              const ContentIcon = contentType.icon;
              const PurposeIcon = purpose.icon;
              const firstImage = project.generated_images?.[0]?.image_url;

              return (
                <div
                  key={project.id}
                  onClick={() => handleContinueProject(project)}
                  className="group relative bg-card border border-default rounded-2xl overflow-hidden cursor-pointer transition-all duration-300 hover:border-accent-500/50 hover:shadow-lg hover:shadow-accent-500/5"
                >
                  {/* Thumbnail */}
                  <div className="aspect-[4/3] bg-gradient-to-br from-muted/50 to-muted relative overflow-hidden">
                    {firstImage ? (
                      <img
                        src={`http://localhost:8000${firstImage}`}
                        alt={project.title}
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                      />
                    ) : (
                      <div className={`w-full h-full bg-gradient-to-br ${contentType.gradient} opacity-20 flex items-center justify-center`}>
                        <ContentIcon className="w-16 h-16 text-foreground/20" />
                      </div>
                    )}

                    {/* Status Badge */}
                    <div className={`absolute top-3 left-3 px-2.5 py-1 rounded-lg text-xs font-medium ${status.bgColor} ${status.color} backdrop-blur-sm`}>
                      {project.status === "generating" && (
                        <Loader2 className="w-3 h-3 animate-spin inline mr-1" />
                      )}
                      {status.label}
                    </div>

                    {/* Content Type Badge */}
                    <div className="absolute top-3 right-3 px-2.5 py-1 rounded-lg text-xs font-medium bg-black/50 text-white backdrop-blur-sm flex items-center gap-1">
                      <ContentIcon className="w-3 h-3" />
                      {contentType.label}
                    </div>

                    {/* Hover Overlay */}
                    <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-3">
                      {project.status !== "completed" && project.status !== "failed" ? (
                        <button className="px-4 py-2 bg-accent-500 text-white rounded-lg font-medium flex items-center gap-2 hover:bg-accent-600 transition-colors">
                          <Play className="w-4 h-4" />
                          이어서 작업
                        </button>
                      ) : (
                        <button className="px-4 py-2 bg-white/20 text-white rounded-lg font-medium flex items-center gap-2 hover:bg-white/30 transition-colors backdrop-blur-sm">
                          상세 보기
                          <ChevronRight className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                  </div>

                  {/* Info */}
                  <div className="p-4">
                    <h3 className="font-semibold text-foreground truncate group-hover:text-accent-500 transition-colors">
                      {project.title || "제목 없음"}
                    </h3>

                    <div className="flex items-center gap-2 mt-2 text-xs text-muted">
                      <PurposeIcon className="w-3.5 h-3.5" />
                      <span>{purpose.label}</span>
                      <span className="text-border">•</span>
                      <span>{project.method === "reference" ? "레퍼런스" : "프롬프트"}</span>
                    </div>

                    <div className="flex items-center justify-between mt-3 pt-3 border-t border-default">
                      <span className="text-xs text-muted">
                        {formatDate(project.updated_at || project.created_at)}
                      </span>

                      <button
                        onClick={(e) => handleDeleteProject(project.id, e)}
                        className="p-1.5 text-muted hover:text-red-500 hover:bg-red-500/10 rounded-lg transition-colors opacity-0 group-hover:opacity-100"
                        title="삭제"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>

                  {/* Progress indicator for generating */}
                  {project.status === "generating" && (
                    <div className="absolute bottom-0 left-0 right-0 h-1 bg-muted overflow-hidden">
                      <div className="h-full bg-accent-500 animate-pulse" style={{ width: "60%" }} />
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
