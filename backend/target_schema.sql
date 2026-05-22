-- ==============================================================
-- Target Schema: ExpenseLens AI ERP Platform
-- PostgreSQL 15+ DDL
-- ==============================================================

-- 1. CURRENCIES
CREATE TABLE IF NOT EXISTS currencies (
    currency_code CHAR(3) PRIMARY KEY,
    currency_name VARCHAR(100) NOT NULL,
    symbol VARCHAR(10)
);

INSERT INTO currencies (currency_code, currency_name, symbol) VALUES
    ('INR', 'Indian Rupee', '₹'),
    ('USD', 'US Dollar', '$'),
    ('EUR', 'Euro', '€'),
    ('GBP', 'British Pound', '£'),
    ('SGD', 'Singapore Dollar', 'S$'),
    ('AED', 'UAE Dirham', 'د.إ')
ON CONFLICT (currency_code) DO NOTHING;

-- 2. DEPARTMENTS
CREATE TABLE IF NOT EXISTS departments (
    dept_id SERIAL PRIMARY KEY,
    dept_name VARCHAR(200) NOT NULL UNIQUE,
    dept_code VARCHAR(10) NOT NULL UNIQUE
);

INSERT INTO departments (dept_name, dept_code) VALUES
    ('Engineering', 'ENGG'),
    ('Sales', 'SALES'),
    ('Product', 'PROD'),
    ('Operations', 'OPS'),
    ('Finance', 'FIN')
ON CONFLICT (dept_name) DO NOTHING;

-- 3. COST CENTERS
CREATE TABLE IF NOT EXISTS cost_centers (
    cc_id SERIAL PRIMARY KEY,
    dept_id INT NOT NULL REFERENCES departments(dept_id),
    cc_code VARCHAR(10) NOT NULL UNIQUE,
    cc_name VARCHAR(200) NOT NULL,
    annual_budget_inr NUMERIC(15,2) NOT NULL CHECK (annual_budget_inr >= 0)
);

INSERT INTO cost_centers (dept_id, cc_code, cc_name, annual_budget_inr) VALUES
    (1, 'CC001', 'Engineering Core', 12000000),
    (2, 'CC002', 'Sales & Marketing', 8000000),
    (3, 'CC003', 'Product Development', 6000000),
    (4, 'CC004', 'Operations & Admin', 9000000),
    (5, 'CC005', 'Finance & Accounting', 4000000)
ON CONFLICT (cc_code) DO NOTHING;

-- 4. EMPLOYEES
CREATE TABLE IF NOT EXISTS employees (
    employee_id SERIAL PRIMARY KEY,
    full_name VARCHAR(200) NOT NULL,
    email VARCHAR(300) UNIQUE NOT NULL,
    dept_id INT REFERENCES departments(dept_id),
    cost_center_id INT REFERENCES cost_centers(cc_id),
    role VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. EXCHANGE RATES
CREATE TABLE IF NOT EXISTS exchange_rates (
    rate_id SERIAL PRIMARY KEY,
    from_currency CHAR(3) NOT NULL REFERENCES currencies(currency_code),
    to_currency CHAR(3) NOT NULL REFERENCES currencies(currency_code),
    rate NUMERIC(12,6) NOT NULL CHECK (rate > 0),
    effective_date DATE NOT NULL,
    source VARCHAR(50) DEFAULT 'RBI_REFERENCE',
    UNIQUE (from_currency, to_currency, effective_date),
    CHECK (from_currency <> to_currency)
);

INSERT INTO exchange_rates (from_currency, to_currency, rate, effective_date) VALUES
    ('USD', 'INR', 83.500000, '2026-04-01'),
    ('EUR', 'INR', 91.200000, '2026-04-01'),
    ('GBP', 'INR', 106.400000, '2026-04-01'),
    ('SGD', 'INR', 62.300000, '2026-04-01'),
    ('AED', 'INR', 22.730000, '2026-04-01')
ON CONFLICT (from_currency, to_currency, effective_date) DO NOTHING;

-- 6. VENDORS
CREATE TABLE IF NOT EXISTS vendors (
    vendor_id SERIAL PRIMARY KEY,
    canonical_name VARCHAR(200) UNIQUE NOT NULL,
    vendor_type VARCHAR(50),
    country_code CHAR(2),
    gstin VARCHAR(20),
    preferred_currency CHAR(3) REFERENCES currencies(currency_code),
    is_approved BOOLEAN DEFAULT FALSE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS vendor_aliases (
    alias_id SERIAL PRIMARY KEY,
    vendor_id INT NOT NULL REFERENCES vendors(vendor_id) ON DELETE CASCADE,
    alias_name VARCHAR(200) NOT NULL UNIQUE
);

-- 7. EXPENSE CATEGORIES
CREATE TABLE IF NOT EXISTS expense_categories (
    category_id SERIAL PRIMARY KEY,
    category_code VARCHAR(20) UNIQUE NOT NULL,
    category_name VARCHAR(100) NOT NULL,
    parent_category_id INT REFERENCES expense_categories(category_id),
    is_reimbursable BOOLEAN DEFAULT TRUE,
    receipt_threshold_inr NUMERIC(10,2) DEFAULT 500.00,
    description TEXT
);

INSERT INTO expense_categories (category_code, category_name, is_reimbursable, receipt_threshold_inr, description) VALUES
    ('CLOUD', 'Cloud Infrastructure', TRUE, 500.00, 'Cloud compute, storage, networking, and managed services'),
    ('SAAS', 'SaaS Subscriptions', TRUE, 500.00, 'Third-party software licenses and subscription renewals'),
    ('TRAVEL', 'Travel & Transport', TRUE, 500.00, 'Flights, cabs, hotels, and ground transport for business purposes'),
    ('FOOD', 'Meals & Catering', TRUE, 1000.00, 'Team meals, client entertainment, and event catering'),
    ('HARDWARE', 'Hardware & Equipment', TRUE, 1000.00, 'Physical devices, peripherals, and office equipment'),
    ('FINANCE', 'Finance & Banking', TRUE, 0.00, 'Payment gateway fees, banking charges, and disbursement costs'),
    ('PERSONAL', 'Personal Expense', FALSE, 0.00, 'Non-business personal expenses - not reimbursable'),
    ('OTHER', 'Miscellaneous', TRUE, 500.00, 'Expenses that do not fit any other category')
ON CONFLICT (category_code) DO NOTHING;

-- 8. LEDGER ENTRIES (main fact table)
CREATE TABLE IF NOT EXISTS ledger_entries (
    entry_id SERIAL PRIMARY KEY,
    txn_ref VARCHAR(20) UNIQUE NOT NULL,
    entry_date DATE NOT NULL,
    submission_date DATE,
    amount_raw_value NUMERIC(18,4) NOT NULL,
    original_currency CHAR(3) REFERENCES currencies(currency_code),
    exchange_rate_used NUMERIC(12,6),
    amount_inr NUMERIC(15,2) NOT NULL,
    vendor_id INT REFERENCES vendors(vendor_id),
    category_id INT REFERENCES expense_categories(category_id),
    cost_center_id INT REFERENCES cost_centers(cc_id),
    submitted_by INT REFERENCES employees(employee_id),
    approved_by INT REFERENCES employees(employee_id),
    description TEXT,
    receipt_attached BOOLEAN DEFAULT FALSE,
    is_flagged BOOLEAN DEFAULT FALSE,
    flag_reason TEXT,
    is_duplicate BOOLEAN DEFAULT FALSE,
    duplicate_of VARCHAR(20),
    is_personal BOOLEAN DEFAULT FALSE,
    approval_status VARCHAR(20) DEFAULT 'pending' CHECK (approval_status IN ('pending', 'approved', 'rejected', 'under_review')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_nonzero_raw CHECK (amount_raw_value <> 0),
    CONSTRAINT chk_currency_if_rate CHECK (
        (exchange_rate_used IS NULL AND original_currency = 'INR')
        OR (exchange_rate_used IS NOT NULL)
    ),
    CONSTRAINT chk_duplicate_ref CHECK (
        (is_duplicate = FALSE AND duplicate_of IS NULL)
        OR (is_duplicate = TRUE AND duplicate_of IS NOT NULL)
    )
);

-- 9. AUDIT LOG
CREATE TABLE IF NOT EXISTS audit_log (
    log_id SERIAL PRIMARY KEY,
    table_name VARCHAR(60) NOT NULL,
    record_id INT NOT NULL,
    action VARCHAR(10) NOT NULL CHECK (action IN ('INSERT', 'UPDATE', 'DELETE')),
    changed_by VARCHAR(150),
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    old_values JSONB,
    new_values JSONB
);

-- 10. INDEXES
CREATE INDEX IF NOT EXISTS idx_ledger_entry_date ON ledger_entries(entry_date);
CREATE INDEX IF NOT EXISTS idx_ledger_vendor ON ledger_entries(vendor_id);
CREATE INDEX IF NOT EXISTS idx_ledger_cost_center ON ledger_entries(cost_center_id);
CREATE INDEX IF NOT EXISTS idx_ledger_submitted_by ON ledger_entries(submitted_by);
CREATE INDEX IF NOT EXISTS idx_ledger_approval ON ledger_entries(approval_status);
CREATE INDEX IF NOT EXISTS idx_ledger_flagged ON ledger_entries(is_flagged) WHERE is_flagged = TRUE;
CREATE INDEX IF NOT EXISTS idx_ledger_personal ON ledger_entries(is_personal) WHERE is_personal = TRUE;
CREATE INDEX IF NOT EXISTS idx_ledger_duplicate ON ledger_entries(is_duplicate) WHERE is_duplicate = TRUE;
CREATE INDEX IF NOT EXISTS idx_vendor_alias_name ON vendor_aliases(alias_name);
CREATE INDEX IF NOT EXISTS idx_xrates_lookup ON exchange_rates(from_currency, to_currency, effective_date);
CREATE INDEX IF NOT EXISTS idx_audit_table_record ON audit_log(table_name, record_id);

-- 11. VIEWS
CREATE OR REPLACE VIEW v_flagged_entries AS
SELECT
    le.txn_ref,
    le.entry_date,
    le.amount_inr,
    v.canonical_name AS vendor,
    ec.category_name AS category,
    e.full_name AS submitted_by,
    d.dept_name AS department,
    cc.cc_code AS cost_center,
    le.flag_reason,
    le.is_duplicate,
    le.duplicate_of,
    le.is_personal,
    le.approval_status
FROM ledger_entries le
LEFT JOIN vendors v ON le.vendor_id = v.vendor_id
LEFT JOIN expense_categories ec ON le.category_id = ec.category_id
LEFT JOIN employees e ON le.submitted_by = e.employee_id
LEFT JOIN cost_centers cc ON le.cost_center_id = cc.cc_id
LEFT JOIN departments d ON cc.dept_id = d.dept_id
WHERE le.is_flagged = TRUE;

CREATE OR REPLACE VIEW v_department_budget_utilisation AS
SELECT
    d.dept_name,
    cc.cc_code,
    cc.annual_budget_inr AS budget_inr,
    COALESCE(SUM(le.amount_inr), 0) AS spent_inr,
    cc.annual_budget_inr - COALESCE(SUM(le.amount_inr), 0) AS remaining_inr,
    ROUND(
        COALESCE(SUM(le.amount_inr), 0) / NULLIF(cc.annual_budget_inr, 0) * 100, 2
    ) AS utilisation_pct
FROM cost_centers cc
JOIN departments d ON cc.dept_id = d.dept_id
LEFT JOIN ledger_entries le ON le.cost_center_id = cc.cc_id AND le.approval_status = 'approved'
GROUP BY d.dept_name, cc.cc_code, cc.annual_budget_inr
ORDER BY utilisation_pct DESC NULLS LAST;

CREATE OR REPLACE VIEW v_vendor_spend_summary AS
SELECT
    v.canonical_name AS vendor,
    v.vendor_type,
    COUNT(le.entry_id) AS transaction_count,
    SUM(le.amount_inr) AS total_inr,
    MIN(le.entry_date) AS first_txn_date,
    MAX(le.entry_date) AS last_txn_date
FROM vendors v
JOIN ledger_entries le ON le.vendor_id = v.vendor_id
WHERE le.approval_status = 'approved' AND le.is_duplicate = FALSE
GROUP BY v.canonical_name, v.vendor_type
ORDER BY total_inr DESC;
