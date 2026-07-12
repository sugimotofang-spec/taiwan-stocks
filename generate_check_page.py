#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
產生手機版「下單前檢查」網頁 check.html
從 每日追價.py 讀取 STOCKS，嵌入成 JSON，純前端 JS 判斷區間
會被 GitHub Actions 自動推到 gh-pages，網址：
https://sugimotofang-spec.github.io/taiwan-stocks/check.html
"""
import os, sys, re, json, glob

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.abspath(__file__))

def load_stocks():
    src_matches = glob.glob(os.path.join(BASE, "*追價*.py"))
    if not src_matches:
        print("找不到 每日追價.py"); sys.exit(1)
    with open(src_matches[0], encoding="utf-8") as f:
        text = f.read()
    m = re.search(r"^STOCKS = (\[.*?^\])", text, re.S | re.M)
    if not m:
        print("無法解析 STOCKS 清單"); sys.exit(1)
    return eval(m.group(1))

STOCKS = load_stocks()
STOCKS_JSON = json.dumps(STOCKS, ensure_ascii=False)

HTML = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="下單檢查">
<meta name="theme-color" content="#0a0f1e">
<title>下單前檢查 | 印和闐</title>
<style>
  :root {{
    --bg:#0a0f1e; --surface:#111827; --surface2:#1e293b;
    --border:#1e293b; --text:#e2e8f0; --muted:#64748b;
    --gold:#fbbf24; --sky:#7dd3fc;
    --ok:#22c87a; --warn:#f5a020; --danger:#e84545;
  }}
  * {{ box-sizing:border-box; margin:0; padding:0; -webkit-tap-highlight-color:transparent; }}
  html {{ font-size:16px; }}
  body {{
    background:var(--bg); color:var(--text);
    font-family:'PingFang TC','Microsoft JhengHei','Segoe UI',sans-serif;
    min-height:100vh; padding:20px 16px 48px;
    padding-top:calc(20px + env(safe-area-inset-top));
    padding-bottom:calc(48px + env(safe-area-inset-bottom));
  }}
  h1 {{ font-size:1.15rem; color:var(--gold); letter-spacing:1px; font-weight:800; margin-bottom:2px; }}
  .subtitle {{ color:var(--muted); font-size:0.75rem; margin-bottom:20px; }}

  .field {{ margin-bottom:16px; }}
  label {{ display:block; font-size:0.75rem; color:var(--muted); letter-spacing:0.5px; margin-bottom:6px; text-transform:uppercase; }}

  select, input[type="number"] {{
    width:100%; background:var(--surface); border:1px solid var(--border);
    color:var(--text); border-radius:10px; padding:14px 12px;
    font-size:1.05rem; font-family:inherit; -webkit-appearance:none; appearance:none;
  }}
  select:focus, input:focus {{ outline:none; border-color:var(--sky); }}

  .stock-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-bottom:16px; }}
  .stock-btn {{
    background:var(--surface); border:1px solid var(--border); color:var(--text);
    border-radius:10px; padding:12px 10px; font-size:0.9rem; text-align:left;
    font-family:inherit; cursor:pointer;
  }}
  .stock-btn .code {{ color:var(--muted); font-size:0.7rem; display:block; }}
  .stock-btn.selected {{ border-color:var(--gold); background:#20180a; }}
  .group-label {{ font-size:0.7rem; color:var(--muted); letter-spacing:2px; margin:14px 0 8px; }}

  button.check-btn {{
    width:100%; background:var(--gold); color:#1a1200; border:none;
    border-radius:12px; padding:16px; font-size:1.05rem; font-weight:800;
    letter-spacing:1px; margin-top:6px; font-family:inherit;
  }}
  button.check-btn:active {{ opacity:0.8; }}

  .result {{ margin-top:20px; display:none; }}
  .result.show {{ display:block; animation:fade .2s ease; }}
  @keyframes fade {{ from{{opacity:0;transform:translateY(6px)}} to{{opacity:1;transform:translateY(0)}} }}

  .result-card {{
    border-radius:14px; padding:20px 18px; border:1px solid var(--border);
    background:var(--surface);
  }}
  .result-card.ok {{ border-color:var(--ok); background:#0d1f16; }}
  .result-card.warn {{ border-color:var(--warn); background:#221a0a; }}
  .result-card.danger {{ border-color:var(--danger); background:#240f0f; }}

  .zone-title {{ font-size:1.3rem; font-weight:800; margin-bottom:6px; }}
  .zone-msg {{ font-size:0.9rem; color:var(--text); opacity:0.9; line-height:1.5; }}
  .zone-verdict {{ font-size:1rem; font-weight:800; margin-top:12px; padding-top:12px; border-top:1px solid rgba(255,255,255,0.08); }}
  .verdict-ok {{ color:var(--ok); }}
  .verdict-no {{ color:var(--danger); }}

  .range-info {{
    margin-top:14px; font-size:0.78rem; color:var(--muted);
    display:grid; grid-template-columns:1fr 1fr 1fr; gap:6px;
  }}
  .range-info div {{ background:var(--surface2); border-radius:8px; padding:8px 6px; text-align:center; }}
  .range-info b {{ display:block; color:var(--text); font-size:0.82rem; margin-top:2px; }}

  .risk-tag {{
    display:inline-block; margin-top:10px; font-size:0.72rem;
    background:#3a1414; color:#ff8080; padding:4px 10px; border-radius:20px;
  }}

  .footer-link {{
    display:block; text-align:center; margin-top:28px; color:var(--sky);
    font-size:0.8rem; text-decoration:none;
  }}
  .footer-note {{ text-align:center; color:var(--border); font-size:0.7rem; margin-top:6px; }}
</style>
</head>
<body>

<h1>🔒 下單前檢查</h1>
<div class="subtitle">紀律鎖：只有甜甜區和入手區可以買</div>

<div class="field">
  <label>選擇股票</label>
  <div id="stockGrid" class="stock-grid"></div>
</div>

<div class="field">
  <label>想買的價格</label>
  <input type="number" id="priceInput" inputmode="decimal" placeholder="輸入現價" step="0.01">
</div>

<button class="check-btn" onclick="doCheck()">檢查</button>

<div class="result" id="result">
  <div class="result-card" id="resultCard">
    <div class="zone-title" id="zoneTitle"></div>
    <div class="zone-msg" id="zoneMsg"></div>
    <div class="risk-tag" id="riskTag" style="display:none">⚠️ 七殺/地劫屬性，追高代價更大</div>
    <div class="range-info">
      <div>甜甜區<b id="rSweet"></b></div>
      <div>入手區<b id="rEntry"></b></div>
      <div>目標區<b id="rTarget"></b></div>
    </div>
    <div class="zone-verdict" id="zoneVerdict"></div>
  </div>
</div>

<a class="footer-link" href="./index.html">← 回台股藏金閣儀表板</a>
<div class="footer-note">甜甜區才動手</div>

<script>
const STOCKS = {STOCKS_JSON};
let selected = null;

function renderGrid() {{
  const grid = document.getElementById('stockGrid');
  const groups = {{}};
  STOCKS.forEach(s => {{ (groups[s.group] = groups[s.group] || []).push(s); }});
  let html = '';
  Object.keys(groups).forEach(g => {{
    html += `<div class="group-label" style="grid-column:1/-1">${{g}}</div>`;
    groups[g].forEach(s => {{
      html += `<button class="stock-btn" data-code="${{s.code}}" onclick="selectStock('${{s.code}}')">
                 ${{s.name}}<span class="code">${{s.code}}</span>
               </button>`;
    }});
  }});
  grid.innerHTML = html;
}}

function selectStock(code) {{
  selected = STOCKS.find(s => s.code === code);
  document.querySelectorAll('.stock-btn').forEach(b => {{
    b.classList.toggle('selected', b.dataset.code === code);
  }});
  document.getElementById('result').classList.remove('show');
}}

function checkZone(price, s) {{
  const [sl, sh] = s.sweet, [el, eh] = s.entry, [tl, th] = s.target;
  if (price < sl)      return ['🔥 超甜區', `低於甜甜區下限 ${{sl}}，超值價，紀律內可買`, true, 'ok'];
  if (price <= sh)      return ['🍬 甜甜區', `在甜甜區 ${{sl}}–${{sh}} 內，紀律內可買`, true, 'ok'];
  if (price < el)       return ['⬜ 空白地帶', `介於甜甜區上限 ${{sh}} 與入手區下限 ${{el}} 之間，等回落再買`, false, 'warn'];
  if (price <= eh)       return ['🎯 入手區', `在入手區 ${{el}}–${{eh}} 內，可買但不是最優價`, true, 'ok'];
  if (price < tl) {{
    const pct = ((price - eh) / eh * 100).toFixed(1);
    return ['🚫 追高區', `高於入手區上限 ${{eh}} 達 ${{pct}}%，地劫警示：禁止買進`, false, 'danger'];
  }}
  if (price <= th)       return ['🎯 目標區', `已達目標區 ${{tl}}–${{th}}，該想的是賣不是買`, false, 'warn'];
  return ['🚀 超過目標', `已超過目標區上限 ${{th}}，絕對禁止追高`, false, 'danger'];
}}

function doCheck() {{
  if (!selected) {{ alert('請先選擇股票'); return; }}
  const price = parseFloat(document.getElementById('priceInput').value);
  if (isNaN(price)) {{ alert('請輸入價格'); return; }}

  const [zone, msg, ok, level] = checkZone(price, selected);
  const card = document.getElementById('resultCard');
  card.className = 'result-card ' + level;

  document.getElementById('zoneTitle').textContent = `${{selected.name}}　${{zone}}`;
  document.getElementById('zoneMsg').textContent = msg;
  document.getElementById('rSweet').textContent = selected.sweet.join('–');
  document.getElementById('rEntry').textContent = selected.entry.join('–');
  document.getElementById('rTarget').textContent = selected.target.join('–');

  const verdict = document.getElementById('zoneVerdict');
  verdict.textContent = ok ? '✅ 紀律內，可以買' : '🔒 紀律鎖：這個價位不買';
  verdict.className = 'zone-verdict ' + (ok ? 'verdict-ok' : 'verdict-no');

  const risk = document.getElementById('riskTag');
  risk.style.display = (selected.role.includes('七殺') || selected.role.includes('地劫')) ? 'inline-block' : 'none';

  document.getElementById('result').classList.add('show');
  document.getElementById('result').scrollIntoView({{behavior:'smooth', block:'nearest'}});
}}

renderGrid();
</script>
</body>
</html>
"""

out_path = os.path.join(BASE, "check.html")
with open(out_path, "w", encoding="utf-8") as f:
    f.write(HTML)
print(f"✅ 已產生 {out_path}")
print(f"   共 {len(STOCKS)} 檔股票")
