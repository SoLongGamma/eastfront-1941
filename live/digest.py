#!/usr/bin/env python3
"""심판용 압축 다이제스트 → live/digest.md (< 4 KB).
심판 봇은 digest.md + briefs/roundN-*.md + strategy.json 만 읽는다(state.json/state.md 금지).
  digest.py            생성(수동 실행 가능, tick.py 가 라운드 경계마다 자동 실행)
  digest.py --print    생성 후 출력
"""
import datetime as dt, glob, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *  # noqa

OUT = os.path.join(LIVE, "digest.md")
SNAP = os.path.join(LIVE, "snapshots")
NAME = {"north": "북부", "center": "중부", "south": "남부"}
LIMIT = 4000


def tick_period():
    p = os.environ.get("TICK_PERIOD")
    if not p:
        try:
            for ln in open(os.path.join(LIVE, "ticker.conf"), encoding="utf-8"):
                if ln.strip().startswith("TICK_PERIOD="):
                    p = ln.split("=", 1)[1].strip()
        except OSError:
            pass
    return int(p or 3600)


def cut(s, n):
    s = " ".join(str(s or "").split())
    return s if len(s) <= n else s[:n - 1] + "…"


def ev_date(ev):
    try:
        y, m, rest = ev["game_time"].split(".", 2)
        return f"{int(y):04d}-{int(m):02d}-{int(rest.split(' ')[0]):02d}"
    except Exception:
        return ""


def d2(s):
    d = dt.date.fromisoformat(s); return f"{d.month}.{d.day}"


def snapshot_at(date):
    """date 00시 스냅숏(없으면 그 이후 가장 이른 것)."""
    fs = sorted(glob.glob(os.path.join(SNAP, "*T00.json")))
    for f in fs:
        if os.path.basename(f)[:10] >= date:
            return f
    return None


def front_change(st, old):
    """축별 독일 통제 면적 변화(km²)와 평균 전진(km) — 게임 추정."""
    try:
        import judge as J
        from shapely.geometry import LineString
        pn, po = J.german_poly(st), J.german_poly(old)
        res = {}
        for a in AXES:
            segs = [s["pts"] for s in st["fronts"].get(a, [])] + [s["pts"] for s in old["fronts"].get(a, [])]
            pts = [p for s in segs for p in s]
            if len(pts) < 2:
                continue
            zone = LineString(pts).buffer(1.2)
            lat0 = sum(p[1] for p in pts) / len(pts)
            k2 = (111.32 ** 2) * math.cos(math.radians(lat0))
            gain = pn.difference(po).intersection(zone).area * k2
            loss = po.difference(pn).intersection(zone).area * k2
            L = sum(J.dist_km(s[i], s[i + 1]) for s in [x["pts"] for x in st["fronts"].get(a, [])] for i in range(len(s) - 1))
            res[a] = (gain, loss, (gain - loss) / L if L else 0)
        return res
    except Exception as e:
        return {"err": str(e)}


def next_boundary(st, strat, period):
    a = dt.date.fromisoformat(strat.get("round_anchor", "1941-08-23"))
    n = strat.get("round_days", 14)
    cur = dt.date.fromisoformat(st["clock"]["date"])   # 아직 판정 안 된 날
    diff = (cur - a).days
    k = max(0, -(-diff // n))
    b = a + dt.timedelta(days=k * n)
    rnd = k + 1
    ticks = (b - cur).days + 1   # 경계일 판정 틱 포함
    return b, rnd, ticks


def build(st=None):
    st = st or load_state()
    strat = load_json(os.path.join(LIVE, "strategy.json"))
    period = tick_period()
    nd = strat.get("round_days", 14)
    cur = st["clock"]["date"]
    since = (dt.date.fromisoformat(cur) - dt.timedelta(days=nd)).isoformat()
    js = st.get("judge") or {}
    snap = snapshot_at(since)
    fc = front_change(st, load_json(snap)) if snap else {}
    b, rnd, ticks = next_boundary(st, strat, period)
    now = now_kst()
    nxt = dt.datetime.fromtimestamp((int(now.timestamp()) // period + 1) * period + 2, KST)
    aw = st.get("awaiting_orders")
    if aw:
        eta = f"명령 대기 중(라운드 {aw.get('round')}) — 자동 재개 {aw.get('auto_resume_real', '')[:16]} KST"
    elif st.get("paused"):
        eta = f"일시정지 중 — 재개 후 {ticks}틱(≈{ticks * period / 3600:g}시간)"
    else:
        eta = f"≈ 실시간 {(nxt + dt.timedelta(seconds=period * (ticks - 1))).strftime('%m-%d %H:%M')} KST ({ticks}틱 후)"
    import judge as J
    L = [f"# 심판 다이제스트 — 게임 {clock_label(st['clock'])} 시작 전",
         f"상태: {st.get('status')}{' (paused)' if st.get('paused') else ''} · 턴 {st.get('turn')} · 1틱={period // 60}분=1일 · 생성 {now.strftime('%m-%d %H:%M')} KST",
         f"다음 라운드 {rnd} 경계: {b.isoformat()} 24:00 · {eta}",
         f"구간 기준: 최근 {nd}일({d2(since)}~{d2((dt.date.fromisoformat(cur) - dt.timedelta(days=1)).isoformat())}), 수치는 게임 추정치", ""]
    for a in AXES:
        cfg = strat["axes"][a]
        ov = cfg.get("override") or {}
        posture = cfg["posture"]
        if ov and cur <= ov.get("until", ""):
            posture = f"{ov.get('posture')}(override~{d2(ov['until'])})"
        L.append(f"## {NAME[a]} — {posture}")
        L.append(f"- 방침: {cut(cfg.get('summary'), 110)}")
        if cfg.get("stages"):
            si = (js.get("stage") or {}).get(a, 0)
            stg = cfg["stages"][min(si, len(cfg["stages"]) - 1)]
            prog = ", ".join(f"{o['name']} {'✔' if o['name'] in js.get('captured', []) else str(js.get('progress', {}).get(o['name'], 0)) + '/' + str(o.get('resist', '?'))}"
                             for o in stg.get("objectives", []))
            L.append(f"- 단계 {si + 1}/{len(cfg['stages'])} {cut(stg['name'], 40)}: {prog or '목표 없음'}")
        elif cfg.get("objectives"):
            L.append("- 목표: " + ", ".join(f"{o['name']} {js.get('progress', {}).get(o['name'], 0)}/{o.get('resist', '?')}" for o in cfg["objectives"]))
        else:
            L.append("- 섹터: " + ", ".join(s["name"] for s in cfg.get("sectors", [])))
        rolls = [r for d in st.get("dice", []) if since <= d["date"] < cur for r in d["rolls"] if r.get("axis") == a]
        cnt = {k: sum(1 for r in rolls if r.get("band") == k) for k in ("유리", "기본", "불리")}
        f = fc.get(a)
        npk = sum(1 for p in st.get("pockets", []) if p.get("axis") == a)
        mv = (f"독 통제 +{f[0]:,.0f}/−{f[1]:,.0f} km², 평균 {f[2]:+.1f} km" + (f"(포위망 {npk}개 반영)" if npk else "")) if f else "자료 없음"
        L.append(f"- {nd}일 전선: {mv} · 주사위 유리{cnt['유리']}/기본{cnt['기본']}/불리{cnt['불리']}")
        evs = [e for e in st.get("events", []) if e.get("axis") == a and since <= ev_date(e) < cur and
               (e.get("kind") in ("capture", "pocket", "booty") or any(w in e.get("text", "") for w in ("포위", "도하", "장악", "점령", "돌파", "노획")))
               and not e.get("text", "").startswith("정오")]
        seen, keep = set(), []
        for e in reversed(evs):   # 같은 유형(앞 12자) 반복은 최신 1건만
            k = e.get("text", "")[:12]
            if k not in seen:
                seen.add(k); keep.append(e)
        for e in reversed(keep[:3]):
            L.append(f"  - {ev_date(e)[5:]}: {cut(e['text'], 80)}")
        lo = (st.get("losses") or {}).get(a) or {}
        L.append(f"- 손실(누적 전투력): 독 {lo.get('de_pct', '?')}% · 소 {lo.get('su_pct', '?')}%")
        L.append("- " + J.capture_line(J.captures_of(st)[a], J.sum_vehicles(st, a, since, cur, False)))
        if cfg.get("su_posture"):
            L.append(f"- 소련: {cut(cfg['su_posture'].replace('스타프카: ', ''), 90)}")
        L.append("")
    tst = js.get("transfers", {})
    L.append("## 기갑 전용")
    for t in strat.get("transfers", []):
        s = tst.get(t["unit"], "대기")
        s = {"transit": "이동 중", "arrived": "도착"}.get(s, s)
        L.append(f"- {t['name']}({NAME.get(t['from'], t['from'])}→남부) {d2(t['depart'])}→{d2(t['arrive'])}: {s}")
    txt = "\n".join(L).rstrip() + "\n"
    # 크기 상한: 넘으면 이벤트 줄부터 줄인다
    while len(txt.encode()) > LIMIT:
        idx = [i for i, l in enumerate(L) if l.startswith("  - ")]
        if idx:
            L.pop(idx[0])
        else:
            L = [cut(l, 70) for l in L]
        txt = "\n".join(L).rstrip() + "\n"
        if not idx and len(txt.encode()) > LIMIT:
            txt = txt.encode()[:LIMIT].decode(errors="ignore"); break
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(txt)
    return OUT, len(txt.encode())


if __name__ == "__main__":
    p, n = build()
    print(f"{p} {n} bytes")
    if "--print" in sys.argv:
        print(open(p, encoding="utf-8").read())
