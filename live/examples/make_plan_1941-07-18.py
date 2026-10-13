#!/usr/bin/env python3
"""일일 계획 — 1941-07-18 (턴4 6일차). 주사위: 북1 불리 / 중16 유리 / 남18 유리.
전일(7.17) 종결: 스트루기 소폭·루가도로 위협 / 보브루이스크·보리소프 소폭 / 슬루치 급축·가도 후퇴.
7.18: 북 동안 교두보 급축·스트루기 역전(불리1) / 중 동안·보리소프 유의미 확장(유리16) / 남 슬루치·가도 강반등·테테레프 서접근(유리18)."""
import copy, json, os, sys
LIVE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, LIVE)

end_path = "/tmp/end_07-17.json"
if os.path.exists(end_path):
    end = json.load(open(end_path))
    F0 = copy.deepcopy(end["fronts"])
    U0_list = end["units"]
else:
    p17 = json.load(open(os.path.join(LIVE, "plans", "1941-07-17.json")))
    kf24 = [k for k in p17["keyframes"] if k["hour"] == 24][0]
    F0 = copy.deepcopy(kf24["fronts"])
    U0_list = kf24["units"]


def lerp(a, b, t):
    return a + (b - a) * t


def lerp_pts(a, b, t):
    return [[round(lerp(p[0], q[0], t), 3), round(lerp(p[1], q[1], t), 3)] for p, q in zip(a, b)]


def segs(axis_id_style_pts):
    return [dict(id=i, style=s, pts=copy.deepcopy(pts)) for i, s, pts in axis_id_style_pts]


# --- 목표 전선 (7.18@24) ---
# 북부(불리1): 프스코프 SE 단일 도하점·스트루기 선두 급타격 → 동안 교두보 급축·루가도로 위협 역전. 시가 미완전·기갑 미투입. 타르투·오포치카 소강.
N_EST_END = [
    [24.4, 58.46], [25.25, 58.39], [26.05, 58.37],
    [26.90, 58.46], [27.48, 58.44], [27.88, 58.28],
]
N_GAP_END = [
    [27.88, 58.28], [27.95, 58.28], [28.18, 58.12],
    [28.38, 58.12], [28.55, 58.10],  # 동안 교두보 급축·스트루기 접근 상실
]
N_STALIN_END = [
    [28.55, 58.10],
    [28.62, 57.98],
    [28.70, 57.72],
    [28.48, 57.48],
    [28.22, 57.30],
    [28.20, 57.24],
    [28.20, 56.94],
    [28.18, 56.60],
    [28.14, 56.26],
    [28.20, 55.90],
    [28.3, 55.6],
]

# 중부(유리16): 보브루이스크 동안 유의미 확장·보리소프 보병 인수 고착·레펠-비텝스크 소폭. 모길료프 우회 정찰만(미도하). 브레스트 항전.
C_DVINA_END = [
    [28.3, 55.6],
    [28.58, 55.28],
    [28.88, 55.00],  # 레펠-비텝스크 소폭
    [29.02, 54.80],
    [29.35, 54.40],  # 보리소프 고착·소폭 동진
    [29.28, 54.08],
    [29.38, 53.70],  # 모길료프 우회 접근·정찰
    [29.48, 53.38],
    [29.55, 53.12],  # 보브루이스크 동안 유의미
    [29.15, 52.85],
]
C_PRIP_END = copy.deepcopy(F0["center"][1]["pts"])
C_PRIP_END[0] = [29.15, 52.85]

# 남부(유리18): 6군 AT/88 입구 고수 → 3차량화·기갑 선두 슬루치 강확장·가도 테테레프 서접근. 24기계화 입구 반격 분쇄. NV 배후 위협(벨트 미포기). 드네스트르 비니차 소폭.
S_MAIN_END = copy.deepcopy(F0["south"][0]["pts"])
S_MAIN_END[2] = [27.85, 50.62]
S_MAIN_END[3] = [28.92, 50.36]  # 가도 테테레프 서접근
S_MAIN_END[4] = [28.12, 50.30]  # 입구 교두보 재확장
S_MAIN_END[5] = [27.42, 50.28]  # 남어깨 확장·요새 배후
S_MAIN_END[22] = [27.82, 48.14]
S_MAIN_END[23] = [28.48, 48.12]  # 드네스트르→비니차 소폭
S_MAIN_END[24] = [27.85, 47.76]
S_MAIN_END[25] = [27.92, 47.50]


def fronts_at(t):
    # North 불리: dawn counter/fire hits hard early — front-loaded reverse
    tn = t ** 0.7 if t > 0 else 0
    # Center 유리: steady meaningful expansion
    tc = t
    # South 유리: rebound builds through day — slight back-load
    ts = t ** 1.15 if t > 0 else 0
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
    # north: 41pz 교두보 급축·타격, 1mech 잔존 국지반격 후 재편, 시가 기갑 미투입
    unit_track("de-41pz", 28.68, 58.08, 38),
    unit_track("de-56pz", 28.78, 57.98, 65),
    unit_track("de-18a", 27.22, 58.54, 77),
    unit_track("de-16a", 28.82, 56.98, 76),
    unit_track("su-8a", 26.20, 58.65, 36),
    unit_track("su-41rc", 28.85, 58.28, 24),
    unit_track("su-1mech", 28.72, 58.18, 24),  # 잔존 국지반격 후 소진
    unit_track("su-27a", 29.10, 56.78, 25),
    # center: 2pzg 동안 유의미, 3pzg 보리소프 고착, 20a 육교 예비 대기
    unit_track("de-3pzg", 29.38, 54.40, 61),
    unit_track("de-2pzg", 29.52, 53.12, 64),
    unit_track("de-4a", 28.05, 53.52, 84),
    unit_track("de-9a", 25.60, 53.55, 86),
    unit_track("su-3-10a", 29.75, 52.88, 13),
    unit_track("su-20a", 29.70, 54.70, 39),  # 육교 예비 대기
    unit_track("su-borisov", 29.68, 54.30, 27),
    unit_track("su-bobr", 29.78, 53.16, 40),
    # south: 3mot 가도 강반등, 24mech 입구 분쇄, 6a AT 고수, 드네스트르 소폭
    unit_track("de-3mot", 28.85, 50.36, 45),
    unit_track("de-48mot", 27.48, 50.28, 56),
    unit_track("de-6a", 27.95, 50.45, 74),
    unit_track("su-nv", 28.40, 50.55, 37),
    unit_track("su-24mech", 27.65, 50.28, 20),  # 입구 반격 분쇄·소진
    unit_track("su-5a", 28.35, 50.78, 32),
    unit_track("de-11a", 28.72, 48.42, 76),
    unit_track("su-12a", 27.55, 48.22, 56),
    unit_track("su-16mech", 28.40, 48.22, 52),
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
        n_goal = "교두보 급타"
        mech_goal = "국지반격"
    elif phase < 0.75:
        n_goal = "동안 급축"
        mech_goal = "잔존 압박"
    else:
        n_goal = "스트루기 역전"
        mech_goal = "재편·소진"

    if phase < 0.35:
        bob = "보병 인수·고착"
        bobr = "동안 확장 개시"
    elif phase < 0.75:
        bob = "교두보 고착"
        bobr = "동안 유의미"
    else:
        bob = "고착·소폭 동진"
        bobr = "유의미 확장"

    if phase < 0.35:
        sluch = "입구 AT 고수"
        tip_goal = "가도 재추진"
    elif phase < 0.75:
        sluch = "입구 반격 분쇄"
        tip_goal = "테테레프 서접근"
    else:
        sluch = "교두보 강확장"
        tip_goal = "테테레프 서접근"

    dniester = "비니차 소폭" if phase >= 0.4 else "드네스트르 확장"

    # north tip retreats west as phase grows
    tip_n = 29.10 - 0.45 * phase
    tip_n_lat = 58.14 - 0.06 * phase
    tip_c3 = 29.05 + 0.33 * phase
    tip_c2 = 29.00 + 0.55 * phase
    # south tip advances east toward Teterev
    tip_s = 28.20 + 0.72 * phase

    return [
        {"id": "a-41pz", "goal": n_goal,
         "pts": [[28.95, 58.05], [28.85, 58.08], [tip_n, tip_n_lat]],
         "label": f"4기갑집단(41군단)\n{n_goal}", "lx": 27.4, "ly": 57.85},
        {"id": "a-1mech", "goal": mech_goal,
         "pts": [[29.20, 58.28], [28.95, 58.22], [28.72 + 0.10 * (1 - phase), 58.16]],
         "label": f"1기계화군단\n({mech_goal})", "lx": 29.55, "ly": 57.95},
        {"id": "a-16a", "goal": "포르호프 연결",
         "pts": [[28.55, 56.78], [28.68, 56.88], [28.82, 56.98]]},
        {"id": "a-18a", "goal": "→ 타르투·포위",
         "pts": [[26.60, 58.30], [26.88, 58.42], [27.22, 58.54]]},
        {"id": "a-3pzg", "goal": bob,
         "pts": [[28.95, 54.32], [29.15, 54.36], [tip_c3, 54.40]],
         "label": f"3기갑집단\n({bob})", "lx": 27.8, "ly": 54.55},
        {"id": "a-2pzg", "goal": bobr,
         "pts": [[28.85, 53.16], [29.15, 53.14], [tip_c2, 53.12]],
         "label": f"2기갑집단\n({bobr})", "lx": 27.75, "ly": 53.1},
        {"id": "a-20a", "goal": "육교 예비 대기",
         "pts": [[29.55, 54.95], [29.62, 54.82], [29.70, 54.70]],
         "label": "20군 기계화\n육교 예비 대기", "lx": 29.8, "ly": 54.55},
        {"id": "a-1pzg", "goal": tip_goal,
         "pts": [[28.20, 50.40], [28.50, 50.38], [tip_s, 50.36]],
         "label": f"1기갑집단\n({tip_goal})", "lx": 26.2, "ly": 50.9},
        {"id": "a-24mech", "goal": sluch,
         "pts": [[28.05, 50.28], [27.90, 50.30], [27.70, 50.28]],
         "label": f"24기계화군단\n{sluch}", "lx": 28.45, "ly": 50.08},
        {"id": "a-5a", "goal": "테테레프 2차선",
         "pts": [[28.50, 50.95], [28.40, 50.85], [28.35, 50.78]]},
        {"id": "a-11a", "goal": dniester,
         "pts": [[27.90, 48.10], [28.25, 48.25], [28.45 + 0.25 * phase, 48.40]],
         "label": f"11군·루마니아군\n{dniester}", "lx": 26.7, "ly": 47.6},
    ]


def losses_at(t):
    # from 07-17 end: N32/57, C29/55, S41/52 → end N37/58, C30/56, S39/55
    return {
        "north": {
            "de_pct": int(round(lerp(32, 37, t))),
            "su_pct": int(round(lerp(57, 58, t))),
            "de_text": "독 기갑·기계화 ~%d%%(교두보 급축·41기갑 타격·게임추정)" % int(round(lerp(32, 37, t))),
            "su_text": "소련 북서전선 ~%d%%(국지반격·사전사격·게임추정)" % int(round(lerp(57, 58, t))),
        },
        "center": {
            "de_pct": int(round(lerp(29, 30, t))),
            "su_pct": int(round(lerp(55, 56, t))),
            "de_text": "독 ~%d%%(동안·보리소프 확장·게임추정)" % int(round(lerp(29, 30, t))),
            "su_text": "소련 서부전선 ~%d%%(야간 국지·교두보 압박·게임추정)" % int(round(lerp(55, 56, t))),
        },
        "south": {
            "de_pct": int(round(lerp(41, 39, t))),
            "su_pct": int(round(lerp(52, 55, t))),
            "de_text": "독 1기갑집단 ~%d%%(가도 반등·입구 고수·게임추정)" % int(round(lerp(41, 39, t))),
            "su_text": "소련 남서전선 ~%d%%(입구 반격 소진·게임추정)" % int(round(lerp(52, 55, t))),
        },
    }


def situation_at(t):
    if t < 0.35:
        n = "7.18 새벽 프스코프 SE 도하점·스트루기 선두에 소련 사전사격·국지반격(불리1). 41기갑 타격·교두보 급축 개시. 시가 기갑 미투입."
        c = "보브루이스크 동안·보리소프 보병 인수 확장 개시(유리16). 레펠 소폭. 육교 예비 대기. 브레스트 항전."
        s = "6군 AT·88 입구 고수 후 3차량화·기갑 선두 가도 재추진(유리18). 24기계화 입구 반격 분쇄 개시."
    elif t < 0.75:
        n = "동안 교두보 급축·스트루기 접근·루가도로 위협 역전. 시가 미완전. 타르투·오포치카 소강."
        c = "보브루이스크 동안 유의미 확장·보리소프 고착. 레펠-비텝스크 소폭. 모길료프 우회 정찰만·미도하."
        s = "슬루치 교두보 강확장·가도 테테레프 서접근. 24기계화 소진. NV 배후 위협·벨트 미포기."
    else:
        n = "7.18 동안 교두보 급축·스트루기 역전(불리1). 41기갑 타격. 시가 미완전. 타르투·오포치카."
        c = "보브루이스크·보리소프 유의미 확장(유리16). 육교 예비 대기. 모길료프 미도하. 브레스트 항전."
        s = "슬루치·가도 강반등·테테레프 서접근(유리18). 24기계화 분쇄. 드네스트르 비니차 소폭. NV 유지."
    return {"north": n, "center": c, "south": s}


plan = {
    "schema": 1,
    "date": "1941-07-18",
    "turn": 4,
    "referee": "라이브 매시 판정 — 턴4 명령 지속, 주사위 북1/중16/남18",
    "dice": [
        {"axis": "north", "roll": 1, "band": "불리",
         "note": "프스코프 SE 단일 도하점·스트루기 선두에 사전사격·국지반격·부교 피해 → 동안 교두보 급축·루가도로 위협 역전. 41기갑 타격. 시가 기갑 미투입·시가 미완전. 타르투·오포치카 소강. 전군 붕괴 아님"},
        {"axis": "center", "roll": 16, "band": "유리",
         "note": "보브루이스크 동안 유의미 확장·보리소프 보병 인수 고착·소폭 동진. 레펠-비텝스크 소폭. 모길료프 우회 정찰만·드네프르 미도하. 육교 예비 대기. 브레스트 항전"},
        {"axis": "south", "roll": 18, "band": "유리",
         "note": "6군 AT·88 입구 고수 후 3차량화·기갑 선두 슬루치 강확장·가도 테테레프 서접근. 24기계화 입구 반격 분쇄·소진. NV 배후 위협·벨트 미포기. 드네스트르 비니차 소폭. 12군·16기계화 둔화"},
    ],
    "summary": {
        "north": "주사위 1(불리): 동안 교두보 급축·스트루기 역전. 41기갑 타격. 시가 미완전. 타르투·오포치카.",
        "center": "주사위 16(유리): 보브루이스크·보리소프 유의미 확장. 육교 예비 대기. 모길료프 미도하. 브레스트 항전.",
        "south": "주사위 18(유리): 슬루치·가도 강반등·테테레프 서접근. 24기계화 분쇄. 드네스트르 소폭·NV 유지.",
    },
    "keyframes": [],
}

KF_META = [
    (6, 0.25, [
        {"axis": "north", "text": "새벽, 프스코프 SE 도하점·스트루기 선두에 소련 사전사격·잔존 국지반격이 집중(주사위 1 불리). 부교·집결지가 타격받고 41기갑 교두보가 급축 개시. 시가 기갑 미투입."},
        {"axis": "center", "text": "새벽, 2·3기갑집단이 보브루이스크 동안·보리소프 교두보를 보병 인수로 확장(주사위 16 유리). 육교 예비 대기. 브레스트 항전."},
        {"axis": "south", "text": "6군 AT·88이 입구를 고수한 뒤 3차량화·기갑 선두가 가도로 재추진(주사위 18 유리). 24기계화 입구 반격은 분쇄되기 시작."},
    ], {"de-41pz": 44, "su-1mech": 25, "su-24mech": 24, "de-3mot": 40}),
    (12, 0.50, [
        {"axis": "north", "text": "정오, 동안 교두보가 급축되고 스트루기 접근·루가 도로 위협이 역전. 41기갑 선두 타격·재편. 시가 미완전."},
        {"axis": "north", "text": "18군 타르투·포위는 소강. 16군 오포치카-노보르제프에서 56기갑과 연결 유지하나 전진 미미."},
        {"axis": "center", "text": "보브루이스크 동안 유의미 확장 고수. 보리소프도 보병 인수로 교두보 고착·소폭 동진. 레펠 축 소폭."},
        {"axis": "center", "text": "20군 5·7기계화 잔존은 비텝스크-오르샤 육교 예비로 대기. 모길료프 우회는 정찰만·미도하. 브레스트 항전."},
        {"axis": "south", "text": "슬루치 교두보가 강확장되고 가도 선두는 테테레프 서접근까지 도달. 24기계화 입구 반격은 분쇄·소진."},
        {"axis": "south", "text": "48자동차화군단 남쪽 어깨 확장·NV 배후 위협. 11군·루마니아군은 드네스트르에서 비니차 방향 소폭 확장. NV 벨트 미포기."},
    ], {"de-41pz": 40, "de-2pzg": 63, "de-3mot": 43, "su-24mech": 22, "su-bobr": 42}),
    (18, 0.75, [
        {"axis": "north", "text": "해질녘, 동안 교두보 잔존만·스트루기·루가도로 위협 역전 고착. 시가전 기갑 미투입·시가 미완전."},
        {"axis": "north", "text": "56기갑군단 동측방 엄호로 붕괴 방지. 타르투·오포치카 소강. 1기계화 잔존 재편·소진."},
        {"axis": "center", "text": "보리소프·보브루이스크 모두 유의미 교두보로 안정. 모길료프 우회 접근·정찰만 — 드네프르 미도하."},
        {"axis": "center", "text": "육교 기동예비 대기 지속. 2항공함대 철도 차단 지속. 브레스트 요새 항전."},
        {"axis": "south", "text": "교두보 강확장·가도 테테레프 서접근 고착. 키예프 함락 아님. 24기계화 소진 보고(게임 추정치)."},
        {"axis": "south", "text": "드네스트르 비니차 소폭. 5군 테테레프 2차선 지연. NV 요새벨트 유지·배후 위협."},
    ], None),
    (24, 1.0, [
        {"axis": "north", "text": "하루 종료: 동안 교두보 급축·스트루기 역전(주사위 1 불리). 41기갑 타격. 시가 미완전·기갑 미투입. 타르투·오포치카."},
        {"axis": "center", "text": "보브루이스크·보리소프 유의미 확장(주사위 16 유리). 육교 예비 대기. 모길료프 미도하. 브레스트 항전."},
        {"axis": "south", "text": "슬루치·가도 강반등·테테레프 서접근(주사위 18 유리). 24기계화 분쇄. 드네스트르 비니차 소폭. NV 유지."},
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

out = "/tmp/plan-1941-07-18.json"
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
print("h6 N tip", kf6["fronts"]["north"][1]["pts"][-1], "from F0", F0["north"][1]["pts"][-1])
print("h6 C bobr", kf6["fronts"]["center"][0]["pts"][8], "from F0", F0["center"][0]["pts"][8])
print("h6 S tip", kf6["fronts"]["south"][0]["pts"][3], "from F0", F0["south"][0]["pts"][3])
print("h24 N tip", kf["fronts"]["north"][1]["pts"][-1], "41pz", [u for u in kf["units"] if u["id"]=="de-41pz"][0])
print("h24 C bobr", kf["fronts"]["center"][0]["pts"][8], "borisov", kf["fronts"]["center"][0]["pts"][4])
print("h24 S tip", kf["fronts"]["south"][0]["pts"][3], "entr", kf["fronts"]["south"][0]["pts"][4])
for k in plan["keyframes"]:
    for e in k["events"]:
        print(f"  h{k['hour']} {e['axis']}: {len(e['text'])}c")
print("dice", [(d['axis'], d['roll'], d['band']) for d in plan['dice']])
print("summary", plan["summary"])
print("losses@24", kf["losses"])
