#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
盤中即時提醒
由 GitHub Actions 在開盤時段（09:30 / 11:30 / 13:20）定時執行
只有命中「甜甜區以下」或「目標區以上」才發送 Telegram，其餘狀況靜默不通知
"""
import os, sys
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8")

TOKEN   = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

if not TOKEN or not CHAT_ID:
    print("未設定 TELEGRAM_BOT_TOKEN 或 TELEGRAM_CHAT_ID，跳過")
    sys.exit(0)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 每日追價 import STOCKS, get_zone

def fetch_intraday_prices():
    """抓盤中即時價（分鐘線最新一筆），而非昨日收盤價"""
    try:
        import yfinance as yf
    except ImportError:
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "yfinance", "-q"])
        import yfinance as yf

    prices = {}
    for s in STOCKS:
        code = s["code"]
        for suffix in ([".TW", ".TWO"] if s["ex"] == "tse" else [".TWO", ".TW"]):
            try:
                ticker = yf.Ticker(f"{code}{suffix}")
                hist = ticker.history(period="1d", interval="1m")
                if not hist.empty:
                    prices[code] = round(float(hist["Close"].iloc[-1]), 2)
                    break
            except Exception:
                continue
    return prices

prices = fetch_intraday_prices()

buy_alerts  = []   # 甜甜區以下：可以動手
sell_alerts = []   # 目標區以上：該想賣了

for s in STOCKS:
    code  = s["code"]
    price = prices.get(code)
    if price is None:
        continue
    zone  = get_zone(price, s["sweet"], s["entry"], s["target"], s["holding"])
    group = "🔴一軍" if s["holding"] else "🔵二軍"
    cost  = s.get("cost")
    pnl   = f"（損益 {((price/cost-1)*100):+.1f}%）" if cost else ""

    if zone == "below_sweet":
        buy_alerts.append(f"🔥 <b>{s['name']}</b>({code}) {price:,.1f}  低於甜甜區下限 {s['sweet'][0]}！{pnl}")
    elif zone == "sweet":
        buy_alerts.append(f"🍬 <b>{s['name']}</b>({code}) {price:,.1f}  在甜甜區 {s['sweet'][0]}–{s['sweet'][1]} 內 {group}{pnl}")
    elif zone == "target":
        sell_alerts.append(f"🎯 <b>{s['name']}</b>({code}) {price:,.1f}  已達目標區 {s['target'][0]}–{s['target'][1]} {group}{pnl}")
    elif zone == "above_target":
        sell_alerts.append(f"🚀 <b>{s['name']}</b>({code}) {price:,.1f}  已超過目標區上限 {s['target'][1]}！{group}{pnl}")

# 沒有任何命中 → 完全不發送，安靜
if not buy_alerts and not sell_alerts:
    print("盤中檢查：無股票命中甜甜區/目標區，不發送通知")
    sys.exit(0)

now = datetime.now().strftime("%H:%M")
lines = [f"<b>⏱ 盤中提醒</b>　{now}", "─────────────────"]

if buy_alerts:
    lines.append("<b>🍬 打到甜甜價了！</b>")
    lines.extend(buy_alerts)
    lines.append("")

if sell_alerts:
    lines.append("<b>🎯 到達滿足點！</b>")
    lines.extend(sell_alerts)
    lines.append("")

lines.append("─────────────────")
lines.append("紀律內動手，不追高不追殺")

text = "\n".join(lines)

import urllib.request, urllib.parse, json
data = urllib.parse.urlencode({
    "chat_id":    CHAT_ID,
    "text":       text,
    "parse_mode": "HTML",
}).encode()

req = urllib.request.Request(
    f"https://api.telegram.org/bot{TOKEN}/sendMessage",
    data=data, method="POST"
)

try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        result = json.loads(resp.read())
        if result.get("ok"):
            print(f"盤中提醒已發送：{len(buy_alerts)} 買進訊號、{len(sell_alerts)} 賣出訊號")
        else:
            print("發送失敗:", result)
except Exception as e:
    print("發送錯誤:", e)
    sys.exit(1)
