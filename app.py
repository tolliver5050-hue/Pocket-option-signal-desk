import os, io, csv, math
from flask import Flask, request, jsonify, render_template_string
app = Flask(__name__)

PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>OTC Signal Desk</title>
<style>
:root{color-scheme:dark;--bg:#0b1020;--panel:#141c31;--line:#273451;--muted:#9aa8c4;--green:#39d98a;--red:#ff667d;--gold:#f5c66b}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(ellipse at top,#172447,#0b1020 58%);font:15px system-ui,-apple-system,Segoe UI,sans-serif;color:#f3f6ff}
header{padding:22px 18px 14px;border-bottom:1px solid var(--line);display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap}
.brand{font-size:20px;font-weight:800;letter-spacing:.04em}.brand span{color:#9eabff}.sub{color:var(--muted);font-size:12px;margin-top:4px}
.pill{border:1px solid #6e5a2a;color:var(--gold);padding:7px 10px;border-radius:20px;font-size:12px}
main{max-width:1000px;margin:auto;padding:18px;display:grid;gap:15px}.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}
.card{background:linear-gradient(145deg,#18223b,#11182a);border:1px solid var(--line);border-radius:16px;padding:16px;min-width:0}
.label{font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:.08em}.value{font-size:23px;font-weight:750;margin-top:8px}.muted{color:var(--muted);font-size:13px;line-height:1.5}
.signal{display:flex;align-items:center;justify-content:space-between;gap:12px}.signalword{font-size:34px;font-weight:900;letter-spacing:.04em}.wait{color:var(--gold)}.call{color:var(--green)}.put{color:var(--red)}
button,.filebtn{background:#7c8cff;color:#081024;border:0;border-radius:10px;padding:11px 14px;font-weight:750;cursor:pointer;display:inline-block}
button.secondary{background:#263451;color:#eaf0ff;border:1px solid #344465}input,select{background:#0b1224;border:1px solid #334260;color:#fff;padding:11px;border-radius:9px;width:100%;margin-top:6px}
label{display:block;color:#c4cde2;font-size:13px;margin-top:12px}.row{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.actions{display:flex;gap:9px;flex-wrap:wrap;margin-top:14px}.notice{border-left:3px solid var(--gold);padding:10px 12px;background:#211f1b;border-radius:7px;color:#e7d7af;font-size:13px;line-height:1.5}
table{width:100%;border-collapse:collapse;font-size:13px;margin-top:10px}td,th{text-align:left;padding:9px 6px;border-bottom:1px solid var(--line)}th{color:var(--muted);font-weight:600}
footer{text-align:center;color:var(--muted);font-size:12px;padding:0 18px 24px}
@media(max-width:650px){.grid{grid-template-columns:1fr}.row{grid-template-columns:1fr}.value{font-size:21px}main{padding:12px}header{padding:18px 14px}}
</style></head><body>
<header><div><div class="brand">◈ OTC <span>SIGNAL DESK</span></div><div class="sub">Pocket Option companion · signals only · 1-minute expiry</div></div><div class="pill">● AUTO-TRADING DISABLED</div></header>
<main>
<div class="notice"><b>Data status: MANUAL / DEMO</b><br>This dashboard does not claim live OTC prices. To scan all OTC markets automatically, a compatible market-data API must be connected on the server. Never put an API key in this webpage.</div>
<div class="grid">
<div class="card"><div class="label">Signal</div><div id="signal" class="signalword wait">WAIT</div><div id="reason" class="muted">Upload OHLC candles to analyze.</div></div>
<div class="card"><div class="label">ADX (14)</div><div id="adx" class="value">—</div><div class="muted">Trend-strength filter: strictly above 27</div></div>
<div class="card"><div class="label">DI / Vortex</div><div id="cross" class="value">—</div><div class="muted">Requires confirmed cross on latest closed candle</div></div>
</div>
<div class="card"><h3 style="margin:0 0 6px">Analyze candle data</h3><div class="muted">Upload a CSV with columns: <b>time, open, high, low, close</b>. Use at least 40 closed 1-minute candles for a more meaningful calculation. This runs on the server; no trading is placed.</div>
<form id="form">
<label>OTC market label (for your reference)<input id="market" value="GBP/USD (OTC)" required></label>
<label>OHLC CSV file<input id="csv" type="file" accept=".csv,text/csv" required></label>
<div class="actions"><button type="submit">Analyze candles</button><button class="secondary" type="button" id="demo">Load sample data</button><button class="secondary" type="button" id="reset">Reset</button></div>
</form><div id="status" class="muted" style="margin-top:12px"></div>
</div>
<div class="card"><h3 style="margin:0">Signal rules</h3><table><tr><th>Filter</th><th>Rule</th></tr><tr><td>ADX</td><td>ADX(14) &gt; 27</td></tr><tr><td>CALL</td><td>+DI crosses above −DI AND VI+ crosses above VI− on latest closed candle</td></tr><tr><td>PUT</td><td>−DI crosses above +DI AND VI− crosses above VI+ on latest closed candle</td></tr><tr><td>Otherwise</td><td>WAIT — no qualifying signal</td></tr></table><p class="muted">A signal is a rule-based reading, not a guarantee of the next candle’s direction. Confirm candle timestamps and market source before use.</p></div>
</main><footer>For analysis and paper testing only. No automatic trading or broker connection.</footer>
<script>
const form=document.getElementById('form'), statusEl=document.getElementById('status');
function show(d){
 const s=document.getElementById('signal');s.textContent=d.signal||'WAIT';s.className='signalword '+(d.signal==='CALL'?'call':d.signal==='PUT'?'put':'wait');
 document.getElementById('reason').textContent=d.reason||'No signal';
 document.getElementById('adx').textContent=d.adx==null?'—':Number(d.adx).toFixed(2);
 document.getElementById('cross').textContent=d.cross_status||'—';
 statusEl.textContent=d.status||'Analysis complete.';
}
form.addEventListener('submit',async e=>{e.preventDefault();const f=document.getElementById('csv').files[0];if(!f)return;const fd=new FormData();fd.append('file',f);fd.append('market',document.getElementById('market').value);statusEl.textContent='Analyzing uploaded candles…';try{const r=await fetch('/analyze',{method:'POST',body:fd});const d=await r.json();if(!r.ok)throw new Error(d.error||'Could not analyze file');show(d)}catch(err){statusEl.textContent=err.message}});
document.getElementById('demo').onclick=async()=>{statusEl.textContent='Loading sample data…';try{const r=await fetch('/demo',{method:'POST'});show(await r.json())}catch(e){statusEl.textContent='Could not load sample.'}};
document.getElementById('reset').onclick=()=>{show({signal:'WAIT',reason:'Upload OHLC candles to analyze.',status:'Reset complete.'});document.getElementById('adx').textContent='—';document.getElementById('cross').textContent='—';form.reset();document.getElementById('market').value='GBP/USD (OTC)'};
</script></body></html>"""

def calc_signal(rows):
    if len(rows) < 35:
        raise ValueError("Please upload at least 35 candles; 40+ is recommended.")
    h=[r["high"] for r in rows]; l=[r["low"] for r in rows]; c=[r["close"] for r in rows]
    n=len(rows); tr=[None]*n; pdm=[0.0]*n; mdm=[0.0]*n
    for i in range(1,n):
        tr[i]=max(h[i]-l[i],abs(h[i]-c[i-1]),abs(l[i]-c[i-1]))
        up=h[i]-h[i-1]; down=l[i-1]-l[i]
        pdm[i]=up if up>down and up>0 else 0.0
        mdm[i]=down if down>up and down>0 else 0.0
    def wilder(vals, period):
        out=[None]*len(vals)
        if len(vals)<=period: return out
        seed=sum(vals[1:period+1])
        out[period]=seed
        for i in range(period+1,len(vals)): out[i]=out[i-1]-(out[i-1]/period)+vals[i]
        return out
    tr14=wilder([0 if x is None else x for x in tr],14)
    p14=wilder(pdm,14); m14=wilder(mdm,14)
    pdi=[None]*n; mdi=[None]*n; dx=[None]*n
    for i in range(n):
        if tr14[i] and tr14[i]>0 and p14[i] is not None:
            pdi[i]=100*p14[i]/tr14[i]; mdi[i]=100*m14[i]/tr14[i]
            den=pdi[i]+mdi[i]; dx[i]=100*abs(pdi[i]-mdi[i])/den if den else 0
    adx=[None]*n
    valid=[i for i,x in enumerate(dx) if x is not None]
    if len(valid)>=15:
        first=valid[14]; adx[first]=sum(dx[i] for i in valid[:14])/14
        for i in range(first+1,n):
            if dx[i] is not None: adx[i]=(adx[i-1]*13+dx[i])/14 if adx[i-1] is not None else None
    vip=[None]*n; vim=[None]*n
    # Vortex(14): sum |high - previous low| / sum true range, and inverse
    for i in range(14,n):
        denom=sum(tr[j] or 0 for j in range(i-13,i+1))
        if denom:
            vip[i]=sum(abs(h[j]-l[j-1]) for j in range(i-13,i+1))/denom
            vim[i]=sum(abs(l[j]-h[j-1]) for j in range(i-13,i+1))/denom
    i=n-1; prev=i-1
    if any(x is None for x in (adx[i],pdi[i],mdi[i],pdi[prev],mdi[prev],vip[i],vim[i],vip[prev],vim[prev])):
        return {"signal":"WAIT","reason":"Indicator warm-up incomplete; upload more candles.","adx":adx[i],"cross_status":"Not ready"}
    di_call=pdi[prev] <= mdi[prev] and pdi[i] > mdi[i]
    di_put=mdi[prev] <= pdi[prev] and mdi[i] > pdi[i]
    vi_call=vip[prev] <= vim[prev] and vip[i] > vim[i]
    vi_put=vim[prev] <= vip[prev] and vim[i] > vip[i]
    if adx[i] > 27 and di_call and vi_call: sig="CALL"; reason="ADX > 27; +DI and VI+ crossed above their opposing lines on the latest candle."
    elif adx[i] > 27 and di_put and vi_put: sig="PUT"; reason="ADX > 27; −DI and VI− crossed above their opposing lines on the latest candle."
    else:
        sig="WAIT"
        reason="No complete qualifying crossover on the latest candle, or ADX is not strictly above 27."
    return {"signal":sig,"reason":reason,"adx":adx[i],"cross_status":("DI + Vortex bullish cross" if di_call and vi_call else "DI + Vortex bearish cross" if di_put and vi_put else "No simultaneous cross"),"status":f"Analyzed {n} candles. Last row is treated as the latest closed candle."}

def parse_csv(stream):
    text=stream.read().decode("utf-8-sig")
    reader=csv.DictReader(io.StringIO(text))
    if not reader.fieldnames: raise ValueError("CSV is empty or missing a header row.")
    names={x.strip().lower():x for x in reader.fieldnames}
    required=["open","high","low","close"]
    if not all(k in names for k in required):
        raise ValueError("CSV needs column headers: open, high, low, close (time is optional).")
    rows=[]
    for row in reader:
        try:
            item={k:float(row[names[k]]) for k in required}
            if not all(math.isfinite(v) for v in item.values()): continue
            if item["high"] < max(item["open"],item["close"],item["low"]) or item["low"] > min(item["open"],item["close"],item["high"]):
                continue
            rows.append(item)
        except (ValueError,TypeError): continue
    return rows

@app.get("/")
def home(): return render_template_string(PAGE)

@app.post("/analyze")
def analyze():
    try:
        if "file" not in request.files: raise ValueError("Choose a CSV file first.")
        rows=parse_csv(request.files["file"])
        result=calc_signal(rows)
        result["status"]=(request.form.get("market","Market"))+" · "+result["status"]
        return jsonify(result)
    except Exception as e: return jsonify({"error":str(e)}),400

@app.post("/demo")
def demo():
    # Explicitly synthetic sample, only for testing the interface and indicator pipeline.
    rows=[]
    close=1.2500
    for i in range(60):
        change=(0.00018 if i>45 else 0.00002)*math.sin(i*0.7)+(0.00010 if i>48 else -0.00001)
        o=close; close+=change
        rows.append({"open":o,"high":max(o,close)+0.00008,"low":min(o,close)-0.00007,"close":close})
    try:
        r=calc_signal(rows); r["status"]="SYNTHETIC DEMO only — not live OTC data. "+r["status"]; return jsonify(r)
    except Exception as e: return jsonify({"error":str(e)}),400

if __name__ == "__main__":
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT","10000")))
