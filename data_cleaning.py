"""
Bluestock Mutual Fund Analytics — Day 2 Data Cleaning Pipeline

Cleans raw CSV datasets and writes validated outputs to data/processed/.
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd

RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

VALID_TRANSACTION_TYPES = {"SIP", "Lumpsum", "Redemption"}
VALID_KYC_STATUS = {"Verified", "Pending"}

TRANSACTION_TYPE_MAP = {
    "sip": "SIP",
    "SIP": "SIP",
    "lumpsum": "Lumpsum",
    "Lumpsum": "Lumpsum",
    "lump sum": "Lumpsum",
    "Lump Sum": "Lumpsum",
    "lump-sum": "Lumpsum",
    "redemption": "Redemption",
    "Redemption": "Redemption",
}

KYC_STATUS_MAP = {
    "verified": "Verified",
    "Verified": "Verified",
    "pending": "Pending",
    "Pending": "Pending",
}

PERFORMANCE_NUMERIC_COLS = [
    "return_1yr_pct",
    "return_3yr_pct",
    "return_5yr_pct",
    "benchmark_3yr_pct",
    "alpha",
    "beta",
    "sharpe_ratio",
    "sortino_ratio",
    "std_dev_ann_pct",
    "max_drawdown_pct",
    "aum_crore",
    "expense_ratio_pct",
    "morningstar_rating",
]

EXPENSE_RATIO_MIN = 0.1
EXPENSE_RATIO_MAX = 2.5

VALID_PLAN_TYPES = {"Regular", "Direct"}


def _parse_dates(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Parse date columns; drop rows with unparseable values."""
    out = df.copy()
    for col in columns:
        out[col] = pd.to_datetime(out[col], errors="coerce")
        invalid = out[col].isna()
        if invalid.any():
            logger.warning("Dropping %s rows with invalid %s", invalid.sum(), col)
            out = out.loc[~invalid]
    return out


def _parse_months(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Parse YYYY-MM month columns; drop rows with unparseable values."""
    out = df.copy()
    for col in columns:
        out[col] = pd.to_datetime(out[col], format="%Y-%m", errors="coerce")
        invalid = out[col].isna()
        if invalid.any():
            logger.warning("Dropping %s rows with invalid %s", invalid.sum(), col)
            out = out.loc[~invalid]
    return out


def clean_fund_master(df: pd.DataFrame) -> pd.DataFrame:
    """Clean fund master: types, dates, expense ratio, dedup by amfi_code."""
    out = df.copy()

    out["amfi_code"] = pd.to_numeric(out["amfi_code"], errors="coerce")
    out = out.dropna(subset=["amfi_code"])
    out["amfi_code"] = out["amfi_code"].astype(int)

    out = _parse_dates(out, ["launch_date"])

    for col in ["expense_ratio_pct", "exit_load_pct"]:
        out[col] = pd.to_numeric(out[col], errors="coerce")

    for col in ["min_sip_amount", "min_lumpsum_amount"]:
        out[col] = pd.to_numeric(out[col], errors="coerce")

    invalid_expense = out["expense_ratio_pct"].isna() | (
        out["expense_ratio_pct"] < EXPENSE_RATIO_MIN
    ) | (out["expense_ratio_pct"] > EXPENSE_RATIO_MAX)
    if invalid_expense.any():
        logger.warning("Dropping %s rows with invalid expense_ratio_pct", invalid_expense.sum())
        out = out.loc[~invalid_expense]

    invalid_amounts = (
        out["min_sip_amount"].isna()
        | (out["min_sip_amount"] <= 0)
        | out["min_lumpsum_amount"].isna()
        | (out["min_lumpsum_amount"] <= 0)
    )
    if invalid_amounts.any():
        logger.warning("Dropping %s rows with invalid minimum amounts", invalid_amounts.sum())
        out = out.loc[~invalid_amounts]

    out["plan"] = out["plan"].astype(str).str.strip()
    invalid_plan = ~out["plan"].isin(VALID_PLAN_TYPES)
    if invalid_plan.any():
        logger.warning("Dropping %s rows with invalid plan", invalid_plan.sum())
        out = out.loc[~invalid_plan]

    string_cols = [
        "fund_house", "scheme_name", "category", "sub_category",
        "benchmark", "fund_manager", "risk_category", "sebi_category_code",
    ]
    for col in string_cols:
        out[col] = out[col].astype(str).str.strip()

    out["min_sip_amount"] = out["min_sip_amount"].astype(int)
    out["min_lumpsum_amount"] = out["min_lumpsum_amount"].astype(int)
    out = out.drop_duplicates(subset=["amfi_code"], keep="last")
    return out.sort_values("amfi_code").reset_index(drop=True)


def clean_aum_by_fund_house(df: pd.DataFrame) -> pd.DataFrame:
    """Clean AUM by fund house: dates, positive metrics, dedup."""
    out = _parse_dates(df.copy(), ["date"])

    out["aum_lakh_crore"] = pd.to_numeric(out["aum_lakh_crore"], errors="coerce")
    out["aum_crore"] = pd.to_numeric(out["aum_crore"], errors="coerce")
    out["num_schemes"] = pd.to_numeric(out["num_schemes"], errors="coerce")

    invalid = (
        out["aum_lakh_crore"].isna()
        | (out["aum_lakh_crore"] <= 0)
        | out["aum_crore"].isna()
        | (out["aum_crore"] <= 0)
        | out["num_schemes"].isna()
        | (out["num_schemes"] <= 0)
    )
    if invalid.any():
        logger.warning("Dropping %s rows with invalid AUM metrics", invalid.sum())
        out = out.loc[~invalid]

    out["fund_house"] = out["fund_house"].astype(str).str.strip()
    out["aum_crore"] = out["aum_crore"].astype(int)
    out["num_schemes"] = out["num_schemes"].astype(int)
    out = out.drop_duplicates(subset=["date", "fund_house"], keep="last")
    return out.sort_values(["date", "fund_house"]).reset_index(drop=True)


def clean_monthly_sip_inflows(df: pd.DataFrame) -> pd.DataFrame:
    """Clean monthly SIP inflows: month format, positive metrics; retain null YoY for year 1."""
    out = _parse_months(df.copy(), ["month"])

    numeric_cols = [
        "sip_inflow_crore",
        "active_sip_accounts_crore",
        "new_sip_accounts_lakh",
        "sip_aum_lakh_crore",
    ]
    for col in numeric_cols:
        out[col] = pd.to_numeric(out[col], errors="coerce")

    invalid = out[numeric_cols].isna().any(axis=1) | (out[numeric_cols] <= 0).any(axis=1)
    if invalid.any():
        logger.warning("Dropping %s rows with invalid SIP inflow metrics", invalid.sum())
        out = out.loc[~invalid]

    out["yoy_growth_pct"] = pd.to_numeric(out["yoy_growth_pct"], errors="coerce")
    out["sip_inflow_crore"] = out["sip_inflow_crore"].astype(int)
    out = out.drop_duplicates(subset=["month"], keep="last")
    return out.sort_values("month").reset_index(drop=True)


def clean_category_inflows(df: pd.DataFrame) -> pd.DataFrame:
    """Clean category inflows: month format, numeric inflows, dedup."""
    out = _parse_months(df.copy(), ["month"])

    out["net_inflow_crore"] = pd.to_numeric(out["net_inflow_crore"], errors="coerce")
    invalid = out["net_inflow_crore"].isna()
    if invalid.any():
        logger.warning("Dropping %s rows with invalid net_inflow_crore", invalid.sum())
        out = out.loc[~invalid]

    out["category"] = out["category"].astype(str).str.strip()
    out = out.drop_duplicates(subset=["month", "category"], keep="last")
    return out.sort_values(["month", "category"]).reset_index(drop=True)


def clean_industry_folio_count(df: pd.DataFrame) -> pd.DataFrame:
    """Clean industry folio counts: month format, positive folio metrics."""
    out = _parse_months(df.copy(), ["month"])

    folio_cols = [
        "total_folios_crore",
        "equity_folios_crore",
        "debt_folios_crore",
        "hybrid_folios_crore",
        "others_folios_crore",
    ]
    for col in folio_cols:
        out[col] = pd.to_numeric(out[col], errors="coerce")

    invalid = out[folio_cols].isna().any(axis=1) | (out[folio_cols] <= 0).any(axis=1)
    if invalid.any():
        logger.warning("Dropping %s rows with invalid folio metrics", invalid.sum())
        out = out.loc[~invalid]

    out = out.drop_duplicates(subset=["month"], keep="last")
    return out.sort_values("month").reset_index(drop=True)


def clean_portfolio_holdings(df: pd.DataFrame) -> pd.DataFrame:
    """Clean portfolio holdings: dates, positive weights/prices, dedup."""
    out = df.copy()

    out["amfi_code"] = pd.to_numeric(out["amfi_code"], errors="coerce")
    out = out.dropna(subset=["amfi_code"])
    out["amfi_code"] = out["amfi_code"].astype(int)
    out = _parse_dates(out, ["portfolio_date"])

    out["weight_pct"] = pd.to_numeric(out["weight_pct"], errors="coerce")
    out["market_value_cr"] = pd.to_numeric(out["market_value_cr"], errors="coerce")
    out["current_price_inr"] = pd.to_numeric(out["current_price_inr"], errors="coerce")

    invalid = (
        out["weight_pct"].isna()
        | (out["weight_pct"] <= 0)
        | out["market_value_cr"].isna()
        | (out["market_value_cr"] <= 0)
        | out["current_price_inr"].isna()
        | (out["current_price_inr"] <= 0)
    )
    if invalid.any():
        logger.warning("Dropping %s rows with invalid holding metrics", invalid.sum())
        out = out.loc[~invalid]

    for col in ["stock_symbol", "stock_name", "sector"]:
        out[col] = out[col].astype(str).str.strip()

    out = out.drop_duplicates(
        subset=["amfi_code", "portfolio_date", "stock_symbol"],
        keep="last",
    )
    return out.sort_values(
        ["amfi_code", "portfolio_date", "weight_pct"],
        ascending=[True, True, False],
    ).reset_index(drop=True)


def clean_benchmark_indices(df: pd.DataFrame) -> pd.DataFrame:
    """Clean benchmark indices: dates, positive close values, dedup."""
    out = _parse_dates(df.copy(), ["date"])

    out["close_value"] = pd.to_numeric(out["close_value"], errors="coerce")
    invalid = out["close_value"].isna() | (out["close_value"] <= 0)
    if invalid.any():
        logger.warning("Dropping %s rows with invalid close_value", invalid.sum())
        out = out.loc[~invalid]

    out["index_name"] = out["index_name"].astype(str).str.strip()
    out = out.drop_duplicates(subset=["date", "index_name"], keep="last")
    return out.sort_values(["index_name", "date"]).reset_index(drop=True)


def clean_nav_history(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean NAV history:
    - Parse dates to datetime
    - Sort by amfi_code + date
    - Remove duplicates (keep last NAV per fund-date)
    - Drop rows with NAV <= 0
    - Forward-fill NAV across calendar gaps (weekends / holidays)
    """
    out = df.copy()

    out["date"] = pd.to_datetime(out["date"], errors="coerce")
    out = out.dropna(subset=["date"])

    out["amfi_code"] = out["amfi_code"].astype(int)
    out["nav"] = pd.to_numeric(out["nav"], errors="coerce")

    out = out.sort_values(["amfi_code", "date"])
    out = out.drop_duplicates(subset=["amfi_code", "date"], keep="last")
    out = out.loc[out["nav"].notna() & (out["nav"] > 0)]

    filled_groups: list[pd.DataFrame] = []
    for amfi_code, group in out.groupby("amfi_code", sort=True):
        group = group.sort_values("date").set_index("date")
        full_range = pd.date_range(group.index.min(), group.index.max(), freq="D")
        expanded = group.reindex(full_range)
        expanded["nav"] = expanded["nav"].ffill()
        expanded = expanded.dropna(subset=["nav"])
        expanded = expanded.reset_index(names="date")
        expanded["amfi_code"] = amfi_code
        filled_groups.append(expanded[["amfi_code", "date", "nav"]])

    result = pd.concat(filled_groups, ignore_index=True)
    return result.sort_values(["amfi_code", "date"]).reset_index(drop=True)


def clean_investor_transactions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean investor transactions:
    - Standardise transaction_type to SIP / Lumpsum / Redemption
    - Validate amount_inr > 0
    - Fix date formats to ISO YYYY-MM-DD
    - Validate kyc_status enum (Verified, Pending)
    """
    out = df.copy()

    out["transaction_type"] = (
        out["transaction_type"].astype(str).str.strip().map(TRANSACTION_TYPE_MAP)
    )
    invalid_type = out["transaction_type"].isna()
    if invalid_type.any():
        logger.warning("Dropping %s rows with invalid transaction_type", invalid_type.sum())
        out = out.loc[~invalid_type]

    out["amount_inr"] = pd.to_numeric(out["amount_inr"], errors="coerce")
    invalid_amount = out["amount_inr"].isna() | (out["amount_inr"] <= 0)
    if invalid_amount.any():
        logger.warning("Dropping %s rows with invalid amount_inr", invalid_amount.sum())
        out = out.loc[~invalid_amount]
    out["amount_inr"] = out["amount_inr"].astype(int)

    out["transaction_date"] = pd.to_datetime(out["transaction_date"], errors="coerce")
    invalid_date = out["transaction_date"].isna()
    if invalid_date.any():
        logger.warning("Dropping %s rows with unparseable transaction_date", invalid_date.sum())
        out = out.loc[~invalid_date]

    out["kyc_status"] = out["kyc_status"].astype(str).str.strip().map(KYC_STATUS_MAP)
    invalid_kyc = out["kyc_status"].isna()
    if invalid_kyc.any():
        logger.warning("Dropping %s rows with invalid kyc_status", invalid_kyc.sum())
        out = out.loc[~invalid_kyc]

    out["amfi_code"] = out["amfi_code"].astype(int)
    out = out.drop_duplicates()
    out = out.sort_values(["transaction_date", "investor_id", "amfi_code"]).reset_index(drop=True)

    assert set(out["transaction_type"].unique()).issubset(VALID_TRANSACTION_TYPES)
    assert set(out["kyc_status"].unique()).issubset(VALID_KYC_STATUS)

    return out


def _flag_performance_anomalies(row: pd.Series) -> str:
    """Return semicolon-separated anomaly codes for a performance record."""
    flags: list[str] = []

    expense = row["expense_ratio_pct"]
    if pd.notna(expense) and (expense < EXPENSE_RATIO_MIN or expense > EXPENSE_RATIO_MAX):
        flags.append("expense_ratio_out_of_range")

    sharpe = row["sharpe_ratio"]
    return_3yr = row["return_3yr_pct"]
    if pd.notna(sharpe) and sharpe > 3:
        flags.append("high_sharpe_ratio")
    if pd.notna(sharpe) and pd.notna(return_3yr) and np.isclose(sharpe, return_3yr):
        flags.append("sharpe_matches_return_3yr")

    sortino = row["sortino_ratio"]
    if pd.notna(sortino) and sortino > 5:
        flags.append("high_sortino_ratio")

    drawdown = row["max_drawdown_pct"]
    if pd.notna(drawdown) and drawdown > 0:
        flags.append("positive_max_drawdown")

    return_1yr = row["return_1yr_pct"]
    if pd.notna(return_1yr) and abs(return_1yr) > 50:
        flags.append("extreme_return_1yr")

    beta = row["beta"]
    if pd.notna(beta) and (beta < 0 or beta > 2):
        flags.append("beta_out_of_range")

    rating = row["morningstar_rating"]
    if pd.notna(rating) and (rating < 1 or rating > 5):
        flags.append("invalid_morningstar_rating")

    return ";".join(flags)


def clean_scheme_performance(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean scheme performance:
    - Validate all return/risk metrics are numeric
    - Flag anomalies (expense ratio, sharpe, sortino, drawdown, etc.)
    - Check expense_ratio_pct is within 0.1% – 2.5%
    """
    out = df.copy()

    out["amfi_code"] = pd.to_numeric(out["amfi_code"], errors="coerce")
    out = out.dropna(subset=["amfi_code"])
    out["amfi_code"] = out["amfi_code"].astype(int)

    for col in PERFORMANCE_NUMERIC_COLS:
        out[col] = pd.to_numeric(out[col], errors="coerce")

    invalid_numeric = out[PERFORMANCE_NUMERIC_COLS].isna().any(axis=1)
    if invalid_numeric.any():
        logger.warning(
            "Dropping %s rows with non-numeric performance metrics",
            invalid_numeric.sum(),
        )
        out = out.loc[~invalid_numeric]

    out = out.drop_duplicates(subset=["amfi_code"], keep="last")

    out["anomaly_flag"] = out.apply(_flag_performance_anomalies, axis=1)
    anomaly_count = (out["anomaly_flag"] != "").sum()
    if anomaly_count:
        logger.warning("Flagged %s schemes with anomalies", anomaly_count)
        for _, row in out.loc[out["anomaly_flag"] != ""].iterrows():
            logger.warning(
                "  amfi_code=%s | %s | flags=%s",
                row["amfi_code"],
                row["scheme_name"],
                row["anomaly_flag"],
            )

    out["morningstar_rating"] = out["morningstar_rating"].astype(int)
    out["aum_crore"] = out["aum_crore"].astype(int)
    out = out.sort_values("amfi_code").reset_index(drop=True)

    assert out[PERFORMANCE_NUMERIC_COLS].notna().all().all()
    assert (out["expense_ratio_pct"] >= EXPENSE_RATIO_MIN).all()
    assert (out["expense_ratio_pct"] <= EXPENSE_RATIO_MAX).all()

    return out


def save_csv(
    df: pd.DataFrame,
    path: Path,
    date_columns: list[str] | None = None,
    month_columns: list[str] | None = None,
) -> None:
    """Write dataframe to CSV with ISO date (YYYY-MM-DD) and month (YYYY-MM) formatting."""
    export = df.copy()
    for col in date_columns or []:
        if col in export.columns:
            export[col] = pd.to_datetime(export[col]).dt.strftime("%Y-%m-%d")
    for col in month_columns or []:
        if col in export.columns:
            export[col] = pd.to_datetime(export[col]).dt.strftime("%Y-%m")
    export.to_csv(path, index=False)
    logger.info("Saved %s rows to %s", len(export), path)


CLEANING_PIPELINE: list[tuple[str, object, list[str] | None, list[str] | None]] = [
    ("01_fund_master.csv", clean_fund_master, ["launch_date"], None),
    ("02_nav_history.csv", clean_nav_history, ["date"], None),
    ("03_aum_by_fund_house.csv", clean_aum_by_fund_house, ["date"], None),
    ("04_monthly_sip_inflows.csv", clean_monthly_sip_inflows, None, ["month"]),
    ("05_category_inflows.csv", clean_category_inflows, None, ["month"]),
    ("06_industry_folio_count.csv", clean_industry_folio_count, None, ["month"]),
    ("07_scheme_performance.csv", clean_scheme_performance, None, None),
    ("08_investor_transactions.csv", clean_investor_transactions, ["transaction_date"], None),
    ("09_portfolio_holdings.csv", clean_portfolio_holdings, ["portfolio_date"], None),
    ("10_benchmark_indices.csv", clean_benchmark_indices, ["date"], None),
]


def run_all() -> dict[str, tuple[int, int]]:
    """Clean all 10 datasets and write to data/processed/. Returns raw vs cleaned row counts."""
    row_counts: dict[str, tuple[int, int]] = {}

    for filename, clean_fn, date_cols, month_cols in CLEANING_PIPELINE:
        source_path = RAW_DIR / filename
        logger.info("Cleaning %s", source_path)
        raw = pd.read_csv(source_path)
        cleaned = clean_fn(raw)
        save_csv(
            cleaned,
            PROCESSED_DIR / filename,
            date_columns=date_cols,
            month_columns=month_cols,
        )
        row_counts[filename] = (len(raw), len(cleaned))
        logger.info("  %s: %s -> %s rows", filename, len(raw), len(cleaned))

    return row_counts


def run_step_nav_history() -> pd.DataFrame:
    source_path = RAW_DIR / "02_nav_history.csv"
    logger.info("Cleaning %s", source_path)
    cleaned = clean_nav_history(pd.read_csv(source_path))
    save_csv(cleaned, PROCESSED_DIR / "02_nav_history.csv", date_columns=["date"])
    return cleaned


def run_step_investor_transactions() -> pd.DataFrame:
    source_path = RAW_DIR / "08_investor_transactions.csv"
    logger.info("Cleaning %s", source_path)
    raw = pd.read_csv(source_path)
    cleaned = clean_investor_transactions(raw)
    save_csv(
        cleaned,
        PROCESSED_DIR / "08_investor_transactions.csv",
        date_columns=["transaction_date"],
    )
    return cleaned


def run_step_scheme_performance() -> pd.DataFrame:
    source_path = RAW_DIR / "07_scheme_performance.csv"
    logger.info("Cleaning %s", source_path)
    cleaned = clean_scheme_performance(pd.read_csv(source_path))
    save_csv(cleaned, PROCESSED_DIR / "07_scheme_performance.csv")
    return cleaned


if __name__ == "__main__":
    counts = run_all()
    logger.info("All 10 datasets cleaned. Summary:")
    for filename, (raw_n, clean_n) in counts.items():
        logger.info("  %s: %d -> %d", filename, raw_n, clean_n)
