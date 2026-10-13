#!/usr/bin/env bash
# 일시정지: paused=true. 시계·부대 정지, 사이트에 '일시정지' 배지. 사이트 즉시 갱신.
#   pause.sh [사유]
LIVE="$(cd "$(dirname "$0")" && pwd)"; PY="$LIVE/../.venv/bin/python"
"$PY" - "$LIVE" "${*:-}" <<'PYEOF'
import sys; sys.path.insert(0, sys.argv[1])
from common import *
with state_lock():
    st = load_state(); st["paused"] = True; st["status"] = "일시정지"
    gt = game_stamp(st["clock"]["date"], st["clock"]["hour"])
    st["events"].append(dict(game_time=gt, axis="all", kind="system", text="진행 일시정지" + (f" — {sys.argv[2]}" if sys.argv[2] else ""), real_time=iso_kst()))
    save_state(st)
print("paused=True mode=%s" % st["mode"])
PYEOF
"$PY" "$LIVE/tick.py" --site-only >>"$LIVE/ticker.log" 2>&1; tail -n 2 "$LIVE/ticker.log"
