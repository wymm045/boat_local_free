Renderを使わないローカル無料運用スターター

目的:
- Render / Render Cron / Render PostgreSQL を使わず、PC上で候補生成・CSV保存・簡易画面表示をする。
- 既存の collector_base.py / collector.py のロジックはなるべくそのまま使う。

ファイル:
- collector_base.py : 朝base生成用。v10.57_statsを同梱。
- collector.py : 直前latest生成用。v10.58_preinfo_pit_tilt_fix3を同梱。
- local_store.py : ローカルJSON/CSV保存と締切後final凍結の簡易処理。
- run_base_local.py : collector_base.pyをローカル保存用に実行。
- run_latest_local.py : collector.pyをローカル保存用に実行。
- app_local.py : PCブラウザ用の簡易表示画面。

初回セットアップ:
1) このzipを展開
2) PowerShellで展開先へ移動
   cd "C:\Users\wymm0\OneDrive\デスクトップ\race_system_local"
3) 必要ライブラリ
   python -m pip install requests beautifulsoup4 flask

毎日の運用:
1) 朝base作成
   python run_base_local.py
2) 直前更新
   $env:SKIP_PAST_RACES="1"
   $env:RESULT_REPAIR_MODE="0"
   $env:ENABLE_ALL_RACE_LIVE="0"
   python run_latest_local.py
3) 画面表示
   python app_local.py
   ブラウザで http://127.0.0.1:5000 を開く

& "C:\Program Files\Tailscale\tailscale.exe" serve http://127.0.0.1:5000

締切後テスト/補完:
   $env:SKIP_PAST_RACES="0"
   $env:RESULT_REPAIR_MODE="0"
   $env:ENABLE_ALL_RACE_LIVE="0"
   python run_latest_local.py

出力:
- local_data/races_latest.csv
- local_data/races_YYYY-MM-DD.csv
- local_data/races_latest.json

注意:
- これはRender撤退用のローカル版スターターです。
- 既存のRenderアプリほどUIは作り込んでいません。
- ただし、買い目生成ロジックは同梱collectorを使うので、無料運用の検証には使えます。
- run_latest_local.pyは締切後final_ai_selectionが既にある場合、local_store側で買い目系を凍結します。


[v4_render_like]
Render版に近い情報量に寄せたローカル表示版です。買い方メモ、AI/公式2列、艇別材料、直前追加、展示タイム/順位、水面・風波、AI艇別スコア、更新情報、理由全文を表示します。保存方式はローカルJSON/CSVのままなのでRender/PostgreSQLは不要です。
