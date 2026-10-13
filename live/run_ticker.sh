#!/usr/bin/env bash
# 틱 스케줄러 (cron 없는 박스용 while-루프). 절차 판정 모드: 틱 1회 = 게임 1일.
# 주기는 live/ticker.conf 의 TICK_PERIOD(초, 현재 3600 = 매시 정각+TICK_OFFSET 초). 환경변수 TICK_PERIOD 가 있으면 우선.
#   run_ticker.sh start   백그라운드 시작(setsid+nohup, 세션 종료 후에도 유지) → live/ticker.pid, live/ticker.log
#   run_ticker.sh stop    중지
#   run_ticker.sh status  상태
#   run_ticker.sh loop    (내부용) 포그라운드 루프
#   run_ticker.sh once    tick.py 1회 실행 (cron 사용 시: 0 * * * * /workspace/eastfront/live/run_ticker.sh once)
set -uo pipefail
LIVE="$(cd "$(dirname "$0")" && pwd)"
PY="$LIVE/../.venv/bin/python"
PIDF="$LIVE/ticker.pid"
LOG="$LIVE/ticker.log"
export TZ=Asia/Seoul
CONF_P="${TICK_PERIOD:-}"
[ -f "$LIVE/ticker.conf" ] && . "$LIVE/ticker.conf"
export TICK_PERIOD="${CONF_P:-${TICK_PERIOD:-3600}}" TICK_OFFSET="${TICK_OFFSET:-2}"
alive() { [ -f "$PIDF" ] && kill -0 "$(cat "$PIDF")" 2>/dev/null; }
once() { "$PY" "$LIVE/tick.py" "$@" >>"$LOG" 2>&1; }
loop() {
  echo "[$(date '+%F %T KST')] ticker 루프 시작 pid $$ (주기 ${TICK_PERIOD}s +${TICK_OFFSET}s)" >>"$LOG"
  while true; do
    now=$(date +%s)
    P="$TICK_PERIOD"
    next=$(( (now / P + 1) * P ))          # 다음 주기 경계(3600 → 다음 정시)
    sleep $(( next - now + TICK_OFFSET ))   # 경계 TICK_OFFSET 초 뒤 실행
    # 로그 회전(5MB)
    [ -f "$LOG" ] && [ "$(stat -c %s "$LOG")" -gt 5000000 ] && mv -f "$LOG" "$LOG.1"
    TO=$(( P < 120 ? P - 5 : 600 ))
    timeout "$TO" "$PY" "$LIVE/tick.py" >>"$LOG" 2>&1 || echo "[$(date '+%F %T KST')] tick 종료코드 $?" >>"$LOG"
  done
}
case "${1:-status}" in
  start)
    if alive; then echo "이미 실행 중 (pid $(cat "$PIDF"))"; exit 0; fi
    setsid nohup bash "$LIVE/run_ticker.sh" loop >>"$LOG" 2>&1 < /dev/null &
    echo $! > "$PIDF"; sleep 1
    alive && echo "ticker 시작 pid $(cat "$PIDF") — 로그 $LOG" || { echo "시작 실패"; exit 1; } ;;
  stop)
    if alive; then pkill -P "$(cat "$PIDF")" 2>/dev/null; kill "$(cat "$PIDF")"; echo "중지"; else echo "실행 중 아님"; fi
    rm -f "$PIDF" ;;
  status)
    if alive; then echo "running pid $(cat "$PIDF")"; else echo "stopped"; fi
    tail -n 5 "$LOG" 2>/dev/null ;;
  loop) loop ;;
  once) shift; once "$@" ;;
  *) echo "usage: $0 start|stop|status|once"; exit 2 ;;
esac
