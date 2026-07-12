#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
交易日誌檢視器
雙擊執行 → 顯示所有交易紀錄 + 紀律統計
資料來源：交易日誌.csv（由 下單前檢查.py 寫入，也可用 Excel 直接編輯）
"""

import os, sys, csv
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(BASE, "交易日誌.csv")

def main():
    if not os.path.exists(LOG_FILE):
        print("還沒有任何交易紀錄。")
        print("用 下單前檢查.py 檢查價位時，就能順手記錄。")
        return

    with open(LOG_FILE, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    if not rows:
        print("日誌是空的。")
        return

    # ── 全部紀錄 ──
    print("═" * 78)
    print("  📒 交易日誌")
    print("═" * 78)
    print(f"{'日期':<18}{'名稱':<8}{'動作':<10}{'價格':>8}  {'張數':>4}  {'當時區間':<10} 理由")
    print("─" * 78)
    for r in rows:
        print(f"{r['日期']:<18}{r['名稱']:<8}{r['動作']:<10}{r['價格']:>8}  {r['張數']:>4}  {r['當時區間']:<10} {r['理由']}")

    # ── 紀律統計 ──
    buys = [r for r in rows if "買" in r["動作"]]
    disciplined = [r for r in buys if r["動作"] == "買進"]
    violated   = [r for r in buys if "違紀" in r["動作"]]
    zones = Counter(r["當時區間"] for r in buys)

    print()
    print("═" * 78)
    print("  📊 紀律統計")
    print("─" * 78)
    print(f"  買進筆數：{len(buys)}　其中紀律內 {len(disciplined)} 筆、違紀 {len(violated)} 筆")
    if buys:
        rate = len(disciplined) / len(buys) * 100
        bar = "█" * int(rate // 5) + "░" * (20 - int(rate // 5))
        print(f"  紀律達成率：{bar} {rate:.0f}%")
    print(f"  買進區間分布：", "、".join(f"{z} {n}筆" for z, n in zones.most_common()))
    if violated:
        print()
        print("  ⚠️ 違紀清單（檢討重點）：")
        for r in violated:
            print(f"    {r['日期']} {r['名稱']} @{r['價格']}（{r['當時區間']}）理由：{r['理由']}")
    print("═" * 78)
    print("  🌙 目標：紀律達成率 100%。協易機能做到，其他股票也能。")

if __name__ == "__main__":
    main()
    input("\n按 Enter 關閉視窗...")
