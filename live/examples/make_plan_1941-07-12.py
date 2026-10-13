#!/usr/bin/env python3
"""일일 계획 — 1941-07-12 (턴3 마지막날/토). 주사위: 북5 불리 / 중20 유리 / 남12 기본.
전일(7.11) 종결: 프스코프 ~3km 시가 미완·보리소프 소폭 재확장·슬루치 소형 교두보·드네스트르 소형 교두보."""
import copy, json, os, sys
LIVE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, LIVE)

p11 = json.load(open(os.path.join(LIVE, "plans", "1941-07-11.json")))
kf24 = [k for k in p11["keyframes"] if k["hour"] == 24][0]
F0 = copy.deepcopy(kf24["fronts"])


def lerp(a, b, t):
    return a + (b - a) * t


def lerp_pts(a, b, t):
    return [[round(lerp(p[0], q[0], t), 3), round(lerp(p[1], q[1], t), 3)] for p, q in zip(a, b)]


def segs(axis_id_style_pts):
    return [dict(id=i, style=s, pts=copy.deepcopy(pts)) for i, s, pts in axis_id_style_pts]


# --- 목표 전선 (7.12@24) ---
# 북부(불리5): 시가 돌입 실패·벨리카야 교량 폭파. 외곽 ~5km로 소폭 후퇴/교착. 에스토니아 소폭만.
N_EST_END = [
    [24.4, 58.46], [25.25, 58.39], [26.05, 58.37],
    [26.72, 58.41], [27.28, 58.39], [27.74, 58.23],
]
N_GAP_END = [
    [27.74, 58.23], [27.84, 58.26], [28.16, 58.06],
    [28.4, 58.14], [28.52, 58.15],
]
N_STALIN_END = [
    [28.52, 58.15],  # 프스코프 남쪽 ~5km (교량 폭파 후 시가 미진입)
    [28.7, 57.98],
    [28.74, 57.74],
    [28.55, 57.48],
    [28.22, 57.28],
    [28.2, 57.22],
    [28.19, 56.9],
    [28.14, 56.55],
    [28.1, 56.22],
    [28.18, 55.88],
    [28.3, 55.6],
]

# 중부(유리20): 보리소프 교두보 대확장 + 보브루이스크 동안 소형 교두보.
C_DVINA_END = [
    [28.3, 55.6],
    [28.48, 55.3],
    [28.55, 55.02],
    [28.78, 54.85],
    [28.98, 54.4],   # 보리소프 동안 대확장
    [29.12, 54.08],
    [29.2, 53.75],
    [29.3, 53.42],
    [29.38, 53.12],  # 보브루이스크 동안 교두보
    [29.08, 52.85],
]
C_PRIP_END = copy.deepcopy(F0["center"][1]["pts"])
C_PRIP_END[0] = [29.08, 52.85]

# 남부(기본12): 슬루치 교두보 소폭 확장·지토미르 가도 추진. 드네스트르 소폭. NV 본대 유지.
S_MAIN_END = copy.deepcopy(F0["south"][0]["pts"])
S_MAIN_END[2] = [27.5, 50.73]
S_MAIN_END[3] = [27.88, 50.5]
S_MAIN_END[4] = [27.65, 50.35]
S_MAIN_END[5] = [27.0, 50.28]
S_MAIN_END[22] = [27.48, 48.08]
S_MAIN_END[23] = [27.85, 48.02]
S_MAIN_END[24] = [27.68, 47.74]
S_MAIN_END[25] = [27.78, 47.48]


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
    # north: 시가 돌입 실패·교량 폭파 → 외곽 ~5km, 41pz 소모
    unit_track("de-41pz", 28.48, 58.16, 61),
    unit_track("de-56pz", 28.5, 57.76, 75),
    unit_track("de-18a", 26.82, 58.42, 83),
    unit_track("de-16a", 28.55, 56.85, 81),
    unit_track("su-8a", 26.45, 58.56, 44),
    unit_track("su-41rc", 28.88, 58.3, 33),
    unit_track("su-1mech", 29.35, 58.08, 31),
    unit_track("su-27a", 28.88, 56.55, 29),
    # center: 보리소프 대확장 + 보브루이스크 소형 교두보
    unit_track("de-3pzg", 29.2, 54.28, 68),
    unit_track("de-2pzg", 29.25, 53.18, 74),
    unit_track("de-4a", 27.4, 53.48, 87),
    unit_track("de-9a", 25.35, 53.52, 87),
    unit_track("su-3-10a", 29.35, 52.95, 18),
    unit_track("su-20a", 29.3, 55.0, 43),
    unit_track("su-borisov", 29.45, 54.28, 30),
    unit_track("su-bobr", 29.55, 53.2, 44),
    # south: 슬루치 소폭 확장, 24기계화 소모, 11군 소폭
    unit_track("de-3mot", 27.72, 50.46, 51),
    unit_track("de-48mot", 26.78, 50.32, 62),
    unit_track("de-6a", 26.95, 50.7, 80),
    unit_track("su-nv", 28.05, 50.66, 54),
    unit_track("su-24mech", 27.85, 50.4, 44),
    unit_track("su-5a", 27.7, 50.96, 41),
    unit_track("de-11a", 28.08, 48.32, 79),
    unit_track("su-12a", 27.55, 48.36, 66),
    unit_track("su-16mech", 28.55, 48.28, 61),
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
    km = max(4, round(3 + 2 * phase)) if phase < 0.5 else max(4, round(5 - 0 * phase))
    # 불리: 시가 실패 후 ~5km
    if phase < 0.35:
        n_goal = "→ 프스코프 시가"
        n_km = 3
    elif phase < 0.7:
        n_goal = "교량 폭파·교착"
        n_km = 4
    else:
        n_goal = "→ 프스코프(~5km)"
        n_km = 5
    bob = ("교두보 돌파" if phase >= 0.55 else
           ("전차 도하" if phase >= 0.25 else "가교 증설"))
    bobr = ("소형 교두보" if phase >= 0.7 else
            ("도하 강행" if phase >= 0.4 else "도하 준비"))
    sluch = ("가도 추진" if phase >= 0.55 else
             ("교두보 확장" if phase >= 0.25 else "교두보 고수"))
    dniester = "교두보 확장" if phase >= 0.5 else "소형 교두보"
    return [
        {"id": "a-41pz", "goal": n_goal,
         "pts": [[28.5, 58.08], [28.48, 58.12 + 0.02 * (1 - phase)], [28.48, 58.14 + 0.02 * (1 - phase)]],
         "label": f"4기갑집단(41군단)\n{n_goal}", "lx": 27.35, "ly": 57.92},
        {"id": "a-1mech", "goal": "재편·국지",
         "pts": [[29.35, 58.1], [29.25, 58.05], [29.12, 57.98]],
         "label": "1기계화군단\n(재편·국지)", "lx": 29.5, "ly": 57.9},
        {"id": "a-16a", "goal": "오포치카 유지",
         "pts": [[28.3, 56.6], [28.45, 56.72], [28.55, 56.85]]},
        {"id": "a-18a", "goal": "→ 타르투",
         "pts": [[26.4, 58.2], [26.6, 58.34], [26.82, 58.42]]},
        {"id": "a-3pzg", "goal": bob,
         "pts": [[28.95, 54.32], [29.08, 54.3], [29.15 + 0.08 * phase, 54.28]],
         "label": f"3기갑집단\n({bob})", "lx": 27.8, "ly": 54.55},
        {"id": "a-2pzg", "goal": bobr,
         "pts": [[28.5, 53.22], [28.9, 53.2], [29.15 + 0.15 * phase, 53.18]],
         "label": f"2기갑집단\n({bobr})", "lx": 27.75, "ly": 53.1},
        {"id": "a-20a", "goal": "레펠 소강",
         "pts": [[29.35, 55.05], [29.22, 55.0], [29.08, 54.96]],
         "label": "20군 기계화\n레펠 소강", "lx": 29.5, "ly": 54.72},
        {"id": "a-1pzg", "goal": sluch,
         "pts": [[27.2, 50.5], [27.45, 50.48], [27.65 + 0.12 * phase, 50.46]],
         "label": f"1기갑집단\n({sluch})", "lx": 26.0, "ly": 50.95},
        {"id": "a-24mech", "goal": "어깨 반격",
         "pts": [[28.1, 50.34], [27.95, 50.38], [27.78, 50.42]],
         "label": "24기계화군단\n어깨 반격", "lx": 28.25, "ly": 50.12},
        {"id": "a-5a", "goal": "야간 기습",
         "pts": [[28.15, 51.08], [27.9, 51.02], [27.65, 50.96]]},
        {"id": "a-11a", "goal": dniester,
         "pts": [[27.55, 47.98], [27.8, 48.12], [28.0 + 0.05 * phase, 48.28]],
         "label": f"11군·루마니아군\n{dniester}", "lx": 26.55, "ly": 47.55},
    ]


def losses_at(t):
    # from 07-11 end: N20/44, C16/50, S30/37 → end N22/46, C18/53, S32/39
    return {
        "north": {
            "de_pct": int(round(lerp(20, 22, t))),
            "su_pct": int(round(lerp(44, 46, t))),
            "de_text": "독 기갑·기계화 ~%d%%(프스코프 시가 실패)" % int(round(lerp(20, 22, t))),
            "su_text": "소련 북서전선 ~%d%%(교량 폭파·지연)" % int(round(lerp(44, 46, t))),
        },
        "center": {
            "de_pct": int(round(lerp(16, 18, t))),
            "su_pct": int(round(lerp(50, 53, t))),
            "de_text": "독 ~%d%%(베레지나 돌파 소모)" % int(round(lerp(16, 18, t))),
            "su_text": "소련 서부전선 ~%d%%(교두보 붕괴 압박)" % int(round(lerp(50, 53, t))),
        },
        "south": {
            "de_pct": int(round(lerp(30, 32, t))),
            "su_pct": int(round(lerp(37, 39, t))),
            "de_text": "독 1기갑집단 ~%d%%(슬루치 확장)" % int(round(lerp(30, 32, t))),
            "su_text": "소련 남서전선 기계화·제병 ~%d%%(어깨 반격)" % int(round(lerp(37, 39, t))),
        },
    }


def situation_at(t):
    if t < 0.35:
        n = "7.12 새벽 프스코프 시가 남단 돌입 시도(불리). 교량 폭파 장약 격발 조짐. 1기계화 국지."
        c = "보리소프 가교 증설·전차 주간 도하 개시(유리20). 보브루이스크 도하 준비."
        s = "슬루치 교두보 고수·확장 준비(기본). 24기계화 어깨 압박. 드네스트르 소형 유지."
    elif t < 0.7:
        n = "벨리카야 교량 폭파 — 시가 돌입 좌절. 외곽 ~4~5km 교착. 타르투 소폭·오포치카 유지."
        c = "보리소프 동안 교두보 대확장·전차 다수 도하. 2기갑 보브루이스크 도하 강행 중."
        s = "슬루치 교두보 소폭 동진·지토미르 가도 선두. NV 본대 유지. 드네스트르 소폭 확장."
    else:
        n = "7.12 프스코프 남쪽 ~5km 교착(불리·교량 폭파). 시가 미점령. 오포치카·중부 접촉·타르투 소폭."
        c = "보리소프 교두보 대확장·보브루이스크 동안 소형 교두보(유리20). 레펠 소강. 브레스트 항전."
        s = "슬루치 교두보 소폭 확장·가도 추진(기본). NV 본대 유지. 11군 드네스트르 소폭 확장."
    return {"north": n, "center": c, "south": s}


plan = {
    "schema": 1,
    "date": "1941-07-12",
    "turn": 3,
    "referee": "라이브 매시 판정 — 턴3 마지막날, 주사위 북5/중20/남12",
    "dice": [
        {"axis": "north", "roll": 5, "band": "불리",
         "note": "프스코프 시가 돌입 실패. 벨리카야 교량 폭파로 동안 진입 차단. 외곽 ~5km 교착·41군단 소모"},
        {"axis": "center", "roll": 20, "band": "유리",
         "note": "보리소프 교두보 대확장·전차 대량 도하. 2기갑 보브루이스크 동안 소형 교두보 확보. 레펠 소강·브레스트 항전"},
        {"axis": "south", "roll": 12, "band": "기본",
         "note": "슬루치 교두보 소폭 확장·지토미르 가도 추진. 24기계화 어깨 반격으로 돌파는 아님. NV 본대·드네스트르 소폭"},
    ],
    "summary": {
        "north": "주사위 5(불리): 프스코프 시가 돌입 실패·벨리카야 교량 폭파. 외곽 ~5km 교착. 타르투 소폭·오포치카·중부 접촉.",
        "center": "주사위 20(유리): 보리소프 교두보 대확장·보브루이스크 동안 소형 교두보. 레펠 소강. 브레스트 항전.",
        "south": "주사위 12(기본): 슬루치 교두보 소폭 확장·가도 추진. NV 본대 유지. 11군 드네스트르 소폭 확장.",
    },
    "keyframes": [],
}

KF_META = [
    (6, 0.15, [
        {"axis": "north", "text": "41기갑군단, 새벽 프스코프 시가 남단으로 돌입 시도(주사위 5 불리). 41소총군단·시민 노동대가 벨리카야 교량 장약을 격발 준비."},
        {"axis": "center", "text": "보리소프 공병, 가교를 이중으로 증설하고 3기갑 전차 대대 주간 도하를 개시(주사위 20 유리)."},
        {"axis": "south", "text": "3자동차화군단, 슬루치 교두보를 보병·대전차포로 고착시킨 뒤 선두 기갑이 동진 준비(주사위 12)."},
    ], {"de-41pz": 65, "su-41rc": 33}),
    (12, 0.45, [
        {"axis": "north", "text": "정오 직전, 벨리카야 주요 교량 2곳이 폭파 — 시가 남단 독일 선두가 동안으로 못 넘어감. 외곽에서 시가전·포병전."},
        {"axis": "north", "text": "18군 타르투 접근로 소폭 압박. 8군 파르누~타르투 선 고수. 1기계화는 국지 엄호만, 본대 반격은 없음."},
        {"axis": "center", "text": "보리소프 동안 교두보가 급속 확장 — 전차·기계화 중대가 동안 도로망을 밀어붙임. 수비대는 동쪽으로 밀림."},
        {"axis": "center", "text": "2기갑집단, 보브루이스크 맞은편 도하 강행 개시. 가교 1개 중대가 동안에 발판. 레펠은 소강 유지."},
        {"axis": "south", "text": "슬루치 교두보 소폭 동진. 선두 기갑이 지토미르 가도 진입로를 압박. 24기계화가 북쪽 어깨를 반격."},
        {"axis": "south", "text": "11군·루마니아군, 드네스트르 소형 교두보를 보병으로 소폭 확장. 12군 요새포 견제 지속."},
    ], {"de-41pz": 63, "de-3pzg": 69, "de-2pzg": 76, "su-borisov": 33, "su-bobr": 47, "su-24mech": 45}),
    (18, 0.75, [
        {"axis": "north", "text": "해질녘, 41군단은 프스코프 남쪽 외곽(~5km)에서 교착. 시가 점령 실패·도하 장비 야간 집결만. 기갑 소모 큼."},
        {"axis": "north", "text": "16군 오포치카 유지·중부 좌익 접촉. 1기계화 재편은 여전히 미완이나 교량 폭파로 시가 방어는 숨 쉼."},
        {"axis": "center", "text": "보리소프 교두보 대확장 상태로 야간 보급 통과. 2기갑 보브루이스크 동안 소형 교두보 확보 — 보병 후속 중."},
        {"axis": "center", "text": "레펠 소강·브레스트 요새 항전 지속. 탈출 전투단은 드네프르 방면으로 더 밀림."},
        {"axis": "south", "text": "슬루치 교두보 유지·가도 선두만 전진. 24기계화 반격이 돌파를 막으나 교두보 소멸은 못 함. NV 본대 유지."},
        {"axis": "south", "text": "11군 드네스트르 교두보 소폭 확장. 5군 야간 기습은 호송 강화로 효과 제한."},
    ], None),
    (24, 1.0, [
        {"axis": "north", "text": "하루 종료: 프스코프 남쪽 ~5km 교착(주사위 5 불리)·교량 폭파·시가 미점령. 타르투 소폭·오포치카·중부 접촉."},
        {"axis": "center", "text": "보리소프 교두보 대확장·보브루이스크 동안 소형 교두보(주사위 20 유리). 레펠 소강. 브레스트 항전."},
        {"axis": "south", "text": "슬루치 교두보 소폭 확장·가도 추진(주사위 12 기본). NV 본대 유지. 11군 드네스트르 소폭 확장."},
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

out = "/tmp/plan-1941-07-12.json"
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
