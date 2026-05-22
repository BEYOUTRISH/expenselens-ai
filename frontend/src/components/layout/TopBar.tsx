"use client";

import { useEffect, useState } from "react";
import { useTheme } from "next-themes";
import { Sun, Moon } from "lucide-react";
import { useAppStore } from "@/store/appStore";

export default function TopBar() {
  const { theme, setTheme } = useTheme();
  const { fileName, isCleaned } = useAppStore();
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);

  return (
    <header className="sticky top-0 z-20 glass-card rounded-none lg:rounded-2xl px-6 py-3 flex items-center justify-between">
      <div className="flex items-center gap-4">
        <h1 className="text-lg font-semibold hidden sm:block">Dashboard</h1>
        {fileName && (
          <span className="text-sm text-muted px-3 py-1 rounded-full bg-white/5 border border-white/10">
            {fileName}
            {isCleaned && (
              <span className="ml-2 text-success">✓ Cleaned</span>
            )}
          </span>
        )}
      </div>

      <div className="flex items-center gap-3">
        <button
          onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
          className="p-2 rounded-xl hover:bg-white/5 transition-colors text-muted hover:text-foreground"
        >
          {!mounted ? <div className="w-[18px] h-[18px]" /> : theme === "dark" ? <Sun size={18} /> : <Moon size={18} />}
        </button>
      </div>
    </header>
  );
}
