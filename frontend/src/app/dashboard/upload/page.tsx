"use client";

import { useState, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { motion, AnimatePresence } from "framer-motion";
import { Upload, File, X, CheckCircle, AlertCircle, Loader2, Table, ArrowRight } from "lucide-react";
import { api, UploadResponse } from "@/lib/api";
import { useAppStore } from "@/store/appStore";
import { formatNumber } from "@/lib/utils";
import { toast } from "sonner";
import { useRouter } from "next/navigation";

export default function UploadPage() {
  const router = useRouter();
  const { setSession, setCleaned, setProcessing, isProcessing } = useAppStore();
  const [uploadResult, setUploadResult] = useState<UploadResponse | null>(null);
  const [cleaningResult, setCleaningResult] = useState<any>(null);
  const [step, setStep] = useState<"upload" | "preview" | "cleaning" | "done">("upload");

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return;
    const file = acceptedFiles[0];
    setProcessing(true);
    try {
      const result = await api.upload(file);
      setUploadResult(result);
      setSession(result.session_id, result.filename, result.total_rows);
      setStep("preview");
      toast.success(`Uploaded ${result.filename} (${formatNumber(result.total_rows)} rows)`);
    } catch (e: any) {
      toast.error(e.message || "Upload failed");
    }
    setProcessing(false);
  }, [setSession, setProcessing]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "text/csv": [".csv"],
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
      "application/vnd.ms-excel": [".xls"],
    },
    maxFiles: 1,
    disabled: isProcessing,
  });

  const handleRunCleaning = async () => {
    if (!uploadResult) return;
    setProcessing(true);
    setStep("cleaning");
    try {
      const result = await api.runCleaning(uploadResult.session_id);
      setCleaningResult(result);
      setCleaned(true);
      setStep("done");
      toast.success(`Cleaning complete! ${result.rows_loaded} rows loaded.`);
    } catch (e: any) {
      toast.error(e.message || "Cleaning failed");
      setStep("preview");
    }
    setProcessing(false);
  };

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6 max-w-4xl mx-auto">
      <div className="stats-card text-center">
        <h2 className="text-2xl font-bold mb-2">Upload Expense File</h2>
        <p className="text-muted">CSV, XLSX, or XLS files supported</p>
      </div>

      <AnimatePresence mode="wait">
        {step === "upload" && (
          <motion.div key="upload" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }}>
            <div
              {...getRootProps()}
              className={`glass-card rounded-2xl p-16 text-center cursor-pointer transition-all border-2 border-dashed ${
                isDragActive ? "border-indigo-500 bg-indigo-500/5" : "border-white/10 hover:border-indigo-500/50"
              }`}
            >
              <input {...getInputProps()} />
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-indigo-500/20 to-cyan-500/20 flex items-center justify-center mx-auto mb-6">
                {isProcessing ? <Loader2 size={28} className="animate-spin text-indigo-400" /> : <Upload size={28} className="text-indigo-400" />}
              </div>
              <h3 className="text-xl font-semibold mb-2">
                {isDragActive ? "Drop your file here" : "Drag & drop your expense file"}
              </h3>
              <p className="text-muted mb-4">or click to browse</p>
              <p className="text-xs text-muted">Supports CSV, XLSX, XLS • Max 50MB</p>
            </div>
          </motion.div>
        )}

        {step === "preview" && uploadResult && (
          <motion.div key="preview" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }} className="space-y-4">
            <div className="stats-card">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-emerald-500/20 flex items-center justify-center">
                    <CheckCircle size={20} className="text-emerald-400" />
                  </div>
                  <div>
                    <h3 className="font-semibold">{uploadResult.filename}</h3>
                    <p className="text-sm text-muted">{formatNumber(uploadResult.total_rows)} rows • {uploadResult.total_columns} columns</p>
                  </div>
                </div>
                <button onClick={() => { setStep("upload"); setUploadResult(null); }} className="p-2 rounded-lg hover:bg-white/5 transition-colors">
                  <X size={18} className="text-muted" />
                </button>
              </div>

              <div className="mb-4">
                <h4 className="text-sm font-medium mb-2">Detected Columns:</h4>
                <div className="flex flex-wrap gap-2">
                  {uploadResult.columns.map((col, i) => (
                    <span key={i} className="text-xs px-2.5 py-1 rounded-full bg-white/5 border border-white/10">
                      {col}
                    </span>
                  ))}
                </div>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-white/10">
                      {uploadResult.columns.slice(0, 8).map((col) => (
                        <th key={col} className="text-left py-2 px-3 text-muted font-medium">{col}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {uploadResult.preview.slice(0, 5).map((row, i) => (
                      <tr key={i} className="border-b border-white/5">
                        {uploadResult.columns.slice(0, 8).map((col) => (
                          <td key={col} className="py-2 px-3 text-sm truncate max-w-[150px]">
                            {String(row[col] ?? "").slice(0, 40)}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <p className="text-xs text-muted mt-2">Showing first 5 of {formatNumber(uploadResult.total_rows)} rows</p>
            </div>

            <button
              onClick={handleRunCleaning}
              className="w-full py-3.5 bg-gradient-to-r from-indigo-500 to-cyan-500 hover:from-indigo-600 hover:to-cyan-600 text-white rounded-xl font-medium transition-all flex items-center justify-center gap-2"
            >
              Run AI Cleaning Pipeline <ArrowRight size={16} />
            </button>
          </motion.div>
        )}

        {step === "cleaning" && (
          <motion.div key="cleaning" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }} className="stats-card text-center py-12">
            <Loader2 size={40} className="animate-spin text-indigo-400 mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">Processing Your Data</h3>
            <p className="text-muted">Standardizing vendors • Parsing dates • Converting currencies • Detecting anomalies</p>
          </motion.div>
        )}

        {step === "done" && cleaningResult && (
          <motion.div key="done" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }} className="space-y-4">
            <div className="stats-card">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-12 h-12 rounded-xl bg-emerald-500/20 flex items-center justify-center">
                  <CheckCircle size={24} className="text-emerald-400" />
                </div>
                <div>
                  <h3 className="font-semibold text-lg">Cleaning Complete</h3>
                  <p className="text-sm text-muted">Your data is ready for analysis</p>
                </div>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="p-3 rounded-xl bg-white/5">
                  <div className="text-lg font-bold text-green-400">{formatNumber(cleaningResult.rows_loaded)}</div>
                  <div className="text-xs text-muted">Rows Loaded</div>
                </div>
                <div className="p-3 rounded-xl bg-white/5">
                  <div className="text-lg font-bold text-red-400">{formatNumber(cleaningResult.rows_excluded)}</div>
                  <div className="text-xs text-muted">Rows Excluded</div>
                </div>
                <div className="p-3 rounded-xl bg-white/5">
                  <div className="text-lg font-bold text-yellow-400">{cleaningResult.summary?.CRITICAL || 0}</div>
                  <div className="text-xs text-muted">Critical Issues</div>
                </div>
                <div className="p-3 rounded-xl bg-white/5">
                  <div className="text-lg font-bold text-blue-400">{cleaningResult.summary?.WARNING || 0}</div>
                  <div className="text-xs text-muted">Warnings</div>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <button
                onClick={() => router.push("/dashboard")}
                className="py-3 bg-indigo-500 hover:bg-indigo-600 text-white rounded-xl font-medium transition-all"
              >
                View Dashboard
              </button>
              <button
                onClick={() => router.push("/dashboard/data-quality")}
                className="py-3 bg-white/5 hover:bg-white/10 text-white rounded-xl font-medium transition-all border border-white/10"
              >
                Review Data Quality
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
