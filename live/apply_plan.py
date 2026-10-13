#!/usr/bin/env python3
"""일일 판정 계획(plan) 검증·설치·병합.

  apply_plan.py validate <plan.json>            검증만 (오류 시 exit 1)
  apply_plan.py install  <plan.json> [--force]  검증 후 plans/<date>.json 으로 설치
  apply_plan.py merge    <plan.json> --hour H   키프레임 H(6/12/18/24)를 state.json 에 즉시 병합(수동 복구용)
스키마는 live/README.md 참고. tick.py 가 이 모듈의 apply_keyframe()/interpolate_phase() 를 사용한다.
"""
import copy, datetime as dt, json, math, os, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *  # noqa

SIDES = {"de", "su"}
ARROW_SIDES = {"de", "su", "esc"}
KINDS = {"armor", "mech", "inf", "garrison", "hq"}
ECHELONS = {"group", "army", "corps"}
STYLES = {"solid", "loose"}
MAX_EVENT = 220


def band(roll):
    return "불리" if roll <= 5 else ("유리" if roll >= 16 else "기본")


class PlanError(Exception):
    pass


def _pt(p, where, errs):
    if not (isinstance(p, (list, tuple)) and len(p) == 2 and all(isinstance(v, (int, float)) for v in p)):
        errs.append(f"{where}: 좌표는 [lon, lat] 숫자 쌍이어야 함: {p!r}")
        return
    lo, la = p
    if not (14 <= lo <= 45 and 40 <= la <= 66):
        errs.append(f"{where}: 좌표 범위 밖 (lon 14~45, lat 40~66): {p!r}")


def _pts(pts, where, errs, minn=2):
    if not isinstance(pts, list) or len(pts) < minn:
        errs.append(f"{where}: pts 는 {minn}개 이상 점의 리스트")
        return
    for i, p in enumerate(pts):
        _pt(p, f"{where}[{i}]", errs)


def _upserts(items, where, errs, known_ids, required_new, check):
    if not isinstance(items, list):
        errs.append(f"{where}: 리스트여야 함")
        return
    for i, it in enumerate(items):
        w = f"{where}[{i}]"
        if not isinstance(it, dict) or not isinstance(it.get("id"), str) or not it["id"]:
            errs.append(f"{w}: id(문자열) 필수")
            continue
        if it.get("remove"):
            continue
        if it["id"] not in known_ids:
            miss = [k for k in required_new if k not in it]
            if miss:
                errs.append(f"{w} ({it['id']}): 신규 항목은 {miss} 필요")
        check(it, w, errs)
        known_ids.add(it["id"])


def _check_unit(u, w, errs):
    if "side" in u and u["side"] not in SIDES: errs.append(f"{w}: side ∈ {SIDES}")
    if "axis" in u and u["axis"] not in AXES: errs.append(f"{w}: axis ∈ {AXES}")
    if "kind" in u and u["kind"] not in KINDS: errs.append(f"{w}: kind ∈ {KINDS}")
    if "echelon" in u and u["echelon"] not in ECHELONS: errs.append(f"{w}: echelon ∈ {ECHELONS}")
    if ("lon" in u) != ("lat" in u): errs.append(f"{w}: lon/lat 은 함께")
    if "lon" in u: _pt([u["lon"], u["lat"]], w, errs)
    s = u.get("strength")
    if s is not None and not (isinstance(s, (int, float)) and 0 <= s <= 100): errs.append(f"{w}: strength 0~100 또는 null")


def _check_pocket(p, w, errs):
    if "axis" in p and p["axis"] not in AXES: errs.append(f"{w}: axis ∈ {AXES}")
    if "lon" in p: _pt([p["lon"], p.get("lat")], w, errs)
    for k in ("rx", "ry"):
        if k in p and not (isinstance(p[k], (int, float)) and 0 < p[k] < 3): errs.append(f"{w}: {k} 0~3도")


def _check_arrow(a, w, errs):
    if "side" in a and a["side"] not in ARROW_SIDES: errs.append(f"{w}: side ∈ {ARROW_SIDES}")
    if "axis" in a and a["axis"] not in AXES: errs.append(f"{w}: axis ∈ {AXES}")
    if "pts" in a: _pts(a["pts"], w, errs)
    if a.get("label") and ("lx" not in a or "ly" not in a): errs.append(f"{w}: label 있으면 lx, ly 필요")


def _check_fort(f, w, errs):
    if "pts" in f: _pts(f["pts"], w, errs)


def validate(plan, state=None):
    """오류 리스트, 경고 리스트 반환."""
    errs, warns = [], []
    if not isinstance(plan, dict):
        return ["plan 은 JSON 객체여야 함"], []
    if plan.get("schema") != 1: errs.append("schema: 1 이어야 함")
    try:
        d = dt.date.fromisoformat(plan.get("date", ""))
    except Exception:
        errs.append("date: YYYY-MM-DD 필수"); d = None
    dice = plan.get("dice")
    if not isinstance(dice, list) or not dice:
        errs.append("dice: 최소 1개 이상의 주사위 기록 필요")
    else:
        seen = set()
        for i, r in enumerate(dice):
            w = f"dice[{i}]"
            if not isinstance(r, dict): errs.append(f"{w}: 객체"); continue
            if r.get("axis") not in AXES: errs.append(f"{w}: axis ∈ {AXES}")
            roll = r.get("roll")
            if not (isinstance(roll, int) and 1 <= roll <= 20): errs.append(f"{w}: roll 1~20 정수"); continue
            if r.get("band") and r["band"] != band(roll): errs.append(f"{w}: band '{r['band']}' ≠ 규칙상 '{band(roll)}'")
            seen.add(r.get("axis"))
        for a in AXES:
            if a not in seen: warns.append(f"dice: {a} 축 주사위 없음")
    kfs = plan.get("keyframes")
    if not isinstance(kfs, list) or not kfs:
        errs.append("keyframes: 1~4개 필요")
        kfs = []
    hours = [k.get("hour") for k in kfs if isinstance(k, dict)]
    if any(h not in HOURS for h in hours): errs.append(f"keyframes[].hour ∈ {HOURS}")
    if len(set(hours)) != len(hours): errs.append("keyframes: hour 중복")
    if hours != sorted(hours): errs.append("keyframes: hour 오름차순")
    if 24 not in hours: errs.append("keyframes: 24시 키프레임 필수(하루 종료 상태)")
    if len(hours) < 4: warns.append(f"keyframes: {sorted(set(HOURS) - set(hours))} 없음 → 보간")

    st = state or {}
    unit_ids = {u["id"] for u in st.get("units", [])}
    pocket_ids = {p["id"] for p in st.get("pockets", [])}
    arrow_ids = {a["id"] for a in st.get("arrows", [])}
    fort_ids = {f["id"] for f in st.get("forts", [])}
    for k in kfs:
        if not isinstance(k, dict): errs.append("keyframe 은 객체"); continue
        w = f"keyframes[h={k.get('hour')}]"
        ev = k.get("events", [])
        if not isinstance(ev, list): errs.append(f"{w}.events: 리스트")
        else:
            for i, e in enumerate(ev):
                if not isinstance(e, dict) or e.get("axis") not in AXES + ["all"] or not isinstance(e.get("text"), str) or not e["text"].strip():
                    errs.append(f"{w}.events[{i}]: {{axis, text}} 필요 (axis ∈ north/center/south/all)")
                elif len(e["text"]) > MAX_EVENT:
                    errs.append(f"{w}.events[{i}]: text {MAX_EVENT}자 이하 한 줄")
                elif "\n" in e["text"]:
                    errs.append(f"{w}.events[{i}]: 한 줄(개행 금지)")
        fr = k.get("fronts", {})
        if not isinstance(fr, dict): errs.append(f"{w}.fronts: {{axis: [segments]}}")
        else:
            for a, segs in fr.items():
                if a not in AXES: errs.append(f"{w}.fronts: 알 수 없는 축 {a}"); continue
                if not isinstance(segs, list) or not segs: errs.append(f"{w}.fronts.{a}: 세그먼트 리스트"); continue
                for i, sg in enumerate(segs):
                    if not isinstance(sg, dict): errs.append(f"{w}.fronts.{a}[{i}]: 객체"); continue
                    if sg.get("style", "solid") not in STYLES: errs.append(f"{w}.fronts.{a}[{i}].style ∈ {STYLES}")
                    _pts(sg.get("pts"), f"{w}.fronts.{a}[{i}]", errs)
        _upserts(k.get("units", []), f"{w}.units", errs, unit_ids,
                 ["name", "side", "axis", "lon", "lat", "kind", "echelon"], _check_unit)
        _upserts(k.get("pockets", []), f"{w}.pockets", errs, pocket_ids,
                 ["axis", "name", "lon", "lat", "rx", "ry"], _check_pocket)
        _upserts(k.get("arrows", []), f"{w}.arrows", errs, arrow_ids, ["axis", "side", "pts"], _check_arrow)
        _upserts(k.get("forts", []), f"{w}.forts", errs, fort_ids, ["pts"], _check_fort)
        for key in ("losses", "situation", "orders"):
            v = k.get(key)
            if v is not None and (not isinstance(v, dict) or any(a not in AXES + (["note"] if key == "losses" else []) for a in v)):
                errs.append(f"{w}.{key}: {{north|center|south: ...}}")
        if "views" in k:
            for kind, m in k["views"].items():
                if kind not in ("tactical", "operational") or not isinstance(m, dict):
                    errs.append(f"{w}.views: {{tactical|operational: {{axis: [x0,x1,y0,y1]}}}}"); continue
                for a, e in m.items():
                    if a not in AXES or not (isinstance(e, list) and len(e) == 4 and e[0] < e[1] and e[2] < e[3]):
                        errs.append(f"{w}.views.{kind}.{a}: [lon_min, lon_max, lat_min, lat_max]")
    if st and d:
        cd = dt.date.fromisoformat(st["clock"]["date"])
        if d < cd: warns.append(f"date {d} 는 현재 게임일 {cd} 보다 과거 — tick 이 사용하지 않음")
    return errs, warns


# ------------------------------------------------------------------ merge
def _upsert_list(lst, items):
    idx = {x["id"]: i for i, x in enumerate(lst)}
    for it in items:
        if it.get("remove"):
            if it["id"] in idx:
                lst[idx[it["id"]]] = None
            continue
        it = {k: v for k, v in it.items() if k != "remove"}
        if it["id"] in idx and lst[idx[it["id"]]] is not None:
            lst[idx[it["id"]]].update(it)
        else:
            lst.append(it); idx[it["id"]] = len(lst) - 1
    lst[:] = [x for x in lst if x is not None]


def apply_keyframe(state, plan, kf):
    """키프레임 하나를 state 에 병합. 추가된 이벤트 리스트 반환."""
    date, hour = plan["date"], kf["hour"]
    for a, segs in (kf.get("fronts") or {}).items():
        state["fronts"][a] = copy.deepcopy(segs)
    for key in ("units", "pockets", "arrows", "forts"):
        if kf.get(key):
            _upsert_list(state.setdefault(key, []), copy.deepcopy(kf[key]))
    for key in ("situation", "orders"):
        for a, v in (kf.get(key) or {}).items():
            if key == "orders":
                state["orders"].setdefault(a, {}).update(v)
            else:
                state[key][a] = v
    for a, v in (kf.get("losses") or {}).items():
        if a == "note":
            state["losses"]["note"] = v
        else:
            state["losses"].setdefault(a, {}).update(v)
    cap = kf.get("captures")
    if isinstance(cap, dict):
        state["captures"] = copy.deepcopy(cap)
    for kind, m in (kf.get("views") or {}).items():
        state["views"][kind].update(m)
    added = []
    for e in kf.get("events", []):
        ev = dict(game_time=game_stamp(date, hour), axis=e["axis"], kind=e.get("kind", "event"),
                  text=e["text"].strip(), real_time=iso_kst())
        state["events"].append(ev); added.append(ev)
    return added


# ------------------------------------------------------------------ interpolation
def _resample(pts, n):
    pts = [tuple(p) for p in pts]
    d = [0.0]
    for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
        d.append(d[-1] + math.hypot(x1 - x0, y1 - y0))
    tot = d[-1] or 1.0
    out, j = [], 0
    for i in range(n):
        t = tot * i / (n - 1)
        while j < len(d) - 2 and d[j + 1] < t:
            j += 1
        seg = (d[j + 1] - d[j]) or 1.0
        f = (t - d[j]) / seg
        out.append([round(pts[j][0] + (pts[j + 1][0] - pts[j][0]) * f, 4),
                    round(pts[j][1] + (pts[j + 1][1] - pts[j][1]) * f, 4)])
    return out


def interpolate_phase(state, target_kf, frac):
    """다음 키프레임(target_kf)으로 frac(0~1) 만큼 이동 — 부대·포위망 위치, 전선."""
    lerp = lambda a, b: round(a + (b - a) * frac, 4)
    for key in ("units", "pockets"):
        cur = {x["id"]: x for x in state.get(key, [])}
        for it in target_kf.get(key, []) or []:
            c = cur.get(it["id"])
            if not c or it.get("remove"):
                continue
            for f in ("lon", "lat", "rx", "ry"):
                if f in it and f in c:
                    c[f] = lerp(c[f], it[f])
            if key == "units" and it.get("strength") is not None and c.get("strength") is not None:
                c["strength"] = int(round(lerp(c["strength"], it["strength"])))
    for a, segs in (target_kf.get("fronts") or {}).items():
        cur = state["fronts"].get(a, [])
        if [s.get("id") for s in cur] != [s.get("id") for s in segs]:
            continue  # 세그먼트 구성이 다르면 보간 생략(다음 키프레임에서 교체)
        for c, t in zip(cur, segs):
            n = max(len(c["pts"]), len(t["pts"]), 8)
            A, B = _resample(c["pts"], n), _resample(t["pts"], n)
            c["pts"] = [[lerp(p[0], q[0]), lerp(p[1], q[1])] for p, q in zip(A, B)]


def load_plan(date):
    p = plan_path(date)
    return load_json(p) if os.path.exists(p) else None


def main(argv):
    if len(argv) < 3 or argv[1] not in ("validate", "install", "merge"):
        print(__doc__); return 2
    cmd, path = argv[1], argv[2]
    plan = load_json(path)
    st = load_state() if os.path.exists(STATE) else None
    errs, warns = validate(plan, st)
    for w in warns: print("경고:", w)
    for e in errs: print("오류:", e)
    if errs:
        print(f"검증 실패 ({len(errs)}건)"); return 1
    print("검증 통과:", plan["date"], "키프레임", [k["hour"] for k in plan["keyframes"]],
          "주사위", {r["axis"]: r["roll"] for r in plan["dice"]})
    if cmd == "install":
        dst = plan_path(plan["date"])
        if os.path.exists(dst) and os.path.abspath(dst) != os.path.abspath(path) and "--force" not in argv:
            print("이미 설치됨:", dst, "(덮어쓰려면 --force)"); return 1
        plan.setdefault("installed_real", iso_kst())
        save_json(dst, plan)
        print("설치:", dst)
        if st:
            with state_lock():
                st = load_state()
                st["needs_plan"] = first_missing_plan(st)
                if st.get("status") == "판정 대기" and st["needs_plan"] != st["clock"]["date"]:
                    st["status"] = "진행"
                save_state(st)
    elif cmd == "merge":
        h = int(argv[argv.index("--hour") + 1])
        kf = next(k for k in plan["keyframes"] if k["hour"] == h)
        with state_lock():
            st = load_state()
            key = f"{plan['date']}@{h:02d}"
            if key in st["applied"]:
                print("이미 적용됨:", key); return 0
            apply_keyframe(st, plan, kf); st["applied"].append(key)
            save_state(st)
        print("병합:", key)
    return 0


def first_missing_plan(st, horizon=3):
    d = dt.date.fromisoformat(st["clock"]["date"])
    for i in range(horizon):
        x = (d + dt.timedelta(days=i)).isoformat()
        if not os.path.exists(plan_path(x)):
            return x
    return None


if __name__ == "__main__":
    sys.exit(main(sys.argv))
