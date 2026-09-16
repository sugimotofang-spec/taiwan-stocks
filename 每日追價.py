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
     "sweet":(28.5, 30.0),"entry":(30.5, 32.0),"target":(38.0, 42.0),"cost":29.56,
     "memo":"跌破 30 是假跌破，用力撿"},
    {"code":"3455","name":"由田", "group":"一軍","role":"🦾 武曲主攻 ★AOI取代Onto","ex":"otc","holding":False,
     "sweet":(215.0, 225.0),"entry":(228.0, 240.0),"target":(290.0, 310.0),"cost":None,
     "memo":"【PA 2026九月】台系 AOI 檢測設備商由田、政美應用分別在不同站點取代 Onto，RDL 結構檢測需求隨日月光／矽品前段 CoW 製程能力提升同步放大，訂單能見度至 2027 年底。"},
    {"code":"3587","name":"閎康", "group":"一軍","role":"🔬 武曲驗證師","ex":"otc","holding":True,
     "sweet":(295.0, 308.0),"entry":(312.0, 326.0),"target":(390.0, 420.0),"cost":339.53,
     "memo":"半導體測試驗證服務，隨 CoWoS/先進封裝成長，毛利率穩健。成本 340，逢低可補。"},

    # ─ 三軍 ─
    {"code":"3583","name":"辛耘", "group":"三軍","role":"🦾 武曲濕製程主力 ★CoWoS/SoIC","ex":"tse","holding":False,
     "sweet":(626.6, 654.7),"entry":(661.8, 697.0),"target":(844.8, 901.1),"cost":None,
     "memo":"【PA 2026九月】台積電 CoWoS 先進封裝主力設備商（弘塑、辛耘、志聖、均華、萬潤、倍利科）之一，2026/2027/2028 底產能目標 13.0萬/18.5萬/24.0萬片月。SoIC 潛在供應鏈同時納入濕製程設備商角色。"},
    {"code":"6187","name":"萬潤", "group":"三軍","role":"🦾 武曲點膠封裝 ★CoWoS主力","ex":"otc","holding":False,
     "sweet":(1112.0, 1162.0),"entry":(1175.0, 1238.0),"target":(1500.0, 1600.0),"cost":None,
     "memo":"【PA 2026九月】台積電 CoWoS 先進封裝主力設備商之一，隨 CoWoS 產能三年倍增（13.0萬→24.0萬片/月）同步受惠，also切入 GPU/ASIC 大尺寸 reticle 整合趨勢。"},
    {"code":"6640","name":"均華", "group":"三軍","role":"🦾 武曲挑揀設備 ★CoWoS主力","ex":"otc","holding":False,
     "sweet":(1041.0, 1088.0),"entry":(1100.0, 1158.0),"target":(1404.0, 1498.0),"cost":None,
     "memo":"【PA 2026九月】台積電 CoWoS 先進封裝主力設備商之一，隨 CoWoS/SoIC 雙軌放量，晶粒挑揀（Known Good Die）需求同步成長。"},
    {"code":"7853","name":"政美應用", "group":"三軍","role":"🦾 武曲RDL檢測 ★取代Onto","ex":"otc","holding":False,
     "sweet":(280.4, 292.9),"entry":(296.1, 311.9),"target":(378.0, 403.2),"cost":None,
     "memo":"【PA 2026九月】隨日月光、矽品前段 CoW 製程能力提升並擴大建置產能，RDL 結構（線路、焊墊、介電層）檢測需求增加，於成本、交期考量下取代 Onto，訂單能見度至 2027 年底。同步切入日月光 FOPLP 實驗線。"},
    {"code":"6239","name":"力成", "group":"三軍","role":"⚡ 破軍大型封測龍頭 ★FOPLP PiFO","ex":"tse","holding":False,
     "sweet":(243.0, 253.9),"entry":(256.6, 270.3),"target":(327.6, 349.4),"cost":None,
     "memo":"【PA 2026九月】FOPLP 先進封裝主打 PiFO 技術（chip middle製程），已取得 AMD Gaming ASIC、Broadcom TV SoC 訂單，AMD Gaming ASIC 良率已突破 90%，規劃 2027 年產能自 1,000~2,000片/月提升至 6,000~7,000片/月。設備供應鏈含弘塑、志聖、政美應用、由田。"},
    {"code":"6510","name":"精測", "group":"三軍","role":"🌀 陀羅探針卡龍頭 ★CPU/高功率老化","ex":"otc","holding":False,
     "sweet":(3097.0, 3236.0),"entry":(3271.0, 3445.0),"target":(4176.0, 4454.0),"cost":None,
     "memo":"【PA 2026九月】AI晶片功耗自500~600W提升至2,000W以上，公司延伸產品線至 SLT、High Power Burn-in Board。代理式AI帶動CPU需求，ARM-based CPU滲透率提高。自主開發全自動植針設備。Tesla AI5 FSD專案已送樣，2027年可望導入量產；雲端服務商ASIC專案2028~2029導入量產。2026/8底探針產能自40~50萬針/月提升至70~80萬針/月，2027/3再提升至150~160萬針/月，平鎮三廠2028年底完工。"},
    {"code":"6223","name":"旺矽", "group":"三軍","role":"🌀 陀羅ASIC探針卡 ★CPO測試先鋒","ex":"otc","holding":False,
     "sweet":(5002.0, 5227.0),"entry":(5283.0, 5564.0),"target":(6744.0, 7194.0),"cost":None,
     "memo":"【PA 2026九月】積極爭取 Google TPU v9（Humufish）專案訂單，2026Q1 VPC/MEMS探針產能120萬/200萬針月，2026Q4擴至200萬/350萬針月，2027年底湖口新廠一期完工後達250萬/600萬針月。已向4~5家海外IC設計業者送樣CPO Insertion 3測試方案。"},
    {"code":"6515","name":"穎崴", "group":"三軍","role":"🛡️ 太陰測試基座龍頭 ★CPO Insertion3/4","ex":"tse","holding":False,
     "sweet":(6132.0, 6408.0),"entry":(6477.0, 6821.0),"target":(8268.0, 8819.0),"cost":None,
     "memo":"【PA 2026九月】Hyper Socket 增加導電矽膠設計解決晶片翹曲問題，部份高階產品單價較傳統Coaxial Socket高約30%。彈簧針產能2026Q4自350~400萬針/月擴至700~800萬針/月，2027年再擴至1,600~1,700萬針/月。與Technoprobe合作向FT/SLT前延伸至CP測試；同步布局CPO Insertion 3、4測試基座，已有少量出貨驗證。"},
    {"code":"6217","name":"中探針", "group":"三軍","role":"🌀 陀羅探路 ★MEMS探針/CleanSheet","ex":"otc","holding":False,
     "sweet":(146.8, 153.5),"entry":(155.1, 163.3),"target":(198.0, 211.2),"cost":None,
     "memo":"【PA 2026九月】Clean Sheet用於清除Probe上錫渣氧化物，降低接觸電阻誤判風險，預計2027年開始貢獻營收。產品線延伸至CP/FT/Burn-in測試接觸元件與治具。"},
    {"code":"7856","name":"漢測", "group":"三軍","role":"🌀 陀羅利基探路 ★薄膜探針卡・興櫃","ex":"otc","holding":False,
     "sweet":(4641.0, 4850.0),"entry":(4902.0, 5163.0),"target":(6258.0, 6675.0),"cost":None,
     "memo":"【PA 2026九月】薄膜探針卡鎖定高頻高速晶片測試需求，與美系手機品牌網通晶片、美系IC設計業者TIA晶片進行驗證；MEMS探針卡與MJC合作切入國內IC設計業者。CPO測試領域協助歐系廠商代工Insertion 2設備，第一代機型已通過台系晶圓代工廠驗證，洽談Insertion 3設備代工訂單。"},
    {"code":"7899","name":"景美科技", "group":"三軍","role":"🌀 陀羅探路 ★探針卡結構件微孔・興櫃","ex":"otc","holding":False,
     "sweet":(338.2, 353.4),"entry":(357.2, 376.2),"target":(456.0, 486.4),"cost":None,
     "memo":"【PA 2026九月】陶瓷導板隨探針卡探針間距縮小、數量增加，微孔加工難度提升；MEMS探針卡須導入雷射鑽孔，單價、毛利率同步提升。現有23台Cobra機械鑽孔設備(約320~350萬孔/月)，2026Q3台南廠新增50台；2026年購置五軸飛秒雷射設備，MEMS導板雷射鑽孔產能自50萬/月提升至90~100萬/月。"},
    {"code":"7734","name":"印能科技", "group":"三軍","role":"🌀 陀羅探路 ★SoIC熱製程・2026上櫃新兵","ex":"otc","holding":False,
     "sweet":(2296.0, 2399.0),"entry":(2425.0, 2554.0),"target":(3096.0, 3302.0),"cost":None,
     "memo":"【PA 2026九月】為 SoIC 先進封裝銅墊塗佈、烘烤等熱製程潛在供應鏈之一。公司已於 2026/2/26 上櫃掛牌（資本額2.8億），主要業務含半導體除泡、封裝、檢測、自動化、迴焊燒結、貼合設備。掛牌時間短，籌碼與線型資料有限，價位帶僅供參考。"},

    # ─ 白名單額外追蹤 ─
    {"code":"2404","name":"漢唐", "group":"白名單額外追蹤","role":"🛡️ 太陰防禦 ★訂單能見度2029 ★白名單額外追蹤","ex":"tse","holding":False,
     "sweet":(903.4, 944.0),"entry":(954.1, 1005.0),"target":(1218.0, 1299.0),"cost":None,
     "memo":"【PA 2026初期報告】台積電2026~2028加速擴產帶動廠務工程龐大商機：無塵室與機電整合為漢唐主力（水循環系統-兆聯、氣體供應-和淞、化學供應-帆宣同列受惠）。在手訂單1,322億創新高，能見度已達2029年，優於帆宣945億(能見度2027)。2026 EPS 法人預估站穩70元以上，2027估上看80~90元。市場開始將其本益比從傳統營造股(10-12倍)向設備股評價靠攏，具評價重估空間。"},
    {"code":"3580","name":"友威科", "group":"白名單額外追蹤","role":"🛡️ 太陰輔助 ★白名單額外追蹤","ex":"otc","holding":True,
     "sweet":(90.0, 97.0),"entry":(98.0, 103.0),"target":(120.0, 130.0),"cost":111.04,
     "memo":"技術輔助型，玻璃基板配套設備，風險較低。太陰財庫型，天同化祿田宅宮靜待收益。"},
    {"code":"2493","name":"揚博科技", "group":"白名單額外追蹤","role":"🦾 武曲設備擴產 ★新 ★白名單額外追蹤","ex":"tse","holding":False,
     "sweet":(164.7, 172.1),"entry":(173.9, 183.2),"target":(222.0, 236.8),"cost":None,
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
