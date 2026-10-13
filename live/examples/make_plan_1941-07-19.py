#!/usr/bin/env python3
"""일일 계획 — 1941-07-19 (턴4 7일차·토·주말). 주사위: 북9 기본 / 중1 불리 / 남12 기본.
전일(7.18) 종결: 동안 교두보 급축·스트루기 역전 / 보브루이스크·보리소프 유의미 / 슬루치·가도 테테레프 서접근.
7.19: 북 동안 잔존 재정비·스트루기 재접근(루가도로 미차단) / 중 동안·보리소프 재붕괴(불리1) / 남 가도 소폭·테테레프 미달."""
import copy, json, os, sys
LIVE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, LIVE)

end_path = "/tmp/end_07-18.json"
if os.path.exists(end_path):
    end = json.load(open(end_path))
    F0 = copy.deepcopy(end["fronts"])
    U0_list = end["units"]
else:
    p18 = json.load(open(os.path.join(LIVE, "plans", "1941-07-18.json")))
    kf24 = [k for k in p18["keyframes"] if k["hour"] == 24][0]
    F0 = copy.deepcopy(kf24["fronts"])
    U0_list = kf24["units"]


def lerp(a, b, t):
    return a + (b - a) * t


def lerp_pts(a, b, t):
    return [[round(lerp(p[0], q[0], t), 3), round(lerp(p[1], q[1], t), 3)] for p, q in zip(a, b)]


def segs(axis_id_style_pts):
    return [dict(id=i, style=s, pts=copy.deepcopy(pts)) for i, s, pts in axis_id_style_pts]


# --- 목표 전선 (7.19@24) ---
# 북부(기본9): 동안 잔존 교두보 소폭 재정비·동북(스트루기) 재접근, 루가도로 미완전 차단. 시가 미완전·기갑 미투입. 타르투·오포치카 소폭/유지.
N_EST_END = [
    [24.4, 58.46], [25.25, 58.39], [26.05, 58.37],
    [26.92, 58.46], [27.50, 58.44], [27.90, 58.28],
]
N_GAP_END = [
    [27.90, 58.28], [27.98, 58.28], [28.22, 58.12],
    [28.52, 58.13], [28.78, 58.14],  # 동안 잔존 재정비·스트루기 재접근(도로 미차단)
]
N_STALIN_END = [
    [28.78, 58.14],
    [28.72, 58.00],
    [28.74, 57.74],
    [28.50, 57.48],
    [28.22, 57.30],
    [28.20, 57.24],
    [28.20, 56.94],
    [28.18, 56.60],
    [28.14, 56.26],
    [28.20, 55.90],
    [28.3, 55.6],
]

# 중부(불리1): 보브루이스크 동안 재붕괴·철수, 보리소프 급축(부교 손상), 레펠-비텝스크 소강. 모길료프/드네프르 미도하. 육교 예비 대기. 브레스트 항전.
C_DVINA_END = [
    [28.3, 55.6],
    [28.48, 55.30],
    [28.62, 55.02],  # 레펠 소강
    [28.82, 54.82],
    [28.98, 54.36],  # 보리소프 급축 (from 29.35)
    [29.05, 54.08],
    [29.12, 53.72],  # 모길료프 접근 상실
    [29.18, 53.40],
    [29.05, 53.12],  # 보브루이스크 동안 소멸 (from 29.55)
    [28.98, 52.85],
]
C_PRIP_END = copy.deepcopy(F0["center"][1]["pts"])
C_PRIP_END[0] = [28.98, 52.85]
# keep south tip shared [26.75, 51.25]
C_PRIP_END[-1] = [26.75, 51.25]

# 남부(기본12): 전일 슬루치·가도 이득 유지·소폭 확장, 테테레프 강 미달. 잔존 24기계화·NV 둔화. 드네스트르·비니차 소폭. NV 벨트 유지.
S_MAIN_END = copy.deepcopy(F0["south"][0]["pts"])
S_MAIN_END[0] = [26.75, 51.25]
S_MAIN_END[2] = [27.90, 50.62]
S_MAIN_END[3] = [29.08, 50.36]  # 가도 소폭·테테레프 서접근 심화(강 미달)
S_MAIN_END[4] = [28.18, 50.30]  # 입구 교두보 소폭 유지
S_MAIN_END[5] = [27.48, 50.28]  # 남어깨 소폭
S_MAIN_END[22] = [27.88, 48.14]
S_MAIN_END[23] = [28.55, 48.12]  # 드네스트르→비니차 소폭
S_MAIN_END[24] = [27.88, 47.76]
S_MAIN_END[25] = [27.94, 47.50]


def fronts_at(t):
    # North 기본: steady modest restabilization through day
    tn = t
    # Center 불리: overnight/dawn smash — front-loaded collapse
    tc = t ** 0.7 if t > 0 else 0
    # South 기본: steady modest push, slight blunt late
    ts = t
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
    # north: 41pz 동안 잔존 재정비·스트루기 재접근(~42), 시가 기갑 미투입, 1mech 국지반격 둔화
    unit_track("de-41pz", 28.90, 58.12, 42),
    unit_track("de-56pz", 28.80, 57.98, 65),
    unit_track("de-18a", 27.28, 58.54, 77),
    unit_track("de-16a", 28.84, 56.98, 76),
    unit_track("su-8a", 26.18, 58.65, 35),
    unit_track("su-41rc", 28.88, 58.26, 24),
    unit_track("su-1mech", 28.95, 58.18, 22),  # 교두보 형성 시 국지반격 후 둔화
    unit_track("su-27a", 29.08, 56.78, 25),
    # center: 2pzg 동안 철퇴, 3pzg 보리소프 급축, 20a 육교 예비 대기
    unit_track("de-3pzg", 29.00, 54.32, 58),
    unit_track("de-2pzg", 28.95, 53.18, 60),
    unit_track("de-4a", 28.00, 53.52, 83),
    unit_track("de-9a", 25.60, 53.55, 86),
    unit_track("su-3-10a", 29.60, 52.90, 14),
    unit_track("su-20a", 29.70, 54.70, 39),  # 육교 예비 대기
    unit_track("su-borisov", 29.45, 54.28, 30),
    unit_track("su-bobr", 29.55, 53.18, 45),
    # south: 3mot 가도 소폭, 24mech 잔존 둔화, 6a 어깨, 드네스트르 소폭
    unit_track("de-3mot", 29.00, 50.36, 46),
    unit_track("de-48mot", 27.52, 50.28, 56),
    unit_track("de-6a", 28.00, 50.45, 74),
    unit_track("su-nv", 28.45, 50.55, 36),
    unit_track("su-24mech", 27.80, 50.28, 18),  # 잔존 둔화
    unit_track("su-5a", 28.40, 50.78, 31),
    unit_track("de-11a", 28.80, 48.40, 76),
    unit_track("su-12a", 27.52, 48.22, 55),
    unit_track("su-16mech", 28.35, 48.22, 51),
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
        n_goal = "동안 재정비"
        mech_goal = "국지반격"
    elif phase < 0.75:
        n_goal = "스트루기 재접근"
        mech_goal = "교두보 둔화"
    else:
        n_goal = "루가도로 미차단"
        mech_goal = "잔존 압박"

    if phase < 0.35:
        bob = "야간 급축"
        bobr = "동안 붕괴 개시"
    elif phase < 0.75:
        bob = "교두보 급축"
        bobr = "동안 철수"
    else:
        bob = "급축·고착"
        bobr = "동안 소멸"

    if phase < 0.35:
        tip_goal = "가도 소폭 동진"
        sluch = "잔존 입구 압박"
    elif phase < 0.75:
        tip_goal = "테테레프 미달"
        sluch = "잔존 둔화"
    else:
        tip_goal = "테테레프 미달"
        sluch = "잔존 둔화"

    dniester = "비니차 소폭" if phase >= 0.4 else "드네스트르 소폭"

    # north tip advances modestly NE from collapsed position
    tip_n = 28.65 + 0.25 * phase
    tip_n_lat = 58.10 + 0.04 * phase
    # center tips retreat west
    tip_c3 = 29.35 - 0.37 * phase
    tip_c2 = 29.52 - 0.57 * phase
    # south tip modest east short of Teterev
    tip_s = 28.92 + 0.16 * phase

    return [
        {"id": "a-41pz", "goal": n_goal,
         "pts": [[28.70, 58.08], [28.80, 58.10], [tip_n, tip_n_lat]],
         "label": f"4기갑집단(41군단)\n{n_goal}", "lx": 27.4, "ly": 57.85},
        {"id": "a-1mech", "goal": mech_goal,
         "pts": [[29.15, 58.28], [29.05, 58.22], [28.95 - 0.05 * phase, 58.18]],
         "label": f"1기계화군단\n({mech_goal})", "lx": 29.55, "ly": 57.95},
        {"id": "a-16a", "goal": "포르호프 연결",
         "pts": [[28.55, 56.78], [28.70, 56.88], [28.84, 56.98]]},
        {"id": "a-18a", "goal": "→ 타르투·포위",
         "pts": [[26.65, 58.30], [26.92, 58.42], [27.28, 58.54]]},
        {"id": "a-3pzg", "goal": bob,
         "pts": [[29.30, 54.38], [tip_c3 + 0.05, 54.35], [tip_c3, 54.32]],
         "label": f"3기갑집단\n({bob})", "lx": 27.8, "ly": 54.55},
        {"id": "a-2pzg", "goal": bobr,
         "pts": [[29.45, 53.14], [tip_c2 + 0.10, 53.16], [tip_c2, 53.18]],
         "label": f"2기갑집단\n({bobr})", "lx": 27.75, "ly": 53.1},
        {"id": "a-20a", "goal": "육교 예비 대기",
         "pts": [[29.55, 54.95], [29.62, 54.82], [29.70, 54.70]],
         "label": "20군 기계화\n육교 예비 대기", "lx": 29.8, "ly": 54.55},
        {"id": "a-1pzg", "goal": tip_goal,
         "pts": [[28.70, 50.40], [28.90, 50.38], [tip_s, 50.36]],
         "label": f"1기갑집단\n({tip_goal})", "lx": 26.2, "ly": 50.9},
        {"id": "a-24mech", "goal": sluch,
         "pts": [[28.10, 50.28], [27.95, 50.30], [27.80, 50.28]],
         "label": f"24기계화군단\n{sluch}", "lx": 28.45, "ly": 50.08},
        {"id": "a-5a", "goal": "테테레프 2차선",
         "pts": [[28.55, 50.95], [28.45, 50.85], [28.40, 50.78]]},
        {"id": "a-11a", "goal": dniester,
         "pts": [[27.95, 48.10], [28.30, 48.25], [28.50 + 0.20 * phase, 48.38]],
         "label": f"11군·루마니아군\n{dniester}", "lx": 26.7, "ly": 47.6},
    ]


def losses_at(t):
    # from 07-18 end: N37/58, C30/56, S39/55 → end N36/58, C34/55, S38/56
    return {
        "north": {
            "de_pct": int(round(lerp(37, 36, t))),
            "su_pct": int(round(lerp(58, 58, t))),
            "de_text": "독 기갑·기계화 ~%d%%(동안 재정비·스트루기 재접근·게임추정)" % int(round(lerp(37, 36, t))),
            "su_text": "소련 북서전선 ~%d%%(국지반격·시가 고수·게임추정)" % int(round(lerp(58, 58, t))),
        },
        "center": {
            "de_pct": int(round(lerp(30, 34, t))),
            "su_pct": int(round(lerp(56, 55, t))),
            "de_text": "독 ~%d%%(보브루이스크 재붕괴·부교 손상·게임추정)" % int(round(lerp(30, 34, t))),
            "su_text": "소련 서부전선 ~%d%%(야간 국지·교두보 압박·게임추정)" % int(round(lerp(56, 55, t))),
        },
        "south": {
            "de_pct": int(round(lerp(39, 38, t))),
            "su_pct": int(round(lerp(55, 56, t))),
            "de_text": "독 1기갑집단 ~%d%%(가도 소폭·어깨 유지·게임추정)" % int(round(lerp(39, 38, t))),
            "su_text": "소련 남서전선 ~%d%%(잔존 둔화·테테레프 2차선·게임추정)" % int(round(lerp(55, 56, t))),
        },
    }


def situation_at(t):
    if t < 0.35:
        n = "7.19 새벽 프스코프 SE 잔존 도하점·공병 재정비(기본9). 41기갑 동안 교두보 소폭 재확장 개시. 시가 기갑 미투입."
        c = "야간 소련 국지공격으로 보브루이스크 동안 급축·부교 손상(불리1). 보리소프도 압박. 육교 예비 대기. 브레스트 항전."
        s = "슬루치·가도 전일 이득 유지·소폭 동진(기본12). 잔존 24기계화·NV 둔화. 테테레프 강 미달."
    elif t < 0.75:
        n = "동안 잔존 재정비·스트루기 재접근. 1기계화 국지반격으로 루가도로 미차단. 시가 미완전. 타르투·오포치카."
        c = "보브루이스크 동안 붕괴·철수. 보리소프 급축. 레펠-비텝스크 소강. 모길료프 미도하. 육교 예비 대기."
        s = "가도 선두 테테레프 서접근 소폭·강 미달. 입구·남어깨 유지. 드네스트르 비니차 소폭. NV 벨트 유지."
    else:
        n = "7.19 동안 잔존 재정비·스트루기 재접근(기본9). 루가도로 미차단·시가 미완전. 타르투·오포치카."
        c = "보브루이스크 재붕괴·보리소프 급축(불리1). 레펠 소강·육교 예비 대기. 브레스트 항전."
        s = "슬루치·가도 소폭·테테레프 미달(기본12). 24기계화 잔존 둔화. 드네스트르 소폭·NV 유지."
    return {"north": n, "center": c, "south": s}


plan = {
    "schema": 1,
    "date": "1941-07-19",
    "turn": 4,
    "referee": "라이브 매시 판정 — 턴4 명령 지속·주말 마지막 날, 주사위 북9/중1/남12",
    "dice": [
        {"axis": "north", "roll": 9, "band": "기본",
         "note": "프스코프 SE 잔존 도하점·공병 재정비 → 동안 교두보 소폭 재확장·스트루기 재접근. 1기계화 국지반격으로 루가도로 미완전 차단. 시가 기갑 미투입·시가 미완전. 41기갑 소폭 회복(~42). 타르투·오포치카 소폭/유지"},
        {"axis": "center", "roll": 1, "band": "불리",
         "note": "야간 소련 국지공격·부교 손상 → 보브루이스크 동안 재붕괴·철수. 보리소프 급축. 레펠-비텝스크 소강. 모길료프·드네프르 미도하. 육교 예비 대기. 브레스트 항전. 중부집단군 고난의 하루"},
        {"axis": "south", "roll": 12, "band": "기본",
         "note": "슬루치·가도 전일 이득 유지·소폭 동진. 테테레프 강 미달. 잔존 24기계화·NV 둔화. 6군 어깨 유지. 드네스트르·비니차 소폭. NV 요새벨트 유지(미포기)"},
    ],
    "summary": {
        "north": "주사위 9(기본): 동안 잔존 재정비·스트루기 재접근. 루가도로 미차단·시가 미완전. 타르투·오포치카.",
        "center": "주사위 1(불리): 보브루이스크 재붕괴·보리소프 급축. 레펠 소강·육교 예비 대기. 브레스트 항전.",
        "south": "주사위 12(기본): 슬루치·가도 소폭·테테레프 미달. 24기계화 잔존 둔화. 드네스트르 소폭·NV 유지.",
    },
    "keyframes": [],
}

KF_META = [
    (6, 0.25, [
        {"axis": "north", "text": "새벽, 프스코프 SE 잔존 도하점·공병 재정비 후 41기갑이 동안 교두보를 소폭 재확장(주사위 9 기본). 시가 기갑 미투입. 1기계화 경계."},
        {"axis": "center", "text": "야간·새벽, 소련 국지공격으로 보브루이스크 동안 교두보가 급축·부교 손상(주사위 1 불리). 보리소프도 압박. 육교 예비 대기. 브레스트 항전."},
        {"axis": "south", "text": "슬루치·가도 전일 이득을 유지한 채 선두가 소폭 동진(주사위 12 기본). 잔존 24기계화·NV가 확장을 둔화. 테테레프 강 미달."},
    ], {"de-41pz": 39, "su-1mech": 23, "de-2pzg": 62, "su-bobr": 42, "su-24mech": 19}),
    (12, 0.50, [
        {"axis": "north", "text": "정오, 동안 잔존 교두보가 재정비되고 스트루기 방향으로 재접근. 1기계화 국지반격으로 루가 도로 차단은 미완. 시가 미완전."},
        {"axis": "north", "text": "18군 타르투·포위는 소폭 압박 유지. 16군 오포치카-노보르제프에서 56기갑과 연결·전진 미미."},
        {"axis": "center", "text": "보브루이스크 동안 붕괴·철수 진행. 보리소프 교두보 급축·부교 손상. 레펠-비텝스크 축 소강."},
        {"axis": "center", "text": "20군 5·7기계화 잔존은 육교 예비로 대기(미투입). 모길료프·드네프르 미도하. 브레스트 항전."},
        {"axis": "south", "text": "가도 선두가 테테레프 서접근을 소폭 심화하나 강에는 미달. 입구·남어깨는 6군·48군단이 유지."},
        {"axis": "south", "text": "24기계화 잔존·NV가 추가 확장을 둔화. 11군·루마니아군 드네스트르→비니차 소폭. NV 벨트 유지."},
    ], {"de-41pz": 41, "de-2pzg": 61, "de-3pzg": 59, "de-3mot": 45, "su-24mech": 18, "su-bobr": 44}),
    (18, 0.75, [
        {"axis": "north", "text": "해질녘, 동안 잔존 재정비·스트루기 재접근 고착. 루가도로 미차단. 시가전 기갑 미투입·시가 미완전."},
        {"axis": "north", "text": "56기갑군단 동측방 엄호. 타르투·오포치카 소폭/유지. 1기계화 잔존 압박·소진."},
        {"axis": "center", "text": "보브루이스크 동안 소멸·서안 근처 철수. 보리소프 급축 고착. 모길료프 접근 상실 — 드네프르 미도하."},
        {"axis": "center", "text": "육교 기동예비 대기 지속. 2항공함대 철도 차단 지속. 브레스트 요새 항전."},
        {"axis": "south", "text": "가도 소폭·테테레프 미달 고착. 키예프 함락 아님. 24기계화 잔존 둔화(게임 추정치)."},
        {"axis": "south", "text": "드네스트르 비니차 소폭. 5군 테테레프 2차선 지연. NV 요새벨트 유지."},
    ], None),
    (24, 1.0, [
        {"axis": "north", "text": "하루 종료: 동안 잔존 재정비·스트루기 재접근(주사위 9 기본). 루가도로 미차단·시가 미완전. 타르투·오포치카."},
        {"axis": "center", "text": "보브루이스크 재붕괴·보리소프 급축(주사위 1 불리). 레펠 소강·육교 예비 대기. 브레스트 항전."},
        {"axis": "south", "text": "슬루치·가도 소폭·테테레프 미달(주사위 12 기본). 24기계화 잔존 둔화. 드네스트르 소폭·NV 유지."},
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

out = "/tmp/plan-1941-07-19.json"
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
