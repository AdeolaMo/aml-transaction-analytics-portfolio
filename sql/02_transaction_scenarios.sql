-- All thresholds are DEMONSTRATION parameters, not legal/regulatory thresholds.
DELETE FROM transaction_scenario_hits;
INSERT INTO transaction_scenario_hits
SELECT transaction_id, 'LARGE_WIRE' FROM transactions
WHERE channel='WIRE' AND amount_cents >= 3000000;
INSERT INTO transaction_scenario_hits
SELECT transaction_id, 'CROSS_BORDER_WIRE' FROM transactions
WHERE channel='WIRE' AND cross_border=1 AND amount_cents >= 1200000;
INSERT INTO transaction_scenario_hits
SELECT transaction_id, 'CASH_AMOUNT_REVIEW' FROM transactions
WHERE channel='CASH' AND amount_cents >= 800000;
INSERT INTO transaction_scenario_hits
SELECT transaction_id, 'LARGE_OUTBOUND_ACH' FROM transactions
WHERE channel='ACH' AND direction='OUT' AND amount_cents >= 4500000;

DELETE FROM customer_month_summary;
INSERT INTO customer_month_summary
SELECT customer_id, substr(booked_at,1,7) AS month,
       COUNT(*) AS txn_count,
       SUM(CASE WHEN direction='IN' THEN amount_cents ELSE 0 END) AS inflow_cents,
       SUM(CASE WHEN direction='OUT' THEN amount_cents ELSE 0 END) AS outflow_cents,
       SUM(amount_cents) AS gross_volume_cents
FROM transactions GROUP BY customer_id, substr(booked_at,1,7);
DELETE FROM customer_month_flags;
INSERT INTO customer_month_flags
SELECT m.customer_id,m.month,'TWO_WAY_FLOW'
FROM customer_month_summary m
WHERE inflow_cents >= 4000000 AND outflow_cents >= 4000000
 AND 1.0*outflow_cents/NULLIF(inflow_cents,0) BETWEEN 0.90 AND 1.10;
INSERT INTO customer_month_flags
SELECT m.customer_id,m.month,'PROFILE_VOLUME_VARIANCE'
FROM customer_month_summary m JOIN customers c USING(customer_id)
WHERE m.gross_volume_cents > 2.5*c.expected_monthly_volume_cents;
