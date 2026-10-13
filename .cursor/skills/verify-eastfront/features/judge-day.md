# Judge one day

Judge one day lets an operator advance the Eastern Front clock by one game day. The procedural judge writes that day's plan, appends a daylog line, and leaves the game running when the day is not a round boundary.

## Sub-features

- `judge-clock` moves the clock from the seed date to the next date at hour 0.
- `judge-plan` writes `live/plans/<seed-date>.json` for that day.
- `judge-daylog` appends one line naming that date and the three dice.
- `judge-stay-running` leaves the game unpaused when the judged date is not a 14-day boundary.

## How to get to it (user POV)

- Run `live/tick.py` once (the hourly ticker's one-day step).
- Run `live/run_ticker.sh once`, which is the same tick.

## Driving it with eastfront-verify

Preconditions:

- Fresh launch. `eastfront-verify doctor` prints `ok` and `clock` `1941-09-05 hour=0 paused=False`.
- The instance has no `live/plans/1941-09-05.json`.
- `source_state=unchanged` and `publish=disabled`.

- **Read the clock.** Run `eastfront-verify show-clock`. The line is `1941-09-05 hour=0 paused=False status=진행`.
- **Judge the day.** Run `eastfront-verify tick --evidence judge-day`. Exit code `0`. Stdout contains `tick_rc=0`, `clock_before=1941-09-05 hour=0 paused=False status=진행`, and `clock_after=1941-09-06 hour=0 paused=False status=진행`.
- **Confirm the plan.** Read the instance file `live/plans/1941-09-05.json`. It contains `"date": "1941-09-05"` and `"generator": "judge.py"`.
- **Confirm the daylog.** The last line of the instance `live/daylog.md` contains `1941.09.05` and `주사위`.
- **Confirm isolation.** `evidence/judge-day/summary.txt` contains `source_state=unchanged` and `network=silent`. The checkout `live/state.json` hash still matches `evidence/judge-day/source-state.sha256`.

## Gotchas

- Without `--force`, a tick whose `last_slot` is already the current hour returns success and does not move the clock. The helper always passes `--force`.
- If `live/plans/1941-09-05.json` already exists in the seed, the tick replays that file instead of judging a new day. Stop and report that precondition; do not delete the checkout plan.
- `1941-09-05` is not a round boundary. A pause on this tick means the run did not start from the seed clock.
- The checkout `live/state.json` is only hashed and copied. A changed hash fails the drive.
- Map render may print `findfont` warnings about NanumGothic bold or heavy weights. Exit code `0` and `tick_rc=0` still pass. A missing font directory does not: doctor fails first.
