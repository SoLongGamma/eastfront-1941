#!/usr/bin/env python3
"""일일 계획 — 1941-07-10 (턴3 5일차). 주사위: 북12 / 중3 / 남12.
전일(7.9) 종결: 프스코프 ~15km·오포치카 일부·보리소프 교두보 안정·민스크/비아위스토크 섬멸 종료·기갑 정지 2일차·드네스트르 강변."""
import copy, json, os, sys
LIVE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, LIVE)

p09 = json.load(open(os.path.join(LIVE, "plans", "1941-07-09.json")))
kf24 = [k for k in p09["keyframes"] if k["hour"] == 24][0]
F0 = copy.deepcopy(kf24["fronts"])


def lerp(a, b, t):
    return a + (b - a) * t


def lerp_pts(a, b, t):
    return [[round(lerp(p[0], q[0], t), 3), round(lerp(p[1], q[1], t), 3)] for p, q in zip(a, b)]


def segs(axis_id_style_pts):
    return [dict(id=i, style=s, pts=copy.deepcopy(pts)) for i, s, pts in axis_id_style_pts]


# --- 목표 전선 (7.10@24) ---
# 북부: 프스코프 남쪽 접근(약 7km). n-stalin 북단을 북동으로, n-gap도 따라감. 에스토니아 소폭 북진.
N_EST_END = [
    [24.4, 58.42], [25.25, 58.35], [26.05, 58.33],
    [26.65, 58.37], [27.2, 58.35], [27.69, 58.19],
]
N_GAP_END = [
    [27.69, 58.19], [27.78, 58.24], [28.12, 58.02],
    [28.48, 58.08], [28.62, 58.1],
]
# n-stalin: 북단 프스코프 남쪽(~58.15 부근), 남으로 오포치카·중부 경계
N_STALIN_END = [
    [28.62, 58.1],
    [28.75, 57.95],
    [28.76, 57.72],
    [28.53, 57.45],
    [28.2, 57.25],
    [28.19, 57.2],
    [28.18, 56.88],
    [28.13, 56.54],
    [28.08, 56.22],
    [28.17, 55.87],
    [28.3, 55.6],
]

# 중부(불리): 보리소프 교두보 수축 — c-dvina 중간의 동안 돌출을 서쪽으로 되돌림
C_DVINA_END = [
    [28.3, 55.6],
    [28.47, 55.32],
    [28.48, 55.05],
    [28.68, 54.88],
    [28.52, 54.48],   # 교두보 수축(동진 후퇴)
    [28.78, 54.15],
    [28.92, 53.82],
    [29.08, 53.48],
    [29.1, 53.12],
    [28.92, 52.85],
]
C_PRIP_END = copy.deepcopy(F0["center"][1]["pts"])

# 남부(기본): NV 외곽 소폭 압박(정점 약간 동), 남쪽 드네스트르 접근 소폭
S_MAIN_END = copy.deepcopy(F0["south"][0]["pts"])
# index 3 near NV apex ~ (27.438, 50.54) → slightly east under infantry pressure
S_MAIN_END[3] = [27.48, 50.54]
S_MAIN_END[2] = [27.38, 50.76]
# Dniester approach (indices ~22-24)
S_MAIN_END[22] = [27.32, 47.98]
S_MAIN_END[23] = [27.55, 47.88]
S_MAIN_END[24] = [27.45, 47.65]


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


# 7.9@24 부대 위치 (plan upsert 기준)
U0 = {x["id"]: x for x in kf24["units"]}


def unit_track(uid, lon, lat, strength=None):
    s = U0[uid]
    return {"id": uid, "lon0": s.get("lon", lon), "lat0": s.get("lat", lat),
            "lon1": lon, "lat1": lat, "s0": s.get("strength"), "s1": strength}


# 종결 목표 위치·전투력
TRACKS = [
    # north: 41pz → 프스코프 남쪽 ~7km (프스코프 ~57.82/28.33 시내; 남쪽 접근 ~28.55, 58.18)
    unit_track("de-41pz", 28.55, 58.18, 69),
    unit_track("de-56pz", 28.48, 57.68, 78),
    unit_track("de-18a", 26.7, 58.35, 85),
    unit_track("de-16a", 28.55, 56.82, 83),
    unit_track("su-8a", 26.55, 58.52, 47),
    unit_track("su-41rc", 29.05, 58.22, 37),
    unit_track("su-1mech", 29.45, 58.08, 33),
    unit_track("su-27a", 28.9, 56.58, 31),
    # center: 교두보 수축 — 3pzg 약간 서퇴, 수비대 반격
    unit_track("de-3pzg", 28.95, 54.28, 71),
    unit_track("de-2pzg", 28.65, 53.22, 79),
    unit_track("de-4a", 27.3, 53.52, 89),
    unit_track("de-9a", 25.25, 53.58, 89),
    unit_track("su-13a", 27.4, 53.85, 3),  # 잔존 거의 소진
    unit_track("su-3-10a", 29.2, 53.0, 21),
    unit_track("su-20a", 29.3, 55.0, 46),
    unit_track("su-borisov", 29.2, 54.3, 40),  # 야간 타격 후 소모되나 교두보 압박 성공
    unit_track("su-bobr", 29.4, 53.25, 52),
    # south: 정지 해제 준비, 보병 압박
    unit_track("de-3mot", 27.08, 50.51, 58),
    unit_track("de-48mot", 26.62, 50.37, 66),
    unit_track("de-6a", 26.78, 50.76, 83),
    unit_track("su-nv", 27.92, 50.7, 62),
    unit_track("su-24mech", 27.92, 50.4, 53),
    unit_track("su-5a", 27.72, 51.0, 44),
    unit_track("de-11a", 27.78, 48.12, 84),
    unit_track("su-12a", 27.4, 48.42, 71),
    unit_track("su-16mech", 28.7, 48.3, 66),
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
    # distances Pskov
    km = round(15 - 8 * phase)  # 15 → ~7
    pause_label = "48h 정지 종료" if phase >= 0.75 else ("재보급·대기" if phase >= 0.4 else "정지·재보급")
    bob_goal = "교두보 수축" if phase >= 0.25 else "교두보 방어"
    return [
        {"id": "a-41pz", "goal": f"→ 프스코프(~{km}km)",
         "pts": [[28.52, 57.95], [28.54, 58.05 + 0.1 * phase], [28.52, 58.15 + 0.08 * phase]],
         "label": f"4기갑집단(41군단)\n→ 프스코프(~{km}km)", "lx": 27.45, "ly": 57.9},
        {"id": "a-1mech", "goal": "재편",
         "pts": [[29.45, 58.1], [29.3, 58.0], [29.15, 57.9]],
         "label": "1기계화군단\n(재편 중)", "lx": 29.6, "ly": 57.9},
        {"id": "a-16a", "goal": "오포치카 정리",
         "pts": [[28.25, 56.58], [28.42, 56.7], [28.55, 56.8]]},
        {"id": "a-18a", "goal": "→ 타르투",
         "pts": [[26.3, 58.15], [26.5, 58.3], [26.7, 58.4]]},
        {"id": "a-3pzg", "goal": bob_goal,
         "pts": [[28.9, 54.35], [28.95, 54.3], [29.1 - 0.15 * phase, 54.26]],
         "label": f"3기갑집단\n({bob_goal})", "lx": 27.7, "ly": 54.55},
        {"id": "a-2pzg", "goal": "→ 보브루이스크(대기)",
         "pts": [[28.25, 53.25], [28.7, 53.2], [29.25, 53.15]]},
        {"id": "a-20a", "goal": "국지 압박",
         "pts": [[29.4, 55.08], [29.2, 55.0], [29.0, 54.95]],
         "label": "20군 기계화\n국지 압박", "lx": 29.55, "ly": 54.75},
        {"id": "a-1pzg", "goal": pause_label,
         "pts": [[26.9, 50.55], [27.0, 50.52], [27.1, 50.5]],
         "label": f"1기갑집단\n({pause_label})", "lx": 25.85, "ly": 50.9},
        {"id": "a-24mech", "goal": "예비 유지",
         "pts": [[28.1, 50.35], [27.85, 50.4], [27.55, 50.48]]},
        {"id": "a-5a", "goal": "야간 기습",
         "pts": [[28.25, 51.12], [27.9, 51.06], [27.55, 50.99]]},
        {"id": "a-11a", "goal": "도하 준비",
         "pts": [[27.4, 47.9], [27.6, 48.05], [27.85, 48.25]],
         "label": "11군·루마니아군\n도하 준비", "lx": 26.55, "ly": 47.55},
    ]


def losses_at(t):
    # cumulative game estimates
    return {
        "north": {
            "de_pct": int(round(lerp(17, 19, t))),
            "su_pct": int(round(lerp(40, 42, t))),
            "de_text": "독 기갑·기계화 ~%d%%(프스코프 접근)" % int(round(lerp(17, 19, t))),
            "su_text": "소련 북서전선 ~%d%%(지연·외곽)" % int(round(lerp(40, 42, t))),
        },
        "center": {
            "de_pct": int(round(lerp(12, 15, t))),
            "su_pct": int(round(lerp(48, 49, t))),
            "de_text": "독 ~%d%%(가교 피격·교두보 수축)" % int(round(lerp(12, 15, t))),
            "su_text": "소련 서부전선 ~%d%%(섬멸 잔존·국지 반격)" % int(round(lerp(48, 49, t))),
        },
        "south": {
            "de_pct": 27,
            "su_pct": int(round(lerp(33, 34, t))),
            "de_text": "독 1기갑집단 ~27%(재보급·정지 해제)",
            "su_text": "소련 남서전선 기계화·제병 ~%d%%" % int(round(lerp(33, 34, t))),
        },
    }


def situation_at(t):
    km = round(15 - 8 * t)
    if t < 0.35:
        n = f"7.10 새벽 프스코프 ~{km}km 접근 개시. 1기계화 재편. 오포치카 정리."
        c = "보리소프 교두보 야간 피격 직후 — 가교 손상, 확장 중단."
        s = "기갑 정지 3일차 새벽. 연료 종대 도착 중. NV 외곽 보병만."
    elif t < 0.7:
        n = f"프스코프 남쪽 외곽 ~{km}km. 시가 남단 포병전. 중부 좌익 접촉 유지."
        c = "교두보 수축·보급 적체. 보브루이스크 미도하. 브레스트 항전."
        s = "재보급 진행. 6군 NV 외곽 압박. 11군 드네스트르 도하 준비. 기갑 아직 미투입."
    else:
        n = f"7.10 프스코프 ~{km}km(외곽 교전). 1기계화 재편 미완. 오포치카 정리·중부 접촉."
        c = "보리소프 교두보 축소 유지(불리). 민스크 잔존 소진. 보브루이스크·브레스트 변화 없음."
        s = "48시간 정지 해제·익일 돌파 준비. NV 교두보 전무. 11군 도하 미실시."
    return {"north": n, "center": c, "south": s}


plan = {
    "schema": 1,
    "date": "1941-07-10",
    "turn": 3,
    "referee": "라이브 매시 판정 — 턴3 5일차, 주사위 북12/중3/남12",
    "dice": [
        {"axis": "north", "roll": 12, "band": "기본",
         "note": "항공 우세 속 프스코프 남쪽 외곽까지 추진(~7km). 시가 돌입은 지연전·교량 위협으로 보류"},
        {"axis": "center", "roll": 3, "band": "불리",
         "note": "보리소프 동안 소련 포병·수비대 야간 타격으로 가교 손상, 교두보 수축·확장 중단. 보브루이스크 대기 유지"},
        {"axis": "south", "roll": 12, "band": "기본",
         "note": "연료·공병 재보급 완료에 가깝고 48시간 정지 해제. 6군 보병 NV 외곽 압박, 슬루치 도하·기갑 투입은 익일"},
    ],
    "summary": {
        "north": "주사위 12(기본): 41군단이 프스코프 남쪽 외곽(~7km)까지 접근, 시가 남단 포병전. 1기계화는 재편만. 오포치카 정리·중부 좌익 접촉 유지.",
        "center": "주사위 3(불리): 보리소프 가교 야간 피격으로 교두보 수축·보급 적체. 보브루이스크 미도하. 민스크 잔존 거의 소진, 브레스트 항전.",
        "south": "주사위 12(기본): 기갑 48시간 정지 해제·재보급. NV 슬루치 교두보 전무(보병 외곽만). 11군 드네스트르 도하 준비만.",
    },
    "keyframes": [],
}

# strength spikes for center bad luck midday
KF_META = [
    (6, 0.15, [
        {"axis": "north", "text": "41기갑군단, 새벽부터 벨리카야 동안을 따라 프스코프 남쪽 접근로 추진(주사위 12). 소련 41소총군단은 외곽 토치카로 지연전."},
        {"axis": "center", "text": "새벽 직전, 소련 보리소프 수비대·군단포가 동안 가교와 집적 탄약에 집중 사격(주사위 3) — 가교 1경간 파손, 보급 중단."},
        {"axis": "south", "text": "1기갑집단 정지 3일차. 야간 도착한 연료 종대가 로브노~NV 도로 거점으로 분산. 6군 보병은 NV 외곽 포병 준비사격."},
    ], {"de-3pzg": 72, "su-borisov": 41}),
    (12, 0.45, [
        {"axis": "north", "text": "정오, 41군단 선두가 프스코프 남쪽 약 10km 도로분기에서 소련 대전차포와 교전. 슈투카가 토치카를 제압하나 시가 진입은 보류."},
        {"axis": "north", "text": "16군, 오포치카 시가 잔적을 정리. 폴로츠크 방면 중부 좌익과 지상 연락선 유지."},
        {"axis": "center", "text": "보리소프 교두보 폭이 전날의 절반 가까이 축소. 공병이 비상 가교를 가설하나 전차 재투입은 오후까지 불가."},
        {"axis": "center", "text": "레펠 방면 20군 잔존 기계화가 국지 압박 — 늪지·탄약 부족으로 돌파는 못 하나 3기갑 측면을 묶음."},
        {"axis": "south", "text": "6군 보병사단, NV 요새 외곽 토치카 2개를 포병으로 침묵. 슬루치 도하 장비는 아직 후방 집결. 기갑 미투입."},
    ], {"de-3pzg": 71, "su-borisov": 40, "de-41pz": 70}),
    (18, 0.75, [
        {"axis": "north", "text": "해질녘, 41군단 선두 프스코프 남쪽 외곽(~7km). 벨리카야 교량 접근로에 소련 폭파 준비가 관측됨 — 시가 돌입 명령 보류."},
        {"axis": "north", "text": "18군 타르투 접근로 압박 지속, 8군은 파르누~타르투 선 고수. 1기계화는 여전히 재편·탄약 대기."},
        {"axis": "center", "text": "비상 가교로 보병·대전차포만 동안 유지. 3기갑 주력은 서안 재정비. 보브루이스크 맞은편 2기갑은 도하 대기 유지."},
        {"axis": "center", "text": "민스크 잔존 13군 전투력 거의 소진. 브레스트 요새는 포격에도 항전 계속."},
        {"axis": "south", "text": "남부집단군, 48시간 작전 정지 해제 통보 — 익일 새벽 슬루치 재도하·기갑 투입 준비. 오늘 도하는 없음."},
    ], None),
    (24, 1.0, [
        {"axis": "north", "text": "하루 종료: 프스코프 남쪽 외곽 약 7km(주사위 12 기본). 시가 미진입. 오포치카 정리·중부 좌익 접촉 유지. 1기계화 재편 미완."},
        {"axis": "center", "text": "보리소프 교두보 축소 상태로 야간 방어(주사위 3 불리). 보브루이스크 미도하. 민스크 잔존 사실상 소진, 브레스트 항전."},
        {"axis": "south", "text": "슬루치 교두보 전무·정지 해제만 완료. NV 요새 유지. 11군 드네스트르 강변 도하 준비, 미도하. 연료·공병 재보급 거의 회복."},
    ], None),
]

pockets_seq = [
    [{"id": "p-brest", "status": "항전", "label": "브레스트 요새\n항전 중"}],
    [{"id": "p-brest", "status": "항전", "label": "브레스트 요새\n항전 중"}],
    [{"id": "p-brest", "status": "항전", "label": "브레스트 요새\n항전 중"}],
    [{"id": "p-brest", "status": "항전", "label": "브레스트 요새\n항전 중"}],
]

for (hour, t, events, sov), pockets in zip(KF_META, pockets_seq):
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
    # remove nearly-dead 13a at end of day
    if hour == 24:
        kf["units"] = [u for u in kf["units"] if u["id"] != "su-13a"] + [
            {"id": "su-13a", "remove": True}
        ]
    plan["keyframes"].append(kf)

out = "/tmp/plan-1941-07-10.json"
json.dump(plan, open(out, "w"), ensure_ascii=False, indent=1)
print("wrote", out, "keyframes", len(plan["keyframes"]))
