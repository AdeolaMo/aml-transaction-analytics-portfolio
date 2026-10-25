PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS customers (
    customer_id TEXT PRIMARY KEY,
    customer_name TEXT NOT NULL,
    segment TEXT NOT NULL CHECK (segment IN ('RETAIL','SME','CORPORATE')),
    risk_tier TEXT NOT NULL CHECK (risk_tier IN ('LOW','MEDIUM','HIGH')),
    onboarded_at TEXT NOT NULL,
    expected_monthly_volume_cents INTEGER NOT NULL CHECK (expected_monthly_volume_cents > 0),
    home_country TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL REFERENCES customers(customer_id),
    booked_at TEXT NOT NULL,
    direction TEXT NOT NULL CHECK(direction IN ('IN','OUT')),
    channel TEXT NOT NULL CHECK(channel IN ('ACH','WIRE','CARD','CASH')),
    amount_cents INTEGER NOT NULL CHECK(amount_cents > 0),
    counterparty_country TEXT NOT NULL,
    cross_border INTEGER NOT NULL CHECK(cross_border IN (0,1)),
    reference_id TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS transaction_scenario_hits (
    transaction_id TEXT NOT NULL REFERENCES transactions(transaction_id),
    scenario_code TEXT NOT NULL,
    PRIMARY KEY(transaction_id, scenario_code)
);
CREATE TABLE IF NOT EXISTS customer_month_summary (
    customer_id TEXT NOT NULL REFERENCES customers(customer_id),
    month TEXT NOT NULL,
    txn_count INTEGER NOT NULL,
    inflow_cents INTEGER NOT NULL,
    outflow_cents INTEGER NOT NULL,
    gross_volume_cents INTEGER NOT NULL,
    PRIMARY KEY (customer_id, month)
);
CREATE TABLE IF NOT EXISTS customer_month_flags (
    customer_id TEXT NOT NULL,
    month TEXT NOT NULL,
    scenario_code TEXT NOT NULL,
    PRIMARY KEY(customer_id,month,scenario_code)
);
