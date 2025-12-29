"use client";

import { useState, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { LogOut, Shield, User as UserIcon, ChevronDown } from "lucide-react";
import { authService, type User } from "@/lib/auth";
import { toast } from "sonner";

interface UserMenuProps {
  user: User;
}

export default function UserMenu({ user }: UserMenuProps) {
  const router = useRouter();
  const [isOpen, setIsOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleLogout = async () => {
    try {
      await authService.logout();
      router.push("/login");
    } catch {
      toast.error("로그아웃에 실패했습니다.");
    }
  };

  return (
    <div className="relative" ref={menuRef}>
      {/* Trigger Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-muted/50 transition-colors"
      >
        {user.picture_url ? (
          <img
            src={user.picture_url}
            alt={user.name}
            className="w-8 h-8 rounded-full"
          />
        ) : (
          <div className="w-8 h-8 rounded-full bg-accent-500/20 flex items-center justify-center">
            <UserIcon className="w-4 h-4 text-accent-500" />
          </div>
        )}
        <span className="text-sm font-medium text-foreground hidden sm:block">
          {user.name}
        </span>
        <ChevronDown
          className={`w-4 h-4 text-muted transition-transform ${
            isOpen ? "rotate-180" : ""
          }`}
        />
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div className="absolute right-0 mt-2 w-56 rounded-xl border border-default bg-card shadow-lg py-2 z-50">
          {/* User Info */}
          <div className="px-4 py-3 border-b border-default">
            <p className="font-medium text-foreground">{user.name}</p>
            <p className="text-sm text-muted truncate">{user.email}</p>
            {user.role === "admin" && (
              <span className="inline-flex items-center gap-1 mt-2 px-2 py-0.5 text-xs font-medium bg-accent-500/10 text-accent-500 rounded-full">
                <Shield className="w-3 h-3" />
                관리자
              </span>
            )}
          </div>

          {/* Menu Items */}
          <div className="py-2">
            {user.role === "admin" && (
              <Link
                href="/admin"
                onClick={() => setIsOpen(false)}
                className="flex items-center gap-3 px-4 py-2.5 text-sm text-foreground hover:bg-muted/50 transition-colors"
              >
                <Shield className="w-4 h-4 text-muted" />
                사용자 관리
              </Link>
            )}
            <button
              onClick={handleLogout}
              className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-foreground hover:bg-muted/50 transition-colors"
            >
              <LogOut className="w-4 h-4 text-muted" />
              로그아웃
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
