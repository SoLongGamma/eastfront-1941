# Round boundary

A round boundary pauses the game after the judged day, writes three axis briefs, and writes `live/digest.md` for the referee. The next orders are collected until someone resumes.

## Sub-features

- `boundary-pause` sets paused and status `명령 대기` after the boundary day is judged.
- `boundary-flag` writes `live/awaiting_orders.json` with the round, brief paths, and digest path.
- `boundary-briefs` writes one brief per axis.
- `boundary-digest` writes `live/digest.md` with the capture line.

## How to get to it (user POV)

- Let the hourly ticker judge the boundary date. With `round_anchor` `1941-08-23` and `round_days` 14, the next boundary after the seed is the judgment of `1941-09-06`.
- Run `live/tick.py` on that date (two forced ticks from the seed: `1941-09-05`, then `1941-09-06`).

## Driving it with eastfront-verify

Preconditions:

- Fresh launch at `1941-09-05`, not an instance that already judged that day.
- `eastfront-verify doctor` prints `ok`, `paused=False`, and `publish=disabled`.
- Instance `live/strategy.json` still has `"round_anchor": "1941-08-23"` and `"round_days": 14`.

- **Judge the day before the boundary.** Run `eastfront-verify tick --evidence round-boundary`. Exit code `0`. `eastfront-verify show-clock` prints `1941-09-06 hour=0 paused=False status=진행`.
- **Judge the boundary day.** Run `eastfront-verify tick --evidence round-boundary` again. Exit code `0`. `show-clock` prints `1941-09-07 hour=0 paused=True status=명령 대기`.
- **Read the flag.** Instance `live/awaiting_orders.json` contains `"boundary": "1941-09-06 24:00"` and a `digest` path ending in `digest.md`.
- **Read the briefs.** The three paths named in that JSON exist. Each file contains `결산` and `노획(게임추정)`.
- **Read the digest.** Instance `live/digest.md` contains `심판 다이제스트` and `노획(게임추정)`. Its size is at most 4000 bytes.
- **Confirm isolation.** `evidence/round-boundary/network.log` is empty and `summary.txt` contains `network=silent`.

## Gotchas

- The boundary test is the date that just finished (`1941-09-06`), not the clock after the tick (`1941-09-07`).
- Both ticks must use `--force`. The helper does. A second tick without it no-ops in the same hour.
- Starting from a clock that is already past `1941-09-06` does not revisit this boundary. Report that unmet precondition.
- Briefs and the digest are written only on the boundary tick. The first tick's evidence is the same directory and is overwritten; keep the second tick's `summary.txt` as the proof.
