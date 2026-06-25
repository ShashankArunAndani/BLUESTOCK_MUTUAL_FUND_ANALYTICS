"""
Load cleaned CSVs into the Bluestock SQLite star schema.

Usage:
    py load_database.py
"""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

PROCESSED_DIR = Path("data/processed")
SCHEMA_PATH = Path("sql/schema.sql")
DB_PATH = Path("bluestock_mf.db")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def to_date_key(dates: pd.Series) -> pd.Series:
    return pd.to_datetime(dates).dt.strftime("%Y%m%d").astype(int)


def build_dim_date(date_columns: list[pd.Series]) -> pd.DataFrame:
    """Build date dimension from all date fields used in fact tables."""
    combined = pd.concat(
        [pd.to_datetime(s, errors="coerce") for s in date_columns],
        ignore_index=True,
    ).dropna().drop_duplicates().sort_values()

    dim = pd.DataFrame({"full_date": combined})
    dim["date_key"] = dim["full_date"].dt.strftime("%Y%m%d").astype(int)
    dim["year"] = dim["full_date"].dt.year
    dim["quarter"] = dim["full_date"].dt.quarter
    dim["month"] = dim["full_date"].dt.month
    dim["month_name"] = dim["full_date"].dt.strftime("%B")
    dim["day"] = dim["full_date"].dt.day
    dim["day_of_week"] = dim["full_date"].dt.dayofweek
    dim["day_name"] = dim["day_of_week"].map(lambda x: DAY_NAMES[x])
    dim["is_weekend"] = dim["day_of_week"].isin([5, 6]).astype(int)
    dim["is_month_end"] = (
        dim["full_date"] == dim["full_date"] + pd.offsets.MonthEnd(0)
    ).astype(int)
    dim["full_date"] = dim["full_date"].dt.strftime("%Y-%m-%d")

    return dim.sort_values("date_key").reset_index(drop=True)


def init_database(db_path: Path) -> None:
    if db_path.exists():
        db_path.unlink()
        logger.info("Removed existing database: %s", db_path)

    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    conn.close()
    logger.info("Schema created from %s", SCHEMA_PATH)


def load_fund_dimension(engine) -> pd.DataFrame:
    funds = pd.read_csv(PROCESSED_DIR / "01_fund_master.csv")
    funds.to_sql("dim_fund", engine, if_exists="append", index=False)
    logger.info("Loaded dim_fund: %s rows", len(funds))

    fund_map = pd.read_sql("SELECT fund_key, amfi_code FROM dim_fund", engine)
    return fund_map


def load_date_dimension(engine, fund_master: pd.DataFrame, nav: pd.DataFrame,
                        transactions: pd.DataFrame, aum: pd.DataFrame) -> None:
    dim_date = build_dim_date([
        fund_master["launch_date"],
        nav["date"],
        transactions["transaction_date"],
        aum["date"],
    ])
    dim_date.to_sql("dim_date", engine, if_exists="append", index=False)
    logger.info("Loaded dim_date: %s rows", len(dim_date))


def load_fact_nav(engine, nav: pd.DataFrame, fund_map: pd.DataFrame) -> None:
    fact = nav.merge(fund_map, on="amfi_code")
    fact["date_key"] = to_date_key(fact["date"])
    fact = fact[["fund_key", "date_key", "nav"]]
    fact.to_sql("fact_nav", engine, if_exists="append", index=False, chunksize=5000)
    logger.info("Loaded fact_nav: %s rows", len(fact))


def load_fact_transactions(engine, transactions: pd.DataFrame,
                           fund_map: pd.DataFrame) -> None:
    fact = transactions.merge(fund_map, on="amfi_code")
    fact["date_key"] = to_date_key(fact["transaction_date"])
    fact = fact[[
        "fund_key", "date_key", "investor_id", "transaction_type", "amount_inr",
        "state", "city", "city_tier", "age_group", "gender",
        "annual_income_lakh", "payment_mode", "kyc_status",
    ]]
    fact.to_sql("fact_transactions", engine, if_exists="append", index=False, chunksize=5000)
    logger.info("Loaded fact_transactions: %s rows", len(fact))


def load_fact_performance(engine, performance: pd.DataFrame,
                          fund_map: pd.DataFrame) -> None:
    fact = performance.merge(fund_map, on="amfi_code")
    fact["anomaly_flag"] = fact["anomaly_flag"].replace("", None)
    fact = fact[[
        "fund_key", "return_1yr_pct", "return_3yr_pct", "return_5yr_pct",
        "benchmark_3yr_pct", "alpha", "beta", "sharpe_ratio", "sortino_ratio",
        "std_dev_ann_pct", "max_drawdown_pct", "aum_crore", "expense_ratio_pct",
        "morningstar_rating", "risk_grade", "anomaly_flag",
    ]]
    fact.to_sql("fact_performance", engine, if_exists="append", index=False)
    logger.info("Loaded fact_performance: %s rows", len(fact))


def load_fact_aum(engine, aum: pd.DataFrame) -> None:
    fact = aum.copy()
    fact["date_key"] = to_date_key(fact["date"])
    fact = fact[["date_key", "fund_house", "aum_lakh_crore", "aum_crore", "num_schemes"]]
    fact.to_sql("fact_aum", engine, if_exists="append", index=False)
    logger.info("Loaded fact_aum: %s rows", len(fact))


def verify_row_counts(engine) -> None:
    """Compare fact table row counts against source CSVs."""
    checks = {
        "dim_fund": ("01_fund_master.csv", "dim_fund"),
        "fact_nav": ("02_nav_history.csv", "fact_nav"),
        "fact_aum": ("03_aum_by_fund_house.csv", "fact_aum"),
        "fact_performance": ("07_scheme_performance.csv", "fact_performance"),
        "fact_transactions": ("08_investor_transactions.csv", "fact_transactions"),
    }

    logger.info("Row count verification:")
    all_ok = True

    for label, (csv_name, table_name) in checks.items():
        csv_count = len(pd.read_csv(PROCESSED_DIR / csv_name))
        db_count = pd.read_sql(f"SELECT COUNT(*) AS n FROM {table_name}", engine).iloc[0]["n"]
        status = "OK" if csv_count == db_count else "MISMATCH"
        if status != "OK":
            all_ok = False
        logger.info("  %-20s CSV=%6d  DB=%6d  %s", label, csv_count, db_count, status)

    if not all_ok:
        raise RuntimeError("Row count verification failed")

    logger.info("All row counts match.")


def main() -> None:
    logger.info("Reading processed CSVs...")
    fund_master = pd.read_csv(PROCESSED_DIR / "01_fund_master.csv")
    nav = pd.read_csv(PROCESSED_DIR / "02_nav_history.csv")
    aum = pd.read_csv(PROCESSED_DIR / "03_aum_by_fund_house.csv")
    performance = pd.read_csv(PROCESSED_DIR / "07_scheme_performance.csv")
    transactions = pd.read_csv(PROCESSED_DIR / "08_investor_transactions.csv")

    init_database(DB_PATH)
    engine = create_engine(f"sqlite:///{DB_PATH.resolve()}")

    with engine.begin() as conn:
        conn.execute(text("PRAGMA foreign_keys = ON"))

    fund_map = load_fund_dimension(engine)
    load_date_dimension(engine, fund_master, nav, transactions, aum)
    load_fact_nav(engine, nav, fund_map)
    load_fact_transactions(engine, transactions, fund_map)
    load_fact_performance(engine, performance, fund_map)
    load_fact_aum(engine, aum)

    verify_row_counts(engine)
    engine.dispose()

    logger.info("Database ready: %s", DB_PATH.resolve())


if __name__ == "__main__":
    main()
