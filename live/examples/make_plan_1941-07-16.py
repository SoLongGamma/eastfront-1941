#!/usr/bin/env python3
"""일일 계획 — 1941-07-16 (턴4 4일차). 주사위: 북18 유리 / 중7 기본 / 남6 기본.
전일(7.15) 종결: 동안 동북 소폭·1기계화 반격 둔화 / 보브루이스크 재붕괴·보리소프 급축 / 6군 어깨·가도 소폭.
7.16: 북 41기갑 재추진·스트루기·루가도로 위협(유리) / 중 보브루이스크 소형 재확보·보리소프 소폭 재건(기본) / 남 가도 소폭·입구 교착(기본)."""
import copy, json, os, sys
LIVE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, LIVE)

end_path = "/tmp/end_07-15.json"
if os.path.exists(end_path):
    end = json.load(open(end_path))
    F0 = copy.deepcopy(end["fronts"])
    U0_list = end["units"]
else:
    p15 = json.load(open(os.path.join(LIVE, "plans", "1941-07-15.json")))
    kf24 = [k for k in p15["keyframes"] if k["hour"] == 24][0]
    F0 = copy.deepcopy(kf24["fronts"])
    U0_list = kf24["units"]


def lerp(a, b, t):
    return a + (b - a) * t


def lerp_pts(a, b, t):
    return [[round(lerp(p[0], q[0], t), 3), round(lerp(p[1], q[1], t), 3)] for p, q in zip(a, b)]


def segs(axis_id_style_pts):
    return [dict(id=i, style=s, pts=copy.deepcopy(pts)) for i, s, pts in axis_id_style_pts]


# --- 목표 전선 (7.16@24) ---
# 북부(유리18): 1기계화 국지반격 소진 후 41기갑 재추진 → 스트루기 접근·루가 도로 위협/부분차단. 시가 기갑 미투입.
N_EST_END = [
    [24.4, 58.46], [25.25, 58.39], [26.05, 58.37],
    [26.90, 58.46], [27.48, 58.44], [27.88, 58.28],
]
N_GAP_END = [
    [27.88, 58.28], [27.98, 58.30], [28.30, 58.12],
    [28.62, 58.18], [28.95, 58.20],
]
N_STALIN_END = [
    [28.95, 58.20],  # 스트루기 접근·루가도로 위협
    [28.98, 58.08],
    [28.90, 57.78],
    [28.58, 57.50],
    [28.24, 57.30],
    [28.22, 57.24],
    [28.22, 56.94],
    [28.18, 56.60],
    [28.14, 56.26],
    [28.20, 55.90],
    [28.3, 55.6],
]

# 중부(기본7): 보브루이스크 동안 소형 재확보, 보리소프 가교 수리·교두보 소폭 재건, 레펠 소강/소폭. 모길료프 미도하.
C_DVINA_END = [
    [28.3, 55.6],
    [28.50, 55.30],
    [28.62, 55.04],  # 레펠 소폭
    [28.82, 54.86],
    [29.08, 54.40],  # 보리소프 소폭 재건
    [29.08, 54.10],
    [29.12, 53.76],
    [29.16, 53.44],
    [29.18, 53.14],  # 보브루이스크 동안 소형
    [28.98, 52.85],
]
C_PRIP_END = copy.deepcopy(F0["center"][1]["pts"])
C_PRIP_END[0] = [28.98, 52.85]

# 남부(기본6): 가도 소폭 동진(테테레프 미달), 입구 교착 지속, 남어깨 소폭, 드네스트르 소폭. NV 유지.
S_MAIN_END = copy.deepcopy(F0["south"][0]["pts"])
S_MAIN_END[2] = [27.78, 50.64]
S_MAIN_END[3] = [28.55, 50.38]  # 가도 소폭
S_MAIN_END[4] = [27.95, 50.30]  # 입구 교착
S_MAIN_END[5] = [27.22, 50.28]  # 남어깨 소폭
S_MAIN_END[22] = [27.78, 48.16]
S_MAIN_END[23] = [28.32, 48.16]  # 드네스트르 소폭
S_MAIN_END[24] = [27.80, 47.78]
S_MAIN_END[25] = [27.90, 47.52]


def fronts_at(t):
    # North 유리: mid-day surge then consolidate — slight back-loaded
    tn = t ** 0.85 if t > 0 else 0
    # Center recovery: steady rebuild after dawn pontoon work
    tc = t
    # South: steady modest (low-basic)
    return {
        "north": segs([
            ("n-estonia", "solid", lerp_pts(F0["north"][0]["pts"], N_EST_END, tn)),
            ("n-gap", "loose", lerp_pts(F0["north"][1]["pts"], N_GAP_END, tn)),
            ("n-stalin", "solid", lerp_pts(F0["north"][2]["pts"], N_STALIN_END, tn)),
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
    # north: 41pz 스트루기 재추진, 1mech 소진 후퇴·재편, 시가 기갑 미투입
    unit_track("de-41pz", 29.18, 58.18, 52),
    unit_track("de-56pz", 28.90, 58.02, 69),
    unit_track("de-18a", 27.22, 58.55, 79),
    unit_track("de-16a", 28.82, 57.00, 78),
    unit_track("su-8a", 26.20, 58.65, 37),
    unit_track("su-41rc", 28.95, 58.30, 24),
    unit_track("su-1mech", 29.20, 58.28, 27),  # 반격 소진 후 재편
    unit_track("su-27a", 29.12, 56.75, 26),
    # center: 2pzg 동안 소형 재확보, 3pzg 교두보 소폭 재건, 20a 육교 예비 대기
    unit_track("de-3pzg", 29.10, 54.38, 60),
    unit_track("de-2pzg", 29.10, 53.16, 63),
    unit_track("de-4a", 27.80, 53.55, 85),
    unit_track("de-9a", 25.55, 53.55, 87),
    unit_track("su-3-10a", 29.60, 52.88, 15),
    unit_track("su-20a", 29.68, 54.68, 39),  # 육교 예비 대기
    unit_track("su-borisov", 29.45, 54.30, 31),
    unit_track("su-bobr", 29.42, 53.18, 46),
    # south: 3mot 가도 소폭, 6a 어깨 고수, 24mech 입구 지속, 48mot 남어깨
    unit_track("de-3mot", 28.58, 50.36, 44),
    unit_track("de-48mot", 27.35, 50.30, 56),
    unit_track("de-6a", 27.75, 50.50, 75),
    unit_track("su-nv", 28.28, 50.52, 41),
    unit_track("su-24mech", 28.00, 50.30, 28),
    unit_track("su-5a", 28.20, 50.74, 34),
    unit_track("de-11a", 28.65, 48.55, 75),
    unit_track("su-12a", 27.40, 48.26, 59),
    unit_track("su-16mech", 28.28, 48.30, 56),
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
        n_goal = "재추진 개시"
        mech_goal = "반격 소진·재편"
    elif phase < 0.75:
        n_goal = "스트루기 접근"
        mech_goal = "측방 지연"
    else:
        n_goal = "루가도로 위협"
        mech_goal = "재편 중"

    if phase < 0.35:
        bob = "가교 수리"
        bobr = "소형 재도하"
    elif phase < 0.75:
        bob = "교두보 소폭 재건"
        bobr = "동안 소형 확보"
    else:
        bob = "확장 제한"
        bobr = "서안·동안 유지"

    if phase < 0.35:
        sluch = "가도 재추진"
    elif phase < 0.75:
        sluch = "가도 소폭 동진"
    else:
        sluch = "테테레프 미달"

    dniester = "비니차 소폭" if phase >= 0.4 else "드네스트르 유지"

    tip_n = 29.05 + 0.13 * phase
    tip_n_lat = 58.08 + 0.12 * phase
    tip_c3 = 28.95 + 0.15 * phase
    tip_c2 = 28.85 + 0.25 * phase
    tip_s = 28.48 + 0.10 * phase

    return [
        {"id": "a-41pz", "goal": n_goal,
         "pts": [[28.85, 57.98], [29.00, 58.08], [tip_n, tip_n_lat]],
         "label": f"4기갑집단(41군단)\n{n_goal}", "lx": 27.4, "ly": 57.85},
        {"id": "a-1mech", "goal": mech_goal,
         "pts": [[29.30, 58.30], [29.22, 58.28], [29.15, 58.24]],
         "label": f"1기계화군단\n({mech_goal})", "lx": 29.55, "ly": 57.95},
        {"id": "a-16a", "goal": "포르호프 연결",
         "pts": [[28.5, 56.75], [28.65, 56.88], [28.82, 57.00]]},
        {"id": "a-18a", "goal": "→ 타르투·포위",
         "pts": [[26.55, 58.28], [26.85, 58.42], [27.22, 58.55]]},
        {"id": "a-3pzg", "goal": bob,
         "pts": [[28.90, 54.30], [29.00, 54.34], [tip_c3, 54.38]],
         "label": f"3기갑집단\n({bob})", "lx": 27.8, "ly": 54.55},
        {"id": "a-2pzg", "goal": bobr,
         "pts": [[28.70, 53.18], [28.90, 53.16], [tip_c2, 53.14]],
         "label": f"2기갑집단\n({bobr})", "lx": 27.75, "ly": 53.1},
        {"id": "a-20a", "goal": "육교 예비 대기",
         "pts": [[29.55, 54.95], [29.62, 54.80], [29.68, 54.68]],
         "label": "20군 기계화\n육교 예비 대기", "lx": 29.8, "ly": 54.55},
        {"id": "a-1pzg", "goal": sluch,
         "pts": [[27.7, 50.45], [28.1, 50.42], [tip_s, 50.38]],
         "label": f"1기갑집단\n({sluch})", "lx": 26.2, "ly": 50.9},
        {"id": "a-24mech", "goal": "입구 공격 지속",
         "pts": [[28.28, 50.28], [28.12, 50.30], [28.00, 50.30]],
         "label": "24기계화군단\n입구 공격 지속", "lx": 28.45, "ly": 50.08},
        {"id": "a-5a", "goal": "테테레프 2차선",
         "pts": [[28.45, 50.95], [28.30, 50.85], [28.20, 50.74]]},
        {"id": "a-11a", "goal": dniester,
         "pts": [[27.80, 48.10], [28.20, 48.30], [28.5 + 0.15 * phase, 48.50]],
         "label": f"11군·루마니아군\n{dniester}", "lx": 26.7, "ly": 47.6},
    ]


def losses_at(t):
    # from 07-15 end: N28/54, C25/53, S37/49 → end N30/56, C27/54, S38/50
    return {
        "north": {
            "de_pct": int(round(lerp(28, 30, t))),
            "su_pct": int(round(lerp(54, 56, t))),
            "de_text": "독 기갑·기계화 ~%d%%(스트루기 재추진)" % int(round(lerp(28, 30, t))),
            "su_text": "소련 북서전선 ~%d%%(1기계화 소진·시가)" % int(round(lerp(54, 56, t))),
        },
        "center": {
            "de_pct": int(round(lerp(25, 27, t))),
            "su_pct": int(round(lerp(53, 54, t))),
            "de_text": "독 ~%d%%(재도하·교두보 재건)" % int(round(lerp(25, 27, t))),
            "su_text": "소련 서부전선 ~%d%%(야간 공격 둔화)" % int(round(lerp(53, 54, t))),
        },
        "south": {
            "de_pct": int(round(lerp(37, 38, t))),
            "su_pct": int(round(lerp(49, 50, t))),
            "de_text": "독 1기갑집단 ~%d%%(가도·입구)" % int(round(lerp(37, 38, t))),
            "su_text": "소련 남서전선 ~%d%%(입구 교착)" % int(round(lerp(49, 50, t))),
        },
    }


def situation_at(t):
    if t < 0.35:
        n = "7.16 새벽 공병 집중·41기갑 동안 재추진 개시(유리18). 1기계화 국지반격 소진·재편. 시가 기갑 미투입."
        c = "보브루이스크 서안에서 소형 재도하 시도(기본7). 보리소프 가교 수리 착수. 육교 예비 대기. 브레스트 항전."
        s = "6군 어깨 고수 속 가도 재추진(기본6). 24기계화 입구 공격 지속. 테테레프 미달."
    elif t < 0.75:
        n = "41기갑 스트루기 접근·루가 도로 위협. 1기계화 측방 지연만. 타르투·오포치카. 시가 미완전."
        c = "보브루이스크 동안 소형 교두보 재확보. 보리소프 소폭 재건·확장 제한. 레펠 소폭. 모길료프 미도하."
        s = "가도 소폭 동진·테테레프 미달. 입구 교착 유지. 48자동차화 남어깨 소폭. NV 요새선 유지."
    else:
        n = "7.16 스트루기 접근·루가 도로 위협(유리18). 시가 미완전·기갑 미투입. 타르투·오포치카·포르호프 연결."
        c = "보브루이스크 소형 재확보·보리소프 소폭 재건(기본7). 육교 예비 대기. 모길료프 미도하. 브레스트 항전."
        s = "가도 소폭·테테레프 미달·입구 교착(기본6). 드네스트르 소폭. NV 요새선 유지."
    return {"north": n, "center": c, "south": s}


plan = {
    "schema": 1,
    "date": "1941-07-16",
    "turn": 4,
    "referee": "라이브 매시 판정 — 턴4 명령 지속, 주사위 북18/중7/남6",
    "dice": [
        {"axis": "north", "roll": 18, "band": "유리",
         "note": "1기계화 국지반격 소진 후 41기갑 재추진. 스트루기 접근·루가 도로 위협/부분차단. 시가 기갑 미투입·시가 미완전. 타르투·오포치카"},
        {"axis": "center", "roll": 7, "band": "기본",
         "note": "보브루이스크 동안 소형 재확보·야간 공격 둔화. 보리소프 가교 수리·교두보 소폭 재건. 레펠 소폭. 육교 예비 대기. 모길료프 미도하. 브레스트 항전"},
        {"axis": "south", "roll": 6, "band": "기본",
         "note": "가도 소폭 동진·테테레프 미달. 6군 어깨 고수·입구 교착 지속. 48자동차화 남어깨 소폭. 드네스트르 소폭. NV 요새선 유지"},
    ],
    "summary": {
        "north": "주사위 18(유리): 스트루기 접근·루가 도로 위협. 1기계화 소진·시가 미완전. 타르투·오포치카.",
        "center": "주사위 7(기본): 보브루이스크 소형 재확보·보리소프 소폭 재건. 육교 예비 대기. 브레스트 항전.",
        "south": "주사위 6(기본): 가도 소폭·테테레프 미달·입구 교착. 드네스트르 소폭·NV 유지.",
    },
    "keyframes": [],
}

KF_META = [
    (6, 0.25, [
        {"axis": "north", "text": "새벽, 공병을 프스코프 남동 도하점에 재집중·41기갑군단이 동안 교두보 재추진 개시(주사위 18 유리). 시가 기갑 미투입. 1기계화는 전일 반격 소진으로 재편."},
        {"axis": "center", "text": "새벽, 2기갑집단이 보브루이스크 서안에서 소형 재도하를 시도(주사위 7 기본). 소련 야간 국지공격은 서안 엄호에 둔화. 보리소프 가교 수리 착수."},
        {"axis": "south", "text": "6군 어깨 고수 속 차량화사단이 지토미르 가도 재추진(주사위 6 기본). 24기계화·NV는 입구 남북 공격 지속."},
    ], {"de-2pzg": 63, "su-1mech": 28}),
    (12, 0.50, [
        {"axis": "north", "text": "정오, 41기갑 선두가 스트루기크라스니예 접근로에 진입·루가 도로를 위협. 1기계화는 측방 지연만 가능. 시가는 아직 미완전 점령."},
        {"axis": "north", "text": "18군 타르투 압박·남서 포위 지속. 16군 오포치카-노보르제프에서 포르호프 방향으로 56기갑과 연결 시도."},
        {"axis": "center", "text": "보브루이스크 동안 소형 교두보 재확보. 보리소프도 가교 부분 복구로 교두보 소폭 재건 — 확장는 제한. 레펠 소폭 전진."},
        {"axis": "center", "text": "20군 5·7기계화 잔존은 비텝스크-오르샤 육교 예비로 대기. 모길료프 우회 도하 미실시. 브레스트 항전."},
        {"axis": "south", "text": "가도 선두 소폭 동진하나 테테레프 미달. 입구는 6군 AT·88과 24기계화 공격이 맞붙어 교착 유지."},
        {"axis": "south", "text": "48자동차화군단 남쪽 어깨 소폭. 11군·루마니아군 드네스트르를 비니차 방향으로 소폭. NV 요새벨트 유지."},
    ], {"de-3pzg": 60, "de-41pz": 53, "su-24mech": 28, "su-bobr": 46}),
    (18, 0.75, [
        {"axis": "north", "text": "해질녘, 스트루기 부근에서 루가 도로를 위협·부분 차단 시도. 완전 차단은 아직 미확인. 시가전 기갑 미투입·시가 미완전."},
        {"axis": "north", "text": "56기갑군단 동측방 엄호. 타르투·오포치카 유지. 1기계화 재편 중."},
        {"axis": "center", "text": "보리소프·보브루이스크 모두 소형~소폭 교두보로 안정화 시작. 전일 붕괴 피해 복구가 우선 — 모길료프 레이스는 보류."},
        {"axis": "center", "text": "육교 기동예비 대기 지속. 2항공함대 철도 차단 지속. 브레스트 요새 항전."},
        {"axis": "south", "text": "가도 선두는 테테레프 미달에서 정지. 입구 교착·교두보 유지. 6군 후속 호송·도로 거점."},
        {"axis": "south", "text": "11군 비니차 방향 소폭. 5군 테테레프 2차선. NV 배후 압박은 이어지나 요새벨트 유지."},
    ], None),
    (24, 1.0, [
        {"axis": "north", "text": "하루 종료: 스트루기 접근·루가 도로 위협(주사위 18 유리). 시가 미완전·기갑 미투입. 타르투·오포치카·포르호프 연결."},
        {"axis": "center", "text": "보브루이스크 소형 재확보·보리소프 소폭 재건(주사위 7 기본). 육교 예비 대기. 모길료프 미도하. 브레스트 항전."},
        {"axis": "south", "text": "가도 소폭·테테레프 미달·입구 교착(주사위 6 기본). 드네스트르 소폭. NV 요새선 유지."},
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

out = "/tmp/plan-1941-07-16.json"
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
kf6 = plan["keyframes"][0]
print("h6 N tip", kf6["fronts"]["north"][2]["pts"][0], "from F0", F0["north"][2]["pts"][0])
print("h6 C bobr", kf6["fronts"]["center"][0]["pts"][8], "from F0", F0["center"][0]["pts"][8])
for k in plan["keyframes"]:
    for e in k["events"]:
        print(f"  h{k['hour']} {e['axis']}: {len(e['text'])}c")
print("dice", [(d['axis'], d['roll'], d['band']) for d in plan['dice']])
print("summary", plan["summary"])
