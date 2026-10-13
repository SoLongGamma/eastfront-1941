#!/usr/bin/env bash
# live/site 공개 게시. 대상(PUBLISH_TARGETS, 공백 구분, 기본 "tunnel brewpage"):
#   tunnel   — 로컬 정적 서버 + Cloudflare Quick Tunnel (무로그인). 디스크의 site/ 를 그대로 서비스하므로
#              업로드 없음; 여기서는 서버·터널이 살아있는지 확인하고 죽었으면 재시작(URL 바뀜 → tunnel_urls.log).
#   brewpage — BrewPage 무가입 사이트(ZIP 업로드, 같은 URL 갱신, 매번 TTL 30일 연장). 403 차단 시 6시간 백오프.
#   github   — GitHub Pages. live/.publish/github_remote 에 원격 주소를 넣고 사용자의 git 인증이 있어야만 동작.
set -uo pipefail
LIVE="$(cd "$(dirname "$0")" && pwd)"
SITE="$LIVE/site"
PUB="$LIVE/.publish"
PY="$LIVE/../.venv/bin/python"
UA="grok-bot/eastfront-live-1.0"
NS="${BREWPAGE_NS:-eastfront-1941}"
mkdir -p "$PUB" "$LIVE/cache"; chmod 700 "$PUB"
TARGETS="${PUBLISH_TARGETS:-brewpage}"
[ -f "$PUB/github_remote" ] && [[ "$TARGETS" != *github* ]] && TARGETS="$TARGETS github"
rc=0
jget() { "$PY" -c 'import json,sys;print(json.load(open(sys.argv[1])).get(sys.argv[2],""))' "$1" "$2"; }

publish_tunnel() {
  out="$(bash "$LIVE/tunnel.sh" start 2>&1)"; r=$?
  echo "tunnel: $(cat "$PUB/tunnel_url" 2>/dev/null)"; [ $r -ne 0 ] && { echo "$out"; rc=1; }
}

publish_brewpage() {
  local zip="$LIVE/cache/site.zip" meta="$PUB/brewpage.json" block="$PUB/brewpage_block_until" resp code now
  now="$(date +%s)"
  if [ -f "$block" ] && [ "$now" -lt "$(cat "$block")" ]; then
    echo "brewpage: 차단 백오프 중($(TZ=Asia/Seoul date -d @"$(cat "$block")" '+%H:%M KST')까지) — 건너뜀"; return
  fi
  # 1분 틱에서 과도한 업로드 방지: 최소 간격 BREWPAGE_MIN_INTERVAL(기본 900초)
  local lastf="$PUB/brewpage_last_try"
  if [ -f "$lastf" ] && [ $(( now - $(cat "$lastf") )) -lt "${BREWPAGE_MIN_INTERVAL:-900}" ]; then
    echo "brewpage: 간격 제한 — 건너뜀"; return
  fi
  echo "$now" > "$lastf"
  "$PY" - "$SITE" "$zip" <<'PYEOF'
import os, sys, zipfile
site, out = sys.argv[1], sys.argv[2]
with zipfile.ZipFile(out + ".tmp", "w", zipfile.ZIP_DEFLATED) as z:
    for root, _, files in os.walk(site):
        for f in sorted(files):
            if f.startswith("."): continue
            p = os.path.join(root, f)
            z.write(p, os.path.relpath(p, site))
os.replace(out + ".tmp", out)
PYEOF
  resp="$(mktemp)"
  if [ -f "$meta" ]; then
    code="$(curl -sS -m 120 -o "$resp" -w '%{http_code}' -X PUT "https://brewpage.app/api/sites/$NS/$(jget "$meta" id)?ttl=30" \
      -A "$UA" -H "X-Owner-Token: $(jget "$meta" ownerToken)" -F "archive=@$zip;type=application/zip")"
    want=200
  else
    code="$(curl -sS -m 120 -o "$resp" -w '%{http_code}' -X POST "https://brewpage.app/api/sites?ns=$NS&ttl=30&tags=wargame,eastfront" \
      -A "$UA" -F "archive=@$zip;type=application/zip")"
    want=201
  fi
  if [ "$code" = "$want" ] || [ "$code" = "200" ]; then
    if [ -f "$meta" ]; then
      "$PY" - "$meta" "$resp" <<'PYEOF'
import json, sys
m = json.load(open(sys.argv[1])); r = json.load(open(sys.argv[2]))
m["expiresAt"] = r.get("expiresAt", m.get("expiresAt"))
json.dump(m, open(sys.argv[1], "w"), ensure_ascii=False, indent=1)
PYEOF
    else
      (umask 077; cp "$resp" "$meta")
    fi
    rm -f "$block"
    echo "brewpage OK: $(jget "$meta" link) (만료 $(jget "$meta" expiresAt))"
  else
    echo "brewpage 실패 HTTP $code: $(head -c 200 "$resp")"
    [ "$code" = "403" ] || [ "$code" = "429" ] && echo $((now + 6 * 3600)) > "$block"
    rc=1
  fi
  rm -f "$resp"
}

publish_github() {
  # 사용자의 GitHub 인증(gh auth login / SSH 키 / credential helper)이 있어야 함. 토큰을 찾거나 만들지 않는다.
  local remote repo="$LIVE/gh-pages-repo"
  remote="$(cat "$PUB/github_remote")"
  [ -d "$repo/.git" ] || { git init -q -b main "$repo" && git -C "$repo" remote add origin "$remote"; }
  find "$repo" -mindepth 1 -maxdepth 1 ! -name .git -exec rm -rf {} +
  cp -r "$SITE/." "$repo/"; touch "$repo/.nojekyll"
  git -C "$repo" add -A
  git -C "$repo" -c user.name="eastfront-bot" -c user.email="eastfront-bot@users.noreply.github.com" \
     commit -q -m "tick $(TZ=Asia/Seoul date '+%F %H:%M KST')" || true
  if GIT_TERMINAL_PROMPT=0 git -C "$repo" push -q origin main 2>&1; then echo "github push OK ($remote)"
  else echo "github push 실패 — 사용자 GitHub 로그인 필요"; rc=1; fi
}

for t in $TARGETS; do
  case "$t" in
    tunnel) publish_tunnel ;;
    brewpage) publish_brewpage ;;
    github) publish_github ;;
  esac
done
exit $rc
