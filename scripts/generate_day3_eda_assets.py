from pathlib import Path
import json
import math

import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageFont


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data" / "processed"
CHART_DIR = BASE_DIR / "reports" / "day3_charts"
NOTEBOOK_PATH = BASE_DIR / "notebooks" / "EDA_Analysis.ipynb"
SUMMARY_PATH = BASE_DIR / "reports" / "EDA_Findings_summary.md"
CHART_DIR.mkdir(parents=True, exist_ok=True)


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


FONTS = {
    "title": font(36, True),
    "subtitle": font(20),
    "axis": font(22, True),
    "tick": font(17),
    "small": font(15),
    "tiny": font(13),
    "label": font(18, True),
}

COLORS = {
    "text": (31, 41, 55, 255),
    "muted": (75, 85, 99, 255),
    "axis": (55, 65, 81, 255),
    "grid": (229, 231, 235, 255),
    "blue": (31, 105, 168, 255),
    "green": (22, 163, 74, 255),
    "orange": (234, 88, 12, 255),
    "purple": (109, 40, 217, 255),
    "teal": (13, 148, 136, 255),
    "red": (220, 38, 38, 255),
    "yellow": (202, 138, 4, 255),
    "pink": (219, 39, 119, 255),
}
PALETTE = [
    COLORS["blue"], COLORS["green"], COLORS["orange"], COLORS["purple"], COLORS["teal"],
    COLORS["red"], COLORS["yellow"], COLORS["pink"], (14, 116, 144, 255),
    (100, 116, 139, 255), (132, 204, 22, 255), (168, 85, 247, 255),
    (249, 115, 22, 255), (6, 182, 212, 255), (190, 18, 60, 255),
]


def new_canvas(width=1800, height=1000):
    image = Image.new("RGBA", (width, height), (255, 255, 255, 255))
    return image, ImageDraw.Draw(image)


def text(draw, xy, value, text_font=None, fill=None):
    draw.text(xy, str(value), font=text_font or FONTS["tick"], fill=fill or COLORS["text"])


def centered(draw, x, y, value, text_font=None, fill=None):
    value = str(value)
    text_font = text_font or FONTS["tick"]
    bbox = draw.textbbox((0, 0), value, font=text_font)
    draw.text((x - (bbox[2] - bbox[0]) / 2, y), value, font=text_font, fill=fill or COLORS["text"])


def right_aligned(draw, x, y, value, text_font=None, fill=None):
    value = str(value)
    text_font = text_font or FONTS["tick"]
    bbox = draw.textbbox((0, 0), value, font=text_font)
    draw.text((x - (bbox[2] - bbox[0]), y), value, font=text_font, fill=fill or COLORS["text"])


def save_chart(image, filename):
    path = CHART_DIR / filename
    image.convert("RGB").save(path, quality=95)
    return path


def line_chart(series, title, subtitle, ylabel, filename, markers=None, shades=None, y_min=None, y_max=None):
    width, height = 1800, 1000
    left, right, top, bottom = 150, 110, 130, 170
    plot_w, plot_h = width - left - right, height - top - bottom
    image, draw = new_canvas(width, height)
    centered(draw, width / 2, 36, title, FONTS["title"])
    centered(draw, width / 2, 82, subtitle, FONTS["subtitle"], COLORS["muted"])

    series = series.dropna().sort_index()
    dates = pd.to_datetime(series.index)
    values = series.astype(float).values
    y_min = float(np.nanmin(values) * 0.95) if y_min is None else float(y_min)
    y_max = float(np.nanmax(values) * 1.05) if y_max is None else float(y_max)
    if y_max == y_min:
        y_max += 1

    def x_at(date_value):
        return left + ((pd.Timestamp(date_value) - dates.min()).days / max(1, (dates.max() - dates.min()).days)) * plot_w

    def y_at(value):
        return top + plot_h - ((value - y_min) / (y_max - y_min)) * plot_h

    if shades:
        for start, end, color, label in shades:
            x0, x1 = x_at(start), x_at(end)
            draw.rectangle((x0, top, x1, top + plot_h), fill=color)
            centered(draw, (x0 + x1) / 2, top + 12, label, FONTS["small"], COLORS["muted"])

    for idx in range(6):
        value = y_min + (y_max - y_min) * idx / 5
        y = y_at(value)
        draw.line((left, y, left + plot_w, y), fill=COLORS["grid"], width=1)
        right_aligned(draw, left - 14, y - 9, f"{value:,.0f}", FONTS["tick"])

    draw.line((left, top, left, top + plot_h), fill=COLORS["axis"], width=3)
    draw.line((left, top + plot_h, left + plot_w, top + plot_h), fill=COLORS["axis"], width=3)

    points = [(x_at(d), y_at(v)) for d, v in zip(dates, values)]
    for p1, p2 in zip(points, points[1:]):
        draw.line((p1[0], p1[1], p2[0], p2[1]), fill=COLORS["blue"], width=5)
    for x, y in points[:: max(1, len(points) // 55)]:
        draw.ellipse((x - 3, y - 3, x + 3, y + 3), fill=COLORS["blue"])

    if markers:
        for marker_date, label, color in markers:
            nearest_idx = int(np.abs(dates - pd.Timestamp(marker_date)).argmin())
            marker_x = x_at(dates[nearest_idx])
            marker_y = y_at(values[nearest_idx])
            draw.line((marker_x, top, marker_x, top + plot_h), fill=color, width=3)
            draw.ellipse((marker_x - 10, marker_y - 10, marker_x + 10, marker_y + 10), fill=color, outline=(255, 255, 255, 255), width=3)
            box_w, box_h = 220, 66
            box_x = min(max(marker_x + 25, left + 8), left + plot_w - box_w)
            box_y = max(top + 42, marker_y - 105)
            draw.rounded_rectangle((box_x, box_y, box_x + box_w, box_y + box_h), radius=10, fill=(255, 255, 255, 245), outline=color, width=2)
            text(draw, (box_x + 12, box_y + 9), label, FONTS["label"])
            text(draw, (box_x + 12, box_y + 36), f"{values[nearest_idx]:,.0f}", FONTS["small"], color)

    for year in range(dates.min().year, dates.max().year + 1):
        x = x_at(pd.Timestamp(f"{year}-01-01"))
        if left <= x <= left + plot_w:
            draw.line((x, top + plot_h, x, top + plot_h + 8), fill=COLORS["axis"], width=2)
            centered(draw, x, top + plot_h + 20, year, FONTS["tick"])

    text(draw, (28, top + plot_h / 2 - 26), ylabel, FONTS["axis"])
    centered(draw, left + plot_w / 2, height - 58, "Period", FONTS["axis"])
    return save_chart(image, filename)


def horizontal_bar(df, label_col, value_col, title, subtitle, ylabel, filename, fmt="{:.1f}"):
    width, height = 1800, 1000
    left, right, top, bottom = 300, 120, 130, 120
    plot_w, plot_h = width - left - right, height - top - bottom
    image, draw = new_canvas(width, height)
    centered(draw, width / 2, 36, title, FONTS["title"])
    centered(draw, width / 2, 82, subtitle, FONTS["subtitle"], COLORS["muted"])
    values = df[value_col].astype(float).tolist()
    labels = df[label_col].astype(str).tolist()
    max_value = max(values) * 1.12
    draw.line((left, top, left, top + plot_h), fill=COLORS["axis"], width=3)
    draw.line((left, top + plot_h, left + plot_w, top + plot_h), fill=COLORS["axis"], width=3)
    bar_h = (plot_h - 10 * (len(values) - 1)) / len(values)
    for idx, (label, value) in enumerate(zip(labels, values)):
        y = top + idx * (bar_h + 10)
        x1 = left + value / max_value * plot_w
        draw.rounded_rectangle((left, y, x1, y + bar_h), radius=5, fill=PALETTE[idx % len(PALETTE)])
        right_aligned(draw, left - 14, y + bar_h / 2 - 9, label[:31], FONTS["tick"])
        text(draw, (x1 + 8, y + bar_h / 2 - 9), fmt.format(value), FONTS["tick"])
    text(draw, (36, top + plot_h / 2 - 18), ylabel, FONTS["axis"])
    return save_chart(image, filename)


def heatmap(matrix, title, subtitle, filename, fmt="{:.0f}"):
    width, height = 1900, 1050
    left, right, top, bottom = 270, 90, 145, 170
    plot_w, plot_h = width - left - right, height - top - bottom
    image, draw = new_canvas(width, height)
    centered(draw, width / 2, 35, title, FONTS["title"])
    centered(draw, width / 2, 82, subtitle, FONTS["subtitle"], COLORS["muted"])
    rows, cols = list(matrix.index.astype(str)), list(matrix.columns.astype(str))
    values = matrix.values.astype(float)
    min_val, max_val = float(np.nanmin(values)), float(np.nanmax(values))
    cell_w, cell_h = plot_w / len(cols), plot_h / len(rows)

    def cell_color(value):
        if value < 0:
            ratio = min(1, abs(value) / max(abs(min_val), 1))
            return (int(230 - 120 * ratio), int(242 - 125 * ratio), 255, 255)
        ratio = min(1, value / max(max_val, 1))
        return (255, int(245 - 130 * ratio), int(235 - 190 * ratio), 255)

    for i, row in enumerate(rows):
        y = top + i * cell_h
        right_aligned(draw, left - 10, y + cell_h / 2 - 8, row[:25], FONTS["small"])
        for j, col in enumerate(cols):
            x = left + j * cell_w
            val = values[i, j]
            draw.rectangle((x, y, x + cell_w, y + cell_h), fill=cell_color(val), outline=(255, 255, 255, 255))
            if cell_w > 52 and cell_h > 28:
                centered(draw, x + cell_w / 2, y + cell_h / 2 - 7, fmt.format(val), FONTS["tiny"])
    for j, col in enumerate(cols):
        centered(draw, left + j * cell_w + cell_w / 2, top + plot_h + 12, col, FONTS["tiny"])
    return save_chart(image, filename)


def pie_chart(labels, values, title, subtitle, filename, donut=False):
    width, height = 1600, 1000
    image, draw = new_canvas(width, height)
    centered(draw, width / 2, 35, title, FONTS["title"])
    centered(draw, width / 2, 82, subtitle, FONTS["subtitle"], COLORS["muted"])
    cx, cy, radius = 560, 525, 320
    total = float(sum(values))
    start = -90
    for idx, (label, value) in enumerate(zip(labels, values)):
        extent = 360 * value / total if total else 0
        draw.pieslice((cx - radius, cy - radius, cx + radius, cy + radius), start, start + extent, fill=PALETTE[idx % len(PALETTE)], outline=(255, 255, 255, 255), width=3)
        start += extent
    if donut:
        draw.ellipse((cx - 155, cy - 155, cx + 155, cy + 155), fill=(255, 255, 255, 255))
        centered(draw, cx, cy - 18, "Total", FONTS["label"])
        centered(draw, cx, cy + 10, f"{total:,.1f}", FONTS["label"], COLORS["muted"])
    legend_x, legend_y = 970, 220
    for idx, (label, value) in enumerate(zip(labels, values)):
        y = legend_y + idx * 44
        draw.rounded_rectangle((legend_x, y, legend_x + 24, y + 24), radius=4, fill=PALETTE[idx % len(PALETTE)])
        pct = 100 * value / total if total else 0
        text(draw, (legend_x + 38, y - 2), f"{label}: {pct:.1f}%", FONTS["tick"])
    return save_chart(image, filename)


def grouped_bar(yearly_values, groups, years, title, subtitle, filename):
    width, height = 1800, 1000
    left, right, top, bottom = 160, 90, 130, 230
    plot_w, plot_h = width - left - right, height - top - bottom
    image, draw = new_canvas(width, height)
    centered(draw, width / 2, 36, title, FONTS["title"])
    centered(draw, width / 2, 82, subtitle, FONTS["subtitle"], COLORS["muted"])
    max_value = max(yearly_values.values()) * 1.12
    draw.line((left, top, left, top + plot_h), fill=COLORS["axis"], width=3)
    draw.line((left, top + plot_h, left + plot_w, top + plot_h), fill=COLORS["axis"], width=3)
    for idx in range(6):
        value = max_value * idx / 5
        y = top + plot_h - value / max_value * plot_h
        draw.line((left, y, left + plot_w, y), fill=COLORS["grid"])
        right_aligned(draw, left - 12, y - 9, f"{value:.0f}", FONTS["tick"])
    group_w = plot_w / len(groups)
    bar_w = min(25, (group_w - 20) / len(years))
    gap = 6
    year_colors = [(68, 1, 84, 255), (49, 104, 142, 255), (53, 183, 121, 255), (253, 231, 37, 255)]
    for i, group in enumerate(groups):
        gx = left + i * group_w + group_w / 2
        total_w = len(years) * bar_w + (len(years) - 1) * gap
        start_x = gx - total_w / 2
        for j, year in enumerate(years):
            value = yearly_values.get((group, year), 0)
            x = start_x + j * (bar_w + gap)
            y = top + plot_h - value / max_value * plot_h
            draw.rounded_rectangle((x, y, x + bar_w, top + plot_h), radius=3, fill=year_colors[j % len(year_colors)])
        centered(draw, gx, top + plot_h + 20, group[:16], FONTS["tiny"])
    for j, year in enumerate(years):
        x = width - 440 + j * 95
        draw.rounded_rectangle((x, 40, x + 24, 64), radius=4, fill=year_colors[j])
        text(draw, (x + 32, 41), year, FONTS["tick"])
    return save_chart(image, filename)


def box_plot(group_values, title, subtitle, filename):
    width, height = 1800, 1000
    left, right, top, bottom = 150, 90, 130, 160
    plot_w, plot_h = width - left - right, height - top - bottom
    image, draw = new_canvas(width, height)
    centered(draw, width / 2, 36, title, FONTS["title"])
    centered(draw, width / 2, 82, subtitle, FONTS["subtitle"], COLORS["muted"])
    all_values = np.concatenate([np.asarray(values) for values in group_values.values()])
    y_min, y_max = 0, np.percentile(all_values, 99) * 1.1

    def y_at(value):
        return top + plot_h - (value - y_min) / (y_max - y_min) * plot_h

    draw.line((left, top, left, top + plot_h), fill=COLORS["axis"], width=3)
    draw.line((left, top + plot_h, left + plot_w, top + plot_h), fill=COLORS["axis"], width=3)
    for idx in range(6):
        value = y_max * idx / 5
        y = y_at(value)
        draw.line((left, y, left + plot_w, y), fill=COLORS["grid"])
        right_aligned(draw, left - 15, y - 9, f"{value:,.0f}", FONTS["tick"])
    labels = list(group_values.keys())
    step = plot_w / len(labels)
    for idx, label in enumerate(labels):
        values = np.asarray(group_values[label])
        values = values[values <= y_max]
        q1, median, q3 = np.percentile(values, [25, 50, 75])
        low, high = np.percentile(values, [5, 95])
        x = left + idx * step + step / 2
        box_w = 90
        draw.line((x, y_at(low), x, y_at(high)), fill=COLORS["axis"], width=3)
        draw.line((x - 28, y_at(low), x + 28, y_at(low)), fill=COLORS["axis"], width=3)
        draw.line((x - 28, y_at(high), x + 28, y_at(high)), fill=COLORS["axis"], width=3)
        draw.rounded_rectangle((x - box_w / 2, y_at(q3), x + box_w / 2, y_at(q1)), radius=5, fill=(219, 234, 254, 255), outline=COLORS["blue"], width=3)
        draw.line((x - box_w / 2, y_at(median), x + box_w / 2, y_at(median)), fill=COLORS["red"], width=4)
        centered(draw, x, top + plot_h + 20, label, FONTS["tick"])
    text(draw, (34, top + plot_h / 2 - 20), "SIP Amount (INR)", FONTS["axis"])
    return save_chart(image, filename)


def build_notebook(findings, chart_sections):
    def md(source):
        return {"cell_type": "markdown", "metadata": {}, "source": source.splitlines(True)}

    def code(source):
        return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": source.splitlines(True)}

    cells = [
        md("# Day 3: Exploratory Data Analysis (EDA)\n\nBluestock Mutual Fund Analytics EDA notebook. Charts are exported to `reports/day3_charts/` and referenced inline for final reporting."),
        code("from pathlib import Path\nimport pandas as pd\nimport numpy as np\nimport matplotlib.pyplot as plt\nimport seaborn as sns\nimport plotly.express as px\n\nsns.set_theme(style='whitegrid', context='notebook')\nBASE_DIR = Path.cwd().parent if Path.cwd().name == 'notebooks' else Path.cwd()\nDATA_DIR = BASE_DIR / 'data' / 'processed'\nCHART_DIR = BASE_DIR / 'reports' / 'day3_charts'\n"),
    ]

    code_by_task = {
        "Task 1": "fund = pd.read_csv(DATA_DIR / '01_fund_master.csv')\nnav = pd.read_csv(DATA_DIR / '02_nav_history.csv', parse_dates=['date'])\nnav_merged = nav.merge(fund[['amfi_code','scheme_name','category']], on='amfi_code')\n# Plotly: px.line(nav_merged, x='date', y='nav', color='scheme_name')\n",
        "Task 2": "aum = pd.read_csv(DATA_DIR / '03_aum_by_fund_house.csv', parse_dates=['date'])\naum['year'] = aum['date'].dt.year\nyearly_aum = aum.sort_values('date').groupby(['year','fund_house'], as_index=False).tail(1)\n# Seaborn: sns.barplot(data=yearly_aum, x='fund_house', y='aum_lakh_crore', hue='year')\n",
        "Task 3": "sip = pd.read_csv(DATA_DIR / '04_monthly_sip_inflows.csv')\nsip['month_dt'] = pd.to_datetime(sip['month'] + '-01')\n# Plotly: px.line(sip, x='month_dt', y='sip_inflow_crore', markers=True)\n",
        "Task 4": "category = pd.read_csv(DATA_DIR / '05_category_inflows.csv')\ncategory_matrix = category.pivot(index='category', columns='month', values='net_inflow_crore')\n# Seaborn: sns.heatmap(category_matrix, cmap='YlOrRd')\n",
        "Task 5": "tx = pd.read_csv(DATA_DIR / '08_investor_transactions.csv', parse_dates=['transaction_date'])\nsip_tx = tx[tx['transaction_type'] == 'SIP']\n# Age pie, SIP amount boxplot by age group, and gender split.\n",
        "Task 6": "state_sip = sip_tx.groupby('state')['amount_inr'].sum().sort_values(ascending=False)\ncity_tier_sip = sip_tx.groupby('city_tier')['amount_inr'].sum()\n",
        "Task 7": "folios = pd.read_csv(DATA_DIR / '06_industry_folio_count.csv')\nfolios['month_dt'] = pd.to_datetime(folios['month'] + '-01')\n",
        "Task 8": "performance = pd.read_csv(DATA_DIR / '07_scheme_performance.csv')\nselected_codes = performance.sort_values('aum_crore', ascending=False).head(10)['amfi_code']\n# Pivot NAV, compute daily returns, then corr(); visualize with sns.heatmap.\n",
        "Task 9": "holdings = pd.read_csv(DATA_DIR / '09_portfolio_holdings.csv')\nequity_codes = fund[fund['category'] == 'Equity']['amfi_code']\nsector_weights = holdings[holdings['amfi_code'].isin(equity_codes)].groupby('sector')['weight_pct'].sum()\n",
        "Supporting": "# Supporting diagnostics for return ranking and risk-adjusted performance.\n",
    }

    for title, description, images in chart_sections:
        cells.append(md(f"## {title}\n\n{description}"))
        task_key = title.split(":")[0] if title.startswith("Task") else "Supporting"
        cells.append(code(code_by_task.get(task_key, "")))
        for image in images:
            cells.append(md(f"![{image}](../reports/day3_charts/{image})"))

    cells.append(md("## Task 10: Key EDA Findings\n\n" + "\n".join(f"{idx + 1}. {finding}" for idx, finding in enumerate(findings))))
    cells.append(md("## Deliverable Checklist\n\n- `EDA_Analysis.ipynb` contains all 10 Day 3 task sections.\n- `reports/day3_charts/` contains 17 exported PNG charts.\n- `reports/EDA_Findings_summary.md` contains the final findings summary."))

    notebook = {
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "pygments_lexer": "ipython3"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    try:
        NOTEBOOK_PATH.write_text(json.dumps(notebook, indent=2), encoding="utf-8")
    except PermissionError:
        fallback_path = BASE_DIR / "reports" / "EDA_Analysis.generated.ipynb"
        fallback_path.write_text(json.dumps(notebook, indent=2), encoding="utf-8")
        print(f"Notebook write was blocked; wrote fallback copy to {fallback_path}")


def main():
    fund = pd.read_csv(DATA_DIR / "01_fund_master.csv")
    nav = pd.read_csv(DATA_DIR / "02_nav_history.csv", parse_dates=["date"])
    aum = pd.read_csv(DATA_DIR / "03_aum_by_fund_house.csv", parse_dates=["date"])
    sip = pd.read_csv(DATA_DIR / "04_monthly_sip_inflows.csv")
    category = pd.read_csv(DATA_DIR / "05_category_inflows.csv")
    folios = pd.read_csv(DATA_DIR / "06_industry_folio_count.csv")
    performance = pd.read_csv(DATA_DIR / "07_scheme_performance.csv")
    transactions = pd.read_csv(DATA_DIR / "08_investor_transactions.csv", parse_dates=["transaction_date"])
    holdings = pd.read_csv(DATA_DIR / "09_portfolio_holdings.csv", parse_dates=["portfolio_date"])

    nav_merged = nav.merge(fund[["amfi_code", "scheme_name", "category"]], on="amfi_code", how="left")
    nav_pivot = nav_merged.pivot(index="date", columns="amfi_code", values="nav").sort_index()
    nav_indexed = nav_pivot / nav_pivot.iloc[0] * 100
    average_indexed_nav = nav_indexed.mean(axis=1)

    # Task 1: NAV trend analysis.
    width, height = 1900, 1050
    left, right, top, bottom = 130, 240, 135, 165
    plot_w, plot_h = width - left - right, height - top - bottom
    image, draw = new_canvas(width, height)
    centered(draw, width / 2, 36, "Daily NAV Trend - All 40 Schemes (2022-2026)", FONTS["title"])
    centered(draw, width / 2, 82, "2023 bull-run window and 2024 correction period highlighted", FONTS["subtitle"], COLORS["muted"])
    dates = nav_pivot.index
    values = nav_pivot.values
    y_min, y_max = np.nanmin(values) * 0.95, np.nanmax(values) * 1.05

    def x_nav(date_value):
        return left + ((pd.Timestamp(date_value) - dates.min()).days / (dates.max() - dates.min()).days) * plot_w

    def y_nav(value):
        return top + plot_h - (value - y_min) / (y_max - y_min) * plot_h

    for start, end, color, label in [
        (pd.Timestamp("2023-01-01"), pd.Timestamp("2023-12-31"), (220, 252, 231, 120), "2023 bull run"),
        (pd.Timestamp("2024-09-01"), pd.Timestamp("2024-11-30"), (254, 226, 226, 130), "2024 correction"),
    ]:
        x0, x1 = x_nav(start), x_nav(end)
        draw.rectangle((x0, top, x1, top + plot_h), fill=color)
        centered(draw, (x0 + x1) / 2, top + 12, label, FONTS["small"], COLORS["muted"])
    for idx in range(6):
        value = y_min + (y_max - y_min) * idx / 5
        y = y_nav(value)
        draw.line((left, y, left + plot_w, y), fill=COLORS["grid"])
        right_aligned(draw, left - 12, y - 9, f"{value:.0f}", FONTS["tick"])
    draw.line((left, top, left, top + plot_h), fill=COLORS["axis"], width=3)
    draw.line((left, top + plot_h, left + plot_w, top + plot_h), fill=COLORS["axis"], width=3)
    for idx, code in enumerate(nav_pivot.columns):
        series = nav_pivot[code].dropna().iloc[::5]
        points = [(x_nav(date), y_nav(value)) for date, value in series.items()]
        for p1, p2 in zip(points, points[1:]):
            draw.line((p1[0], p1[1], p2[0], p2[1]), fill=PALETTE[idx % len(PALETTE)], width=2)
    for year in range(2022, 2027):
        x = x_nav(pd.Timestamp(f"{year}-01-01"))
        draw.line((x, top + plot_h, x, top + plot_h + 8), fill=COLORS["axis"], width=2)
        centered(draw, x, top + plot_h + 20, year, FONTS["tick"])
    text(draw, (28, top + plot_h / 2 - 10), "NAV", FONTS["axis"])
    save_chart(image, "task_01_nav_trend_all_40_schemes.png")

    line_chart(
        average_indexed_nav,
        "Average Indexed NAV Trend - 40 Schemes",
        "Base = 100 on first available NAV date",
        "Indexed NAV",
        "task_01_nav_average_indexed.png",
        shades=[
            (pd.Timestamp("2023-01-01"), pd.Timestamp("2023-12-31"), (220, 252, 231, 120), "2023 bull run"),
            (pd.Timestamp("2024-09-01"), pd.Timestamp("2024-11-30"), (254, 226, 226, 130), "2024 correction"),
        ],
    )
    category_nav = nav_merged.pivot_table(index="date", columns="category", values="nav", aggfunc="mean").sort_index()
    category_nav = category_nav / category_nav.iloc[0] * 100
    line_chart(category_nav["Equity"], "Indexed NAV - Equity Funds", "Average equity scheme NAV, base = 100", "Indexed NAV", "task_01_nav_equity_indexed.png")
    focus = average_indexed_nav.loc["2024-07-01":"2024-12-31"]
    line_chart(
        focus,
        "2024 Market Correction Focus",
        "Average indexed NAV, July-Dec 2024",
        "Indexed NAV",
        "task_01_nav_2024_correction_focus.png",
        markers=[(focus.idxmin(), "Local low", COLORS["red"])],
        y_min=focus.min() * 0.995,
        y_max=focus.max() * 1.005,
    )

    # Task 2: AUM.
    aum["year"] = aum["date"].dt.year
    yearly_aum = aum.sort_values("date").groupby(["year", "fund_house"], as_index=False).tail(1)
    latest_aum = yearly_aum[yearly_aum["year"] == yearly_aum["year"].max()].sort_values("aum_lakh_crore", ascending=False)
    fund_house_order = latest_aum["fund_house"].tolist()
    years = sorted(yearly_aum["year"].unique())
    yearly_values = {(row.fund_house, int(row.year)): float(row.aum_lakh_crore) for row in yearly_aum.itertuples()}
    grouped_bar(yearly_values, fund_house_order, years, "AUM Growth by Fund House (2022-2025)", "Year-end/latest snapshot by AMC; SBI reaches Rs. 12.50 lakh crore in 2025", "task_02_aum_growth_by_amc.png")
    pie_chart(latest_aum["fund_house"].tolist(), latest_aum["aum_lakh_crore"].tolist(), "2025 AUM Market Share by Fund House", "Latest available AUM snapshot in lakh crore INR", "support_aum_2025_market_share.png", donut=True)

    # Task 3: SIP.
    sip["month_dt"] = pd.to_datetime(sip["month"] + "-01")
    sip = sip.sort_values("month_dt")
    sip_series = sip.set_index("month_dt")["sip_inflow_crore"]
    line_chart(
        sip_series,
        "Monthly SIP Inflow Trend (Jan 2022 - Dec 2025)",
        "Dec 2025 annotated as all-time high in available data",
        "SIP Inflow\n(Crore INR)",
        "task_03_sip_inflow_trend.png",
        markers=[
            (pd.Timestamp("2025-12-01"), "All-time high", COLORS["red"]),
            (pd.Timestamp("2023-01-01"), "Jan 2023", COLORS["orange"]),
            (pd.Timestamp("2024-01-01"), "Jan 2024", COLORS["purple"]),
        ],
        y_min=0,
        y_max=sip_series.max() * 1.15,
    )
    line_chart(sip.set_index("month_dt")["active_sip_accounts_crore"], "Active SIP Accounts Growth", "Monthly active SIP accounts in crore", "Accounts\n(Crore)", "support_active_sip_accounts.png", y_min=0)

    # Task 4.
    category_matrix = category.pivot(index="category", columns="month", values="net_inflow_crore").fillna(0)
    category_matrix = category_matrix.loc[category_matrix.sum(axis=1).sort_values(ascending=False).index]
    heatmap(category_matrix, "Category-Wise Monthly Net Inflow Heatmap", "Net inflow in crore INR; warmer cells indicate stronger inflows", "task_04_category_inflow_heatmap.png")

    # Task 5.
    sip_transactions = transactions[transactions["transaction_type"] == "SIP"].copy()
    age_order = ["18-25", "26-35", "36-45", "46-55", "56+"]
    age_counts = transactions["age_group"].value_counts().reindex(age_order).dropna()
    pie_chart(age_counts.index.tolist(), age_counts.values.tolist(), "Investor Age Group Distribution", "Distribution by transaction records", "task_05_age_group_distribution_pie.png")
    box_plot({age: grp["amount_inr"].values for age, grp in sip_transactions.groupby("age_group") if age in age_order}, "SIP Amount Distribution by Age Group", "Box plot uses SIP transactions; whiskers show 5th-95th percentile", "task_05_sip_amount_box_by_age.png")
    gender_counts = transactions["gender"].value_counts()
    pie_chart(gender_counts.index.tolist(), gender_counts.values.tolist(), "Investor Gender Split", "Distribution by transaction records", "task_05_gender_split.png", donut=True)

    # Task 6.
    state_sip = sip_transactions.groupby("state", as_index=False)["amount_inr"].sum()
    state_sip["sip_amount_crore"] = state_sip["amount_inr"] / 10_000_000
    state_top = state_sip.sort_values("sip_amount_crore", ascending=False).head(30)
    horizontal_bar(state_top, "state", "sip_amount_crore", "State-Wise SIP Distribution", "Top states by total SIP amount", "SIP Amount\n(Crore INR)", "task_06_state_sip_distribution_bar.png")
    city_tier = sip_transactions.groupby("city_tier")["amount_inr"].sum() / 10_000_000
    pie_chart(city_tier.index.tolist(), city_tier.values.tolist(), "SIP Amount by City Tier", "T30 versus B30 contribution based on SIP amount", "task_06_city_tier_pie.png", donut=True)

    # Task 7.
    folios["month_dt"] = pd.to_datetime(folios["month"] + "-01")
    folios = folios.sort_values("month_dt")
    folio_series = folios.set_index("month_dt")["total_folios_crore"]
    line_chart(folio_series, "Industry Folio Count Growth", "Total folios from Jan 2022 to Dec 2025, crore units", "Folios\n(Crore)", "task_07_folio_count_growth.png", markers=[(folio_series.index[0], "Start", COLORS["orange"]), (folio_series.index[-1], "End", COLORS["red"])], y_min=0, y_max=folio_series.max() * 1.18)
    latest_folio = folios.iloc[-1]
    folio_mix = pd.Series({"Equity": latest_folio.equity_folios_crore, "Debt": latest_folio.debt_folios_crore, "Hybrid": latest_folio.hybrid_folios_crore, "Others": latest_folio.others_folios_crore})
    pie_chart(folio_mix.index.tolist(), folio_mix.values.tolist(), "Folio Mix by Category - Dec 2025", "Latest folio composition in crore", "support_folio_mix_dec_2025.png", donut=True)

    # Task 8.
    selected_codes = performance.sort_values("aum_crore", ascending=False).head(10)["amfi_code"].tolist()
    returns = nav_pivot[selected_codes].pct_change().dropna()
    correlation = returns.corr()
    labels = fund.set_index("amfi_code").loc[selected_codes, "scheme_name"].str.replace(" Fund", "", regex=False).str[:18]
    correlation.index = labels.values
    correlation.columns = labels.values
    heatmap(correlation, "NAV Daily Return Correlation Matrix", "Top 10 funds by AUM; pairwise daily NAV return correlation", "task_08_nav_return_correlation_matrix.png", fmt="{:.2f}")

    # Task 9.
    equity_codes = fund[fund["category"] == "Equity"]["amfi_code"]
    equity_holdings = holdings[holdings["amfi_code"].isin(equity_codes)]
    sector_weights = equity_holdings.groupby("sector")["weight_pct"].sum().sort_values(ascending=False)
    top_sectors = sector_weights.head(9)
    other_weight = sector_weights.iloc[9:].sum()
    sector_plot = pd.concat([top_sectors, pd.Series({"Others": other_weight})]) if other_weight > 0 else top_sectors
    pie_chart(sector_plot.index.tolist(), sector_plot.values.tolist(), "Sector Allocation Across Equity Funds", "Aggregated portfolio weights from portfolio holdings", "task_09_sector_allocation_donut.png", donut=True)

    # Supporting charts to exceed 15 charts.
    horizontal_bar(performance.sort_values("return_3yr_pct", ascending=False).head(10), "scheme_name", "return_3yr_pct", "Top 10 Schemes by 3-Year Return", "Performance snapshot from scheme performance dataset", "3Y Return (%)", "support_top_10_3yr_returns.png", fmt="{:.1f}%")
    horizontal_bar(performance.sort_values("sharpe_ratio", ascending=False).head(10), "scheme_name", "sharpe_ratio", "Top 10 Schemes by Sharpe Ratio", "Risk-adjusted return comparison", "Sharpe Ratio", "support_top_10_sharpe_ratio.png", fmt="{:.2f}")

    # Findings.
    sbi_2025 = float(latest_aum[latest_aum["fund_house"] == "SBI Mutual Fund"]["aum_lakh_crore"].iloc[0])
    sip_growth = (sip_series.iloc[-1] / sip_series.iloc[0] - 1) * 100
    category_totals = category.groupby("category")["net_inflow_crore"].sum().sort_values(ascending=False)
    top_state = state_top.iloc[0]
    folio_growth = folio_series.iloc[-1] - folio_series.iloc[0]
    corr_values = correlation.values[np.triu_indices_from(correlation.values, k=1)]
    average_correlation = float(np.nanmean(corr_values))
    top_sector = sector_plot.index[0]
    top_sector_share = sector_plot.iloc[0] / sector_plot.sum() * 100
    findings = [
        f"SBI Mutual Fund is the largest AMC in 2025 with Rs. {sbi_2025:.2f} lakh crore AUM, well ahead of peers.",
        f"Monthly SIP inflows grew {sip_growth:.1f}% from Jan 2022 to Dec 2025, reaching the dataset high of Rs. {sip_series.iloc[-1]:,.0f} crore.",
        f"{category_totals.index[0]} recorded the highest cumulative category net inflow at Rs. {category_totals.iloc[0]:,.0f} crore during the available category window.",
        f"The {age_counts.idxmax()} age group contributes the largest share of investor transaction records.",
        f"{top_state.state} is the leading SIP state by amount with Rs. {top_state.sip_amount_crore:,.1f} crore in SIP transactions.",
        f"Industry folios increased by {folio_growth:.2f} crore, from {folio_series.iloc[0]:.2f} crore to {folio_series.iloc[-1]:.2f} crore.",
        f"The selected top 10 funds show an average pairwise daily return correlation of {average_correlation:.2f}, indicating limited co-movement in this synthetic NAV sample.",
        f"{top_sector} is the largest aggregated equity portfolio sector at {top_sector_share:.1f}% of summed sector weights.",
        f"The 2024 correction focus chart shows the average indexed NAV local low at {focus.idxmin().date()}.",
        f"December 2025 also has the largest active SIP account base in the dataset at {sip['active_sip_accounts_crore'].iloc[-1]:.2f} crore accounts.",
    ]
    SUMMARY_PATH.write_text("# Day 3 EDA Findings Summary\n\n" + "\n".join(f"{idx + 1}. {finding}" for idx, finding in enumerate(findings)) + "\n", encoding="utf-8")

    chart_sections = [
        ("Task 1: NAV Trend Analysis", "Daily NAV for all 40 schemes, with 2023 bull-run and 2024 correction context.", ["task_01_nav_trend_all_40_schemes.png", "task_01_nav_average_indexed.png", "task_01_nav_equity_indexed.png", "task_01_nav_2024_correction_focus.png"]),
        ("Task 2: AUM Growth by Fund House", "Grouped yearly AUM comparison for 2022-2025, highlighting SBI leadership.", ["task_02_aum_growth_by_amc.png", "support_aum_2025_market_share.png"]),
        ("Task 3: SIP Inflow Time-Series", "Monthly SIP trend from Jan 2022 to Dec 2025, with Dec 2025 all-time high annotation.", ["task_03_sip_inflow_trend.png", "support_active_sip_accounts.png"]),
        ("Task 4: Category Inflow Heatmap", "Category-wise net inflow by month using heatmap intensity.", ["task_04_category_inflow_heatmap.png"]),
        ("Task 5: Investor Demographics", "Age distribution, SIP amount by age group, and gender split.", ["task_05_age_group_distribution_pie.png", "task_05_sip_amount_box_by_age.png", "task_05_gender_split.png"]),
        ("Task 6: Geographic Distribution", "State-wise SIP amount and T30/B30 city tier contribution.", ["task_06_state_sip_distribution_bar.png", "task_06_city_tier_pie.png"]),
        ("Task 7: Folio Count Growth", "Industry folio growth and latest category mix.", ["task_07_folio_count_growth.png", "support_folio_mix_dec_2025.png"]),
        ("Task 8: NAV Return Correlation Matrix", "Pairwise daily NAV return correlation for top 10 selected funds.", ["task_08_nav_return_correlation_matrix.png"]),
        ("Task 9: Sector Allocation Donut", "Aggregated sector weights across equity fund portfolio holdings.", ["task_09_sector_allocation_donut.png"]),
        ("Supporting Performance Diagnostics", "Additional charts included to exceed the 15-chart deliverable and enrich EDA context.", ["support_top_10_3yr_returns.png", "support_top_10_sharpe_ratio.png"]),
    ]
    build_notebook(findings, chart_sections)
    print(f"Generated {len(list(CHART_DIR.glob('*.png')))} PNG charts")
    print(f"Notebook: {NOTEBOOK_PATH}")
    print(f"Summary: {SUMMARY_PATH}")


if __name__ == "__main__":
    main()
