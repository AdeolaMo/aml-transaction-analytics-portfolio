"""Validate raw fictional transaction data; build audited SQLite marts and BI exports.
Run from any directory: python scripts/run_analysis.py
No external Python packages required.
"""
from __future__ import annotations
import csv, json, re, sqlite3
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'data' / 'raw'; OUT = ROOT / 'data' / 'processed'; BI = ROOT / 'powerbi' / 'model'
SQL = ROOT / 'sql'; DB = OUT / 'aml_demo.sqlite'
TX_COLUMNS=['transaction_id','customer_id','booked_at','direction','channel','amount_usd','counterparty_country','cross_border','reference_id']
CUST_COLUMNS=['customer_id','customer_name','segment','risk_tier','onboarded_at','expected_monthly_volume_usd','home_country']
CLEAN_COLUMNS=['transaction_id','customer_id','booked_at','month','direction','channel','amount_usd','counterparty_country','cross_border','reference_id']

def read_csv(path):
    with path.open(newline='', encoding='utf-8') as f: return list(csv.DictReader(f))

def write_csv(path, fields, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=fields,lineterminator='\n')
        writer.writeheader()
        for row in data:writer.writerow({k:row.get(k,'') for k in fields})

def cents(s):
    try:
        a=Decimal(str(s))
        if not a.is_finite() or a <= 0 or a.as_tuple().exponent < -2: return None
        return int(a*100)
    except (InvalidOperation,TypeError,ValueError):return None

def validate_transaction(row, customer_ids, seen):
    txn=row['transaction_id']
    if not re.fullmatch(r'(?:T\d{6}|BAD\d{4})',txn):return 'INVALID_TRANSACTION_ID'
    if txn in seen:return 'DUPLICATE_TRANSACTION_ID'
    if row['customer_id'] not in customer_ids:return 'UNKNOWN_CUSTOMER'
    if row['direction'] not in ('IN','OUT'):return 'INVALID_DIRECTION'
    if row['channel'] not in ('ACH','WIRE','CARD','CASH'):return 'INVALID_CHANNEL'
    if cents(row['amount_usd']) is None:return 'INVALID_AMOUNT'
    try: d=date.fromisoformat(row['booked_at'])
    except ValueError:return 'INVALID_DATE'
    if d < date(2026,4,1) or d > date(2026,9,30):return 'OUTSIDE_PERIOD'
    country=row['counterparty_country']
    if not re.fullmatch('[A-Z]{2}', country):return 'INVALID_COUNTRY'
    if row['cross_border'] not in ('0','1') or int(row['cross_border'])!=int(country!='US'):return 'CROSS_BORDER_INCONSISTENT'
    return None

def database(customers, cleaned):
    if DB.exists():DB.unlink()
    conn=sqlite3.connect(DB);conn.executescript((SQL/'01_schema.sql').read_text())
    conn.executemany('INSERT INTO customers VALUES (?,?,?,?,?,?,?)', [(
        c['customer_id'],c['customer_name'],c['segment'],c['risk_tier'],c['onboarded_at'],
        cents(c['expected_monthly_volume_usd']),c['home_country']) for c in customers])
    conn.executemany('INSERT INTO transactions VALUES (?,?,?,?,?,?,?,?,?)', [(
        t['transaction_id'],t['customer_id'],t['booked_at'],t['direction'],t['channel'],
        cents(t['amount_usd']),t['counterparty_country'],int(t['cross_border']),t['reference_id']) for t in cleaned])
    conn.executescript((SQL/'02_transaction_scenarios.sql').read_text());conn.commit()
    return conn

def export_query(conn, filename, columns, sql, params=()):
    conn.row_factory=sqlite3.Row
    data=[dict(x) for x in conn.execute(sql,params).fetchall()]
    write_csv(OUT/filename, columns, data)
    return data

def run():
    OUT.mkdir(parents=True, exist_ok=True);BI.mkdir(parents=True, exist_ok=True)
    customers=read_csv(RAW/'customers.csv')
    if len(set(x['customer_id'] for x in customers))!=len(customers):raise ValueError('Customer IDs not unique')
    customer_ids={c['customer_id'] for c in customers}
    for c in customers:
        if c['segment'] not in ('RETAIL','SME','CORPORATE') or c['risk_tier'] not in ('LOW','MEDIUM','HIGH') or cents(c['expected_monthly_volume_usd']) is None:
            raise ValueError(f'Invalid customer dimension: {c["customer_id"]}')
    seen=set(); cleaned=[]; rejected=[]
    for line_num,t in enumerate(read_csv(RAW/'transactions_raw.csv'),start=2):
        reason=validate_transaction(t,customer_ids,seen)
        if reason:rejected.append(dict(source_row=line_num,transaction_id=t['transaction_id'],reason=reason))
        else:
            seen.add(t['transaction_id']);cleaned.append(t)
    write_csv(OUT/'transactions_clean.csv',TX_COLUMNS,cleaned)
    write_csv(OUT/'dq_rejections.csv',['source_row','transaction_id','reason'],rejected)
    conn=database(customers,cleaned)
    txn_hits=export_query(conn,'transaction_scenario_hits.csv',['transaction_id','scenario_code'],
        'SELECT transaction_id,scenario_code FROM transaction_scenario_hits ORDER BY transaction_id,scenario_code')
    monthly_flags=export_query(conn,'customer_month_flags.csv',['customer_id','month','scenario_code'],
        'SELECT customer_id,month,scenario_code FROM customer_month_flags ORDER BY month,customer_id,scenario_code')
    # Derive additive values from base transactions, never from the one-to-many hit join.
    monthly=export_query(conn,'kpi_monthly.csv',['month','txn_count','flagged_transactions','scenario_hits','inflow_usd','outflow_usd','gross_volume_usd','active_customers','customer_month_flags'],'''
      WITH base AS (
         SELECT substr(booked_at,1,7) month, COUNT(*) txn_count,
          ROUND(SUM(CASE WHEN direction='IN' THEN amount_cents ELSE 0 END)/100.0,2) inflow_usd,
          ROUND(SUM(CASE WHEN direction='OUT' THEN amount_cents ELSE 0 END)/100.0,2) outflow_usd,
          ROUND(SUM(amount_cents)/100.0,2) gross_volume_usd,
          COUNT(DISTINCT customer_id) active_customers FROM transactions GROUP BY substr(booked_at,1,7)
      ), hits AS (
         SELECT substr(t.booked_at,1,7) month, COUNT(DISTINCT h.transaction_id) flagged_transactions,
             COUNT(*) scenario_hits FROM transaction_scenario_hits h JOIN transactions t USING(transaction_id)
             GROUP BY substr(t.booked_at,1,7)
      ), flags AS (
         SELECT month,COUNT(*) customer_month_flags FROM customer_month_flags GROUP BY month
      )
      SELECT base.*,COALESCE(hits.flagged_transactions,0) flagged_transactions,
            COALESCE(hits.scenario_hits,0) scenario_hits,
            COALESCE(flags.customer_month_flags,0) customer_month_flags
      FROM base LEFT JOIN hits USING(month) LEFT JOIN flags USING(month) ORDER BY base.month''')
    scenarios=export_query(conn,'kpi_scenarios.csv',['scenario_code','hit_count','distinct_customers','hit_value_usd'],'''
      SELECT scenario_code,COUNT(*) hit_count, COUNT(DISTINCT t.customer_id) distinct_customers,
         ROUND(SUM(t.amount_cents)/100.0,2) hit_value_usd
      FROM transaction_scenario_hits h JOIN transactions t USING(transaction_id)
      GROUP BY scenario_code ORDER BY hit_count DESC,scenario_code''')
    segments=export_query(conn,'kpi_segments.csv',['segment','transaction_count','flagged_transactions','gross_volume_usd','customers'],'''
      SELECT c.segment,COUNT(t.transaction_id) transaction_count,
         COUNT(DISTINCT h.transaction_id) flagged_transactions,
         ROUND(SUM(t.amount_cents)/100.0,2) gross_volume_usd,
         COUNT(DISTINCT t.customer_id) customers
      FROM customers c JOIN transactions t USING(customer_id)
      LEFT JOIN (SELECT DISTINCT transaction_id FROM transaction_scenario_hits) h ON h.transaction_id=t.transaction_id
      GROUP BY c.segment ORDER BY c.segment''')
    channels=export_query(conn,'kpi_channels.csv',['channel','transaction_count','flagged_transactions','gross_volume_usd'],'''
      SELECT t.channel,COUNT(*) transaction_count,
      SUM(CASE WHEN h.transaction_id IS NOT NULL THEN 1 ELSE 0 END) flagged_transactions,
      ROUND(SUM(t.amount_cents)/100.0,2) gross_volume_usd FROM transactions t
      LEFT JOIN (SELECT DISTINCT transaction_id FROM transaction_scenario_hits) h USING(transaction_id)
      GROUP BY t.channel ORDER BY gross_volume_usd DESC''')
    customer_review=export_query(conn,'customer_month_review.csv',['customer_id','customer_name','segment','risk_tier','month','txn_count','inflow_usd','outflow_usd','gross_volume_usd','expected_monthly_volume_usd','flag_count'],'''
      SELECT m.customer_id,c.customer_name,c.segment,c.risk_tier,m.month,m.txn_count,
             ROUND(m.inflow_cents/100.0,2) inflow_usd,ROUND(m.outflow_cents/100.0,2) outflow_usd,
             ROUND(m.gross_volume_cents/100.0,2) gross_volume_usd,
             ROUND(c.expected_monthly_volume_cents/100.0,2) expected_monthly_volume_usd,
             (SELECT COUNT(*) FROM customer_month_flags f WHERE f.customer_id=m.customer_id AND f.month=m.month) flag_count
      FROM customer_month_summary m JOIN customers c USING(customer_id)
      ORDER BY flag_count DESC,gross_volume_usd DESC,customer_id,month''')
    n=len(cleaned); total_cents=sum(cents(t['amount_usd']) for t in cleaned)
    flagged_count=conn.execute('SELECT COUNT(DISTINCT transaction_id) FROM transaction_scenario_hits').fetchone()[0]
    total_hits=conn.execute('SELECT COUNT(*) FROM transaction_scenario_hits').fetchone()[0]
    monthly_flags_count=len(monthly_flags)
    # Independent data lineage and reconciliation checks (fail loud)
    assert sum(int(x['txn_count']) for x in monthly)==n
    assert abs(sum(Decimal(str(x['gross_volume_usd'])) for x in monthly)-Decimal(total_cents)/100)<Decimal('0.01')
    assert sum(int(x['flagged_transactions']) for x in monthly)==flagged_count
    assert sum(int(x['scenario_hits']) for x in monthly)==total_hits==len(txn_hits)==sum(int(x['hit_count']) for x in scenarios)
    assert sum(int(x['customer_month_flags']) for x in monthly)==monthly_flags_count
    assert sum(int(x['transaction_count']) for x in segments)==n
    assert sum(int(x['flagged_transactions']) for x in segments)==flagged_count
    assert sum(int(x['transaction_count']) for x in channels)==n
    assert sum(int(x['flagged_transactions']) for x in channels)==flagged_count
    by_reason=defaultdict(int)
    for r in rejected:by_reason[r['reason']]+=1
    summary=dict(synthetic=True,period_start='2026-04-01',period_end='2026-09-30',customers=len(customers),
        clean_transactions=n,raw_transactions=n+len(rejected),rejected_records=len(rejected),
        gross_volume_usd=round(total_cents/100,2),flagged_transactions=flagged_count,
        flagged_transaction_rate_pct=round(100*flagged_count/n,2),transaction_scenario_hits=total_hits,
        customer_month_review_flags=monthly_flags_count,
        rejected_by_reason=dict(sorted(by_reason.items())))
    (OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    # Portable Power BI model tables at declared grains.
    for src,dst in [('transactions_clean.csv','fact_transactions.csv'),('transaction_scenario_hits.csv','fact_scenario_hits.csv'),
        ('customer_month_review.csv','fact_customer_month.csv'),('customer_month_flags.csv','fact_customer_month_flags.csv'),
        ('kpi_monthly.csv','view_monthly.csv')]:
        (BI/dst).write_bytes((OUT/src).read_bytes())
    (BI/'dim_customers.csv').write_bytes((RAW/'customers.csv').read_bytes())
    conn.close()
    print(json.dumps(summary,indent=2))
    return summary

if __name__=='__main__':run()
