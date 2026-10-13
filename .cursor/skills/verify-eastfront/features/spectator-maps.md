# Spectator maps

Spectator maps lets an operator rebuild the situation PNGs and the local spectator page from the current game state without advancing the clock.

## Sub-features

- `maps-render` writes the theater, operational, and tactical PNGs.
- `maps-page` writes `live/site/index.html` titled for the current clock.
- `maps-hold-clock` leaves the clock and pause flag unchanged.

## How to get to it (user POV)

- Run `live/render.py all`, then `live/build_site.py`.
- A normal judge tick also refreshes the same page. That tick is [Judge one day](./judge-day.md), not this entry.

## Driving it with eastfront-verify

Preconditions:

- Fresh launch. `eastfront-verify doctor` prints `ok` and `fonts=ok`.
- Note the clock with `eastfront-verify show-clock`.

- **Render and build.** Run `eastfront-verify maps --evidence spectator-maps`. Exit code `0`. Stdout starts with `maps_ok` and repeats the same clock line.
- **Check the files.** `evidence/spectator-maps/maps.txt` lists `theater.png`, `tactical_north.png`, `tactical_center.png`, `tactical_south.png`, `operational_north.png`, `operational_center.png`, and `operational_south.png`, each with a size greater than 1000.
- **Check the page.** `evidence/spectator-maps/index.html` contains `동부전선 1941` and the clock text from `show-clock` with dots in place of dashes (the seed page contains `1941.9.5`).
- **Confirm the clock.** `eastfront-verify show-clock` prints the same line as before the command.
- **Confirm isolation.** `evidence/spectator-maps/network.log` is empty.

## Gotchas

- `live/render.py` reads fonts only from `/usr/share/fonts/truetype/sand-box/google/Nanum Gothic/`. If doctor does not print `fonts=ok`, stop. Do not retarget the renderer. `findfont` warnings about bold or heavy weights are not a failure when the command exits `0`.
- A judge tick also writes these files, but that is a different entry point. Do not mark this feature verified because a tick happened to render.
- The page clock uses `1941.9.5` (no leading zero on the month or day), not `1941-09-05`.
