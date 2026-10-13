#!/usr/bin/env python3
"""노획 건조 실행. 기존 state.json 은 captures 없이 0으로 읽고, 유리한 전진·포위·소련 측 역습에서 노획이 난다.

  .venv/bin/python live/test_captures.py
"""
import os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import apply_plan as AP
import judge as J
from common import load_state, STATE


def check(cond, msg):
    if not cond:
        raise SystemExit("FAIL: " + msg)


def main():
    st = load_state()
    check("captures" not in st, "committed state.json should not need a captures key")
    blank = J.captures_of(st)
    check(all(blank[a][s][k] == 0 for a in blank for s in ("de", "su") for k in ("trucks", "tanks")),
          "missing captures must read as zero")
    print("state load", STATE, "clock", st["clock"]["date"], "captures default 0")

    ger = J.haul_for({"band": "유리", "km": 16, "posture": "offensive"}, rng=random.Random(0))
    check(ger["de"]["trucks"] >= 38 and ger["de"]["tanks"] >= 2, "favorable armored advance captures Soviet trucks and tanks")
    check(ger["su"]["trucks"] == 0 and ger["su"]["tanks"] == 0, "a German success does not hand German vehicles to the Soviets")
    note = J.capture_note(ger, {"de": J.booty_boost(ger["de"]), "su": 0})
    check("노획" in note and len(note) <= 220 and "\n" not in note, "notable capture fits an event line")

    sov = J.haul_for({"band": "불리", "km": 6, "mag": -6.4, "posture": "offensive"}, rng=random.Random(1))
    check(sov["su"]["tanks"] == 1 and sov["su"]["trucks"] >= 9, "a sharp German retreat lets the Soviets take trucks and one panzer")
    check(sov["de"]["trucks"] == 0 and sov["de"]["tanks"] == 0, "the retreating side does not also capture")
    check(sov["su"]["tanks"] < ger["de"]["tanks"] and sov["su"]["trucks"] < ger["de"]["trucks"],
          "1941 Soviet reuse stays smaller than a German haul")
    mild = J.haul_for({"band": "불리", "km": 2, "mag": -2.2, "posture": "limited"}, rng=random.Random(2))
    check(mild["su"]["trucks"] >= 5 and mild["su"]["tanks"] == 0, "a short repulse yields trucks only")

    quiet = J.haul_for({"band": "기본", "km": 0, "mag": 0.2, "posture": "hold"}, rng=random.Random(3))
    check(quiet == {"de": {"trucks": 0, "tanks": 0}, "su": {"trucks": 0, "tanks": 0}}, "a quiet hold day captures nothing")
    Lq = {"de_pct": 40.0, "su_pct": 50.0}
    J.add_capture_losses(Lq, quiet)
    check(Lq == {"de_pct": 40.0, "su_pct": 50.0}, "a zero haul does not touch losses")

    pocket = J.haul_for({"band": "기본", "km": 0, "mag": 0, "posture": "hold"}, closed=True, rng=random.Random(4))
    check(pocket["de"]["trucks"] >= 80 and pocket["de"]["tanks"] >= 6, "closing a pocket captures a depot-sized haul")

    L = {"de_pct": 40.0, "su_pct": 50.0}
    J.add_capture_losses(L, ger)
    check(L["su_pct"] > 50.0 and L["de_pct"] == 40.0, "captured Soviet vehicles count as Soviet losses only")
    check(L["su_veh_lost"]["trucks"] == ger["de"]["trucks"] and L["de_veh_lost"]["tanks"] == 0, "loss tally matches the haul")
    Ls = {"de_pct": 40.0, "su_pct": 55.0}
    J.add_capture_losses(Ls, sov)
    check(Ls["de_pct"] > 40.0 and Ls["su_pct"] == 55.0 and Ls["de_veh_lost"]["tanks"] == 1, "captured German vehicles count as German losses")

    units = [
        {"id": "inf", "axis": "south", "side": "de", "echelon": "army", "kind": "inf", "strength": 90, "lon": 30, "lat": 50},
        {"id": "pz", "axis": "south", "side": "de", "echelon": "corps", "kind": "armor", "strength": 40, "lon": 30, "lat": 50},
    ]
    ops = [{"id": "pz", "strength": 39}]
    check(J.apply_booty_strength(units, ops, "south", "de", ger["de"]) == 1, "a real haul gives +1 strength")
    check(ops == [{"id": "pz", "strength": 40}], "the +1 lands on armor and stops at one point")
    ops100 = [{"id": "pz", "strength": 100}]
    check(J.apply_booty_strength(units, ops100, "south", "de", ger["de"]) == 0 and ops100[0]["strength"] == 100,
          "spare parts and a full strength bar block a second point")

    cum = J.blank_captures()
    cum["south"]["de"] = dict(ger["de"])
    state = {"losses": {"note": "keep"}, "events": []}
    AP.apply_keyframe(state, {"date": "1941-09-05"}, {"hour": 24, "events": [], "captures": cum})
    check(state["captures"]["south"]["de"]["tanks"] == ger["de"]["tanks"], "keyframe writes cumulative captures")
    check(state["losses"]["note"] == "keep", "captures merge leaves the rest of state alone")
    bare = {"losses": {}, "events": []}
    AP.apply_keyframe(bare, {"date": "1941-09-05"}, {"hour": 24, "events": []})
    check("captures" not in bare and J.captures_of(bare)["center"]["su"]["tanks"] == 0, "old keyframes without captures still load")

    logged = {"dice": [
        {"date": "1941-09-01", "rolls": []},
        {"date": "1941-09-02", "rolls": [], "vehicles": {"south": {"de": ger["de"], "su": {"trucks": 0, "tanks": 0}}}},
    ], "captures": cum}
    per = J.sum_vehicles(logged, "south", "1941-09-01", "1941-09-03", False)
    check(per["de"]["trucks"] == ger["de"]["trucks"], "period sum ignores dice rows that predate the field")
    line = J.capture_line(J.captures_of(logged)["south"], per)
    brief = J.brief_capture(logged, "south", "1941-09-01", "1941-09-02")
    check("노획" in line and "노획" in brief and str(ger["de"]["trucks"]) in line, "digest and briefs can see the counts")
    print("haul de", ger["de"], "su-retreat", sov["su"], "pocket", pocket["de"])
    print("digest:", line)

    # 실제 하루 판정. 계획을 저장하지 않는다. 주사위만 유리로 고정해 남부 전진 노획을 확인.
    class HighDice(random.Random):
        def randint(self, a, b):
            if (a, b) == (1, 20):
                return 20
            return random.Random.randint(self, a, b)

    before = os.path.getmtime(STATE)
    old = J.RNG
    J.RNG = HighDice(1)
    try:
        plan = J.make_plan(st, st["clock"]["date"])
    finally:
        J.RNG = old
    check(os.path.getmtime(STATE) == before, "dry-run must not rewrite state.json")
    check("captures" not in st, "make_plan must not mutate the loaded state")
    day = plan["vehicles"]["south"]["de"]
    check(day["trucks"] > 0 and day["tanks"] >= 1, "south favorable day captures Soviet trucks and tanks")
    kf = plan["keyframes"][-1]
    check(kf["captures"]["south"]["de"]["trucks"] == day["trucks"], "plan stores the cumulative count")
    check(kf["losses"]["south"].get("su_veh_lost", {}).get("trucks") == day["trucks"], "those trucks are Soviet losses")
    check("노획" in plan["summary"]["south"], "daylog summary mentions the capture")
    check(any(e.get("kind") == "booty" and "노획" in e["text"] and len(e["text"]) <= 220 for e in kf["events"]),
          "booty event is present")
    errs, _warns = AP.validate(plan, st)
    check(not errs, "plan still validates: " + "; ".join(errs[:4]))
    print("dry-run", plan["date"], "south", day, "ok")


if __name__ == "__main__":
    main()
