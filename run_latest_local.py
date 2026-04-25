import importlib.util
import os
from pathlib import Path

from local_store import make_base_map, merge_records, today_text


def load_module(path: str):
    spec = importlib.util.spec_from_file_location("collector_latest_local", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    path = os.environ.get("COLLECTOR_FILE", "collector.py")
    if not Path(path).exists():
        raise FileNotFoundError(f"collector file not found: {path}")
    mod = load_module(path)

    def fetch_base_map_local():
        base_map = make_base_map(today_text())
        print(f"[local_base_map_ok] count={len(base_map)}")
        if not base_map:
            raise RuntimeError("local_dataにbaseがありません。先に python run_base_local.py を実行してください。")
        return base_map

    mod.fetch_base_map_today = fetch_base_map_local
    races = mod.build_candidates()

    freeze_closed = os.environ.get("LOCAL_FREEZE_CLOSED", "1").strip() != "0"
    rows = merge_records(races, mode="latest", date=today_text(), freeze_closed=freeze_closed)

    print(f"[local_latest_ok] latest_updates={len(races)} total_rows={len(rows)} freeze_closed={freeze_closed}")
    print("[local_latest_csv] local_data/races_latest.csv")


if __name__ == "__main__":
    main()
