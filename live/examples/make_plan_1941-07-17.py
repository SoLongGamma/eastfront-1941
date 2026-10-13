#!/usr/bin/env python3
"""일일 계획 — 1941-07-17 (턴4 5일차). 주사위: 북9 기본 / 중14 기본 / 남4 불리.
전일(7.16) 종결: 스트루기 접근·루가도로 위협 / 보브루이스크 소형·보리소프 소폭 / 가도 소폭·입구 교착.
7.17: 북 스트루기 소폭 재접근·도로 미완전차단(기본) / 중 동안·교두보 소폭 확장(기본14) / 남 입구 야간공격·교두보 급축(불리)."""
import copy, json, os, sys
LIVE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, LIVE)

end_path = "/tmp/end_07-16.json"
if os.path.exists(end_path):
    end = json.load(open(end_path))
    F0 = copy.deepcopy(end["fronts"])
    U0_list = end["units"]
else:
    p16 = json.load(open(os.path.join(LIVE, "plans", "1941-07-16.json")))
    kf24 = [k for k in p16["keyframes"] if k["hour"] == 24][0]
    F0 = copy.deepcopy(kf24["fronts"])
    U0_list = kf24["units"]


def lerp(a, b, t):
    return a + (b - a) * t


def lerp_pts(a, b, t):
    return [[round(lerp(p[0], q[0], t), 3), round(lerp(p[1], q[1], t), 3)] for p, q in zip(a, b)]


def segs(axis_id_style_pts):
    return [dict(id=i, style=s, pts=copy.deepcopy(pts)) for i, s, pts in axis_id_style_pts]


# --- 목표 전선 (7.17@24) ---
# 북부(기본9): 스트루기 소폭 재접근·루가도로 위협 지속(완전차단 아님). 시가 기갑 미투입. 동안 소폭 동북만.
N_EST_END = [
    [24.4, 58.46], [25.25, 58.39], [26.05, 58.37],
    [26.92, 58.47], [27.50, 58.45], [27.90, 58.29],
]
N_GAP_END = [
    [27.90, 58.29], [28.00, 58.31], [28.32, 58.13],
    [28.65, 58.19], [29.02, 58.22],
]
N_STALIN_END = [
    [29.02, 58.22],  # 스트루기 소폭 접근·도로 위협(미완전차단)
    [29.00, 58.10],
    [28.92, 57.80],
    [28.60, 57.52],
    [28.26, 57.32],
    [28.24, 57.26],
    [28.24, 56.96],
    [28.20, 56.62],
    [28.16, 56.28],
    [28.22, 55.92],
    [28.3, 55.6],
]

# 중부(기본14 mid-high): 보브루이스크 동안 소폭 확장, 보리소프 재건 지속, 레펠 소폭 정찰. 모길료프 미도하.
C_DVINA_END = [
    [28.3, 55.6],
    [28.52, 55.30],
    [28.70, 55.05],  # 레펠 소폭
    [28.88, 54.88],
    [29.18, 54.42],  # 보리소프 소폭 재확장
    [29.12, 54.12],
    [29.16, 53.78],
    [29.22, 53.46],
    [29.30, 53.14],  # 보브루이스크 동안 소폭
    [29.02, 52.85],
]
C_PRIP_END = copy.deepcopy(F0["center"][1]["pts"])
C_PRIP_END[0] = [29.02, 52.85]

# 남부(불리4): 24기계화·NV 야간/새벽 입구 공격 → 슬루치 교두보 급축·가도 선두 후퇴. 테테레프 미달. 드네스트르 소폭 압박. NV 유지.
S_MAIN_END = copy.deepcopy(F0["south"][0]["pts"])
S_MAIN_END[2] = [27.70, 50.64]
S_MAIN_END[3] = [28.15, 50.40]  # 가도 선두 급축(테테레프 미달·후퇴)
S_MAIN_END[4] = [27.82, 50.30]  # 입구 교두보 급축
S_MAIN_END[5] = [27.12, 50.28]  # 남어깨 수축
S_MAIN_END[22] = [27.75, 48.16]
S_MAIN_END[23] = [28.22, 48.14]  # 드네스트르 소폭 압박(독 확장 없음)
S_MAIN_END[24] = [27.78, 47.78]
S_MAIN_END[25] = [27.88, 47.52]


def fronts_at(t):
    # North modest: steady consolidation
    tn = t
    # Center mid-high basic: steady rebuild/expansion
    tc = t
    # South 불리: dawn attack hits hard early, then German blunt holds remnant — front-loaded reverse
    ts = t ** 0.7 if t > 0 else 0
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
            ("s-main", "solid", lerp_pts(F0["south"][0]["pts"], S_MAIN_END, ts)),
        ]),
    }


U0 = {x["id"]: x for x in U0_list if not x.get("remove")}


def unit_track(uid, lon, lat, strength=None):
    s = U0[uid]
    return {"id": uid, "lon0": s.get("lon", lon), "lat0": s.get("lat", lat),
            "lon1": lon, "lat1": lat, "s0": s.get("strength"), "s1": strength}


TRACKS = [
    # north: 41pz 스트루기 소폭, 1mech 소진·재편, 시가 기갑 미투입
    unit_track("de-41pz", 29.28, 58.24, 50),
    unit_track("de-56pz", 28.95, 58.05, 68),
    unit_track("de-18a", 27.28, 58.56, 78),
    unit_track("de-16a", 28.88, 57.02, 77),
    unit_track("su-8a", 26.18, 58.66, 36),
    unit_track("su-41rc", 28.98, 58.32, 23),
    unit_track("su-1mech", 29.28, 58.30, 26),  # 소진·재편·약한 지연만
    unit_track("su-27a", 29.15, 56.78, 25),
    # center: 2pzg 동안 소폭, 3pzg 교두보 재확장, 20a 육교 예비 대기
    unit_track("de-3pzg", 29.20, 54.40, 58),
    unit_track("de-2pzg", 29.22, 53.14, 61),
    unit_track("de-4a", 27.85, 53.55, 84),
    unit_track("de-9a", 25.55, 53.55, 86),
    unit_track("su-3-10a", 29.62, 52.88, 14),
    unit_track("su-20a", 29.68, 54.68, 39),  # 육교 예비 대기
    unit_track("su-borisov", 29.50, 54.32, 30),
    unit_track("su-bobr", 29.50, 53.18, 44),
    # south: 3mot 가도 후퇴, 24mech 입구 성공, 6a AT 둔화만, 드네스트르 유지
    unit_track("de-3mot", 28.18, 50.40, 38),
    unit_track("de-48mot", 27.22, 50.28, 53),
    unit_track("de-6a", 27.70, 50.48, 72),
    unit_track("su-nv", 28.20, 50.50, 40),
    unit_track("su-24mech", 27.90, 50.30, 27),
    unit_track("su-5a", 28.15, 50.72, 33),
    unit_track("de-11a", 28.55, 48.52, 74),
    unit_track("su-12a", 27.45, 48.26, 58),
    unit_track("su-16mech", 28.25, 48.28, 55),
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
        n_goal = "스트루기 소폭"
        mech_goal = "재편·약한 지연"
    elif phase < 0.75:
        n_goal = "루가도로 위협"
        mech_goal = "측방 지연"
    else:
        n_goal = "도로 미완전차단"
        mech_goal = "재편 중"

    if phase < 0.35:
        bob = "보병 인수·확장"
        bobr = "동안 소폭 확장"
    elif phase < 0.75:
        bob = "교두보 소폭"
        bobr = "동안 고수·소폭"
    else:
        bob = "재건 지속"
        bobr = "소폭 유지"

    if phase < 0.35:
        sluch = "입구 야간공격"
        tip_goal = "가도 압박 후퇴"
    elif phase < 0.75:
        sluch = "교두보 급축"
        tip_goal = "선두 후퇴"
    else:
        sluch = "입구 교착·잔존"
        tip_goal = "테테레프 미달"

    dniester = "소폭 압박 감내" if phase >= 0.4 else "드네스트르 고수"

    tip_n = 29.10 + 0.10 * phase
    tip_n_lat = 58.14 + 0.08 * phase
    tip_c3 = 29.05 + 0.15 * phase
    tip_c2 = 29.00 + 0.22 * phase
    # south tip retreats west as phase grows
    tip_s = 28.55 - 0.40 * phase

    return [
        {"id": "a-41pz", "goal": n_goal,
         "pts": [[28.95, 58.05], [29.10, 58.14], [tip_n, tip_n_lat]],
         "label": f"4기갑집단(41군단)\n{n_goal}", "lx": 27.4, "ly": 57.85},
        {"id": "a-1mech", "goal": mech_goal,
         "pts": [[29.35, 58.32], [29.30, 58.30], [29.22, 58.26]],
         "label": f"1기계화군단\n({mech_goal})", "lx": 29.55, "ly": 57.95},
        {"id": "a-16a", "goal": "포르호프 연결",
         "pts": [[28.55, 56.78], [28.70, 56.90], [28.88, 57.02]]},
        {"id": "a-18a", "goal": "→ 타르투·포위",
         "pts": [[26.60, 58.30], [26.90, 58.44], [27.28, 58.56]]},
        {"id": "a-3pzg", "goal": bob,
         "pts": [[28.95, 54.32], [29.08, 54.36], [tip_c3, 54.40]],
         "label": f"3기갑집단\n({bob})", "lx": 27.8, "ly": 54.55},
        {"id": "a-2pzg", "goal": bobr,
         "pts": [[28.85, 53.16], [29.00, 53.14], [tip_c2, 53.14]],
         "label": f"2기갑집단\n({bobr})", "lx": 27.75, "ly": 53.1},
        {"id": "a-20a", "goal": "육교 예비 대기",
         "pts": [[29.55, 54.95], [29.62, 54.80], [29.68, 54.68]],
         "label": "20군 기계화\n육교 예비 대기", "lx": 29.8, "ly": 54.55},
        {"id": "a-1pzg", "goal": tip_goal,
         "pts": [[28.50, 50.40], [28.35, 50.40], [tip_s, 50.40]],
         "label": f"1기갑집단\n({tip_goal})", "lx": 26.2, "ly": 50.9},
        {"id": "a-24mech", "goal": sluch,
         "pts": [[28.20, 50.28], [28.05, 50.30], [27.90, 50.30]],
         "label": f"24기계화군단\n{sluch}", "lx": 28.45, "ly": 50.08},
        {"id": "a-5a", "goal": "테테레프 2차선",
         "pts": [[28.40, 50.92], [28.25, 50.82], [28.15, 50.72]]},
        {"id": "a-11a", "goal": dniester,
         "pts": [[27.85, 48.10], [28.15, 48.28], [28.45 - 0.10 * phase, 48.48]],
         "label": f"11군·루마니아군\n{dniester}", "lx": 26.7, "ly": 47.6},
    ]


def losses_at(t):
    # from 07-16 end: N30/56, C27/54, S38/50 → end N32/57, C29/55, S41/52
    return {
        "north": {
            "de_pct": int(round(lerp(30, 32, t))),
            "su_pct": int(round(lerp(56, 57, t))),
            "de_text": "독 기갑·기계화 ~%d%%(스트루기 소폭·게임추정)" % int(round(lerp(30, 32, t))),
            "su_text": "소련 북서전선 ~%d%%(1기계화 재편·시가·게임추정)" % int(round(lerp(56, 57, t))),
        },
        "center": {
            "de_pct": int(round(lerp(27, 29, t))),
            "su_pct": int(round(lerp(54, 55, t))),
            "de_text": "독 ~%d%%(동안·교두보 소폭·게임추정)" % int(round(lerp(27, 29, t))),
            "su_text": "소련 서부전선 ~%d%%(야간 국지·게임추정)" % int(round(lerp(54, 55, t))),
        },
        "south": {
            "de_pct": int(round(lerp(38, 41, t))),
            "su_pct": int(round(lerp(50, 52, t))),
            "de_text": "독 1기갑집단 ~%d%%(입구 급축·연료·공병·게임추정)" % int(round(lerp(38, 41, t))),
            "su_text": "소련 남서전선 ~%d%%(입구 야간공격·게임추정)" % int(round(lerp(50, 52, t))),
        },
    }


def situation_at(t):
    if t < 0.35:
        n = "7.17 새벽 41기갑 스트루기 축 소폭 재접근(기본9). 1기계화 소진·약한 지연. 시가 기갑 미투입."
        c = "보브루이스크 동안·보리소프 보병 인수·소폭 확장(기본14). 레펠 소폭. 육교 예비 대기. 브레스트 항전."
        s = "24기계화·NV 야간/새벽 입구 남북 공격 성공(불리4). 가도 선두 압박·후퇴 개시. 테테레프 미달."
    elif t < 0.75:
        n = "스트루기 접근·루가 도로 위협 지속·완전차단 미확인. 시가 미완전. 타르투·오포치카."
        c = "보브루이스크 동안 소폭·보리소프 재건 지속. 레펠-비텝스크 소폭 정찰. 모길료프 미도하."
        s = "슬루치 교두보 급축·가도 선두 후퇴. 6군 AT·88 둔화하나 축소 막지 못함. NV 요새선 유지."
    else:
        n = "7.17 스트루기 소폭·루가도로 위협·미완전차단(기본9). 시가 미완전. 타르투·오포치카."
        c = "보브루이스크·보리소프 소폭 확장(기본14). 육교 예비 대기. 모길료프 미도하. 브레스트 항전."
        s = "슬루치 교두보 급축·가도 후퇴(불리4). 테테레프 미달. 드네스트르 소폭 압박. NV 유지."
    return {"north": n, "center": c, "south": s}


plan = {
    "schema": 1,
    "date": "1941-07-17",
    "turn": 4,
    "referee": "라이브 매시 판정 — 턴4 명령 지속, 주사위 북9/중14/남4",
    "dice": [
        {"axis": "north", "roll": 9, "band": "기본",
         "note": "41기갑 스트루기 소폭 재접근·루가 도로 위협(완전차단 아님). 1기계화 소진·약한 지연. 시가 기갑 미투입·시가 미완전. 타르투·오포치카. 동안 소폭 동북"},
        {"axis": "center", "roll": 14, "band": "기본",
         "note": "보브루이스크 동안 소폭 확장·보리소프 보병 인수·교두보 재건 지속. 레펠-비텝스크 소폭 정찰. 육교 예비 대기. 모길료프 미도하. 브레스트 항전"},
        {"axis": "south", "roll": 4, "band": "불리",
         "note": "24기계화·NV 야간/새벽 입구 공격으로 슬루치 교두보 급축·가도 선두 후퇴. 테테레프 미달. 6군 AT·88 둔화만. 드네스트르 소폭 압박. NV 요새선 유지. 연료·공병 손실"},
    ],
    "summary": {
        "north": "주사위 9(기본): 스트루기 소폭·루가도로 위협·미완전차단. 1기계화 소진·시가 미완전. 타르투·오포치카.",
        "center": "주사위 14(기본): 보브루이스크·보리소프 소폭 확장. 육교 예비 대기. 모길료프 미도하. 브레스트 항전.",
        "south": "주사위 4(불리): 슬루치 교두보 급축·가도 후퇴. 테테레프 미달. 드네스트르 소폭 압박·NV 유지.",
    },
    "keyframes": [],
}

KF_META = [
    (6, 0.25, [
        {"axis": "north", "text": "새벽, 41기갑군단이 스트루기크라스니예 축으로 소폭 재접근(주사위 9 기본). 시가 기갑 미투입. 1기계화는 소진 상태로 약한 지연만."},
        {"axis": "center", "text": "새벽, 2·3기갑집단이 보브루이스크 동안·보리소프 교두보를 보병 인수로 소폭 확장(주사위 14 기본). 육교 예비 대기. 브레스트 항전."},
        {"axis": "south", "text": "24기계화·NV 수비대가 야간·새벽 입구 남북 동시 공격에 성공(주사위 4 불리). 가도 선두 차량화사단이 압박받아 후퇴 개시."},
    ], {"de-3mot": 41, "su-24mech": 28, "su-1mech": 26}),
    (12, 0.50, [
        {"axis": "north", "text": "정오, 41기갑 선두가 스트루기 접근로를 압박·루가 도로를 위협하나 완전 차단은 미확인. 시가 미완전."},
        {"axis": "north", "text": "18군 타르투 압박·남서 포위 지속. 16군 오포치카-노보르제프에서 포르호프 방향으로 56기갑과 연결 유지."},
        {"axis": "center", "text": "보브루이스크 동안 소폭 확장 고수. 보리소프도 가교·보병으로 교두보 재건 지속. 레펠 축 소폭 정찰."},
        {"axis": "center", "text": "20군 5·7기계화 잔존은 비텝스크-오르샤 육교 예비로 대기. 모길료프 우회 도하 미실시. 브레스트 항전."},
        {"axis": "south", "text": "슬루치 교두보가 급축되고 가도 선두는 테테레프 미달에서 후퇴. 6군 AT·88이 둔화하나 축소를 막지 못함."},
        {"axis": "south", "text": "48자동차화군단 남쪽 어깨도 수축. 11군·루마니아군은 드네스트르에서 소련 소폭 압박을 감내. NV 요새벨트 유지."},
    ], {"de-3pzg": 59, "de-41pz": 51, "de-3mot": 39, "su-bobr": 45}),
    (18, 0.75, [
        {"axis": "north", "text": "해질녘, 스트루기 부근 루가 도로 위협 지속·완전 차단은 아직 아님. 시가전 기갑 미투입·시가 미완전."},
        {"axis": "north", "text": "56기갑군단 동측방 엄호. 타르투·오포치카 유지. 1기계화 재편·약한 지연."},
        {"axis": "center", "text": "보리소프·보브루이스크 모두 소폭 교두보로 안정. 스몰렌스크 레이스 결전은 아직 아님 — 모길료프 미도하."},
        {"axis": "center", "text": "육교 기동예비 대기 지속. 2항공함대 철도 차단 지속. 브레스트 요새 항전."},
        {"axis": "south", "text": "교두보 잔존만 유지·입구 교착. 가도 선두 후퇴 고착. 연료·공병 손실 보고(게임 추정치)."},
        {"axis": "south", "text": "드네스트르 독일 확장 없음·소련 소폭 압박. 5군 테테레프 2차선. NV 요새벨트 유지."},
    ], None),
    (24, 1.0, [
        {"axis": "north", "text": "하루 종료: 스트루기 소폭·루가도로 위협·미완전차단(주사위 9 기본). 시가 미완전·기갑 미투입. 타르투·오포치카."},
        {"axis": "center", "text": "보브루이스크·보리소프 소폭 확장(주사위 14 기본). 육교 예비 대기. 모길료프 미도하. 브레스트 항전."},
        {"axis": "south", "text": "슬루치 교두보 급축·가도 후퇴(주사위 4 불리). 테테레프 미달. 드네스트르 소폭 압박. NV 요새선 유지."},
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

out = "/tmp/plan-1941-07-17.json"
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
print("h6 S tip", kf6["fronts"]["south"][0]["pts"][3], "from F0", F0["south"][0]["pts"][3])
print("h24 S tip", kf["fronts"]["south"][0]["pts"][3], "entr", kf["fronts"]["south"][0]["pts"][4])
for k in plan["keyframes"]:
    for e in k["events"]:
        print(f"  h{k['hour']} {e['axis']}: {len(e['text'])}c")
print("dice", [(d['axis'], d['roll'], d['band']) for d in plan['dice']])
print("summary", plan["summary"])
