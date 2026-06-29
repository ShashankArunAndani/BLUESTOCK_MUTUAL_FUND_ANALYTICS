# BLUESTOCK MUTUAL FUND ANALYTICS

## Overview

This project is part of the Bluestock Fintech Data Analytics Internship.

The objective is to build a complete mutual fund analytics platform by performing data ingestion, ETL, SQL database design, analytics, and dashboard visualization.

---

## Project Structure

```
data/
├── raw/
├── processed/

dashboard/
notebooks/
reports/
sql/

data_ingestion.py
live_nav_fetch.py
requirements.txt
```

---

## Day 1 Completed

- Project setup
- GitHub repository initialization
- Data ingestion for all datasets
- Live NAV fetching using MFAPI
- Data quality assessment
- AMFI code validation
- Generated reports

---

## Technologies Used

- Python
- Pandas
- Requests
- SQLAlchemy
- Jupyter Notebook
- Git
- GitHub

---


Day 2 Summary (Short Version)
Completed the full Day 2 workflow for Bluestock Mutual Fund Analytics.
Cleaned and standardized all 10 required datasets, then saved outputs in data/processed/ with validation checks for dates, numeric fields, enums, duplicates, and dataset-specific quality rules.
Designed and implemented a SQLite star schema (dim_fund, dim_date, fact_nav, fact_transactions, fact_performance, fact_aum) in sql/schema.sql with proper primary/foreign keys and constraints.
Loaded cleaned data into bluestock_mf.db using SQLAlchemy + to_sql() and verified table row counts against source processed CSVs.
Created 10 analytical SQL queries in queries.sql covering AUM ranking, NAV trends, SIP YoY growth, transaction geography, cost-efficient funds, and advanced performance/flow analytics.
Prepared complete documentation in data_dictionary.md with column definitions, data types, business meaning, and source references.
Final commit completed: Day 2: Cleaned data + SQLite DB loaded



# Bluestock Mutual Fund Analytics

## Day 3: Exploratory Data Analysis (EDA)

This phase focuses on exploratory analysis of the cleaned mutual fund datasets prepared during Day 2. The objective was to identify key trends, patterns, anomalies, and insights across NAV, AUM, SIP inflows, investor behaviour, folio growth, fund categories, geography, and sector allocation.

## Work Completed

- Analysed daily NAV trends for all 40 mutual fund schemes from 2022 to 2026.
- Created AUM growth analysis by fund house for 2022-2025.
- Analysed monthly SIP inflow trends from January 2022 to December 2025.
- Highlighted December 2025 as the highest SIP inflow month at Rs. 31,002 crore.
- Built category-wise monthly net inflow heatmap.
- Analysed investor demographics by age group and gender.
- Created SIP amount distribution analysis by age group.
- Analysed geographic SIP distribution by state and city tier.
- Analysed industry folio count growth from 13.26 crore to 26.12 crore.
- Computed NAV return correlation matrix for selected top funds.
- Aggregated portfolio holdings to analyse equity sector allocation.
- Documented 10 key EDA findings.

## Deliverables

- `notebooks/EDA_Analysis.ipynb`  
  Structured Jupyter Notebook containing all Day 3 EDA sections.

- `reports/day3_charts/`  
  Folder containing 20 exported PNG charts for reporting and presentation.

- `reports/EDA_Findings_summary.md`  
  Summary file containing 10 key EDA insights.

- `scripts/generate_day3_eda_assets.py`  
  Reusable script to regenerate Day 3 EDA charts and findings.

## Key Insights

1. SBI Mutual Fund is the largest AMC in 2025 with Rs. 12.50 lakh crore AUM.
2. SIP inflows grew 169.2% from January 2022 to December 2025.
3. December 2025 recorded the highest SIP inflow at Rs. 31,002 crore.
4. Liquid funds recorded the highest cumulative category net inflow.
5. The 26-35 age group contributed the largest share of investor transactions.
6. Madhya Pradesh led SIP contribution by transaction amount in the available dataset.
7. Industry folios increased from 13.26 crore to 26.12 crore.
8. Banking was the largest aggregated sector allocation across equity fund holdings.

## Tools Used

- Python
- Pandas
- NumPy
- Matplotlib
- Seaborn
- Plotly
- Jupyter Notebook


## Day 4: Performance Analytics and Fund Ranking

This phase focused on building a complete performance analytics layer for all 40 mutual fund schemes using cleaned NAV, benchmark, and fund master datasets prepared during earlier project stages.

## Work Completed

- Computed daily NAV returns for all 40 mutual fund schemes.
- Validated daily return distribution across funds to check for abnormal return values.
- Calculated 1-year and 3-year CAGR from NAV history.
- Evaluated 5-year CAGR availability and marked it unavailable due to insufficient NAV history from 2022-01-03 to 2026-05-29.
- Computed annualized volatility for each fund.
- Calculated Sharpe Ratio using 6.5% annual risk-free rate assumption.
- Calculated Sortino Ratio using downside deviation from negative return days.
- Performed alpha and beta regression of each fund against Nifty 100 daily returns.
- Calculated maximum drawdown for every fund, including drawdown start, trough, and recovery dates.
- Computed tracking error against mapped benchmark indices.
- Built a weighted fund scorecard using:
  - 30% 3-year return rank
  - 25% Sharpe Ratio rank
  - 20% Alpha rank
  - 15% inverse expense ratio rank
  - 10% inverse maximum drawdown rank
- Ranked all 40 funds using the final weighted score.
- Created a 3-year benchmark comparison chart for the top 5 funds against Nifty 50 and Nifty 100.
- Created a reusable script to regenerate all Day 4 outputs.

## Deliverables

- `notebooks/Performance_Analytics.ipynb`  
  Notebook structure for Day 4 performance analytics review.

- `reports/day4_performance/fund_daily_returns.csv`  
  Daily return dataset for all 40 funds.

- `reports/day4_performance/fund_scorecard.csv`  
  Final fund ranking scorecard with CAGR, Sharpe, Sortino, alpha, beta, drawdown, tracking error, and weighted score.

- `reports/day4_performance/alpha_beta.csv`  
  Regression output containing alpha, beta, R-squared, and observation count for each fund.

- `reports/day4_performance/benchmark_comparison_top5.png`  
  Benchmark comparison chart showing top 5 funds versus Nifty 50 and Nifty 100 over 3 years.

- `reports/day4_performance/day4_validation_summary.json`  
  Validation summary for generated Day 4 outputs.

- `scripts/generate_day4_performance_analytics.py`  
  Reusable script to regenerate all Day 4 analytics deliverables.

## Validation Summary

- Total funds processed: 40
- Total NAV rows used: 64,320
- Daily returns calculated: 64,280
- Missing daily returns: 40, one expected first-row return per fund
- Date range: 2022-01-03 to 2026-05-29
- Final scorecard ranks generated from 1 to 40
- Top-ranked fund: Mirae Asset Large Cap Fund - Regular - Growth

## Key Insights

1. Mirae Asset Large Cap Fund - Regular - Growth ranked highest overall based on the weighted scorecard.
2. ICICI Pru Midcap Fund - Regular - Growth and Kotak Flexicap Fund - Regular - Growth were among the top-performing funds on risk-adjusted metrics.
3. Daily return values were within a reasonable range, indicating no major NAV calculation issues.
4. The dataset does not contain a complete 5-year NAV history, so 5-year CAGR was not calculated from NAV.
5. Maximum drawdown and Sortino Ratio helped identify funds with better downside risk control.
6. Alpha and beta regression added benchmark-adjusted performance interpretation.
7. The benchmark comparison chart showed the top-ranked funds outperforming Nifty 50 and Nifty 100 over the available 3-year period.

## Tools Used

- Python
- Pandas
- NumPy
- Pillow
- Jupyter Notebook



## Author

**Shashank Arun Andani**
