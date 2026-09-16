#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
同步 每日追價.py 的 STOCKS 名單 ↔ 2026我的配置*.xlsx

用法：
    python sync_stocks.py            # 用最新的 2026我的配置*.xlsx 同步
    python sync_stocks.py --dry-run  # 只印出結果，不寫回 每日追價.py

規則：
- 只納入 xlsx 工作表1 的「一軍」「二軍」兩個區塊（三軍/探針卡新觀察、玻璃基板候補不納入通知名單）
- EXTRA_WHITELIST 手動加入不在一軍/二軍、但想額外追蹤的個股（例如揚博）
- 甜甜價/入手區/滿足點、Sugi筆記（取第一行當 memo）一律以 xlsx 為準覆蓋
- holding（是否持有）與 cost（實際成本價）不會被 xlsx 覆蓋——因為 xlsx 的「成本價」欄
  多數是空的，不是真實持股紀錄。這兩個欄位永遠沿用 每日追價.py 裡舊的值，新股預設
  holding=False, cost=None，避免同步時誤刪真實持股資料。
"""
import os, re, glob, ast, ex_market_map

BASE = os.path.dirname(os.path.abspath(__file__))
SCRIPT_PATH = os.path.join(BASE, "每日追價.py")

# 額外白名單：不在 xlsx 一軍/二軍區塊，但想加進通知名單的股票代號
EXTRA_WHITELIST = {
    "2493",  # 揚博科技（使用者指定額外追蹤）
    "3580",  # 友威科（每日追價.py 原本有 cost=111.04 實際持股，防止同步時被誤刪）
    "6438",  # 迅得（每日追價.py 原本有 cost=178.16 實際持股，防止同步時被誤刪）
}


def latest_config_xlsx():
    files = glob.glob(os.path.join(BASE, "2026我的配置*.xlsx"))
    if not files:
        raise FileNotFoundError("找不到 2026我的配置*.xlsx")
    return max(files, key=os.path.basename)


def parse_band(s):
    if not isinstance(s, str):
        return None
    m = re.findall(r"[\d,]+\.?\d*", s)
    if len(m) < 2:
        return None
    lo, hi = (float(x.replace(",", "")) for x in m[:2])
    return (lo, hi)


def read_existing_stocks():
    """讀取 每日追價.py 目前的 STOCKS，取出 holding / cost，做為覆蓋保護。"""
    src = open(SCRIPT_PATH, encoding="utf-8").read()
    m = re.search(r"STOCKS\s*=\s*\[(.*?)\n\]\s*\n", src, re.S)
    block = m.group(1) if m else ""
    existing = {}
    for entry in re.finditer(r"\{[^{}]*\}", block):
        try:
            d = ast.literal_eval(entry.group(0))
        except Exception:
            continue
        if "code" in d:
            existing[d["code"]] = {"holding": d.get("holding", False), "cost": d.get("cost")}
    return existing


def extract_from_xlsx(path):
    import openpyxl
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb["工作表1"]

    section = None
    rows = []
    for r in range(1, ws.max_row + 1):
        a = ws.cell(r, 1).value
        if isinstance(a, str) and ws.cell(r, 2).value is None:
            if a.strip() in ("一軍", "二軍"):
                section = a.strip()
            elif "三軍" in a or "玻璃基板" in a or "下半年新觀察" in a:
                section = None  # 離開一軍/二軍，之後的列都不納入
            continue
        if section not in ("一軍", "二軍"):
            continue
        code = a
        if not (isinstance(code, int) or (isinstance(code, str) and code.isdigit())):
            continue
        code = str(code)
        name = ws.cell(r, 2).value
        role = ws.cell(r, 3).value or ""
        sweet = parse_band(ws.cell(r, 7).value)
        entry = parse_band(ws.cell(r, 8).value)
        target = parse_band(ws.cell(r, 9).value)
        note = (ws.cell(r, 10).value or "").split("\n")[0]
        rows.append({
            "code": code, "name": name, "group": section, "role": role,
            "sweet": sweet, "entry": entry, "target": target, "memo": note,
        })
    return rows


def build_stocks_block(rows, existing, ex_map):
    lines = ["STOCKS = ["]
    for grp in ("一軍", "二軍"):
        lines.append(f"    # ─ {grp} ─")
        for r in rows:
            if r["group"] != grp:
                continue
            prev = existing.get(r["code"], {})
            holding = prev.get("holding", grp == "一軍")
            cost = prev.get("cost")
            ex = ex_map.get(r["code"], "tse")
            cost_repr = "None" if cost is None else repr(cost)
            lines.append(
                f'    {{"code":"{r["code"]}","name":"{r["name"]}", "group":"{grp}","role":"{r["role"]}",'
                f'"ex":"{ex}","holding":{holding},\n'
                f'     "sweet":{r["sweet"]},"entry":{r["entry"]},"target":{r["target"]},"cost":{cost_repr},\n'
                f'     "memo":"{r["memo"]}"}},'
            )
        lines.append("")
    lines[-1] = lines[-1]  # trailing section already blank
    if lines[-1] == "":
        lines.pop()
    lines.append("]")
    return "\n".join(lines)


def main(dry_run=False):
    path = latest_config_xlsx()
    print(f"讀取: {os.path.basename(path)}")
    rows = extract_from_xlsx(path)

    missing = [c for c in EXTRA_WHITELIST if not any(r["code"] == c for r in rows)]
    if missing:
        import openpyxl
        wb = openpyxl.load_workbook(path, data_only=True)
        for code in missing:
            found = False
            for sheet_name in wb.sheetnames:
                ws = wb[sheet_name]
                for r in range(1, ws.max_row + 1):
                    if str(ws.cell(r, 1).value) == code:
                        rows.append({
                            "code": code, "name": ws.cell(r, 2).value, "group": "二軍",
                            "role": (ws.cell(r, 3).value or "") + " ★白名單額外追蹤",
                            "sweet": parse_band(ws.cell(r, 7).value),
                            "entry": parse_band(ws.cell(r, 8).value),
                            "target": parse_band(ws.cell(r, 9).value),
                            "memo": (ws.cell(r, 10).value or "").split("\n")[0],
                        })
                        found = True
                        break
                if found:
                    break
            if not found:
                print(f"⚠️  白名單 {code} 在 xlsx 全部工作表都找不到，請人工檢查（可能已下市/代號變更）")

    existing = read_existing_stocks()
    ex_map = ex_market_map.EX_MAP
    block = build_stocks_block(rows, existing, ex_map)

    codes_new = {r["code"] for r in rows}
    codes_old = set(existing)
    added = codes_new - codes_old
    removed = codes_old - codes_new
    print(f"名單筆數: {len(rows)}（一軍 {sum(1 for r in rows if r['group']=='一軍')} + 二軍 {sum(1 for r in rows if r['group']=='二軍')}）")
    if added:
        print("新增:", ", ".join(sorted(added)))
    if removed:
        print("移除:", ", ".join(sorted(removed)))

    if dry_run:
        print("\n--dry-run，未寫回檔案。以下為預覽：\n")
        print(block[:2000])
        return

    src = open(SCRIPT_PATH, encoding="utf-8").read()
    new_src = re.sub(r"STOCKS\s*=\s*\[.*?\n\]\s*\n", block + "\n\n", src, flags=re.S, count=1)
    open(SCRIPT_PATH, "w", encoding="utf-8").write(new_src)
    print(f"\n已寫回 {SCRIPT_PATH}")


if __name__ == "__main__":
    import sys
    main(dry_run="--dry-run" in sys.argv)
