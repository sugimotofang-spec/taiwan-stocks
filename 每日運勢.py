#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
印和闐 每日運勢分析（干支五行規則版）
每晚 21:00 自動執行，發送隔天運勢到 Telegram
"""

import os, sys, json, urllib.request, urllib.parse
from datetime import datetime, timedelta, timezone

sys.stdout.reconfigure(encoding="utf-8")

TELEGRAM_TOKEN   = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

# ── 天干地支 ──────────────────────────────────────────────────────────────────
TIANGAN = ["甲","乙","丙","丁","戊","己","庚","辛","壬","癸"]
DIZHI   = ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"]

TG_WUXING = {"甲":"木","乙":"木","丙":"火","丁":"火","戊":"土","己":"土",
              "庚":"金","辛":"金","壬":"水","癸":"水"}
DZ_WUXING = {"子":"水","丑":"土","寅":"木","卯":"木","辰":"土","巳":"火",
              "午":"火","未":"土","申":"金","酉":"金","戌":"土","亥":"水"}

def get_ganzhi(date):
    # 以 1900/1/31 為甲子日（JD基準）
    base = datetime(1900, 1, 31)
    delta = (date - base).days
    tg = TIANGAN[delta % 10]
    dz = DIZHI[delta % 12]
    return tg, dz

def get_year_ganzhi(year):
    tg = TIANGAN[(year - 4) % 10]
    dz = DIZHI[(year - 4) % 12]
    return tg, dz

# ── 命盤資料（正確版：科技紫微網＋正確命盤文字化_枋立忠.docx）────────────────
# 命宮（辰）：太陰（陷、化權）＋陀羅（廟）＋左輔 → 水+金
# 財帛宮（子）：空宮，借對拱太陽（火/木）＋巨門 → 靠分析/口才賺錢，非天機忌
# 遷移宮（戌）：天機（利）＋右弼 → 木，靈活出外求財
# 事業宮（申）：七殺（旺）＋地劫 → 金/火，有爆發力但地劫警示勿追高
# 田宅宮（未）：天同（順）＋天梁＋天馬 → 資產穩健
# 福德宮（午）：武曲（利）→ 2026流年命宮
# 大限：事業宮（申），七殺旺（45-54歲，2023-2032）

# 對你有利的五行：金生水，水為命宮太陰，金為陀羅
FAVORABLE   = {"金", "水"}
UNFAVORABLE = {"火"}   # 火剋金水，命宮受衝需謹慎

# 五行對應幸運色
WUXING_COLORS = {
    "木": ("綠色 / 青色", "天機遷移共鳴，靈活出手的好時機"),
    "火": ("紅色 / 橘色", "活躍但剋命宮金水，情緒容易衝動，宜守不宜攻"),
    "土": ("黃色 / 咖啡色", "土五局本命，穩重守成，適合檢視持倉"),
    "金": ("白色 / 金色 / 銀色", "陀羅命宮共鳴，精密佈局最有利"),
    "水": ("黑色 / 深藍色 / 深灰", "太陰命宮共鳴，策略清晰，分析判斷力最強"),
}

# ── 干支組合分析 ──────────────────────────────────────────────────────────────
def analyze_day(tg, dz, year_tg):
    tg_wx = TG_WUXING[tg]
    dz_wx = DZ_WUXING[dz]

    # 判斷整體吉凶
    favorable_count = sum(1 for w in [tg_wx, dz_wx] if w in FAVORABLE)
    unfavorable_count = sum(1 for w in [tg_wx, dz_wx] if w in UNFAVORABLE)

    # 幸運色：優先取對你有利的五行
    if tg_wx in FAVORABLE:
        lucky_wx = tg_wx
    elif dz_wx in FAVORABLE:
        lucky_wx = dz_wx
    else:
        lucky_wx = tg_wx
    lucky_color, lucky_reason = WUXING_COLORS[lucky_wx]

    # 評分 1-5
    score = 3 + favorable_count - unfavorable_count
    score = max(1, min(5, score))
    stars = "⭐" * score + "☆" * (5 - score)

    # 注意事項
    warnings = []
    stock_tips = []

    if "火" in [tg_wx, dz_wx]:
        warnings.append("火旺剋命宮金水，事業宮七殺衝動易被激發，切忌追高或情緒化操作")
        stock_tips.append("📉 今日守倉為主，不加碼，等股價回到甜甜區再動手")
    else:
        warnings.append("財帛空宮靠分析取財，今日宜冷靜覆盤，不靠感覺下單")

    if "金" in [tg_wx, dz_wx]:
        warnings.append("陀羅命宮金系共鳴，精密設備股今日能量強")
        stock_tips.append("💰 本命金系股（長虹・協易機）陀羅/武曲命宮共鳴，今日精密佈局最有利")
    elif "水" in [tg_wx, dz_wx]:
        warnings.append("太陰命宮水系共鳴，策略思維清晰，適合覆盤與規劃")
        stock_tips.append("📊 今日適合做功課、整理持倉邏輯，長線佈局方向再確認")
    elif "木" in [tg_wx, dz_wx]:
        warnings.append("天機遷移木系旺，靈活切換是今日優勢，但木生火需防衝動")
        stock_tips.append("📋 可觀察二軍是否有甜甜區訊號，靈活換股機會")
    elif "土" in [tg_wx, dz_wx]:
        warnings.append("土日穩健，本命土五局共鳴，守成為上策")
        stock_tips.append("🏦 持倉不動，等待明確趨勢突破再決策")

    # 大限＋事業宮提示
    stock_tips.append("🎯 大限事業宮七殺旺（45-54歲），有爆發力但地劫警示：嚴守紀律，甜甜區才動手")

    return {
        "score": score,
        "stars": stars,
        "tg_wx": tg_wx,
        "dz_wx": dz_wx,
        "lucky_color": lucky_color,
        "lucky_reason": lucky_reason,
        "warnings": warnings,
        "stock_tips": stock_tips,
    }

# ── 生成訊息 ──────────────────────────────────────────────────────────────────
def generate_message(target_date):
    tg, dz = get_ganzhi(target_date)
    year_tg, year_dz = get_year_ganzhi(target_date.year)
    result = analyze_day(tg, dz, year_tg)

    weekdays = ["週一","週二","週三","週四","週五","週六","週日"]
    weekday = weekdays[target_date.weekday()]
    date_str = target_date.strftime(f"%Y年%m月%d日（{weekday}）")
    ganzhi_str = f"{year_tg}{year_dz}年 {tg}{dz}日"

    lines = [
        f"🌅 <b>印和闐 {date_str} 每日運勢</b>",
        f"<i>{ganzhi_str}　天干{result['tg_wx']} / 地支{result['dz_wx']}</i>",
        f"今日能量：{result['stars']}",
        "─────────────────",
        f"🎨 <b>幸運色</b>：{result['lucky_color']}",
        f"💡 {result['lucky_reason']}",
        "",
        "⚠️ <b>今日注意</b>：",
    ]
    for w in result["warnings"]:
        lines.append(f"• {w}")

    lines += ["", "📈 <b>股票操作心態</b>："]
    for t in result["stock_tips"]:
        lines.append(f"• {t}")

    lines += [
        "",
        "─────────────────",
        "🌙 太陰化權+陀羅坐命（辰），核心心法：<b>紀律・結構・防守・磨功，甜甜區才動手</b>",
    ]

    return "\n".join(lines)

# ── 發送 Telegram ─────────────────────────────────────────────────────────────
def send_telegram(text):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("未設定 Telegram 環境變數，印出到 stdout：")
        print(text)
        return

    data = urllib.parse.urlencode({
        "chat_id":    TELEGRAM_CHAT_ID,
        "text":       text,
        "parse_mode": "HTML",
    }).encode()

    req = urllib.request.Request(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        data=data, method="POST"
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        result = json.loads(resp.read())
        if result.get("ok"):
            print("✅ Telegram 發送成功")
        else:
            print("❌ 發送失敗:", result)

# ── 主程式 ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    tz = timezone(timedelta(hours=8))
    now = datetime.now(tz)
    tomorrow = (now + timedelta(days=1)).replace(tzinfo=None)
    target = datetime(tomorrow.year, tomorrow.month, tomorrow.day)

    print(f"正在生成 {target.strftime('%Y/%m/%d')} 運勢...")
    msg = generate_message(target)
    print(msg)
    print("─" * 30)
    send_telegram(msg)
