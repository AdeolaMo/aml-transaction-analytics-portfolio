# Validation record

Run:

```bash
python scripts/generate_synthetic_data.py
python scripts/run_analysis.py
python -m unittest discover -s tests -v
```

Expected on the deterministic data seed:

| Metric | Expected |
|---|---:|
| Synthetic customers | 140 |
| Raw transaction rows | 5,091 |
| Validated transactions | 5,067 |
| Quarantined rows | 24 |
| Gross amount magnitude | $58,775,686.58 |
| Distinct flagged transactions | 804 |
| Transaction scenario hits | 906 |
| Flagged rate | 15.87% |
| Customer-month review flags | 15 |

Reconciliation assertions appear in `scripts/run_analysis.py`. Eight tests cover source-clean/reject partition, exact cents/volume reconciliation, scenario hit overlap, independent scenario rules, customer-month flags, rejection reasons, country-flag consistency and synthetic identifiers. **Do not conflate monitoring indicators with illegal activity.**
