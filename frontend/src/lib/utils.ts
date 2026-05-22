import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatCurrency(amount: number): string {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 2,
  }).format(amount);
}

export function formatNumber(num: number): string {
  return new Intl.NumberFormat("en-IN").format(num);
}

export function formatPercent(pct: number): string {
  return `${pct >= 0 ? "+" : ""}${pct.toFixed(1)}%`;
}

export function formatCompactNumber(num: number): string {
  if (Math.abs(num) >= 1e9) {
    return `${(num / 1e9).toFixed(1).replace(/\.0$/, "")}B`;
  }
  if (Math.abs(num) >= 1e6) {
    return `${(num / 1e6).toFixed(1).replace(/\.0$/, "")}M`;
  }
  if (Math.abs(num) >= 1e3) {
    return `${(num / 1e3).toFixed(1).replace(/\.0$/, "")}K`;
  }
  return `${Math.round(num)}`;
}

export function formatCompactCurrency(num: number): string {
  return `₹${formatCompactNumber(num)}`;
}
