"use client";

import { useState, useRef, useEffect } from "react";
import { motion } from "framer-motion";
import { Send, Bot, User, Sparkles, Loader2 } from "lucide-react";
import { api, ChatResponse } from "@/lib/api";
import { useAppStore } from "@/store/appStore";
import { cn } from "@/lib/utils";

const suggestions = [
  "Which department overspent the most?",
  "Show suspicious transactions",
  "Top vendors this period",
  "Any personal expenses?",
  "Are there any duplicates?",
  "Predict next month spend",
];

export default function AiAssistantPage() {
  const { sessionId } = useAppStore();
  const [messages, setMessages] = useState<{ role: "user" | "assistant"; content: string; ai?: boolean; ai_provider?: string }[]>([
    { role: "assistant", content: "Hi! I'm your Expense AI assistant. Ask me anything about your expense data." },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [selectedMode, setSelectedMode] = useState<"groq" | "none">("none");
  const chatRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (chatRef.current) {
      chatRef.current.scrollTop = chatRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = async (msg?: string) => {
    const text = (msg || input).trim();
    if (!text || !sessionId) return;

    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setInput("");
    setLoading(true);

    try {
      const result = await api.chat(sessionId, text, selectedMode);
      setMessages((prev) => [...prev, { role: "assistant", content: result.response, ai: result.ai, ai_provider: result.ai_provider }]);
    } catch (e: any) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Sorry, I encountered an error. Please try again." },
      ]);
    }
    setLoading(false);
  };

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex flex-col h-full max-w-4xl mx-auto">
       <div className="stats-card mb-4">
         <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
           <div className="flex items-center gap-3">
             <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500/20 to-cyan-500/20 flex items-center justify-center">
               <Bot size={20} className="text-indigo-400" />
             </div>
             <div>
               <div className="flex items-center gap-2">
                 <h2 className="font-semibold">AI Expense Assistant</h2>
                 {(() => {
                   const lastAi = [...messages].reverse().find((m) => m.ai === true);
                   const hasAnyAi = messages.some((m) => m.ai === true);
                   if (lastAi?.ai_provider === "groq") {
                     return <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">Groq AI</span>;
                   }
                   if (hasAnyAi) {
                     return <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">AI Powered</span>;
                   }
                   if (messages.length > 1) {
                     return <span className="text-xs px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20">Rule-based mode</span>;
                   }
                   return null;
                 })()}
               </div>
               <p className="text-xs text-muted">Powered by natural language processing</p>
             </div>
           </div>
           <div className="flex items-center gap-2 bg-white/5 rounded-xl p-1">
             <button
               onClick={() => setSelectedMode("none")}
               disabled={loading}
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
               disabled={loading}
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
         </div>
       </div>

      {!sessionId ? (
        <div className="flex-1 stats-card flex items-center justify-center text-center py-12">
          <div>
            <Bot size={48} className="mx-auto mb-4 text-muted" />
            <h3 className="text-lg font-semibold mb-2">Upload Data First</h3>
            <p className="text-muted">Upload and process expense data to start asking questions</p>
          </div>
        </div>
      ) : (
        <>
          <div
            ref={chatRef}
            className="flex-1 chart-container overflow-y-auto space-y-4 mb-4 max-h-[500px]"
          >
            {messages.map((msg, i) => (
              <div
                key={i}
                className={cn(
                  "flex gap-3",
                  msg.role === "user" ? "justify-end" : "justify-start"
                )}
              >
                <div
                  className={cn(
                    "max-w-[80%] p-4 rounded-2xl text-sm",
                    msg.role === "user"
                      ? "bg-indigo-500 text-white"
                      : "bg-white/5 border border-white/10"
                  )}
                >
                  <div className="flex items-center gap-2 mb-1">
                    {msg.role === "assistant" ? (
                      <Bot size={12} className="text-indigo-400" />
                    ) : (
                      <User size={12} className="text-white/70" />
                    )}
                    <span className="text-xs opacity-70">
                      {msg.role === "assistant" ? "AI" : "You"}
                    </span>
                  </div>
                  <p className="whitespace-pre-wrap">{msg.content}</p>
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex gap-3">
                <div className="bg-white/5 border border-white/10 rounded-2xl p-4 text-sm">
                  <Loader2 size={16} className="animate-spin text-indigo-400" />
                </div>
              </div>
            )}
          </div>

          <div className="flex flex-wrap gap-2 mb-4">
            {suggestions.map((s, i) => (
              <button
                key={i}
                onClick={() => handleSend(s)}
                className="text-xs px-3 py-1.5 rounded-full bg-white/5 border border-white/10 text-muted hover:text-white hover:bg-white/10 transition-all"
              >
                {s}
              </button>
            ))}
          </div>

          <div className="flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSend()}
              placeholder="Ask about your expense data..."
              className="flex-1 glass-input rounded-xl px-4 py-3 text-sm outline-none focus:border-indigo-500/50 transition-colors"
              disabled={loading}
            />
            <button
              onClick={() => handleSend()}
              disabled={loading || !input.trim()}
              className="px-4 py-3 bg-indigo-500 hover:bg-indigo-600 disabled:opacity-50 text-white rounded-xl transition-all"
            >
              <Send size={18} />
            </button>
          </div>
        </>
      )}
    </motion.div>
  );
}
