# Eastfront verification map

This directory is the maintained source for verifying the user-facing behavior of the eastfront-1941 replay. Read the index before driving, then use the matching feature file as the recipe.

## Baseline preconditions

- Launch an isolated copy with `.cursor/skills/verify-eastfront/scripts/eastfront-verify launch` and export `EASTFRONT_VERIFY_RUN`.
- The seed is the checkout's `live/state.json`, `live/strategy.json`, and `live/plans/`, copied once. The committed clock is `1941-09-05` hour `0`, `engine` `judge`, not paused.
- Run `eastfront-verify doctor` and require `ok`, `source_state=unchanged`, `publish=disabled`, and `fonts=ok`.
- Never drive the checkout's `live/` directory. A running game's `live/state.json` must stay byte-identical to the hash saved at launch.
- Map rendering needs at least one `.ttf` in `/usr/share/fonts/truetype/sand-box/google/Nanum Gothic/`.

## Driving conventions

- Start every recipe from a fresh launch unless its preconditions say to keep the instance.
- Treat every command as literal. Keep flags and evidence ids unchanged.
- Run actions through `eastfront-verify`. Do not call `live/publish.sh`.
- `tick` always passes `--force --no-publish`.
- Restore a fresh instance after a mutation when the next feature needs the baseline clock. Do not remove proof artifacts during cleanup.

## Proof and skip reporting

- Capture the command and the resulting clock, plan, or page, not only the helper's exit code.
- CLI proof includes stdout, stderr, and exit code under `$EASTFRONT_VERIFY_RUN/evidence/<feature-id>/`.
- Mutation proof includes a second read (`show-clock`, the plan file, or `captures.json`).
- Publish proof includes an empty `network.log` and no `live/.publish/brewpage.json`.
- Record the feature id in `summary.txt`.
- Report an unreachable path with the attempted command and the unmet precondition.
- Do not report a skipped entry point as verified through a different path.

## Feature entry contract

Each feature file starts with an H1 title and one paragraph describing the user-visible behavior. It then uses exactly four H2 sections in this order.

1. `Sub-features` lists short IDs with one line for each behavior.
2. `How to get to it (user POV)` lists every user entry point.
3. `Driving it with eastfront-verify` starts with `Preconditions:` and uses labeled bullets that pair each user action with an exact command and observable result.
4. `Gotchas` lists traps that can waste or invalidate a verification run.

Keep implementation details out of the map. Name only user paths, stable handles, required state, commands, and observable proof.

## Features

- [Judge one day](./judge-day.md) advances the clock one game day and writes that day's plan and daylog line.
- [Round boundary](./round-boundary.md) pauses on a 14-day boundary and writes briefs plus `digest.md`.
- [Resume orders](./resume-orders.md) clears the pause after `strategy.json` is edited.
- [Captures](./captures.md) records trucks and tanks taken that day.
- [Spectator maps](./spectator-maps.md) renders the map PNGs and the spectator `index.html`.
- [Publish skip](./publish-skip.md) rebuilds the local page without contacting BrewPage.
