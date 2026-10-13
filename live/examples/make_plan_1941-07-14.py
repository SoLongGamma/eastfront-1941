#!/usr/bin/env python3
"""일일 계획 — 1941-07-14 (턴4 2일차, 신명령 반영 첫날). 주사위: 북13 기본 / 중16 유리 / 남11 기본.
전일(7.13) 종결: 프스코프 남동 부교·동안 소형 교두보 / 보브루이스크 붕괴·보리소프 정지 / 슬루치 대확장·테테레프 접근.
턴4 명령: 북 7.14 야간 돌격도하·스트루기크라스니예 / 중 베레지나 재확장·비텝스크·모길료프 축 / 남 입구 싸움·테테레프."""
import copy, json, os, sys
LIVE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, LIVE)

p13 = json.load(open(os.path.join(LIVE, "plans", "1941-07-13.json")))
kf24 = [k for k in p13["keyframes"] if k["hour"] == 24][0]
F0 = copy.deepcopy(kf24["fronts"])


def lerp(a, b, t):
    return a + (b - a) * t


def lerp_pts(a, b, t):
    return [[round(lerp(p[0], q[0], t), 3), round(lerp(p[1], q[1], t), 3)] for p, q in zip(a, b)]


def segs(axis_id_style_pts):
    return [dict(id=i, style=s, pts=copy.deepcopy(pts)) for i, s, pts in axis_id_style_pts]


# --- 목표 전선 (7.14@24) ---
# 북부(기본13): 주간 도하 집결·야간 돌격도하로 동안 교두보 소폭 확장. 루가 도로 미차단·시가 기갑 미투입.
# 남동 교두보 tip을 동북으로 조금 밀어 스트루기 방향 발판만.
N_EST_END = [
    [24.4, 58.46], [25.25, 58.39], [26.05, 58.37],
    [26.82, 58.44], [27.38, 58.42], [27.78, 58.25],
]
N_GAP_END = [
    [27.78, 58.25], [27.88, 58.27], [28.2, 58.08],
    [28.52, 58.12], [28.72, 58.1],
]
N_STALIN_END = [
    [28.72, 58.1],   # 남동 교두보 소폭 동북 확장 (스트루기 미달)
    [28.78, 58.02],
    [28.82, 57.74],
    [28.55, 57.48],
    [28.22, 57.28],
    [28.2, 57.22],
    [28.2, 56.92],
    [28.16, 56.58],
    [28.12, 56.24],
    [28.18, 55.88],
    [28.3, 55.6],
]

# 중부(유리16): 보리소프 재확장 + 보브루이스크 동안 재확보 + 레펠 방향 소폭 북진.
C_DVINA_END = [
    [28.3, 55.6],
    [28.52, 55.32],
    [28.62, 55.05],  # 레펠 방향 소폭
    [28.85, 54.88],
    [29.1, 54.42],   # 보리소프 동안 재확장
    [29.22, 54.1],
    [29.28, 53.75],
    [29.32, 53.42],
    [29.35, 53.14],  # 보브루이스크 동안 재확보
    [29.1, 52.85],
]
C_PRIP_END = copy.deepcopy(F0["center"][1]["pts"])
C_PRIP_END[0] = [29.1, 52.85]

# 남부(기본11): 슬루치 교두보 동진 소폭(테테레프 미도달)·입구 어깨 교착. 드네스트르 소폭.
S_MAIN_END = copy.deepcopy(F0["south"][0]["pts"])
S_MAIN_END[2] = [27.72, 50.66]
S_MAIN_END[3] = [28.28, 50.42]  # 가도 동진
S_MAIN_END[4] = [27.9, 50.3]
S_MAIN_END[5] = [27.05, 50.28]
S_MAIN_END[22] = [27.68, 48.16]
S_MAIN_END[23] = [28.15, 48.14]
S_MAIN_END[24] = [27.72, 47.76]
S_MAIN_END[25] = [27.82, 47.5]


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


U0 = {x["id"]: x for x in kf24["units"] if not x.get("remove")}


def unit_track(uid, lon, lat, strength=None):
    s = U0[uid]
    return {"id": uid, "lon0": s.get("lon", lon), "lat0": s.get("lat", lat),
            "lon1": lon, "lat1": lat, "s0": s.get("strength"), "s1": strength}


TRACKS = [
    # north: 야간 도하로 동안 교두보 소폭, 41pz 선도·56pz 엄호, 1mech 스트루기 집결
    unit_track("de-41pz", 28.95, 58.0, 57),
    unit_track("de-56pz", 28.78, 57.95, 72),
    unit_track("de-18a", 27.05, 58.5, 81),
    unit_track("de-16a", 28.68, 56.92, 80),
    unit_track("su-8a", 26.3, 58.6, 39),
    unit_track("su-41rc", 28.95, 58.28, 26),
    unit_track("su-1mech", 29.2, 58.15, 33),  # 스트루기크라스니예 집결
    unit_track("su-27a", 29.05, 56.7, 28),
    # center: 보리소프 재확장·보브루이스크 재도하·20군 육교 예비 이동
    unit_track("de-3pzg", 29.25, 54.35, 66),
    unit_track("de-2pzg", 29.3, 53.16, 70),
    unit_track("de-4a", 27.8, 53.55, 86),
    unit_track("de-9a", 25.5, 53.55, 87),
    unit_track("su-3-10a", 29.65, 52.85, 15),
    unit_track("su-20a", 29.55, 54.85, 40),  # 비텝스크-오르샤 방향으로 이동
    unit_track("su-borisov", 29.55, 54.25, 28),
    unit_track("su-bobr", 29.55, 53.18, 42),
    # south: 교두보 동진·입구 교착, 6군 어깨 접근, 24mech 입구 공격
    unit_track("de-3mot", 28.35, 50.38, 46),
    unit_track("de-48mot", 27.2, 50.35, 58),
    unit_track("de-6a", 27.45, 50.58, 77),
    unit_track("su-nv", 28.25, 50.55, 44),
    unit_track("su-24mech", 27.95, 50.32, 32),
    unit_track("su-5a", 28.1, 50.78, 36),
    unit_track("de-11a", 28.45, 48.5, 77),
    unit_track("su-12a", 27.45, 48.28, 61),
    unit_track("su-16mech", 28.35, 48.32, 58),
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
        n_goal = "도하 집결"
    elif phase < 0.75:
        n_goal = "야간 돌격도하"
    else:
        n_goal = "동안 교두보"
    bob = ("교두보 재확장" if phase >= 0.55 else
           ("전차 재도하" if phase >= 0.25 else "가교 복구"))
    bobr = ("소형 교두보" if phase >= 0.7 else
            ("재도하" if phase >= 0.4 else "도하 재집결"))
    sluch = ("테테레프 접근" if phase >= 0.7 else
             ("가도 동진" if phase >= 0.35 else "입구 고수"))
    dniester = "비니차 방향" if phase >= 0.5 else "교두보 확장"
    mech_goal = "스트루기 집결" if phase < 0.75 else "국지반격 준비"
    return [
        {"id": "a-41pz", "goal": n_goal,
         "pts": [[28.75, 57.95], [28.85, 57.98], [28.95, 58.0]],
         "label": f"4기갑집단(41군단)\n{n_goal}", "lx": 27.4, "ly": 57.85},
        {"id": "a-1mech", "goal": mech_goal,
         "pts": [[29.35, 58.2], [29.25, 58.17], [29.15, 58.12]],
         "label": f"1기계화군단\n({mech_goal})", "lx": 29.55, "ly": 57.95},
        {"id": "a-16a", "goal": "노보르제프",
         "pts": [[28.4, 56.7], [28.55, 56.82], [28.68, 56.92]]},
        {"id": "a-18a", "goal": "→ 타르투·포위",
         "pts": [[26.5, 58.25], [26.75, 58.38], [27.05, 58.5]]},
        {"id": "a-3pzg", "goal": bob,
         "pts": [[28.95, 54.3], [29.1, 54.32], [29.2 + 0.05 * phase, 54.35]],
         "label": f"3기갑집단\n({bob})", "lx": 27.8, "ly": 54.55},
        {"id": "a-2pzg", "goal": bobr,
         "pts": [[28.6, 53.2], [28.95, 53.18], [29.15 + 0.15 * phase, 53.16]],
         "label": f"2기갑집단\n({bobr})", "lx": 27.75, "ly": 53.1},
        {"id": "a-20a", "goal": "육교 예비",
         "pts": [[29.45, 55.1], [29.5, 54.95], [29.55, 54.85]],
         "label": "20군 기계화\n육교 예비", "lx": 29.7, "ly": 54.7},
        {"id": "a-1pzg", "goal": sluch,
         "pts": [[27.5, 50.45], [27.9, 50.42], [28.2 + 0.15 * phase, 50.38]],
         "label": f"1기갑집단\n({sluch})", "lx": 26.2, "ly": 50.9},
        {"id": "a-24mech", "goal": "입구 공격",
         "pts": [[28.2, 50.28], [28.05, 50.3], [27.9, 50.32]],
         "label": "24기계화군단\n입구 공격", "lx": 28.4, "ly": 50.1},
        {"id": "a-5a", "goal": "테테레프 2차선",
         "pts": [[28.4, 50.95], [28.25, 50.85], [28.1, 50.78]]},
        {"id": "a-11a", "goal": dniester,
         "pts": [[27.7, 48.05], [28.05, 48.25], [28.3 + 0.1 * phase, 48.45]],
         "label": f"11군·루마니아군\n{dniester}", "lx": 26.7, "ly": 47.6},
    ]


def losses_at(t):
    # from 07-13 end: N24/50, C21/50, S34/46 → end N26/52, C22/52, S36/48
    return {
        "north": {
            "de_pct": int(round(lerp(24, 26, t))),
            "su_pct": int(round(lerp(50, 52, t))),
            "de_text": "독 기갑·기계화 ~%d%%(야간 도하 소모)" % int(round(lerp(24, 26, t))),
            "su_text": "소련 북서전선 ~%d%%(교두보·감시초소)" % int(round(lerp(50, 52, t))),
        },
        "center": {
            "de_pct": int(round(lerp(21, 22, t))),
            "su_pct": int(round(lerp(50, 52, t))),
            "de_text": "독 ~%d%%(베레지나 재확장)" % int(round(lerp(21, 22, t))),
            "su_text": "소련 서부전선 ~%d%%(교두보 압박·후퇴)" % int(round(lerp(50, 52, t))),
        },
        "south": {
            "de_pct": int(round(lerp(34, 36, t))),
            "su_pct": int(round(lerp(46, 48, t))),
            "de_text": "독 1기갑집단 ~%d%%(가도·입구)" % int(round(lerp(34, 36, t))),
            "su_text": "소련 남서전선 ~%d%%(입구 공격 소모)" % int(round(lerp(46, 48, t))),
        },
    }


def situation_at(t):
    if t < 0.35:
        n = "7.14 새벽 프스코프 남동 도하점 집결·포병 준비(기본13). 시가 기갑 미투입. 1기계화 스트루기 집결."
        c = "보리소프 가교 복구·전차 재도하 개시(유리16). 보브루이스크 재집결. 20군 육교 예비 이동."
        s = "슬루치 교두보 입구 고수·동진 준비(기본11). 24기계화 입구 공격 개시. 6군 어깨 접근."
    elif t < 0.75:
        n = "해질녘~야간 돌격도하 개시 — 동안 발판 확대 중. 감시초소·사전 사격으로 소모. 루가 도로 미차단."
        c = "보리소프 교두보 재확장·보병 인수 개시. 2기갑 보브루이스크 재도하. 레펠 방향 소폭. 브레스트 항전."
        s = "가도 동진·테테레프 미달. 입구 어깨 교착(24기계화). 11군 비니차 방향 소폭. NV 배후 압박."
    else:
        n = "7.14 프스코프 남동 동안 교두보 소폭 확장(기본13)·야간 도하. 루가 도로·스트루기 미달. 타르투·오포치카."
        c = "보리소프 재확장·보브루이스크 동안 재확보(유리16). 레펠 소폭. 육교 예비 이동. 브레스트 항전."
        s = "슬루치 가도 동진·입구 교착(기본11). 테테레프 미도달. 드네스트르 소폭. NV 배후 유지."
    return {"north": n, "center": c, "south": s}


plan = {
    "schema": 1,
    "date": "1941-07-14",
    "turn": 4,
    "referee": "라이브 매시 판정 — 턴4 신명령 첫날, 주사위 북13/중16/남11",
    "dice": [
        {"axis": "north", "roll": 13, "band": "기본",
         "note": "주간 도하 집결 후 야간 돌격도하로 동안 교두보 소폭 확장. 사전 사격·감시초소로 소모. 루가 도로·스트루기 미달·시가 기갑 미투입"},
        {"axis": "center", "roll": 16, "band": "유리",
         "note": "보리소프 교두보 재확장·보병 인수 개시. 보브루이스크 동안 재확보. 레펠 방향 소폭. 20군 육교 예비 이동. 브레스트 항전"},
        {"axis": "south", "roll": 11, "band": "기본",
         "note": "슬루치 가도 동진하나 테테레프 미달. 24기계화 입구 공격으로 어깨 교착. 6군 선두 어깨 접근. 드네스트르 소폭"},
    ],
    "summary": {
        "north": "주사위 13(기본): 프스코프 남동 야간 도하·동안 교두보 소폭. 루가 도로·스트루기 미달. 타르투·오포치카.",
        "center": "주사위 16(유리): 보리소프 재확장·보브루이스크 동안 재확보. 레펠 소폭. 육교 예비 이동. 브레스트 항전.",
        "south": "주사위 11(기본): 슬루치 가도 동진·입구 교착. 테테레프 미달. 드네스트르 소폭. NV 배후 유지.",
    },
    "keyframes": [],
}

KF_META = [
    (6, 0.15, [
        {"axis": "north", "text": "4기갑집단 공병·교량종대, 프스코프 남동 단일 도하점에 새벽 집결(주사위 13 기본). 포병·연막 준비. 시가 기갑은 투입 안 함."},
        {"axis": "center", "text": "보리소프 공병, 손상 가교를 복구하고 3기갑 전차 재도하를 개시(주사위 16 유리). 2기갑은 보브루이스크 맞은편 재집결."},
        {"axis": "south", "text": "3자동차화군단 차량화사단, 슬루치 교두보 입구를 고수한 채 동진 준비(주사위 11). 24기계화가 남북 입구로 접근."},
    ], {"de-41pz": 58, "su-1mech": 34}),
    (12, 0.45, [
        {"axis": "north", "text": "정오, 도하 장비 전방 집결 완료. 소련 감시초소·사전 사격제원이 집적지를 포격 — 공병 손실. 18군 1개 군단이 프스코프 남·서를 포위 압박."},
        {"axis": "north", "text": "1기계화군단, 스트루기크라스니예에 집결·재편. 대반격 없이 교두보 형성 대기. 16군 노보르제프 방면 소폭 진출."},
        {"axis": "center", "text": "보리소프 동안 교두보가 전날보다 동진 — 전차·보병 통과. 4군 선두가 교두보 인수에 착수. 레펠 방향 3기갑 측면 엄호 사단 전진."},
        {"axis": "center", "text": "2기갑집단, 보브루이스크 재도하 강행. 소련 야간 국지공격 여파는 주간에 정리. 20군 5·7기계화는 비텝스크-오르샤 육교로 이동 개시."},
        {"axis": "south", "text": "슬루치 교두보 소폭 동진·지토미르 가도 추진. 24기계화·NV가 입구 남북을 동시 공격 — 어깨 확장 둔화."},
        {"axis": "south", "text": "6군 선두 보병사단이 교두보 북쪽 어깨에 접근. 11군·루마니아군 드네스트르 교두보를 비니차 방향으로 소폭 확장."},
    ], {"de-3pzg": 65, "de-2pzg": 69, "su-24mech": 34, "su-bobr": 45}),
    (18, 0.75, [
        {"axis": "north", "text": "해질녘, 연막·집중포격 아래 돌격도하 개시. 동안 발판 확대·부교 가설 중. 소련 사전 사격으로 가교 일부 손상하나 교두보는 유지."},
        {"axis": "north", "text": "41기갑군단 선두만 동안 투입, 스트루기·루가 도로는 아직 미차단. 1기계화 국지반격 준비. 타르투 압박·오포치카 유지."},
        {"axis": "center", "text": "보리소프 교두보 재확장 상태로 야간 보급. 보브루이스크 동안 소형 교두보 재확보 — 보병 후속. 브레스트 항전."},
        {"axis": "center", "text": "레펠~비텝스크 축 소폭 전진. 육교 기동예비 이동 지속. 모길료프 우회 도하는 아직 미실시."},
        {"axis": "south", "text": "가도 선두는 테테레프 접근로 직전에서 정지. 입구 어깨는 24기계화 공격과 교착 — 교두보 소멸은 없음."},
        {"axis": "south", "text": "6군 대전차포 일부가 북쪽 어깨에 도착. 11군 비니차 방향 소폭. 5군 테테레프 2차선 진지 작업."},
    ], None),
    (24, 1.0, [
        {"axis": "north", "text": "하루 종료: 프스코프 남동 동안 교두보 소폭 확장(주사위 13 기본)·야간 도하. 루가 도로·스트루기 미달. 타르투·오포치카."},
        {"axis": "center", "text": "보리소프 재확장·보브루이스크 동안 재확보(주사위 16 유리). 레펠 소폭. 육교 예비 이동. 브레스트 항전."},
        {"axis": "south", "text": "슬루치 가도 동진·입구 교착(주사위 11 기본). 테테레프 미달. 드네스트르 소폭. NV 배후 유지."},
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

out = "/tmp/plan-1941-07-14.json"
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
for k in plan["keyframes"]:
    for e in k["events"]:
        print(f"  h{k['hour']} {e['axis']}: {len(e['text'])}c")
