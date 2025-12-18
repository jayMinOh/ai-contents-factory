"use client";

/**
 * Canvas Text Editor Page
 * Phase 5: SPEC-CONTENT-FACTORY-001
 *
 * Full-featured text overlay editor for SNS content creation
 */

import { Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import Link from "next/link";
import { ChevronLeft, Save, Loader2 } from "lucide-react";
import { CanvasTextEditor } from "@/components/canvas";

function EditorContent() {
  const searchParams = useSearchParams();
  const router = useRouter();

  // Get initial canvas size from query params
  const type = searchParams.get("type") || "single";

  // Determine canvas size based on content type
  const getCanvasSize = () => {
    switch (type) {
      case "story":
        return { width: 1080, height: 1920 };
      case "carousel":
        return { width: 1080, height: 1350 };
      case "single":
      default:
        return { width: 1080, height: 1080 };
    }
  };

  const { width, height } = getCanvasSize();

  return (
    <div className="fixed inset-0 flex flex-col bg-background">
      {/* Header */}
      <header className="flex items-center justify-between px-4 py-3 border-b border-default bg-card">
        <div className="flex items-center gap-4">
          <Link
            href="/create"
            className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            <ChevronLeft className="w-4 h-4" />
            돌아가기
          </Link>
          <div className="w-px h-5 bg-border" />
          <h1 className="font-semibold text-foreground">텍스트 에디터</h1>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs text-muted-foreground px-2 py-1 rounded bg-muted">
            {type === "story"
              ? "스토리 (9:16)"
              : type === "carousel"
              ? "캐러셀 (4:5)"
              : "정사각형 (1:1)"}
          </span>
        </div>
      </header>

      {/* Editor */}
      <main className="flex-1 overflow-hidden">
        <CanvasTextEditor
          initialWidth={width}
          initialHeight={height}
          backgroundColor="#1a1f2e"
          className="h-full"
        />
      </main>
    </div>
  );
}

export default function EditPage() {
  return (
    <Suspense
      fallback={
        <div className="fixed inset-0 flex items-center justify-center bg-background">
          <div className="flex flex-col items-center gap-4">
            <Loader2 className="w-8 h-8 animate-spin text-accent-500" />
            <p className="text-muted-foreground">에디터 로딩 중...</p>
          </div>
        </div>
      }
    >
      <EditorContent />
    </Suspense>
  );
}
