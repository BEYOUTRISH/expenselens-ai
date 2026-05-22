"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Settings, Save, DollarSign, Building, Shield, Bot } from "lucide-react";
import { api } from "@/lib/api";
import { toast } from "sonner";

export default function SettingsPage() {
  const [settings, setSettings] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [baseCurrency, setBaseCurrency] = useState("INR");
  const [receiptThreshold, setReceiptThreshold] = useState(5000);
  const [anomalyZscore, setAnomalyZscore] = useState(3.0);
  const [aiProvider, setAiProvider] = useState<"none" | "groq" | "openai">("none");

  useEffect(() => {
    async function load() {
      try {
        const s = await api.settings.get();
        setSettings(s);
         setBaseCurrency(s.base_currency);
         setReceiptThreshold(s.receipt_threshold);
         setAnomalyZscore(s.anomaly_threshold_zscore);
         if (s.ai_provider) {
           setAiProvider(s.ai_provider as "none" | "groq" | "openai");
         }
       } catch (e) { console.error(e); }
      setLoading(false);
    }
    load();
  }, []);

  const handleSave = async () => {
    try {
      await api.settings.update({
        base_currency: baseCurrency,
        receipt_threshold: receiptThreshold,
        anomaly_threshold_zscore: anomalyZscore,
        ai_provider: aiProvider,
      });
      toast.success("Settings saved successfully");
    } catch (e: any) {
      toast.error(e.message || "Failed to save settings");
    }
  };

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6 max-w-3xl mx-auto">
      <div className="stats-card">
        <div className="flex items-center gap-3 mb-2">
          <Settings size={20} className="text-indigo-400" />
          <h2 className="text-xl font-bold">Settings</h2>
        </div>
        <p className="text-sm text-muted">Configure ExpenseLens AI for your organization</p>
      </div>

      <div className="chart-container space-y-6">
        <div>
          <div className="flex items-center gap-2 mb-3">
            <DollarSign size={16} className="text-emerald-400" />
            <h3 className="font-semibold">Currency & Exchange Rates</h3>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-sm text-muted block mb-1">Base Currency</label>
              <select
                value={baseCurrency}
                onChange={(e) => setBaseCurrency(e.target.value)}
                className="glass-input rounded-xl px-4 py-2.5 w-full text-sm outline-none focus:border-indigo-500/50"
              >
                {["INR", "USD", "EUR", "GBP", "SGD", "AED"].map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>
            {settings?.exchange_rates && (
              <div>
                <label className="text-sm text-muted block mb-1">Exchange Rates (1 → {baseCurrency})</label>
                <div className="glass-input rounded-xl p-3 text-sm space-y-1">
                  {Object.entries(settings.exchange_rates).map(([cur, rate]) => (
                    <div key={cur} className="flex justify-between">
                      <span>{cur}</span>
                      <span className="font-mono">{Number(rate).toFixed(4)}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="border-t border-white/10 pt-6">
          <div className="flex items-center gap-2 mb-3">
            <Building size={16} className="text-indigo-400" />
            <h3 className="font-semibold">Departments</h3>
          </div>
          <div className="flex flex-wrap gap-2">
            {["Engineering", "Sales", "Product", "Operations", "Finance"].map((d) => (
              <span key={d} className="px-3 py-1.5 rounded-xl bg-white/5 border border-white/10 text-sm">
                {d}
              </span>
            ))}
          </div>
        </div>

         <div className="border-t border-white/10 pt-6">
           <div className="flex items-center gap-2 mb-3">
             <Shield size={16} className="text-amber-400" />
             <h3 className="font-semibold">Policy Rules</h3>
           </div>
           <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
             <div>
               <label className="text-sm text-muted block mb-1">Receipt Required Above (INR)</label>
               <input
                 type="number"
                 value={receiptThreshold}
                 onChange={(e) => setReceiptThreshold(Number(e.target.value))}
                 className="glass-input rounded-xl px-4 py-2.5 w-full text-sm outline-none focus:border-indigo-500/50"
               />
             </div>
             <div>
               <label className="text-sm text-muted block mb-1">Anomaly Z-Score Threshold</label>
               <input
                 type="number"
                 step="0.1"
                 value={anomalyZscore}
                 onChange={(e) => setAnomalyZscore(Number(e.target.value))}
                 className="glass-input rounded-xl px-4 py-2.5 w-full text-sm outline-none focus:border-indigo-500/50"
               />
             </div>
           </div>
         </div>

         <div className="border-t border-white/10 pt-6">
           <div className="flex items-center gap-2 mb-3">
             <Bot size={16} className="text-emerald-400" />
             <h3 className="font-semibold">AI Settings</h3>
           </div>
           <div>
             <label className="text-sm text-muted block mb-1">Default AI Provider</label>
             <select
               value={aiProvider}
               onChange={(e) => setAiProvider(e.target.value as "none" | "groq" | "openai")}
               className="glass-input rounded-xl px-4 py-2.5 w-full text-sm outline-none focus:border-indigo-500/50"
             >
               <option value="none">Normal (Rule-based only)</option>
               <option value="groq">Groq AI (Llama 3.1)</option>
               <option value="openai">OpenAI (GPT-4o-mini)</option>
             </select>
             <p className="text-xs text-muted mt-2">
               This sets the global default. Individual pages can override this choice.
             </p>
           </div>
         </div>

         <button
          onClick={handleSave}
          className="w-full py-3 bg-gradient-to-r from-indigo-500 to-cyan-500 hover:from-indigo-600 hover:to-cyan-600 text-white rounded-xl font-medium transition-all flex items-center justify-center gap-2"
        >
          <Save size={18} /> Save Settings
        </button>
      </div>
    </motion.div>
  );
}
