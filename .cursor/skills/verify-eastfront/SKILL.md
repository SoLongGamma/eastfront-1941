---
name: verify-eastfront
description: "Drive the eastfront-1941 CLI wargame (hourly judge tick, order-round pause, spectator maps) against an isolated copy of state. Use to prove a game day, a 14-day round boundary, resume, captures, map render, or that BrewPage publish stays disabled."
---

# Verify eastfront-1941

Eastfront is a short-lived CLI. A user advances the game with `live/tick.py` (one real hour, one game day), reads `live/daylog.md` and the spectator page, and resumes a paused order round with `live/resume.sh`. There is no long-lived app server to keep up. Each drive is a command against an isolated copy of the tree. The checkout's `live/state.json` is the running game: hash it, copy it once, never write it.

The helper is `.cursor/skills/verify-eastfront/scripts/eastfront-verify`. It must be executable. Invoke it by that path, from anywhere, after exporting `EASTFRONT_VERIFY_RUN`.

Publish to BrewPage is disabled for every command this skill runs. `tick.py --no-publish` is the gate. The isolated copy's `resume.sh` is patched at launch so its site rebuild also passes `--no-publish`. The checkout's `resume.sh` and `publish.sh` are not modified. A `curl` shim is first on `PATH` during drives; any real HTTP client invocation appends to the run's `network.log` and fails the command.

## Launch

From an empty run directory the helper copies the engine, the Natural Earth files, and the checkout's `live/state.json`, `strategy.json`, and `plans/` into the instance. That copy is the seed. It does not migrate a database. Ready means the copy loads, `engine` is `judge`, and the clock prints.

```bash
chmod +x .cursor/skills/verify-eastfront/scripts/eastfront-verify
.cursor/skills/verify-eastfront/scripts/eastfront-verify launch
```

`launch` prints one `export EASTFRONT_VERIFY_RUN=/tmp/eastfront-verify/<id>` line. Export it in the same shell. It then prints:

```text
ready <YYYY-MM-DD> hour=<0-23> paused=<True|False> status=<status> engine=judge instance=<path>
```

On the committed seed that clock is `1941-09-05 hour=0 paused=False status=진행`. Launch refuses to replace an instance that already exists. Teardown is `eastfront-verify cleanup` (see Cleanup). Requires `$REPO/.venv/bin/python` and the map font directory below.

## Doctor

Run this before the first drive and again after any failed drive. It does not advance the clock.

```bash
.cursor/skills/verify-eastfront/scripts/eastfront-verify doctor
```

Exit 0 prints one line starting with `ok`, including `engine=judge`, `source_state=unchanged`, `network=silent`, `fonts=ok`, and `publish=disabled`. The instance `live/state.json` must not be the checkout file. The checkout `live/state.json` sha256 must still match the hash saved at launch. The curl shim must be the `curl` on `PATH`. `live/.publish/brewpage.json` must be absent. `live/render.py` must be able to see at least one `.ttf` in `/usr/share/fonts/truetype/sand-box/google/Nanum Gothic/`. The instance `resume.sh` must contain `--no-publish`; the checkout `resume.sh` must not contain `--site-only --no-publish`.

Anything else is not worth driving. If doctor fails because the instance is gone, launch again. Do not point the helper at the checkout's `live/` directory.

## Drive

Harness: `eastfront-verify`. Recipes and expected output live in `features/`. Start each feature from a fresh launch unless that feature's preconditions say to continue an instance. Always run doctor first.

```bash
.cursor/skills/verify-eastfront/scripts/eastfront-verify show-clock
.cursor/skills/verify-eastfront/scripts/eastfront-verify tick --evidence <feature-id>
.cursor/skills/verify-eastfront/scripts/eastfront-verify maps --evidence <feature-id>
.cursor/skills/verify-eastfront/scripts/eastfront-verify resume auto --evidence <feature-id>
.cursor/skills/verify-eastfront/scripts/eastfront-verify captures --evidence <feature-id>
.cursor/skills/verify-eastfront/scripts/eastfront-verify publish-skip --evidence <feature-id>
```

`tick` runs `live/tick.py --force --no-publish` inside the instance. `--force` is required so a same-hour `last_slot` does not no-op. `maps` runs `live/render.py all` and `live/build_site.py` without moving the clock. `resume` runs the instance's patched `resume.sh`. `publish-skip` runs `live/tick.py --site-only --no-publish` and does not execute `publish.sh`.

Every drive fails if `network.log` grows, if `brewpage.json` appears, or if the checkout `state.json` hash changes.

## Evidence

Proof artifacts go under `$EASTFRONT_VERIFY_RUN/evidence/<feature-id>/`. Capture the command output and the resulting state, not only a final file.

- CLI proof is the helper's stdout, stderr, and exit code (`tick.stdout.txt`, `tick.stderr.txt`, `summary.txt`, or the matching resume files).
- State proof is a second read: `show-clock`, the new `live/plans/YYYY-MM-DD.json`, the appended `live/daylog.md` line, and `captures.json` when the feature is captures.
- Publish proof is an empty `network.log` plus the absence of `live/.publish/brewpage.json`. Do not treat the flag name `--no-publish` as proof by itself; the shim records a real `curl` if `publish.sh` runs.
- Map proof is `maps.txt` (byte sizes) and a copy of `site/index.html`.
- Record the feature id in `summary.txt`.

`publish.sh` has no dry-run that skips the network. `${PUBLISH_TARGETS:-brewpage}` still uploads when the variable is empty. Verification never executes `publish.sh`. The safe path is `--no-publish`, checked by the empty network log.

## Cleanup

```bash
.cursor/skills/verify-eastfront/scripts/eastfront-verify cleanup
```

This kills only pids recorded in `$EASTFRONT_VERIFY_RUN/pids/` (the helper does not background processes today) and deletes the instance directory and the curl shim. It does not delete `$EASTFRONT_VERIFY_RUN/evidence/`. It does not signal processes by name. After cleanup, `doctor` must fail because the instance is gone, and the evidence directory must still contain the proof files.

Run cleanup after a failed drive too, so a broken tick does not leave an instance that the next launch refuses to replace. Use a new `EASTFRONT_VERIFY_RUN` for the next attempt, or cleanup first and launch again with the same variable unset.

## Helpers

One script: `.cursor/skills/verify-eastfront/scripts/eastfront-verify`.

```bash
chmod +x .cursor/skills/verify-eastfront/scripts/eastfront-verify
.cursor/skills/verify-eastfront/scripts/eastfront-verify launch
export EASTFRONT_VERIFY_RUN=/tmp/eastfront-verify/<id>   # the line launch printed
.cursor/skills/verify-eastfront/scripts/eastfront-verify doctor
.cursor/skills/verify-eastfront/scripts/eastfront-verify show-clock
.cursor/skills/verify-eastfront/scripts/eastfront-verify tick --evidence judge-day
.cursor/skills/verify-eastfront/scripts/eastfront-verify maps --evidence spectator-maps
.cursor/skills/verify-eastfront/scripts/eastfront-verify resume auto --evidence resume-orders
.cursor/skills/verify-eastfront/scripts/eastfront-verify captures --evidence captures
.cursor/skills/verify-eastfront/scripts/eastfront-verify publish-skip --evidence publish-skip
.cursor/skills/verify-eastfront/scripts/eastfront-verify cleanup
```

Optional `EASTFRONT_REPO` overrides the checkout used as the read-only seed. The default is the repository that contains this script.
