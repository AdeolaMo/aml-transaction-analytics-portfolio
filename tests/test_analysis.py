"""Independent invariants against generated fixture and SQLite outputs."""
import csv, json, sqlite3, unittest
from collections import Counter
from decimal import Decimal
from pathlib import Path
from scripts.run_analysis import validate_transaction, cents
ROOT=Path(__file__).resolve().parents[1]

def rows(path):
    with path.open(newline='',encoding='utf-8') as f:return list(csv.DictReader(f))

class PortfolioPipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw=rows(ROOT/'data/raw/transactions_raw.csv')
        cls.clean=rows(ROOT/'data/processed/transactions_clean.csv')
        cls.rejected=rows(ROOT/'data/processed/dq_rejections.csv')
        cls.hits=rows(ROOT/'data/processed/transaction_scenario_hits.csv')
        cls.months=rows(ROOT/'data/processed/kpi_monthly.csv')
        cls.summary=json.loads((ROOT/'data/processed/summary.json').read_text())
        cls.customers=rows(ROOT/'data/raw/customers.csv')
    def test_reconciliation(self):
        self.assertEqual(len(self.raw),len(self.clean)+len(self.rejected))
        self.assertEqual(self.summary['rejected_records'],len(self.rejected))
        self.assertEqual(len({r['transaction_id'] for r in self.clean}),len(self.clean))
        self.assertEqual(len(self.rejected),24)
    def test_amount_precision_and_totals(self):
        actual=sum(Decimal(t['amount_usd']) for t in self.clean)
        self.assertEqual(actual,Decimal(str(self.summary['gross_volume_usd'])))
        monthly=sum(Decimal(t['gross_volume_usd']) for t in self.months)
        self.assertEqual(actual,monthly)
    def test_monthly_counts_and_nonduplicate_hits(self):
        ids={h['transaction_id'] for h in self.hits}
        self.assertEqual(len(ids),self.summary['flagged_transactions'])
        self.assertEqual(len(self.hits),self.summary['transaction_scenario_hits'])
        self.assertGreaterEqual(len(self.hits),len(ids))
        self.assertEqual(sum(int(r['txn_count']) for r in self.months),len(self.clean))
        self.assertEqual(sum(int(r['scenario_hits']) for r in self.months),len(self.hits))
    def test_exact_rule_implementation_independent(self):
        expected=set()
        for t in self.clean:
            a=cents(t['amount_usd']);tid=t['transaction_id']
            if t['channel']=='WIRE' and a>=3000000:expected.add((tid,'LARGE_WIRE'))
            if t['channel']=='WIRE' and t['cross_border']=='1' and a>=1200000:expected.add((tid,'CROSS_BORDER_WIRE'))
            if t['channel']=='CASH' and a>=800000:expected.add((tid,'CASH_AMOUNT_REVIEW'))
            if t['channel']=='ACH' and t['direction']=='OUT' and a>=4500000:expected.add((tid,'LARGE_OUTBOUND_ACH'))
        self.assertEqual(expected,{(r['transaction_id'],r['scenario_code']) for r in self.hits})
    def test_monthly_customer_flags_against_aggregates(self):
        monthly=rows(ROOT/'data/processed/customer_month_review.csv')
        actual={ (r['customer_id'],r['month'],r['scenario_code']) for r in rows(ROOT/'data/processed/customer_month_flags.csv')}
        expected=set()
        for r in monthly:
            incoming=Decimal(r['inflow_usd']);outgoing=Decimal(r['outflow_usd'])
            gross=Decimal(r['gross_volume_usd']);ref=Decimal(r['expected_monthly_volume_usd'])
            key=(r['customer_id'],r['month'])
            if incoming>=40000 and outgoing>=40000 and Decimal('0.9')<=outgoing/incoming<=Decimal('1.1'):
                expected.add((*key,'TWO_WAY_FLOW'))
            if gross>Decimal('2.5')*ref:expected.add((*key,'PROFILE_VOLUME_VARIANCE'))
        self.assertEqual(expected,actual)
    def test_quality_reason_distribution(self):
        types=Counter(r['reason'] for r in self.rejected)
        self.assertEqual(set(types),{'DUPLICATE_TRANSACTION_ID','UNKNOWN_CUSTOMER','INVALID_DIRECTION',
            'INVALID_AMOUNT','INVALID_DATE','CROSS_BORDER_INCONSISTENT'})
        self.assertTrue(all(v==4 for v in types.values()))
    def test_cross_border_consistency(self):
        self.assertTrue(all((t['cross_border']=='1')==(t['counterparty_country']!='US') for t in self.clean))
    def test_data_not_real_identities(self):
        self.assertTrue(all(c['customer_name'].startswith('Synthetic Customer ') for c in self.customers))

if __name__=='__main__':unittest.main()
