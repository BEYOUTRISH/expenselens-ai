"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import {
  ArrowRight,
  Sparkles,
  Shield,
  BarChart3,
  Upload,
  Bot,
  TrendingUp,
} from "lucide-react";

const features = [
  {
    icon: Upload,
    title: "Smart Upload",
    desc: "Drag-and-drop CSV/XLSX files. Auto-detect encoding, delimiter, and schema.",
  },
  {
    icon: Sparkles,
    title: "AI Cleaning",
    desc: "Auto-standardize vendors, currencies, dates. Detect duplicates and anomalies.",
  },
  {
    icon: BarChart3,
    title: "Premium Dashboards",
    desc: "Interactive charts and KPIs. Executive, department, vendor, and compliance views.",
  },
  {
    icon: Shield,
    title: "Anomaly Detection",
    desc: "Isolation Forest + Z-score + IQR. Flag suspicious transactions with explanations.",
  },
  {
    icon: Bot,
    title: "AI Assistant",
    desc: "Ask questions in plain English. Get instant answers about your expense data.",
  },
  {
    icon: TrendingUp,
    title: "Forecasting",
    desc: "Prophet-powered predictions with confidence intervals. Plan ahead with data.",
  },
];

const stats = [
  { value: "99.9%", label: "Data Accuracy" },
  { value: "50+", label: "Vendors Auto-Resolved" },
  { value: "18K+", label: "Rows/Min Processed" },
  { value: "95%", label: "Anomaly Detection Rate" },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-[#0b0d17] via-[#0f172a] to-[#0b0d17]">
      <nav className="sticky top-0 z-50 glass-card rounded-none px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-cyan-500 flex items-center justify-center">
              <TrendingUp size={16} className="text-white" />
            </div>
            <span className="font-bold text-xl text-white">ExpenseLens</span>
          </div>
          <div className="flex items-center gap-4">
            <Link
              href="/dashboard"
              className="px-4 py-2 text-sm text-slate-300 hover:text-white transition-colors"
            >
              Dashboard
            </Link>
            <Link
              href="/dashboard/upload"
              className="px-5 py-2 bg-indigo-500 hover:bg-indigo-600 text-white rounded-xl text-sm font-medium transition-all flex items-center gap-2"
            >
              Get Started <ArrowRight size={14} />
            </Link>
          </div>
        </div>
      </nav>

      <section className="max-w-7xl mx-auto px-6 pt-24 pb-20 text-center">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-sm mb-6">
            <Sparkles size={14} /> AI-Powered Expense Intelligence
          </div>
          <h1 className="text-5xl md:text-7xl font-bold text-white mb-6 leading-tight">
            Turn Expense Data Into
            <span className="bg-gradient-to-r from-indigo-400 via-cyan-400 to-emerald-400 text-transparent bg-clip-text"> Actionable Insights</span>
          </h1>
          <p className="text-lg text-slate-400 max-w-2xl mx-auto mb-10">
            Upload raw expense files and let AI clean, standardize, reconcile, and analyze them.
            Enterprise-grade dashboards, anomaly detection, and forecasting in minutes.
          </p>
          <Link
            href="/dashboard/upload"
            className="inline-flex items-center gap-2 px-8 py-3.5 bg-gradient-to-r from-indigo-500 to-cyan-500 hover:from-indigo-600 hover:to-cyan-600 text-white rounded-2xl text-lg font-medium transition-all shadow-lg shadow-indigo-500/25"
          >
            Upload Your First File <ArrowRight size={18} />
          </Link>
        </motion.div>
      </section>

      <section className="max-w-7xl mx-auto px-6 pb-20">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-20">
          {stats.map((stat, i) => (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 + i * 0.1 }}
              className="glass-card rounded-2xl p-6 text-center"
            >
              <div className="text-3xl font-bold bg-gradient-to-r from-indigo-400 to-cyan-400 text-transparent bg-clip-text">
                {stat.value}
              </div>
              <div className="text-sm text-slate-400 mt-1">{stat.label}</div>
            </motion.div>
          ))}
        </div>

        <h2 className="text-3xl font-bold text-white text-center mb-12">
          Everything You Need for Expense Intelligence
        </h2>
        <div className="grid md:grid-cols-3 gap-6">
          {features.map((feature, i) => (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 + i * 0.08 }}
              className="glass-card rounded-2xl p-6 hover:translate-y-[-4px] transition-all duration-300"
            >
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500/20 to-cyan-500/20 flex items-center justify-center mb-4">
                <feature.icon size={20} className="text-indigo-400" />
              </div>
              <h3 className="text-lg font-semibold text-white mb-2">{feature.title}</h3>
              <p className="text-sm text-slate-400">{feature.desc}</p>
            </motion.div>
          ))}
        </div>
      </section>

      <footer className="border-t border-white/5 py-8 text-center text-sm text-slate-500">
        <p>ExpenseLens AI v1.0.0 — Built with Next.js, FastAPI, and AI</p>
      </footer>
    </div>
  );
}
