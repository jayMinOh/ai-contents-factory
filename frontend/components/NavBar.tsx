"use client";

import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import Link from "next/link";
import {
  Home,
  PlusCircle,
  Bookmark,
  Building2,
  Zap,
  History,
} from "lucide-react";
import { ThemeToggleDropdown } from "@/components/theme-toggle";
import UserMenu from "@/components/UserMenu";
import { authService, type User } from "@/lib/auth";

const navItems = [
  { href: "/", label: "홈", icon: Home },
  { href: "/create", label: "콘텐츠 생성", icon: PlusCircle },
  { href: "/history", label: "히스토리", icon: History },
  { href: "/references", label: "레퍼런스", icon: Bookmark },
  { href: "/brands", label: "브랜드 관리", icon: Building2 },
];

export default function NavBar() {
  const pathname = usePathname();
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Don't show nav on login/pending pages
  const isAuthPage = pathname === "/login" || pathname === "/pending";

  useEffect(() => {
    const fetchUser = async () => {
      try {
        const userData = await authService.getMe();
        setUser(userData);
      } catch {
        setUser(null);
      } finally {
        setIsLoading(false);
      }
    };

    if (!isAuthPage) {
      fetchUser();
    } else {
      setIsLoading(false);
    }
  }, [isAuthPage]);

  // Don't render nav on auth pages
  if (isAuthPage) {
    return null;
  }

  return (
    <nav className="glass sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          {/* Logo */}
          <div className="flex items-center">
            <Link href="/" className="flex items-center gap-3 group">
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
                className={`nav-link flex items-center gap-2 text-sm ${
                  pathname === item.href ? "text-accent-500" : ""
                }`}
              >
                <item.icon className="w-4 h-4" />
                <span className="hidden sm:inline">{item.label}</span>
              </Link>
            ))}
          </div>

          {/* Right Side */}
          <div className="flex items-center gap-2">
            <ThemeToggleDropdown />
            {!isLoading && user && <UserMenu user={user} />}
          </div>
        </div>
      </div>
    </nav>
  );
}
