#!/usr/bin/env bash
# 재개: paused=false. 명령 라운드 대기(live/awaiting_orders.json)도 해제. 선택적으로 모드 지정.
#   resume.sh              (모드 유지)
#   resume.sh broadcast    방송 모드(사이트에 '● 방송 중' 배지)
#   resume.sh auto         자동 모드
LIVE="$(cd "$(dirname "$0")" && pwd)"; PY="$LIVE/../.venv/bin/python"
MODE="${1:-}"
case "$MODE" in ""|auto|broadcast) ;; *) echo "mode 는 auto|broadcast"; exit 2 ;; esac
"$PY" - "$LIVE" "$MODE" <<'PYEOF'
import sys; sys.path.insert(0, sys.argv[1])
from common import *
with state_lock():
    st = load_state(); was = st.get("paused")
    import rounds as RD
    if st.get("awaiting_orders") or os.path.exists(RD.FLAG):
        RD.clear_flag(st, "심판 재개(resume.sh) — 새 명령/strategy.json 반영")
    st["paused"] = False
    if sys.argv[2]: st["mode"] = sys.argv[2]
    st["status"] = "진행"
    if was:
        gt = game_stamp(st["clock"]["date"], st["clock"]["hour"])
        st["events"].append(dict(game_time=gt, axis="all", kind="system", text="진행 재개" + (" (방송 모드)" if st["mode"] == "broadcast" else ""), real_time=iso_kst()))
    save_state(st)
print("paused=False mode=%s" % st["mode"])
PYEOF
"$PY" "$LIVE/tick.py" --site-only >>"$LIVE/ticker.log" 2>&1; tail -n 2 "$LIVE/ticker.log"
