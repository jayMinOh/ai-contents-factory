"use client";

import { useState } from "react";
import Link from "next/link";
import Image from "next/image";
import {
  Plus,
  Clock,
  Image as ImageIcon,
  Layers,
  Smartphone,
  ArrowRight,
  Sparkles,
  TrendingUp,
  Zap,
  Target,
} from "lucide-react";

// Mock data for recent works
const recentWorks = [
  { id: "1", type: "carousel", title: "제품 소개 캐러셀", createdAt: "2024-12-18", thumbnail: null },
  { id: "2", type: "single", title: "프로모션 이미지", createdAt: "2024-12-17", thumbnail: null },
  { id: "3", type: "story", title: "신제품 스토리", createdAt: "2024-12-16", thumbnail: null },
];

const contentTypes = [
  {
    type: "single",
    icon: ImageIcon,
    label: "단일 이미지",
    desc: "1:1, 4:5 비율",
    color: "accent",
    gradient: "from-accent-500 to-accent-600",
  },
  {
    type: "carousel",
    icon: Layers,
    label: "캐러셀",
    desc: "2~10장 세트",
    color: "electric",
    gradient: "from-electric-500 to-electric-600",
  },
  {
    type: "story",
    icon: Smartphone,
    label: "스토리",
    desc: "9:16 세로형",
    color: "glow",
    gradient: "from-glow-500 to-glow-600",
  },
];

export default function HomePage() {
  const [stats] = useState({
    weeklyCount: 15,
    totalCount: 128,
    savedReferences: 24,
  });

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Hero Section */}
      <div className="relative overflow-hidden rounded-3xl">
        {/* Background */}
        <div className="absolute inset-0 bg-gradient-to-br from-accent-600/20 via-electric-600/10 to-glow-600/20" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-accent-500/20 via-transparent to-transparent" />

        {/* Content */}
        <div className="relative px-8 py-12 md:py-16">
          <div className="max-w-2xl">
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-accent-500/10 border border-accent-500/20 mb-6">
              <Sparkles className="w-4 h-4 text-accent-500 dark:text-accent-400" />
              <span className="text-sm font-medium text-accent-600 dark:text-accent-300">AI 기반 콘텐츠 생성</span>
            </div>

            <h1 className="font-display text-4xl md:text-5xl font-bold mb-4 leading-tight">
              <span className="text-foreground">SNS 콘텐츠를</span>
              <br />
              <span className="gradient-text">빠르게 대량 생산</span>
              <span className="text-foreground">하세요</span>
            </h1>

            <p className="text-lg text-muted mb-8 leading-relaxed">
              Gemini AI로 마케팅 이미지와 스토리를 자동 생성하고,
              <br className="hidden md:block" />
              직관적인 에디터로 완성도를 높여보세요.
            </p>

            <div className="flex flex-wrap gap-4">
              <Link href="/create" className="btn-primary flex items-center gap-2 text-base px-8 py-4">
                <Plus className="w-5 h-5" />
                새 콘텐츠 만들기
                <ArrowRight className="w-4 h-4 ml-1" />
              </Link>
              <Link href="/references" className="btn-secondary flex items-center gap-2 px-6 py-4">
                레퍼런스 둘러보기
              </Link>
            </div>
          </div>

          {/* Decorative elements */}
          <div className="absolute top-8 right-8 w-32 h-32 rounded-full bg-accent-500/10 blur-3xl" />
          <div className="absolute bottom-8 right-24 w-24 h-24 rounded-full bg-electric-500/10 blur-2xl" />
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 stagger-children">
        <div className="stat-card accent">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-accent-500/20 flex items-center justify-center">
              <TrendingUp className="w-6 h-6 text-accent-500 dark:text-accent-400" />
            </div>
            <div>
              <p className="text-sm text-muted mb-1">이번 주 생성</p>
              <p className="text-3xl font-bold text-foreground">{stats.weeklyCount}<span className="text-lg text-muted ml-1">개</span></p>
            </div>
          </div>
        </div>

        <div className="stat-card purple">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-electric-500/20 flex items-center justify-center">
              <ImageIcon className="w-6 h-6 text-electric-500 dark:text-electric-400" />
            </div>
            <div>
              <p className="text-sm text-muted mb-1">전체 콘텐츠</p>
              <p className="text-3xl font-bold text-foreground">{stats.totalCount}<span className="text-lg text-muted ml-1">개</span></p>
            </div>
          </div>
        </div>

        <div className="stat-card cyan">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-glow-500/20 flex items-center justify-center">
              <Target className="w-6 h-6 text-glow-600 dark:text-glow-400" />
            </div>
            <div>
              <p className="text-sm text-muted mb-1">저장된 레퍼런스</p>
              <p className="text-3xl font-bold text-foreground">{stats.savedReferences}<span className="text-lg text-muted ml-1">개</span></p>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="card">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-xl font-semibold text-foreground mb-1">빠른 생성</h2>
            <p className="text-sm text-muted">콘텐츠 유형을 선택하세요</p>
          </div>
          <Link href="/create" className="text-sm text-accent-500 hover:text-accent-600 dark:text-accent-400 dark:hover:text-accent-300 flex items-center gap-1">
            전체 보기 <ArrowRight className="w-4 h-4" />
          </Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {contentTypes.map((item) => (
            <Link
              key={item.type}
              href={`/create?type=${item.type}`}
              className="card-interactive group relative overflow-hidden"
            >
              {/* Gradient overlay on hover */}
              <div className={`absolute inset-0 bg-gradient-to-br ${item.gradient} opacity-0 group-hover:opacity-5 transition-opacity duration-300`} />

              <div className="relative flex items-center gap-4">
                <div className={`w-14 h-14 rounded-xl bg-gradient-to-br ${item.gradient} bg-opacity-20 flex items-center justify-center shadow-lg`}>
                  <item.icon className="w-7 h-7 text-white" />
                </div>
                <div className="flex-1">
                  <p className="font-semibold text-foreground mb-0.5">{item.label}</p>
                  <p className="text-sm text-muted">{item.desc}</p>
                </div>
                <ArrowRight className="w-5 h-5 text-muted group-hover:text-accent-500 group-hover:translate-x-1 transition-all" />
              </div>
            </Link>
          ))}
        </div>
      </div>

      {/* Recent Works */}
      <div className="card">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-xl font-semibold text-foreground mb-1">최근 작업</h2>
            <p className="text-sm text-muted">최근에 생성한 콘텐츠</p>
          </div>
          <Link href="/history" className="text-sm text-accent-500 hover:text-accent-600 dark:text-accent-400 dark:hover:text-accent-300 flex items-center gap-1">
            전체 보기 <ArrowRight className="w-4 h-4" />
          </Link>
        </div>

        {recentWorks.length === 0 ? (
          <div className="text-center py-16">
            <div className="w-16 h-16 rounded-2xl bg-muted flex items-center justify-center mx-auto mb-4">
              <ImageIcon className="w-8 h-8 text-muted" />
            </div>
            <p className="text-muted mb-2">아직 생성한 콘텐츠가 없습니다</p>
            <Link href="/create" className="text-accent-500 hover:text-accent-600 dark:text-accent-400 dark:hover:text-accent-300 text-sm font-medium">
              첫 콘텐츠 만들기 →
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {recentWorks.map((work, index) => (
              <div
                key={work.id}
                className="group cursor-pointer"
                style={{ animationDelay: `${index * 100}ms` }}
              >
                <div className="aspect-square rounded-xl overflow-hidden relative bg-muted border border-default mb-3">
                  {work.thumbnail ? (
                    <Image
                      src={work.thumbnail}
                      alt={work.title}
                      fill
                      className="object-cover group-hover:scale-105 transition-transform duration-500"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center group-hover:bg-muted/80 transition-colors">
                      {work.type === "carousel" && <Layers className="w-10 h-10 text-muted" />}
                      {work.type === "single" && <ImageIcon className="w-10 h-10 text-muted" />}
                      {work.type === "story" && <Smartphone className="w-10 h-10 text-muted" />}
                    </div>
                  )}

                  {/* Type badge */}
                  <div className="absolute top-2 left-2">
                    <span className={`badge ${
                      work.type === "carousel" ? "badge-purple" :
                      work.type === "story" ? "badge-cyan" : "badge-accent"
                    }`}>
                      {work.type === "carousel" && "캐러셀"}
                      {work.type === "single" && "단일"}
                      {work.type === "story" && "스토리"}
                    </span>
                  </div>
                </div>
                <p className="font-medium text-foreground truncate mb-1 group-hover:text-accent-500 transition-colors">
                  {work.title}
                </p>
                <p className="text-xs text-muted flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  {work.createdAt}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Pro Tips Section */}
      <div className="card-glow">
        <div className="flex items-start gap-4">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-accent-500 to-electric-600 flex items-center justify-center flex-shrink-0">
            <Zap className="w-6 h-6 text-white" />
          </div>
          <div>
            <h3 className="font-semibold text-foreground mb-2">Pro Tip</h3>
            <p className="text-muted text-sm leading-relaxed">
              레퍼런스를 먼저 등록하면 AI가 더 정확한 스타일로 콘텐츠를 생성합니다.
              Instagram이나 Pinterest에서 마음에 드는 이미지를 저장해두세요.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
