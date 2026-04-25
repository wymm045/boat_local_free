import importlib.util
import os
from pathlib import Path

from local_store import merge_records, today_text


def load_module(path: str):
    spec = importlib.util.spec_from_file_location("collector_base_local", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    path = os.environ.get("COLLECTOR_BASE_FILE", "collector_base.py")
    if not Path(path).exists():
        raise FileNotFoundError(f"collector_base file not found: {path}")
    mod = load_module(path)
    races = mod.build_candidates()
    rows = merge_records(races, mode="base", date=today_text())
    print(f"[local_base_ok] base={len(races)} total_rows={len(rows)}")
    print("[local_base_csv] local_data/races_latest.csv")


if __name__ == "__main__":
    main()
