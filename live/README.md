# 동부전선 1941 라이브 — 인프라

## ★ 현재 운영 모델 (2026-10-11 23:50 KST~): 실시간 1시간 = 게임 1일, 14일마다 명령 라운드, 절차 판정
- **주기**: `live/ticker.conf` `TICK_PERIOD=3600`, `TICK_OFFSET=2` → `run_ticker.sh` 가 매시 정각 :00:02 에 `tick.py` 실행(틱 1회 = 게임 1일).
  멱등 키 `last_slot` = 그 시간 슬롯(`YYYY-MM-DDTHH:00+09:00`, TICK_PERIOD 단위 내림). 놓친 시간은 따라잡지 않음. `--force` 는 무시(테스트용).
- **명령 라운드**: `strategy.json` `round_anchor 1941-08-23` + `round_days 14` → 경계 9.6, 9.20, 10.4, 10.18 … (각 24:00, 실시간 14시간마다).
  경계 판정 직후 일시정지 + `awaiting_orders.json` + 브리핑 `briefs/roundN-{north,center,south}.md`(각 < 2 KB) + **`digest.md`(< 4 KB)**.
  `await_timeout_min 120`: 2시간 안에 `resume.sh auto` 가 없으면 다음 정시 틱이 기존 명령·전략으로 자동 재개.
- **심판(LLM)은 `digest.md` + 해당 라운드 briefs + `strategy.json` 만 읽는다. `state.json`·`state.md` 는 읽지 않는다(토큰 절약).**
  digest = 게임 날짜·상태·다음 경계(실시간 추정), 축별 태세·단계/목표 진척·14일 전선 변화(독 통제 km², 게임 추정)·주요 사건·손실·소련 태세, 기갑 전용 현황.
  수동 생성: `.venv/bin/python live/digest.py [--print]`. 명령은 `strategy.json` 수정 → `live/resume.sh auto`.
- 판정 규칙(judge.py, 변경 없음): `state.engine = "judge"` → `tick.py` 는 틱마다 게임 하루를 진행한다.
  1. `judge.py` 가 그날 계획 `plans/YYYY-MM-DD.json` 을 생성(이미 있으면 재사용 → 멱등·크래시 안전). LLM 없음.
     축마다 `1d20 + mod`(strategy.json, 1~20 자름) → 1~5 불리 · 6~15 기본 · 16~20 유리. dice 항목에 `raw`, `mod`, `posture`, `objective` 기록.
  2. 기존 plan 스키마 그대로(키프레임 12시=이벤트, 24시=전선·부대·화살표·손실·상황) + `judge_state`(단계·진척·점령·전용 상태).
  3. 전선 이동: 목표/섹터 중심 가우시안 가중 변위(소련 쪽 법선+목표 방향), 태세별 km — offensive 유리 14~26/기본 3~9/불리 −3~−8,
     limited 4~8/0~3/−2~−5, hold 2~5/±1/−2~−5, defend 0~2/±0.5/−1~−4. 바다 진입 금지, 주요 하천(드네프르·남부크·돈·도네츠·드네스트르·쿠반·테레크)
     도하는 유리일 때만(아니면 강안 정지), 축 경계점 고정, 자기교차·무효 다각형이면 1/2·1/4로 줄여 재시도 후 포기. 부대·화살표는 가까운 전선 변위를 따름.
  4. 목표 진척: 유리 +2 · 기본 +1 · 불리 −1, `resist` 이상 + 목표가 독일 통제/전선 15km 이내면 "장악". 단계 목표 전부 장악 → 다음 단계.
  5. 모든 지도(전체·전역·전술) 매 틱 렌더(측정 ≈3초/틱). 전체도는 매주(일요일 00시)·라운드 경계마다 maps_archive 보관.
  6. 일일 로그: `live/daylog.md` 추가. 이벤트는 state 에 최근 600~800건만, 오래된 것은 `events_archive.jsonl`. 스냅숏은 최근 300개만.
- **태세·목표 설정: `live/strategy.json`** (심판이 라운드 사이 수정, 매 틱 다시 읽음)
  ```
  {round_anchor: "1941-08-23", round_days: 14, await_timeout_min: 120,
   axes: {north|center|south: {posture: offensive|limited|hold, summary, su_posture,
          sectors: [{name, lon, lat, w}]            # hold/limited 국지 판정 위치(가중치 w)
          objectives: [{name, lon, lat, resist}]     # (선택) 단일 목표 목록
          stages: [{name, objectives:[...], defend?}]# (선택) 단계식 목표(남부)
          mod: [{from: 날짜, mod: 정수}]              # 주사위 보정(날짜별 계단)
          override: {until: 날짜, posture, summary, sectors|objectives}}},  # until 까지 우선(턴9 명령)
   transfers: [{unit, name, from, depart, arrive}]}  # 기갑 전용: depart 에 지도에서 빠지고 arrive 에 남부 주공 후방 등장
  ```
  시드(사용자 신 독일 전략): 북·중부 hold(보병 고수·견제), 남부 offensive 5단계(벨트 정리→드네프르 도하→돈바스→로스토프·마이코프-그로즈니→방어선),
  남부 증원 보너스 8.31 +1 · 9.7 +2 · 9.14 +3(상한), 3기갑(8.24→8.31)·2기갑(8.28→9.7)·56기갑(8.31→9.10)·41기갑(9.4→9.14) 남부 전용.
  8.23 까지는 턴9 명령(override, 전 축 limited).
- **명령 라운드 상세**: 게임 `round_anchor`(1941-08-23) 24:00, 이후 `round_days`(14)일마다 그날 판정 직후
  `live/awaiting_orders.json` {round, range, boundary, briefs, digest, since_real, auto_resume_real, resume_cmd} 생성,
  `state.paused=true`, `status="명령 대기"`(사이트 배지), 브리핑 `live/briefs/roundN-{north,center,south}.md`(라운드 결산·전망·OKH/히틀러·스타프카·[명령]3·[요청]1·[리스크]1).
  심판은 명령을 받아 `strategy.json` 수정 후 **`live/resume.sh auto`** → 플래그 삭제·재개.
  await_timeout_min(120분) 안에 재개가 없으면 다음 틱이 **자동 재개**(기존 명령·전략 유지, 이벤트·daylog 기록).
- `pause.sh` 는 수동 일시정지(자동 재개 없음), `resume.sh` 는 둘 다 해제.
- 이전 1분=1일 모드: `ticker.conf` TICK_PERIOD=60. 구 방식(심판 LLM 이 계획 작성, 15분=6시간): state.engine 을 지우고 `TICK_PERIOD=900 run_ticker.sh start`.
- brewpage 게시는 최소 900초 간격으로 제한(BREWPAGE_MIN_INTERVAL).

---
## (이하 구 방식 문서 — 스키마는 여전히 유효)

실시간 **1시간 = 게임 1일**, **15분 = 게임 6시간(1 페이즈)**. 라이브 시작 게임 시각 1941-07-06 00:00 (턴3 명령).
판정(LLM 심판)은 하루 단위 계획 파일로 미리 쓰고, `tick.py`(LLM 없음)가 15분마다 한 페이즈씩 재생한다.

## 파일 구성
```
live/
  state.json            기계 판독용 게임 상태 (아래 스키마)
  plans/YYYY-MM-DD.json 일일 판정 계획 (심판이 작성) · examples/make_plan_1941-07-06.py 예시 생성기
  common.py             경로·시계·원자적 저장·잠금
  seed.py               state.md 7.5 상황 + draw_map.py DATA BLOCK → state.json 초기화 (--force)
  apply_plan.py         계획 검증(validate)·설치(install)·수동 병합(merge)
  tick.py               틱 엔진 (1 페이즈 진행 → 지도 → 사이트 → 게시)
  render.py             지도 렌더러 (draw_map.py 리팩터; 전술/전역/전체)
  build_site.py         site/index.html + site/state.json 생성
  site/                 공개 정적 사이트 (index.html, state.json, maps/*.png)
  publish.sh            게시 (tunnel / brewpage / github)
  tunnel.sh, serve.py   로컬 정적 서버 + Cloudflare Quick Tunnel (무로그인 공개 URL)
  run_ticker.sh         15분 정렬 스케줄러 (start|stop|status|once)
  pause.sh / resume.sh  일시정지 / 재개(+모드 auto|broadcast)
  snapshots/            틱마다 state 스냅숏 · maps_archive/ 전역도(일)·전체도 보관
  ticker.log            스케줄러·틱 로그
```
실행 파이썬: `/workspace/eastfront/.venv/bin/python` (matplotlib, shapely, pyshp).

## 시계·틱 규칙
- `state.clock = {"date": "1941-07-06", "hour": 0|6|12|18}`. 24시 키프레임을 적용하면 다음 날 00시가 된다.
- 틱 1회 = 다음 키프레임 1개. **정시 정렬**: 실시간 :15→06시, :30→12시, :45→18시, :00→24시(하루 끝).
  1슬롯 밀리면 2페이즈로 따라잡고, 앞서 있으면 맞는 슬롯까지 대기(최대 3슬롯, 로그 "정시 정렬 대기").
  `--force` / `--no-align` 은 정렬 무시하고 1페이즈 진행(테스트용).
- 그날 계획이 없거나 검증 실패면 **시계 정지 + "판정 대기" 이벤트 1회**(중복 기록 없음). 계획이 생기면 다음 틱부터 재개.
- 멱등성: 같은 15분 슬롯(KST) 재호출은 무시(`last_slot`), 키프레임은 `"날짜@시각"`(`applied`)로 1회만 적용,
  `fcntl` 잠금으로 동시 실행 차단, state.json 원자적 저장.
- 지도: 전술도 3장(축별)은 진행된 틱마다, 전역도 3장은 하루 끝(24시)마다, 전체도는 게임 24일마다(+시드 때) 재생성.

## state.json 스키마 (주요 필드)
| 필드 | 내용 |
|---|---|
| `clock` | `{date, hour}` 게임 시계 |
| `paused` / `mode` | 일시정지 여부 / `"auto"` 또는 `"broadcast"` (사이트에 ● 방송 중 배지) |
| `status` | `진행` / `판정 대기` / `일시정지` |
| `needs_plan` | 아직 계획이 없는 가장 이른 날짜 (심판은 이 날짜를 작성) |
| `fronts` | `{north|center|south: [{id, style: solid|loose, pts: [[lon,lat],...]}]}` 북→남 연속, 축 경계점 공유 |
| `german_closure` | 독일 통제 다각형을 닫는 점들(전선 남단→서쪽→리가만→전선 북단) |
| `pockets` | `[{id, axis, name, lon, lat, rx, ry, label, lx, ly, status}]` 타원(도 단위) |
| `units` | `[{id, name, side: de|su, axis, lon, lat, strength(0~100|null), kind: armor|mech|inf|garrison|hq, echelon: group|army|corps, dx, dy}]` dx/dy = 라벨 오프셋(pt) |
| `arrows` | `[{id, axis, side: de|su|esc, pts, unit(연결 부대 id), goal(전술도용 짧은 목표), goal_off, label, lx, ly}]` |
| `forts` | `[{id, axis, name, pts}]` 요새지대 |
| `orders` | `{axis: {turn, received, de: [..], su: [..]}}` 현재 유효 명령 요약 |
| `losses` | `{note, axis: {de_pct, su_pct, de_text, su_text}}` — **게임 추정치** |
| `situation` | `{axis: 한 문단}` |
| `events` | `[{game_time "1941.7.6 18:00", axis: north|center|south|all, kind, text(한 줄), real_time}]` |
| `dice` | `[{date, rolls: [...]}]` 일별 주사위 기록 · `day` 오늘 주사위 · `last_day` 전일 판정 요약 |
| `views` | `{tactical|operational: {axis: [lon_min, lon_max, lat_min, lat_max]}}` 지도 범위 |
| `maps` | 렌더 기록(`version` = 이미지 캐시버스터) |

## 일일 계획(plan) 스키마 — `plans/YYYY-MM-DD.json`
```json
{
  "schema": 1,
  "date": "1941-07-07",
  "turn": 3,
  "referee": "판정자/메모",
  "dice": [ {"axis": "north", "roll": 14, "band": "기본", "note": "근거"} , ... 축마다 1개 ],
  "summary": {"north": "하루 판정 한 줄", "center": "...", "south": "..."},
  "keyframes": [
    {"hour": 6,  "events": [{"axis": "north", "text": "한국어 한 줄(≤220자)"}],
                 "fronts": {"north": [ {id, style, pts}, ... ]},
                 "units":   [{"id": "de-41pz", "lon": 28.4, "lat": 57.5, "strength": 80}],
                 "pockets": [{"id": "p-minsk", "rx": 0.5, "ry": 0.25}],
                 "arrows":  [{"id": "a-41pz", "pts": [[..],[..]]}],
                 "forts":   [],
                 "losses":  {"north": {"de_pct": 14, "su_pct": 35, "de_text": "...", "su_text": "..."}},
                 "situation": {"north": "..."},
                 "orders": {"north": {"de": ["..."], "su": ["..."]}},
                 "views": {"tactical": {"north": [26, 31, 56.3, 58.9]}} },
    {"hour": 12, ...}, {"hour": 18, ...}, {"hour": 24, ...}
  ]
}
```
규칙
- `hour` ∈ 6/12/18/24, 오름차순, **24 필수**. 빠진 시각은 다음 키프레임 쪽으로 선형 보간(부대·포위망 위치·전투력, 세그먼트 id가 같은 전선).
- 모든 변경 키는 선택. `fronts.<axis>` 는 그 축 세그먼트 **전체 교체**(축 경계점은 이웃 축과 맞출 것).
- `units/pockets/arrows/forts` 는 id 기준 **upsert**(부분 필드만 주면 갱신), 신규 항목은 필수 필드 포함, `{"id": "...", "remove": true}` 로 삭제.
  신규 unit 필수: name, side, axis, lon, lat, kind, echelon. 신규 pocket: axis, name, lon, lat, rx, ry. 신규 arrow: axis, side, pts.
- `dice.roll` 1~20 정수, `band` 는 규칙과 일치해야 함(1~5 불리, 6~15 기본, 16~20 유리). 축마다 1개 권장(없으면 경고).
- 좌표 [lon, lat], 범위 lon 14~45 / lat 40~66. 이벤트 text 는 개행 없는 한 줄.
- 주사위는 실제로 굴려 기록: `shuf -i 1-20 -n 1` (축마다).
- `summary` 는 사이트에 그날 24시 이후에만 공개된다(스포일러 방지). 주사위는 06시부터 표시.

설치 절차 (심판 루틴용)
```bash
PY=/workspace/eastfront/.venv/bin/python
D=$($PY -c 'import json;print(json.load(open("/workspace/eastfront/live/state.json"))["needs_plan"])')
# ... state.json + state.md 읽고, 주사위 굴리고, /tmp/plan.json 작성 ...
$PY /workspace/eastfront/live/apply_plan.py validate /tmp/plan.json   # 오류 시 exit 1
$PY /workspace/eastfront/live/apply_plan.py install  /tmp/plan.json   # → plans/$D.json
```
권장: 심판은 매시 :05 경 실행해 `needs_plan`(보통 다음 날)을 작성 → 다음 :15 틱 전에 여유 있게 도착.
`apply_plan.py merge <plan> --hour H` 는 키프레임 하나를 즉시 state 에 병합(수동 복구용; tick 이 같은 키를 다시 적용하지 않음).

## 운영
```bash
live/run_ticker.sh start|stop|status     # 15분 루프 (setsid+nohup, 로그 live/ticker.log, PID live/ticker.pid)
live/pause.sh [사유]                      # 일시정지(시계·부대 정지, 사이트 배지 즉시 반영)
live/resume.sh [auto|broadcast]          # 재개, 모드 전환(broadcast → ● 방송 중)
live/tick.py --site-only                 # 진행 없이 사이트만 재생성+게시
live/tick.py --render-all --site-only    # 지도 전부 재생성
live/tunnel.sh status|start|stop|url     # 공개 URL 상태
```
cron 이 있는 환경이면 루프 대신: `*/15 * * * * /workspace/eastfront/live/run_ticker.sh once`

## 게시 (publish.sh)
- `tunnel` (기본, 동작 중): `serve.py`(127.0.0.1:8941, site/ 만, 디렉터리 목록 금지) + Cloudflare Quick Tunnel.
  계정 불필요. 사이트 파일을 그대로 서비스하므로 틱 즉시 반영. **터널 프로세스가 재시작되면 URL이 바뀜**
  (`.publish/tunnel_url`, 변경 이력 `tunnel_urls.log`). publish 가 매 틱 생존 확인·재시작.
- `brewpage`: 무가입 사이트 호스팅(같은 URL 갱신, 매 게시 TTL 30일 연장). 현재 이 박스 IP 가 BrewPage 에서
  `403 Too many failed attempts` 로 차단됨 → 6시간 백오프 후 자동 재시도. 성공하면 `.publish/brewpage.json`(소유 토큰, 600) 생성.
- `github`: 고정 URL 이 필요하면 GitHub Pages. 사용자가 박스에서 `gh auth login`(SoLongGamma) 후
  저장소(예: `SoLongGamma/eastfront-live`, Pages: main / root) 생성 → `echo https://github.com/SoLongGamma/eastfront-live.git > live/.publish/github_remote`
  (그리고 `gh auth setup-git`). 이후 매 틱 자동 push → `https://solonggamma.github.io/eastfront-live/`.
