from __future__ import annotations

import csv
import json
import os
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

JST = timezone(timedelta(hours=9))
DATA_DIR = Path(os.environ.get("LOCAL_DATA_DIR", "local_data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)

FINAL_FREEZE_FIELDS = [
    "final_ai_score",
    "final_ai_rating",
    "final_ai_selection",
    "final_rank",
    "latest_reason_text",
    "latest_updated_at",
]

CSV_PRIORITY_COLUMNS = [
    "race_date", "time", "venue", "race_no", "race_no_num", "candidate_source", "rating",
    "selection", "base_ai_score", "base_ai_rating", "base_ai_selection", "base_reason_text",
    "final_ai_score", "final_ai_rating", "final_ai_selection", "final_rank", "latest_reason_text", "latest_updated_at",
    "exhibition", "exhibition_rank", "weather", "wind_speed", "wave_height", "wind_type", "wind_dir", "water_state_score",
    "ai_lane_score_text", "class_history_text", "player_names_text", "player_stat_text", "player_reason_text",
    "result_trifecta_text", "result_trifecta_payout", "result_exacta_text", "result_exacta_payout", "result_trio_text", "result_trio_payout",
    "settled_flag", "settled_at", "result_source_url", "imported_at",
    "purchased", "purchased_selection_text", "amount", "hit", "payout", "memo",
]


def jst_now() -> datetime:
    return datetime.now(JST)


def today_text() -> str:
    return jst_now().strftime("%Y-%m-%d")


def now_text() -> str:
    return jst_now().strftime("%Y-%m-%d %H:%M:%S JST")


def normalize_race_no(value: Any) -> str:
    s = str(value or "").strip()
    m = re.search(r"(\d{1,2})", s)
    return f"{int(m.group(1))}R" if m else s


def normalize_race_no_num(value: Any) -> int:
    m = re.search(r"(\d{1,2})", str(value or ""))
    return int(m.group(1)) if m else 0


def normalize_source(value: Any) -> str:
    s = str(value or "official_all").strip() or "official_all"
    if s in {"official_all", "official_star", "shadow_ai", "all_race_ai"}:
        return s
    return "official_all"


def race_key(row: Dict[str, Any]) -> str:
    race_date = str(row.get("race_date") or today_text()).strip()
    venue = str(row.get("venue") or "").strip()
    race_no = normalize_race_no(row.get("race_no") or row.get("race_no_num"))
    source = normalize_source(row.get("candidate_source"))
    return "|".join([race_date, venue, race_no, source])


def time_to_min(value: Any) -> int | None:
    s = str(value or "").strip()
    m = re.fullmatch(r"(\d{1,2}):(\d{2})", s)
    if not m:
        return None
    return int(m.group(1)) * 60 + int(m.group(2))


def is_closed(row: Dict[str, Any]) -> bool:
    if str(row.get("race_date") or today_text()) != today_text():
        return True
    t = time_to_min(row.get("time"))
    if t is None:
        return False
    return t < (jst_now().hour * 60 + jst_now().minute)


def data_json_path(date: str | None = None) -> Path:
    return DATA_DIR / f"races_{date or today_text()}.json"


def data_csv_path(date: str | None = None) -> Path:
    return DATA_DIR / f"races_{date or today_text()}.csv"


def latest_csv_path() -> Path:
    return DATA_DIR / "races_latest.csv"


def latest_json_path() -> Path:
    return DATA_DIR / "races_latest.json"


def read_rows(date: str | None = None) -> List[Dict[str, Any]]:
    path = data_json_path(date)
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    return data.get("races", []) if isinstance(data, dict) else []


def stringify_for_csv(value: Any) -> Any:
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False)
    return value


def write_rows(rows: List[Dict[str, Any]], date: str | None = None) -> None:
    date = date or today_text()
    rows = sorted(rows, key=lambda r: (str(r.get("race_date") or ""), str(r.get("time") or "99:99"), str(r.get("venue") or ""), normalize_race_no_num(r.get("race_no") or r.get("race_no_num")), normalize_source(r.get("candidate_source"))))

    for r in rows:
        r.setdefault("race_date", date)
        r["race_no"] = normalize_race_no(r.get("race_no") or r.get("race_no_num"))
        r["race_no_num"] = normalize_race_no_num(r.get("race_no") or r.get("race_no_num"))
        r["candidate_source"] = normalize_source(r.get("candidate_source"))

    payload = {"updated_at": now_text(), "races": rows}
    with data_json_path(date).open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    with latest_json_path().open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    all_keys = []
    seen = set()
    for c in CSV_PRIORITY_COLUMNS:
        seen.add(c); all_keys.append(c)
    for r in rows:
        for k in r.keys():
            if k not in seen:
                seen.add(k); all_keys.append(k)

    for csv_path in [data_csv_path(date), latest_csv_path()]:
        with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=all_keys, extrasaction="ignore")
            w.writeheader()
            for r in rows:
                w.writerow({k: stringify_for_csv(r.get(k, "")) for k in all_keys})


def merge_records(new_rows: Iterable[Dict[str, Any]], mode: str = "latest", date: str | None = None, freeze_closed: bool = True) -> List[Dict[str, Any]]:
    date = date or today_text()
    existing = {race_key(r): dict(r) for r in read_rows(date)}

    for incoming in new_rows:
        inc = dict(incoming or {})
        inc.setdefault("race_date", date)
        inc["race_no"] = normalize_race_no(inc.get("race_no") or inc.get("race_no_num"))
        inc["race_no_num"] = normalize_race_no_num(inc.get("race_no") or inc.get("race_no_num"))
        inc["candidate_source"] = normalize_source(inc.get("candidate_source"))
        inc.setdefault("imported_at", now_text())
        key = race_key(inc)
        old = existing.get(key, {})
        merged = dict(old)

        if mode == "base":
            merged.update({k: v for k, v in inc.items() if v is not None})
        else:
            # app.pyの締切後凍結に近い挙動。既存finalがある締切後は買い目系を守る。
            preserve_final = freeze_closed and old and is_closed(old) and str(old.get("final_ai_selection") or "").strip()
            for k, v in inc.items():
                if preserve_final and k in FINAL_FREEZE_FIELDS:
                    continue
                if v is None:
                    continue
                if isinstance(v, str) and v == "" and k in old:
                    continue
                merged[k] = v

        existing[key] = merged

    rows = list(existing.values())
    write_rows(rows, date=date)
    return rows


def make_base_map(date: str | None = None) -> Dict[str, Dict[str, Any]]:
    base_map: Dict[str, Dict[str, Any]] = {}
    for r in read_rows(date):
        venue = str(r.get("venue") or "").strip()
        race_no = normalize_race_no(r.get("race_no") or r.get("race_no_num"))
        source = normalize_source(r.get("candidate_source"))
        if not venue or not race_no:
            continue
        key_with_source = f"{venue}|{race_no}|{source}"
        base_map[key_with_source] = dict(r)
        if source == "official_all":
            base_map.setdefault(f"{venue}|{race_no}", dict(r))
    return base_map


def save_purchases(purchases: Dict[str, Dict[str, Any]], date: str | None = None) -> None:
    path = DATA_DIR / f"purchases_{date or today_text()}.json"
    with path.open("w", encoding="utf-8") as f:
        json.dump(purchases, f, ensure_ascii=False, indent=2)


def load_purchases(date: str | None = None) -> Dict[str, Dict[str, Any]]:
    path = DATA_DIR / f"purchases_{date or today_text()}.json"
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, dict) else {}
