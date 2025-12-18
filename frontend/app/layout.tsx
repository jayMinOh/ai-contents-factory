import type { Metadata } from "next";
import { Sora, Noto_Sans_KR } from "next/font/google";
import "./globals.css";
import { Providers } from "./providers";
import { ThemeProvider } from "@/components/theme-provider";
import { ThemeToggleDropdown } from "@/components/theme-toggle";
import { Toaster } from "sonner";
import Link from "next/link";
import { Sparkles, Home, PlusCircle, Bookmark, Building2, Zap } from "lucide-react";

// Display font - Sora (geometric, modern)
const sora = Sora({
  subsets: ["latin"],
  variable: "--font-sora",
  display: "swap",
  weight: ["400", "500", "600", "700"],
});

// Body font - Noto Sans KR (excellent Korean support)
const notoSansKr = Noto_Sans_KR({
  subsets: ["latin"],
  variable: "--font-noto-sans-kr",
  display: "swap",
  weight: ["400", "500", "600", "700"],
});

export const metadata: Metadata = {
  title: "AI Content Factory",
  description: "AI를 활용한 SNS 콘텐츠 대량 생산 플랫폼",
};

const navItems = [
  { href: "/", label: "홈", icon: Home },
  { href: "/create", label: "콘텐츠 생성", icon: PlusCircle },
  { href: "/references", label: "레퍼런스", icon: Bookmark },
  { href: "/brands", label: "브랜드 관리", icon: Building2 },
];

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ko" className={`${sora.variable} ${notoSansKr.variable}`} suppressHydrationWarning>
      <body className={`${notoSansKr.className} antialiased`}>
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          <Providers>
            <Toaster
              position="top-center"
              richColors
              toastOptions={{
                className: "!bg-card !border !border-default",
              }}
            />

            {/* Mesh gradient background */}
            <div className="fixed inset-0 mesh-bg pointer-events-none" />

            {/* Subtle noise overlay */}
            <div className="noise-overlay" />

            <div className="relative min-h-screen flex flex-col">
              {/* Navigation */}
              <nav className="glass sticky top-0 z-50">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                  <div className="flex justify-between h-16">
                    {/* Logo */}
                    <div className="flex items-center">
                      <Link
                        href="/"
                        className="flex items-center gap-3 group"
                      >
                        <div className="relative">
                          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-accent-500 to-electric-600 flex items-center justify-center shadow-glow-sm group-hover:shadow-glow-md transition-shadow duration-300">
                            <Zap className="w-5 h-5 text-white" />
                          </div>
                          <div className="absolute -top-1 -right-1 w-3 h-3 rounded-full bg-glow-400 animate-pulse" />
                        </div>
                        <div>
                          <span className="font-display font-bold text-lg tracking-tight">
                            <span className="gradient-text">AI</span>
                            <span className="text-foreground ml-1">Content Factory</span>
                          </span>
                        </div>
                      </Link>
                    </div>

                    {/* Navigation Links */}
                    <div className="flex items-center gap-1">
                      {navItems.map((item) => (
                        <Link
                          key={item.href}
                          href={item.href}
                          className="nav-link flex items-center gap-2 text-sm"
                        >
                          <item.icon className="w-4 h-4" />
                          <span className="hidden sm:inline">{item.label}</span>
                        </Link>
                      ))}
                    </div>

                    {/* Right Side */}
                    <div className="flex items-center gap-2">
                      <ThemeToggleDropdown />
                      <Link href="/create" className="btn-primary flex items-center gap-2 text-sm py-2 px-4">
                        <Sparkles className="w-4 h-4" />
                        <span className="hidden sm:inline">새 콘텐츠</span>
                      </Link>
                    </div>
                  </div>
                </div>
              </nav>

              {/* Main Content */}
              <main className="flex-1 relative">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                  {children}
                </div>
              </main>

              {/* Footer */}
              <footer className="border-t border-default py-6 mt-auto">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                  <div className="flex items-center justify-between text-sm text-muted">
                    <p>AI Content Factory</p>
                    <p>Powered by Gemini AI</p>
                  </div>
                </div>
              </footer>
            </div>
          </Providers>
        </ThemeProvider>
      </body>
    </html>
  );
}
