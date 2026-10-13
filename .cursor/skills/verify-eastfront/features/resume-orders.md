# Resume orders

Resume orders lets an operator edit `strategy.json` during a pause and continue the game. The pause flag and `awaiting_orders.json` go away, and the status returns to `진행`.

## Sub-features

- `resume-clear` clears the pause and deletes `live/awaiting_orders.json`.
- `resume-strategy` keeps the edited `strategy.json` in place.
- `resume-event` appends a `진행 재개` event.
- `resume-mode` sets mode `auto` when that argument is passed.

## How to get to it (user POV)

- While the site shows `명령 대기`, edit `live/strategy.json`.
- Run `live/resume.sh auto`.

## Driving it with eastfront-verify

Preconditions:

- The instance is paused on a round boundary. Drive [Round boundary](./round-boundary.md) on this same instance first. A fresh seed is not paused, so resume from the seed does not prove this feature.
- `eastfront-verify doctor` prints `paused=True` and `publish=disabled`.
- Instance `live/awaiting_orders.json` exists.

- **Edit orders.** In the instance `live/strategy.json` only, set the north axis `summary` to a string that contains `VERIFY-RESUME`. Do not edit the checkout file.
- **Resume.** Run `eastfront-verify resume auto --evidence resume-orders`. Exit code `0`. Stdout contains `paused=False mode=auto` and `clock_after=` with `paused=False` and `status=진행`.
- **Confirm the flag is gone.** Instance `live/awaiting_orders.json` does not exist. `eastfront-verify show-clock` prints `paused=False status=진행`.
- **Confirm the edit survived.** Instance `live/strategy.json` still contains `VERIFY-RESUME`. The checkout `live/strategy.json` does not.
- **Confirm the event.** Instance `live/state.json` events include the text `진행 재개`.
- **Confirm isolation.** `evidence/resume-orders/network.log` is empty and `summary.txt` contains `network=silent`.

## Gotchas

- The checkout `live/resume.sh` rebuilds the site and would call `publish.sh`. Launch patches only the instance copy to add `--no-publish`. Doctor fails if that patch is missing or if the checkout gained the same patch.
- Resume from a seed that is not paused returns success and does not write `진행 재개`. That is not this feature.
- `resume.sh broadcast` is a different mode. This recipe uses `auto` only.
