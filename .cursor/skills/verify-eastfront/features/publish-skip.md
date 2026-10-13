# Publish skip

Publish skip rebuilds the local spectator page the way an operator would before a public upload, and proves the upload did not run. BrewPage is a live public site. Verification must not call it.

## Sub-features

- `publish-local` rebuilds `live/site/index.html` without moving the clock.
- `publish-no-http` leaves the network log empty and does not write `live/.publish/brewpage.json`.
- `publish-script-intact` leaves `live/publish.sh` still aimed at BrewPage, and does not execute it.

## How to get to it (user POV)

- An operator publishes with `live/publish.sh`, which uploads to BrewPage by default.
- The verification stand-in for that step is `live/tick.py --site-only --no-publish`, which refreshes the local page and skips the upload.

## Driving it with eastfront-verify

Preconditions:

- Fresh launch or any healthy instance. `eastfront-verify doctor` prints `publish=disabled` and `network=silent`.
- Note the clock with `eastfront-verify show-clock`.

- **Rebuild without uploading.** Run `eastfront-verify publish-skip --evidence publish-skip`. Exit code `0`. Stdout contains `publish_skip=ok`, `network=silent`, and `brewpage=absent`.
- **Confirm the page.** Instance `live/site/index.html` exists and contains `동부전선 1941`.
- **Confirm the clock.** `eastfront-verify show-clock` prints the same line as before the command.
- **Confirm no upload.** `evidence/publish-skip/network.log` is empty. Instance `live/.publish/brewpage.json` does not exist. `evidence/publish-skip/publish-sh-not-executed.txt` exists. Instance `live/publish.sh` still contains `https://brewpage.app`.
- **Confirm the checkout.** The checkout `live/publish.sh` and `live/state.json` are unchanged.

## Gotchas

- Do not run `live/publish.sh` to see what it skips. It has no dry-run. An empty `PUBLISH_TARGETS` still selects BrewPage because the script uses `${PUBLISH_TARGETS:-brewpage}`.
- `--no-publish` is not proof by itself. The curl shim must stay first on `PATH`, and `network.log` must stay empty.
- The checkout `resume.sh` would publish after a resume. This recipe does not resume. [Resume orders](./resume-orders.md) uses the patched instance script.
