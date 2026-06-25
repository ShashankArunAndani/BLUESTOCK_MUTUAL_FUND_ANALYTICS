-- =============================================================================
-- Bluestock Mutual Fund Analytics
-- Day 2: Analytical SQL Queries
-- Database: SQLite (bluestock_mf.db)
-- =============================================================================

-- 1) Top 5 funds by AUM (scheme-level snapshot)
SELECT
    df.amfi_code,
    df.scheme_name,
    df.fund_house,
    fp.aum_crore
FROM fact_performance fp
JOIN dim_fund df
    ON fp.fund_key = df.fund_key
ORDER BY fp.aum_crore DESC
LIMIT 5;


-- 2) Average NAV per month (industry-wide)
SELECT
    dd.year,
    dd.month,
    ROUND(AVG(fn.nav), 4) AS avg_nav
FROM fact_nav fn
JOIN dim_date dd
    ON fn.date_key = dd.date_key
GROUP BY dd.year, dd.month
ORDER BY dd.year, dd.month;


-- 3) SIP YoY growth (amount and transaction count)
WITH monthly_sip AS (
    SELECT
        dd.year,
        dd.month,
        SUM(ft.amount_inr) AS sip_amount,
        COUNT(*) AS sip_txn_count
    FROM fact_transactions ft
    JOIN dim_date dd
        ON ft.date_key = dd.date_key
    WHERE ft.transaction_type = 'SIP'
    GROUP BY dd.year, dd.month
)
SELECT
    m.year,
    m.month,
    m.sip_amount,
    m.sip_txn_count,
    ROUND(
        100.0 * (m.sip_amount - p.sip_amount) / NULLIF(p.sip_amount, 0),
        2
    ) AS yoy_sip_amount_pct,
    ROUND(
        100.0 * (m.sip_txn_count - p.sip_txn_count) / NULLIF(p.sip_txn_count, 0),
        2
    ) AS yoy_sip_count_pct
FROM monthly_sip m
LEFT JOIN monthly_sip p
    ON p.year = m.year - 1
   AND p.month = m.month
ORDER BY m.year, m.month;


-- 4) Transactions by state (volume + value)
SELECT
    ft.state,
    COUNT(*) AS transaction_count,
    ROUND(SUM(ft.amount_inr), 2) AS total_amount_inr,
    ROUND(AVG(ft.amount_inr), 2) AS avg_ticket_size_inr
FROM fact_transactions ft
GROUP BY ft.state
ORDER BY total_amount_inr DESC, transaction_count DESC;


-- 5) Funds with expense ratio < 1% (cost-efficient funds)
SELECT
    df.amfi_code,
    df.scheme_name,
    df.fund_house,
    df.plan,
    fp.expense_ratio_pct,
    fp.return_3yr_pct,
    fp.sharpe_ratio
FROM fact_performance fp
JOIN dim_fund df
    ON fp.fund_key = df.fund_key
WHERE fp.expense_ratio_pct < 1.0
ORDER BY fp.expense_ratio_pct ASC, fp.return_3yr_pct DESC;


-- 6) Top alpha generators vs benchmark
SELECT
    df.amfi_code,
    df.scheme_name,
    df.fund_house,
    fp.return_3yr_pct,
    fp.benchmark_3yr_pct,
    ROUND(fp.return_3yr_pct - fp.benchmark_3yr_pct, 2) AS excess_return_3yr_pct,
    fp.alpha,
    fp.sharpe_ratio
FROM fact_performance fp
JOIN dim_fund df
    ON fp.fund_key = df.fund_key
ORDER BY fp.alpha DESC, excess_return_3yr_pct DESC
LIMIT 10;


-- 7) Risk-adjusted leaders by category (Sharpe rank)
SELECT
    df.sub_category,
    df.scheme_name,
    df.fund_house,
    fp.sharpe_ratio,
    fp.sortino_ratio,
    fp.std_dev_ann_pct
FROM fact_performance fp
JOIN dim_fund df
    ON fp.fund_key = df.fund_key
WHERE fp.sharpe_ratio = (
    SELECT MAX(fp2.sharpe_ratio)
    FROM fact_performance fp2
    JOIN dim_fund df2
        ON fp2.fund_key = df2.fund_key
    WHERE df2.sub_category = df.sub_category
)
ORDER BY df.sub_category;


-- 8) Net flow trend by month (SIP + Lumpsum - Redemption)
WITH flow_monthly AS (
    SELECT
        dd.year,
        dd.month,
        SUM(CASE WHEN ft.transaction_type IN ('SIP', 'Lumpsum') THEN ft.amount_inr ELSE 0 END) AS gross_inflow,
        SUM(CASE WHEN ft.transaction_type = 'Redemption' THEN ft.amount_inr ELSE 0 END) AS redemption,
        SUM(CASE
                WHEN ft.transaction_type IN ('SIP', 'Lumpsum') THEN ft.amount_inr
                WHEN ft.transaction_type = 'Redemption' THEN -ft.amount_inr
                ELSE 0
            END) AS net_flow
    FROM fact_transactions ft
    JOIN dim_date dd
        ON ft.date_key = dd.date_key
    GROUP BY dd.year, dd.month
)
SELECT
    year,
    month,
    gross_inflow,
    redemption,
    net_flow,
    ROUND(
        100.0 * (net_flow - LAG(net_flow) OVER (ORDER BY year, month))
        / NULLIF(LAG(net_flow) OVER (ORDER BY year, month), 0),
        2
    ) AS mom_net_flow_change_pct
FROM flow_monthly
ORDER BY year, month;


-- 9) Fund house concentration using Herfindahl-Hirschman Index (HHI)
WITH latest_aum AS (
    SELECT fa.*
    FROM fact_aum fa
    WHERE fa.date_key = (SELECT MAX(date_key) FROM fact_aum)
),
share_calc AS (
    SELECT
        fund_house,
        aum_crore,
        1.0 * aum_crore / SUM(aum_crore) OVER () AS market_share
    FROM latest_aum
)
SELECT
    ROUND(SUM(market_share * market_share) * 10000, 2) AS hhi_index,
    ROUND(MAX(market_share) * 100, 2) AS largest_fund_house_share_pct
FROM share_calc;


-- 10) Investor behavior segmentation by city tier
SELECT
    ft.city_tier,
    ft.transaction_type,
    COUNT(*) AS txn_count,
    ROUND(SUM(ft.amount_inr), 2) AS total_amount_inr,
    ROUND(AVG(ft.amount_inr), 2) AS avg_ticket_size_inr,
    ROUND(COUNT(DISTINCT ft.investor_id) * 1.0 / COUNT(*), 4) AS unique_investor_ratio
FROM fact_transactions ft
GROUP BY ft.city_tier, ft.transaction_type
ORDER BY ft.city_tier, total_amount_inr DESC;
