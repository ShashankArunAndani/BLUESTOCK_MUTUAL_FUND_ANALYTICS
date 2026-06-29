from pathlib import Path
import json

import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageFont


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data" / "processed"
REPORT_DIR = BASE_DIR / "reports" / "day4_performance"
NOTEBOOK_PATH = BASE_DIR / "notebooks" / "Performance_Analytics.ipynb"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

TRADING_DAYS = 252
RISK_FREE_RATE = 0.065
NIFTY100 = "NIFTY100"
NIFTY50 = "NIFTY50"

COLORS = [
    (37, 99, 235),
    (22, 163, 74),
    (234, 88, 12),
    (147, 51, 234),
    (13, 148, 136),
    (220, 38, 38),
    (31, 41, 55),
]


def font(size, bold=False):
    paths = [
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
    ]
    for path in paths:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            pass
    return ImageFont.load_default()


def clean_columns(df):
    df = df.copy()
    df.columns = [str(col).strip() for col in df.columns]
    return df


def load_inputs():
    nav = clean_columns(pd.read_csv(DATA_DIR / "02_nav_history.csv"))
    fund_master = clean_columns(pd.read_csv(DATA_DIR / "01_fund_master.csv"))
    benchmarks = clean_columns(pd.read_csv(DATA_DIR / "10_benchmark_indices.csv"))

    nav["date"] = pd.to_datetime(nav["date"])
    nav["nav"] = pd.to_numeric(nav["nav"], errors="coerce")
    nav["amfi_code"] = pd.to_numeric(nav["amfi_code"], errors="coerce").astype("Int64")
    nav = nav.dropna(subset=["amfi_code", "date", "nav"])
    nav["amfi_code"] = nav["amfi_code"].astype(int)

    fund_master["amfi_code"] = pd.to_numeric(fund_master["amfi_code"], errors="coerce").astype(int)
    fund_master["expense_ratio_pct"] = pd.to_numeric(
        fund_master["expense_ratio_pct"], errors="coerce"
    )

    benchmarks["date"] = pd.to_datetime(benchmarks["date"])
    benchmarks["close_value"] = pd.to_numeric(benchmarks["close_value"], errors="coerce")
    benchmarks["index_name"] = benchmarks["index_name"].astype(str).str.strip()
    benchmarks = benchmarks.dropna(subset=["date", "index_name", "close_value"])

    return nav, fund_master, benchmarks


def compute_daily_returns(nav, fund_master):
    nav = nav.sort_values(["amfi_code", "date"]).drop_duplicates(["amfi_code", "date"])
    nav["previous_nav"] = nav.groupby("amfi_code")["nav"].shift(1)
    nav["daily_return"] = nav["nav"] / nav["previous_nav"] - 1

    metadata_cols = [
        "amfi_code",
        "scheme_name",
        "fund_house",
        "category",
        "sub_category",
        "benchmark",
        "expense_ratio_pct",
    ]
    available_cols = [col for col in metadata_cols if col in fund_master.columns]
    return nav.merge(fund_master[available_cols], on="amfi_code", how="left")


def compute_benchmark_returns(benchmarks):
    benchmarks = benchmarks.sort_values(["index_name", "date"]).drop_duplicates(
        ["index_name", "date"]
    )
    benchmarks["benchmark_return"] = benchmarks.groupby("index_name")["close_value"].pct_change()
    return benchmarks


def value_near_date(fund_df, target_date):
    fund_df = fund_df.sort_values("date")
    eligible = fund_df[fund_df["date"] <= target_date]
    if eligible.empty:
        return None
    return eligible.iloc[-1]


def compute_cagr(fund_df, years):
    fund_df = fund_df.dropna(subset=["nav"]).sort_values("date")
    if fund_df.empty:
        return np.nan

    end = fund_df.iloc[-1]
    target_start_date = end["date"] - pd.DateOffset(years=years)
    start = value_near_date(fund_df, target_start_date)
    if start is None:
        return np.nan

    observed_years = (end["date"] - start["date"]).days / 365.25
    if observed_years < years * 0.95 or start["nav"] <= 0:
        return np.nan
    return (end["nav"] / start["nav"]) ** (1 / observed_years) - 1


def annualized_return(daily_returns):
    returns = daily_returns.dropna()
    if returns.empty:
        return np.nan
    return (1 + returns.mean()) ** TRADING_DAYS - 1


def compute_max_drawdown(fund_df):
    fund_df = fund_df.sort_values("date").copy()
    fund_df["running_max"] = fund_df["nav"].cummax()
    fund_df["drawdown"] = fund_df["nav"] / fund_df["running_max"] - 1
    trough = fund_df.loc[fund_df["drawdown"].idxmin()]
    peak_candidates = fund_df[fund_df["date"] <= trough["date"]]
    peak = peak_candidates.loc[peak_candidates["nav"].idxmax()]
    recovery_candidates = fund_df[(fund_df["date"] > trough["date"]) & (fund_df["nav"] >= peak["nav"])]
    recovery_date = recovery_candidates.iloc[0]["date"] if not recovery_candidates.empty else pd.NaT
    return trough["drawdown"], peak["date"], trough["date"], recovery_date


def compute_fund_metrics(daily_returns, benchmark_returns):
    nifty100_returns = benchmark_returns[benchmark_returns["index_name"] == NIFTY100][
        ["date", "benchmark_return"]
    ].rename(columns={"benchmark_return": "nifty100_return"})

    rows = []
    for amfi_code, fund_df in daily_returns.groupby("amfi_code"):
        fund_df = fund_df.sort_values("date")
        returns = fund_df["daily_return"].dropna()
        downside = returns[returns < 0]
        ann_return = annualized_return(returns)
        ann_vol = returns.std(ddof=1) * np.sqrt(TRADING_DAYS) if len(returns) > 1 else np.nan
        downside_vol = (
            downside.std(ddof=1) * np.sqrt(TRADING_DAYS) if len(downside) > 1 else np.nan
        )
        sharpe = (ann_return - RISK_FREE_RATE) / ann_vol if ann_vol and ann_vol > 0 else np.nan
        sortino = (
            (ann_return - RISK_FREE_RATE) / downside_vol
            if downside_vol and downside_vol > 0
            else np.nan
        )

        regression_df = fund_df[["date", "daily_return"]].merge(
            nifty100_returns, on="date", how="inner"
        ).dropna()
        if len(regression_df) >= 30:
            x = regression_df["nifty100_return"].to_numpy()
            y = regression_df["daily_return"].to_numpy()
            beta, alpha_daily = np.polyfit(x, y, 1)
            alpha_ann = alpha_daily * TRADING_DAYS
            correlation = np.corrcoef(x, y)[0, 1]
            r_squared = correlation**2
        else:
            beta = alpha_daily = alpha_ann = r_squared = np.nan

        max_dd, dd_start, dd_trough, dd_recovery = compute_max_drawdown(fund_df)

        first = fund_df.iloc[0]
        rows.append(
            {
                "amfi_code": amfi_code,
                "scheme_name": first.get("scheme_name"),
                "fund_house": first.get("fund_house"),
                "category": first.get("category"),
                "sub_category": first.get("sub_category"),
                "benchmark": first.get("benchmark"),
                "expense_ratio_pct": first.get("expense_ratio_pct"),
                "start_date": fund_df["date"].min(),
                "end_date": fund_df["date"].max(),
                "nav_observations": len(fund_df),
                "return_observations": returns.count(),
                "annualized_return_pct": ann_return * 100 if pd.notna(ann_return) else np.nan,
                "cagr_1y_pct": compute_cagr(fund_df, 1) * 100,
                "cagr_3y_pct": compute_cagr(fund_df, 3) * 100,
                "cagr_5y_pct": compute_cagr(fund_df, 5) * 100,
                "annualized_volatility_pct": ann_vol * 100 if pd.notna(ann_vol) else np.nan,
                "sharpe_ratio": sharpe,
                "sortino_ratio": sortino,
                "alpha_daily": alpha_daily,
                "alpha_annualized_pct": alpha_ann * 100 if pd.notna(alpha_ann) else np.nan,
                "beta": beta,
                "r_squared": r_squared,
                "regression_observations": len(regression_df),
                "max_drawdown_pct": max_dd * 100 if pd.notna(max_dd) else np.nan,
                "drawdown_start_date": dd_start,
                "drawdown_trough_date": dd_trough,
                "drawdown_recovery_date": dd_recovery,
                "min_daily_return_pct": returns.min() * 100 if not returns.empty else np.nan,
                "max_daily_return_pct": returns.max() * 100 if not returns.empty else np.nan,
                "mean_daily_return_pct": returns.mean() * 100 if not returns.empty else np.nan,
                "std_daily_return_pct": returns.std(ddof=1) * 100 if len(returns) > 1 else np.nan,
            }
        )

    return pd.DataFrame(rows)


def benchmark_key(benchmark_name):
    text = str(benchmark_name).upper()
    if "NIFTY 50" in text:
        return "NIFTY50"
    if "NIFTY 100" in text:
        return "NIFTY100"
    if "NIFTY 500" in text:
        return "NIFTY500"
    if "MIDCAP" in text:
        return "NIFTY_MIDCAP150"
    if "SMALL" in text:
        return "BSE_SMALLCAP"
    if "LIQUID" in text:
        return "CRISIL_LIQUID"
    if "GILT" in text:
        return "CRISIL_GILT"
    if "BOND" in text or "DEBT" in text:
        return "CRISIL_GILT"
    return "NIFTY100"


def add_tracking_error(metrics, daily_returns, benchmark_returns):
    benchmark_wide = benchmark_returns.pivot(
        index="date", columns="index_name", values="benchmark_return"
    )
    rows = []
    for _, metric in metrics.iterrows():
        key = benchmark_key(metric["benchmark"])
        fund_returns = daily_returns[daily_returns["amfi_code"] == metric["amfi_code"]][
            ["date", "daily_return"]
        ].dropna()
        merged = fund_returns.merge(
            benchmark_wide[[key]].rename(columns={key: "benchmark_return"}),
            left_on="date",
            right_index=True,
            how="inner",
        ).dropna()
        tracking_error = (
            (merged["daily_return"] - merged["benchmark_return"]).std(ddof=1)
            * np.sqrt(TRADING_DAYS)
            if len(merged) > 1
            else np.nan
        )
        row = metric.to_dict()
        row["tracking_benchmark"] = key
        row["tracking_error_pct"] = tracking_error * 100 if pd.notna(tracking_error) else np.nan
        rows.append(row)
    return pd.DataFrame(rows)


def add_scorecard_ranks(metrics):
    scorecard = metrics.copy()
    scorecard["rank_3y_return"] = scorecard["cagr_3y_pct"].rank(ascending=False, method="min")
    scorecard["rank_sharpe"] = scorecard["sharpe_ratio"].rank(ascending=False, method="min")
    scorecard["rank_alpha"] = scorecard["alpha_annualized_pct"].rank(ascending=False, method="min")
    scorecard["rank_expense_inverse"] = scorecard["expense_ratio_pct"].rank(
        ascending=True, method="min"
    )
    scorecard["rank_max_drawdown_inverse"] = scorecard["max_drawdown_pct"].rank(
        ascending=False, method="min"
    )

    max_rank = len(scorecard)
    components = {
        "score_3y_return": ("rank_3y_return", 0.30),
        "score_sharpe": ("rank_sharpe", 0.25),
        "score_alpha": ("rank_alpha", 0.20),
        "score_expense": ("rank_expense_inverse", 0.15),
        "score_drawdown": ("rank_max_drawdown_inverse", 0.10),
    }
    for score_col, (rank_col, weight) in components.items():
        scorecard[score_col] = ((max_rank - scorecard[rank_col] + 1) / max_rank) * weight * 100

    score_cols = list(components.keys())
    scorecard["fund_score"] = scorecard[score_cols].sum(axis=1)
    scorecard = scorecard.sort_values(
        ["fund_score", "cagr_3y_pct", "sharpe_ratio", "alpha_annualized_pct", "scheme_name"],
        ascending=[False, False, False, False, True],
    ).reset_index(drop=True)
    scorecard["fund_rank"] = np.arange(1, len(scorecard) + 1)
    return scorecard


def normalized_series(df, value_col, group_col):
    normalized = []
    for name, group in df.groupby(group_col):
        group = group.sort_values("date").copy()
        first_value = group[value_col].iloc[0]
        group["normalized_value"] = group[value_col] / first_value * 100
        group["series_name"] = name
        normalized.append(group[["date", "series_name", "normalized_value"]])
    return pd.concat(normalized, ignore_index=True)


def create_benchmark_chart(scorecard, daily_returns, benchmarks):
    top_funds = scorecard.head(5)["amfi_code"].tolist()
    end_date = daily_returns["date"].max()
    start_date = end_date - pd.DateOffset(years=3)

    fund_nav = daily_returns[
        (daily_returns["amfi_code"].isin(top_funds))
        & (daily_returns["date"] >= start_date)
        & (daily_returns["date"] <= end_date)
    ][["date", "scheme_name", "nav"]].copy()
    fund_series = normalized_series(fund_nav, "nav", "scheme_name")

    benchmark_values = benchmarks[
        (benchmarks["index_name"].isin([NIFTY50, NIFTY100]))
        & (benchmarks["date"] >= start_date)
        & (benchmarks["date"] <= end_date)
    ][["date", "index_name", "close_value"]].copy()
    benchmark_series = normalized_series(benchmark_values, "close_value", "index_name")

    chart_df = pd.concat([fund_series, benchmark_series], ignore_index=True)

    chart_path = REPORT_DIR / "benchmark_comparison_top5.png"
    draw_line_chart(
        chart_df,
        chart_path,
        "Top 5 Mutual Funds vs Nifty 50 and Nifty 100",
        "3 Year Growth of Rs.100",
    )
    return chart_path


def draw_line_chart(chart_df, chart_path, title, subtitle):
    width, height = 1800, 1050
    margin_left, margin_right = 120, 470
    margin_top, margin_bottom = 120, 110
    plot_left, plot_top = margin_left, margin_top
    plot_right, plot_bottom = width - margin_right, height - margin_bottom
    plot_width, plot_height = plot_right - plot_left, plot_bottom - plot_top

    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    title_font = font(42, True)
    subtitle_font = font(24)
    label_font = font(20, True)
    tick_font = font(18)
    legend_font = font(18)

    draw.text((margin_left, 38), title, fill=(17, 24, 39), font=title_font)
    draw.text((margin_left, 88), subtitle, fill=(75, 85, 99), font=subtitle_font)

    min_date = chart_df["date"].min()
    max_date = chart_df["date"].max()
    min_value = float(chart_df["normalized_value"].min())
    max_value = float(chart_df["normalized_value"].max())
    value_pad = max((max_value - min_value) * 0.08, 5)
    min_axis = np.floor((min_value - value_pad) / 10) * 10
    max_axis = np.ceil((max_value + value_pad) / 10) * 10

    draw.rectangle([plot_left, plot_top, plot_right, plot_bottom], outline=(209, 213, 219), width=2)

    y_ticks = np.linspace(min_axis, max_axis, 6)
    for y_tick in y_ticks:
        y = plot_bottom - ((y_tick - min_axis) / (max_axis - min_axis)) * plot_height
        draw.line([(plot_left, y), (plot_right, y)], fill=(229, 231, 235), width=1)
        label = f"{y_tick:.0f}"
        bbox = draw.textbbox((0, 0), label, font=tick_font)
        draw.text((plot_left - bbox[2] - 14, y - 10), label, fill=(75, 85, 99), font=tick_font)

    date_ticks = pd.date_range(min_date, max_date, periods=5)
    total_seconds = (max_date - min_date).total_seconds()
    for date_tick in date_ticks:
        x = plot_left + ((date_tick - min_date).total_seconds() / total_seconds) * plot_width
        draw.line([(x, plot_bottom), (x, plot_bottom + 8)], fill=(107, 114, 128), width=2)
        label = date_tick.strftime("%b %Y")
        bbox = draw.textbbox((0, 0), label, font=tick_font)
        draw.text((x - bbox[2] / 2, plot_bottom + 18), label, fill=(75, 85, 99), font=tick_font)

    draw.text((plot_left, plot_bottom + 65), "Date", fill=(31, 41, 55), font=label_font)
    draw.text((32, plot_top + plot_height / 2 - 20), "Value", fill=(31, 41, 55), font=label_font)

    legend_x = plot_right + 45
    legend_y = plot_top + 12
    draw.text((legend_x, legend_y - 40), "Series", fill=(31, 41, 55), font=label_font)

    for idx, (name, group) in enumerate(chart_df.groupby("series_name")):
        group = group.sort_values("date")
        color = COLORS[idx % len(COLORS)]
        points = []
        for _, row in group.iterrows():
            x = plot_left + ((row["date"] - min_date).total_seconds() / total_seconds) * plot_width
            y = plot_bottom - ((row["normalized_value"] - min_axis) / (max_axis - min_axis)) * plot_height
            points.append((x, y))
        line_width = 5 if name in [NIFTY50, NIFTY100] else 3
        if len(points) > 1:
            draw.line(points, fill=color, width=line_width, joint="curve")

        y = legend_y + idx * 58
        draw.line([(legend_x, y + 11), (legend_x + 42, y + 11)], fill=color, width=line_width)
        legend_name = abbreviate_series_name(name)
        draw.text((legend_x + 55, y), legend_name, fill=(31, 41, 55), font=legend_font)

    image.save(chart_path)


def abbreviate_series_name(name):
    text = str(name)
    replacements = {
        " Fund - Regular - Growth": "",
        " - Regular - Growth": "",
        " Fund - Regular Plan - Growth": "",
        "HDFC Mid-Cap Opportunities": "HDFC Mid-Cap Opps",
        "Mirae Asset Large Cap": "Mirae Asset Large Cap",
        "ICICI Pru Midcap": "ICICI Pru Midcap",
        "Kotak Flexicap": "Kotak Flexicap",
        "Axis Midcap": "Axis Midcap",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text[:31] + "..." if len(text) > 34 else text


def write_notebook():
    cells = [
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "# Performance Analytics\n",
                "\n",
                "Day 4 mutual fund performance analytics covering daily returns, CAGR, Sharpe Ratio, Sortino Ratio, alpha, beta, maximum drawdown, fund scorecard ranking, tracking error, and benchmark comparison.",
            ],
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "## Workflow\n",
                "\n",
                "1. Load cleaned Day 2 data from `data/processed/`.\n",
                "2. Calculate daily NAV returns fund-wise.\n",
                "3. Validate return distributions.\n",
                "4. Calculate CAGR, Sharpe, Sortino, alpha, beta, maximum drawdown, and tracking error.\n",
                "5. Rank funds using the prescribed weighted scorecard.\n",
                "6. Export CSV and benchmark comparison deliverables.",
            ],
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "from pathlib import Path\n",
                "import pandas as pd\n",
                "\n",
                "BASE_DIR = Path.cwd().parent if Path.cwd().name == 'notebooks' else Path.cwd()\n",
                "REPORT_DIR = BASE_DIR / 'reports' / 'day4_performance'\n",
                "fund_scorecard = pd.read_csv(REPORT_DIR / 'fund_scorecard.csv')\n",
                "alpha_beta = pd.read_csv(REPORT_DIR / 'alpha_beta.csv')\n",
                "daily_returns = pd.read_csv(REPORT_DIR / 'fund_daily_returns.csv')\n",
                "fund_scorecard.head(10)\n",
            ],
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "fund_scorecard[['fund_rank', 'scheme_name', 'cagr_3y_pct', 'sharpe_ratio', 'alpha_annualized_pct', 'max_drawdown_pct', 'expense_ratio_pct', 'fund_score']].head(10)\n",
            ],
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "daily_returns['daily_return'].describe(percentiles=[0.01, 0.05, 0.5, 0.95, 0.99])\n",
            ],
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "## Benchmark Comparison Chart\n",
                "\n",
                "The chart is exported to `reports/day4_performance/benchmark_comparison_top5.png`.",
            ],
        },
    ]
    notebook = {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python", "pygments_lexer": "ipython3"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    notebook_json = json.dumps(notebook, indent=2)
    try:
        NOTEBOOK_PATH.write_text(notebook_json, encoding="utf-8")
    except PermissionError:
        fallback_path = REPORT_DIR / "Performance_Analytics.ipynb"
        fallback_path.write_text(notebook_json, encoding="utf-8")


def export_outputs(daily_returns, scorecard, chart_path):
    daily_returns_out = daily_returns.copy()
    daily_returns_out["daily_return_pct"] = daily_returns_out["daily_return"] * 100
    daily_returns_out.to_csv(REPORT_DIR / "fund_daily_returns.csv", index=False)

    alpha_beta_cols = [
        "amfi_code",
        "scheme_name",
        "fund_house",
        "category",
        "alpha_daily",
        "alpha_annualized_pct",
        "beta",
        "r_squared",
        "regression_observations",
    ]
    scorecard[alpha_beta_cols].to_csv(REPORT_DIR / "alpha_beta.csv", index=False)
    scorecard.to_csv(REPORT_DIR / "fund_scorecard.csv", index=False)

    validation = {
        "fund_count": int(scorecard["amfi_code"].nunique()),
        "daily_return_rows": int(daily_returns["daily_return"].notna().sum()),
        "missing_first_return_rows": int(daily_returns["daily_return"].isna().sum()),
        "date_min": str(daily_returns["date"].min().date()),
        "date_max": str(daily_returns["date"].max().date()),
        "top_fund": str(scorecard.iloc[0]["scheme_name"]),
        "top_fund_score": round(float(scorecard.iloc[0]["fund_score"]), 4),
        "cagr_5y_available_funds": int(scorecard["cagr_5y_pct"].notna().sum()),
        "benchmark_chart": str(chart_path.relative_to(BASE_DIR)),
    }
    (REPORT_DIR / "day4_validation_summary.json").write_text(
        json.dumps(validation, indent=2), encoding="utf-8"
    )
    write_notebook()
    return validation


def main():
    nav, fund_master, benchmarks = load_inputs()
    daily_returns = compute_daily_returns(nav, fund_master)
    benchmark_returns = compute_benchmark_returns(benchmarks)
    metrics = compute_fund_metrics(daily_returns, benchmark_returns)
    metrics = add_tracking_error(metrics, daily_returns, benchmark_returns)
    scorecard = add_scorecard_ranks(metrics)
    chart_path = create_benchmark_chart(scorecard, daily_returns, benchmarks)
    validation = export_outputs(daily_returns, scorecard, chart_path)

    print("Day 4 performance analytics generated successfully.")
    for key, value in validation.items():
        print(f"{key}: {value}")
    print("Top 5 funds:")
    print(
        scorecard[
            [
                "fund_rank",
                "scheme_name",
                "cagr_3y_pct",
                "sharpe_ratio",
                "alpha_annualized_pct",
                "max_drawdown_pct",
                "fund_score",
            ]
        ]
        .head(5)
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()
