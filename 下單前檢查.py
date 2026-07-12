#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
下單前檢查（紀律鎖）
雙擊執行 → 輸入代號和想買的價格 → 告訴你能不能買
判斷依據：每日追價.py 裡自己定義的甜甜區/入手區/目標區
檢查完可選擇直接記入交易日誌
"""

import os, sys, csv, glob, re
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(BASE, "交易日誌.csv")

# ── 從每日追價.py 讀取 STOCKS 資料（不執行整個檔案）─────────────────────────
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

# ── 區間判斷（與每日追價.py 的 get_zone 一致）───────────────────────────────
def check(price, stock):
    sl, sh = stock["sweet"]
    el, eh = stock["entry"]
    tl, th = stock["target"]

    if price < sl:
        return "🔥 超甜區", f"低於甜甜區下限 {sl}，超值價，紀律內可買", True
    elif sl <= price <= sh:
        return "🍬 甜甜區", f"在甜甜區 {sl}–{sh} 內，紀律內可買", True
    elif sh < price < el:
        return "⬜ 空白地帶", f"介於甜甜區上限 {sh} 與入手區下限 {el} 之間，等回落再買", False
    elif el <= price <= eh:
        return "🎯 入手區", f"在入手區 {el}–{eh} 內，可買但不是最優價", True
    elif eh < price < tl:
        pct = (price - eh) / eh * 100
        return "🚫 追高區", f"高於入手區上限 {eh} 達 {pct:.1f}%，地劫警示：禁止買進", False
    elif tl <= price <= th:
        return "🎯 目標區", f"已達目標區 {tl}–{th}，該想的是賣不是買", False
    else:
        return "🚀 超過目標", f"已超過目標區上限 {th}，絕對禁止追高", False

# ── 記入交易日誌 ──────────────────────────────────────────────────────────────
def log_trade(code, name, action, price, lots, zone, reason):
    new_file = not os.path.exists(LOG_FILE)
    with open(LOG_FILE, "a", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        if new_file:
            w.writerow(["日期", "代號", "名稱", "動作", "價格", "張數", "當時區間", "理由"])
        w.writerow([datetime.now().strftime("%Y/%m/%d %H:%M"), code, name,
                    action, price, lots, zone, reason])
    print(f"✅ 已記入交易日誌：{LOG_FILE}")

# ── 主程式 ────────────────────────────────────────────────────────────────────
def main():
    stocks = {s["code"]: s for s in load_stocks()}

    print("═" * 46)
    print("  🔒 下單前檢查（紀律鎖）")
    print("  規則：只有甜甜區和入手區可以買")
    print("═" * 46)

    while True:
        print()
        code = input("股票代號（直接按 Enter 離開）：").strip()
        if not code:
            break
        if code not in stocks:
            print(f"❌ {code} 不在追蹤清單裡。先加入每日追價.py 再來檢查。")
            print("   （不在清單內的股票 = 沒做過功課 = 不買）")
            continue

        s = stocks[code]
        try:
            price = float(input(f"{s['name']} 想買的價格："))
        except ValueError:
            print("請輸入數字"); continue

        zone, msg, allowed = check(price, s)
        print()
        print(f"  {s['name']}（{code}）{s['role']}")
        print(f"  甜甜區 {s['sweet'][0]}–{s['sweet'][1]} ｜ 入手區 {s['entry'][0]}–{s['entry'][1]} ｜ 目標區 {s['target'][0]}–{s['target'][1]}")
        print(f"  ▶ {zone}：{msg}")
        if "七殺" in s["role"] or "地劫" in s["role"]:
            print("  ⚠️ 此股為七殺/地劫屬性，追高的代價比其他股票更大")
        print()

        if allowed:
            ans = input("要記入交易日誌嗎？(y=買進紀錄 / s=賣出紀錄 / Enter=跳過)：").strip().lower()
            if ans in ("y", "s"):
                action = "買進" if ans == "y" else "賣出"
                lots = input("張數：").strip() or "?"
                reason = input("一句話理由：").strip() or "-"
                log_trade(code, s["name"], action, price, lots, zone, reason)
        else:
            print("  🔒 紀律鎖：這個價位不買。太陰陀羅的武器是等待。")
            ans = input("  仍然要強制記錄嗎？(f=我還是買了 / Enter=聽話不買)：").strip().lower()
            if ans == "f":
                lots = input("張數：").strip() or "?"
                reason = input("一句話理由（誠實寫，之後檢討用）：").strip() or "-"
                log_trade(code, s["name"], "買進(違紀)", price, lots, zone, reason)

    print("\n離開。甜甜區才動手。")

if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\n離開。")
    input("\n按 Enter 關閉視窗...")
