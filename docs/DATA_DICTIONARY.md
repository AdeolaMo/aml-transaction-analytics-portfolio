# Data dictionary and grains

**Entirely synthetic**; no real institution, individual, investigation, customer or counterparty.

## Source tables

### `data/raw/customers.csv` — one row per fictional customer

| Field | Type | Meaning |
|---|---|---|
| `customer_id` | Text, unique | Fictional stable customer identifier |
| `customer_name` | Text | Synthetic nonidentifying label |
| `segment` | RETAIL / SME / CORPORATE | Illustrative customer segment |
| `risk_tier` | LOW / MEDIUM / HIGH | Fictional preset segmentation (not an AML risk scoring model) |
| `onboarded_at` | ISO Date | Fictional account onboarding date |
| `expected_monthly_volume_usd` | USD Decimal | Illustrative customer expected activity; used only for variance indicator |
| `home_country` | Country code | US for all demo customers |

### `data/raw/transactions_raw.csv` — one incoming source-row per transaction observation

| Field | Type | Meaning |
|---|---|---|
| `transaction_id` | Text | Payment ID; intentionally duplicated in four invalid records |
| `customer_id` | Text | FK to customers |
| `booked_at` | ISO Date | Fictional transaction booking date |
| `direction` | IN / OUT | Direction relative to fictional customer account |
| `channel` | ACH / WIRE / CARD / CASH | Product/channel label |
| `amount_usd` | Decimal USD | Positive absolute magnitude; not signed balance |
| `counterparty_country` | ISO-like two-letter | Simplified jurisdiction field |
| `cross_border` | 0 / 1 | 1 iff counterparty_country != US; no sanctions assessment |
| `reference_id` | Text | Synthetic audit trace |

`data/processed/transactions_clean.csv` contains only rows passing validation. `dq_rejections.csv` contains **one reason per rejected row** under documented precedence and the original CSV line number. The pipeline uses `Decimal` and integer cents internally.

## Analytical tables

| Dataset | Grain | Measurement |
|---|---|---|
| `transaction_scenario_hits.csv` | Transaction × scenario | Potentially multiple hits per transaction |
| `customer_month_flags.csv` | Customer × month × scenario | Separate monthly profile-level indicators |
| `kpi_monthly.csv` | Calendar month | Reconciled monthly aggregates |
| `kpi_scenarios.csv` | Scenario | Hit count, distinct affected customers, sum of hit magnitudes |
| `kpi_segments.csv` | Customer segment | Transactions, unique flagged transactions, volume, customers |
| `kpi_channels.csv` | Payment channel | Transactions, unique flagged transactions, volume |
| `customer_month_review.csv` | Customer × month | Inflows, outflows, gross volume, expected activity, flag count |

## Counting rules

- **Transaction** = one unique validated `transaction_id`.
- **Gross volume** = sum of positive transaction magnitudes; not net inflow and not customer account balances.
- **Flagged transaction** = transaction ID with ≥1 scenario hit, counted exactly once even if several scenario hits apply.
- **Scenario hit** = one rule hit on one transaction; additive by scenario but not equivalent to distinct flagged transactions.
- **Flagged rate** = distinct flagged transactions / all valid transactions in the selected population.
- **Customer-month review flag** = one hit per customer-month per monthly scenario; not a transaction alert.
- **Risk tier** is a synthetic input categorical attribute; not derived by this portfolio.
