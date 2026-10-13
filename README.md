# eastfront-1941

1941년 동부전선 대체역사 워게임입니다. 실제 1시간마다 게임 하루가 진행됩니다. 아래처럼 가상환경을 만든 뒤 `live/run_ticker.sh`로 틱을 돌리세요. BrewPage 소유 토큰은 `live/.publish/`에만 두며, 그 디렉터리는 git에 올리지 않습니다.

Hobby replay of the 1941 Eastern Front. One real hour advances one game day. Create the virtualenv below, then run `live/run_ticker.sh`. The BrewPage owner token stays in `live/.publish/` and is gitignored.

## Setup / 준비

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

`live/*.sh` uses `.venv/bin/python` at the repo root.

## Run / 실행

```bash
live/run_ticker.sh once     # one game day
live/resume.sh auto         # continue after an order round
```

`live/ticker.conf` sets `TICK_PERIOD=3600` (Asia/Seoul, a few seconds past the hour). `live/judge.py` rolls 1d20 per axis and writes `live/plans/YYYY-MM-DD.json`. Every 14 game days the ticker pauses, writes `live/awaiting_orders.json`, axis briefs, and `live/digest.md`. Edit `live/strategy.json`, then `live/resume.sh`.

`live/publish.sh` can upload `live/site/` to BrewPage. It reads the owner token from `live/.publish/` at runtime. Do not commit that directory.
