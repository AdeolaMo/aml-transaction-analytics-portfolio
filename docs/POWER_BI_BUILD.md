# Power BI Desktop — build guide

**Status:** Power BI-ready semantic model and DAX measures; **not** a native `.pbix` file. Creating a tested `.pbix` requires Power BI Desktop. The included Excel workbook is already usable.

## Import the tables

Open Power BI Desktop > **Get data > Text/CSV**, then import these files from `powerbi/model/`:

| CSV | Rename to | Grain |
| --- | --- | --- |
| `dim_customers.csv` | `DimCustomers` | Customer |
| `fact_transactions.csv` | `FactTransactions` | Transaction |
| `fact_scenario_hits.csv` | `FactScenarioHits` | Transaction × scenario hit |
| `fact_customer_month_flags.csv` | `FactCustomerMonthFlags` | Customer × month × review scenario |
| `fact_customer_month.csv` | `FactCustomerMonth` | Customer × month (audit/detail) |

Use Power Query to set `booked_at` and `onboarded_at` to Date, `amount_usd` and other `_usd` values to Fixed decimal/Decimal number, `cross_border` to Whole number, and IDs to Text. `month` is a `yyyy-MM` text label and sorts chronologically. **Do not sum across repeated scenarios to count distinct flagged transactions.**

## Model relationships

- `DimCustomers[customer_id]` (one) → `FactTransactions[customer_id]` (many), single-direction.
- `FactTransactions[transaction_id]` (one) → `FactScenarioHits[transaction_id]` (many), single-direction.
- `DimCustomers[customer_id]` (one) → `FactCustomerMonthFlags[customer_id]` (many), single-direction.
- `DimCustomers[customer_id]` (one) → `FactCustomerMonth[customer_id]` (many), single-direction.

In `FactTransactions`, create calculated column `Month = FORMAT(FactTransactions[booked_at], "yyyy-MM")` for visuals. For shared month slicers across the customer-month flags table, create a distinct month dimension with `month` labels and use single-direction relationships; alternatively use separate month slicers. Avoid multiple active ambiguous fact-to-fact paths. Because `FactCustomerMonth` and `FactTransactions` overlap at customer level, **never sum both into one transaction denominator**.

## Measures

Copy measures individually from [`powerbi/MEASURES.dax`](../powerbi/MEASURES.dax). In particular:

- **Flagged Transactions** = distinct transaction IDs in `FactScenarioHits`; overlapping scenarios do not duplicate it.
- **Scenario Hits** = total rows in `FactScenarioHits`; overlap is deliberately counted.
- **Flagged Transaction Rate** = flagged transactions / all cleaned transactions under the same filter context.
- **Gross Volume USD** = sum of transaction amount magnitudes, *not* the net flow.
- **Net Inflows USD** = inflow magnitudes less outflow magnitudes.
- **Customer-Month Review Flags** = separate case-level review indicators, *not* transaction alerts.

## Suggested report pages

**Page 1 — Portfolio overview:** Cards for Transactions, Gross Volume, Flagged Transactions, Flagged Transaction Rate, and Customer-Month Review Flags. Line chart for Inflows / Outflows by FactTransactions[Month]. Column chart for scenario hits by FactScenarioHits[scenario_code]. Bar chart for gross volume by channel. Slicers for risk tier, segment and transaction month. Label all charts **Synthetic**.

**Page 2 — Review explorer:** Matrix by customer risk tier and segment with Transactions, Flagged Transactions and Gross Volume. A detail table by customer-month (use FactCustomerMonth) with monthly volume, expected monthly volume, and review flags. Set the descriptive title to "Illustrative review queue" rather than "Suspicious customers."

**Page 3 — Data controls:** Data-quality rejects from `data/processed/dq_rejections.csv`; row counts; the reconciliation checks documented in `docs/VALIDATION.md`.

## Quality check after build

With slicers cleared, the five core outputs should match `data/processed/summary.json`: **5,067 transactions**, **$58,775,686.58** gross volume, **804 distinct flagged transactions**, **15.87% flagged rate**, **15 customer-month review flags**. There are **906 scenario-hit rows** and **24 quarantined raw records**. DAX totals should react to segment/risk filters. Do not use gross transaction volume as net inflow, and do not treat indicator hits as SAR determinations.
