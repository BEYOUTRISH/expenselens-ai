"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard,
  Upload,
  BarChart3,
  ShieldCheck,
  Lightbulb,
  Bot,
  FileText,
  Settings,
  LineChart,
  TrendingUp,
  Menu,
  X,
  Wallet,
} from "lucide-react";
import { useState } from "react";

const navItems = [
  { href: "/dashboard", icon: LayoutDashboard, label: "Executive Dashboard" },
  { href: "/dashboard/upload", icon: Upload, label: "Upload" },
  { href: "/dashboard/analytics", icon: BarChart3, label: "Analytics" },
  { href: "/dashboard/data-quality", icon: ShieldCheck, label: "Data Quality" },
  { href: "/dashboard/insights", icon: Lightbulb, label: "AI Insights" },
  { href: "/dashboard/ai-assistant", icon: Bot, label: "AI Assistant" },
  { href: "/dashboard/forecasting", icon: TrendingUp, label: "Forecasting" },
  { href: "/dashboard/reports", icon: FileText, label: "Reports" },
  { href: "/dashboard/settings", icon: Settings, label: "Settings" },
];

export default function Sidebar() {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <>
      <button
        onClick={() => setMobileOpen(!mobileOpen)}
        className="fixed top-4 left-4 z-50 lg:hidden glass-card p-2 rounded-lg"
      >
        {mobileOpen ? <X size={20} /> : <Menu size={20} />}
      </button>

      <aside
        className={cn(
          "glass-sidebar fixed lg:sticky top-0 left-0 h-screen w-64 z-40 flex flex-col transition-transform duration-300",
          mobileOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
        )}
      >
        <div className="flex items-center gap-2 px-6 py-5 border-b border-white/10">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-indigo-500 to-cyan-500 flex items-center justify-center">
            <Wallet size={18} className="text-white" />
          </div>
          <span className="font-semibold text-lg text-white">ExpenseLens</span>
        </div>

        <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
          {navItems.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setMobileOpen(false)}
                className={cn(
                  "flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200",
                  isActive
                    ? "bg-indigo-500/20 text-indigo-300 border border-indigo-500/30"
                    : "text-slate-400 hover:text-white hover:bg-white/5"
                )}
              >
                <item.icon size={18} className="shrink-0" />
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="p-4 border-t border-white/10">
          <div className="glass-card rounded-xl p-3">
            <p className="text-xs text-slate-400 mb-1">ExpenseLens AI</p>
            <p className="text-xs text-slate-500">v1.0.0 • AI-Powered</p>
          </div>
        </div>
      </aside>

      {mobileOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-30 lg:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}
    </>
  );
}
