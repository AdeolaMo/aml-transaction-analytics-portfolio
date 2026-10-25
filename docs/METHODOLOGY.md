# Methodology and interpretation

## Analyst question

Given fictional transaction records and CDD-style expected-volume information, can we validate the source, generate reproducible transaction-monitoring **review indicators**, reconcile volume and counts, and communicate exceptions in an accessible dashboard?

## Fully illustrative transaction-level scenarios

The thresholds below are **fabricated for this portfolio, not U.S. regulatory thresholds or real bank AML policy**.

| Code | Illustrative trigger |
|---|---|
| `LARGE_WIRE` | WIRE and amount ≥ **$30,000** |
| `CROSS_BORDER_WIRE` | WIRE, non-US counterparty-country flag, amount ≥ **$12,000** |
| `CASH_AMOUNT_REVIEW` | CASH and amount ≥ **$8,000** |
| `LARGE_OUTBOUND_ACH` | ACH, OUT direction, amount ≥ **$45,000** |

A wire can match both `LARGE_WIRE` and `CROSS_BORDER_WIRE`. That **does not mean two distinct flagged payments**.

## Separate monthly pattern indicators

| Code | Illustrative trigger |
|---|---|
| `TWO_WAY_FLOW` | Inflow ≥ $40k, outflow ≥ $40k and 0.90 ≤ outflow/inflow ≤ 1.10 in the same customer-month |
| `PROFILE_VOLUME_VARIANCE` | Customer-month gross transaction volume > 2.5× fictional expected monthly volume |

These indicate unusual quantitative conditions in *synthetic records*. They do not establish financial crime or require a SAR.

## Data quality and auditability

- Generator seed `20261024` reproduces the same fictional transactions.
- 24 deliberately planted invalid records: four each of duplicate transaction ID, unknown customer, invalid direction, zero amount, invalid date, cross-border/country mismatch.
- First-failure data-quality rule determines one rejection reason per raw row.
- Money is validated in decimal cents and stored as SQLite integer cents.
- Analysis aggregates from the validated base table, **not** from a scenario-join that duplicates transactions.
- Distinct flags, scenario-hit totals, gross volume, inbound/outbound volume, segment/channel totals, and monthly totals are independently reconciled.
- Unit and integration tests recompute scenario eligibility without reusing the SQL rule table.

## Regulatory context, carefully scoped

The FFIEC BSA/AML Examination Manual distinguishes identification of unusual activity, managing alerts, SAR decision-making, completion/filing and monitoring continuing activity. This portfolio **models only identification-style quantitative indicators**; it has no determinations of suspicious activity, SAR necessity, entity-level culpability or sanctions status.

Primary context: https://bsaaml.ffiec.gov/manual/AssessingComplianceWithBSARegulatoryRequirements/04

## Limits

Simulated single-currency USD data; simplified channels and countries; no counterparty entity-resolution, customer-bank consolidated view, alert disposition, transaction velocity windows, account balances, reporting requirements, tuning or false-positive claims. No effectiveness/recall claims are possible because there is no genuine labeled wrongdoing or investigation ground truth.
