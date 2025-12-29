"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Clock, LogOut, RefreshCw, CheckCircle2 } from "lucide-react";
import { authService, type User } from "@/lib/auth";
import { toast } from "sonner";

export default function PendingPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isCheckingStatus, setIsCheckingStatus] = useState(false);

  useEffect(() => {
    checkUser();
  }, []);

  const checkUser = async () => {
    try {
      const userData = await authService.getMe();
      setUser(userData);

      // If approved, redirect to home
      if (userData.status === "approved") {
        toast.success("승인되었습니다!");
        router.push("/");
      } else if (userData.status === "rejected") {
        toast.error("계정이 거부되었습니다.");
        await authService.logout();
        router.push("/login");
      }
    } catch {
      router.push("/login");
    } finally {
      setIsLoading(false);
    }
  };

  const handleCheckStatus = async () => {
    setIsCheckingStatus(true);
    try {
      const userData = await authService.getMe();
      setUser(userData);

      if (userData.status === "approved") {
        toast.success("승인되었습니다!");
        router.push("/");
      } else if (userData.status === "rejected") {
        toast.error("계정이 거부되었습니다.");
        await authService.logout();
        router.push("/login");
      } else {
        toast.info("아직 승인 대기 중입니다.");
      }
    } catch {
      toast.error("상태 확인에 실패했습니다.");
    } finally {
      setIsCheckingStatus(false);
    }
  };

  const handleLogout = async () => {
    try {
      await authService.logout();
      router.push("/login");
    } catch {
      toast.error("로그아웃에 실패했습니다.");
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-accent-500" />
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="w-full max-w-md p-8">
        {/* Pending Card */}
        <div className="card p-8 text-center">
          {/* Icon */}
          <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-amber-500/10 mb-6">
            <Clock className="w-10 h-10 text-amber-500" />
          </div>

          {/* Title */}
          <h1 className="text-2xl font-bold text-foreground mb-2">
            승인 대기 중
          </h1>

          {/* Message */}
          <p className="text-muted mb-6">
            관리자의 승인을 기다리고 있습니다.
            <br />
            승인 후 서비스를 이용하실 수 있습니다.
          </p>

          {/* User Info */}
          {user && (
            <div className="flex items-center justify-center gap-3 p-4 rounded-xl bg-muted/50 mb-6">
              {user.picture_url ? (
                <img
                  src={user.picture_url}
                  alt={user.name}
                  className="w-10 h-10 rounded-full"
                />
              ) : (
                <div className="w-10 h-10 rounded-full bg-accent-500/20 flex items-center justify-center">
                  <span className="text-accent-500 font-medium">
                    {user.name.charAt(0)}
                  </span>
                </div>
              )}
              <div className="text-left">
                <p className="font-medium text-foreground">{user.name}</p>
                <p className="text-sm text-muted">{user.email}</p>
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex flex-col gap-3">
            <button
              onClick={handleCheckStatus}
              disabled={isCheckingStatus}
              className="btn-primary flex items-center justify-center gap-2 w-full"
            >
              {isCheckingStatus ? (
                <RefreshCw className="w-4 h-4 animate-spin" />
              ) : (
                <CheckCircle2 className="w-4 h-4" />
              )}
              승인 상태 확인
            </button>

            <button
              onClick={handleLogout}
              className="btn-secondary flex items-center justify-center gap-2 w-full"
            >
              <LogOut className="w-4 h-4" />
              로그아웃
            </button>
          </div>
        </div>

        {/* Info */}
        <p className="text-center text-sm text-muted mt-6">
          문의사항이 있으시면 관리자에게 연락해주세요.
        </p>
      </div>
    </div>
  );
}
