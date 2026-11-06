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
    # ─ 一軍 ─
    {"code":"4533","name":"協易機", "group":"一軍","role":"🦾 重裝主力","ex":"otc","holding":True,
     "sweet":(24.2, 25.9),"entry":(26.1, 28.1),"target":(33.0, 35.6),"cost":27.79,
     "memo":"跌破 30 是假跌破，用力撿"},
    {"code":"3455","name":"由田", "group":"一軍","role":"🦾 武曲主攻 ★AOI取代Onto","ex":"otc","holding":False,
     "sweet":(148.5, 158.5),"entry":(160.0, 172.0),"target":(237.0, 256.0),"cost":None,
     "memo":"【PA 2026九月】台系 AOI 檢測設備商由田、政美應用分別在不同站點取代 Onto，RDL 結構檢測需求隨日月光／矽品前段 CoW 製程能力提升同步放大，訂單能見度至 2027 年底。"},
    {"code":"3587","name":"閎康", "group":"一軍","role":"🔬 武曲驗證師","ex":"otc","holding":True,
     "sweet":(154.5, 165.0),"entry":(166.5, 179.0),"target":(210.5, 227.5),"cost":327.62,
     "memo":"半導體測試驗證服務，隨 CoWoS/先進封裝成長，毛利率穩健。成本 340，逢低可補。"},
    {"code":"2441","name":"超豐", "group":"一軍","role":"🦾 武曲正財封測 ★AI PMIC漲價・持有中","ex":"tse","holding":True,
     "sweet":(85.8, 91.6),"entry":(92.6, 99.4),"target":(117.0, 126.5),"cost":98.67,
     "memo":"【持有・2026/11/05-06 恐慌分批買進 500 股，均價 98.67】"},

    # ─ 白名單額外追蹤 ─
    {"code":"2404","name":"漢唐", "group":"白名單額外追蹤","role":"🛡️ 太陰防禦 ★訂單能見度2029 ★白名單額外追蹤","ex":"tse","holding":False,
     "sweet":(780.0, 833.0),"entry":(842.0, 904.0),"target":(1065.0, 1150.0),"cost":None,
     "memo":"【PA 2026初期報告】台積電2026~2028加速擴產帶動廠務工程龐大商機：無塵室與機電整合為漢唐主力（水循環系統-兆聯、氣體供應-和淞、化學供應-帆宣同列受惠）。在手訂單1,322億創新高，能見度已達2029年，優於帆宣945億(能見度2027)。2026 EPS 法人預估站穩70元以上，2027估上看80~90元。市場開始將其本益比從傳統營造股(10-12倍)向設備股評價靠攏，具評價重估空間。"},
    {"code":"2493","name":"揚博科技", "group":"白名單額外追蹤","role":"🦾 武曲設備擴產 ★新 ★白名單額外追蹤","ex":"tse","holding":False,
     "sweet":(117.0, 125.0),"entry":(126.5, 135.5),"target":(175.5, 189.5),"cost":None,
     "memo":"【PA 2026H2】在手訂單自 300 億上修至 400 億，能見度已達 2028Q2。臻鼎潛在訂單由 80 億上修至 170 億。載板設備廠轉作半導體設備造成產能排擠，載板設備單價有調漲空間。目標 2026 年底產能 1.4~1.6 倍、2027 年底 2.0~2.5 倍。2026 預估 9 元 → 2027 預估 17 元。"},
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
    elif sh < price < el:          # 甜甜區上限～入手下限之間的空白地帶
        return "normal_hold" if holding else "normal_watch"
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
