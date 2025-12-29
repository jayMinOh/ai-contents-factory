import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "./providers";
import { ThemeProvider } from "@/components/theme-provider";
import { Toaster } from "sonner";
import NavBar from "@/components/NavBar";

export const metadata: Metadata = {
  title: "AI Content Factory",
  description: "AI를 활용한 SNS 콘텐츠 대량 생산 플랫폼",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ko" suppressHydrationWarning>
      <body className="antialiased">
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
              <NavBar />

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
