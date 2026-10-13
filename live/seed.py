#!/usr/bin/env python3
"""state.json 초기 생성: state.md 7.5 상황 + draw_map.py DATA BLOCK에서 시드.
사용: .venv/bin/python live/seed.py [--force]   (기존 state.json 있으면 --force 필요)
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *  # noqa

# ---- 전선: draw_map.py FRONT를 축별로 분할 (북→남 연속, 경계점 공유) ----
FRONTS = {
    "north": [
        dict(id="n-estonia", style="solid", pts=[[24.15, 58.10], [25.0, 58.02], [25.8, 58.00], [26.4, 58.08], [26.95, 58.10], [27.50, 57.98]]),
        dict(id="n-gap", style="loose", pts=[[27.50, 57.98], [27.62, 57.70], [27.85, 57.45], [28.02, 57.28]]),
        dict(id="n-stalin", style="solid", pts=[[28.02, 57.28], [28.08, 57.05], [28.15, 56.75], [28.10, 56.45], [28.05, 56.15], [28.15, 55.85], [28.30, 55.60]]),
    ],
    "center": [
        dict(id="c-dvina", style="solid", pts=[[28.30, 55.60], [28.35, 55.35], [28.30, 55.10], [28.25, 54.85], [28.15, 54.55], [28.32, 54.25], [28.55, 53.90], [28.80, 53.55], [28.95, 53.20], [28.85, 52.85]]),
        dict(id="c-pripyat", style="loose", pts=[[28.85, 52.85], [28.30, 52.45], [27.60, 52.00], [27.00, 51.60], [26.75, 51.25]]),
    ],
    "south": [
        dict(id="s-main", style="solid", pts=[[26.75, 51.25], [27.00, 50.95], [27.35, 50.75], [27.45, 50.55], [27.35, 50.40], [26.90, 50.32], [26.40, 50.28], [25.80, 50.18], [25.15, 50.12], [24.50, 50.18], [23.90, 50.12], [23.45, 49.92], [23.15, 49.65], [22.85, 49.30], [22.70, 49.05], [23.30, 48.75], [24.00, 48.35], [24.70, 47.95], [25.40, 47.90], [26.00, 47.98], [26.60, 48.15], [26.95, 48.20], [27.25, 47.95], [27.48, 47.85], [27.38, 47.62], [27.62, 47.42], [27.88, 47.30], [27.86, 47.08], [28.05, 46.85], [28.20, 46.50], [28.15, 46.00], [28.20, 45.50]]),
    ],
}
GERMAN_CLOSURE = [[18.0, 45.5], [18.0, 57.78], [21.5, 57.78], [22.3, 57.82], [23.5, 57.86]]

POCKETS = [
    dict(id="p-brest", axis="center", name="브레스트 요새", lon=23.68, lat=52.09, rx=0.17, ry=0.10, label="브레스트 요새\n항전 중", lx=23.05, ly=51.88, status="항전"),
    dict(id="p-bialystok", axis="center", name="비아위스토크 내부 포위망", lon=24.15, lat=53.20, rx=0.55, ry=0.27, label="비아위스토크 내부 포위망\n(축소 중)", lx=24.15, ly=52.62, status="축소"),
    dict(id="p-minsk", axis="center", name="민스크 포위망", lon=26.95, lat=53.75, rx=0.75, ry=0.33, label="민스크 포위망\n(13군 등 · 누수 큼)", lx=25.75, ly=54.22, status="누수"),
]

ARROWS = [
    dict(id="a-41pz", unit="de-41pz", goal='→ 프스코프', axis="north", side="de", pts=[[27.55, 56.95], [28.22, 57.28], [28.30, 57.72]], label="4기갑집단(41군단)\n→ 프스코프", lx=26.45, ly=57.02, ha="center"),
    dict(id="a-18a-w", unit="de-18a", goal=None, axis="north", side="de", pts=[[24.95, 57.62], [24.62, 58.25]], label=None),
    dict(id="a-18a", unit="de-18a", goal='→ 에스토니아 남부', axis="north", side="de", pts=[[25.85, 57.62], [26.45, 58.25]], label="18군 → 에스토니아 남부", lx=25.35, ly=57.5, ha="center"),
    dict(id="a-16a", unit="de-16a", goal='→ 오포치카', axis="north", side="de", pts=[[27.30, 56.25], [27.85, 56.52], [28.45, 56.62]], label="16군 → 오포치카", lx=27.05, ly=56.12, ha="center"),
    dict(id="a-1mech", unit="su-1mech", goal='대기 반격', axis="north", side="su", pts=[[28.85, 57.62], [28.45, 57.50], [28.10, 57.36]], label="1기계화군단\n(대기 반격)", lx=29.0, ly=57.66, ha="left"),
    dict(id="a-27a", unit="su-27a", goal='측방 타격', axis="north", side="su", pts=[[29.25, 56.98], [28.70, 56.92], [28.15, 56.92]], label="27군·21기계화", lx=29.0, ly=56.82, ha="left"),
    dict(id="a-3pzg", unit="de-3pzg", goal=None, axis="center", side="de", pts=[[27.25, 54.47], [28.22, 54.28]], label="3기갑집단\n(보리소프 맞은편 집결)", lx=27.35, ly=54.7, ha="center"),
    dict(id="a-2pzg", unit="de-2pzg", goal=None, axis="center", side="de", pts=[[27.95, 53.36], [28.85, 53.20]], label="2기갑집단\n(보브루이스크 맞은편)", lx=27.85, ly=53.2, ha="right"),
    dict(id="a-20a", unit="su-20a", goal="→ 레펠 반격", goal_off=[-4, 12], axis="center", side="su", pts=[[30.05, 55.08], [29.45, 54.98], [28.85, 54.90]], label="20군 5·7기계화\n→ 레펠 반격", lx=30.15, ly=54.7, ha="left"),
    dict(id="a-esc", unit="su-3-10a", goal='탈출로(중장비 유기)', axis="center", side="esc", pts=[[25.95, 53.35], [26.40, 52.85], [27.60, 52.60], [28.75, 52.72]], label="3·10군 탈출로\n(중장비 유기)", lx=26.85, ly=52.4, ha="center"),
    dict(id="a-1pzg", unit="de-3mot", goal="→ 지토미르", goal_off=[0, 13], axis="south", side="de", pts=[[26.45, 50.68], [27.20, 50.58], [27.75, 50.48], [28.50, 50.28]], label="1기갑집단\n→ 지토미르", lx=25.75, ly=50.95, ha="center"),
    dict(id="a-11a", unit="de-11a", goal='→ 드네스트르 도하', axis="south", side="de", pts=[[27.15, 47.70], [27.55, 48.02], [27.72, 48.36]], label="11군·루마니아군\n→ 모길료프-포돌스키", lx=26.4, ly=47.45, ha="center"),
    dict(id="a-24mech", unit="su-24mech", goal=None, axis="south", side="su", pts=[[28.45, 49.98], [28.0, 50.08], [27.60, 50.30]], label="24기계화", lx=28.5, ly=49.86, ha="left"),
    dict(id="a-5a", unit="su-5a", goal='야간 기습', axis="south", side="su", pts=[[28.45, 51.25], [27.85, 51.16], [27.32, 51.0]], label="5군 삼림 기습", lx=28.5, ly=51.30, ha="left"),
    dict(id="a-16mech", unit="su-16mech", goal='반격 예비', axis="south", side="su", pts=[[28.75, 48.15], [28.15, 48.05], [27.62, 47.95]], label="16기계화(예비)", lx=28.8, ly=48.0, ha="left"),
]

FORTS = [
    dict(id="f-pskov", axis="north", name="오스트로프·프스코프 요새지대", pts=[[28.22, 57.95], [28.27, 57.60], [28.40, 57.25], [28.45, 57.05]]),
    dict(id="f-sebezh", axis="north", name="오포치카·세베시 요새지대", pts=[[28.52, 56.85], [28.45, 56.50], [28.40, 56.15]]),
    dict(id="f-polotsk", axis="center", name="폴로츠크 요새지대", pts=[[28.55, 55.75], [28.62, 55.45], [28.75, 55.25]]),
    dict(id="f-nv", axis="south", name="노보그라드-볼린스키 요새지대", pts=[[27.72, 51.00], [27.66, 50.75], [27.70, 50.40], [27.82, 50.15]]),
    dict(id="f-mp", axis="south", name="모길료프-포돌스키 요새지대", pts=[[27.40, 48.62], [27.80, 48.40], [28.25, 48.27]]),
]

# 부대 마커. kind: armor/mech/inf/hq/garrison. echelon: group(집단군·전선)/army/corps
# dx,dy: 라벨 오프셋(pt). strength: 전투력 % (게임 추정)
def U(id, name, side, axis, lon, lat, strength, kind, echelon, dx=0, dy=-14, note=""):
    return dict(id=id, name=name, side=side, axis=axis, lon=lon, lat=lat, strength=strength,
                kind=kind, echelon=echelon, dx=dx, dy=dy, note=note)

UNITS = [
    # 북부
    U("de-hgn", "북부집단군", "de", "north", 24.6, 55.85, None, "hq", "group"),
    U("de-41pz", "41기갑군단", "de", "north", 27.70, 57.02, 84, "armor", "corps", -6, 12),
    U("de-56pz", "56기갑군단", "de", "north", 27.42, 56.62, 86, "armor", "corps", 0, -14),
    U("de-18a", "18군", "de", "north", 25.55, 57.78, 90, "inf", "army", 0, -14),
    U("de-16a", "16군", "de", "north", 27.15, 56.30, 89, "inf", "army", -4, -14),
    U("su-nwf", "북서전선", "su", "north", 31.3, 58.45, None, "hq", "group"),
    U("su-8a", "8군", "su", "north", 25.90, 58.32, 55, "inf", "army", 0, 13),
    U("su-41rc", "41소총군단·11군 잔존", "su", "north", 28.62, 57.42, 58, "inf", "corps", 8, 0),
    U("su-1mech", "1기계화군단", "su", "north", 29.05, 57.88, 62, "mech", "corps", 8, 0),
    U("su-27a", "27군·21기계화 잔존", "su", "north", 29.15, 56.45, 40, "inf", "army", 8, 0),
    # 중부
    U("de-hgc", "중부집단군", "de", "center", 24.8, 52.0, None, "hq", "group"),
    U("de-3pzg", "3기갑집단", "de", "center", 27.55, 54.55, 82, "armor", "army", 0, 13),
    U("de-2pzg", "2기갑집단", "de", "center", 27.75, 53.40, 85, "armor", "army", 0, 13),
    U("de-4a", "4군", "de", "center", 25.95, 53.10, 93, "inf", "army", 0, -14),
    U("de-9a", "9군", "de", "center", 24.85, 53.75, 92, "inf", "army", 0, 13),
    U("su-wf", "서부전선", "su", "center", 31.6, 53.35, None, "hq", "group"),
    U("su-13a", "13군 잔존(민스크)", "su", "center", 27.05, 53.68, 30, "inf", "army", 0, -14),
    U("su-3-10a", "3·10군 탈출 전투단", "su", "center", 28.10, 52.62, 28, "inf", "army", 0, -14),
    U("su-20a", "20군 5·7기계화", "su", "center", 30.45, 54.98, 80, "mech", "army", 0, -14),
    U("su-borisov", "보리소프 전차학교·예비", "su", "center", 29.05, 54.42, 60, "garrison", "corps", 8, 0),
    U("su-bobr", "보브루이스크 교두 방어대", "su", "center", 29.40, 53.25, 55, "garrison", "corps", 8, 0),
    # 남부
    U("de-hgs", "남부집단군", "de", "south", 24.5, 51.25, None, "hq", "group"),
    U("de-3mot", "3자동차화군단", "de", "south", 27.18, 50.68, 80, "armor", "corps", -4, 13),
    U("de-48mot", "48자동차화군단", "de", "south", 26.80, 50.45, 74, "armor", "corps", -10, -13),
    U("de-6a", "6군", "de", "south", 26.20, 50.85, 88, "inf", "army", 0, 13),
    U("de-17a", "17군", "de", "south", 23.55, 50.05, 90, "inf", "army", -4, -14),
    U("de-11a", "11군·루마니아 3·4군", "de", "south", 26.95, 47.62, 91, "inf", "army", -6, -14),
    U("su-swf", "남서전선", "su", "south", 30.9, 49.35, None, "hq", "group"),
    U("su-nv", "NV 요새 수비대·보병군단", "su", "south", 27.95, 50.72, 74, "garrison", "corps", 8, 0),
    U("su-24mech", "24기계화군단", "su", "south", 28.35, 50.05, 70, "mech", "corps", 8, -4),
    U("su-5a", "5군·기계화 잔존", "su", "south", 28.25, 51.20, 52, "inf", "army", 8, 4),
    U("su-6-26a", "6·26군(리보프 돌출부)", "su", "south", 24.60, 49.60, 72, "inf", "army", 0, -14),
    U("su-12a", "12군", "su", "south", 27.05, 48.55, 75, "inf", "army", 0, 13),
    U("su-16mech", "16기계화군단(예비)", "su", "south", 28.70, 48.30, 70, "mech", "corps", 8, 0),
]

ORDERS = {
    "north": {
        "de": ["41기갑군단: 오스트로프 토치카 지대 좁은 정면 돌파(돌격공병·포병·슈투카) → 벨리카야 따라 북진, 7.10 전후 프스코프",
               "56기갑군단: 돌파구 추종·동북 측면 엄호, 두 군단 간격 하루 행군 이내",
               "18군 에스토니아 남부 추격(파르누·타르투), 16군 오포치카 진출·폴로츠크 방면 중부 좌익 접촉",
               "요청(정식): 7.6~7.8 8항공군단 일부 1항공함대 임시 배속"],
        "su": ["41소총군단+11군 잔존: 오스트로프·프스코프 요새지대 고수, 벨리카야 교량 적 3km 접근 시 폭파",
               "1기계화군단: 오스트로프 북쪽 대기 → 돌파구 형성 순간 서측면 반격(사전 투입 금지)",
               "27군+21기계화 잔존: 오포치카~노보르제프 스탈린선, 적 기갑 북선회 시 측방 타격 / 8군 파르누~타르투~페이푸스 선",
               "요청: 북부전선 항공대 7.6~7.9 오스트로프~프스코프 집중"],
    },
    "center": {
        "de": ["4군: 노보그루도크~스톨프치 포위망 남·서 구간 인수·구멍 차단, 민스크 잔적 소탕 / 9군 비아위스토크 정리, 45사단 브레스트 요새",
               "2·3기갑: 인계 전까지 민스크 동쪽 포위선 유지, 인계 사단부터 보리소프·보브루이스크 맞은편 집결",
               "2항공함대: 탈출 종대·베레지나 접근로 타격(교량은 보존)",
               "요청: 보병 인계 구간부터 베레지나 도하 개시 OKH 승인"],
        "su": ["민스크 잔존: 버티다 야간 남동 돌파, 탈출 3·4·10군 보브루이스크·모길료프 재편성 후 베레지나 방어",
               "보리소프·보브루이스크 교량 고수, 적 전차 도달 시 즉시 폭파",
               "20군 5·7기계화군단: 비텝스크 남쪽 → 레펠 반격, 3기갑 측면 타격",
               "요청: 드네프르 2제대 투입 시점 통보"],
    },
    "south": {
        "de": ["3자동차화군단: 노보그라드-볼린스키 슬루치 도하점 한 곳 집중, 토치카 순차 제거 → 교두보 후 지토미르 가도",
               "48군단: 남쪽 견제 공격으로 적 예비 분산 / 6군 로브노~NV 도로 북측방 거점·주간 호송",
               "17군 리보프 서쪽 압박, 11군 프루트 교두보 확장 → 모길료프-포돌스키 드네스트르 도하점",
               "요청(정식): 4항공군 급강하폭격 돌파 구간 2~3일 집중"],
        "su": ["NV 수비대+보병군단+24기계화: 슬루치선 고수, 교두보 형성 즉시 기갑 도하 전 반격, 교량 폭파 준비",
               "5군+기계화 잔존: 야간 기습·도로 지뢰, 연료 종대·철도 공병 집중",
               "12군 모길료프-포돌스키·드네스트르 고수, 16기계화 반격 예비, 6·26군 돌출부 고수",
               "요청: NV 돌파 구간 전투기 연대·고사포 긴급 배정"],
    },
}

LOSSES = {
    "note": "게임 판정 추정치(누적, 전투력 기준). 실제 역사 수치 아님.",
    "north": dict(de_pct=12, su_pct=32, de_text="독 기갑·기계화 ~12%", su_text="소련 북서전선 ~32%"),
    "center": dict(de_pct=8, su_pct=40, de_text="독 ~8%", su_text="소련 서부전선 ~40%+"),
    "south": dict(de_pct=20, su_pct=28, de_text="독 1기갑집단 ~20%", su_text="소련 남서전선 기계화·제병 ~28%"),
}

SITUATION = {
    "north": "리가 함락. 4기갑집단 선두 레제크네~오스트로프 접근로 도달, 스탈린선 본격 돌파 전. 8군은 파르누·타르투 선, 27군과 접촉 단절.",
    "center": "민스크 외곽 포위는 닫혔으나 누수 큼(3·10군 상당수 남쪽 탈출). 비아위스토크 축소 중, 브레스트 요새 미함락. 베레지나는 소련 교량 방어·폭파 준비.",
    "south": "1기갑집단 노보그라드-볼린스키 요새 접근, 지토미르 미달. 5군 삼림 기습이 로브노 보급 교란. 11군·루마니아군 프루트 도하, 모길료프-포돌스키 압박.",
}

TACTICAL = {"north": [25.2, 30.9, 56.05, 58.75], "center": [25.4, 31.2, 52.35, 55.55], "south": [25.0, 30.6, 49.55, 51.75]}
OPERATIONAL = {"north": [21.0, 33.2, 54.9, 60.2], "center": [21.8, 33.6, 51.2, 56.3], "south": [21.6, 33.0, 45.7, 52.4]}

EVENTS = [
    dict(game_time="1941.6.28 24:00", axis="all", kind="turn", text="턴1 종료(주사위 북16/중15/남5): 드빈스크 교량 확보, 비아위스토크 포위 형성, 두브노-브로디 소련 협공으로 클라이스트 지연."),
    dict(game_time="1941.7.5 24:00", axis="north", kind="turn", text="턴2(주사위 12): 리가 함락, 레제크네 반격 실패. 스탈린선 미돌파, 8군 해안 유출."),
    dict(game_time="1941.7.5 24:00", axis="center", kind="turn", text="턴2(주사위 3): 민스크 포위 폐쇄되나 누수 커 3·10군 상당수 탈출. 베레지나 미도하·브레스트 미함락."),
    dict(game_time="1941.7.5 24:00", axis="south", kind="turn", text="턴2(주사위 13): 기갑 재정비 후 NV 요새 접근, 지토미르 미달. 프루트 도하 개시, 스타프카 돌출부 사전철수 거부."),
    dict(game_time="1941.7.6 00:00", axis="all", kind="system", text="라이브 진행 개시 — 실시간 1시간 = 게임 1일, 15분 = 6시간. 턴3 명령으로 판정."),
]


def build():
    return {
        "schema": 1,
        "title": "동부전선 1941 — 대체역사 라이브 워게임",
        "clock": {"date": "1941-07-06", "hour": 0},
        "turn": 3, "turn_range": "1941-07-06..1941-07-12",
        "paused": False, "mode": "auto",
        "status": "진행",           # 진행 | 판정 대기 | 일시정지
        "needs_plan": "1941-07-06",
        "tick_count": 0, "last_slot": None, "last_tick_real": None, "last_published_real": None,
        "applied": [],              # 적용된 키프레임 키 "YYYY-MM-DD@HH"
        "fronts": FRONTS, "german_closure": GERMAN_CLOSURE,
        "pockets": POCKETS, "arrows": ARROWS, "forts": FORTS, "units": UNITS,
        "orders": {a: {"turn": 3, "received": "2026-10-01 21:07~21:08 KST", **ORDERS[a]} for a in AXES},
        "situation": SITUATION, "losses": LOSSES,
        "views": {"tactical": TACTICAL, "operational": OPERATIONAL},
        "dice": [],
        "events": EVENTS,
        "maps": {"theater_game_date": None, "operational_game_date": None, "tactical_game_time": None, "version": 0},
        "seeded_real": iso_kst(),
    }


if __name__ == "__main__":
    if os.path.exists(STATE) and "--force" not in sys.argv:
        sys.exit("state.json 이미 있음 — 덮어쓰려면 --force")
    save_state(build())
    print("seeded", STATE)
