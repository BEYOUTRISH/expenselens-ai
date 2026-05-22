"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { TrendingUp, LineChart, AlertCircle } from "lucide-react";
import {
  LineChart as RechartsLineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Area, AreaChart, Legend,
} from "recharts";
import { api, ForecastResponse } from "@/lib/api";
import { useAppStore } from "@/store/appStore";
import { formatCurrency, formatCompactCurrency } from "@/lib/utils";

export default function ForecastingPage() {
  const { sessionId } = useAppStore();
  const [data, setData] = useState<ForecastResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [periods, setPeriods] = useState(6);

  useEffect(() => {
    async function load() {
      if (!sessionId) { setLoading(false); return; }
      try {
        const result = await api.forecast(sessionId, periods);
        setData(result);
      } catch (e) { console.error(e); }
      setLoading(false);
    }
    load();
  }, [sessionId, periods]);

  const chartData = [];
  if (data?.historical) {
    for (const h of data.historical) {
      chartData.push({ date: h.ds, historical: h.y, forecast: null, lower: null, upper: null });
    }
  }
  if (data?.forecast) {
    for (const f of data.forecast) {
      chartData.push({ date: f.ds, historical: null, forecast: f.yhat, lower: f.yhat_lower, upper: f.yhat_upper });
    }
  }

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
      <div className="stats-card">
        <div className="flex items-center gap-3 mb-2">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500/20 to-teal-500/20 flex items-center justify-center">
            <TrendingUp size={20} className="text-emerald-400" />
          </div>
          <div>
            <h2 className="text-xl font-bold">Expense Forecasting</h2>
            <p className="text-sm text-muted">Predict future spending with AI-powered time series analysis</p>
          </div>
        </div>
      </div>

      {data?.error && (
        <div className="stats-card flex items-center gap-3 text-amber-400">
          <AlertCircle size={18} />
          <span className="text-sm">{data.error}</span>
        </div>
      )}

      {!sessionId ? (
        <div className="stats-card text-center py-12">
          <LineChart size={40} className="mx-auto mb-4 text-muted" />
          <h3 className="text-lg font-semibold mb-2">No Data to Forecast</h3>
          <p className="text-muted">Upload and process expense data first</p>
        </div>
      ) : loading ? (
        <div className="space-y-4">
          <div className="skeleton h-80 rounded-2xl" />
        </div>
      ) : (
        <>
          <div className="flex items-center gap-4 mb-4">
            <span className="text-sm text-muted">Forecast periods:</span>
            {[3, 6, 12].map((p) => (
              <button
                key={p}
                onClick={() => setPeriods(p)}
                className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                  periods === p ? "bg-indigo-500 text-white" : "bg-white/5 text-muted hover:text-white"
                }`}
              >
                {p} months
              </button>
            ))}
          </div>

          <div className="chart-container">
            <h3 className="font-semibold mb-4">Expense Projection</h3>
            <ResponsiveContainer width="100%" height={400}>
              <AreaChart data={chartData}>
                <defs>
                  <linearGradient id="forecastGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.15} />
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.1)" />
                 <XAxis dataKey="date" tick={{ fontSize: 11 }} stroke="rgba(148,163,184,0.5)" />
                 <YAxis tickFormatter={(value) => formatCompactCurrency(value)} tick={{ fontSize: 12 }} stroke="rgba(148,163,184,0.5)" />
                 <Tooltip
                   contentStyle={{ background: "rgba(15,23,42,0.9)", border: "1px solid rgba(51,65,85,0.5)", borderRadius: "12px" }}
                 />
                <Legend />
                <Area type="monotone" dataKey="upper" stroke="none" fill="rgba(16,185,129,0.05)" name="Confidence Upper" />
                <Area type="monotone" dataKey="lower" stroke="none" fill="rgba(16,185,129,0.05)" name="Confidence Lower" />
                <Line type="monotone" dataKey="historical" stroke="#6366f1" strokeWidth={2} dot={false} name="Historical" connectNulls />
                <Line type="monotone" dataKey="forecast" stroke="#10b981" strokeWidth={2} strokeDasharray="5 5" dot={false} name="Forecast" connectNulls />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          {data?.metrics && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="stats-card">
                <div className="text-sm text-muted">Mean Monthly Spend</div>
                <div className="text-xl font-bold">{formatCurrency(data.metrics.mean_monthly)}</div>
              </div>
              <div className="stats-card">
                <div className="text-sm text-muted">Monthly Trend</div>
                <div className="text-xl font-bold">{data.metrics.trend > 0 ? "+" : ""}{formatCurrency(data.metrics.trend)}/mo</div>
              </div>
              <div className="stats-card">
                <div className="text-sm text-muted">Volatility</div>
                <div className="text-xl font-bold">{formatCurrency(data.metrics.volatility)}</div>
              </div>
            </div>
          )}
        </>
      )}
    </motion.div>
  );
}
