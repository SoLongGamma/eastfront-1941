#!/usr/bin/env python3
"""절차 판정기 (LLM 없음). 게임 하루 → plans/YYYY-MM-DD.json (기존 plan 스키마 + judge_state).
  judge.py plan [DATE]     오늘(state.clock) 계획 생성·설치 (이미 있으면 그대로 사용)
축마다 1d20(+strategy.json mod) → 1~5 불리 · 6~15 기본 · 16~20 유리. posture(offensive|limited|hold)·목표·지형(강·바다)에 따라 전선 이동.
유리한 주사위·전진·포위 폐쇄/축소·적 후퇴 때 적 트럭·전차를 노획(게임추정, state.captures). 키가 없으면 0.
"""
import copy, datetime as dt, json, math, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *  # noqa
import apply_plan as AP
from shapely.geometry import LineString, Polygon, Point
from shapely.prepared import prep

STRATEGY = os.path.join(LIVE, "strategy.json")
RNG = random.SystemRandom()
KM = 111.32
BARRIER_NAMES = {"Dnipro", "Dnepr", "Dnepre", "Southern Bug", "Don", "Donets", "Seversky Donets", "Dniester", "Kuban", "Terek"}

# posture → band → (km 범위, sigma km)
MOVE = {
    "offensive": {"유리": (14, 26), "기본": (3, 9), "불리": (-8, -3), "sigma": 75},
    "limited":   {"유리": (4, 8), "기본": (0, 3), "불리": (-5, -2), "sigma": 40},
    "hold":      {"유리": (2, 5), "기본": (-1, 1.5), "불리": (-5, -2), "sigma": 30},
    "defend":    {"유리": (0, 2), "기본": (-0.5, 0.5), "불리": (-4, -1), "sigma": 40},
}

_GEO = None


def geo():
    global _GEO
    if _GEO is None:
        import render as R
        from shapely.ops import unary_union
        G = R.geo()
        land = prep(G["land"])
        bars = []
        for fn in ("ne_10m_rivers_lake_centerlines", "ne_10m_rivers_europe"):
            with open(os.path.join(ROOT, "ne", fn + ".geojson")) as fh:
                for f in json.load(fh)["features"]:
                    if (f["properties"].get("name") or "") in BARRIER_NAMES:
                        from shapely.geometry import shape
                        g = shape(f["geometry"])
                        if g.intersects(Polygon([(18, 42), (48, 42), (48, 61), (18, 61)])):
                            bars.append(g)
        _GEO = dict(land=land, barrier=prep(unary_union(bars)) if bars else None)
    return _GEO


def km_xy(p, lat0):
    return (p[0] * KM * math.cos(math.radians(lat0)), p[1] * KM)


def dist_km(a, b):
    lat0 = (a[1] + b[1]) / 2
    return math.hypot((a[0] - b[0]) * KM * math.cos(math.radians(lat0)), (a[1] - b[1]) * KM)


def d2(date):
    d = dt.date.fromisoformat(date)
    return f"{d.month}.{d.day}"


def load_strategy():
    return load_json(STRATEGY)


def axis_cfg(strat, axis, date):
    c = copy.deepcopy(strat["axes"][axis])
    ov = c.pop("override", None)
    if ov and date <= ov["until"]:
        c.update({k: v for k, v in ov.items() if k != "until"})
        c["override_active"] = ov["until"]
    return c


def axis_mod(cfg, date):
    m = 0
    for r in sorted(cfg.get("mod", []), key=lambda r: r["from"]):
        if date >= r["from"]:
            m = r["mod"]
    return m


def band(r):
    return AP.band(r)


# ------------------------------------------------------------------ chain helpers
def flatten(st):
    """전체 전선 체인 + 각 점의 소속 [(axis, seg_i, pt_i)...]. 공유점(세그먼트·축 경계)은 1번만."""
    chain, refs = [], []
    for a in AXES:
        for si, seg in enumerate(st["fronts"][a]):
            for pi, p in enumerate(seg["pts"]):
                if chain and pi == 0 and tuple(chain[-1]) == tuple(p):
                    refs[-1].append((a, si, pi))
                    continue
                chain.append(list(p)); refs.append([(a, si, pi)])
    return chain, refs


def unflatten(st, chain, refs):
    fr = copy.deepcopy(st["fronts"])
    for p, rs in zip(chain, refs):
        for a, si, pi in rs:
            fr[a][si]["pts"][pi] = [round(p[0], 4), round(p[1], 4)]
    return fr


def chain_ok(chain, closure):
    try:
        ls = LineString(chain)
        if not ls.is_simple:
            return False
        return Polygon([tuple(p) for p in chain] + [tuple(p) for p in closure]).is_valid
    except Exception:
        return False


def german_poly(st):
    chain, _ = flatten(st)
    return Polygon([tuple(p) for p in chain] + [tuple(p) for p in st["german_closure"]]).buffer(0)


def densify(st, axis, maxkm=35):
    """이동 축 세그먼트에 긴 구간 중간점 삽입(경계점 유지)."""
    for seg in st["fronts"][axis]:
        pts, out = seg["pts"], [seg["pts"][0]]
        for p, q in zip(pts[:-1], pts[1:]):
            n = int(dist_km(p, q) // maxkm)
            for k in range(1, n + 1):
                f = k / (n + 1)
                out.append([round(p[0] + (q[0] - p[0]) * f, 4), round(p[1] + (q[1] - p[1]) * f, 4)])
            out.append(q)
        seg["pts"] = out


def displace(st, axis, center, mag_km, sigma, toward=None):
    """axis 전선 점들을 center 주변 가우시안 가중으로 이동. mag>0 = 독일 전진(소련 쪽 법선). 반환 (새 fronts, 최대 이동 km)."""
    G = geo()
    chain, refs = flatten(st)
    n = len(chain)
    orig = [list(p) for p in chain]
    allowed_cross = toward is not None and toward.get("cross", False)
    best = None
    for shrink in (1.0, 0.5, 0.25):
        new = [list(p) for p in orig]
        moved = 0.0
        for i in range(1, n - 1):
            rs = refs[i]
            if len(rs) > 1 and len({r[0] for r in rs}) > 1:
                continue  # 축 경계점 고정
            if rs[0][0] != axis:
                continue
            p = orig[i]
            dkm = dist_km(p, center)
            w = math.exp(-(dkm / sigma) ** 2)
            if w < 0.03:
                continue
            lat0 = p[1]
            cx = math.cos(math.radians(lat0))
            a, b = orig[i - 1], orig[i + 1]
            tx, ty = (b[0] - a[0]) * cx, (b[1] - a[1])
            L = math.hypot(tx, ty) or 1
            nx, ny = -ty / L, tx / L          # 왼쪽 법선 = 소련 쪽
            if mag_km > 0 and toward is not None:
                ox, oy = (toward["lon"] - p[0]) * cx, (toward["lat"] - p[1])
                Lo = math.hypot(ox, oy) or 1
                ux, uy = 0.45 * nx + 0.55 * ox / Lo, 0.45 * ny + 0.55 * oy / Lo
                Lu = math.hypot(ux, uy) or 1
                ux, uy = ux / Lu, uy / Lu
                if ux * nx + uy * ny < 0.15:
                    ux, uy = nx, ny
                step = mag_km * w * shrink
                step = min(step, max(0.0, Lo * KM - 4))  # 목표 4km 앞에서 멈춤
            else:
                ux, uy = nx, ny
                step = mag_km * w * shrink
            q = [p[0] + ux * step / (KM * cx), p[1] + uy * step / KM]
            if not (14 <= q[0] <= 45 and 40 <= q[1] <= 66):
                continue
            if not G["land"].contains(Point(q)):
                continue
            if G["barrier"] is not None and not allowed_cross and abs(step) > 0.05:
                if G["barrier"].intersects(LineString([p, q])):
                    q = [p[0] + (q[0] - p[0]) * 0.15, p[1] + (q[1] - p[1]) * 0.15]  # 강안에서 정지
            new[i] = q
            moved = max(moved, abs(step))
        if chain_ok(new, st["german_closure"]):
            best = (new, moved)
            break
    if best is None:
        return st["fronts"], 0.0
    return unflatten(st, best[0], refs), best[1]


def nearest_disp(old_chain, new_chain, pt, maxkm=90):
    bi, bd = None, 1e9
    for i, p in enumerate(old_chain):
        d = dist_km(p, pt)
        if d < bd:
            bi, bd = i, d
    if bi is None or bd > maxkm:
        return 0.0, 0.0
    w = max(0.0, 1 - bd / maxkm)
    # make_plan 은 아침 전선(old_chain) 인덱스로 저녁 전선을 읽는다.
    # 포위 절단으로 new_chain 이 더 짧으면 IndexError — 그 부대는 그날 이동 없음.
    try:
        return (new_chain[bi][0] - old_chain[bi][0]) * w, (new_chain[bi][1] - old_chain[bi][1]) * w
    except IndexError:
        return 0.0, 0.0


def axis_chain(st, axis):
    """한 축의 전선 점. 세그먼트가 맞닿은 공유점은 한 번만."""
    pts = []
    for seg in (st.get("fronts") or {}).get(axis) or []:
        for p in seg.get("pts") or []:
            if pts and tuple(pts[-1]) == tuple(p):
                continue
            pts.append((p[0], p[1]))
    return pts


def front_side_km(chain, pt):
    """가장 가까운 전선 구간까지의 부호 있는 km. 양수 = 진행 방향의 왼쪽 = 소련 쪽."""
    if not chain or len(chain) < 2:
        return 0.0
    lat0 = pt[1]
    px, py = km_xy(pt, lat0)
    best, best_d = 0.0, 1e18
    for a, b in zip(chain[:-1], chain[1:]):
        ax, ay = km_xy(a, lat0)
        bx, by = km_xy(b, lat0)
        vx, vy = bx - ax, by - ay
        L2 = vx * vx + vy * vy
        if L2 < 1e-9:
            continue
        t = max(0.0, min(1.0, ((px - ax) * vx + (py - ay) * vy) / L2))
        qx, qy = ax + t * vx, ay + t * vy
        L = math.hypot(vx, vy) or 1.0
        nx, ny = -vy / L, vx / L
        sx, sy = px - qx, py - qy
        d = math.hypot(sx, sy)
        if d < best_d:
            best_d = d
            best = sx * nx + sy * ny
    return best


def pocketed_unit(st, unit, js=None):
    """포위망에 든 부대. judge.pockets 의 명단이거나, 지도 포위 타원 안."""
    uid = unit.get("id")
    js = st.get("judge") if js is None else js
    for P in ((js or {}).get("pockets") or {}).values():
        if uid in (P.get("units") or []):
            return True
    for pk in st.get("pockets") or []:
        rx, ry = pk.get("rx") or 0, pk.get("ry") or 0
        if rx <= 0 or ry <= 0 or "lon" not in pk or "lat" not in pk:
            continue
        if ((unit.get("lon", 0) - pk["lon"]) / rx) ** 2 + ((unit.get("lat", 0) - pk["lat"]) / ry) ** 2 <= 1:
            return True
    return False


def side_guard(dx, dy, unit, chain, pocketed=False):
    """자기 전선 반대편으로 더 들어가는 이동은 1 → 0.5 → 0.25 → 0 으로 줄인다. 포위 부대는 제외."""
    if pocketed or abs(dx) + abs(dy) < 1e-12:
        return dx, dy
    if unit.get("side") not in ("de", "su") or len(chain) < 2:
        return dx, dy
    start = (unit["lon"], unit["lat"])

    def depth(signed):
        if unit["side"] == "de":
            return max(0.0, signed)
        return max(0.0, -signed)

    base = depth(front_side_km(chain, start))
    for shrink in (1.0, 0.5, 0.25, 0.0):
        end = (start[0] + dx * shrink, start[1] + dy * shrink)
        if depth(front_side_km(chain, end)) <= base + 0.05:
            return dx * shrink, dy * shrink
    return 0.0, 0.0


# ------------------------------------------------------------------ text
TPL = {
    ("offensive", "유리"): ["{obj} 방면 돌파 유의미 — 선두 {km}km 전진, 적 후위 붕괴", "{obj} 축 기갑 돌진 성공 — {km}km 진출·측면 확장"],
    ("offensive", "기본"): ["{obj} 방면 소폭 전진 {km}km — 적 지연전·지뢰로 템포 제한", "{obj} 축 보병·기갑 합동 압박, {km}km 진척"],
    ("offensive", "불리"): ["{obj} 방면 반격에 선두 {km}km 후퇴 — 연료·측면 압박", "{obj} 공격 좌절 — 적 국지 반격으로 {km}km 밀림"],
    ("limited", "유리"): ["{obj} 국지 공격 성공 — 교두·진지 {km}km 확장", "{obj} 고지·거점 탈취, {km}km 심화"],
    ("limited", "기본"): ["{obj} 소폭 진척·현 진지 고수", "{obj} 소모전 지속, 미세 진척"],
    ("limited", "불리"): ["{obj} 야간 역습에 {km}km 수축", "{obj} 진지 일부 상실·교두 수축"],
    ("hold", "유리"): ["{obj} 국지 개선 — 보병 {km}km 전진, 진지 정리", "{obj} 소련 탐색 공격 격퇴 후 국지 확장"],
    ("hold", "기본"): ["{obj} 현 전선 고수 — 견제 포격·정찰, 변화 미미", "{obj} 보병 고수·견제, 소련 야간 탐색 격퇴"],
    ("hold", "불리"): ["{obj} 소련 국지 반격 — 진지 {km}km 상실", "{obj} 야간 압박에 국지 후퇴 {km}km"],
    ("defend", "유리"): ["{obj} 방어선 강화·소련 공격 격퇴", "{obj} 방어진지 완성도↑"],
    ("defend", "기본"): ["{obj} 방어선 고수", "{obj} 진지 공사·정찰"],
    ("defend", "불리"): ["{obj} 소련 반격으로 국지 상실 {km}km", "{obj} 방어선 일부 돌파 — 예비 투입"],
}
SU_TPL = {"유리": "소련 후위 붕괴·후퇴", "기본": "소련 지연·국지 반격", "불리": "소련 반격 성공"}


def pick(lst):
    return lst[RNG.randrange(len(lst))]


# ------------------------------------------------------------------ vehicle capture
# 게임 추정치. 1941년 독일은 진격로에 버린 소련 트럭·T-34를 자주 거두고,
# 소련이 독일 차량을 다시 굴리는 일은 그보다 드물다(부품·연료). 가산은 하루 축당 전투력 +1이 상한.
def _cell(raw):
    raw = raw or {}
    return {"trucks": max(0, int(raw.get("trucks") or 0)), "tanks": max(0, int(raw.get("tanks") or 0))}


def _add_cell(prev, add):
    base, inc = _cell(prev), _cell(add)
    return {"trucks": base["trucks"] + inc["trucks"], "tanks": base["tanks"] + inc["tanks"]}


def blank_captures():
    return {a: {"de": _cell(None), "su": _cell(None)} for a in AXES}


def captures_of(st):
    """누적 노획. captures 가 없는 기존 state 는 전부 0."""
    raw = (st or {}).get("captures") or {}
    return {a: {"de": _cell((raw.get(a) or {}).get("de")), "su": _cell((raw.get(a) or {}).get("su"))} for a in AXES}


def fmt_pair(cell):
    cell = _cell(cell)
    return f"{cell['trucks']}트럭·{cell['tanks']}전차"


def _swing(rng, lo, hi):
    lo, hi = int(lo), int(hi)
    if hi <= lo:
        return lo
    return rng.randint(lo, hi)


def haul_for(note, closed=False, reduced=0, eliminated=0, rng=None):
    """그날 그 축에서 각 측이 빼앗은 트럭·전차. de = 독일(소련 차량), su = 소련(독일 차량).

    조건(하나면 충분): 유리한 주사위, 전진, 포위 폐쇄, 포위 축소/소멸, 적 후퇴·공격 붕괴.
    소련 전차는 공세가 6km 이상 밀릴 때만 1대. 그 외 독일 차량 노획은 트럭이 대부분.
    """
    rng = rng or RNG
    b = note.get("band") or "기본"
    km = abs(int(note.get("km") or 0))
    # km 는 전선이 실제로 움직인 거리(절대값). mag 가 음수면 독일 후퇴 = 소련 측 전진.
    if note.get("mag") is not None:
        signed = km if float(note["mag"]) >= 0 else -km
    else:
        signed = int(note.get("km") or 0)
    adv = max(0, signed)
    pst = note.get("posture") or "hold"
    if pst not in MOVE:
        pst = "hold"
    de_tr = de_tk = su_tr = su_tk = 0
    if b == "유리":
        de_tr += {"offensive": _swing(rng, 22, 48), "limited": _swing(rng, 10, 24),
                  "hold": _swing(rng, 4, 12), "defend": _swing(rng, 2, 6)}[pst] + adv
        if pst == "offensive":
            de_tk += 1 + _swing(rng, 0, 2) + (1 if adv >= 14 else 0)
        elif pst == "limited":
            de_tk += 1 if adv >= 4 else _swing(rng, 0, 1)
        elif adv >= 3 and _swing(rng, 1, 5) == 5:
            de_tk += 1
    elif adv > 0 and b == "기본" and pst in ("offensive", "limited", "hold"):
        de_tr += {"offensive": _swing(rng, 8, 18), "limited": _swing(rng, 4, 10), "hold": _swing(rng, 2, 6)}[pst] + adv // 2
        if pst == "offensive" and adv >= 6:
            de_tk += _swing(rng, 0, 1)
    if closed:
        de_tr += _swing(rng, 80, 140)
        de_tk += _swing(rng, 6, 12)
    if reduced:
        de_tr += _swing(rng, 12, 26) * int(reduced)
        de_tk += _swing(rng, 0, 2) * int(reduced)
    if eliminated:
        de_tr += _swing(rng, 30, 60) * int(eliminated)
        de_tk += _swing(rng, 2, 5) * int(eliminated)
    if b == "불리" and signed < 0:
        su_tr += _swing(rng, 3, 8) + min(6, abs(signed))
        if pst in ("offensive", "limited") and signed <= -6:
            su_tk += 1
    elif b == "불리" and pst == "offensive":
        su_tr += _swing(rng, 1, 4)
    return {"de": {"trucks": min(de_tr, 250), "tanks": min(de_tk, 30)},
            "su": {"trucks": min(su_tr, 20), "tanks": min(su_tk, 1)}}


def is_notable(day):
    return any(day[s]["tanks"] >= 1 or day[s]["trucks"] >= 10 for s in ("de", "su"))


def booty_boost(cell):
    """부품·연료 때문에 노획분의 전투 가산은 0 또는 1."""
    cell = _cell(cell)
    return 1 if cell["tanks"] >= 1 or cell["trucks"] >= 12 else 0


def loss_from_capture(cell):
    """빼앗긴 측 전투력 % 가산. 상한 0.8. 트럭은 잘게, 전차는 조금 더."""
    cell = _cell(cell)
    return round(min(0.8, cell["trucks"] * 0.004 + cell["tanks"] * 0.05), 2)


def add_capture_losses(L, day):
    """노획을 잃은 측 손실로 기록. 아무것도 없으면 losses 를 건드리지 않는다."""
    if not any(day[s][k] for s in ("de", "su") for k in ("trucks", "tanks")):
        return L
    L["de_veh_lost"] = _add_cell(L.get("de_veh_lost"), day["su"])
    L["su_veh_lost"] = _add_cell(L.get("su_veh_lost"), day["de"])
    L["de_pct"] = round(min(99.9, float(L.get("de_pct") or 0) + loss_from_capture(day["su"])), 1)
    L["su_pct"] = round(min(99.9, float(L.get("su_pct") or 0) + loss_from_capture(day["de"])), 1)
    return L


def apply_booty_strength(work_units, unit_ops, axis, side, haul):
    """노획 측 부대 하나 전투력 +1. 전차 노획이면 기갑을 우선. 100 이 상한."""
    haul = _cell(haul)
    if booty_boost(haul) != 1:
        return 0
    removed = {op.get("id") for op in unit_ops if op.get("remove")}
    cands = [u for u in work_units
             if u.get("axis") == axis and u.get("side") == side and u.get("echelon") != "group"
             and u.get("strength") is not None and u.get("id") not in removed]
    if haul["tanks"] >= 1:
        arm = [u for u in cands if u.get("kind") == "armor"]
        if arm:
            cands = arm
    if not cands:
        return 0
    u = max(cands, key=lambda u: (u.get("strength") or 0, u.get("id") or ""))
    op = next((x for x in unit_ops if x.get("id") == u["id"] and not x.get("remove")), None)
    cur = u.get("strength") if op is None or op.get("strength") is None else op["strength"]
    if cur is None or cur >= 100:
        return 0
    new = min(100, int(cur) + 1)
    if op is None:
        unit_ops.append({"id": u["id"], "strength": new})
    else:
        op["strength"] = new
    return 1


def capture_note(day, boosts):
    """일지에 남길 만큼 큰 노획만 한 줄. 작은 트럭 몇 대는 누적에만 더한다."""
    if not is_notable(day):
        return ""
    bits = []
    if day["de"]["trucks"] or day["de"]["tanks"]:
        bits.append("독 " + fmt_pair(day["de"]))
    if day["su"]["trucks"] or day["su"]["tanks"]:
        bits.append("소 " + fmt_pair(day["su"]))
    gained = [lab for lab, side in (("독", "de"), ("소", "su")) if boosts.get(side)]
    lim = ("부품·연료 제한으로 " + "·".join(gained) + " 전투력 +1") if gained else "부품·연료 부족으로 전투 가산 없음"
    return "노획(게임추정): " + ", ".join(bits) + " — " + lim + "."


def sum_vehicles(st, axis, start, end, inclusive=True):
    tot = {"de": _cell(None), "su": _cell(None)}
    for rec in (st or {}).get("dice") or []:
        ds = rec.get("date") or ""
        if not ds or ds < start:
            continue
        if ds > end or (not inclusive and ds >= end):
            continue
        arm = (rec.get("vehicles") or {}).get(axis) or {}
        for side in ("de", "su"):
            tot[side] = _add_cell(tot[side], arm.get(side))
    return tot


def capture_line(cum, period):
    line = "노획(게임추정) 누적 독 " + fmt_pair(cum["de"]) + " / 소 " + fmt_pair(cum["su"])
    if any(period[s][k] for s in ("de", "su") for k in ("trucks", "tanks")):
        line += " · 구간 독 " + fmt_pair(period["de"]) + " / 소 " + fmt_pair(period["su"])
    return line


def brief_capture(st, axis, start, end):
    cum = captures_of(st)[axis]
    per = sum_vehicles(st, axis, start, end, True)
    return "노획(게임추정) 누적 독 " + fmt_pair(cum["de"]) + " / 소 " + fmt_pair(cum["su"]) + ", 이 구간 독 " + fmt_pair(per["de"]) + " / 소 " + fmt_pair(per["su"])


# ------------------------------------------------------------------ main judge
def default_judge_state(st):
    return {"stage": {"south": 0}, "progress": {}, "captured": [], "transfers": {}, "stored_units": {}}


def make_plan(st, date, strat=None):
    strat = strat or load_strategy()
    js = copy.deepcopy(st.get("judge") or default_judge_state(st))
    work = copy.deepcopy(st)
    G = geo()
    dice, summary, ev12, ev24, notes = [], {}, [], [], {}
    closed_axes = set()
    old_chain, _ = flatten(work)
    units_out = {}
    arrows_out = {}
    views = {"tactical": {}, "operational": {}}
    turn = 9 + max(0, (dt.date.fromisoformat(date) - dt.date(1941, 8, 17)).days // 7)

    for axis in AXES:
        cfg = axis_cfg(strat, axis, date)
        posture = cfg.get("posture", "hold")
        raw = RNG.randint(1, 20)
        mod = axis_mod(cfg, date)
        roll = max(1, min(20, raw + mod))
        b = band(roll)
        obj = None
        stage_name = ""
        stage_cross = "0000"
        if posture in ("offensive", "limited") and (cfg.get("objectives") or cfg.get("stages")):
            if cfg.get("objectives"):
                objs = cfg["objectives"]
                stage_name = "턴9 명령" if cfg.get("override_active") else "현 명령"
            else:
                si = min(js["stage"].get(axis, 0), len(cfg["stages"]) - 1)
                stg = cfg["stages"][si]
                stage_name = stg["name"]
                stage_cross = stg.get("cross_from", "0000")
                objs = stg.get("objectives", [])
                if stg.get("defend"):
                    posture = "defend"
            remaining = [o for o in objs if o["name"] not in js["captured"]]
            if remaining and posture != "defend":
                # 전선에 가장 가까운 미점령 목표
                obj = min(remaining, key=lambda o: (o.get("priority", 5), min(dist_km(p, (o["lon"], o["lat"])) for p in old_chain)))
            elif posture == "offensive" and cfg.get("stages") and not remaining:
                js["stage"][axis] = js["stage"].get(axis, 0) + 1
        if obj is None:
            secs = cfg.get("sectors") or [{"name": AXIS_KO[axis] + " 전선", "lon": old_chain[len(old_chain) // 2][0], "lat": old_chain[len(old_chain) // 2][1], "w": 1}]
            tot = sum(s.get("w", 1) for s in secs)
            r = RNG.uniform(0, tot)
            for s in secs:
                r -= s.get("w", 1)
                if r <= 0:
                    break
            center, oname, toward = (s["lon"], s["lat"]), s["name"], None
            if posture == "offensive":
                posture = "limited"
        else:
            center = min(old_chain, key=lambda p: dist_km(p, (obj["lon"], obj["lat"])))
            oname = obj["name"]
            toward = dict(obj, cross=(b == "유리" and date >= obj.get("cross_from", stage_cross)))
        M = MOVE[posture]
        lo_, hi_ = M[b]
        mag = RNG.uniform(lo_, hi_)
        before_chain, _ = flatten(work)
        if abs(mag) >= 0.3:
            if mag > 0 and posture == "offensive":
                densify(work, axis)
            work["fronts"], moved = displace(work, axis, center, mag, M["sigma"], toward)
        else:
            moved = 0.0
        km = int(round(moved))
        pocket_made = None
        if axis == "south":
            wd = cfg.get("su_withdraw")
            if wd and date >= wd["from"] and not js.get("pockets_made"):
                tipi = min(range(len(work["fronts"]["south"][0]["pts"])), key=lambda i: work["fronts"]["south"][0]["pts"][i][0])
                tip = work["fronts"]["south"][0]["pts"][tipi]
                if tip[0] < 27.0:
                    work["fronts"], wkm = displace(work, "south", tip, RNG.uniform(*wd.get("tip_km", [4, 9])), 130, None)
                    if wkm > 0.5:
                        ev24.append(dict(axis="south", kind="event", text=f"{wd['name']} — 돌출부 서단 {int(round(wkm))}km 축소, 17군 추격"))
            pocket_made = try_pocket(work, js, date, ev24)
            if pocket_made:
                closed_axes.add("south")
        # 목표 진척
        prog_txt = ""
        if obj is not None:
            pr = js["progress"].get(obj["name"], 0) + {"유리": 2, "기본": 1, "불리": -1}[b]
            pr = max(0, pr)
            js["progress"][obj["name"]] = pr
            gp = german_poly(work)
            near = gp.contains(Point(obj["lon"], obj["lat"])) or \
                min(dist_km(p, (obj["lon"], obj["lat"])) for p in flatten(work)[0]) < 15
            prog_txt = f"{oname} 진척 {min(pr, obj['resist'])}/{obj['resist']}"
            if obj.get("link"):
                near = pocket_made is not None
                if not near and pr >= obj["resist"]:
                    prog_txt = f"{oname} 진척 {obj['resist']}/{obj['resist']} — 고리 미폐쇄"
            if pr >= obj["resist"] and near:
                js["captured"].append(obj["name"])
                ev24.append(dict(axis=axis, kind="capture", text=f"{oname} 장악 — {stage_name} 목표 달성({d2(date)})"))
                prog_txt = f"{oname} 장악"
        if km == 0 and b == "기본":
            core = pick(TPL[(posture, b)]).replace(" {km}km", "").replace("{km}km ", "").replace("{km}km", "소폭")
        else:
            core = pick(TPL[(posture, b)])
        core = core.format(obj=oname, km=max(km, 1))
        modtxt = f"{raw}{'+' if mod >= 0 else ''}{mod}→{roll}" if mod else f"{roll}"
        note = f"{cfg.get('summary', '')[:60]} · 1d20={raw}" + (f" {mod:+d}(증원 보너스)" if mod else "") + f" → {roll} {b}"
        dice.append(dict(axis=axis, roll=roll, band=b, raw=raw, mod=mod, note=note, posture=posture, objective=oname))
        summary[axis] = f"주사위 {modtxt}({b}): {core}." + (f" {prog_txt}." if prog_txt else "")
        notes[axis] = dict(posture=posture, objective=oname, band=b, km=km, core=core, stage=stage_name, prog=prog_txt, mag=round(mag, 1))
        ev12.append(dict(axis=axis, text=f"정오: {oname} — " + {"유리": "공세 측 우세, 적 저항 약화", "기본": "교전 지속·국지 쟁탈", "불리": "소련 측 반격·압박 강화"}[b] + f" ({cfg.get('su_posture', '')[:40]})"))
        ev24.append(dict(axis=axis, text=f"{d2(date)} 종료(주사위 {roll} {b}): {core}." + (f" {prog_txt}." if prog_txt else "")))
        # 지도 범위: 남부 주공은 목표 따라 전술도 이동
        if axis == "south" and obj is not None:
            cx_, cy_ = (center[0] + obj["lon"]) / 2, (center[1] + obj["lat"]) / 2
            views["tactical"]["south"] = [round(cx_ - 2.8, 2), round(cx_ + 2.8, 2), round(cy_ - 1.1, 2), round(cy_ + 1.1, 2)]
            op = st["views"]["operational"]["south"]
            if not (op[0] + 1 < obj["lon"] < op[1] - 1 and op[2] + 0.6 < obj["lat"] < op[3] - 0.6):
                views["operational"]["south"] = [round(obj["lon"] - 7.5, 2), round(obj["lon"] + 4, 2), round(obj["lat"] - 3.3, 2), round(obj["lat"] + 3.3, 2)]

    # 부대·화살표 이동: 가까운 전선점 변위를 따라감
    new_chain, _ = flatten(work)
    axis_chains = {a: axis_chain(work, a) for a in AXES}
    for u in work["units"]:
        if u.get("echelon") == "group":
            continue
        dx, dy = nearest_disp(old_chain, new_chain, (u["lon"], u["lat"]))
        dx, dy = side_guard(dx, dy, u, axis_chains.get(u.get("axis")) or [], pocketed_unit(work, u, js))
        b = notes[u["axis"]]["band"]
        s = u.get("strength")
        if s is not None:
            if u["side"] == "de":
                s += {"유리": -1, "기본": RNG.choice([-1, 0, 1]), "불리": -2}[b]
            else:
                s += {"유리": -2, "기본": RNG.choice([-1, 0, 1]), "불리": 1}[b]
            s = max(2, min(100, s))
        if abs(dx) + abs(dy) > 1e-4 or s != u.get("strength"):
            units_out[u["id"]] = dict(id=u["id"], lon=round(u["lon"] + dx, 4), lat=round(u["lat"] + dy, 4), strength=s)
    for a in work["arrows"]:
        uid = a.get("unit")
        if uid in units_out:
            u0 = next(x for x in work["units"] if x["id"] == uid)
            dx, dy = units_out[uid]["lon"] - u0["lon"], units_out[uid]["lat"] - u0["lat"]
            arrows_out[a["id"]] = dict(id=a["id"], pts=[[round(p[0] + dx, 4), round(p[1] + dy, 4)] for p in a["pts"]])
    # 남부 주공 화살표 → 현재 목표
    sn = notes["south"]
    sobj = next((o for st_ in [axis_cfg(strat, "south", date)] for o in
                 (st_.get("objectives") or [o for g in st_.get("stages", []) for o in g.get("objectives", [])])
                 if o["name"] == sn["objective"]), None)
    if sobj:
        u = units_out.get("de-3mot") or next((x for x in work["units"] if x["id"] == "de-3mot"), None)
        if u:
            ux, uy = u["lon"], u["lat"]
            tx, ty = ux + (sobj["lon"] - ux) * 0.85, uy + (sobj["lat"] - uy) * 0.85
            if dist_km((ux, uy), (tx, ty)) > 8:
                arrows_out["a-1pzg"] = dict(id="a-1pzg", pts=[[round(ux, 4), round(uy, 4)], [round((ux + tx) / 2, 4), round((uy + ty) / 2, 4)], [round(tx, 4), round(ty, 4)]], goal=sn["objective"])
    # 북·중부 고수 태세 → 독일 화살표 목표 문구
    for a in work["arrows"]:
        ax_ = a.get("axis")
        if a["side"] == "de" and ax_ in ("north", "center") and notes[ax_]["posture"] == "hold":
            arrows_out.setdefault(a["id"], {"id": a["id"]})["goal"] = "현 전선 고수·견제"

    # 기갑 전용(transfers)
    unit_ops = list(units_out.values())
    arrow_ops = list(arrows_out.values())
    for t in strat.get("transfers", []):
        tid = t["unit"]
        status = js["transfers"].get(tid)
        if status is None and date >= t["depart"]:
            u = next((x for x in work["units"] if x["id"] == tid), None)
            if u:
                js["stored_units"][tid] = copy.deepcopy(u)
                unit_ops = [x for x in unit_ops if x["id"] != tid] + [{"id": tid, "remove": True}]
                for a in work["arrows"]:
                    if a.get("unit") == tid:
                        arrow_ops = [x for x in arrow_ops if x["id"] != a["id"]] + [{"id": a["id"], "remove": True}]
                ev24.append(dict(axis=t["from"], kind="transfer", text=f"{t['name']} 남부집단군으로 전용 출발 — 보병이 정면 인수, 도착 예정 {d2(t['arrive'])}"))
            js["transfers"][tid] = "transit"
        elif status == "transit" and date >= t["arrive"]:
            u = copy.deepcopy(js["stored_units"].pop(tid, None) or {"id": tid, "name": t["name"], "side": "de", "kind": "armor", "echelon": "corps", "strength": 60})
            # 남부 주공 후방 25km
            c = min(new_chain, key=lambda p: dist_km(p, (sobj["lon"], sobj["lat"])) if sobj else 0) if sobj else (29.0, 49.5)
            k = len([1 for v in js["transfers"].values() if v == "arrived"])
            u.update(axis="south", lon=round(c[0] - 0.35 - 0.15 * k, 4), lat=round(c[1] + 0.25 * ((k % 3) - 1), 4),
                     strength=min(100, (u.get("strength") or 40) + 20), dx=0, dy=-14)
            unit_ops.append(u)
            js["transfers"][tid] = "arrived"
            ev24.append(dict(axis="south", kind="transfer", text=f"{t['name']} 남부 도착·재정비 후 주공 배속 — 증원 보너스 단계 상승"))

    pocket_hits = {"reduced": [], "eliminated": []}
    pocket_ops = upkeep_pockets(work, js, date, notes, unit_ops, ev24, pocket_hits)
    # 노획(게임추정). 이동·주사위 RNG 를 모두 쓴 뒤에 굴리므로 기존 판정 난수는 그대로다.
    cum = captures_of(st)
    vehicles = {}
    for axis in AXES:
        nred = sum(1 for a in pocket_hits["reduced"] if a == axis)
        nelim = sum(1 for a in pocket_hits["eliminated"] if a == axis)
        day = haul_for(notes[axis], closed=axis in closed_axes, reduced=nred, eliminated=nelim)
        vehicles[axis] = day
        for side in ("de", "su"):
            cum[axis][side]["trucks"] += day[side]["trucks"]
            cum[axis][side]["tanks"] += day[side]["tanks"]
        got = {side: apply_booty_strength(work["units"], unit_ops, axis, side, day[side]) for side in ("de", "su")}
        note = capture_note(day, got)
        if note:
            summary[axis] = summary[axis] + " " + note
            ev24.append(dict(axis=axis, kind="booty", text=note))
    # 손실(점근 증가). 노획분은 빼앗긴 쪽에만 작은 가산.
    losses = {}
    for axis in AXES:
        L = copy.deepcopy(st["losses"].get(axis, {}))
        b, pst = notes[axis]["band"], notes[axis]["posture"]
        k_de = {"유리": 0.004, "기본": 0.003, "불리": 0.007}[b] * (1.6 if pst == "offensive" else 0.6)
        k_su = {"유리": 0.009, "기본": 0.004, "불리": 0.002}[b] * (1.6 if pst == "offensive" else 0.6)
        dp = L.get("de_pct", 50) + (100 - L.get("de_pct", 50)) * k_de
        sp = L.get("su_pct", 50) + (100 - L.get("su_pct", 50)) * k_su
        L["de_pct"], L["su_pct"] = round(dp, 1), round(sp, 1)
        add_capture_losses(L, vehicles[axis])
        de_n, su_n = {"north": ("독 북부집단군", "소련 북서전선"), "center": ("독 중부집단군", "소련 서부전선"), "south": ("독 남부집단군", "소련 남서·남부전선")}[axis]
        L["de_text"] = f"{de_n} ~{int(L['de_pct'])}%({notes[axis]['objective']}·게임추정)"
        L["su_text"] = f"{su_n} ~{int(L['su_pct'])}%({notes[axis]['objective']}·게임추정)"
        losses[axis] = L
    situation = {}
    for axis in AXES:
        n = notes[axis]
        pst_ko = {"offensive": "주공", "limited": "제한 공세", "hold": "고수·견제", "defend": "방어선"}[n["posture"]]
        situation[axis] = f"{d2(date)} 종료: {n['core']}({n['band']}). 태세 {pst_ko}" + (f" · {n['stage']}" if n["stage"] and axis == "south" else "") + (f" · {n['prog']}" if n["prog"] else "") + "."

    fronts_out = {a: work["fronts"][a] for a in AXES}
    kf24 = dict(hour=24, events=ev24, fronts=fronts_out, units=unit_ops, arrows=arrow_ops, losses=losses, situation=situation, captures=cum)
    if pocket_ops:
        kf24["pockets"] = pocket_ops
    vv = {k: v for k, v in views.items() if v}
    if vv:
        kf24["views"] = vv
    plan = dict(schema=1, date=date, turn=turn, referee="절차 판정(judge.py, LLM 없음)", generator="judge.py",
                dice=dice, summary=summary, vehicles=vehicles,
                keyframes=[dict(hour=12, events=ev12), kf24],
                judge_state=js, generated_real=iso_kst())
    return plan


def try_pocket(work, js, date, ev24, maxkm=22):
    """남부 s-main 에서 돌출부 목이 maxkm 이내로 좁혀지면 잘라 포위망 생성."""
    segs = work["fronts"]["south"]
    for si, seg in enumerate(segs):
        P = seg["pts"]
        best = None
        for i in range(1, len(P)):
            for j in range(i + 6, len(P) - 1):
                d = dist_km(P[i], P[j])
                if d < maxkm and (best is None or d < best[0]):
                    poly = Polygon([tuple(p) for p in P[i:j + 1]])
                    if poly.is_valid and poly.exterior.is_ccw and poly.area > 0.4:
                        best = (d, i, j, poly)
        if not best:
            continue
        d, i, j, poly = best
        trial = copy.deepcopy(work)
        trial["fronts"]["south"][si]["pts"] = P[:i + 1] + P[j:]
        if not chain_ok(flatten(trial)[0], trial["german_closure"]):
            continue
        work["fronts"] = trial["fronts"]
        c = poly.centroid
        x0, y0, x1, y1 = poly.bounds
        pid = "p-salient-" + date.replace("-", "")
        inside = [u["id"] for u in work["units"] if u["side"] == "su" and u.get("echelon") != "group" and poly.contains(Point(u["lon"], u["lat"]))]
        pk = dict(id=pid, axis="south", name="리보프 돌출부 포위망", lon=round(c.x, 3), lat=round(c.y, 3),
                  rx=round(min(2.9, max(0.3, (x1 - x0) / 2 * 0.75)), 3), ry=round(min(2.9, max(0.2, (y1 - y0) / 2 * 0.75)), 3),
                  label="돌출부 포위망\n" + "·".join(next(u["name"] for u in work["units"] if u["id"] == k)[:8] for k in inside[:3]),
                  lx=round(c.x, 3), ly=round(y0 - 0.15, 3), status="포위")
        js.setdefault("pockets", {})[pid] = dict(units=inside, days=0, pocket=pk)
        js["pockets_made"] = js.get("pockets_made", 0) + 1
        ev24.append(dict(axis="south", kind="pocket", text=f"포위 성립 — 비니차 회랑 차단, 돌출부 소련군({len(inside)}개 제대) 포위망 고립({d2(date)})"))
        return pid
    return None


def upkeep_pockets(work, js, date, notes, unit_ops, ev24, pocket_hits=None):
    ops = []
    b = notes["south"]["band"]
    for pid, P in list((js.get("pockets") or {}).items()):
        pk = P["pocket"]
        if P["days"] == 0:
            ops.append(copy.deepcopy(pk))
        else:
            f = {"유리": 0.8, "기본": 0.88, "불리": 0.96}[b]
            pk["rx"], pk["ry"] = round(pk["rx"] * f, 3), round(pk["ry"] * f, 3)
            ops.append(dict(id=pid, rx=pk["rx"], ry=pk["ry"]))
            for uid in P["units"]:
                u = next((x for x in work["units"] if x["id"] == uid), None)
                if not u:
                    continue
                op = next((x for x in unit_ops if x.get("id") == uid), None)
                if op is None:
                    op = {"id": uid}; unit_ops.append(op)
                op["lon"] = round(u["lon"] + (pk["lon"] - u["lon"]) * 0.25, 4)
                op["lat"] = round(u["lat"] + (pk["lat"] - u["lat"]) * 0.25, 4)
                op["strength"] = max(2, (u.get("strength") or 10) - {"유리": 6, "기본": 4, "불리": 1}[b])
        P["days"] += 1
        if pk["rx"] < 0.2 or P["days"] > 16:
            ops = [o for o in ops if o["id"] != pid] + [{"id": pid, "remove": True}]
            for uid in P["units"]:
                unit_ops[:] = [x for x in unit_ops if x.get("id") != uid] + [{"id": uid, "remove": True}]
            ev24.append(dict(axis="south", kind="pocket", text=f"{pk['name']} 소멸({P['days']}일) — 포위 제대 괴멸·일부 소규모 탈출"))
            if pocket_hits is not None:
                pocket_hits["eliminated"].append(pk.get("axis") or "south")
            del js["pockets"][pid]
        elif P["days"] > 1:
            ev24.append(dict(axis="south", kind="pocket", text=f"{pk['name']} {P['days']}일째 축소 — 17군·11군 소탕, 소련 탈출 시도"))
            if pocket_hits is not None:
                pocket_hits["reduced"].append(pk.get("axis") or "south")
    return ops


def ensure_plan(st, date):
    """오늘 계획이 있으면 그대로(멱등), 없으면 생성·원자적 저장."""
    p = plan_path(date)
    if os.path.exists(p):
        return load_json(p), False
    plan = make_plan(st, date)
    errs, warns = AP.validate(plan, st)
    if errs:
        raise RuntimeError("judge 계획 검증 실패: " + "; ".join(errs[:5]))
    save_json(p, plan)
    return plan, True


if __name__ == "__main__":
    st = load_state()
    date = sys.argv[2] if len(sys.argv) > 2 else st["clock"]["date"]
    pl, new = ensure_plan(st, date)
    print("plan", date, "new" if new else "exists", json.dumps(pl["summary"], ensure_ascii=False))
