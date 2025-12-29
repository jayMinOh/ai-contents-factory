"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import {
  Users,
  CheckCircle2,
  XCircle,
  Clock,
  Trash2,
  Shield,
  User as UserIcon,
  ArrowLeft,
  RefreshCw,
  Loader2,
} from "lucide-react";
import { adminService, type User, type UserStatus } from "@/lib/auth";
import { toast } from "sonner";
import { formatDistanceToNow } from "date-fns";
import { ko } from "date-fns/locale";

type TabType = "all" | "pending" | "approved" | "rejected";

const statusConfig: Record<UserStatus, { label: string; color: string; bgColor: string; icon: typeof Clock }> = {
  pending: { label: "대기 중", color: "text-amber-500", bgColor: "bg-amber-500/10", icon: Clock },
  approved: { label: "승인됨", color: "text-emerald-500", bgColor: "bg-emerald-500/10", icon: CheckCircle2 },
  rejected: { label: "거부됨", color: "text-red-500", bgColor: "bg-red-500/10", icon: XCircle },
};

export default function AdminPage() {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<TabType>("all");

  // Fetch users
  const { data: users, isLoading, error, refetch } = useQuery({
    queryKey: ["admin-users"],
    queryFn: () => adminService.listUsers(),
  });

  // Mutations
  const approveMutation = useMutation({
    mutationFn: adminService.approveUser,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-users"] });
      toast.success("사용자를 승인했습니다.");
    },
    onError: () => toast.error("승인에 실패했습니다."),
  });

  const rejectMutation = useMutation({
    mutationFn: adminService.rejectUser,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-users"] });
      toast.success("사용자를 거부했습니다.");
    },
    onError: () => toast.error("거부에 실패했습니다."),
  });

  const deleteMutation = useMutation({
    mutationFn: adminService.deleteUser,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-users"] });
      toast.success("사용자를 삭제했습니다.");
    },
    onError: () => toast.error("삭제에 실패했습니다."),
  });

  // Filter users by tab
  const filteredUsers = users?.filter((user) => {
    if (activeTab === "all") return true;
    return user.status === activeTab;
  }) || [];

  // Count by status
  const counts = {
    all: users?.length || 0,
    pending: users?.filter((u) => u.status === "pending").length || 0,
    approved: users?.filter((u) => u.status === "approved").length || 0,
    rejected: users?.filter((u) => u.status === "rejected").length || 0,
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return "-";
    try {
      const utcDateString = dateString.endsWith("Z") ? dateString : dateString + "Z";
      return formatDistanceToNow(new Date(utcDateString), { addSuffix: true, locale: ko });
    } catch {
      return dateString;
    }
  };

  const handleApprove = (userId: string) => {
    if (confirm("이 사용자를 승인하시겠습니까?")) {
      approveMutation.mutate(userId);
    }
  };

  const handleReject = (userId: string) => {
    if (confirm("이 사용자를 거부하시겠습니까?")) {
      rejectMutation.mutate(userId);
    }
  };

  const handleDelete = (userId: string) => {
    if (confirm("이 사용자를 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.")) {
      deleteMutation.mutate(userId);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <div className="border-b border-default bg-card/50 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-6 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link
                href="/"
                className="p-2 rounded-lg hover:bg-muted/50 transition-colors"
              >
                <ArrowLeft className="w-5 h-5 text-muted" />
              </Link>
              <div>
                <h1 className="text-2xl font-bold text-foreground flex items-center gap-2">
                  <Shield className="w-6 h-6 text-accent-500" />
                  사용자 관리
                </h1>
                <p className="text-muted text-sm mt-1">
                  사용자 승인 및 관리
                </p>
              </div>
            </div>
            <button
              onClick={() => refetch()}
              className="flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium border border-default bg-card hover:bg-muted/50 transition-all"
            >
              <RefreshCw className="w-4 h-4" />
              새로고침
            </button>
          </div>

          {/* Tabs */}
          <div className="flex gap-1 mt-6 p-1 bg-muted/50 rounded-xl w-fit">
            {(["all", "pending", "approved", "rejected"] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all ${
                  activeTab === tab
                    ? "bg-background text-foreground shadow-sm"
                    : "text-muted hover:text-foreground"
                }`}
              >
                {tab === "all" && <Users className="w-4 h-4" />}
                {tab === "pending" && <Clock className="w-4 h-4" />}
                {tab === "approved" && <CheckCircle2 className="w-4 h-4" />}
                {tab === "rejected" && <XCircle className="w-4 h-4" />}
                {tab === "all" && "전체"}
                {tab === "pending" && "대기 중"}
                {tab === "approved" && "승인됨"}
                {tab === "rejected" && "거부됨"}
                {counts[tab] > 0 && (
                  <span
                    className={`px-2 py-0.5 text-xs rounded-full ${
                      tab === "pending"
                        ? "bg-amber-500 text-white"
                        : tab === "approved"
                        ? "bg-emerald-500 text-white"
                        : tab === "rejected"
                        ? "bg-red-500 text-white"
                        : "bg-muted text-foreground"
                    }`}
                  >
                    {counts[tab]}
                  </span>
                )}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-6xl mx-auto px-6 py-8">
        {isLoading ? (
          <div className="flex flex-col items-center justify-center py-20">
            <Loader2 className="w-8 h-8 animate-spin text-accent-500 mb-4" />
            <p className="text-muted">사용자 목록 불러오는 중...</p>
          </div>
        ) : error ? (
          <div className="flex flex-col items-center justify-center py-20">
            <XCircle className="w-12 h-12 text-red-500 mb-4" />
            <p className="text-muted mb-4">사용자 목록을 불러오는데 실패했습니다</p>
            <button onClick={() => refetch()} className="btn-secondary">
              다시 시도
            </button>
          </div>
        ) : filteredUsers.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20">
            <Users className="w-12 h-12 text-muted mb-4" />
            <p className="text-muted">
              {activeTab === "all"
                ? "등록된 사용자가 없습니다"
                : `${statusConfig[activeTab as UserStatus]?.label || ""} 사용자가 없습니다`}
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {filteredUsers.map((user) => {
              const status = statusConfig[user.status];
              const StatusIcon = status.icon;

              return (
                <div
                  key={user.id}
                  className="card p-4 flex items-center justify-between"
                >
                  {/* User Info */}
                  <div className="flex items-center gap-4">
                    {user.picture_url ? (
                      <img
                        src={user.picture_url}
                        alt={user.name}
                        className="w-12 h-12 rounded-full"
                      />
                    ) : (
                      <div className="w-12 h-12 rounded-full bg-muted flex items-center justify-center">
                        <UserIcon className="w-6 h-6 text-muted" />
                      </div>
                    )}
                    <div>
                      <div className="flex items-center gap-2">
                        <p className="font-medium text-foreground">{user.name}</p>
                        {user.role === "admin" && (
                          <span className="px-2 py-0.5 text-xs font-medium bg-accent-500/10 text-accent-500 rounded-full">
                            Admin
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-muted">{user.email}</p>
                      <p className="text-xs text-muted mt-1">
                        가입: {formatDate(user.created_at)}
                        {user.last_login && ` • 마지막 로그인: ${formatDate(user.last_login)}`}
                      </p>
                    </div>
                  </div>

                  {/* Status & Actions */}
                  <div className="flex items-center gap-4">
                    {/* Status Badge */}
                    <div
                      className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg ${status.bgColor}`}
                    >
                      <StatusIcon className={`w-4 h-4 ${status.color}`} />
                      <span className={`text-sm font-medium ${status.color}`}>
                        {status.label}
                      </span>
                    </div>

                    {/* Actions */}
                    <div className="flex items-center gap-2">
                      {user.status === "pending" && (
                        <>
                          <button
                            onClick={() => handleApprove(user.id)}
                            disabled={approveMutation.isPending}
                            className="p-2 rounded-lg bg-emerald-500/10 text-emerald-500 hover:bg-emerald-500/20 transition-colors"
                            title="승인"
                          >
                            <CheckCircle2 className="w-5 h-5" />
                          </button>
                          <button
                            onClick={() => handleReject(user.id)}
                            disabled={rejectMutation.isPending}
                            className="p-2 rounded-lg bg-red-500/10 text-red-500 hover:bg-red-500/20 transition-colors"
                            title="거부"
                          >
                            <XCircle className="w-5 h-5" />
                          </button>
                        </>
                      )}
                      {user.status === "rejected" && (
                        <button
                          onClick={() => handleApprove(user.id)}
                          disabled={approveMutation.isPending}
                          className="p-2 rounded-lg bg-emerald-500/10 text-emerald-500 hover:bg-emerald-500/20 transition-colors"
                          title="승인으로 변경"
                        >
                          <CheckCircle2 className="w-5 h-5" />
                        </button>
                      )}
                      {user.role !== "admin" && (
                        <button
                          onClick={() => handleDelete(user.id)}
                          disabled={deleteMutation.isPending}
                          className="p-2 rounded-lg hover:bg-red-500/10 text-muted hover:text-red-500 transition-colors"
                          title="삭제"
                        >
                          <Trash2 className="w-5 h-5" />
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
