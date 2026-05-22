"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { AlertTriangle, CheckCircle, XCircle, Info, Shield, RefreshCw } from "lucide-react";
import { api, QualityReport, QualityIssue } from "@/lib/api";
import { useAppStore } from "@/store/appStore";
import { formatNumber, cn } from "@/lib/utils";

const severityColors: Record<string, string> = {
  CRITICAL: "bg-red-500/10 text-red-400 border-red-500/20",
  WARNING: "bg-amber-500/10 text-amber-400 border-amber-500/20",
  INFO: "bg-blue-500/10 text-blue-400 border-blue-500/20",
};

const severityIcons: Record<string, any> = {
  CRITICAL: XCircle,
  WARNING: AlertTriangle,
  INFO: Info,
};

export default function DataQualityPage() {
  const { sessionId } = useAppStore();
  const [report, setReport] = useState<QualityReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>("all");

  useEffect(() => {
    async function load() {
      if (!sessionId) { setLoading(false); return; }
      try {
        const r = await api.qualityReport(sessionId);
        setReport(r);
      } catch (e) { console.error(e); }
      setLoading(false);
    }
    load();
  }, [sessionId]);

  const filteredIssues = report?.issues.filter((i) =>
    filter === "all" ? true : i.severity === filter
  ) || [];

  const totalScore = report ? Math.round(
    (report.rows_loaded / Math.max(report.total_rows_in_source, 1)) * 70
    + (1 - (report.summary.CRITICAL || 0) / Math.max(report.total_rows_in_source, 1)) * 30
  ) : 0;

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {[
          { label: "Quality Score", value: `${totalScore}%`, icon: Shield, color: "from-emerald-500 to-teal-500" },
          { label: "Critical Issues", value: report?.summary.CRITICAL || 0, icon: XCircle, color: "from-red-500 to-orange-500" },
          { label: "Warnings", value: report?.summary.WARNING || 0, icon: AlertTriangle, color: "from-amber-500 to-yellow-500" },
          { label: "Info", value: report?.summary.INFO || 0, icon: Info, color: "from-blue-500 to-cyan-500" },
        ].map((item, i) => (
          <motion.div
            key={item.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.08 }}
            className="stats-card"
          >
            <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${item.color}/20 flex items-center justify-center mb-3`}>
              <item.icon size={18} className={`text-${item.color.split(" ")[0].replace("from-", "")}-400`} />
            </div>
            <div className="text-2xl font-bold">{typeof item.value === "number" ? item.value : item.value}</div>
            <div className="text-sm text-muted">{item.label}</div>
          </motion.div>
        ))}
      </div>

      <div className="chart-container">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold">Issues Found ({formatNumber(filteredIssues.length)})</h3>
          <div className="flex gap-2">
            {["all", "CRITICAL", "WARNING", "INFO"].map((s) => (
              <button
                key={s}
                onClick={() => setFilter(s)}
                className={cn(
                  "px-3 py-1 rounded-lg text-xs font-medium transition-all",
                  filter === s ? "bg-indigo-500 text-white" : "bg-white/5 text-muted hover:text-white"
                )}
              >
                {s === "all" ? "All" : s}
              </button>
            ))}
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-white/10">
                <th className="text-left py-3 px-3 text-muted font-medium">Txn ID</th>
                <th className="text-left py-3 px-3 text-muted font-medium">Field</th>
                <th className="text-left py-3 px-3 text-muted font-medium">Issue Type</th>
                <th className="text-left py-3 px-3 text-muted font-medium">Severity</th>
                <th className="text-left py-3 px-3 text-muted font-medium">Raw Value</th>
                <th className="text-left py-3 px-3 text-muted font-medium">Action Taken</th>
              </tr>
            </thead>
            <tbody>
              {filteredIssues.length === 0 ? (
                <tr>
                  <td colSpan={6} className="text-center py-8 text-muted">
                    <CheckCircle size={24} className="mx-auto mb-2 text-emerald-400" />
                    No issues found. Your data is clean!
                  </td>
                </tr>
              ) : (
                filteredIssues.slice(0, 100).map((issue, i) => {
                  const SevIcon = severityIcons[issue.severity] || Info;
                  return (
                    <tr key={i} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                      <td className="py-2.5 px-3 font-mono text-xs">{issue.txn_id}</td>
                      <td className="py-2.5 px-3">{issue.field}</td>
                      <td className="py-2.5 px-3">{issue.issue_type}</td>
                      <td className="py-2.5 px-3">
                        <span className={cn("inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs border", severityColors[issue.severity])}>
                          <SevIcon size={10} />
                          {issue.severity}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 font-mono text-xs max-w-[200px] truncate">{issue.raw_value}</td>
                      <td className="py-2.5 px-3 text-xs">{issue.action_taken}</td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
        {filteredIssues.length > 100 && (
          <p className="text-xs text-muted mt-2">Showing 100 of {formatNumber(filteredIssues.length)} issues</p>
        )}
      </div>
    </motion.div>
  );
}
