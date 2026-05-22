"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend, Line, AreaChart, Area,
} from "recharts";
import { api, DeptData, VendorData, EmployeeData, TimelineData } from "@/lib/api";
import { useAppStore } from "@/store/appStore";
import { formatCurrency, cn, formatNumber, formatCompactCurrency, formatCompactNumber } from "@/lib/utils";

const COLORS = ["#6366f1", "#06b6d4", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#ec4899", "#14b8a6"];

type Tab = "departments" | "vendors" | "employees" | "timeline";

interface TooltipPayloadItem {
  name?: string;
  value?: number;
  color?: string;
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: TooltipPayloadItem[];
  label?: string;
}

function CustomTooltip({ active, payload, label }: CustomTooltipProps) {
  if (active && payload && payload.length) {
    return (
      <div className="bg-slate-900/95 border border-slate-700 rounded-xl p-3 text-sm">
        <p className="font-semibold mb-2">{label}</p>
        {payload.map((entry, index) => (
          <p key={index} style={{ color: entry.color }}>
            {entry.name}: {formatNumber(entry.value || 0)}
          </p>
        ))}
      </div>
    );
  }
  return null;
}

export default function AnalyticsPage() {
  const { sessionId } = useAppStore();
  const [activeTab, setActiveTab] = useState<Tab>("departments");
  const [departments, setDepartments] = useState<DeptData[]>([]);
  const [vendors, setVendors] = useState<VendorData[]>([]);
  const [employees, setEmployees] = useState<EmployeeData[]>([]);
  const [timeline, setTimeline] = useState<TimelineData[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      if (!sessionId) { setLoading(false); return; }
      try {
        const [d, v, e, t] = await Promise.all([
          api.departments(sessionId),
          api.vendors(sessionId, 20),
          api.employees(sessionId),
          api.timeline(sessionId),
        ]);
        setDepartments(d);
        setVendors(v);
        setEmployees(e);
        setTimeline(t);
      } catch (err) { console.error(err); }
      setLoading(false);
    }
    load();
  }, [sessionId]);

  const tabs: { key: Tab; label: string }[] = [
    { key: "departments", label: "Departments" },
    { key: "vendors", label: "Vendors" },
    { key: "employees", label: "Employees" },
    { key: "timeline", label: "Timeline" },
  ];

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
      <div className="flex gap-2 flex-wrap">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={cn(
              "px-4 py-2 rounded-xl text-sm font-medium transition-all",
              activeTab === tab.key
                ? "bg-indigo-500 text-white"
                : "bg-white/5 text-muted hover:text-white hover:bg-white/10"
            )}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="space-y-4">
          <div className="skeleton h-80 rounded-2xl" />
        </div>
      ) : (
        <>
          {activeTab === "departments" && (
            <DepartmentsContent departments={departments} />
          )}

          {activeTab === "vendors" && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="chart-container">
                <h3 className="font-semibold mb-4">Vendor Spend (Top 10)</h3>
                <ResponsiveContainer width="100%" height={400}>
                  <BarChart data={vendors.slice(0, 10)} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.1)" />
                    <XAxis type="number" stroke="rgba(148,163,184,0.5)" />
                    <YAxis type="category" dataKey={vendors[0]?.vendor_canonical ? "vendor_canonical" : "vendor_raw"} width={130} tick={{ fontSize: 11 }} stroke="rgba(148,163,184,0.5)" />
                    <Tooltip contentStyle={{ background: "rgba(15,23,42,0.9)", border: "1px solid rgba(51,65,85,0.5)", borderRadius: "12px" }} />
                    <Bar dataKey="total_spend" fill="#6366f1" radius={[0, 8, 8, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <div className="chart-container">
                <h3 className="font-semibold mb-4">Vendor Distribution</h3>
                <ResponsiveContainer width="100%" height={400}>
                  <PieChart>
                    <Pie data={vendors.slice(0, 8)} dataKey="total_spend" nameKey={vendors[0]?.vendor_canonical ? "vendor_canonical" : "vendor_raw"} cx="50%" cy="50%" outerRadius={120} innerRadius={60}>
                      {vendors.slice(0, 8).map((_, i) => (
                        <Cell key={i} fill={COLORS[i % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          {activeTab === "employees" && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="chart-container lg:col-span-2">
                <h3 className="font-semibold mb-4">Employee Spend Ranking</h3>
                <ResponsiveContainer width="100%" height={400}>
                  <BarChart data={employees.slice(0, 15)} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.1)" />
                    <XAxis type="number" stroke="rgba(148,163,184,0.5)" />
                    <YAxis type="category" dataKey="submitted_by" width={140} tick={{ fontSize: 11 }} stroke="rgba(148,163,184,0.5)" />
                    <Tooltip contentStyle={{ background: "rgba(15,23,42,0.9)", border: "1px solid rgba(51,65,85,0.5)", borderRadius: "12px" }} />
                    <Bar dataKey="total_spend" fill="#8b5cf6" radius={[0, 8, 8, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          {activeTab === "timeline" && (
            <div className="chart-container">
              <h3 className="font-semibold mb-4">Expense Timeline</h3>
              <ResponsiveContainer width="100%" height={400}>
                <AreaChart data={timeline}>
                  <defs>
                    <linearGradient id="tlGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.1)" />
                  <XAxis dataKey="date" tick={{ fontSize: 11 }} stroke="rgba(148,163,184,0.5)" />
                  <YAxis tickFormatter={(value) => formatCompactCurrency(value)} tick={{ fontSize: 12 }} stroke="rgba(148,163,184,0.5)" />
                  <Tooltip contentStyle={{ background: "rgba(15,23,42,0.9)", border: "1px solid rgba(51,65,85,0.5)", borderRadius: "12px" }} />
                  <Area type="monotone" dataKey="total_spend" stroke="#6366f1" strokeWidth={2} fill="url(#tlGrad)" />
                  <Line type="monotone" dataKey="count" stroke="#10b981" strokeWidth={2} dot={false} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          )}
        </>
      )}
    </motion.div>
   );
}

function DepartmentsContent({ departments }: { departments: DeptData[] }) {
  const hasBreakdownData = departments.some(
    (d) => d.positive_count !== undefined || d.negative_count !== undefined
  );

  const totals = departments.reduce(
    (acc, d) => ({
      totalRecords: acc.totalRecords + (d.transaction_count || 0),
      positiveCount: acc.positiveCount + (d.positive_count || 0),
      negativeCount: acc.negativeCount + (d.negative_count || 0),
      zeroCount: acc.zeroCount + (d.zero_count || 0),
      totalPositiveValue: acc.totalPositiveValue + (d.total_positive_value || 0),
      totalNegativeValue: acc.totalNegativeValue + (d.total_negative_value || 0),
      totalSpend: acc.totalSpend + (d.total_spend || 0),
    }),
    {
      totalRecords: 0,
      positiveCount: 0,
      negativeCount: 0,
      zeroCount: 0,
      totalPositiveValue: 0,
      totalNegativeValue: 0,
      totalSpend: 0,
    }
  );

  const positiveRate = totals.totalRecords > 0
    ? (totals.positiveCount / totals.totalRecords * 100)
    : 0;

  const netValue = totals.totalPositiveValue - totals.totalNegativeValue;

   if (!hasBreakdownData) {
     return (
       <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
         <div className="chart-container lg:col-span-2">
           <h3 className="font-semibold mb-4">Spend by Department</h3>
           <ResponsiveContainer width="100%" height={350}>
             <BarChart data={departments} layout="vertical">
               <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.1)" />
               <XAxis type="number" tickFormatter={(value) => formatCompactCurrency(value)} tick={{ fontSize: 12 }} stroke="rgba(148,163,184,0.5)" />
               <YAxis type="category" dataKey="department" tick={{ fontSize: 12 }} stroke="rgba(148,163,184,0.5)" width={120} />
               <Tooltip contentStyle={{ background: "rgba(15,23,42,0.9)", border: "1px solid rgba(51,65,85,0.5)", borderRadius: "12px" }} />
               <Bar dataKey="total_spend" fill="#6366f1" radius={[0, 8, 8, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div className="chart-container">
          <h3 className="font-semibold mb-4">Transaction Count</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie data={departments} dataKey="transaction_count" nameKey="department" cx="50%" cy="50%" outerRadius={100}>
                {departments.map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>
         <div className="chart-container">
           <h3 className="font-semibold mb-4">Average Transaction</h3>
           <ResponsiveContainer width="100%" height={300}>
             <BarChart data={departments}>
               <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.1)" />
               <XAxis dataKey="department" tick={{ fontSize: 10 }} stroke="rgba(148,163,184,0.5)" />
               <YAxis tickFormatter={(value) => formatCompactCurrency(value)} tick={{ fontSize: 12 }} stroke="rgba(148,163,184,0.5)" />
               <Tooltip contentStyle={{ background: "rgba(15,23,42,0.9)", border: "1px solid rgba(51,65,85,0.5)", borderRadius: "12px" }} />
               <Bar dataKey="avg_spend" fill="#06b6d4" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
        <div className="glass-card rounded-2xl p-4 min-w-0">
          <div className="text-xs text-muted mb-1">Total Records</div>
          <div className="text-base sm:text-lg lg:text-xl font-bold truncate">{formatNumber(totals.totalRecords)}</div>
        </div>
        <div className="glass-card rounded-2xl p-4 min-w-0">
          <div className="text-xs text-muted mb-1">Positive (Count)</div>
          <div className="text-base sm:text-lg lg:text-xl font-bold text-emerald-400 truncate">{formatNumber(totals.positiveCount)}</div>
          <div className="text-xs text-emerald-400/70 truncate">{formatCurrency(totals.totalPositiveValue)}</div>
        </div>
        <div className="glass-card rounded-2xl p-4 min-w-0">
          <div className="text-xs text-muted mb-1">Negative (Count)</div>
          <div className="text-base sm:text-lg lg:text-xl font-bold text-rose-400 truncate">{formatNumber(totals.negativeCount)}</div>
          <div className="text-xs text-rose-400/70 truncate">{formatCurrency(totals.totalNegativeValue)}</div>
        </div>
        <div className="glass-card rounded-2xl p-4 min-w-0">
          <div className="text-xs text-muted mb-1">Net Value</div>
          <div className={cn("text-base sm:text-lg lg:text-xl font-bold truncate", netValue >= 0 ? "text-emerald-400" : "text-rose-400")}>
            {formatCurrency(netValue)}
          </div>
        </div>
        <div className="glass-card rounded-2xl p-4 min-w-0 sm:col-span-2 lg:col-span-1">
          <div className="text-xs text-muted mb-1">Positive Rate</div>
          <div className="text-base sm:text-lg lg:text-xl font-bold text-indigo-400">{positiveRate.toFixed(1)}%</div>
          <div className="w-full h-2 bg-white/5 rounded-full mt-2 overflow-hidden">
            <div
              className="h-full bg-indigo-500 rounded-full transition-all"
              style={{ width: `${positiveRate}%` }}
            />
          </div>
        </div>
      </div>

       <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
         <div className="chart-container lg:col-span-2">
           <h3 className="font-semibold mb-4">Spend by Department</h3>
           <ResponsiveContainer width="100%" height={300}>
             <BarChart data={departments} layout="vertical">
               <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.1)" />
               <XAxis type="number" tickFormatter={(value) => formatCompactCurrency(value)} tick={{ fontSize: 12 }} stroke="rgba(148,163,184,0.5)" />
               <YAxis type="category" dataKey="department" tick={{ fontSize: 12 }} stroke="rgba(148,163,184,0.5)" width={120} />
               <Tooltip contentStyle={{ background: "rgba(15,23,42,0.9)", border: "1px solid rgba(51,65,85,0.5)", borderRadius: "12px" }} />
               <Bar dataKey="total_spend" fill="#6366f1" radius={[0, 8, 8, 0]} />
             </BarChart>
           </ResponsiveContainer>
         </div>

         <div className="chart-container lg:col-span-2">
           <h3 className="font-semibold mb-4">Positive vs Negative Count by Department</h3>
           <ResponsiveContainer width="100%" height={350}>
             <BarChart data={departments}>
               <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.1)" />
               <XAxis dataKey="department" tick={{ fontSize: 11 }} stroke="rgba(148,163,184,0.5)" angle={-30} textAnchor="end" height={60} />
               <YAxis tickFormatter={(value) => formatCompactNumber(value)} tick={{ fontSize: 12 }} stroke="rgba(148,163,184,0.5)" />
               <Tooltip content={<CustomTooltip />} />
               <Legend />
               <Bar dataKey="positive_count" name="Positive" stackId="a" fill="#10b981" radius={[4, 4, 0, 0]} />
               <Bar dataKey="negative_count" name="Negative" stackId="a" fill="#ef4444" radius={[4, 4, 0, 0]} />
             </BarChart>
           </ResponsiveContainer>
         </div>
       </div>

      <div className="chart-container">
        <h3 className="font-semibold mb-4">Department Breakdown</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-white/10">
                <th className="text-left py-3 px-4 font-medium text-muted">Department</th>
                <th className="text-right py-3 px-4 font-medium text-muted">Total</th>
                <th className="text-right py-3 px-4 font-medium text-muted text-emerald-400">Positive</th>
                <th className="text-right py-3 px-4 font-medium text-muted text-rose-400">Negative</th>
                <th className="text-right py-3 px-4 font-medium text-muted">Zero</th>
                <th className="text-right py-3 px-4 font-medium text-muted">Net Value</th>
                <th className="text-right py-3 px-4 font-medium text-muted">Positive %</th>
              </tr>
            </thead>
            <tbody>
              {departments.map((dept, i) => {
                const total = dept.transaction_count || 0;
                const positive = dept.positive_count || 0;
                const negative = dept.negative_count || 0;
                const zero = dept.zero_count || 0;
                const posValue = dept.total_positive_value || 0;
                const negValue = dept.total_negative_value || 0;
                const net = posValue - negValue;
                const pct = total > 0 ? (positive / total * 100) : 0;

                 return (
                  <tr key={i} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                    <td className="py-3 px-4 font-medium whitespace-nowrap">{dept.department}</td>
                    <td className="py-3 px-4 text-right whitespace-nowrap">{formatNumber(total)}</td>
                    <td className="py-3 px-4 text-right text-emerald-400 whitespace-nowrap">
                      <div>{formatNumber(positive)}</div>
                      <div className="text-xs text-emerald-400/60">{formatCurrency(posValue)}</div>
                    </td>
                    <td className="py-3 px-4 text-right text-rose-400 whitespace-nowrap">
                      <div>{formatNumber(negative)}</div>
                      <div className="text-xs text-rose-400/60">{formatCurrency(negValue)}</div>
                    </td>
                    <td className="py-3 px-4 text-right text-muted whitespace-nowrap">{formatNumber(zero)}</td>
                    <td className={cn("py-3 px-4 text-right font-medium whitespace-nowrap", net >= 0 ? "text-emerald-400" : "text-rose-400")}>
                      {formatCurrency(net)}
                    </td>
                    <td className="py-3 px-4 text-right whitespace-nowrap">
                      <div className="flex items-center justify-end gap-2">
                        <div className="w-16 h-1.5 bg-white/5 rounded-full overflow-hidden">
                          <div
                            className={cn("h-full rounded-full transition-all", pct >= 80 ? "bg-emerald-500" : pct >= 50 ? "bg-indigo-500" : "bg-amber-500")}
                            style={{ width: `${Math.min(100, pct)}%` }}
                          />
                        </div>
                        <span className="text-xs">{pct.toFixed(1)}%</span>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
