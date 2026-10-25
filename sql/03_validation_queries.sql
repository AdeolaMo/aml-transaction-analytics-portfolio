-- Core reconciliations: these should all return zero or the expected equality.
SELECT 'txn_count' AS metric, COUNT(*) AS value FROM transactions;
SELECT 'distinct_ids' AS metric, COUNT(DISTINCT transaction_id) AS value FROM transactions;
SELECT 'value_cents' AS metric, SUM(amount_cents) AS value FROM transactions;
SELECT 'month_value_cents' AS metric, SUM(gross_volume_cents) AS value FROM customer_month_summary;
SELECT 'flagged_distinct' AS metric, COUNT(DISTINCT transaction_id) AS value FROM transaction_scenario_hits;
SELECT 'scenario_hits' AS metric, COUNT(*) AS value FROM transaction_scenario_hits;
