#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
印和闐 每日運勢分析
每晚 21:00 自動執行，分析隔天運勢並發送到 Telegram
"""

import os, sys, json, urllib.request, urllib.parse
from datetime import datetime, timedelta, timezone

sys.stdout.reconfigure(encoding="utf-8")

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# 命盤資料（正確版本 — 科技紫微網）
BIRTH_CHART = """
姓名：枋立忠（杉本芳）
生辰：西元1978年02月10日 戌時
農曆：戊午年正月初四 戌時
陽男 土5局 生肖馬

命宮（辰）：太陰.陷（化權）、陀羅.廟、左輔
財帛宮：天機.廟（化忌）、文昌.得、天姚
官祿宮（申）：天同.旺、天梁.陷、天馬 ← 大限庚申45-54歲（2023-2032年）
遷移宮（酉）：武曲.利、七殺.旺、地劫
父母宮（巳）：廉貞.陷、貪狼.陷祿、祿存.廟
福德宮（午）：巨門.旺、擎羊.陷
田宅宮（未）：天相.得
子女宮（丑）：紫微.廟、破軍.旺
夫妻宮（寅）：文曲.平
兄弟宮（卯）：天府.得、天官、天德
疾厄宮（戌）：太陽.不、右弼科

命主：廉貞 / 身主：火星

2026丙午年四化：
- 天同化祿 → 官祿宮（事業大旺）
- 天機化權 → 財帛宮（本命忌+流年權，財運波動有掌控力）
- 文昌化科 → 財帛宮（分析判斷力強）
- 廉貞化忌 → 父母宮（注意長官關係）

目前狀態：大限官祿宮（45-54歲），事業財運黃金期
"""

def get_taiwan_tomorrow():
    tz = timezone(timedelta(hours=8))
    now = datetime.now(tz)
    tomorrow = now + timedelta(days=1)
    return tomorrow.strftime("%Y年%m月%d日（%A）")

def call_gemini(prompt):
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    )
    headers = {"Content-Type": "application/json"}
    body = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"maxOutputTokens": 800, "temperature": 0.7}
    }).encode()

    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read())
        return result["candidates"][0]["content"]["parts"][0]["text"]

def generate_fortune(date_str):
    prompt = f"""你是一位精通紫微斗數的命理師，請根據以下命盤為主人分析{date_str}的運勢。

{BIRTH_CHART}

請用繁體中文，依照以下格式輸出（不要多餘說明，直接輸出內容）：

🌅 <b>{date_str} 每日運勢</b>

🎨 <b>幸運色</b>：[顏色名稱]
💡 說明：[一句話說明為何這個顏色今天有利，與命盤哪個星宿有關]

⚠️ <b>今日注意</b>：
• [注意事項1，約25字]
• [注意事項2，約25字]

📈 <b>股票操作心態</b>：
• [心態建議1，結合命盤財帛宮天機忌特性，約30字]
• [心態建議2，具體可操作的建議，約30字]

🌙 <b>今日總評</b>：[一句話總結，30字以內]

注意：
- 幸運色要根據當天天干地支五行來判斷
- 股票建議要結合財帛宮天機化忌（財運波動、靠分析）和大限官祿宮（事業旺）
- 語氣要溫暖但實用，像朋友提醒一樣"""

    return call_claude(prompt)

def send_telegram(text):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("未設定 Telegram 環境變數，印出到 stdout：")
        print(text)
        return

    data = urllib.parse.urlencode({
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
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

if __name__ == "__main__":
    if not GEMINI_API_KEY:
        print("❌ 未設定 GEMINI_API_KEY，請設定環境變數或 GitHub Secret")
        sys.exit(1)

    date_str = get_taiwan_tomorrow()
    print(f"正在生成 {date_str} 運勢分析...")

    try:
        fortune_text = call_gemini(generate_fortune(date_str))
        print("運勢生成完成，發送 Telegram...")
        send_telegram(fortune_text)
    except Exception as e:
        print(f"❌ 錯誤：{e}")
        sys.exit(1)
