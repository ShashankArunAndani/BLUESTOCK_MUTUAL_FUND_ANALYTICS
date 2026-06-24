from pathlib import Path
import pandas as pd

RAW_DIR = Path("data/raw")
REPORTS_DIR = Path("reports")
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

report_lines = []
report_lines.append("#" * 100)
report_lines.append("BLUESTOCK MUTUAL FUND ANALYTICS - DATA INGESTION REPORT")
report_lines.append("#" * 100)

if not RAW_DIR.exists():
    raise FileNotFoundError(f"Folder not found: {RAW_DIR.resolve()}")

csv_files = sorted(RAW_DIR.glob("*.csv"))

if not csv_files:
    raise FileNotFoundError(f"No CSV files found in: {RAW_DIR.resolve()}")

all_dataframes = {}

for csv_file in csv_files:
    report_lines.append("\n" + "=" * 100)
    report_lines.append(f"FILE: {csv_file.name}")
    report_lines.append("=" * 100)

    try:
        df = pd.read_csv(csv_file)
        all_dataframes[csv_file.name] = df

        print("\n" + "=" * 100)
        print(f"Processing: {csv_file.name}")
        print("=" * 100)

        print(f"Shape: {df.shape}")

        print("\nData Types:")
        print(df.dtypes)

        print("\nFirst 5 Rows:")
        print(df.head())

        missing_values = df.isna().sum()
        duplicate_rows = df.duplicated().sum()

        print("\nMissing Values:")
        print(missing_values)

        print(f"\nDuplicate Rows: {duplicate_rows}")

        report_lines.append(f"Shape: {df.shape}")
        report_lines.append("\nData Types:")
        report_lines.append(df.dtypes.to_string())
        report_lines.append("\nMissing Values:")
        report_lines.append(missing_values.to_string())
        report_lines.append(f"\nDuplicate Rows: {duplicate_rows}")

        report_lines.append("\nColumn Names:")
        report_lines.append(", ".join(df.columns.astype(str).tolist()))

        if duplicate_rows > 0:
            report_lines.append("\nNOTE: Duplicate rows found.")
        if missing_values.sum() > 0:
            report_lines.append("\nNOTE: Missing values found.")

    except Exception as e:
        error_msg = f"Error reading {csv_file.name}: {e}"
        print(error_msg)
        report_lines.append(error_msg)

report_lines.append("\n" + "=" * 100)
report_lines.append("SUMMARY")
report_lines.append("=" * 100)
report_lines.append(f"Total CSV files found: {len(csv_files)}")
report_lines.append(f"Total CSV files successfully loaded: {len(all_dataframes)}")

report_path = REPORTS_DIR / "data_quality_report.txt"
report_path.write_text("\n".join(report_lines), encoding="utf-8")

print("\n" + "=" * 100)
print(f"Data quality report saved to: {report_path}")
print("=" * 100)

# ==============================================================================
# FUND MASTER EXPLORATION
# ==============================================================================

print("\n" + "#" * 100)
print("FUND MASTER EXPLORATION")
print("#" * 100)

fund_master = pd.read_csv(RAW_DIR / "01_fund_master.csv")

print("\nDataset Shape:")
print(fund_master.shape)

print("\nUnique Fund Houses:")
print(fund_master["fund_house"].unique())

print("\nUnique Categories:")
print(fund_master["category"].unique())

print("\nUnique Sub Categories:")
print(fund_master["sub_category"].unique())

print("\nUnique Risk Categories:")
print(fund_master["risk_category"].unique())

print("\nSample AMFI Scheme Codes:")
print(fund_master["amfi_code"].head(10))


# ==============================================================================
# AMFI CODE VALIDATION
# ==============================================================================

print("\n" + "#" * 100)
print("AMFI CODE VALIDATION")
print("#" * 100)

nav_history = pd.read_csv(RAW_DIR / "02_nav_history.csv")

master_codes = set(fund_master["amfi_code"].astype(str))
nav_codes = set(nav_history["amfi_code"].astype(str))

missing_codes = master_codes - nav_codes
extra_codes = nav_codes - master_codes

print(f"\nTotal Fund Master Codes : {len(master_codes)}")
print(f"Total NAV History Codes : {len(nav_codes)}")

if len(missing_codes) == 0:
    print("\nAll AMFI codes from fund_master exist in nav_history.")
else:
    print("\nMissing Codes:")
    for code in sorted(missing_codes):
        print(code)

if len(extra_codes) > 0:
    print("\nExtra Codes in NAV History:")
    for code in sorted(extra_codes):
        print(code)


# ==============================================================================
# DATA QUALITY SUMMARY
# ==============================================================================

summary = []

summary.append("#" * 100)
summary.append("DAY 1 DATA QUALITY SUMMARY")
summary.append("#" * 100)

summary.append(f"Total CSV Files Analysed          : {len(csv_files)}")
summary.append(f"Fund Master Records              : {len(fund_master)}")
summary.append(f"NAV History Records              : {len(nav_history)}")

summary.append("")
summary.append("Duplicate Records")

summary.append(f"Fund Master Duplicate Rows       : {fund_master.duplicated().sum()}")
summary.append(f"NAV History Duplicate Rows       : {nav_history.duplicated().sum()}")

summary.append("")
summary.append("Missing Values")

summary.append(f"Fund Master Missing Values       : {fund_master.isnull().sum().sum()}")
summary.append(f"NAV History Missing Values       : {nav_history.isnull().sum().sum()}")

summary.append("")
summary.append("AMFI Code Validation")

if len(missing_codes) == 0:
    summary.append("* Every AMFI code in fund_master exists in nav_history.")
else:
    summary.append(f"Missing AMFI Codes : {len(missing_codes)}")
    summary.extend(sorted(missing_codes))

if len(extra_codes) == 0:
    summary.append("* No unexpected AMFI codes found in nav_history.")
else:
    summary.append(f"Extra AMFI Codes : {len(extra_codes)}")
    summary.extend(sorted(extra_codes))

# ==============================================================================
# SAVE DATA QUALITY SUMMARY AS MARKDOWN
# ==============================================================================

summary_md = []

summary_md.append("# Day 1 Data Quality Summary\n")

summary_md.append("## Dataset Overview")
summary_md.append(f"- **Total CSV Files Analysed:** {len(csv_files)}")
summary_md.append(f"- **Fund Master Records:** {len(fund_master)}")
summary_md.append(f"- **NAV History Records:** {len(nav_history)}")

summary_md.append("\n## Duplicate Records")
summary_md.append(f"- Fund Master Duplicate Rows: **{fund_master.duplicated().sum()}**")
summary_md.append(f"- NAV History Duplicate Rows: **{nav_history.duplicated().sum()}**")

summary_md.append("\n## Missing Values")
summary_md.append(f"- Fund Master Missing Values: **{fund_master.isnull().sum().sum()}**")
summary_md.append(f"- NAV History Missing Values: **{nav_history.isnull().sum().sum()}**")

summary_md.append("\n## AMFI Code Validation")

if len(missing_codes) == 0:
    summary_md.append("-  Every AMFI code in `fund_master.csv` exists in `nav_history.csv`.")
else:
    summary_md.append(f"-  Missing AMFI Codes: **{len(missing_codes)}**")
    for code in sorted(missing_codes):
        summary_md.append(f"  - {code}")

if len(extra_codes) == 0:
    summary_md.append("-  No unexpected AMFI codes found in `nav_history.csv`.")
else:
    summary_md.append(f"-  Extra AMFI Codes: **{len(extra_codes)}**")
    for code in sorted(extra_codes):
        summary_md.append(f"  - {code}")

summary_md.append("\n## Conclusion")

summary_md.append(
    "The datasets were successfully loaded and validated. "
    "AMFI code consistency was checked between the master dataset and NAV history. "
    "This summary serves as the Day 1 data quality assessment."
)

summary_md_file = REPORTS_DIR / "data_quality_summary.md"

with open(summary_md_file, "w", encoding="utf-8") as f:
    f.write("\n".join(summary_md))

print(f"\nMarkdown summary saved to: {summary_md_file}")


print("\n" + "#" * 100)
print("DATA QUALITY SUMMARY")
print("#" * 100)

for line in summary:
    print(line)

print(f"\nSummary saved successfully to: {summary_md_file}")