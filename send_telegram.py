#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日 Telegram 通知
在 GitHub Actions 執行完股價更新後，發送摘要到 Telegram
"""
import os, sys, urllib.request, urllib.parse, json

sys.stdout.reconfigure(encoding="utf-8")

TOKEN   = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

if not TOKEN or not CHAT_ID:
    print("未設定 TELEGRAM_BOT_TOKEN 或 TELEGRAM_CHAT_ID，跳過通知")
    sys.exit(0)

# 讀取股票資料（直接 import 主程式的 STOCKS）
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 每日追價 import STOCKS, fetch_prices, get_zone

prices, volumes = fetch_prices()

# 找出甜甜區 / 超甜的股票
sweet_list  = []
entry_list  = []
target_list = []

for s in STOCKS:
    code  = s["code"]
    price = prices.get(code)
    if price is None:
        continue
    zone = get_zone(price, s["sweet"], s["entry"], s["target"], s["holding"])
    group = "一軍" if s["holding"] else "二軍"
    line  = f"{'🔴' if group=='一軍' else '🔵'} {s['name']}({code}) {price:,.1f}"

    if zone == "below_sweet":
        sweet_list.append(f"🔥 {line}  ← 低於甜甜價！")
    elif zone == "sweet":
        sweet_list.append(f"🍬 {line}")
    elif zone == "entry":
        entry_list.append(f"✅ {line}")
    elif zone in ("target", "above_target"):
        target_list.append(f"🎯 {line}")

# 組訊息
from datetime import datetime
now = datetime.now().strftime("%Y/%m/%d %H:%M")

lines = [f"<b>印和闐 台股藏金閣</b>  {now}"]
lines.append("─────────────────")

if sweet_list:
    lines.append("<b>🍬 甜甜區（可以動手了！）</b>")
    lines.extend(sweet_list)
    lines.append("")

if entry_list:
    lines.append("<b>✅ 推薦入手區</b>")
    lines.extend(entry_list)
    lines.append("")

if target_list:
    lines.append("<b>🎯 接近 / 超過滿足點</b>")
    lines.extend(target_list)
    lines.append("")

if not sweet_list and not entry_list:
    lines.append("今日無股票進入買入區間，繼續持有等待。")

lines.append("─────────────────")
lines.append(f"一軍持有 {sum(1 for s in STOCKS if s['holding'])} 檔　二軍觀察 {sum(1 for s in STOCKS if not s['holding'])} 檔")

text = "\n".join(lines)

# 發送
data = urllib.parse.urlencode({
    "chat_id":    CHAT_ID,
    "text":       text,
    "parse_mode": "HTML",
}).encode()

req = urllib.request.Request(
    f"https://api.telegram.org/bot{TOKEN}/sendMessage",
    data=data,
    method="POST"
)

try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        result = json.loads(resp.read())
        if result.get("ok"):
            print("Telegram 通知發送成功")
        else:
            print("發送失敗:", result)
except Exception as e:
    print("發送錯誤:", e)
    sys.exit(1)
