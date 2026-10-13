#!/usr/bin/env bash
# 공개 게시(무로그인): 로컬 정적 서버 + Cloudflare Quick Tunnel(trycloudflare.com).
#   tunnel.sh start|stop|status|url
# 주의: Quick Tunnel 은 계정 없이 동작하지만 재시작하면 URL 이 바뀐다(무작위 *.trycloudflare.com). SLA 없음.
set -uo pipefail
LIVE="$(cd "$(dirname "$0")" && pwd)"
PY="$LIVE/../.venv/bin/python"
PUB="$LIVE/.publish"; mkdir -p "$PUB"
PORT="${EF_PORT:-8941}"
alive() { [ -f "$1" ] && kill -0 "$(cat "$1")" 2>/dev/null; }
start() {
  if ! alive "$PUB/serve.pid"; then
    setsid nohup "$PY" "$LIVE/serve.py" >>"$LIVE/serve.log" 2>&1 < /dev/null & echo $! > "$PUB/serve.pid"
    sleep 1
  fi
  if ! alive "$PUB/tunnel.pid"; then
    : > "$LIVE/tunnel.log"
    setsid nohup "$LIVE/bin/cloudflared" tunnel --no-autoupdate --url "http://127.0.0.1:$PORT" >>"$LIVE/tunnel.log" 2>&1 < /dev/null & echo $! > "$PUB/tunnel.pid"
    for i in $(seq 1 40); do
      u="$(grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' "$LIVE/tunnel.log" | head -1)"
      [ -n "$u" ] && break; sleep 1
    done
    if [ -n "${u:-}" ]; then
      old="$(cat "$PUB/tunnel_url" 2>/dev/null)"
      echo "$u" > "$PUB/tunnel_url"
      [ "$old" != "$u" ] && echo "$(TZ=Asia/Seoul date '+%F %T KST') 새 터널 URL: $u" >> "$LIVE/tunnel_urls.log"
    else
      echo "터널 URL 획득 실패 — tunnel.log 확인"; return 1
    fi
  fi
  echo "serve pid $(cat "$PUB/serve.pid"), tunnel pid $(cat "$PUB/tunnel.pid"), url $(cat "$PUB/tunnel_url" 2>/dev/null)"
}
stop() {
  for f in tunnel serve; do alive "$PUB/$f.pid" && kill "$(cat "$PUB/$f.pid")"; rm -f "$PUB/$f.pid"; done; echo stopped
}
case "${1:-status}" in
  start) start ;;
  stop) stop ;;
  url) cat "$PUB/tunnel_url" 2>/dev/null ;;
  status) for f in serve tunnel; do alive "$PUB/$f.pid" && echo "$f: running ($(cat "$PUB/$f.pid"))" || echo "$f: stopped"; done; cat "$PUB/tunnel_url" 2>/dev/null ;;
esac
