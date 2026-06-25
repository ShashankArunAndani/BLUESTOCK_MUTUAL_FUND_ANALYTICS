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

## Author

**Shashank Arun Andani**
