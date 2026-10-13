# Captures

Captures lets an operator see how many enemy trucks and tanks each side took on an axis. The counts accumulate in the game state. A notable haul is also named in the daylog.

## Sub-features

- `captures-record` stores trucks and tanks for north, center, and south, for both `de` and `su`.
- `captures-notable` mentions `노획` in the daylog when a side's haul is at least 10 trucks or 1 tank.
- `captures-zero` still writes the three axes when a quiet day takes nothing.

## How to get to it (user POV)

- Run one judge tick, then read the new daylog line and the running state's capture counts.
- On a round boundary, read the same counts in `live/digest.md` and in the axis briefs.

## Driving it with eastfront-verify

Preconditions:

- Fresh launch, then one successful `eastfront-verify tick --evidence captures` so the seed day has been judged. The seed state has no `captures` object.
- `eastfront-verify doctor` prints `ok` and `source_state=unchanged`.

- **Read the counts.** Run `eastfront-verify captures --evidence captures`. Exit code `0`. Stdout is a JSON object with keys `north`, `center`, and `south`. Each has `de` and `su`, and each of those has integer `trucks` and `tanks` greater than or equal to 0.
- **Notable haul.** If stdout contains `notable=True`, it also contains `daylog_mentions_capture=True`, and the instance `live/daylog.md` contains `노획`. The command exits `1` when a notable haul is missing from the daylog.
- **Quiet day.** If stdout contains `notable=False`, the JSON counts are still present and all below the notable threshold. Do not fail the feature for a quiet roll.
- **Second view.** `evidence/captures/captures.json` matches the JSON on stdout.

## Gotchas

- Dice are not seeded. One day can record all zeros. Zeros prove the field was written; they do not prove a battlefield haul.
- Do not force the dice. A quiet day is a valid result.
- Digest and brief wording is proved by [Round boundary](./round-boundary.md), not by this recipe.
- The checkout state has no `captures` key until a tick runs in the instance. The checkout file must remain without that write.
