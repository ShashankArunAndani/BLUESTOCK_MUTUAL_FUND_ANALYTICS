-- =============================================================================
-- Bluestock Mutual Fund Analytics
-- Star schema for SQLite (Day 2)
--
-- Grain:
--   dim_fund          one row per mutual fund scheme (AMFI code)
--   dim_date          one row per calendar day
--   fact_nav          one row per fund per day
--   fact_transactions one row per investor transaction
--   fact_performance  one row per fund (latest performance snapshot)
--   fact_aum          one row per fund house per reporting date
-- =============================================================================

PRAGMA foreign_keys = ON;


-- -----------------------------------------------------------------------------
-- Dimension: Fund
-- Source: 01_fund_master.csv
-- -----------------------------------------------------------------------------
CREATE TABLE dim_fund (
    fund_key            INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code           INTEGER NOT NULL UNIQUE,
    fund_house          TEXT    NOT NULL,
    scheme_name         TEXT    NOT NULL,
    category            TEXT    NOT NULL,
    sub_category        TEXT    NOT NULL,
    plan                TEXT    NOT NULL CHECK (plan IN ('Regular', 'Direct')),
    launch_date         TEXT    NOT NULL,
    benchmark           TEXT    NOT NULL,
    expense_ratio_pct   REAL    NOT NULL,
    exit_load_pct       REAL    NOT NULL,
    min_sip_amount      INTEGER NOT NULL,
    min_lumpsum_amount  INTEGER NOT NULL,
    fund_manager        TEXT    NOT NULL,
    risk_category       TEXT    NOT NULL,
    sebi_category_code  TEXT    NOT NULL
);


-- -----------------------------------------------------------------------------
-- Dimension: Date
-- Populated from NAV dates, transaction dates, AUM dates, etc.
-- date_key uses YYYYMMDD so it sorts naturally and joins easily.
-- -----------------------------------------------------------------------------
CREATE TABLE dim_date (
    date_key        INTEGER PRIMARY KEY,
    full_date       TEXT    NOT NULL UNIQUE,
    year            INTEGER NOT NULL,
    quarter         INTEGER NOT NULL,
    month           INTEGER NOT NULL,
    month_name      TEXT    NOT NULL,
    day             INTEGER NOT NULL,
    day_of_week     INTEGER NOT NULL,
    day_name        TEXT    NOT NULL,
    is_weekend      INTEGER NOT NULL CHECK (is_weekend IN (0, 1)),
    is_month_end    INTEGER NOT NULL CHECK (is_month_end IN (0, 1))
);


-- -----------------------------------------------------------------------------
-- Fact: NAV
-- Source: 02_nav_history.csv
-- -----------------------------------------------------------------------------
CREATE TABLE fact_nav (
    fund_key    INTEGER NOT NULL,
    date_key    INTEGER NOT NULL,
    nav         REAL    NOT NULL CHECK (nav > 0),
    PRIMARY KEY (fund_key, date_key),
    FOREIGN KEY (fund_key) REFERENCES dim_fund (fund_key),
    FOREIGN KEY (date_key) REFERENCES dim_date (date_key)
);


-- -----------------------------------------------------------------------------
-- Fact: Investor transactions
-- Source: 08_investor_transactions.csv
-- Investor attributes kept on the fact row (no separate investor dimension).
-- -----------------------------------------------------------------------------
CREATE TABLE fact_transactions (
    transaction_key     INTEGER PRIMARY KEY AUTOINCREMENT,
    fund_key            INTEGER NOT NULL,
    date_key            INTEGER NOT NULL,
    investor_id         TEXT    NOT NULL,
    transaction_type    TEXT    NOT NULL CHECK (transaction_type IN ('SIP', 'Lumpsum', 'Redemption')),
    amount_inr          INTEGER NOT NULL CHECK (amount_inr > 0),
    state               TEXT    NOT NULL,
    city                TEXT    NOT NULL,
    city_tier           TEXT    NOT NULL,
    age_group           TEXT    NOT NULL,
    gender              TEXT    NOT NULL,
    annual_income_lakh  REAL    NOT NULL,
    payment_mode        TEXT    NOT NULL,
    kyc_status          TEXT    NOT NULL CHECK (kyc_status IN ('Verified', 'Pending')),
    FOREIGN KEY (fund_key) REFERENCES dim_fund (fund_key),
    FOREIGN KEY (date_key) REFERENCES dim_date (date_key)
);


-- -----------------------------------------------------------------------------
-- Fact: Scheme performance
-- Source: 07_scheme_performance.csv
-- One snapshot per fund; descriptive fields live in dim_fund.
-- -----------------------------------------------------------------------------
CREATE TABLE fact_performance (
    fund_key            INTEGER PRIMARY KEY,
    return_1yr_pct      REAL NOT NULL,
    return_3yr_pct      REAL NOT NULL,
    return_5yr_pct      REAL NOT NULL,
    benchmark_3yr_pct   REAL NOT NULL,
    alpha               REAL NOT NULL,
    beta                REAL NOT NULL,
    sharpe_ratio        REAL NOT NULL,
    sortino_ratio       REAL NOT NULL,
    std_dev_ann_pct     REAL NOT NULL,
    max_drawdown_pct    REAL NOT NULL,
    aum_crore           INTEGER NOT NULL,
    expense_ratio_pct   REAL NOT NULL,
    morningstar_rating  INTEGER NOT NULL CHECK (morningstar_rating BETWEEN 1 AND 5),
    risk_grade          TEXT NOT NULL,
    anomaly_flag        TEXT,
    FOREIGN KEY (fund_key) REFERENCES dim_fund (fund_key)
);


-- -----------------------------------------------------------------------------
-- Fact: AUM by fund house
-- Source: 03_aum_by_fund_house.csv
-- Grain is fund house + date (not individual scheme).
-- -----------------------------------------------------------------------------
CREATE TABLE fact_aum (
    date_key            INTEGER NOT NULL,
    fund_house          TEXT    NOT NULL,
    aum_lakh_crore      REAL    NOT NULL CHECK (aum_lakh_crore > 0),
    aum_crore           INTEGER NOT NULL CHECK (aum_crore > 0),
    num_schemes         INTEGER NOT NULL CHECK (num_schemes > 0),
    PRIMARY KEY (date_key, fund_house),
    FOREIGN KEY (date_key) REFERENCES dim_date (date_key)
);


-- -----------------------------------------------------------------------------
-- Indexes for common join and filter patterns
-- -----------------------------------------------------------------------------
CREATE INDEX idx_fact_nav_date        ON fact_nav (date_key);
CREATE INDEX idx_fact_nav_fund        ON fact_nav (fund_key);

CREATE INDEX idx_fact_txn_date        ON fact_transactions (date_key);
CREATE INDEX idx_fact_txn_fund        ON fact_transactions (fund_key);
CREATE INDEX idx_fact_txn_state       ON fact_transactions (state);
CREATE INDEX idx_fact_txn_type        ON fact_transactions (transaction_type);

CREATE INDEX idx_fact_aum_date        ON fact_aum (date_key);
CREATE INDEX idx_fact_aum_fund_house  ON fact_aum (fund_house);

CREATE INDEX idx_dim_fund_house       ON dim_fund (fund_house);
CREATE INDEX idx_dim_fund_category    ON dim_fund (sub_category);
