"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Download, FileSpreadsheet, FileText, Code, CheckCircle } from "lucide-react";
import { useAppStore } from "@/store/appStore";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";

const formats = [
  { key: "csv", label: "CSV", icon: FileText, desc: "Comma-separated values, universal format" },
  { key: "xlsx", label: "Excel (XLSX)", icon: FileSpreadsheet, desc: "Formatted Excel workbook with headers" },
  { key: "json", label: "JSON", icon: Code, desc: "Structured JSON for API integration" },
];

export default function ReportsPage() {
  const { sessionId } = useAppStore();
  const [selectedFormat, setSelectedFormat] = useState("csv");
  const [exporting, setExporting] = useState(false);
  const [done, setDone] = useState(false);

  const handleExport = async () => {
    if (!sessionId) return;
    setExporting(true);
    try {
      const url = api.exportData(sessionId, selectedFormat as any);
      window.open(url, "_blank");
      setDone(true);
      setTimeout(() => setDone(false), 3000);
    } catch (e) {
      console.error(e);
    }
    setExporting(false);
  };

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6 max-w-3xl mx-auto">
      <div className="stats-card">
        <h2 className="text-xl font-bold mb-2">Export Reports</h2>
        <p className="text-muted text-sm">Download cleaned data and analysis results</p>
      </div>

      {!sessionId ? (
        <div className="stats-card text-center py-12">
          <FileText size={40} className="mx-auto mb-4 text-muted" />
          <h3 className="text-lg font-semibold mb-2">No Data to Export</h3>
          <p className="text-muted">Upload and process expense data first</p>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {formats.map((fmt) => (
              <button
                key={fmt.key}
                onClick={() => setSelectedFormat(fmt.key)}
                className={cn(
                  "stats-card text-left transition-all",
                  selectedFormat === fmt.key
                    ? "ring-2 ring-indigo-500 bg-indigo-500/5"
                    : "hover:bg-white/5"
                )}
              >
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500/20 to-cyan-500/20 flex items-center justify-center mb-3">
                  <fmt.icon size={18} className="text-indigo-400" />
                </div>
                <div className="font-semibold mb-1">{fmt.label}</div>
                <div className="text-xs text-muted">{fmt.desc}</div>
              </button>
            ))}
          </div>

          <button
            onClick={handleExport}
            disabled={exporting}
            className="w-full py-3.5 bg-gradient-to-r from-indigo-500 to-cyan-500 hover:from-indigo-600 hover:to-cyan-600 disabled:opacity-50 text-white rounded-xl font-medium transition-all flex items-center justify-center gap-2"
          >
            {done ? (
              <><CheckCircle size={18} /> Exported Successfully</>
            ) : exporting ? (
              <><Download size={18} className="animate-bounce" /> Exporting...</>
            ) : (
              <><Download size={18} /> Export {formats.find((f) => f.key === selectedFormat)?.label}</>
            )}
          </button>
        </>
      )}
    </motion.div>
  );
}
