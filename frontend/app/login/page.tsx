"use client";

import { useEffect, useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Loader2, Sparkles } from "lucide-react";
import { authService, getGoogleOAuthUrl } from "@/lib/auth";
import { toast } from "sonner";

// Track processed codes to prevent duplicate requests
const processedCodes = new Set<string>();

function LoginContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [isLoading, setIsLoading] = useState(false);

  // Handle Google OAuth callback
  useEffect(() => {
    const code = searchParams.get("code");
    if (code && !processedCodes.has(code)) {
      processedCodes.add(code);
      handleGoogleCallback(code);
    }
  }, [searchParams]);

  const handleGoogleCallback = async (code: string) => {
    try {
      setIsLoading(true);
      const response = await authService.googleAuth(code);

      toast.success(response.message);

      // Redirect based on user status
      if (response.user.status === "approved") {
        router.push("/");
      } else if (response.user.status === "pending") {
        router.push("/pending");
      } else {
        toast.error("계정이 거부되었습니다.");
      }
    } catch (error: unknown) {
      console.error("Login error:", error);
      toast.error("로그인에 실패했습니다. 다시 시도해주세요.");
      // Clear the code from URL
      router.replace("/login");
    } finally {
      setIsLoading(false);
    }
  };

  const handleGoogleLogin = () => {
    setIsLoading(true);
    window.location.href = getGoogleOAuthUrl();
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="w-full max-w-md p-8">
        {/* Logo & Title */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-accent-500 to-electric-600 mb-6">
            <Sparkles className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-foreground mb-2">
            AI Video Marketing
          </h1>
          <p className="text-muted">
            AI 기반 마케팅 콘텐츠 생성 플랫폼
          </p>
        </div>

        {/* Login Card */}
        <div className="card p-8">
          <h2 className="text-xl font-semibold text-foreground text-center mb-6">
            로그인
          </h2>

          {isLoading ? (
            <div className="flex flex-col items-center py-8">
              <Loader2 className="w-8 h-8 animate-spin text-accent-500 mb-4" />
              <p className="text-muted">로그인 처리 중...</p>
            </div>
          ) : (
            <button
              onClick={handleGoogleLogin}
              className="w-full flex items-center justify-center gap-3 px-6 py-3.5 rounded-xl border border-default bg-card hover:bg-muted/50 transition-all font-medium"
            >
              <svg className="w-5 h-5" viewBox="0 0 24 24">
                <path
                  fill="#4285F4"
                  d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                />
                <path
                  fill="#34A853"
                  d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                />
                <path
                  fill="#FBBC05"
                  d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                />
                <path
                  fill="#EA4335"
                  d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                />
              </svg>
              Google 계정으로 로그인
            </button>
          )}

          <p className="text-xs text-muted text-center mt-6">
            로그인하면 서비스 이용약관 및 개인정보처리방침에 동의하게 됩니다.
          </p>
        </div>

        {/* Footer */}
        <p className="text-center text-sm text-muted mt-8">
          처음 가입하시나요? 관리자 승인 후 이용 가능합니다.
        </p>
      </div>
    </div>
  );
}

function LoginLoading() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="flex flex-col items-center">
        <Loader2 className="w-8 h-8 animate-spin text-accent-500 mb-4" />
        <p className="text-muted">로딩 중...</p>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={<LoginLoading />}>
      <LoginContent />
    </Suspense>
  );
}
