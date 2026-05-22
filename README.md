# ExpenseLens AI — Expense Intelligence & Financial Analytics Platform

[![Next.js](https://img.shields.io/badge/Next.js-16-black)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://python.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5-blue)](https://typescriptlang.org/)

**ExpenseLens AI** is a production-grade, AI-powered expense intelligence platform that ingests raw CSV/XLSX expense files and automatically cleans, standardizes, reconciles, analyzes, and visualizes financial data with enterprise-level dashboards and insights.

> **Architecture:** Next.js 16 (TypeScript) + FastAPI (Python) + PostgreSQL 15 + Redis

---

## 🚀 Quick Start

### Prerequisites
- Node.js 20+
- Python 3.11+
- PostgreSQL 15+
- Docker (optional)

### Local Development

**1. Backend Setup**
```bash
cd backend
pip install -r requirements.txt

# Set up PostgreSQL database
createdb expenselens
psql -d expenselens -f target_schema.sql

# Start the server
uvicorn app.main:app --reload --port 8000
```

**2. Frontend Setup**
```bash
cd frontend
npm install
npm run dev
```

**3. Open** [http://localhost:3000](http://localhost:3000)

### Docker Setup
```bash
docker compose up --build
```
- Frontend: [http://localhost:3000](http://localhost:3000)
- Backend API: [http://localhost:8000](http://localhost:8000)
- API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🏗 Architecture

```
┌─────────────────────────────────────┐
│       Next.js 16 (App Router)        │
│  TypeScript · TailwindCSS · ShadCN   │
│  Recharts · Framer Motion · Zustand  │
├─────────────────────────────────────┤
│         FastAPI (Python 3.11)         │
│  pandas · scikit-learn · rapidfuzz   │
│  Prophet · LangChain · openpyxl      │
├─────────────────────────────────────┤
│         PostgreSQL 15 + Redis         │
└─────────────────────────────────────┘
```

### Data Pipeline Flow
```
Upload CSV/XLSX
    ↓
Schema Auto-Detection (fuzzy column mapping)
    ↓
Date Parsing (20+ formats + epoch timestamps)
    ↓
Amount Parsing (symbols, codes, Indian notation, sentinels)
    ↓
Currency Detection & Conversion (6 currencies → INR)
    ↓
Vendor Resolution (fuzzy matching + description inference)
    ↓
Department Normalization (fuzzy + typo correction)
    ↓
Duplicate Detection (exact + fuzzy within 3-day window)
    ↓
Personal Expense Detection (keyword-based)
    ↓
Anomaly Detection (Isolation Forest + Z-score + IQR)
    ↓
Cleaned Data + Quality Report
```

---

## ✨ Features

### 📤 Smart File Upload
- Drag-and-drop CSV/XLSX/XLS support
- Auto-detect encoding (chardet) and delimiter
- Preview parsed data before processing
- Upload progress indicators

### 🧹 Intelligent Data Cleaning
- **Column Standardization**: Auto-map headers via fuzzy matching
- **Date Parsing**: 20+ regex patterns + epoch timestamps
- **Amount Parsing**: Currency symbols, embedded codes, Indian comma notation, sentinels
- **Currency Normalization**: 6 currencies → INR with configurable rates
- **Vendor Resolution**: Fuzzy matching + description-based inference
- **Department Normalization**: Fuzzy match against canonical list
- **Duplicate Detection**: Exact + fuzzy (3-day window, description similarity)
- **Personal Expense Detection**: Keyword-based flagging
- **Data Quality Report**: Per-row severity tracking (CRITICAL/WARNING/INFO)

### 📊 Premium Dashboards
- **Executive Dashboard**: Total spend, trends, KPIs, compliance score
- **Department Analytics**: Spend & budget comparison
- **Vendor Intelligence**: Concentration, frequency, risk
- **Employee Analytics**: Top spenders, patterns
- **Time Analytics**: Monthly/weekly trends with moving averages
- **Compliance Dashboard**: Receipt compliance, policy breaches
- **Anomaly Dashboard**: ML-powered detection with explanations

### 🤖 AI Engine
- **Financial Narrative Reports**: Auto-generated executive summaries
- **AI Chat Assistant**: Natural language querying over expense data
- **Anomaly Detection**: Isolation Forest + Z-score + IQR + rule-based
- **Expense Forecasting**: Statistical projection with confidence intervals
- **Smart Categorization**: Rule-based + TF-IDF classification

### 📋 Data Quality Center
- Overall quality scoring (0-100)
- Interactive issue table with severity filtering
- Per-issue action tracking
- Auto-fix suggestions

### 📤 Smart Export
- CSV, XLSX (formatted), JSON exports
- Cleaned dataset download

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/upload` | Upload CSV/XLSX file |
| GET | `/api/upload/{id}/preview` | Preview parsed data |
| POST | `/api/cleaning/run/{id}` | Execute cleaning pipeline |
| GET | `/api/cleaning/quality-report/{id}` | Get quality report |
| POST | `/api/cleaning/fix/{id}` | Apply specific fix |
| POST | `/api/cleaning/detect-duplicates/{id}` | Run dedup detection |
| GET | `/api/analytics/summary/{id}` | Executive summary |
| GET | `/api/analytics/departments/{id}` | Department breakdown |
| GET | `/api/analytics/vendors/{id}` | Vendor intelligence |
| GET | `/api/analytics/employees/{id}` | Employee analysis |
| GET | `/api/analytics/timeline/{id}` | Time series data |
| GET | `/api/analytics/compliance/{id}` | Compliance metrics |
| GET | `/api/anomalies/{id}` | Anomaly detection |
| POST | `/api/insights/generate/{id}` | Generate AI report |
| POST | `/api/assistant/chat` | Chat with AI |
| GET | `/api/forecasting/{id}` | Expense forecast |
| GET | `/api/export/{id}/{format}` | Export cleaned data |
| GET | `/api/settings` | Get configuration |
| POST | `/api/settings` | Update configuration |

---

## 🗄 Database Schema (PostgreSQL 15)

10 tables, 3 views, 11 indexes:
- `currencies`, `departments`, `cost_centers`, `employees`
- `exchange_rates`, `vendors`, `vendor_aliases`, `expense_categories`
- `ledger_entries` (main fact table), `audit_log`
- Views: `v_flagged_entries`, `v_department_budget_utilisation`, `v_vendor_spend_summary`

---

## 📂 Project Structure

```
expenselens/
├── frontend/                          # Next.js 16 App
│   ├── src/
│   │   ├── app/                       # App Router pages
│   │   │   ├── (landing)/             # Marketing page
│   │   │   └── dashboard/             # Protected routes
│   │   │       ├── upload/            # File upload page
│   │   │       ├── analytics/         # Department/Vendor/Employee views
│   │   │       ├── data-quality/      # Quality center
│   │   │       ├── insights/          # AI narrative reports
│   │   │       ├── ai-assistant/      # Chat interface
│   │   │       ├── forecasting/       # Expense predictions
│   │   │       ├── reports/           # Export center
│   │   │       └── settings/          # App configuration
│   │   ├── components/
│   │   │   ├── layout/                # Sidebar, TopBar, ThemeProvider
│   │   │   └── ...                    # UI components
│   │   ├── lib/api.ts                 # API client
│   │   ├── lib/utils.ts               # Utility functions
│   │   ├── store/appStore.ts          # Zustand state
│   │   └── types/                     # TypeScript types
│   └── package.json
│
├── backend/                           # FastAPI
│   ├── app/
│   │   ├── api/                       # Route handlers
│   │   │   ├── upload.py
│   │   │   ├── cleaning.py
│   │   │   ├── analytics.py
│   │   │   ├── anomalies.py
│   │   │   ├── insights.py
│   │   │   ├── forecasting.py
│   │   │   ├── assistant.py
│   │   │   ├── export.py
│   │   │   └── settings_route.py
│   │   ├── core/                      # DB, config, logging
│   │   ├── models/models.py           # SQLAlchemy models
│   │   ├── services/cleaning/         # Core data pipeline
│   │   │   ├── engine.py              # Orchestrator
│   │   │   ├── schema_detector.py     # Auto-map columns
│   │   │   ├── date_parser.py         # 20+ date formats
│   │   │   ├── amount_parser.py       # Amount extraction
│   │   │   ├── currency_converter.py  # INR conversion
│   │   │   ├── vendor_resolver.py     # Fuzzy vendor match
│   │   │   ├── department_normalizer.py
│   │   │   ├── deduplicator.py        # Exact + fuzzy dedup
│   │   │   ├── personal_detector.py   # Keyword detection
│   │   │   ├── missing_handler.py     # Severity classification
│   │   │   ├── quality_reporter.py    # Report generation
│   │   │   └── validator.py           # Reusable class
│   │   └── ml/
│   │       ├── anomaly_detector.py    # Isolation Forest + Z-score
│   │       └── forecast_engine.py     # Prophet wrapper
│   ├── target_schema.sql              # PostgreSQL DDL
│   ├── sample_data/                   # Test fixtures
│   ├── requirements.txt
│   └── Dockerfile
│
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 🛠 Tech Stack

### Frontend
- **Framework**: Next.js 16 (App Router)
- **Language**: TypeScript 5
- **Styling**: Tailwind CSS 4, CSS variables, glassmorphism
- **Components**: ShadCN UI primitives
- **Charts**: Recharts (area, bar, pie, scatter, radial gauge)
- **Animation**: Framer Motion
- **State**: Zustand
- **Tables**: TanStack Table
- **Notifications**: Sonner
- **Upload**: react-dropzone

### Backend
- **Framework**: FastAPI 0.115
- **Language**: Python 3.11
- **Data**: pandas, numpy, openpyxl
- **ML**: scikit-learn (Isolation Forest)
- **Text**: rapidfuzz (fuzzy matching)
- **AI**: LangChain, OpenAI (optional)
- **Forecasting**: Prophet (optional)
- **Database**: SQLAlchemy 2.0 + PostgreSQL 15
- **PDF**: reportlab

---

## 🔐 Environment Variables

See `.env.example`:
```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/expenselens
REDIS_URL=redis://localhost:6379/0
OPENAI_API_KEY=sk-...           # Optional - for AI features
OPENAI_MODEL=gpt-4o-mini
ENVIRONMENT=development
BASE_CURRENCY=INR
SECRET_KEY=change-in-production
```

---

## 📊 Sample Data

A test fixture `dirty_expenses.xlsx` (18,736 rows, 12 columns) is included in `backend/sample_data/` with:
- 50+ vendors with multiple aliases for dedup testing
- 12 departments, 30 cost centers
- Mixed currencies (INR, USD, EUR, GBP, SGD, AED)
- Intentional anomalies (5%), missing data (8%), duplicates (3%)
- Date range: Jan 2024 – May 2026
- 15+ date formats including epoch timestamps
- Indian comma notation amounts
- Personal expenses, sentinel values, department typos

---

## 👨‍💻 Development

```bash
# Backend (with hot reload)
cd backend
uvicorn app.main:app --reload --port 8000

# Frontend (with hot reload)
cd frontend
npm run dev

# Lint
cd frontend && npm run lint
```

---

## 📄 License

MIT
