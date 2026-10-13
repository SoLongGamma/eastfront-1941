#!/usr/bin/env python3
"""예시 일일 계획 생성기 — 1941-07-06 (턴3 1일차). 주사위: shuf -i 1-20 -n 1 → 북18 / 중11 / 남13.
주사위는 공세 측(독일) 기준 판정: 1~5 불리, 6~15 기본, 16~20 유리."""
import copy, json, os, sys
LIVE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, LIVE)
from common import *  # noqa

st = load_state()
F = copy.deepcopy(st["fronts"])
stalin_tail = F["north"][2]["pts"][2:]          # (28.15,56.75) 이후 남쪽 구간은 유지

def north(gap_tail, stalin_head, estonia=None):
    est = estonia or F["north"][0]["pts"]
    return [dict(id="n-estonia", style="solid", pts=est),
            dict(id="n-gap", style="loose", pts=[[27.50, 57.98], [27.62, 57.70], [27.85, 57.46]] + gap_tail),
            dict(id="n-stalin", style="solid", pts=stalin_head + stalin_tail)]

south_pts = copy.deepcopy(F["south"][0]["pts"])
def south(nv):
    p = copy.deepcopy(south_pts); p[3] = nv
    return [dict(id="s-main", style="solid", pts=p)]

center_pts = copy.deepcopy(F["center"][0]["pts"])
def center(lepel):
    p = copy.deepcopy(center_pts); p[3] = lepel
    return [dict(id="c-dvina", style="solid", pts=p), F["center"][1]]

plan = {
  "schema": 1, "date": "1941-07-06", "turn": 3,
  "referee": "예시 판정(시드) — 턴3 수신 명령·state.md 7.5 상황 기준",
  "dice": [
    {"axis": "north", "roll": 18, "band": "유리", "note": "41군단 오스트로프 정면 돌파: 8항공군단 배속 도착 + 소련 1기계화 집결 미완 → 교량 확보"},
    {"axis": "center", "roll": 11, "band": "기본", "note": "4군 인계 진행·민스크 야간 돌파 일부 성공, 레펠 반격 선두 접촉"},
    {"axis": "south", "roll": 13, "band": "기본", "note": "슬루치 도하점 토치카 일부 제거, 교두보는 아직. 5군 야간 기습으로 연료 종대 피해"},
  ],
  "summary": {
    "north": "주사위 18(유리): 41군단이 오스트로프 토치카 지대를 좁은 정면으로 뚫고 벨리카야 교량 1곳을 확보, 오스트로프 장악.",
    "center": "주사위 11(기본): 4군 보병이 민스크 포위망 남·서 구간 인수 시작, 13군 잔존 일부 야간 돌파. 20군 기계화 선두 레펠 접근.",
    "south": "주사위 13(기본): 3자동차화군단 NV 슬루치 도하점 공격, 토치카 일부 제거했으나 교두보 미형성. 5군 야간 기습.",
  },
  "keyframes": [
    {"hour": 6,
     "events": [
       {"axis": "north", "text": "41기갑군단 돌격공병·포병, 새벽 오스트로프 남쪽 토치카 지대 좁은 정면 공격 개시. 8항공군단 슈투카 1개 비행단 도착."},
       {"axis": "center", "text": "4군 선두 보병사단, 스톨프치 남쪽에서 2기갑집단 포위선 인수 시작. 2항공함대 민스크 남동 탈출 종대 타격."},
       {"axis": "south", "text": "3자동차화군단 공병돌격대, 노보그라드-볼린스키 서쪽 슬루치 도하점 한 곳에 집중. 4항공군 급강하폭격 개시."}],
     "units": [
       {"id": "de-41pz", "lon": 27.90, "lat": 57.16},
       {"id": "de-3mot", "lon": 27.28, "lat": 50.64},
       {"id": "de-4a", "lon": 26.25, "lat": 53.25},
       {"id": "su-20a", "lon": 30.25, "lat": 55.02}]},
    {"hour": 12,
     "events": [
       {"axis": "north", "text": "슈투카 집중으로 오스트로프 남쪽 토치카 2km 구간 제압. 소련 전투기 요격은 산발적, 공역 경합에서 독일 우세."},
       {"axis": "center", "text": "소련 20군 5·7기계화군단, 비텝스크 남쪽에서 레펠 방향 행군 개시 — 늪지 도로에서 정비 낙오 다수."},
       {"axis": "south", "text": "슬루치 서안 토치카 3개 제거. 소련 고사포·전투기 증원 일부 도착해 급강하폭격 손실 발생."}],
     "fronts": {"north": north([[28.02, 57.28]], [[28.02, 57.28], [28.16, 57.27], [28.20, 57.18], [28.10, 57.08], [28.08, 57.02]])},
     "units": [
       {"id": "de-41pz", "lon": 28.05, "lat": 57.24, "strength": 83},
       {"id": "su-41rc", "strength": 55},
       {"id": "su-20a", "lon": 29.95, "lat": 54.98},
       {"id": "de-3mot", "lon": 27.36, "lat": 50.62, "strength": 79}]},
    {"hour": 18,
     "events": [
       {"axis": "north", "text": "1기갑사단 선두, 오스트로프 벨리카야 교량 1곳을 폭파 직전 확보(주사위 18) — 동안 교두보 형성."},
       {"axis": "north", "text": "소련 1기계화군단 집결 약 60%, '돌파구 형성 시 반격' 명령에 따라 오스트로프 북쪽에서 야간 반격 준비."},
       {"axis": "center", "text": "민스크 잔존 13군 일부, 해질녘 남동쪽 야간 돌파 시도 — 4군 인계 전 공백 구간으로 일부 빠져나감."},
       {"axis": "south", "text": "48군단 남쪽 견제 공격, 소련 24기계화군단은 요새선 뒤 은닉 유지(미투입). 교두보 형성 실패."}],
     "fronts": {"north": north([[28.05, 57.36], [28.22, 57.38]], [[28.22, 57.38], [28.40, 57.36], [28.42, 57.26], [28.28, 57.15], [28.12, 57.04]])},
     "units": [
       {"id": "de-41pz", "lon": 28.10, "lat": 57.30, "strength": 82, "dx": -11, "dy": 0},
       {"id": "de-56pz", "lon": 27.70, "lat": 56.88},
       {"id": "su-41rc", "lon": 28.66, "lat": 57.48, "strength": 52},
       {"id": "su-1mech", "lon": 28.98, "lat": 57.74},
       {"id": "su-13a", "strength": 27},
       {"id": "su-3-10a", "lon": 28.30, "lat": 52.70},
       {"id": "su-20a", "lon": 29.70, "lat": 54.95, "strength": 77}],
     "pockets": [{"id": "p-minsk", "rx": 0.68, "ry": 0.30}]},
    {"hour": 24,
     "events": [
       {"axis": "north", "text": "오스트로프 시가 대부분 독일군 장악. 41군단 교두보 폭 약 8km — 프스코프까지 50km."},
       {"axis": "north", "text": "18군 발미에라 북쪽으로 추격, 16군 선두 오포치카 서쪽 15km에서 27군 전초와 접촉."},
       {"axis": "center", "text": "20군 기계화 선두, 레펠 남서쪽에서 3기갑집단 측면 경계부대와 첫 접촉. 슈투카 공습으로 전차 손실."},
       {"axis": "center", "text": "OKH, 보병 인계 완료 구간의 기갑사단부터 7.7 이후 베레지나 도하 개시 승인(부분 승인)."},
       {"axis": "south", "text": "소련 5군 야간 기습, 로브노~NV 도로에서 독일 연료 종대 일부 파괴 — 주간 호송 원칙 밖 야간 이동분 피해."},
       {"axis": "south", "text": "11군 프루트 교두보 약 10km 확장, 루마니아군 남측방 진출. 12군은 모길료프-포돌스키 요새선 유지."}],
     "fronts": {
       "north": north([[28.10, 57.43], [28.30, 57.47]], [[28.30, 57.47], [28.53, 57.43], [28.58, 57.29], [28.42, 57.15], [28.15, 57.04]],
                      estonia=[[24.15, 58.13], [25.0, 58.07], [25.8, 58.05], [26.4, 58.12], [26.95, 58.12], [27.50, 57.98]]),
       "center": center([28.38, 54.86]),
       "south": south([27.55, 50.57])},
     "units": [
       {"id": "de-41pz", "lon": 28.14, "lat": 57.38, "strength": 81, "dx": -11, "dy": 0},
       {"id": "de-56pz", "lon": 27.82, "lat": 57.00, "strength": 86},
       {"id": "de-18a", "lon": 25.75, "lat": 57.85},
       {"id": "de-16a", "lon": 27.60, "lat": 56.52},
       {"id": "su-41rc", "lon": 28.70, "lat": 57.55, "strength": 50},
       {"id": "su-1mech", "lon": 28.95, "lat": 57.68, "strength": 60},
       {"id": "de-4a", "lon": 26.45, "lat": 53.30},
       {"id": "de-3pzg", "lon": 27.75, "lat": 54.55, "strength": 81},
       {"id": "su-13a", "strength": 25},
       {"id": "su-3-10a", "lon": 28.45, "lat": 52.78, "strength": 27},
       {"id": "su-20a", "lon": 29.45, "lat": 54.92, "strength": 74},
       {"id": "de-3mot", "lon": 27.40, "lat": 50.64, "strength": 77},
       {"id": "de-48mot", "strength": 73},
       {"id": "de-6a", "lon": 26.40, "lat": 50.84, "strength": 87},
       {"id": "su-nv", "strength": 70},
       {"id": "su-5a", "lon": 28.05, "lat": 51.15, "strength": 51},
       {"id": "de-11a", "lon": 27.10, "lat": 47.70, "strength": 90}],
     "pockets": [
       {"id": "p-minsk", "rx": 0.62, "ry": 0.28, "label": "민스크 포위망\n(4군 인계 중 · 일부 야간 탈출)"},
       {"id": "p-bialystok", "rx": 0.45, "ry": 0.23, "label": "비아위스토크 내부 포위망\n(섬멸 단계)"}],
     "arrows": [
       {"id": "a-41pz", "pts": [[28.40, 57.45], [28.38, 57.62], [28.33, 57.76]], "label": "4기갑집단(41군단)\n→ 프스코프", "lx": 27.35, "ly": 57.62, "goal_off": [-34, 2]},
       {"id": "a-1mech", "pts": [[28.92, 57.78], [28.72, 57.60], [28.52, 57.47]], "goal": None},
       {"id": "a-20a", "pts": [[29.35, 54.98], [29.05, 54.93], [28.62, 54.88]], "goal": "→ 레펠 (선두 접촉)", "lx": 29.6, "ly": 54.7},
       {"id": "a-esc", "pts": [[26.40, 53.30], [26.70, 52.85], [27.70, 52.62], [28.80, 52.78]]}],
     "losses": {
       "north": {"de_pct": 13, "su_pct": 34, "de_text": "독 기갑·기계화 ~13%", "su_text": "소련 북서전선 ~34%"},
       "center": {"de_pct": 9, "su_pct": 42, "de_text": "독 ~9%", "su_text": "소련 서부전선 ~42%"},
       "south": {"de_pct": 21, "su_pct": 29, "de_text": "독 1기갑집단 ~21%", "su_text": "소련 남서전선 기계화·제병 ~29%"}},
     "situation": {
       "north": "7.6 오스트로프 함락·벨리카야 교두보 확보. 41군단 프스코프 50km 전방, 소련 1기계화군단(집결 60%) 야간 서측면 반격 준비. 16군 오포치카 접근.",
       "center": "4군이 민스크 포위망 남·서 구간 인수 중, 13군 잔존 일부 야간 탈출. 20군 5·7기계화 레펠 접근·첫 접촉. OKH 베레지나 도하 부분 승인(7.7~).",
       "south": "3자동차화군단 슬루치 서안 토치카 일부 제거, 교두보 미형성. 24기계화 은닉 대기. 5군 야간 기습으로 연료 종대 피해. 11군 프루트 교두보 확장."}}
  ]
}
out = os.path.join(LIVE, "plans", "1941-07-06.json")
save_json(out, plan)
print(out)
