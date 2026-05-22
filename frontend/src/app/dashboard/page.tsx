"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  TrendingUp, TrendingDown, DollarSign, AlertTriangle,
  Shield, Copy, Users, FileText,
} from "lucide-react";
import {
  AreaChart, Area, BarChart, Bar, XAxis, YAxis,
  CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell,
} from "recharts";
import { api, SummaryData, TimelineData, DeptData, VendorData } from "@/lib/api";
import { useAppStore } from "@/store/appStore";
import { formatCurrency, cn, formatCompactCurrency } from "@/lib/utils";
import Link from "next/link";

const COLORS = ["#6366f1", "#06b6d4", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#ec4899", "#14b8a6"];

export default function ExecutiveDashboard() {
  const { sessionId } = useAppStore();
  const [summary, setSummary] = useState<SummaryData | null>(null);
  const [timeline, setTimeline] = useState<TimelineData[]>([]);
  const [departments, setDepartments] = useState<DeptData[]>([]);
  const [vendors, setVendors] = useState<VendorData[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      if (!sessionId) { setLoading(false); return; }
      try {
        const [s, t, d, v] = await Promise.all([
          api.summary(sessionId),
          api.timeline(sessionId),
          api.departments(sessionId),
          api.vendors(sessionId, 10),
        ]);
        setSummary(s);
        setTimeline(t);
        setDepartments(d);
        setVendors(v);
      } catch (e) {
        console.error("Failed to load dashboard", e);
      }
      setLoading(false);
    }
    load();
  }, [sessionId]);

  if (!sessionId) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-center p-12">
        <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-indigo-500/20 to-cyan-500/20 flex items-center justify-center mb-6">
          <FileText size={36} className="text-indigo-400" />
        </div>
        <h2 className="text-2xl font-bold mb-2">No Data Uploaded Yet</h2>
        <p className="text-muted mb-6 max-w-md">
          Upload an expense CSV or XLSX file to see your dashboard with AI-powered insights.
        </p>
        <Link
          href="/dashboard/upload"
          className="px-6 py-3 bg-indigo-500 hover:bg-indigo-600 text-white rounded-xl font-medium transition-all"
        >
          Upload Expenses
        </Link>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="skeleton h-28 rounded-2xl" />
          ))}
        </div>
        <div className="skeleton h-80 rounded-2xl" />
        <div className="grid grid-cols-2 gap-4">
          <div className="skeleton h-60 rounded-2xl" />
          <div className="skeleton h-60 rounded-2xl" />
        </div>
      </div>
    );
  }

  const kpis = [
    {
      icon: DollarSign,
      label: "Total Spend",
      value: formatCurrency(summary?.total_spend || 0),
      change: undefined,
      up: true,
      color: "from-blue-500 to-cyan-500",
    },
    {
      icon: TrendingUp,
      label: "Transactions",
      value: summary?.transaction_count?.toLocaleString() || "0",
      change: undefined,
      up: true,
      color: "from-emerald-500 to-teal-500",
    },
    {
      icon: AlertTriangle,
      label: "Anomalies Flagged",
      value: String(summary?.anomaly_count || 0),
      change: summary?.anomaly_count ? "Needs review" : "None",
      up: false,
      color: "from-amber-500 to-orange-500",
    },
    {
      icon: Shield,
      label: "Compliance Score",
      value: `${summary?.compliance_score || 100}%`,
      change: summary?.compliance_score && summary.compliance_score < 80 ? "Action needed" : "Good",
      up: (summary?.compliance_score || 100) >= 80,
      color: "from-purple-500 to-pink-500",
    },
  ];

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {kpis.map((kpi, i) => (
          <motion.div
            key={kpi.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.08 }}
            className="stats-card"
          >
             <div className="flex items-start justify-between mb-3">
               <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${kpi.color}/20 flex items-center justify-center`}>
                 <kpi.icon size={18} className={`text-${kpi.color.split(" ")[0].replace("from-", "")}`} />
               </div>
               {kpi.change !== undefined && (
                 <span className={cn("text-xs font-medium px-2 py-0.5 rounded-full", kpi.up ? "bg-emerald-500/10 text-emerald-400" : "bg-amber-500/10 text-amber-400")}>
                   {kpi.change}
                 </span>
               )}
             </div>
            <div className={cn("font-bold", kpi.value.length > 15 ? "text-lg" : kpi.value.length > 10 ? "text-xl" : "text-2xl")}>{kpi.value}</div>
            <div className="text-sm text-muted mt-1">{kpi.label}</div>
          </motion.div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="chart-container lg:col-span-2"
        >
          <h3 className="font-semibold mb-4">Monthly Spend Trend</h3>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={timeline}>
              <defs>
                <linearGradient id="spendGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.1)" />
              <XAxis dataKey="date" tick={{ fontSize: 12 }} stroke="rgba(148,163,184,0.5)" />
              <YAxis tickFormatter={(value) => formatCompactCurrency(value)} tick={{ fontSize: 12 }} stroke="rgba(148,163,184,0.5)" />
              <Tooltip
                contentStyle={{ background: "rgba(15,23,42,0.9)", border: "1px solid rgba(51,65,85,0.5)", borderRadius: "12px", backdropFilter: "blur(12px)" }}
              />
              <Area type="monotone" dataKey="total_spend" stroke="#6366f1" strokeWidth={2} fill="url(#spendGradient)" />
            </AreaChart>
          </ResponsiveContainer>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.35 }}
          className="chart-container"
        >
          <h3 className="font-semibold mb-4">Top Vendors</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={vendors.slice(0, 6)}
                dataKey="total_spend"
                nameKey="vendor_canonical"
                cx="50%"
                cy="50%"
                outerRadius={90}
                innerRadius={50}
              >
                {vendors.slice(0, 6).map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{ background: "rgba(15,23,42,0.9)", border: "1px solid rgba(51,65,85,0.5)", borderRadius: "12px" }}
              />
            </PieChart>
          </ResponsiveContainer>
          <div className="flex flex-wrap gap-2 mt-2">
            {vendors.slice(0, 4).map((v, i) => (
              <span key={i} className="text-xs px-2 py-1 rounded-full bg-white/5 border border-white/10">
                {v.vendor_canonical || v.vendor_raw}
              </span>
            ))}
          </div>
        </motion.div>
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="chart-container"
      >
        <h3 className="font-semibold mb-4">Department Spend Comparison</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={departments}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.1)" />
            <XAxis dataKey="department" tick={{ fontSize: 12 }} stroke="rgba(148,163,184,0.5)" />
            <YAxis tickFormatter={(value) => formatCompactCurrency(value)} tick={{ fontSize: 12 }} stroke="rgba(148,163,184,0.5)" />
            <Tooltip
              contentStyle={{ background: "rgba(15,23,42,0.9)", border: "1px solid rgba(51,65,85,0.5)", borderRadius: "12px" }}
            />
            <Bar dataKey="total_spend" fill="#6366f1" radius={[8, 8, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </motion.div>
    </motion.div>
  );
}
