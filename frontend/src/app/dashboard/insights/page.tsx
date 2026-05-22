"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  Lightbulb, TrendingUp, AlertTriangle, Shield, FileText, Sparkles,
  Users, Clock, Receipt, Copy, DollarSign, BarChart3, User, Heart,
} from "lucide-react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend,
} from "recharts";
import { api, InsightsResponse } from "@/lib/api";
import { useAppStore } from "@/store/appStore";
import { formatCurrency, cn, formatCompactCurrency } from "@/lib/utils";

export default function InsightsPage() {
  const { sessionId } = useAppStore();
  const [insights, setInsights] = useState<InsightsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [isAi, setIsAi] = useState(false);
  const [aiProvider, setAiProvider] = useState<string | null>(null);
  const [selectedMode, setSelectedMode] = useState<"groq" | "none">("none");
  const [generating, setGenerating] = useState(false);

  const fetchInsights = async (mode?: "groq" | "none") => {
    if (!sessionId) return;
    setGenerating(true);
    try {
      const result = await api.generateInsights(sessionId, mode);
      setInsights(result);
      setIsAi(result.ai === true);
      setAiProvider(result.ai_provider || null);
    } catch (e) { console.error(e); }
    setGenerating(false);
    setLoading(false);
  };

  useEffect(() => {
    async function load() {
      if (!sessionId) { setLoading(false); return; }
      setGenerating(true);
      try {
        const result = await api.generateInsights(sessionId);
        setInsights(result);
        setIsAi(result.ai === true);
        setAiProvider(result.ai_provider || null);
        if (result.ai === true && result.ai_provider === "groq") {
          setSelectedMode("groq");
        } else {
          setSelectedMode("none");
        }
      } catch (e) { console.error(e); }
      setGenerating(false);
      setLoading(false);
    }
    load();
  }, [sessionId]);

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="skeleton h-40 rounded-2xl" />
        <div className="skeleton h-60 rounded-2xl" />
        <div className="skeleton h-40 rounded-2xl" />
      </div>
    );
  }

  if (!insights) {
    return (
      <div className="stats-card text-center py-12">
        <Lightbulb size={40} className="mx-auto mb-4 text-amber-400" />
        <h3 className="text-lg font-semibold mb-2">No Insights Available</h3>
        <p className="text-muted">Upload and process expense data first</p>
      </div>
    );
  }

  const { insights: data, summary } = insights;

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="stats-card"
      >
         <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
           <div className="flex items-center gap-3">
             <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-500/20 to-orange-500/20 flex items-center justify-center">
               <FileText size={20} className="text-amber-400" />
             </div>
             <div>
               <div className="flex items-center gap-2">
                 <h2 className="text-xl font-bold">AI Financial Analysis Report</h2>
                 {isAi && aiProvider === "groq" ? (
                   <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">Groq AI</span>
                 ) : isAi && aiProvider === "openai" ? (
                   <span className="text-xs px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">GPT-4o-mini</span>
                 ) : isAi ? (
                   <span className="text-xs px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">AI Powered</span>
                 ) : (
                   <span className="text-xs px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20">Rule-based analysis</span>
                 )}
               </div>
             </div>
           </div>
           <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3">
             <div className="flex items-center gap-2 bg-white/5 rounded-xl p-1">
               <button
                 onClick={() => setSelectedMode("none")}
                 disabled={generating}
                 className={cn(
                   "px-3 py-1.5 rounded-lg text-xs font-medium transition-all",
                   selectedMode === "none"
                     ? "bg-amber-500 text-white"
                     : "text-muted hover:text-white"
                 )}
               >
                 Normal
               </button>
               <button
                 onClick={() => setSelectedMode("groq")}
                 disabled={generating}
                 className={cn(
                   "px-3 py-1.5 rounded-lg text-xs font-medium transition-all",
                   selectedMode === "groq"
                     ? "bg-emerald-500 text-white"
                     : "text-muted hover:text-white"
                 )}
               >
                 Groq AI
               </button>
             </div>
             <button
               onClick={() => fetchInsights(selectedMode)}
               disabled={generating || loading}
               className="px-4 py-1.5 bg-indigo-500 hover:bg-indigo-600 disabled:opacity-50 text-white text-xs font-medium rounded-xl transition-all flex items-center gap-2"
             >
               {generating ? (
                 <>
                   <Sparkles size={14} className="animate-pulse" />
                   Generating...
                 </>
               ) : (
                 <>
                   <Sparkles size={14} />
                   Regenerate
                 </>
               )}
             </button>
           </div>
         </div>
         <p className="text-muted leading-relaxed">{data.executive_summary}</p>
      </motion.div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="stats-card"
        >
          <TrendingUp size={18} className="text-indigo-400 mb-2" />
          <div className={cn("font-bold", formatCurrency(summary?.total_spend || 0).length > 15 ? "text-lg" : formatCurrency(summary?.total_spend || 0).length > 10 ? "text-xl" : "text-2xl")}>{formatCurrency(summary?.total_spend || 0)}</div>
          <div className="text-sm text-muted">Total Spend</div>
        </motion.div>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
          className="stats-card"
        >
          <AlertTriangle size={18} className="text-amber-400 mb-2" />
          <div className="text-2xl font-bold">{summary?.anomaly_count || 0}</div>
          <div className="text-sm text-muted">Anomalies</div>
        </motion.div>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="stats-card"
        >
          <Shield size={18} className="text-emerald-400 mb-2" />
          <div className="text-2xl font-bold">{summary?.compliance_score || 0}%</div>
          <div className="text-sm text-muted">Compliance Score</div>
        </motion.div>
      </div>

      {data.department_trends.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.25 }}
          className="chart-container"
        >
          <h3 className="font-semibold mb-4">Department Trends</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {data.department_trends.map((dept, i) => (
              <div key={i} className="p-4 rounded-xl bg-white/5">
                <div className="text-sm font-medium mb-1">{dept.department}</div>
                <div className="text-lg font-bold">{formatCurrency(dept.total_spend)}</div>
                <div className="text-xs text-muted">{dept.percentage}% of total spend</div>
              </div>
            ))}
          </div>
        </motion.div>
      )}

      {data.risk_signals.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="chart-container"
        >
          <h3 className="font-semibold mb-4 flex items-center gap-2">
            <AlertTriangle size={16} className="text-red-400" /> Risk Signals
          </h3>
          <div className="space-y-3">
            {data.risk_signals.map((signal, i) => (
              <div key={i} className="p-3 rounded-xl bg-red-500/5 border border-red-500/10 text-sm">
                {signal}
              </div>
            ))}
          </div>
        </motion.div>
      )}

      {data.recommendations.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.35 }}
          className="chart-container"
        >
          <h3 className="font-semibold mb-4 flex items-center gap-2">
            <Sparkles size={16} className="text-indigo-400" /> Recommendations
          </h3>
          <ul className="space-y-2">
            {data.recommendations.map((rec, i) => (
              <li key={i} className="flex items-start gap-2 text-sm">
                <span className="text-indigo-400 mt-0.5">•</span>
                {rec}
              </li>
            ))}
          </ul>
        </motion.div>
      )}

      {data.spending_patterns.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="chart-container"
        >
          <h3 className="font-semibold mb-4">Spending Patterns</h3>
          <div className="space-y-2">
            {data.spending_patterns.map((pattern, i) => (
              <p key={i} className="text-sm text-muted">{pattern}</p>
            ))}
          </div>
        </motion.div>
      )}

      {data.employee_analysis.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.45 }}
          className="chart-container"
        >
          <h3 className="font-semibold mb-4 flex items-center gap-2">
            <Users size={16} className="text-cyan-400" /> Employee Analysis
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-white/10">
                  <th className="text-left py-3 px-3 text-muted font-medium">Employee</th>
                  <th className="text-left py-3 px-3 text-muted font-medium">Total Spend</th>
                  <th className="text-left py-3 px-3 text-muted font-medium">Transactions</th>
                  <th className="text-left py-3 px-3 text-muted font-medium">Avg Spend</th>
                  <th className="text-left py-3 px-3 text-muted font-medium">Compliance</th>
                </tr>
              </thead>
              <tbody>
                {data.employee_analysis.map((emp, i) => (
                  <tr key={i} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                    <td className="py-2.5 px-3">{emp.submitted_by}</td>
                    <td className="py-2.5 px-3 font-medium">{formatCurrency(emp.total_spend)}</td>
                    <td className="py-2.5 px-3">{emp.transaction_count}</td>
                    <td className="py-2.5 px-3">{formatCurrency(emp.avg_spend)}</td>
                    <td className="py-2.5 px-3">
                      <span className={cn(
                        "inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium",
                        emp.compliance_rate >= 90 ? "bg-emerald-500/10 text-emerald-400" :
                        emp.compliance_rate >= 70 ? "bg-amber-500/10 text-amber-400" :
                        "bg-red-500/10 text-red-400"
                      )}>
                        {emp.compliance_rate}%
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </motion.div>
      )}

      {data.vendor_risk.high_concentration_vendors?.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="chart-container"
        >
          <h3 className="font-semibold mb-4 flex items-center gap-2">
            <BarChart3 size={16} className="text-violet-400" /> Vendor Risk Analysis
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <div className="p-4 rounded-xl bg-white/5">
              <div className="text-sm text-muted mb-1">Vendor Diversity Score</div>
              <div className="text-2xl font-bold">{data.vendor_risk.vendor_diversity_score}/100</div>
              <div className="w-full bg-white/10 rounded-full h-2 mt-2">
                <div
                  className={cn(
                    "h-2 rounded-full",
                    data.vendor_risk.vendor_diversity_score >= 70 ? "bg-emerald-500" :
                    data.vendor_risk.vendor_diversity_score >= 40 ? "bg-amber-500" :
                    "bg-red-500"
                  )}
                  style={{ width: `${data.vendor_risk.vendor_diversity_score}%` }}
                />
              </div>
            </div>
            {data.vendor_risk.vendors_with_anomalies?.length > 0 && (
              <div className="p-4 rounded-xl bg-white/5">
                <div className="text-sm text-muted mb-2">Vendors with Anomalies</div>
                {data.vendor_risk.vendors_with_anomalies.map((v, i) => (
                  <div key={i} className="flex justify-between text-sm py-1">
                    <span>{v.vendor}</span>
                    <span className="text-red-400 font-medium">{v.anomaly_count} issues</span>
                  </div>
                ))}
              </div>
            )}
          </div>
          <div className="space-y-2">
            <div className="text-sm text-muted mb-2">High Concentration Vendors (&gt;10% spend)</div>
            {data.vendor_risk.high_concentration_vendors.map((v, i) => (
              <div key={i} className="flex items-center gap-3 p-3 rounded-xl bg-white/5">
                <div className="flex-1">
                  <div className="text-sm font-medium">{v.vendor}</div>
                  <div className="text-xs text-muted">{v.spend_pct}% of total spend</div>
                </div>
                <div className="text-right">
                  <div className="text-sm font-medium">{formatCurrency(v.total_spend)}</div>
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      )}

      {data.time_patterns.day_of_week_patterns?.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.55 }}
          className="chart-container"
        >
          <h3 className="font-semibold mb-4 flex items-center gap-2">
            <Clock size={16} className="text-orange-400" /> Time-Based Patterns
          </h3>
          {data.time_patterns.month_end_spike && (
            <div className="p-3 rounded-xl bg-amber-500/5 border border-amber-500/10 text-sm mb-4 flex items-center gap-2">
              <AlertTriangle size={14} className="text-amber-400" />
              Month-end spending spike detected - {data.time_patterns.busiest_month} was the busiest month
            </div>
          )}
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={data.time_patterns.day_of_week_patterns}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.1)" />
              <XAxis dataKey="day" tick={{ fontSize: 11 }} stroke="rgba(148,163,184,0.5)" />
              <YAxis tickFormatter={(value) => formatCompactCurrency(value)} tick={{ fontSize: 12 }} stroke="rgba(148,163,184,0.5)" />
              <Tooltip
                contentStyle={{ background: "rgba(15,23,42,0.9)", border: "1px solid rgba(51,65,85,0.5)", borderRadius: "12px" }}
              />
              <Bar dataKey="total_spend" fill="#f59e0b" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </motion.div>
      )}

      {data.receipt_compliance.overall_rate !== undefined && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="chart-container"
        >
          <h3 className="font-semibold mb-4 flex items-center gap-2">
            <Receipt size={16} className="text-emerald-400" /> Receipt Compliance
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <div className="p-4 rounded-xl bg-white/5">
              <div className="text-sm text-muted mb-1">Overall Receipt Compliance</div>
              <div className="text-2xl font-bold">{data.receipt_compliance.overall_rate}%</div>
              <div className="w-full bg-white/10 rounded-full h-2 mt-2">
                <div
                  className={cn(
                    "h-2 rounded-full",
                    data.receipt_compliance.overall_rate >= 80 ? "bg-emerald-500" :
                    data.receipt_compliance.overall_rate >= 50 ? "bg-amber-500" :
                    "bg-red-500"
                  )}
                  style={{ width: `${data.receipt_compliance.overall_rate}%` }}
                />
              </div>
            </div>
          </div>
          {data.receipt_compliance.by_department?.length > 0 && (
            <div className="space-y-2 mb-4">
              <div className="text-sm text-muted">By Department</div>
              {data.receipt_compliance.by_department.map((d, i) => (
                <div key={i} className="flex items-center gap-3 p-2 rounded-lg bg-white/5">
                  <div className="w-32 text-sm truncate">{d.department}</div>
                  <div className="flex-1">
                    <div className="w-full bg-white/10 rounded-full h-2">
                      <div
                        className={cn(
                          "h-2 rounded-full",
                          d.rate >= 80 ? "bg-emerald-500" :
                          d.rate >= 50 ? "bg-amber-500" :
                          "bg-red-500"
                        )}
                        style={{ width: `${d.rate}%` }}
                      />
                    </div>
                  </div>
                  <div className="text-sm w-12 text-right">{d.rate}%</div>
                </div>
              ))}
            </div>
          )}
          {data.receipt_compliance.high_value_missing_receipt?.length > 0 && (
            <div>
              <div className="text-sm text-muted mb-2">High-Value Transactions Missing Receipts</div>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-white/10">
                      <th className="text-left py-2 px-3 text-muted font-medium">Txn Ref</th>
                      <th className="text-left py-2 px-3 text-muted font-medium">Amount</th>
                      <th className="text-left py-2 px-3 text-muted font-medium">Vendor</th>
                      <th className="text-left py-2 px-3 text-muted font-medium">Department</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.receipt_compliance.high_value_missing_receipt.map((t, i) => (
                      <tr key={i} className="border-b border-white/5">
                        <td className="py-2 px-3 font-mono text-xs">{t.txn_ref}</td>
                        <td className="py-2 px-3 font-medium text-red-400">{formatCurrency(t.amount)}</td>
                        <td className="py-2 px-3">{t.vendor}</td>
                        <td className="py-2 px-3">{t.department}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </motion.div>
      )}

      {data.duplicate_analysis.confirmed_duplicates !== undefined && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.65 }}
          className="chart-container"
        >
          <h3 className="font-semibold mb-4 flex items-center gap-2">
            <Copy size={16} className="text-pink-400" /> Duplicate Analysis
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 rounded-xl bg-white/5">
              <div className="text-sm text-muted mb-1">Confirmed Duplicates</div>
              <div className="text-2xl font-bold">{data.duplicate_analysis.confirmed_duplicates}</div>
            </div>
            <div className="p-4 rounded-xl bg-white/5">
              <div className="text-sm text-muted mb-1">Potential Duplicates</div>
              <div className="text-2xl font-bold">{data.duplicate_analysis.potential_duplicates}</div>
            </div>
            <div className="p-4 rounded-xl bg-white/5">
              <div className="text-sm text-muted mb-1">Duplicate Value</div>
              <div className="text-lg font-bold">{formatCurrency(data.duplicate_analysis.duplicate_value)}</div>
            </div>
          </div>
        </motion.div>
      )}

       {data.high_value_transactions.top_1_percent?.length > 0 && (
         <motion.div
           initial={{ opacity: 0, y: 20 }}
           animate={{ opacity: 1, y: 0 }}
           transition={{ delay: 0.7 }}
           className="chart-container"
         >
           <h3 className="font-semibold mb-4 flex items-center gap-2">
             <DollarSign size={16} className="text-yellow-400" /> High-Value Transactions (Top 1%)
           </h3>
           <div className="p-3 rounded-xl bg-white/5 mb-4 flex flex-wrap gap-4 text-sm">
             <div>
               <span className="text-muted">Threshold: </span>
               <span className="font-medium">{formatCurrency(data.high_value_transactions.threshold)}</span>
             </div>
             <div>
               <span className="text-muted">Count: </span>
               <span className="font-medium">{data.high_value_transactions.count}</span>
             </div>
             <div>
               <span className="text-muted">Total: </span>
               <span className="font-medium">{formatCurrency(data.high_value_transactions.total_high_value)}</span>
             </div>
           </div>
           <div className="overflow-x-auto">
             <table className="w-full text-sm">
               <thead>
                 <tr className="border-b border-white/10">
                   <th className="text-left py-2 px-3 text-muted font-medium">Txn Ref</th>
                   <th className="text-left py-2 px-3 text-muted font-medium">Amount</th>
                   <th className="text-left py-2 px-3 text-muted font-medium">Vendor</th>
                   <th className="text-left py-2 px-3 text-muted font-medium">Department</th>
                   <th className="text-left py-2 px-3 text-muted font-medium">Submitted By</th>
                   <th className="text-left py-2 px-3 text-muted font-medium">Status</th>
                 </tr>
               </thead>
               <tbody>
                 {data.high_value_transactions.top_1_percent.map((t, i) => (
                   <tr key={i} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                     <td className="py-2 px-3 font-mono text-xs">{t.txn_ref}</td>
                     <td className="py-2 px-3 font-medium">{formatCurrency(t.amount)}</td>
                     <td className="py-2 px-3">{t.vendor}</td>
                     <td className="py-2 px-3">{t.department}</td>
                     <td className="py-2 px-3">{t.submitted_by}</td>
                     <td className="py-2 px-3">
                       {t.is_flagged ? (
                         <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs bg-red-500/10 text-red-400">Flagged</span>
                       ) : (
                         <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs bg-emerald-500/10 text-emerald-400">Clean</span>
                       )}
                     </td>
                   </tr>
                 ))}
               </tbody>
             </table>
           </div>
         </motion.div>
       )}

       {data.personal_expense_analysis && (
         <motion.div
           initial={{ opacity: 0, y: 20 }}
           animate={{ opacity: 1, y: 0 }}
           transition={{ delay: 0.75 }}
           className="chart-container"
         >
           <h3 className="font-semibold mb-4 flex items-center gap-2">
             <Heart size={16} className="text-rose-400" /> Personal Expense Detection
           </h3>

           <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
             <div className="p-4 rounded-xl bg-white/5">
               <div className="text-sm text-muted mb-1">Flagged Transactions</div>
               <div className="text-2xl font-bold text-rose-400">{data.personal_expense_analysis.total_count}</div>
             </div>
             <div className="p-4 rounded-xl bg-white/5">
               <div className="text-sm text-muted mb-1">Total Value</div>
               <div className="text-2xl font-bold text-rose-400">
                 {formatCurrency(data.personal_expense_analysis.total_value)}
               </div>
             </div>
             <div className="p-4 rounded-xl bg-white/5">
               <div className="text-sm text-muted mb-1">% of Total Spend</div>
               <div className="text-2xl font-bold text-amber-400">
                 {data.personal_expense_analysis.percentage_of_total}%
               </div>
             </div>
           </div>

           {data.personal_expense_analysis.by_category && data.personal_expense_analysis.by_category.length > 0 && (
             <div className="mb-6">
               <h4 className="text-sm font-medium text-muted mb-3">By Category</h4>
               <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                 <div className="h-72">
                   <ResponsiveContainer width="100%" height="100%">
                     <PieChart>
                       <Pie
                         data={data.personal_expense_analysis.by_category.map(c => ({
                           name: c.category,
                           value: c.value,
                         }))}
                         cx="50%"
                         cy="50%"
                         outerRadius={90}
                         dataKey="value"
                          label={({ name, percent }) => `${name} (${((percent ?? 0) * 100).toFixed(0)}%)`}
                       >
                         {data.personal_expense_analysis.by_category.map((_, index) => (
                           <Cell
                             key={`cell-${index}`}
                             fill={[
                               "#f43f5e", "#f97316", "#eab308", "#22c55e", "#06b6d4",
                               "#3b82f6", "#8b5cf6", "#ec4899", "#64748b",
                             ][index % 9]}
                           />
                         ))}
                       </Pie>
                       <Tooltip formatter={(value) => formatCurrency(Number(value))} />
                       <Legend />
                     </PieChart>
                   </ResponsiveContainer>
                 </div>

                 <div className="space-y-3">
                   {data.personal_expense_analysis.by_category.slice(0, 5).map((cat, i) => (
                     <div key={i} className="p-3 rounded-lg bg-white/5">
                       <div className="flex items-center justify-between mb-2">
                         <span className="font-medium">{cat.category}</span>
                         <span className="text-sm text-muted">{cat.count} txns</span>
                       </div>
                       <div className="text-lg font-bold text-rose-400 mb-2">
                         {formatCurrency(cat.value)}
                       </div>
                       {cat.risk_outcomes?.length > 0 && (
                         <div className="mb-2">
                           <div className="text-xs text-muted mb-1">Risks:</div>
                           <ul className="list-disc list-inside text-xs text-red-400 space-y-0.5">
                             {cat.risk_outcomes.map((r, ri) => (
                               <li key={ri}>{r}</li>
                             ))}
                           </ul>
                         </div>
                       )}
                       {cat.recommended_actions?.length > 0 && (
                         <div>
                           <div className="text-xs text-muted mb-1">Actions:</div>
                           <ul className="list-disc list-inside text-xs text-emerald-400 space-y-0.5">
                             {cat.recommended_actions.slice(0, 2).map((a, ai) => (
                               <li key={ai}>{a.action} ({a.priority})</li>
                             ))}
                           </ul>
                         </div>
                       )}
                     </div>
                   ))}
                 </div>
               </div>
             </div>
           )}

           {data.personal_expense_analysis.top_keywords && data.personal_expense_analysis.top_keywords.length > 0 && (
             <div className="mb-6">
               <h4 className="text-sm font-medium text-muted mb-3">Top Keywords</h4>
               <div className="overflow-x-auto">
                 <table className="w-full text-sm">
                   <thead>
                     <tr className="border-b border-white/10">
                       <th className="text-left py-2 px-3 text-muted font-medium">Keyword</th>
                       <th className="text-left py-2 px-3 text-muted font-medium">Category</th>
                       <th className="text-right py-2 px-3 text-muted font-medium">Count</th>
                       <th className="text-right py-2 px-3 text-muted font-medium">Value</th>
                     </tr>
                   </thead>
                   <tbody>
                     {data.personal_expense_analysis.top_keywords.map((kw, i) => (
                       <tr key={i} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                         <td className="py-2 px-3 font-medium">{kw.keyword}</td>
                         <td className="py-2 px-3 text-sm text-muted">{kw.category}</td>
                         <td className="py-2 px-3 text-right">{kw.count}</td>
                         <td className="py-2 px-3 text-right font-medium text-rose-400">
                           {formatCurrency(kw.value)}
                         </td>
                       </tr>
                     ))}
                   </tbody>
                 </table>
               </div>
             </div>
           )}

           {(data.personal_expense_analysis.by_employee?.length || data.personal_expense_analysis.by_department?.length) ? (
             <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
               {data.personal_expense_analysis.by_employee && data.personal_expense_analysis.by_employee.length > 0 && (
                 <div>
                   <h4 className="text-sm font-medium text-muted mb-3 flex items-center gap-2">
                     <User size={14} /> By Employee
                   </h4>
                   <div className="space-y-2">
                     {data.personal_expense_analysis.by_employee.slice(0, 5).map((emp, i) => (
                       <div key={i} className="flex items-center justify-between p-2 rounded-lg bg-white/5">
                         <span className="text-sm truncate max-w-48">{emp.employee}</span>
                         <div className="flex items-center gap-4">
                           <span className="text-xs text-muted">{emp.count} txns</span>
                           <span className="text-sm font-medium text-rose-400">
                             {formatCurrency(emp.value)}
                           </span>
                         </div>
                       </div>
                     ))}
                   </div>
                 </div>
               )}

               {data.personal_expense_analysis.by_department && data.personal_expense_analysis.by_department.length > 0 && (
                 <div>
                   <h4 className="text-sm font-medium text-muted mb-3 flex items-center gap-2">
                     <Users size={14} /> By Department
                   </h4>
                   <div className="space-y-2">
                     {data.personal_expense_analysis.by_department.slice(0, 5).map((dept, i) => (
                       <div key={i} className="flex items-center justify-between p-2 rounded-lg bg-white/5">
                         <span className="text-sm truncate max-w-48">{dept.department}</span>
                         <div className="flex items-center gap-4">
                           <span className="text-xs text-muted">{dept.count} txns</span>
                           <span className="text-sm font-medium text-rose-400">
                             {formatCurrency(dept.value)}
                           </span>
                         </div>
                       </div>
                     ))}
                   </div>
                 </div>
               )}
             </div>
           ) : null}

           {data.personal_expense_analysis.overall_risk_outcomes?.length > 0 && (
             <div className="mb-4">
               <h4 className="text-sm font-medium text-muted mb-2">Overall Risk Outcomes</h4>
               <ul className="list-disc list-inside text-sm text-red-400 space-y-1 bg-red-500/5 p-3 rounded-lg">
                 {data.personal_expense_analysis.overall_risk_outcomes.map((r, i) => (
                   <li key={i}>{r}</li>
                 ))}
               </ul>
             </div>
           )}

           {data.personal_expense_analysis.overall_recommended_actions?.length > 0 && (
             <div>
               <h4 className="text-sm font-medium text-muted mb-2">Recommended Actions</h4>
               <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                 {data.personal_expense_analysis.overall_recommended_actions.map((a, i) => (
                   <div
                     key={i}
                     className={cn(
                       "p-3 rounded-lg border",
                       a.priority === "high" ? "border-red-500/30 bg-red-500/5" :
                       a.priority === "medium" ? "border-amber-500/30 bg-amber-500/5" :
                       "border-emerald-500/30 bg-emerald-500/5"
                     )}
                   >
                     <div className="flex items-center justify-between mb-1">
                       <span className="font-medium text-sm">{a.action}</span>
                       <span
                         className={cn(
                           "text-xs px-2 py-0.5 rounded-full capitalize",
                           a.priority === "high" ? "bg-red-500/10 text-red-400" :
                           a.priority === "medium" ? "bg-amber-500/10 text-amber-400" :
                           "bg-emerald-500/10 text-emerald-400"
                         )}
                       >
                         {a.priority}
                       </span>
                     </div>
                     <p className="text-xs text-muted">{a.description}</p>
                   </div>
                 ))}
               </div>
             </div>
           )}
         </motion.div>
       )}
     </motion.div>
   );
 }
