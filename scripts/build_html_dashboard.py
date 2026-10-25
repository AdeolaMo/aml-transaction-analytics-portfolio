"""Build a zero-dependency offline HTML analytical viewer from validated marts."""
from __future__ import annotations
import csv,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(p):
 with (ROOT/p).open(newline='',encoding='utf-8') as f:return list(csv.DictReader(f))
cs=read(Path('data/raw/customers.csv'))
ts=read(Path('data/processed/transactions_clean.csv'))
sh=read(Path('data/processed/transaction_scenario_hits.csv'))
cf=read(Path('data/processed/customer_month_flags.csv'))
content={
 'customers':{x['customer_id']:x for x in cs},
 'transactions':[{k:v for k,v in t.items() if k in ('transaction_id','customer_id','booked_at','direction','channel','amount_usd','cross_border')} for t in ts],
 'hits':[[h['transaction_id'],h['scenario_code']] for h in sh],
 'monthFlags':[[f['customer_id'],f['month'],f['scenario_code']] for f in cf],
}
# No remote code, no real identities, and values are JSON-escaped.
script=json.dumps(content,separators=(',',':')).replace('</','<\\/')
html=r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Synthetic AML Transaction Intelligence — Portfolio Demo</title>
<style>
:root{--ink:#13243d;--muted:#5b6f82;--blue:#176aa6;--teal:#0e7d78;--orange:#f0a43b;--border:#dce6ef;--bg:#f1f5f9}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font-family:Inter,ui-sans-serif,system-ui,-apple-system,'Segoe UI',Arial}
header{background:linear-gradient(105deg,#13243d,#176aa6);padding:34px max(22px,calc((100vw - 1200px)/2));color:white}
header h1{font-size:clamp(24px,3.1vw,36px);letter-spacing:-.8px;margin:4px 0 9px}header p{color:#dcebf8;margin:0;max-width:980px;line-height:1.55}
.shell{max-width:1240px;margin:auto;padding:23px 18px 55px}.filters{display:flex;flex-wrap:wrap;gap:15px;align-items:end;background:white;border:1px solid var(--border);border-radius:13px;padding:18px;margin-bottom:18px}
.filter{display:flex;flex-direction:column;gap:5px;flex:1;min-width:150px}label{font-size:12px;font-weight:800;text-transform:uppercase;letter-spacing:.075em;color:var(--muted)}select{border:1px solid #cbd8e3;border-radius:8px;padding:9px 11px;background:#fff;font:inherit;color:var(--ink);height:42px}
button{border:1px solid var(--border);border-radius:9px;background:#eff6fb;color:var(--blue);font:inherit;font-weight:700;cursor:pointer;padding:10px 16px;height:42px}
.kpis{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:12px;margin:18px 0}.kpi{padding:18px;border-radius:12px;background:white;border:1px solid var(--border);box-shadow:0 2px 5px #14284005}.kpi .lbl{font-size:11px;color:var(--muted);font-weight:800;text-transform:uppercase;letter-spacing:.065em}.kpi .val{font-weight:800;font-size:clamp(21px,2.5vw,30px);margin:5px 0}.kpi .sub{font-size:12px;color:var(--muted)}
.cols{display:grid;grid-template-columns:1.2fr 1fr;gap:16px;margin-bottom:16px}.panel{background:white;border:1px solid var(--border);border-radius:13px;padding:20px;min-width:0}.panel h2{margin:0 0 4px;font-size:17px}.desc{color:var(--muted);font-size:12px;line-height:1.5;margin:0 0 10px}.grid2{display:grid;grid-template-columns:1fr 1fr;gap:16px}
svg{display:block;width:100%;height:250px;overflow:visible}.axis{font-size:11px;fill:#627588}.rule-row{display:grid;grid-template-columns:minmax(0,160px) 1fr 44px;gap:10px;align-items:center;padding:9px 0;font-size:12px}.bartrack{height:17px;border-radius:5px;background:#e7eff5;overflow:hidden}.bar{height:100%;border-radius:5px;background:#176aa6}.n{font-variant-numeric:tabular-nums;text-align:right;font-weight:700}
.tblwrap{overflow:auto;max-height:480px}table{border-collapse:collapse;width:100%;font-size:12px}th,td{text-align:left;white-space:nowrap;padding:11px 9px;border-bottom:1px solid #e8eef3}th{position:sticky;top:0;background:#eef4f8;font-size:11px;text-transform:uppercase;letter-spacing:.05em;color:#455e76}tr:hover td{background:#f6fafc}td.num{text-align:right;font-variant-numeric:tabular-nums}.tag{padding:3px 7px;border-radius:5px;background:#eaf3f7;color:#265c7c;font-size:10px;font-weight:800}
.note{margin:19px 0;border-left:4px solid var(--orange);border-radius:6px;background:#fff7e9;padding:14px 18px;color:#614719;font-size:13px;line-height:1.5}footer{font-size:12px;color:var(--muted);margin:20px 0}
@media(max-width:950px){.kpis{grid-template-columns:repeat(2,1fr)}.cols,.grid2{grid-template-columns:1fr}}@media(max-width:540px){.kpis{grid-template-columns:1fr}.rule-row{grid-template-columns:125px 1fr 34px}header{padding:28px 18px}}
</style>
</head><body>
<header><div style="font-size:11px;font-weight:800;letter-spacing:.12em;color:#a6efdf">SYNTHETIC DATA · PORTFOLIO DEMONSTRATION</div><h1>Transaction intelligence</h1><p>SQL + Python transaction-data validation, scenario monitoring and financial-flow reporting. Fictional customers and illustrative review conditions; not a live compliance system or suspicious-activity determination.</p></header>
<main class="shell"><section class="filters" aria-label="Dashboard filters"><div class="filter"><label for="month">Booking month</label><select id="month"><option value="ALL">All months</option></select></div><div class="filter"><label for="segment">Customer segment</label><select id="segment"><option value="ALL">All segments</option><option>RETAIL</option><option>SME</option><option>CORPORATE</option></select></div><div class="filter"><label for="risk">Fictional risk tier</label><select id="risk"><option value="ALL">All tiers</option><option>LOW</option><option>MEDIUM</option><option>HIGH</option></select></div><button id="reset">Reset filters</button></section>
<section class="kpis" id="kpis" aria-live="polite"></section>
<div class="cols"><article class="panel"><h2>Monthly movement of funds</h2><p class="desc">Monthly inbound and outbound transaction magnitudes, USD. These are not account balances.</p><svg id="flows" role="img" aria-label="Line chart of monthly inflows and outflows"></svg></article><article class="panel"><h2>Transaction scenario hits</h2><p class="desc">Nonexclusive illustrative rules. One transaction may appear in more than one scenario.</p><div id="rules"></div></article></div>
<div class="cols"><article class="panel"><h2>Flagged transaction trend</h2><p class="desc">Distinct transactions with one or more rule hits, monthly.</p><svg id="alerts" role="img" aria-label="Line chart of monthly distinct flagged transactions"></svg></article><article class="panel"><h2>Volume by payment channel</h2><p class="desc">Gross movement magnitude (IN and OUT combined), USD.</p><div id="channels"></div></article></div>
<article class="panel" style="margin:16px 0"><h2>Illustrative customer-month review queue</h2><p class="desc">Only rows meeting a customer-month pattern indicator are shown; not a finding or prioritization of suspicious customers. Indicators are separate from transaction hits.</p><div class="tblwrap"><table><thead><tr><th>Customer</th><th>Month</th><th>Review indicator</th><th>Segment</th><th>Tier</th><th class="num">Gross USD</th></tr></thead><tbody id="review"></tbody></table></div></article>
<article class="panel"><h2>Transaction inspection sample</h2><p class="desc">Up to 18 recently booked transactions in the current filter. Scenario labels are based on synthetic conditions, not legal thresholds.</p><div class="tblwrap"><table><thead><tr><th>Date</th><th>Transaction</th><th>Customer</th><th>Dir.</th><th>Channel</th><th class="num">USD</th><th>Scenario hits</th></tr></thead><tbody id="details"></tbody></table></div></article>
<div class="note"><strong>Interpretation:</strong> All data, expected activity and review parameters are invented. No real institution's policy, banking customers, SAR information or restricted datasets are used. An alert is not a suspicious-activity conclusion. Distinct flagged transactions are counted once; scenario hits may overlap.</div>
<footer>Reproducible source: scripts/, sql/, tests/, data/. Excel dashboard and Power BI-ready import tables are included in the portfolio archive. Rules are documented in docs/METHODOLOGY.md.</footer>
</main>
<script>const MODEL=__DATA__;
const $=id=>document.getElementById(id);
const months=[...new Set(MODEL.transactions.map(t=>t.booked_at.slice(0,7)))].sort();
months.forEach(m=>{const o=document.createElement('option');o.value=m;o.textContent=m;$('month').appendChild(o)});
const byCustomer=MODEL.customers;
const byHit={};MODEL.hits.forEach(([id,rule])=>(byHit[id]??=[]).push(rule));
const fmtInt=new Intl.NumberFormat('en-US',{maximumFractionDigits:0});
const fmtUsd=new Intl.NumberFormat('en-US',{style:'currency',currency:'USD',maximumFractionDigits:0});
const fmtPct=v=>`${(v*100).toFixed(1)}%`;
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function getFiltered(){const month=$('month').value,seg=$('segment').value,risk=$('risk').value;
 return MODEL.transactions.filter(t=>(month==='ALL'||t.booked_at.startsWith(month)) && (seg==='ALL'||byCustomer[t.customer_id].segment===seg) && (risk==='ALL'||byCustomer[t.customer_id].risk_tier===risk));}
function svgLine(id,series,{money=false}={}){
 const el=$(id),W=610,H=240,left=50,right=12,top=12,bottom=35,plotW=W-left-right,plotH=H-top-bottom;
 const mx=Math.max(1,...series.flatMap(x=>x.values));const ymax=Math.ceil(mx/(money?1000000:25))*(money?1000000:25);
 let a=[];for(let j=0;j<=4;j++){const y=top+(4-j)*plotH/4;const v=j*ymax/4;a.push(`<line x1="${left}" y1="${y}" x2="${W-right}" y2="${y}" stroke="#d9e3eb" stroke-dasharray="3 4"/><text x="${left-6}" y="${y+4}" text-anchor="end" class="axis">${money?(v/1000000).toFixed(1)+'m':Math.round(v)}</text>`)}
 months.forEach((m,i)=>{const x=left+(months.length===1?0:i*plotW/(months.length-1));a.push(`<text x="${x}" y="${H-12}" text-anchor="middle" class="axis">${m.slice(5)}</text>`)});
 series.forEach((s,k)=>{const pts=s.values.map((v,i)=>`${left+(months.length===1?0:i*plotW/(months.length-1))},${top+plotH-v/ymax*plotH}`).join(' ');a.push(`<polyline points="${pts}" fill="none" stroke="${s.color}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>`)});
 a.push(`<text x="${W-8}" y="${H-26}" text-anchor="end" class="axis">Apr–Sep 2026</text>`);el.setAttribute('viewBox',`0 0 ${W} ${H}`);el.innerHTML=a.join('');}
function bars(id,dict,{money=false}={}){const vals=Object.entries(dict).sort((a,b)=>b[1]-a[1]);const mx=Math.max(1,...vals.map(x=>x[1]));
 $(id).innerHTML=vals.map(([name,n])=>`<div class="rule-row"><div title="${esc(name)}">${esc(name.replaceAll('_',' '))}</div><div class="bartrack"><div class="bar" style="width:${(n/mx*100).toFixed(2)}%"></div></div><div class="n">${money?fmtUsd.format(n).replace('.00',''):fmtInt.format(n)}</div></div>`).join('')||'<p>No records</p>'}
function render(){const rows=getFiltered(), ids=new Set(rows.map(t=>t.transaction_id)),cids=new Set(rows.map(t=>t.customer_id));
 const flagged=new Set(MODEL.hits.filter(([id])=>ids.has(id)).map(([id])=>id));const hits=MODEL.hits.filter(([id])=>ids.has(id));
 const monthFilter=$('month').value,review=MODEL.monthFlags.filter(([cid,m])=>cids.has(cid)&&(monthFilter==='ALL'||monthFilter===m)&&($('segment').value==='ALL'||byCustomer[cid].segment===$('segment').value)&&($('risk').value==='ALL'||byCustomer[cid].risk_tier===$('risk').value));
 let gross=0,inflow=0,outflow=0;const mm={};months.forEach(m=>mm[m]={inflow:0,outflow:0,flagged:new Set()});const chan={};const customerMonths={};
 for(const t of rows){const value=Number(t.amount_usd),m=t.booked_at.slice(0,7);gross+=value;if(t.direction==='IN'){inflow+=value;mm[m].inflow+=value}else{outflow+=value;mm[m].outflow+=value}chan[t.channel]=(chan[t.channel]||0)+value;
 const key=t.customer_id+'|'+m;(customerMonths[key]??={customer:t.customer_id,month:m,inflow:0,outflow:0,gross:0}).gross+=value;const cr=customerMonths[key];cr[t.direction==='IN'?'inflow':'outflow']+=value;if(flagged.has(t.transaction_id))mm[m].flagged.add(t.transaction_id);}
 const k=[['Validated transactions',fmtInt.format(rows.length),'one clean transaction per ID'],['Gross transaction volume',fmtUsd.format(gross),'absolute IN + OUT magnitude'],['Flagged transactions',fmtInt.format(flagged.size),'distinct IDs (not hit rows)'],['Flagged transaction rate',fmtPct(rows.length?flagged.size/rows.length:0),'flagged / valid transactions'],['Customer-month flags',fmtInt.format(review.length),'separate review grain']];
 $('kpis').innerHTML=k.map(([l,n,s])=>`<div class="kpi"><div class="lbl">${esc(l)}</div><div class="val">${esc(n)}</div><div class="sub">${esc(s)}</div></div>`).join('');
 svgLine('flows',[{values:months.map(m=>mm[m].inflow),color:'#176aa6'},{values:months.map(m=>mm[m].outflow),color:'#ed853f'}],{money:true});
 svgLine('alerts',[{values:months.map(m=>mm[m].flagged.size),color:'#0e7d78'}]);
 const byRule={};hits.forEach(([tid,rule])=>byRule[rule]=(byRule[rule]||0)+1);bars('rules',byRule);
 bars('channels',chan,{money:true});
 $('review').innerHTML=review.slice(0,50).map(([cid,m,rule])=>{const r=customerMonths[cid+'|'+m];return `<tr><td>${esc(cid)}</td><td>${esc(m)}</td><td><span class="tag">${esc(rule)}</span></td><td>${esc(byCustomer[cid].segment)}</td><td>${esc(byCustomer[cid].risk_tier)}</td><td class="num">${fmtUsd.format(r?.gross??0)}</td></tr>`}).join('')||'<tr><td colspan="6">No customer-month review indicators in this filter.</td></tr>';
 $('details').innerHTML=[...rows].sort((a,b)=>b.booked_at.localeCompare(a.booked_at)||b.transaction_id.localeCompare(a.transaction_id)).slice(0,18).map(t=>`<tr><td>${esc(t.booked_at)}</td><td>${esc(t.transaction_id)}</td><td>${esc(t.customer_id)}</td><td>${esc(t.direction)}</td><td>${esc(t.channel)}</td><td class="num">${fmtUsd.format(Number(t.amount_usd))}</td><td>${esc((byHit[t.transaction_id]||[]).join(', ')||'—')}</td></tr>`).join('')||'<tr><td colspan="7">No payments in selected filter.</td></tr>';
}
['month','segment','risk'].forEach(id=>$(id).addEventListener('change',render));$('reset').addEventListener('click',()=>{['month','segment','risk'].forEach(id=>$(id).value='ALL');render()});render();
</script></body></html>'''
output=ROOT/'dashboard/index.html'
output.write_text(html.replace('__DATA__',script),encoding='utf-8')
print('wrote',output.stat().st_size,'bytes of portable dashboard')
