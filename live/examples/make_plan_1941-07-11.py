#!/usr/bin/env python3
"""일일 계획 — 1941-07-11 (턴3 6일차). 주사위: 북13 / 중15 / 남17.
전일(7.10) 종결: 프스코프 ~7km 외곽·오포치카 정리·보리소프 교두보 수축·기갑 정지 해제·NV 교두보 전무."""
import copy, json, os, sys
LIVE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, LIVE)

p10 = json.load(open(os.path.join(LIVE, "plans", "1941-07-10.json")))
kf24 = [k for k in p10["keyframes"] if k["hour"] == 24][0]
F0 = copy.deepcopy(kf24["fronts"])


def lerp(a, b, t):
    return a + (b - a) * t


def lerp_pts(a, b, t):
    return [[round(lerp(p[0], q[0], t), 3), round(lerp(p[1], q[1], t), 3)] for p, q in zip(a, b)]


def segs(axis_id_style_pts):
    return [dict(id=i, style=s, pts=copy.deepcopy(pts)) for i, s, pts in axis_id_style_pts]


# --- 목표 전선 (7.11@24) ---
# 북부(기본13): 프스코프 남쪽 외곽~시가 남단 접근(~3km). 에스토니아 소폭(타르투).
N_EST_END = [
    [24.4, 58.45], [25.25, 58.38], [26.05, 58.36],
    [26.7, 58.4], [27.25, 58.38], [27.72, 58.22],
]
N_GAP_END = [
    [27.72, 58.22], [27.82, 58.26], [28.15, 58.08],
    [28.42, 58.18], [28.5, 58.2],
]
# n-stalin: 북단 프스코프 남쪽 외곽/시가 남단(~3km), 남으로 오포치카·중부 경계
N_STALIN_END = [
    [28.5, 58.2],
    [28.68, 58.0],
    [28.74, 57.75],
    [28.55, 57.48],
    [28.22, 57.28],
    [28.2, 57.22],
    [28.19, 56.9],
    [28.14, 56.55],
    [28.1, 56.22],
    [28.18, 55.88],
    [28.3, 55.6],
]

# 중부(기본15): 가교 수리·교두보 소폭 재확장(돌파 아님). 보브루이스크 미도하.
C_DVINA_END = [
    [28.3, 55.6],
    [28.47, 55.32],
    [28.5, 55.05],
    [28.7, 54.88],
    [28.68, 54.48],   # 교두보 소폭 재확장(동안으로)
    [28.85, 54.15],
    [28.95, 53.82],
    [29.1, 53.48],
    [29.1, 53.12],
    [28.92, 52.85],
]
C_PRIP_END = copy.deepcopy(F0["center"][1]["pts"])
C_PRIP_END[0] = [28.92, 52.85]  # c-dvina 남단과 연속

# 남부(유리17): 슬루치 소형 교두보·선두 기갑 일부 도하(지토미르 가도).
# NV 본대 유지. 11군 드네스트르 소형 교두보.
S_MAIN_END = copy.deepcopy(F0["south"][0]["pts"])
# NV / Sluch bulge east (indices 2–5)
S_MAIN_END[2] = [27.45, 50.74]
S_MAIN_END[3] = [27.72, 50.52]   # 교두보 정점(동진)
S_MAIN_END[4] = [27.55, 50.38]
S_MAIN_END[5] = [26.95, 50.3]
# Dniester small foothold (indices ~22-25)
S_MAIN_END[22] = [27.42, 48.05]
S_MAIN_END[23] = [27.72, 47.98]
S_MAIN_END[24] = [27.58, 47.72]
S_MAIN_END[25] = [27.7, 47.48]


def fronts_at(t):
    return {
        "north": segs([
            ("n-estonia", "solid", lerp_pts(F0["north"][0]["pts"], N_EST_END, t)),
            ("n-gap", "loose", lerp_pts(F0["north"][1]["pts"], N_GAP_END, t)),
            ("n-stalin", "solid", lerp_pts(F0["north"][2]["pts"], N_STALIN_END, t)),
        ]),
        "center": segs([
            ("c-dvina", "solid", lerp_pts(F0["center"][0]["pts"], C_DVINA_END, t)),
            ("c-pripyat", "loose", lerp_pts(F0["center"][1]["pts"], C_PRIP_END, t)),
        ]),
        "south": segs([
            ("s-main", "solid", lerp_pts(F0["south"][0]["pts"], S_MAIN_END, t)),
        ]),
    }


def u(t, start, end, strength=None, **extra):
    d = {"id": start["id"],
         "lon": round(lerp(start["lon"], end["lon"], t), 3),
         "lat": round(lerp(start["lat"], end["lat"], t), 3)}
    if strength is not None:
        d["strength"] = strength
    d.update(extra)
    return d


# 7.10@24 부대 위치 (plan upsert 기준; su-13a 는 이미 remove)
U0 = {x["id"]: x for x in kf24["units"] if not x.get("remove")}


def unit_track(uid, lon, lat, strength=None):
    s = U0[uid]
    return {"id": uid, "lon0": s.get("lon", lon), "lat0": s.get("lat", lat),
            "lon1": lon, "lat1": lat, "s0": s.get("strength"), "s1": strength}


# 종결 목표 위치·전투력
TRACKS = [
    # north: 41pz → 프스코프 남쪽 외곽/시가 남단 ~3km
    unit_track("de-41pz", 28.45, 58.22, 67),
    unit_track("de-56pz", 28.52, 57.78, 76),
    unit_track("de-18a", 26.78, 58.4, 84),
    unit_track("de-16a", 28.55, 56.85, 82),
    unit_track("su-8a", 26.48, 58.55, 45),
    unit_track("su-41rc", 28.9, 58.28, 34),
    unit_track("su-1mech", 29.4, 58.05, 32),  # 재편 지속
    unit_track("su-27a", 28.88, 56.55, 30),
    # center: 가교 수리·교두보 소폭 재확장
    unit_track("de-3pzg", 29.08, 54.3, 70),
    unit_track("de-2pzg", 28.72, 53.22, 78),
    unit_track("de-4a", 27.35, 53.5, 88),
    unit_track("de-9a", 25.3, 53.55, 88),
    unit_track("su-3-10a", 29.22, 53.0, 20),
    unit_track("su-20a", 29.28, 55.0, 45),  # 레펠 소강
    unit_track("su-borisov", 29.28, 54.32, 37),
    unit_track("su-bobr", 29.4, 53.25, 51),
    # south: 슬루치 도하·교두보, 24기계화 반격 소모, 11군 소형 교두보
    unit_track("de-3mot", 27.58, 50.48, 54),
    unit_track("de-48mot", 26.72, 50.34, 63),
    unit_track("de-6a", 26.88, 50.72, 81),
    unit_track("su-nv", 27.98, 50.68, 57),
    unit_track("su-24mech", 27.8, 50.42, 47),
    unit_track("su-5a", 27.68, 50.98, 42),
    unit_track("de-11a", 27.98, 48.28, 81),
    unit_track("su-12a", 27.58, 48.38, 68),
    unit_track("su-16mech", 28.62, 48.28, 63),
]


def units_at(t, strength_override=None):
    out = []
    for tr in TRACKS:
        s = None
        if tr["s1"] is not None and tr["s0"] is not None:
            s = int(round(lerp(tr["s0"], tr["s1"], t)))
        elif tr["s1"] is not None:
            s = tr["s1"]
        if strength_override and tr["id"] in strength_override:
            s = strength_override[tr["id"]]
        d = {"id": tr["id"],
             "lon": round(lerp(tr["lon0"], tr["lon1"], t), 3),
             "lat": round(lerp(tr["lat0"], tr["lat1"], t), 3)}
        if s is not None:
            d["strength"] = s
        out.append(d)
    return out


def arrows_at(phase):
    """phase: 0..1 day progress → goal labels."""
    km = max(2, round(7 - 4 * phase))  # 7 → ~3
    bob_goal = "교두보 재확장" if phase >= 0.35 else "가교 수리"
    sluch = ("교두보 확보" if phase >= 0.7 else
             ("선두 도하" if phase >= 0.35 else "슬루치 도하"))
    dniester = "소형 교두보" if phase >= 0.55 else "도하 강행"
    return [
        {"id": "a-41pz", "goal": f"→ 프스코프(~{km}km)",
         "pts": [[28.52, 58.05], [28.48, 58.12 + 0.06 * phase], [28.45, 58.18 + 0.05 * phase]],
         "label": f"4기갑집단(41군단)\n→ 프스코프(~{km}km)", "lx": 27.4, "ly": 57.95},
        {"id": "a-1mech", "goal": "재편",
         "pts": [[29.4, 58.08], [29.28, 58.0], [29.15, 57.92]],
         "label": "1기계화군단\n(재편 중)", "lx": 29.55, "ly": 57.88},
        {"id": "a-16a", "goal": "오포치카 정리",
         "pts": [[28.3, 56.6], [28.45, 56.72], [28.55, 56.85]]},
        {"id": "a-18a", "goal": "→ 타르투",
         "pts": [[26.35, 58.18], [26.55, 58.32], [26.78, 58.42]]},
        {"id": "a-3pzg", "goal": bob_goal,
         "pts": [[28.9, 54.32], [28.98, 54.3], [29.05 + 0.05 * phase, 54.28]],
         "label": f"3기갑집단\n({bob_goal})", "lx": 27.75, "ly": 54.55},
        {"id": "a-2pzg", "goal": "→ 보브루이스크(대기)",
         "pts": [[28.3, 53.25], [28.72, 53.22], [29.2, 53.18]]},
        {"id": "a-20a", "goal": "레펠 소강",
         "pts": [[29.35, 55.05], [29.2, 55.0], [29.05, 54.96]],
         "label": "20군 기계화\n레펠 소강", "lx": 29.5, "ly": 54.72},
        {"id": "a-1pzg", "goal": sluch,
         "pts": [[27.1, 50.52], [27.35, 50.5], [27.55 + 0.1 * phase, 50.48]],
         "label": f"1기갑집단\n({sluch})", "lx": 25.95, "ly": 50.95},
        {"id": "a-24mech", "goal": "교두보 반격",
         "pts": [[28.05, 50.35], [27.9, 50.4], [27.7, 50.45]],
         "label": "24기계화군단\n교두보 반격", "lx": 28.2, "ly": 50.15},
        {"id": "a-5a", "goal": "야간 기습",
         "pts": [[28.15, 51.1], [27.9, 51.04], [27.6, 50.98]]},
        {"id": "a-11a", "goal": dniester,
         "pts": [[27.5, 47.95], [27.75, 48.1], [27.95, 48.25]],
         "label": f"11군·루마니아군\n{dniester}", "lx": 26.55, "ly": 47.55},
    ]


def losses_at(t):
    # cumulative game estimates — from 07-10 end north19/42, center15/49, south27/34
    return {
        "north": {
            "de_pct": int(round(lerp(19, 20, t))),
            "su_pct": int(round(lerp(42, 44, t))),
            "de_text": "독 기갑·기계화 ~%d%%(프스코프 외곽)" % int(round(lerp(19, 20, t))),
            "su_text": "소련 북서전선 ~%d%%(외곽·지연)" % int(round(lerp(42, 44, t))),
        },
        "center": {
            "de_pct": int(round(lerp(15, 16, t))),
            "su_pct": int(round(lerp(49, 50, t))),
            "de_text": "독 ~%d%%(가교 수리·교두보)" % int(round(lerp(15, 16, t))),
            "su_text": "소련 서부전선 ~%d%%(교두보 압박·소강)" % int(round(lerp(49, 50, t))),
        },
        "south": {
            "de_pct": int(round(lerp(27, 30, t))),
            "su_pct": int(round(lerp(34, 37, t))),
            "de_text": "독 1기갑집단 ~%d%%(슬루치 도하 돌격)" % int(round(lerp(27, 30, t))),
            "su_text": "소련 남서전선 기계화·제병 ~%d%%(반격 소모)" % int(round(lerp(34, 37, t))),
        },
    }


def situation_at(t):
    km = max(2, round(7 - 4 * t))
    if t < 0.35:
        n = f"7.11 새벽 프스코프 ~{km}km 외곽 돌입 개시. 1기계화 재편. 오포치카 정리 지속."
        c = "보리소프 비상 가교 수리·보병 재투입. 교두보 소폭 재확장 준비."
        s = "슬루치 도하 개시(유리). 공병·3자동차화 선두. 24기계화 반격 대기."
    elif t < 0.7:
        n = f"프스코프 남쪽 외곽·시가 남단 ~{km}km. 교량 폭파 위협으로 시가 전면 점령 보류. 타르투 소폭 압박."
        c = "가교 통행 재개·교두보 소폭 동진. 보브루이스크 미도하. 레펠 소강·브레스트 항전."
        s = "슬루치 소형 교두보 형성·선두 기갑 일부 도하. 24기계화 반격으로 확장 둔화. 11군 드네스트르 도하 강행."
    else:
        n = f"7.11 프스코프 남쪽 외곽/~{km}km(시가 미완전 장악). 1기계화 재편 미완. 오포치카·중부 접촉 유지."
        c = "보리소프 교두보 소폭 재확장(기본). 보브루이스크 미도하. 레펠 소강. 브레스트 항전."
        s = "슬루치 소형 교두보 유지·지토미르 가도 선두만. NV 본대 유지. 11군 드네스트르 소형 교두보."
    return {"north": n, "center": c, "south": s}


plan = {
    "schema": 1,
    "date": "1941-07-11",
    "turn": 3,
    "referee": "라이브 매시 판정 — 턴3 6일차, 주사위 북13/중15/남17",
    "dice": [
        {"axis": "north", "roll": 13, "band": "기본",
         "note": "프스코프 남쪽 외곽·시가 남단(~3km)까지 추진. 벨리카야 교량 폭파 위협으로 시가 완전 점령은 미완. 타르투 소폭 압박"},
        {"axis": "center", "roll": 15, "band": "기본",
         "note": "보리소프 비상 가교 수리·교두보 소폭 재확장. 돌파·보브루이스크 도하는 없음. 레펠 소강·브레스트 항전"},
        {"axis": "south", "roll": 17, "band": "유리",
         "note": "슬루치 도하 성공·소형 교두보. 선두 기갑 일부 지토미르 가도. 24기계화 반격으로 확장은 둔화되나 교두보 유지. 11군 드네스트르 소형 교두보"},
    ],
    "summary": {
        "north": "주사위 13(기본): 41군단이 프스코프 남쪽 외곽·시가 남단(~3km)까지 접근, 교량 위협으로 시가 완전 점령 미완. 1기계화 재편. 타르투 소폭·오포치카·중부 접촉.",
        "center": "주사위 15(기본): 보리소프 가교 수리·교두보 소폭 재확장(돌파 아님). 보브루이스크 미도하. 레펠 소강. 브레스트 항전.",
        "south": "주사위 17(유리): 슬루치 소형 교두보 형성·선두 기갑 도하. 24기계화 반격으로 확장 둔화. NV 본대 유지. 11군 드네스트르 소형 교두보.",
    },
    "keyframes": [],
}

KF_META = [
    (6, 0.15, [
        {"axis": "north", "text": "41기갑군단, 새벽부터 프스코프 남쪽 외곽 토치카 지대로 재돌입(주사위 13). 41소총군단은 시가 남단·교량 접근로에서 지연전."},
        {"axis": "center", "text": "보리소프 공병, 야간 비상 가교 경간을 연결하고 보병·대전차포 재투입(주사위 15). 전차 대량 재투입은 아직 아님."},
        {"axis": "south", "text": "3자동차화군단 공병돌격대, 슬루치 도하점 한 곳에 집중(주사위 17 유리). 슈투카가 대안에서 토치카를 제압."},
    ], {"de-3mot": 56, "su-24mech": 51}),
    (12, 0.45, [
        {"axis": "north", "text": "정오, 41군단 선두가 프스코프 남쪽 약 4~5km 외곽 지구와 교전. 벨리카야 교량에 폭파 장약이 관측되어 시가 돌입은 보류."},
        {"axis": "north", "text": "18군, 타르투 접근로를 소폭 압박. 8군은 파르누~타르투 선 고수. 1기계화는 여전히 재편·탄약 대기."},
        {"axis": "center", "text": "가교 통행 재개로 교두보가 전날보다 소폭 동진. 수비대 포병은 집적 지점을 견제하나 야간만큼의 타격은 못 함."},
        {"axis": "center", "text": "레펠 방면 20군 기계화는 탄약·늪지로 소강. 2기갑은 보브루이스크 맞은편 대기 유지. 브레스트 항전."},
        {"axis": "south", "text": "슬루치 소형 교두보 형성 — 보병·공병 이어 선두 전차 중대가 동안으로. 24기계화가 교두보 어깨를 즉시 반격."},
        {"axis": "south", "text": "11군·루마니아군, 모길료프-포돌스키 방면 드네스트르 도하를 강행. 12군 요새포가 집결지를 타격."},
    ], {"de-3mot": 55, "su-24mech": 49, "de-41pz": 68, "su-borisov": 38}),
    (18, 0.75, [
        {"axis": "north", "text": "해질녘, 41군단 선두 프스코프 남쪽 외곽·시가 남단(~3km). 교량 폭파 위협으로 시가 완전 점령 명령은 유보."},
        {"axis": "north", "text": "16군 오포치카 잔적 정리·폴로츠크 방면 중부 좌익 접촉 유지. 1기계화 재편은 여전히 미완."},
        {"axis": "center", "text": "교두보 소폭 재확장 상태로 야간 방어 준비. 전차 주력은 서안·교두보에 분산. 보브루이스크 도하 없음."},
        {"axis": "center", "text": "브레스트 요새는 포격·돌격에도 항전 계속. 레펠은 소강 유지."},
        {"axis": "south", "text": "24기계화 반격이 교두보 확장을 둔화시키나 소멸시키진 못함. 선두 기갑만 지토미르 가도 진입로에 도달."},
        {"axis": "south", "text": "11군, 드네스트르 동안에 소형 교두보를 확보. NV 요새 본대 벨트는 여전히 유지."},
    ], None),
    (24, 1.0, [
        {"axis": "north", "text": "하루 종료: 프스코프 남쪽 외곽/~3km(주사위 13 기본). 시가 완전 점령 미완. 오포치카·중부 접촉·타르투 소폭. 1기계화 재편 미완."},
        {"axis": "center", "text": "보리소프 교두보 소폭 재확장(주사위 15 기본). 보브루이스크 미도하. 레펠 소강. 브레스트 항전."},
        {"axis": "south", "text": "슬루치 소형 교두보 유지·선두만 지토미르 가도(주사위 17 유리). NV 본대 유지. 11군 드네스트르 소형 교두보."},
    ], None),
]

pockets_seq = [
    [{"id": "p-brest", "status": "항전", "label": "브레스트 요새\n항전 중"}],
    [{"id": "p-brest", "status": "항전", "label": "브레스트 요새\n항전 중"}],
    [{"id": "p-brest", "status": "항전", "label": "브레스트 요새\n항전 중"}],
    [{"id": "p-brest", "status": "항전", "label": "브레스트 요새\n항전 중"}],
]

for (hour, t, events, sov), pockets in zip(KF_META, pockets_seq):
    # length check helper at build time
    for e in events:
        if len(e["text"]) > 220:
            raise SystemExit(f"event too long h={hour} axis={e['axis']}: {len(e['text'])}")
    kf = {
        "hour": hour,
        "events": events,
        "fronts": fronts_at(t),
        "units": units_at(t, sov),
        "pockets": pockets,
        "arrows": arrows_at(t),
        "losses": losses_at(t),
        "situation": situation_at(t),
    }
    plan["keyframes"].append(kf)

out = "/tmp/plan-1941-07-11.json"
json.dump(plan, open(out, "w"), ensure_ascii=False, indent=1)
print("wrote", out, "keyframes", len(plan["keyframes"]))
# continuity report
kf = plan["keyframes"][-1]
n_end = kf["fronts"]["north"][2]["pts"][-1]
c_start = kf["fronts"]["center"][0]["pts"][0]
c_mid = kf["fronts"]["center"][0]["pts"][-1]
c_prip0 = kf["fronts"]["center"][1]["pts"][0]
c_prip1 = kf["fronts"]["center"][1]["pts"][-1]
s0 = kf["fronts"]["south"][0]["pts"][0]
print("N-C boundary", n_end, c_start, "match", n_end == c_start)
print("C mid", c_mid, c_prip0)
print("C-S boundary", c_prip1, s0, "match", c_prip1 == s0)
for k in plan["keyframes"]:
    for e in k["events"]:
        print(f"  h{k['hour']} {e['axis']}: {len(e['text'])}c")
