"""Generate entirely fictional customers, payments and intentionally invalid raw records."""
from __future__ import annotations
import argparse
import csv
from datetime import date, timedelta
from pathlib import Path
import random

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'data' / 'raw'
SEED = 20261024
COUNTRY = ['US', 'US', 'US', 'US', 'CA', 'GB', 'MX', 'SG', 'AE']
CHANNELS = ['ACH', 'ACH', 'WIRE', 'WIRE', 'CARD', 'CASH']
SEGMENTS = ['RETAIL', 'SME', 'CORPORATE']
RISKS = ['LOW', 'LOW', 'MEDIUM', 'MEDIUM', 'HIGH']
CUSTOMER_FIELDS = ['customer_id','customer_name','segment','risk_tier','onboarded_at','expected_monthly_volume_usd','home_country']
TX_FIELDS = ['transaction_id','customer_id','booked_at','direction','channel','amount_usd','counterparty_country','cross_border','reference_id']

def write_csv(path, header, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='', encoding='utf-8') as f:
        w=csv.DictWriter(f, fieldnames=header, lineterminator='\n');w.writeheader();w.writerows(rows)

def generate():
    rng = random.Random(SEED)
    customers=[]
    for n in range(1,141):
        seg = SEGMENTS[(n-1)%3]
        risk = RISKS[(n*7 + n//9)%len(RISKS)]
        expected = {'RETAIL':25000,'SME':75000,'CORPORATE':175000}[seg]
        expected = round(expected*rng.uniform(.75,1.35),2)
        customers.append(dict(customer_id=f'C{n:04}',customer_name=f'Synthetic Customer {n:03}',segment=seg,
            risk_tier=risk,onboarded_at=f'202{rng.randint(0,4)}-{rng.randint(1,12):02}-{rng.randint(1,28):02}',
            expected_monthly_volume_usd=f'{expected:.2f}',home_country='US'))
    tx=[]; t=0
    start=date(2026,4,1)
    # Six complete fictional months, through September 2026.
    for customer in customers:
        n = int(customer['customer_id'][1:]); base=float(customer['expected_monthly_volume_usd'])
        for month in range(4,10):
            count=rng.randint(3,9)
            if n % 29==0 and month in (6,9): count += 9  # synthetic burst examples
            for _ in range(count):
                t+=1
                day=rng.randint(1, {4:30,5:31,6:30,7:31,8:31,9:30}[month]); dt=date(2026,month,day)
                direction = 'IN' if rng.random()<.51 else 'OUT'
                channel = rng.choice(CHANNELS)
                country = rng.choice(COUNTRY) if channel != 'CASH' else 'US'
                # Amount is generated in cents to avoid binary rounding artifacts.
                nominal=max(900, base/count*rng.lognormvariate(-.3,.6))
                if n%17==0 and month in (5,8) and channel=='WIRE':nominal*=4.2
                if channel=='CASH': nominal=min(nominal,14500)*rng.uniform(.5,1.0)
                if channel=='CARD': nominal=min(nominal,10000)
                cents=int(round(nominal*100))
                tx.append(dict(transaction_id=f'T{t:06}',customer_id=customer['customer_id'],booked_at=dt.isoformat(),
                    direction=direction,channel=channel,amount_usd=f'{cents/100:.2f}',counterparty_country=country,
                    cross_border='1' if country!='US' else '0',reference_id=f'REF{t:07}'))
    tx.sort(key=lambda row:(row['booked_at'],row['transaction_id']))
    # Add 24 deliberate, individually attributable quality exceptions; all fictional.
    bad=[]
    for i in range(1,25):
        r=dict(tx[(i*101)%len(tx)])
        r['reference_id']=f'DQ{i:04}'
        kind=(i-1)%6
        if kind==0: # duplicate transaction identifier, same original row
            r=dict(tx[(i*101)%len(tx)])
        elif kind==1:r['customer_id']='C9999';r['transaction_id']=f'BAD{i:04}'
        elif kind==2:r['direction']='SIDEWAYS';r['transaction_id']=f'BAD{i:04}'
        elif kind==3:r['amount_usd']='0.00';r['transaction_id']=f'BAD{i:04}'
        elif kind==4:r['booked_at']='2026-13-40';r['transaction_id']=f'BAD{i:04}'
        else:r['cross_border']='0' if r['counterparty_country']!='US' else '1';r['transaction_id']=f'BAD{i:04}'
        bad.append(r)
    # Put bad records at end so duplicate-ID quarantine is deterministic.
    RAW.mkdir(parents=True, exist_ok=True)
    write_csv(RAW/'customers.csv', CUSTOMER_FIELDS, customers)
    write_csv(RAW/'transactions_raw.csv',TX_FIELDS, tx+bad)
    print(f'Wrote {len(customers)} fictional customers; {len(tx)} valid generated transactions; {len(bad)} planted quality exceptions')

if __name__ == '__main__':generate()
