#!/usr/bin/env python3
"""전선 반대편으로 넘어가는 부대 이동을 줄이는 side_guard. state.json 은 읽지도 쓰지도 않는다.

  .venv/bin/python live/test_side_guard.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import judge as J

# 동→서가 아니라 서→동 전선. 왼쪽(북쪽)이 소련, 남쪽이 독일.
CHAIN = [(28.0, 54.0), (32.0, 54.0)]


def check(cond, msg):
    if not cond:
        raise SystemExit("FAIL: " + msg)


def main():
    de = {"id": "de-x", "side": "de", "axis": "center", "lon": 30.0, "lat": 53.6}
    su = {"id": "su-x", "side": "su", "axis": "center", "lon": 30.0, "lat": 54.4}
    check(J.front_side_km(CHAIN, (30.0, 53.6)) < -40, "south of an eastbound front is the German side")
    check(J.front_side_km(CHAIN, (30.0, 54.4)) > 40, "north of an eastbound front is the Soviet side")

    dx, dy = J.side_guard(0.0, 0.8, de, CHAIN, pocketed=False)
    check((dx, dy) == (0.0, 0.4), "a German leap across the front is halved until it stops on the line")
    end = J.front_side_km(CHAIN, (de["lon"] + dx, de["lat"] + dy))
    check(end <= 0.05, "the guarded German step does not finish on the Soviet side")

    dx, dy = J.side_guard(0.0, -0.8, su, CHAIN, pocketed=False)
    check((dx, dy) == (0.0, -0.4), "a Soviet leap across the front is halved until it stops on the line")
    end = J.front_side_km(CHAIN, (su["lon"] + dx, su["lat"] + dy))
    check(end >= -0.05, "the guarded Soviet step does not finish on the German side")

    dx, dy = J.side_guard(0.0, 0.2, {"id": "de-near", "side": "de", "lon": 30.0, "lat": 53.98}, CHAIN)
    check((dx, dy) == (0.0, 0.0), "a step that still crosses at one quarter is dropped")

    dx, dy = J.side_guard(0.3, 0.0, de, CHAIN)
    check((dx, dy) == (0.3, 0.0), "sliding along the friendly side is not shrunk")

    dx, dy = J.side_guard(0.05, 0.0, de, CHAIN)
    check(dx == 0.05, "a short move that stays friendly keeps scale 1")

    dx, dy = J.side_guard(0.0, 0.8, de, CHAIN, pocketed=True)
    check((dx, dy) == (0.0, 0.8), "a pocketed unit keeps the full step")

    st = {"judge": {"pockets": {"p1": {"units": ["su-trap"], "pocket": {}}}}, "pockets": [
        {"id": "p-ell", "lon": 23.7, "lat": 52.1, "rx": 0.3, "ry": 0.2}]}
    check(J.pocketed_unit(st, {"id": "su-trap", "lon": 0, "lat": 0}, st["judge"]), "judge pocket roster counts")
    check(J.pocketed_unit(st, {"id": "other", "lon": 23.7, "lat": 52.1}, st["judge"]), "ellipse pockets count")
    check(not J.pocketed_unit(st, {"id": "other", "lon": 30, "lat": 54}, st["judge"]), "a unit outside pockets is not pocketed")
    print("side_guard ok")


if __name__ == "__main__":
    main()
