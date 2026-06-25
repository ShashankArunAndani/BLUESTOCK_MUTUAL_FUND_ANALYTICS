# Bluestock Mutual Fund Analytics — Data Dictionary

This document describes the cleaned Day 2 datasets in `data/processed/`, including column-level data types, business meaning, and source references.

## 01_fund_master.csv

- **Source reference:** `data/raw/01_fund_master.csv` (cleaned into `data/processed/01_fund_master.csv`)
- **Business purpose:** Master dimension of mutual fund schemes (one row per `amfi_code`).

| Column | Data Type | Business Definition |
|---|---|---|
| amfi_code | int64 | Unique AMFI scheme code; primary business identifier for each fund. |
| fund_house | str | Asset management company (AMC) / fund house name. |
| scheme_name | str | Official mutual fund scheme name. |
| category | str | Broad fund category (e.g., Equity, Debt). |
| sub_category | str | Sub-category (e.g., Large Cap, Mid Cap, Liquid). |
| plan | str | Plan type (`Regular` or `Direct`). |
| launch_date | str | Scheme launch date in `YYYY-MM-DD`. |
| benchmark | str | Benchmark index used for performance comparison. |
| expense_ratio_pct | float64 | Total expense ratio in percentage terms. |
| exit_load_pct | float64 | Exit load percentage applicable on redemption. |
| min_sip_amount | int64 | Minimum SIP investment amount (INR). |
| min_lumpsum_amount | int64 | Minimum lump-sum investment amount (INR). |
| fund_manager | str | Fund manager name. |
| risk_category | str | Scheme risk level label. |
| sebi_category_code | str | SEBI category code for regulatory categorization. |

## 02_nav_history.csv

- **Source reference:** `data/raw/02_nav_history.csv` (cleaned into `data/processed/02_nav_history.csv`)
- **Business purpose:** Daily NAV time series per scheme; weekends/holidays forward-filled.

| Column | Data Type | Business Definition |
|---|---|---|
| amfi_code | int64 | AMFI scheme code linking NAV record to a fund. |
| date | str | NAV date in `YYYY-MM-DD`. |
| nav | float64 | Net Asset Value per unit on the specified date. |

## 03_aum_by_fund_house.csv

- **Source reference:** `data/raw/03_aum_by_fund_house.csv` (cleaned into `data/processed/03_aum_by_fund_house.csv`)
- **Business purpose:** Fund house-level AUM snapshot by reporting date.

| Column | Data Type | Business Definition |
|---|---|---|
| date | str | Reporting date in `YYYY-MM-DD`. |
| fund_house | str | AMC / fund house name. |
| aum_lakh_crore | float64 | Assets under management measured in lakh crore INR. |
| aum_crore | int64 | Assets under management measured in crore INR. |
| num_schemes | int64 | Number of schemes managed by the fund house. |

## 04_monthly_sip_inflows.csv

- **Source reference:** `data/raw/04_monthly_sip_inflows.csv` (cleaned into `data/processed/04_monthly_sip_inflows.csv`)
- **Business purpose:** Monthly SIP market trend indicators for the MF industry.

| Column | Data Type | Business Definition |
|---|---|---|
| month | str | Reporting month in `YYYY-MM`. |
| sip_inflow_crore | int64 | Total SIP inflow in crore INR for the month. |
| active_sip_accounts_crore | float64 | Number of active SIP accounts in crore. |
| new_sip_accounts_lakh | float64 | Newly registered SIP accounts in lakh. |
| sip_aum_lakh_crore | float64 | SIP-linked AUM in lakh crore INR. |
| yoy_growth_pct | float64 | Year-over-year SIP inflow growth percentage; null in initial months without prior-year base. |

## 05_category_inflows.csv

- **Source reference:** `data/raw/05_category_inflows.csv` (cleaned into `data/processed/05_category_inflows.csv`)
- **Business purpose:** Monthly net inflow trend by mutual fund category.

| Column | Data Type | Business Definition |
|---|---|---|
| month | str | Reporting month in `YYYY-MM`. |
| category | str | Fund category bucket (e.g., Large Cap, Liquid, Hybrid). |
| net_inflow_crore | float64 | Net flow (inflow minus outflow) in crore INR. |

## 06_industry_folio_count.csv

- **Source reference:** `data/raw/06_industry_folio_count.csv` (cleaned into `data/processed/06_industry_folio_count.csv`)
- **Business purpose:** Industry folio penetration and mix over time.

| Column | Data Type | Business Definition |
|---|---|---|
| month | str | Reporting month in `YYYY-MM`. |
| total_folios_crore | float64 | Total mutual fund folios in crore. |
| equity_folios_crore | float64 | Equity folios in crore. |
| debt_folios_crore | float64 | Debt folios in crore. |
| hybrid_folios_crore | float64 | Hybrid folios in crore. |
| others_folios_crore | float64 | Other category folios in crore. |

## 07_scheme_performance.csv

- **Source reference:** `data/raw/07_scheme_performance.csv` (cleaned into `data/processed/07_scheme_performance.csv`)
- **Business purpose:** Scheme-level return and risk snapshot used for ranking and risk-adjusted analytics.

| Column | Data Type | Business Definition |
|---|---|---|
| amfi_code | int64 | AMFI scheme code linking to master fund data. |
| scheme_name | str | Scheme name at performance snapshot time. |
| fund_house | str | AMC / fund house name. |
| category | str | Category label used in performance reporting. |
| plan | str | Plan type (`Regular` or `Direct`). |
| return_1yr_pct | float64 | 1-year annualized/point return percentage. |
| return_3yr_pct | float64 | 3-year return percentage. |
| return_5yr_pct | float64 | 5-year return percentage. |
| benchmark_3yr_pct | float64 | 3-year benchmark return percentage. |
| alpha | float64 | Alpha versus benchmark (risk-adjusted excess return). |
| beta | float64 | Beta (sensitivity to market movement). |
| sharpe_ratio | float64 | Sharpe ratio (return per unit of total risk). |
| sortino_ratio | float64 | Sortino ratio (return per unit of downside risk). |
| std_dev_ann_pct | float64 | Annualized standard deviation percentage (volatility proxy). |
| max_drawdown_pct | float64 | Maximum drawdown percentage from peak to trough. |
| aum_crore | int64 | Scheme AUM in crore INR (snapshot). |
| expense_ratio_pct | float64 | Scheme expense ratio percentage (snapshot). |
| morningstar_rating | int64 | Morningstar rating (integer scale). |
| risk_grade | str | Risk grade label for the scheme. |
| anomaly_flag | str | Data quality / analytical anomaly flags identified during cleaning. |

## 08_investor_transactions.csv

- **Source reference:** `data/raw/08_investor_transactions.csv` (cleaned into `data/processed/08_investor_transactions.csv`)
- **Business purpose:** Investor-level transaction ledger for flow, behavior, and segmentation analysis.

| Column | Data Type | Business Definition |
|---|---|---|
| investor_id | str | Unique investor identifier. |
| transaction_date | str | Transaction posting date in `YYYY-MM-DD`. |
| amfi_code | int64 | AMFI scheme code transacted by investor. |
| transaction_type | str | Transaction mode (`SIP`, `Lumpsum`, `Redemption`). |
| amount_inr | int64 | Transaction amount in INR. |
| state | str | Investor state. |
| city | str | Investor city. |
| city_tier | str | City tier segmentation bucket. |
| age_group | str | Investor age band. |
| gender | str | Investor gender. |
| annual_income_lakh | float64 | Annual income in lakh INR. |
| payment_mode | str | Payment channel/mode used for transaction. |
| kyc_status | str | KYC status (`Verified` or `Pending`). |

## 09_portfolio_holdings.csv

- **Source reference:** `data/raw/09_portfolio_holdings.csv` (cleaned into `data/processed/09_portfolio_holdings.csv`)
- **Business purpose:** Scheme portfolio composition at security level.

| Column | Data Type | Business Definition |
|---|---|---|
| amfi_code | int64 | AMFI scheme code for the portfolio. |
| stock_symbol | str | Listed stock symbol/ticker. |
| stock_name | str | Security name. |
| sector | str | Sector classification of holding. |
| weight_pct | float64 | Portfolio weight percentage of the holding. |
| market_value_cr | float64 | Holding market value in crore INR. |
| current_price_inr | float64 | Security current market price in INR. |
| portfolio_date | str | Portfolio disclosure date in `YYYY-MM-DD`. |

## 10_benchmark_indices.csv

- **Source reference:** `data/raw/10_benchmark_indices.csv` (cleaned into `data/processed/10_benchmark_indices.csv`)
- **Business purpose:** Daily benchmark index closes for comparative performance analytics.

| Column | Data Type | Business Definition |
|---|---|---|
| date | str | Trading date in `YYYY-MM-DD`. |
| index_name | str | Benchmark index name/code. |
| close_value | float64 | Index closing value on the date. |

## Notes on standards used

- Date columns are standardized to `YYYY-MM-DD`; month columns use `YYYY-MM`.
- Key domain validations applied during cleaning include:
  - `nav > 0`
  - `amount_inr > 0`
  - `transaction_type` in `SIP/Lumpsum/Redemption`
  - `kyc_status` in `Verified/Pending`
  - `expense_ratio_pct` in expected range for performance-focused datasets
