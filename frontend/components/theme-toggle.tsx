"use client";

import { useEffect, useState } from "react";
import { useTheme } from "next-themes";
import { Sun, Moon, Monitor } from "lucide-react";

export function ThemeToggle() {
  const [mounted, setMounted] = useState(false);
  const { theme, setTheme, resolvedTheme } = useTheme();

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return (
      <button className="btn-icon w-10 h-10">
        <Monitor className="w-4 h-4" />
      </button>
    );
  }

  const cycleTheme = () => {
    if (theme === "system") {
      setTheme("light");
    } else if (theme === "light") {
      setTheme("dark");
    } else {
      setTheme("system");
    }
  };

  return (
    <button
      onClick={cycleTheme}
      className="btn-icon w-10 h-10 relative overflow-hidden group"
      aria-label="Toggle theme"
    >
      <div className="relative w-4 h-4">
        {theme === "system" && (
          <Monitor className="w-4 h-4 absolute inset-0 transition-transform group-hover:scale-110" />
        )}
        {theme === "light" && (
          <Sun className="w-4 h-4 absolute inset-0 transition-transform group-hover:rotate-45" />
        )}
        {theme === "dark" && (
          <Moon className="w-4 h-4 absolute inset-0 transition-transform group-hover:-rotate-12" />
        )}
      </div>
    </button>
  );
}

export function ThemeToggleDropdown() {
  const [mounted, setMounted] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const { theme, setTheme, resolvedTheme } = useTheme();

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return (
      <button className="btn-icon w-10 h-10">
        <Monitor className="w-4 h-4" />
      </button>
    );
  }

  const themes = [
    { value: "light", label: "라이트", icon: Sun },
    { value: "dark", label: "다크", icon: Moon },
    { value: "system", label: "시스템", icon: Monitor },
  ];

  const CurrentIcon = theme === "dark" ? Moon : theme === "light" ? Sun : Monitor;

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="btn-icon w-10 h-10 group"
        aria-label="Toggle theme menu"
      >
        <CurrentIcon className="w-4 h-4 transition-transform group-hover:scale-110" />
      </button>

      {isOpen && (
        <>
          <div
            className="fixed inset-0 z-40"
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute right-0 top-full mt-2 z-50 w-36 py-2 rounded-xl bg-card border border-default shadow-lg animate-fade-in">
            {themes.map((t) => (
              <button
                key={t.value}
                onClick={() => {
                  setTheme(t.value);
                  setIsOpen(false);
                }}
                className={`w-full px-4 py-2 flex items-center gap-3 text-sm transition-colors hover:bg-muted ${
                  theme === t.value
                    ? "text-accent-500 font-medium"
                    : "text-muted-foreground"
                }`}
              >
                <t.icon className="w-4 h-4" />
                {t.label}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
