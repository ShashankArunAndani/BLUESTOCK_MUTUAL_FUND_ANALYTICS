# Day 1 Data Quality Summary

## Dataset Overview
- **Total CSV Files Analysed:** 16
- **Fund Master Records:** 40
- **NAV History Records:** 46000

## Duplicate Records
- Fund Master Duplicate Rows: **0**
- NAV History Duplicate Rows: **0**

## Missing Values
- Fund Master Missing Values: **0**
- NAV History Missing Values: **0**

## AMFI Code Validation
-  Every AMFI code in `fund_master.csv` exists in `nav_history.csv`.
-  No unexpected AMFI codes found in `nav_history.csv`.

## Conclusion
The datasets were successfully loaded and validated. AMFI code consistency was checked between the master dataset and NAV history. This summary serves as the Day 1 data quality assessment.