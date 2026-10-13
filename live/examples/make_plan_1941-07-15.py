#!/usr/bin/env python3
"""일일 계획 — 1941-07-15 (턴4 3일차). 주사위: 북12 기본 / 중1 불리 / 남8 기본.
전일(7.14) 종결: 프스코프 남동 동안 교두보 소폭 / 보리소프·보브루이스크 재확보 / 슬루치 가도 동진·입구 교착.
7.15: 북 동안 동북 확장·1기계화 24h 국지반격 / 중 보브루이스크 재붕괴·보리소프 급축 / 남 6군 어깨 인수·가도 소폭."""
import copy, json, os, sys
LIVE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, LIVE)

# Prefer end_07-14 snapshot; fall back to plan hour-24
end_path = "/tmp/end_07-14.json"
if os.path.exists(end_path):
    end = json.load(open(end_path))
    F0 = copy.deepcopy(end["fronts"])
    U0_list = end["units"]
else:
    p14 = json.load(open(os.path.join(LIVE, "plans", "1941-07-14.json")))
    kf24 = [k for k in p14["keyframes"] if k["hour"] == 24][0]
    F0 = copy.deepcopy(kf24["fronts"])
    U0_list = kf24["units"]


def lerp(a, b, t):
    return a + (b - a) * t


def lerp_pts(a, b, t):
    return [[round(lerp(p[0], q[0], t), 3), round(lerp(p[1], q[1], t), 3)] for p, q in zip(a, b)]


def segs(axis_id_style_pts):
    return [dict(id=i, style=s, pts=copy.deepcopy(pts)) for i, s, pts in axis_id_style_pts]


# --- 목표 전선 (7.15@24) ---
# 북부(기본12): 동안 교두보 동북(스트루기) 소폭 확장, 루가 도로 미완전 차단, 1기계화 반격으로 둔화. 시가 미완전.
N_EST_END = [
    [24.4, 58.46], [25.25, 58.39], [26.05, 58.37],
    [26.86, 58.45], [27.42, 58.43], [27.82, 58.26],
]
N_GAP_END = [
    [27.82, 58.26], [27.92, 58.28], [28.24, 58.10],
    [28.56, 58.14], [28.80, 58.14],
]
N_STALIN_END = [
    [28.80, 58.14],  # 동북 소폭 (스트루기 접근·도로 미차단)
    [28.86, 58.06],
    [28.84, 57.76],
    [28.55, 57.48],
    [28.22, 57.28],
    [28.2, 57.22],
    [28.2, 56.92],
    [28.16, 56.58],
    [28.12, 56.24],
    [28.18, 55.88],
    [28.3, 55.6],
]

# 중부(불리1): 보브루이스크 동안 붕괴·철수, 보리소프 급축(가교 손상), 레펠 소강/소폭 후퇴. 모길료프 미도하.
C_DVINA_END = [
    [28.3, 55.6],
    [28.48, 55.30],
    [28.55, 55.02],  # 레펠 소폭 후퇴
    [28.78, 54.85],
    [28.92, 54.38],  # 보리소프 급축
    [29.02, 54.08],
    [29.08, 53.74],
    [29.12, 53.42],
    [29.00, 53.12],  # 보브루이스크 동안 소멸(서안 근처)
    [28.94, 52.85],
]
C_PRIP_END = copy.deepcopy(F0["center"][1]["pts"])
C_PRIP_END[0] = [28.94, 52.85]

# 남부(기본8): 가도 소폭 동진(테테레프 미달), 입구 교착 유지(6군 AT/88 둔화), 남어깨 소폭, 드네스트르 소폭.
S_MAIN_END = copy.deepcopy(F0["south"][0]["pts"])
S_MAIN_END[2] = [27.74, 50.65]
S_MAIN_END[3] = [28.42, 50.40]  # 가도 소폭 동진
S_MAIN_END[4] = [27.92, 50.30]  # 입구 어깨 교착
S_MAIN_END[5] = [27.12, 50.28]  # 남어깨 소폭
S_MAIN_END[22] = [27.72, 48.16]
S_MAIN_END[23] = [28.22, 48.15]  # 드네스트르 소폭
S_MAIN_END[24] = [27.76, 47.78]
S_MAIN_END[25] = [27.86, 47.52]


def fronts_at(t):
    # Center collapse is front-loaded (night/dawn smash): accelerate early pullback
    tc = t ** 0.7 if t > 0 else 0  # slightly front-loaded
    # North: expand mid-day then blunt — use linear to end (end already blunted)
    # South: steady modest
    return {
        "north": segs([
            ("n-estonia", "solid", lerp_pts(F0["north"][0]["pts"], N_EST_END, t)),
            ("n-gap", "loose", lerp_pts(F0["north"][1]["pts"], N_GAP_END, t)),
            ("n-stalin", "solid", lerp_pts(F0["north"][2]["pts"], N_STALIN_END, t)),
        ]),
        "center": segs([
            ("c-dvina", "solid", lerp_pts(F0["center"][0]["pts"], C_DVINA_END, tc)),
            ("c-pripyat", "loose", lerp_pts(F0["center"][1]["pts"], C_PRIP_END, tc)),
        ]),
        "south": segs([
            ("s-main", "solid", lerp_pts(F0["south"][0]["pts"], S_MAIN_END, t)),
        ]),
    }


U0 = {x["id"]: x for x in U0_list if not x.get("remove")}


def unit_track(uid, lon, lat, strength=None):
    s = U0[uid]
    return {"id": uid, "lon0": s.get("lon", lon), "lat0": s.get("lat", lat),
            "lon1": lon, "lat1": lat, "s0": s.get("strength"), "s1": strength}


TRACKS = [
    # north: 41pz 동북 소폭, 1mech 반격 접근, 시가 기갑 미투입
    unit_track("de-41pz", 29.05, 58.08, 54),
    unit_track("de-56pz", 28.82, 57.98, 70),
    unit_track("de-18a", 27.12, 58.52, 80),
    unit_track("de-16a", 28.75, 56.95, 79),
    unit_track("su-8a", 26.25, 58.62, 38),
    unit_track("su-41rc", 28.92, 58.26, 25),
    unit_track("su-1mech", 29.05, 58.18, 30),  # 국지반격 후 소모
    unit_track("su-27a", 29.08, 56.72, 27),
    # center: 2pzg 서안 철수, 3pzg 교두보 축소·일부 서안, 20a 육교 예비 도착
    unit_track("de-3pzg", 28.95, 54.30, 61),
    unit_track("de-2pzg", 28.85, 53.18, 64),
    unit_track("de-4a", 27.75, 53.55, 85),
    unit_track("de-9a", 25.55, 53.55, 87),
    unit_track("su-3-10a", 29.60, 52.88, 15),
    unit_track("su-20a", 29.65, 54.70, 39),  # 육교 예비 도착
    unit_track("su-borisov", 29.42, 54.28, 32),
    unit_track("su-bobr", 29.40, 53.20, 48),
    # south: 3mot 가도 소폭, 6a 북쪽 어깨 인수, 24mech 입구 둔화, 48mot 남어깨
    unit_track("de-3mot", 28.48, 50.36, 45),
    unit_track("de-48mot", 27.28, 50.32, 57),
    unit_track("de-6a", 27.70, 50.52, 76),
    unit_track("su-nv", 28.30, 50.52, 42),
    unit_track("su-24mech", 27.98, 50.30, 29),
    unit_track("su-5a", 28.15, 50.76, 35),
    unit_track("de-11a", 28.55, 48.52, 76),
    unit_track("su-12a", 27.42, 48.26, 60),
    unit_track("su-16mech", 28.30, 48.30, 57),
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
    if phase < 0.35:
        n_goal = "동안 동북 확장"
        mech_goal = "국지반격 개시"
    elif phase < 0.75:
        n_goal = "스트루기 접근"
        mech_goal = "교두보 둔화"
    else:
        n_goal = "루가도로 미차단"
        mech_goal = "국지반격 종료"

    if phase < 0.35:
        bob = "가교 피격"
        bobr = "야간 붕괴"
    elif phase < 0.75:
        bob = "교두보 급축"
        bobr = "동안 철수"
    else:
        bob = "확장 정지"
        bobr = "서안 고수"

    if phase < 0.35:
        sluch = "어깨 인수"
    elif phase < 0.75:
        sluch = "가도 소폭 동진"
    else:
        sluch = "테테레프 미달"

    dniester = "비니차 소폭" if phase >= 0.4 else "드네스트르 유지"

    # tip coords evolve with phase
    tip_n = 28.95 + 0.10 * phase
    tip_n_lat = 58.0 + 0.08 * phase
    tip_c3 = 29.25 - 0.30 * min(1.0, phase * 1.2)
    tip_c2 = 29.30 - 0.45 * min(1.0, phase * 1.2)
    tip_s = 28.35 + 0.13 * phase

    return [
        {"id": "a-41pz", "goal": n_goal,
         "pts": [[28.75, 57.95], [28.90, 58.02], [tip_n, tip_n_lat]],
         "label": f"4기갑집단(41군단)\n{n_goal}", "lx": 27.4, "ly": 57.85},
        {"id": "a-1mech", "goal": mech_goal,
         "pts": [[29.25, 58.22], [29.15, 58.20], [29.05, 58.16]],
         "label": f"1기계화군단\n({mech_goal})", "lx": 29.55, "ly": 57.95},
        {"id": "a-16a", "goal": "노보르제프",
         "pts": [[28.4, 56.7], [28.55, 56.82], [28.75, 56.95]]},
        {"id": "a-18a", "goal": "→ 타르투·포위",
         "pts": [[26.5, 58.25], [26.8, 58.40], [27.12, 58.52]]},
        {"id": "a-3pzg", "goal": bob,
         "pts": [[28.85, 54.28], [28.90, 54.30], [tip_c3, 54.32]],
         "label": f"3기갑집단\n({bob})", "lx": 27.8, "ly": 54.55},
        {"id": "a-2pzg", "goal": bobr,
         "pts": [[28.6, 53.2], [28.75, 53.18], [tip_c2, 53.16]],
         "label": f"2기갑집단\n({bobr})", "lx": 27.75, "ly": 53.1},
        {"id": "a-20a", "goal": "육교 예비 도착",
         "pts": [[29.50, 55.0], [29.58, 54.85], [29.65, 54.70]],
         "label": "20군 기계화\n육교 예비 도착", "lx": 29.8, "ly": 54.55},
        {"id": "a-1pzg", "goal": sluch,
         "pts": [[27.6, 50.45], [28.0, 50.42], [tip_s, 50.38]],
         "label": f"1기갑집단\n({sluch})", "lx": 26.2, "ly": 50.9},
        {"id": "a-24mech", "goal": "입구 공격·둔화",
         "pts": [[28.25, 50.28], [28.10, 50.30], [27.98, 50.30]],
         "label": "24기계화군단\n입구 공격·둔화", "lx": 28.45, "ly": 50.08},
        {"id": "a-5a", "goal": "테테레프 2차선",
         "pts": [[28.4, 50.95], [28.25, 50.85], [28.15, 50.76]]},
        {"id": "a-11a", "goal": dniester,
         "pts": [[27.75, 48.08], [28.15, 48.28], [28.4 + 0.15 * phase, 48.48]],
         "label": f"11군·루마니아군\n{dniester}", "lx": 26.7, "ly": 47.6},
    ]


def losses_at(t):
    # from 07-14 end: N26/52, C22/52, S36/48 → end N28/54, C25/53, S37/49
    return {
        "north": {
            "de_pct": int(round(lerp(26, 28, t))),
            "su_pct": int(round(lerp(52, 54, t))),
            "de_text": "독 기갑·기계화 ~%d%%(교두보 확장·반격)" % int(round(lerp(26, 28, t))),
            "su_text": "소련 북서전선 ~%d%%(1기계화 국지반격)" % int(round(lerp(52, 54, t))),
        },
        "center": {
            "de_pct": int(round(lerp(22, 25, t))),
            "su_pct": int(round(lerp(52, 53, t))),
            "de_text": "독 ~%d%%(보브루이스크 붕괴·가교 손상)" % int(round(lerp(22, 25, t))),
            "su_text": "소련 서부전선 ~%d%%(야간 국지공격·육교 도착)" % int(round(lerp(52, 53, t))),
        },
        "south": {
            "de_pct": int(round(lerp(36, 37, t))),
            "su_pct": int(round(lerp(48, 49, t))),
            "de_text": "독 1기갑집단 ~%d%%(가도·어깨)" % int(round(lerp(36, 37, t))),
            "su_text": "소련 남서전선 ~%d%%(입구 공격 둔화)" % int(round(lerp(48, 49, t))),
        },
    }


def situation_at(t):
    if t < 0.35:
        n = "7.15 새벽 동안 교두보 동북 확장 개시(기본12). 1기계화 스트루기 국지반격 출동. 시가 기갑 미투입."
        c = "보브루이스크 동안 야간 기습으로 붕괴 개시(불리1). 보리소프 가교 포병 피해. 브레스트 항전."
        s = "6군 보병·대전차포가 슬루치 북쪽 어깨 인수(기본8). 24기계화 입구 공격 지속. 가도 동진 준비."
    elif t < 0.75:
        n = "41기갑 스트루기 방향 접근·루가 도로 미차단. 1기계화 반격으로 확장 둔화. 타르투·오포치카."
        c = "보브루이스크 동안 철수·일부 기갑 서안. 보리소프 교두보 급축·확장 정지. 레펠 소강. 육교 예비 도착."
        s = "가도 소폭 동진·테테레프 미달. AT/88이 입구 공격 둔화·교두보 유지. 11군 비니차 소폭. NV 배후."
    else:
        n = "7.15 동안 동북 소폭·1기계화 반격으로 둔화(기본12). 루가 도로 미차단·시가 미완전. 타르투·오포치카."
        c = "보브루이스크 재붕괴·보리소프 급축(불리1). 레펠 소강. 육교 예비 도착. 모길료프 미도하. 브레스트 항전."
        s = "6군 어깨 인수·입구 교착 유지(기본8). 가도 소폭·테테레프 미달. 드네스트르 소폭. NV 요새선 유지."
    return {"north": n, "center": c, "south": s}


plan = {
    "schema": 1,
    "date": "1941-07-15",
    "turn": 4,
    "referee": "라이브 매시 판정 — 턴4 명령 지속, 주사위 북12/중1/남8",
    "dice": [
        {"axis": "north", "roll": 12, "band": "기본",
         "note": "동안 교두보 동북(스트루기) 소폭 확장. 1기계화 24h 국지반격으로 둔화·쌍방 소모. 루가 도로 미완전 차단·시가 기갑 미투입"},
        {"axis": "center", "roll": 1, "band": "불리",
         "note": "보브루이스크 동안 야간 국지공격으로 재붕괴·철수. 보리소프 가교 중포 손상·교두보 급축·확장 정지. 레펠 소강. 육교 예비 도착. 브레스트 항전"},
        {"axis": "south", "roll": 8, "band": "기본",
         "note": "6군 북쪽 어깨 인수·AT/88로 24기계화 입구 공격 둔화. 가도 소폭 동진·테테레프 미달. 48자동차화 남어깨 소폭. 드네스트르 소폭"},
    ],
    "summary": {
        "north": "주사위 12(기본): 동안 동북 소폭·1기계화 국지반격 둔화. 루가 도로 미차단·시가 미완전. 타르투·오포치카.",
        "center": "주사위 1(불리): 보브루이스크 재붕괴·보리소프 급축. 레펠 소강·육교 예비 도착. 브레스트 항전.",
        "south": "주사위 8(기본): 6군 어깨 인수·입구 교착 유지. 가도 소폭·테테레프 미달. 드네스트르 소폭·NV 유지.",
    },
    "keyframes": [],
}

KF_META = [
    (6, 0.15, [
        {"axis": "north", "text": "새벽, 41기갑군단이 프스코프 남동 동안 교두보를 동북으로 확장 개시(주사위 12 기본). 시가 기갑은 투입 안 함. 1기계화 스트루기에서 반격 출동."},
        {"axis": "center", "text": "새벽 직전, 소련 보브루이스크 수비대가 동안 소형 교두보를 야간 국지공격(주사위 1 불리) — 가교 파손·철수 개시."},
        {"axis": "south", "text": "6군 선두 보병·대전차포가 슬루치 북쪽 어깨에 도착·인수 개시(주사위 8 기본). 24기계화 입구 공격 지속."},
    ], {"de-2pzg": 67, "su-bobr": 45}),
    (12, 0.45, [
        {"axis": "north", "text": "정오, 41기갑 선두가 스트루기 방향 접근로에 닿으나 루가 도로는 미차단. 1기계화 국지반격이 교두보 북동 어깨를 압박 — 확장 둔화."},
        {"axis": "north", "text": "18군 타르투 압박 지속, 16군 오포치카-노보르제프. 프스코프 시가는 아직 미완전 점령."},
        {"axis": "center", "text": "보브루이스크 동안 교두보 붕괴·잔여 병력 서안 철수. 일부 전차가 서안에 묶임. 보리소프도 중포에 가교 손상·교두보 급축."},
        {"axis": "center", "text": "레펠~비텝스크 추진 정지·소폭 후퇴. 20군 5·7기계화 잔존이 육교 예비 위치에 도착. 모길료프 우회 도하 미실시. 브레스트 항전."},
        {"axis": "south", "text": "6군 AT·88mm가 입구 공격을 둔화 — 어깨는 교착이나 교두보는 유지. 차량화사단 지토미르 가도 소폭 동진."},
        {"axis": "south", "text": "48자동차화군단 남쪽 어깨 소폭 확장. 11군·루마니아군 드네스트르를 비니차 방향으로 소폭. NV 요새선 배후는 압박받으나 포기 없음."},
    ], {"de-3pzg": 63, "de-2pzg": 65, "su-1mech": 31, "su-24mech": 30}),
    (18, 0.75, [
        {"axis": "north", "text": "해질녘, 1기계화 24시간 국지반격이 교두보 확장을 둔화시키고 쌍방 소모. 동안 발판은 유지되나 루가 도로 차단 실패."},
        {"axis": "north", "text": "56기갑군단 동측방 엄호. 타르투·오포치카 유지. 시가전 기갑 미투입."},
        {"axis": "center", "text": "보리소프 교두보 축소 상태로 방어 전환 — 확장 정지. 보브루이스크는 동안 거점 상실. 중부집단군에 힘든 하루."},
        {"axis": "center", "text": "육교 기동예비 배치 완료. 모길료프 우회·신규 도하 없음. 브레스트 요새 항전 지속."},
        {"axis": "south", "text": "가도 선두는 테테레프 미달에서 정지. 입구는 교착·교두보 유지. 6군 후속 호송·도로 거점 작업."},
        {"axis": "south", "text": "11군 비니차 방향 소폭. 5군 테테레프 2차선 진지. NV 배후 압박은 이어지나 요새벨트 유지."},
    ], None),
    (24, 1.0, [
        {"axis": "north", "text": "하루 종료: 동안 동북 소폭·1기계화 반격 둔화(주사위 12 기본). 루가 도로 미차단·시가 미완전. 타르투·오포치카."},
        {"axis": "center", "text": "보브루이스크 재붕괴·보리소프 급축(주사위 1 불리). 레펠 소강·육교 예비 도착. 모길료프 미도하. 브레스트 항전."},
        {"axis": "south", "text": "6군 어깨 인수·입구 교착 유지(주사위 8 기본). 가도 소폭·테테레프 미달. 드네스트르 소폭. NV 요새선 유지."},
    ], None),
]

pockets_seq = [
    [{"id": "p-brest", "status": "항전", "label": "브레스트 요새\n항전 중"}],
    [{"id": "p-brest", "status": "항전", "label": "브레스트 요새\n항전 중"}],
    [{"id": "p-brest", "status": "항전", "label": "브레스트 요새\n항전 중"}],
    [{"id": "p-brest", "status": "항전", "label": "브레스트 요새\n항전 중"}],
]

for (hour, t, events, sov), pockets in zip(KF_META, pockets_seq):
    for e in events:
        if len(e["text"]) > 220:
            raise SystemExit(f"event too long h={hour} axis={e['axis']}: {len(e['text'])}")
        if "\n" in e["text"]:
            raise SystemExit(f"newline in event h={hour}")
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

out = "/tmp/plan-1941-07-15.json"
json.dump(plan, open(out, "w"), ensure_ascii=False, indent=1)
print("wrote", out, "keyframes", len(plan["keyframes"]))
kf = plan["keyframes"][-1]
n_end = kf["fronts"]["north"][2]["pts"][-1]
c_start = kf["fronts"]["center"][0]["pts"][0]
c_mid = kf["fronts"]["center"][0]["pts"][-1]
c_prip0 = kf["fronts"]["center"][1]["pts"][0]
c_prip1 = kf["fronts"]["center"][1]["pts"][-1]
s0 = kf["fronts"]["south"][0]["pts"][0]
print("N-C boundary", n_end, c_start, "match", n_end == c_start)
print("C mid", c_mid, c_prip0, "match", c_mid == c_prip0)
print("C-S boundary", c_prip1, s0, "match", c_prip1 == s0)
# also check hour-6 starts near F0
kf6 = plan["keyframes"][0]
print("h6 N tip", kf6["fronts"]["north"][2]["pts"][0], "from F0", F0["north"][2]["pts"][0])
print("h6 C bobr tip", kf6["fronts"]["center"][0]["pts"][8], "from F0", F0["center"][0]["pts"][8])
for k in plan["keyframes"]:
    for e in k["events"]:
        print(f"  h{k['hour']} {e['axis']}: {len(e['text'])}c")
print("dice", plan["dice"])
print("summary", plan["summary"])
