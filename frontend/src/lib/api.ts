const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE}${path}`;
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    const error = await res.text();
    throw new Error(`API ${res.status}: ${error}`);
  }
  return res.json();
}

export const api = {
  health: () => request<{ status: string }>("/health"),

  upload: async (file: File) => {
    const form = new FormData();
    form.append("file", file);
    const res = await fetch(`${API_BASE}/upload`, { method: "POST", body: form });
    if (!res.ok) throw new Error(`Upload failed: ${res.statusText}`);
    return res.json() as Promise<UploadResponse>;
  },

  preview: (sessionId: string, rows = 50) =>
    request<PreviewResponse>(`/upload/${sessionId}/preview?rows=${rows}`),

  runCleaning: (sessionId: string) =>
    request<CleaningResponse>(`/cleaning/run/${sessionId}`, { method: "POST" }),

  qualityReport: (sessionId: string) =>
    request<QualityReport>(`/cleaning/quality-report/${sessionId}`),

  applyFix: (sessionId: string, txnRef: string, field: string, newValue: string) =>
    request<any>(`/cleaning/fix/${sessionId}`, {
      method: "POST",
      body: JSON.stringify({ txn_ref: txnRef, field, new_value: newValue }),
    }),

  detectDuplicates: (sessionId: string) =>
    request<any>(`/cleaning/detect-duplicates/${sessionId}`, { method: "POST" }),

  summary: (sessionId: string) =>
    request<SummaryData>(`/analytics/summary/${sessionId}`),

  departments: (sessionId: string) =>
    request<DeptData[]>(`/analytics/departments/${sessionId}`),

  vendors: (sessionId: string, topN = 20) =>
    request<VendorData[]>(`/analytics/vendors/${sessionId}?top_n=${topN}`),

  employees: (sessionId: string) =>
    request<EmployeeData[]>(`/analytics/employees/${sessionId}`),

  timeline: (sessionId: string) =>
    request<TimelineData[]>(`/analytics/timeline/${sessionId}`),

  compliance: (sessionId: string) =>
    request<ComplianceData>(`/analytics/compliance/${sessionId}`),

  anomalies: (sessionId: string) =>
    request<AnomalyResponse>(`/anomalies/${sessionId}`),

  generateInsights: (sessionId: string, aiProvider?: "groq" | "none" | "openai") => {
    const url = aiProvider
      ? `/insights/generate/${sessionId}?ai_provider=${aiProvider}`
      : `/insights/generate/${sessionId}`;
    return request<InsightsResponse>(url, { method: "POST" });
  },

  forecast: (sessionId: string, periods = 6) =>
    request<ForecastResponse>(`/forecasting/${sessionId}?periods=${periods}`),

  chat: (sessionId: string, message: string, aiProvider?: "groq" | "none" | "openai") =>
    request<ChatResponse>(`/assistant/chat`, {
      method: "POST",
      body: JSON.stringify({
        session_id: sessionId,
        message,
        ...(aiProvider !== undefined ? { ai_provider: aiProvider } : {}),
      }),
    }),

  exportData: (sessionId: string, format: "csv" | "xlsx" | "json") =>
    `${API_BASE}/export/${sessionId}/${format}`,

  settings: {
    get: () => request<any>("/settings"),
    update: (data: any) =>
      request<any>("/settings", { method: "POST", body: JSON.stringify(data) }),
  },
};

export interface UploadResponse {
  session_id: string;
  filename: string;
  total_rows: number;
  total_columns: number;
  columns: string[];
  preview: Record<string, any>[];
}

export interface PreviewResponse {
  session_id: string;
  total_rows: number;
  columns: string[];
  preview: Record<string, any>[];
}

export interface CleaningResponse {
  session_id: string;
  total_rows_in_source: number;
  rows_loaded: number;
  rows_excluded: number;
  summary: Record<string, number>;
  cleaned_preview: Record<string, any>[];
}

export interface QualityReport {
  total_rows_in_source: number;
  rows_loaded: number;
  rows_excluded: number;
  issues: QualityIssue[];
  summary: Record<string, number>;
}

export interface QualityIssue {
  txn_id: string;
  field: string;
  issue_type: string;
  severity: "CRITICAL" | "WARNING" | "INFO";
  raw_value: string;
  action_taken: string;
}

export interface SummaryData {
  total_spend: number;
  transaction_count: number;
  average_transaction: number;
  max_transaction: number;
  min_transaction: number;
  anomaly_count: number;
  duplicate_count: number;
  personal_count: number;
  no_receipt_count: number;
  compliance_score: number;
}

export interface DeptData {
  department: string;
  total_spend: number;
  transaction_count: number;
  avg_spend: number;
  positive_count?: number;
  negative_count?: number;
  zero_count?: number;
  total_positive_value?: number;
  total_negative_value?: number;
}

export interface VendorData {
  vendor_canonical?: string;
  vendor_raw?: string;
  total_spend: number;
  transaction_count: number;
  avg_spend: number;
}

export interface EmployeeData {
  submitted_by: string;
  total_spend: number;
  transaction_count: number;
  avg_spend: number;
}

export interface TimelineData {
  date: string;
  total_spend: number;
  count: number;
}

export interface ComplianceData {
  receipt_compliance_rate: number;
  missing_receipts_count: number;
  high_value_without_receipt: Record<string, any>[];
  policy_violations: Record<string, any>[];
}

export interface AnomalyResponse {
  anomalies: AnomalyItem[];
  anomaly_count: number;
  methods_used: string[];
}

export interface AnomalyItem {
  txn_ref: string;
  amount_inr: number;
  vendor: string;
  department: string;
  submitted_by: string;
  entry_date: string;
  description: string;
  anomaly_score: number;
  risk_label: string;
  reasons: string[];
}

export interface InsightsResponse {
  session_id: string;
  summary: Record<string, any>;
  insights: {
    executive_summary: string;
    spending_patterns: string[];
    vendor_analysis: Record<string, any>[];
    department_trends: Record<string, any>[];
    anomaly_insights: string[];
    recommendations: string[];
    risk_signals: string[];
    employee_analysis: EmployeeInsight[];
    vendor_risk: VendorRisk;
    time_patterns: TimePatterns;
    receipt_compliance: ReceiptCompliance;
    duplicate_analysis: DuplicateAnalysis;
    high_value_transactions: HighValueTransactions;
    personal_expense_analysis?: PersonalExpenseAnalysis;
  };
  ai?: boolean;
  ai_provider?: string;
}

export interface EmployeeInsight {
  submitted_by: string;
  total_spend: number;
  transaction_count: number;
  avg_spend: number;
  compliance_rate: number;
}

export interface VendorRisk {
  high_concentration_vendors: { vendor: string; spend_pct: number; total_spend: number }[];
  vendors_with_anomalies: { vendor: string; anomaly_count: number }[];
  vendor_diversity_score: number;
}

export interface TimePatterns {
  day_of_week_patterns: { day: string; total_spend: number; count: number }[];
  busiest_month?: string;
  quietest_month?: string;
  month_end_spike: boolean;
}

export interface ReceiptCompliance {
  overall_rate: number;
  by_department: { department: string; rate: number; with_receipt: number; total: number }[];
  high_value_missing_receipt: { txn_ref: string; amount: number; vendor: string; department: string }[];
}

export interface DuplicateAnalysis {
  confirmed_duplicates: number;
  duplicate_value: number;
  potential_duplicates: number;
}

export interface HighValueTransactions {
  top_1_percent: { txn_ref: string; amount: number; vendor: string; department: string; submitted_by: string; is_flagged: boolean }[];
  threshold: number;
  total_high_value: number;
  count: number;
}

export interface PersonalCategory {
  category: string;
  count: number;
  value: number;
  risk_outcomes: string[];
  recommended_actions: { action: string; priority: string; description: string }[];
}

export interface PersonalKeyword {
  keyword: string;
  count: number;
  value: number;
  category: string;
}

export interface PersonalEmployee {
  employee: string;
  count: number;
  value: number;
}

export interface PersonalDepartment {
  department: string;
  count: number;
  value: number;
}

export interface PersonalExpenseAnalysis {
  total_count: number;
  total_value: number;
  percentage_of_total: number;
  by_category?: PersonalCategory[];
  top_keywords?: PersonalKeyword[];
  by_employee?: PersonalEmployee[];
  by_department?: PersonalDepartment[];
  overall_risk_outcomes: string[];
  overall_recommended_actions: { action: string; priority: string; description: string }[];
}

export interface ForecastResponse {
  historical: { ds: string; y: number }[];
  forecast: { ds: string; yhat: number; yhat_lower: number; yhat_upper: number }[];
  metrics?: Record<string, any>;
  error?: string;
}

export interface ChatResponse {
  response: string;
  message: string;
  ai?: boolean;
  ai_provider?: string;
}
