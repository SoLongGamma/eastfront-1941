"""명령 라운드: strategy.json round_days(현재 14일) 경계에서 일시정지 + awaiting_orders.json + 브리핑 3장(각 < 2 KB) + digest.md."""
import datetime as dt, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *  # noqa

FLAG = os.path.join(LIVE, "awaiting_orders.json")
BRIEFS = os.path.join(LIVE, "briefs")
DAYLOG = os.path.join(LIVE, "daylog.md")
AX = {"north": ("북부축", "북부집단군", "소련 북서전선"), "center": ("중부축", "중부집단군", "소련 서부전선"),
      "south": ("남부축", "남부집단군", "소련 남서전선")}


BRIEF_LIMIT = 1950


def cut(s, n):
    s = " ".join(str(s or "").split())
    return s if len(s) <= n else s[:n - 1] + "…"


def d2(s):
    d = dt.date.fromisoformat(s); return f"{d.month}.{d.day}"


def is_boundary(date, strat):
    a = dt.date.fromisoformat(strat.get("round_anchor", "1941-08-23"))
    n = strat.get("round_days", 28)
    diff = (dt.date.fromisoformat(date) - a).days
    return diff >= 0 and diff % n == 0


def round_no(date, strat):
    a = dt.date.fromisoformat(strat.get("round_anchor", "1941-08-23"))
    return (dt.date.fromisoformat(date) - a).days // strat.get("round_days", 28) + 1


def write_briefs(st, end_date, strat):
    """end_date = 방금 끝난 날(24:00). 다음 블록 = end+1 .. end+round_days."""
    N = round_no(end_date, strat)
    nd = strat.get("round_days", 28)
    e = dt.date.fromisoformat(end_date)
    s0 = (e - dt.timedelta(days=nd - 1)).isoformat()
    n0, n1 = (e + dt.timedelta(days=1)).isoformat(), (e + dt.timedelta(days=nd)).isoformat()
    js = st.get("judge") or {}
    out = []
    os.makedirs(BRIEFS, exist_ok=True)
    for a in AXES:
        name, de, su = AX[a]
        rolls = [r for d in st.get("dice", []) if s0 <= d["date"] <= end_date for r in d["rolls"] if r.get("axis") == a]
        cnt = {b: sum(1 for r in rolls if r.get("band") == b) for b in ("유리", "기본", "불리")}
        avg = sum(r["roll"] for r in rolls) / len(rolls) if rolls else 0
        import judge as J
        cap_txt = J.brief_capture(st, a, s0, end_date)
        caps = [ev["text"] for ev in st["events"] if ev.get("axis") == a and ev.get("kind") in ("capture", "transfer", "pocket", "booty")
                and s0 <= _ev_date(ev) <= end_date]
        caps = [c for i, c in enumerate(caps) if not any(c[:12] == d[:12] for d in caps[i + 1:])][-3:]   # 반복 유형은 최신 1건
        cfg = strat["axes"][a]
        last = (st.get("last_day") or {}).get("summary", {}).get(a, "")
        if a == "south":
            si = (js.get("stage") or {}).get("south", 0)
            stg = cfg["stages"][min(si, len(cfg["stages"]) - 1)]
            rem = [o["name"] for o in stg.get("objectives", []) if o["name"] not in js.get("captured", [])]
            outlook = f"{stg['name']} — 남은 목표: {', '.join(rem) or '없음(다음 단계)'}. 증원 보너스는 전용 기갑 도착에 따라 단계 상승(strategy.json mod)."
            okh = "남부 유전 최우선. 북·중부 기갑·항공을 남부로 순차 전용. 목표 점령 후 강력한 방어선 구축. 시가 정면 소모전 회피, 도하는 공병·교두 확보 후."
        else:
            outlook = f"보병 고수·견제 태세. 대규모 공세 없음, 국지 개선·국지 상실만. 섹터: {', '.join(s['name'] for s in cfg.get('sectors', []))}."
            okh = f"{de}은 현 전선 고수(보병), 견제·고착만. 기갑·항공은 남부집단군으로 전용. 국지 위기 시 예비 보병만 투입."
        per = f"{nd}일"
        for lim, cl, nc in ((260, 110, 3), (160, 80, 2), (90, 60, 1), (0, 0, 0)):   # 2 KB 상한: 현황·이벤트부터 줄임
            cur = cut(f"최근: {last} 현황: {st['situation'].get(a, '')}", lim) if lim else ""
            cs = caps[-nc:] if nc else []
            txt = (f"[심판] 명령 라운드 {N} — {name} ({n0.replace('-', '.')} ~ {n1.replace('-', '.')}, {per})\n\n"
                   f"{per} 결산({d2(s0)}~{d2(end_date)}): 주사위 유리 {cnt['유리']}·기본 {cnt['기본']}·불리 {cnt['불리']} (평균 {avg:.1f}). "
                   + (" ".join(cut(c, cl) for c in cs) + " " if cs else "") + f"{cur} (손실은 게임 추정치. {cap_txt})\n\n"
                   f"전망({d2(n0)}~{d2(n1)}): {outlook}\n\n"
                   f"OKH/히틀러: {okh}\n\n"
                   f"스타프카: {cfg.get('su_posture', '현 태세 유지').replace('스타프카: ', '')}. 무단 철수 금지 유지, 예비는 위협 축 우선.\n\n"
                   f"다음 {per} 명령: 독일 {de} / {su} 각각 [명령] 최대 3 · [요청] 1 · [리스크] 1. {d2(n0)} 00시부터 반영 "
                   f"(미도착 시 {strat.get('await_timeout_min', 15)}분 후 기존 명령·전략 유지로 자동 재개).\n")
            if len(txt.encode()) <= BRIEF_LIMIT:
                break
        p = os.path.join(BRIEFS, f"round{N}-{a}.md")
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(txt)
        out.append(p)
    return N, (n0, n1), out


def _ev_date(ev):
    try:
        y, m, rest = ev["game_time"].split(".", 2)
        d = rest.split(" ")[0]
        return f"{int(y):04d}-{int(m):02d}-{int(d):02d}"
    except Exception:
        return ""


def set_flag(st, end_date, strat):
    N, rng, briefs = write_briefs(st, end_date, strat)
    now = now_kst()
    flag = dict(round=N, range=list(rng), boundary=f"{end_date} 24:00", briefs=briefs,
                since_real=iso_kst(now), auto_resume_real=iso_kst(now + dt.timedelta(minutes=strat.get("await_timeout_min", 15))),
                resume_cmd="live/resume.sh auto")
    save_json(FLAG, flag)
    st["paused"] = True
    st["status"] = "명령 대기"
    st["awaiting_orders"] = flag
    st["events"].append(dict(game_time=game_stamp(end_date, 24), axis="all", kind="system",
                             text=f"명령 라운드 {N} — {d2(rng[0])}~{d2(rng[1])} {strat.get('round_days', 14)}일 명령 수집 중, 시계 정지", real_time=iso_kst()))
    daylog(f"- **명령 라운드 {N} 대기** ({end_date} 24:00, 실시간 {iso_kst()[:16]} KST) — 브리핑 {', '.join(os.path.basename(b) for b in briefs)}")
    return flag


def clear_flag(st, reason):
    f = st.pop("awaiting_orders", None)
    if os.path.exists(FLAG):
        try:
            f = f or load_json(FLAG)
        except Exception:
            pass
        os.remove(FLAG)
    st["paused"] = False
    st["status"] = "진행"
    if f:
        st["events"].append(dict(game_time=game_stamp(st["clock"]["date"], st["clock"]["hour"]), axis="all", kind="system",
                                 text=f"명령 라운드 {f.get('round')} 종료 — {reason}", real_time=iso_kst()))
        daylog(f"- 명령 라운드 {f.get('round')} 재개: {reason} (실시간 {iso_kst()[:16]} KST)")
    return f


def daylog(line):
    new = not os.path.exists(DAYLOG)
    with open(DAYLOG, "a", encoding="utf-8") as fh:
        if new:
            fh.write("# 일일 판정 로그 (절차 판정 judge.py)\n\n")
        fh.write(line.rstrip("\n") + "\n")
