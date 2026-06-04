#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
印和闐 台股藏金閣
雙擊執行 → 自動抓取最新股價+成交量 → 在瀏覽器開啟彩色儀表板
"""

import webbrowser, os, sys
from datetime import datetime

# GitHub Actions 環境自動偵測
CI_MODE = os.environ.get("CI") == "true"

# ── 股票資料 ─────────────────────────────────────────────────────────────────
# holding: True=目前持有(一軍), False=觀察名單(二軍)
# cost: 成本價（二軍不持有請留 None）
STOCKS = [
    # ─ 一軍（目前持有）─
    {"code":"5534","name":"長虹",   "group":"一軍","role":"🏠 資產金庫","ex":"tse","holding":True,
     "sweet":(68.0,70.5),"entry":(71.0,73.5),"target":(88.0,95.0),"cost":78.44,
     "memo":"2026 ICT大樓+虹創科技大樓完工，預估淨值衝破 100"},
    {"code":"4533","name":"協易機", "group":"一軍","role":"🦾 重裝主力","ex":"otc","holding":True,
     "sweet":(28.5,30.0),"entry":(30.5,32.0),"target":(38.0,42.0),"cost":27.0,
     "memo":"伺服沖床主力，跌破 30 用力撿"},
    {"code":"3455","name":"由田",   "group":"一軍","role":"🦾 武曲主攻","ex":"otc","holding":True,
     "sweet":(215.0,225.0),"entry":(228.0,240.0),"target":(290.0,310.0),"cost":265.87,
     "memo":"AOI 檢測設備，TSMC 自主產線指定廠商"},
    {"code":"3587","name":"閎康",   "group":"一軍","role":"🔬 武曲驗證師","ex":"otc","holding":True,
     "sweet":(295.0,308.0),"entry":(312.0,326.0),"target":(390.0,420.0),"cost":340.0,
     "memo":"AI ASIC 可靠度分析，2026 EPS 估 11-13，日本第四實驗室 Q3 開幕"},
    {"code":"6438","name":"迅得",   "group":"一軍","role":"⚡ 變動殺手","ex":"tse","holding":True,
     "sweet":(160.0,167.0),"entry":(168.0,174.0),"target":(208.0,222.0),"cost":178.15,
     "memo":"FOUP Stocker 家登默契夥伴，半導體設備佔比拉至 50%，EPS 估 9-10"},

    {"code":"3580","name":"友威科",  "group":"一軍","role":"🌙 太陰財庫","ex":"otc","holding":True,
     "sweet":(90.0,97.0),"entry":(98.0,103.0),"target":(120.0,130.0),"cost":111.5,
     "memo":"電漿/濺鍍輔助設備，玻璃基板 E-core 2026 H2 受惠，低風險穩健"},

    # ─ 二軍（觀察名單，目前未持有）─
    {"code":"6196","name":"帆宣",   "group":"二軍","role":"🛡️ 太陰防禦","ex":"tse","holding":False,
     "sweet":(460.0,480.0),"entry":(485.0,508.0),"target":(600.0,640.0),"cost":None,
     "memo":"在手訂單 910 億排至 2027，化學品供應 + AIM Bonder，EPS 估 18-20"},
    {"code":"2467","name":"志聖",   "group":"二軍","role":"🦾 武曲備案","ex":"tse","holding":False,
     "sweet":(555.0,580.0),"entry":(585.0,612.0),"target":(730.0,780.0),"cost":None,
     "memo":"TSMC-like 產線 Bonder/除泡烘烤設備，CoWoS 擴產直接受惠"},
    {"code":"5425","name":"台半",   "group":"二軍","role":"裝甲護衛","ex":"otc","holding":False,
     "sweet":(103.0,109.0),"entry":(110.0,115.5),"target":(138.0,148.0),"cost":None,
     "memo":"離散功率元件，車用工控復甦，拉回月線接"},
    {"code":"3693","name":"營邦",   "group":"二軍","role":"重裝主力(核心)","ex":"otc","holding":False,
     "sweet":(510.0,538.0),"entry":(542.0,575.0),"target":(690.0,730.0),"cost":None,
     "memo":"NVIDIA 指定 AI 儲存機櫃，EPS 挑戰 25-30"},
    {"code":"1560","name":"中砂",   "group":"二軍","role":"🌀 陀羅備案","ex":"tse","holding":False,
     "sweet":(645.0,672.0),"entry":(675.0,710.0),"target":(855.0,900.0),"cost":None,
     "memo":"Intel 18A 鑽石碟供貨比重 30%，隨 Intel 18A 爬坡大漲"},
    {"code":"3357","name":"臺慶科", "group":"二軍","role":"🌀 陀羅觀察","ex":"otc","holding":False,
     "sweet":(258.0,270.0),"entry":(273.0,284.0),"target":(343.0,368.0),"cost":None,
     "memo":"TLVR 電感通過認證，2026H2 開始出貨，EPS 估 13.5，營收美國佔 73%"},
    {"code":"2421","name":"建準",   "group":"二軍","role":"🌀 陀羅風神","ex":"tse","holding":False,
     "sweet":(143.0,150.0),"entry":(152.0,158.0),"target":(188.0,200.0),"cost":None,
     "memo":"AI 伺服器散熱風扇，電子備案，磨完會飛"},
    {"code":"2062","name":"橋椿",   "group":"二軍","role":"🛡️🌀 防禦金盾","ex":"tse","holding":False,
     "sweet":(16.8,17.8),"entry":(17.9,18.7),"target":(22.0,23.5),"cost":None,
     "memo":"鋅壓鑄水龍頭，避風港型，賺 15% 就很棒"},
    {"code":"3004","name":"豐達科", "group":"二軍","role":"👑🌀 本命核心","ex":"tse","holding":False,
     "sweet":(110.0,116.0),"entry":(117.0,123.0),"target":(148.0,158.0),"cost":None,
     "memo":"航太螺絲，SPS Technologies 火災轉單，Boeing 爬坡，EPS 估 9.5"},
    {"code":"5222","name":"全訊",   "group":"二軍","role":"⚔️ 七殺戰神","ex":"tse","holding":False,
     "sweet":(114.0,119.0),"entry":(120.0,126.0),"target":(150.0,160.0),"cost":None,
     "memo":"軍工 PA，國防部唯一供應商，逢低補"},
    {"code":"3131","name":"弘塑",   "group":"二軍","role":"⚡ 七殺先鋒","ex":"otc","holding":False,
     "sweet":(3050,3200),"entry":(3230,3420),"target":(4200,4600),"cost":None,
     "memo":"高階濕製程設備霸主，CoWoS/TSMC-like 產線核心，七殺爆發"},
    {"code":"8027","name":"鈦昇",   "group":"二軍","role":"⚡ 破軍黑馬","ex":"otc","holding":False,
     "sweet":(228.0,242.0),"entry":(245.0,257.0),"target":(315.0,345.0),"cost":None,
     "memo":"Intel EMIB 獨家雷射設備，2026 出貨拉曼光譜儀用於 Intel 14A 背面供電"},
    {"code":"4958","name":"臻鼎-KY","group":"二軍","role":"⚡ 破軍觀察","ex":"tse","holding":False,
     "sweet":(460.0,480.0),"entry":(485.0,512.0),"target":(618.0,658.0),"cost":None,
     "memo":"SLP 類載板龍頭，CoWoP 送樣測試，NVIDIA VR200 運算主板"},
    {"code":"6937","name":"天虹",   "group":"二軍","role":"⚡ 破軍主攻","ex":"tse","holding":False,
     "sweet":(270.0,284.0),"entry":(287.0,300.0),"target":(362.0,385.0),"cost":None,
     "memo":"PVD/ALD 設備國產化，打破美商壟斷，台積電供應鏈新星"},
    {"code":"8096","name":"擎亞",   "group":"二軍","role":"⚡ 突擊尖兵","ex":"otc","holding":False,
     "sweet":(108.0,114.0),"entry":(116.0,122.0),"target":(148.0,160.0),"cost":None,
     "memo":"記憶體與 AI 通路，台積電資料中心受惠，嚴禁追高"},
]

# ── 抓取股價 ──────────────────────────────────────────────────────────────────
def fetch_prices():
    try:
        import yfinance as yf
    except ImportError:
        print("正在安裝 yfinance...")
        import subprocess, sys
        subprocess.check_call([sys.executable, "-m", "pip", "install", "yfinance", "-q"])
        import yfinance as yf

    prices, volumes = {}, {}
    for s in STOCKS:
        code = s["code"]
        for suffix in ([".TW", ".TWO"] if s["ex"] == "tse" else [".TWO", ".TW"]):
            try:
                ticker = yf.Ticker(f"{code}{suffix}")
                hist = ticker.history(period="2d")
                if not hist.empty:
                    prices[code]  = round(float(hist["Close"].iloc[-1]), 2)
                    vol = int(hist["Volume"].iloc[-1])
                    # Yahoo Finance Volume for TW stocks = 股（shares），換算成張（1張=1000股）
                    volumes[code] = vol // 1000
                    break
            except Exception:
                continue
    return prices, volumes

# ── 判斷價位區間 ──────────────────────────────────────────────────────────────
def get_zone(price, sweet, entry, target, holding=True):
    sl, sh = sweet
    el, eh = entry
    tl, th = target
    if price < sl:
        return "below_sweet"
    elif sl <= price <= sh:
        return "sweet"
    elif el <= price <= eh:
        return "entry"
    elif eh < price < tl:
        return "normal_hold" if holding else "normal_watch"
    elif tl <= price <= th:
        return "target"
    else:
        return "above_target"

ZONE_LABELS = {
    "below_sweet":  ("🔥 超甜！",   "#dc2626", "#fff"),
    "sweet":        ("🍬 甜甜區",   "#16a34a", "#fff"),
    "entry":        ("✅ 推薦入手", "#2563eb", "#fff"),
    "normal_hold":  ("📊 持有中",   "#475569", "#fff"),  # 一軍專用
    "normal_watch": ("👁 觀察中",   "#374151", "#e5e7eb"),  # 二軍專用
    "target":       ("🎯 接近滿足", "#d97706", "#fff"),
    "above_target": ("⚠️ 超過目標", "#b91c1c", "#fff"),
}

# ── 計算損益 ──────────────────────────────────────────────────────────────────
def pnl_pct(price, cost):
    if not cost or cost == 0:
        return None
    return (price - cost) / cost * 100

# ── 格式化成交量 ──────────────────────────────────────────────────────────────
def fmt_vol(v):
    if v is None: return "—"
    if v >= 10000: return f"{v/10000:.1f}萬張"
    return f"{v:,}張"

# ── 產生 HTML ─────────────────────────────────────────────────────────────────
def generate_html(prices, volumes):
    now = datetime.now().strftime("%Y/%m/%d %H:%M")
    h = datetime.now().hour
    market_open = "市場交易中 🟢" if 9 <= h < 14 else "收盤後資料 ⚫"

    rows = ""
    current_group = ""
    for s in STOCKS:
        code     = s["code"]
        holding  = s["holding"]
        price    = prices.get(code)
        vol      = volumes.get(code)

        # 群組分隔標題
        if s["group"] != current_group:
            current_group = s["group"]
            g_label = "一軍　持有中" if current_group == "一軍" else "二軍　觀察名單"
            rows += f"""
            <tr>
              <td colspan="11" style="background:#1e293b;color:#94a3b8;
                  font-weight:700;font-size:12px;letter-spacing:3px;
                  padding:10px 18px;border-top:2px solid #334155;text-align:left;">
                ── {g_label} ──
              </td>
            </tr>"""

        # 無法取得價格
        if price is None:
            rows += f"""<tr>
              <td>{code}</td><td>{s['name']}</td>
              <td colspan="8" style="color:#6b7280;font-style:italic;">無法取得價格</td>
              <td>—</td></tr>"""
            continue

        zone = get_zone(price, s["sweet"], s["entry"], s["target"], holding)
        label, bg, fg = ZONE_LABELS[zone]

        # 成本 / 損益 — 只有一軍顯示
        if holding and s["cost"]:
            pnl = pnl_pct(price, s["cost"])
            cost_str = f"{s['cost']:,.2f}"
            pnl_str  = (f"+{pnl:.1f}%" if pnl >= 0 else f"{pnl:.1f}%")
            pnl_col  = "#22c55e" if pnl >= 0 else "#f87171"
        else:
            cost_str = "—"
            pnl_str  = "—"
            pnl_col  = "#475569"

        rows += f"""
        <tr>
          <td style="font-weight:600;color:#94a3b8;">{code}</td>
          <td style="font-weight:700;white-space:nowrap;">{s['name']}</td>
          <td style="font-size:11px;color:#94a3b8;white-space:nowrap;">{s['role']}</td>
          <td style="font-weight:800;font-size:15px;color:#f1f5f9;">{price:,.1f}</td>
          <td style="color:#64748b;font-size:12px;">{cost_str}</td>
          <td style="font-weight:700;color:{pnl_col};font-size:12px;">{pnl_str}</td>
          <td style="color:#86efac;font-size:12px;">{s['sweet'][0]:,.0f}－{s['sweet'][1]:,.0f}</td>
          <td style="color:#93c5fd;font-size:12px;">{s['entry'][0]:,.0f}－{s['entry'][1]:,.0f}</td>
          <td style="color:#fcd34d;font-size:12px;">{s['target'][0]:,.0f}－{s['target'][1]:,.0f}</td>
          <td style="color:#94a3b8;font-size:11px;">{fmt_vol(vol)}</td>
          <td>
            <span style="background:{bg};color:{fg};border-radius:5px;
                padding:3px 9px;font-size:11px;font-weight:700;white-space:nowrap;">
              {label}
            </span>
          </td>
        </tr>"""

    # 甜甜區警報
    sweet_stocks = [s["name"] for s in STOCKS
                    if prices.get(s["code"]) and
                    get_zone(prices[s["code"]], s["sweet"], s["entry"], s["target"], s["holding"])
                    in ("below_sweet", "sweet")]
    alert_html = ""
    if sweet_stocks:
        alert_html = f"""
        <div style="background:#14532d;border:1px solid #16a34a;border-radius:10px;
             padding:12px 20px;margin-bottom:18px;font-size:14px;">
          🍬 <strong style="color:#4ade80;">甜甜區警報！</strong>
          　 <span style="color:#bbf7d0;">{" ／ ".join(sweet_stocks)}</span>
        </div>"""

    # 統計
    n1 = sum(1 for s in STOCKS if s["holding"])
    n2 = len(STOCKS) - n1

    html = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>印和闐 台股藏金閣</title>
<style>
  * {{ box-sizing:border-box; margin:0; padding:0; }}
  body {{ background:#0a0f1e; color:#e2e8f0;
          font-family:'Microsoft JhengHei','Segoe UI',Arial,sans-serif;
          font-size:13px; padding:24px; }}
  .header {{ display:flex; align-items:baseline; gap:16px; margin-bottom:6px; }}
  h1 {{ font-size:22px; color:#fbbf24; letter-spacing:2px; font-weight:800; }}
  .badge {{ background:#1e3a5f; color:#7dd3fc; border-radius:6px;
            padding:2px 10px; font-size:11px; font-weight:600; }}
  .subtitle {{ color:#475569; font-size:12px; margin-bottom:20px; }}
  table {{ width:100%; border-collapse:collapse; }}
  th {{ background:#0f172a; color:#64748b; text-align:center; padding:9px 6px;
        font-size:11px; letter-spacing:0.3px; border-bottom:2px solid #1e293b;
        white-space:nowrap; }}
  td {{ padding:8px 6px; border-bottom:1px solid #0f172a; text-align:center;
        vertical-align:middle; }}
  tr:hover td {{ background:#1e293b55; }}
  .legend {{ display:flex; gap:10px; flex-wrap:wrap; margin-top:18px; }}
  .leg {{ border-radius:5px; padding:3px 9px; font-size:11px; font-weight:700; }}
  .footer {{ color:#1e293b; font-size:11px; margin-top:12px; }}
</style>
</head>
<body>
<div class="header">
  <h1>印和闐 台股藏金閣</h1>
  <span class="badge">一軍 {n1} 檔持有</span>
  <span class="badge">二軍 {n2} 檔觀察</span>
</div>
<div class="subtitle">更新時間：{now}　{market_open}　資料來源：Yahoo Finance（約 15 分鐘延遲）</div>
{alert_html}
<table>
  <thead>
    <tr>
      <th>代號</th><th>名稱</th><th>角色</th>
      <th>現價</th><th>成本</th><th>損益%</th>
      <th>🍬 甜甜價</th><th>✅ 推薦入手</th><th>🎯 滿足點</th>
      <th>成交量</th><th>狀態</th>
    </tr>
  </thead>
  <tbody>
    {rows}
  </tbody>
</table>
<div class="legend">
  <span class="leg" style="background:#dc2626;color:#fff">🔥 超甜！低於甜甜價</span>
  <span class="leg" style="background:#16a34a;color:#fff">🍬 甜甜區（用力接）</span>
  <span class="leg" style="background:#2563eb;color:#fff">✅ 推薦入手區</span>
  <span class="leg" style="background:#475569;color:#fff">📊 持有中（一軍）</span>
  <span class="leg" style="background:#374151;color:#e5e7eb">👁 觀察中（二軍）</span>
  <span class="leg" style="background:#d97706;color:#fff">🎯 接近滿足點</span>
  <span class="leg" style="background:#b91c1c;color:#fff">⚠️ 超過目標，考慮了結</span>
</div>
<p class="footer">價格僅供參考，投資決策請自行判斷。成交量為前一交易日資料。</p>
</body>
</html>"""
    return html

# ── 主程式 ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")

    # CI 模式：輸出 index.html（供 GitHub Pages），不開瀏覽器
    # 本機模式：輸出 股價儀表板.html，自動開瀏覽器
    if CI_MODE:
        out_filename = "index.html"
    else:
        out_filename = "股價儀表板.html"

    # 支援命令列指定輸出檔名 python 每日追價.py --output index.html
    if "--output" in sys.argv:
        idx = sys.argv.index("--output")
        if idx + 1 < len(sys.argv):
            out_filename = sys.argv[idx + 1]

    print("正在抓取最新股價與成交量...")
    prices, volumes = fetch_prices()

    fetched = len([s for s in STOCKS if prices.get(s["code"])])
    print(f"取得 {fetched}/{len(STOCKS)} 檔股價")

    html = generate_html(prices, volumes)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    out_path = os.path.join(base_dir, out_filename)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"已輸出：{out_path}")

    if not CI_MODE:
        webbrowser.open(f"file:///{out_path.replace(os.sep, '/')}")
