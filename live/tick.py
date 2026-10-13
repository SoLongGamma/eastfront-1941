#!/usr/bin/env python3
"""틱 엔진 (LLM 없음). judge 모드: 호출 1회 = 게임 1일(주기 ticker.conf TICK_PERIOD, 현재 3600초). 구 모드: 1 페이즈.

  tick.py                 현재 15분 슬롯에 아직 틱이 없으면 1 페이즈 진행 → 지도·사이트 갱신 → 게시
  tick.py --force         슬롯 중복 검사 무시 (수동 테스트용, 그래도 한 번에 1 페이즈만)
  tick.py --render-all    전술·전역·전체 지도 모두 재생성
  tick.py --no-publish    게시 생략
  tick.py --site-only     진행 없이 사이트만 재생성(+게시)

멱등성: (1) 같은 15분 슬롯(KST)에서 두 번째 호출은 아무것도 안 함, (2) 키프레임은 "날짜@시각" 키로
한 번만 적용, (3) 파일 잠금으로 동시 실행 차단, (4) state.json 은 원자적 저장.
"""
import datetime as dt, json, os, shutil, subprocess, sys, traceback
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *  # noqa
import apply_plan as AP

ARCHIVE = os.path.join(LIVE, "maps_archive")
SNAP = os.path.join(LIVE, "snapshots")


def log(*a):
    print(f"[{now_kst().strftime('%Y-%m-%d %H:%M:%S KST')}]", *a, flush=True)


def publish():
    sh = os.path.join(LIVE, "publish.sh")
    try:
        r = subprocess.run(["bash", sh], capture_output=True, text=True, timeout=180)
        out = (r.stdout + r.stderr).strip().splitlines()
        log("publish rc=%d" % r.returncode, " | ".join(out[-4:]))
        return r.returncode == 0
    except Exception as e:
        log("publish 실패:", e)
        return False


def advance(st):
    """한 페이즈 진행. (day_complete, changed) 반환."""
    date, hour, newclock = next_phase(st["clock"])
    key = f"{date}@{hour:02d}"
    plan = AP.load_plan(date)
    if plan is not None:
        errs, _ = AP.validate(plan, st)
        if errs:
            log("계획 검증 실패 → 판정 대기:", errs[:3])
            plan = None
    if plan is None:
        gt = game_stamp(st["clock"]["date"], st["clock"]["hour"])
        last = st["events"][-1] if st["events"] else {}
        if not (last.get("kind") == "wait" and last.get("game_time") == gt):
            st["events"].append(dict(game_time=gt, axis="all", kind="wait",
                                     text=f"판정 대기 — {date} 일일 판정 계획 미도착, 전 축 현 위치 유지.", real_time=iso_kst()))
        st["status"] = "판정 대기"
        log("plan 없음:", date, "→ 판정 대기 (시계 정지)")
        return False, False
    if key in st["applied"]:
        log("이미 적용된 키프레임", key, "→ 시계만 맞춤")
        st["clock"] = newclock
        return hour == 24, False
    kf = next((k for k in plan["keyframes"] if k["hour"] == hour), None)
    if kf is not None:
        added = AP.apply_keyframe(st, plan, kf)
        log("키프레임 적용", key, f"이벤트 {len(added)}건")
    else:
        nxt = next(k for k in plan["keyframes"] if k["hour"] > hour)
        frac = 6.0 / (nxt["hour"] - (hour - 6))
        AP.interpolate_phase(st, nxt, frac)
        log("보간", key, f"→ {nxt['hour']}시 키프레임 {frac:.2f}")
    if not any(d.get("date") == date for d in st["dice"]):
        st["dice"].append(dict(date=date, rolls=plan["dice"]))
    st["day"] = dict(date=date, summary=plan.get("summary", {}), dice=plan["dice"], referee=plan.get("referee", ""))
    if hour == 24:
        st["last_day"] = dict(date=date, summary=plan.get("summary", {}), dice=plan["dice"])
    st["applied"].append(key)
    st["clock"] = newclock
    st["tick_count"] += 1
    st["status"] = "진행"
    return hour == 24, True


SLOT_HOUR = {15: 6, 30: 12, 45: 18, 0: 24}   # 실시간 분 → 적용할 키프레임 시각 (정시 = 하루 끝)
IDX = {6: 0, 12: 1, 18: 2, 24: 3}


def phases_to_run(st, slot, no_align):
    """정시 정렬: :15→06시, :30→12시, :45→18시, :00→24시. 1슬롯 밀렸으면 2페이즈로 따라잡고,
    앞서 있거나 2슬롯 이상 어긋나면 맞는 슬롯까지 대기(최대 3슬롯). 판정 대기 중이면 1(=대기 재확인)."""
    if no_align or not st.get("align", True):
        return 1
    if not os.path.exists(plan_path(next_phase(st["clock"])[0])):
        return 1  # 계획 없음 → advance() 가 '판정 대기' 기록
    if st.get("status") == "판정 대기" and st["clock"]["hour"] != 0:
        return 1
    target = SLOT_HOUR[int(slot[14:16])]
    nxt = next_phase(st["clock"])[1]
    diff = (IDX[target] - IDX[nxt]) % 4
    return {0: 1, 1: 2}.get(diff, 0)


def render_maps(st, day_complete, render_all):
    import render as R
    t0 = now_kst()
    R.render_kind(st, "tactical")
    done = ["tactical"]
    m = st["maps"]
    if day_complete or render_all or not os.path.exists(R.map_path("operational", "north")):
        R.render_kind(st, "operational"); done.append("operational")
        m["operational_game_date"] = st["clock"]["date"]
        m["operational_game_time"] = clock_label(st["clock"])
        os.makedirs(ARCHIVE, exist_ok=True)
        for a in AXES:
            shutil.copy(R.map_path("operational", a), os.path.join(ARCHIVE, f"operational_{a}_{st['clock']['date']}.png"))
    cd = dt.date.fromisoformat(st["clock"]["date"])
    last = m.get("theater_game_date")
    if render_all or last is None or (cd - dt.date.fromisoformat(last)).days >= 24 \
            or not os.path.exists(R.map_path("theater")):
        R.render_kind(st, "theater"); done.append("theater")
        m["theater_game_date"] = st["clock"]["date"]
        m["theater_game_time"] = clock_label(st["clock"])
        os.makedirs(ARCHIVE, exist_ok=True)
        shutil.copy(R.map_path("theater"), os.path.join(ARCHIVE, f"theater_{st['clock']['date']}.png"))
    m["tactical_game_time"] = clock_label(st["clock"])
    m["version"] = int(m.get("version", 0)) + 1
    m["rendered_real"] = iso_kst()
    log("지도 렌더:", done, f"{(now_kst() - t0).total_seconds():.1f}s")


# ------------------------------------------------------------------ 절차 판정 모드 (틱 1회 = 게임 1일, 주기 ticker.conf TICK_PERIOD)
def period_slot(t=None):
    """현재 틱 슬롯(KST, TICK_PERIOD 초 단위로 내림) — last_slot 멱등 키. 3600 → 매시 정각."""
    import digest as DG
    P = DG.tick_period()
    t = t or now_kst()
    s = int(t.timestamp()) // P * P
    return dt.datetime.fromtimestamp(s, KST).strftime("%Y-%m-%dT%H:%M+09:00")


def judge_day(st):
    """게임 하루(00→24시) 진행. judge.py 계획 생성/재사용 → 키프레임 전부 적용. 반환: 끝난 날짜."""
    import judge as J, rounds as RD
    date = st["clock"]["date"]
    if st["clock"]["hour"] != 0:
        # 구 엔진의 하루 중간이면 기존 계획 나머지 페이즈 적용
        while st["clock"]["hour"] != 0:
            dc, ch = advance(st)
            if st["status"] != "진행":
                return None
        return date
    plan, new = J.ensure_plan(st, date)
    log("계획", date, "생성" if new else "재사용", {r["axis"]: r["roll"] for r in plan["dice"]})
    for kf in plan["keyframes"]:
        key = f"{date}@{kf['hour']:02d}"
        if key in st["applied"]:
            continue
        AP.apply_keyframe(st, plan, kf)
        st["applied"].append(key)
    if plan.get("judge_state") is not None:
        st["judge"] = plan["judge_state"]
    if not any(d.get("date") == date for d in st["dice"]):
        rec = dict(date=date, rolls=plan["dice"])
        if plan.get("vehicles"):
            rec["vehicles"] = plan["vehicles"]
        st["dice"].append(rec)
    st["day"] = dict(date=date, summary=plan.get("summary", {}), dice=plan["dice"], referee=plan.get("referee", ""))
    st["last_day"] = dict(date=date, summary=plan.get("summary", {}), dice=plan["dice"])
    st["clock"] = {"date": (dt.date.fromisoformat(date) + dt.timedelta(days=1)).isoformat(), "hour": 0}
    st["tick_count"] = st.get("tick_count", 0) + 1
    st["status"] = "진행"
    t = plan.get("turn")
    if t:
        st["turn"] = t
        d0 = dt.date(1941, 8, 17) + dt.timedelta(days=7 * (t - 9))
        st["turn_range"] = f"{d0.isoformat()}..{(d0 + dt.timedelta(days=6)).isoformat()}"
    sm = plan.get("summary", {})
    rr = "/".join(str(next((r["roll"] for r in plan["dice"] if r["axis"] == a), "?")) for a in AXES)
    RD.daylog(f"- {date.replace('-', '.')} (절차 판정) 주사위 북/중/남 {rr}. 북: {sm.get('north', '')} 중: {sm.get('center', '')} 남: {sm.get('south', '')}")
    # 이벤트 상한(오래된 것은 events_archive.jsonl)
    if len(st["events"]) > 800:
        old, st["events"] = st["events"][:-600], st["events"][-600:]
        with open(os.path.join(LIVE, "events_archive.jsonl"), "a", encoding="utf-8") as fh:
            for e in old:
                fh.write(json.dumps(e, ensure_ascii=False) + "\n")
    return date


def prune_snapshots(keep=300):
    try:
        fs = sorted(f for f in os.listdir(SNAP) if f.endswith(".json"))
        for f in fs[:-keep]:
            os.remove(os.path.join(SNAP, f))
    except Exception as e:
        log("snapshot 정리 실패", e)


def render_judge(st, boundary):
    import render as R
    t0 = now_kst()
    m = st["maps"]
    done = []
    # 렌더 비용(측정): 전체도 ~0.9s, 전역도 3장 ~1.3s, 전술도 3장 ~0.9s → 매 틱 전부 렌더 (< 5s)
    R.render_kind(st, "theater"); done.append("theater")
    lbl = clock_label(st["clock"])
    m["theater_game_date"] = st["clock"]["date"]; m["theater_game_time"] = lbl
    if not st.get("render_light"):
        R.render_kind(st, "operational"); R.render_kind(st, "tactical"); done += ["operational", "tactical"]
        m["operational_game_date"] = st["clock"]["date"]; m["operational_game_time"] = lbl
        m["tactical_game_time"] = lbl
    os.makedirs(ARCHIVE, exist_ok=True)
    cd = dt.date.fromisoformat(st["clock"]["date"])
    if cd.weekday() == 6 or boundary:   # 새 날짜가 일요일 = 주 종료(토 24시)
        shutil.copy(R.map_path("theater"), os.path.join(ARCHIVE, f"theater_{st['clock']['date']}.png"))
    if boundary and "operational" in done:
        for a in AXES:
            shutil.copy(R.map_path("operational", a), os.path.join(ARCHIVE, f"operational_{a}_{st['clock']['date']}.png"))
    m["version"] = int(m.get("version", 0)) + 1
    m["rendered_real"] = iso_kst()
    secs = (now_kst() - t0).total_seconds()
    m["render_secs"] = round(secs, 1)
    log("지도 렌더:", done, f"{secs:.1f}s")


def judge_main(argv, st):
    import rounds as RD, judge as J
    slot = period_slot()
    force = "--force" in argv
    boundary = False
    if st.get("last_slot") == slot and not force:
        log("이 슬롯은 이미 처리됨:", slot); return False, False
    st["last_slot"] = slot
    st["last_tick_real"] = iso_kst()
    if st.get("paused"):
        aw = st.get("awaiting_orders") or (RD.load_json(RD.FLAG) if os.path.exists(RD.FLAG) else None)
        # 90초 여유: 정시 틱(:00:02)이 경계 틱 직후 기록된 auto_resume(:00:0x)을 한 시간 더 놓치지 않게
        if aw and now_kst() + dt.timedelta(seconds=90) >= dt.datetime.fromisoformat(aw["auto_resume_real"]):
            RD.clear_flag(st, f"명령 미도착 {J.load_strategy().get('await_timeout_min', 120)}분 경과 — 기존 명령·전략(standing orders)으로 자동 재개")
            log("명령 대기 시간 초과 → 자동 재개")
        else:
            st["status"] = "명령 대기" if aw else "일시정지"
            log("일시정지 중(%s) → 진행 안 함" % st["status"])
            return False, True
    ended = judge_day(st)
    if ended is None:
        return False, True
    strat = J.load_strategy()
    if RD.is_boundary(ended, strat):
        flag = RD.set_flag(st, ended, strat)
        boundary = True
        log("명령 라운드 경계:", ended, "→ 일시정지, awaiting_orders.json round", flag["round"])
        try:   # 심판용 압축 다이제스트(digest.md) — 심판은 이것 + briefs + strategy.json 만 읽는다
            import digest as DG
            dp, dn = DG.build(st)
            flag["digest"] = dp
            save_json(RD.FLAG, flag); st["awaiting_orders"] = flag
            log("digest.md", dn, "bytes")
        except Exception as e:
            log("digest 실패:", e)
    render_judge(st, boundary)
    os.makedirs(SNAP, exist_ok=True)
    save_json(os.path.join(SNAP, f"{st['clock']['date']}T{st['clock']['hour']:02d}.json"), st)
    prune_snapshots()
    st["needs_plan"] = None
    log("게임 시각:", clock_label(st["clock"]), "| 상태:", st["status"])
    return True, True


def main(argv):
    force = "--force" in argv
    render_all = "--render-all" in argv
    no_pub = "--no-publish" in argv
    site_only = "--site-only" in argv
    try:
        with state_lock(blocking=False):
            st = load_state()
            slot = slot_kst()
            if site_only:
                pass
            elif st.get("engine") == "judge":
                did, cont = judge_main(argv, st)
                if not cont:
                    return 0
            elif st.get("last_slot") == slot and not force:
                log("이 슬롯은 이미 처리됨:", slot, "→ 건너뜀")
                return 0
            else:
                st["last_slot"] = slot
                st["last_tick_real"] = iso_kst()
                if st.get("paused"):
                    prev = st.get("status")
                    st["status"] = "일시정지"
                    save_state(st)
                    log("일시정지 중 → 진행 안 함")
                    if prev == "일시정지":
                        return 0
                    site_only = True  # 상태 배지만 갱신
                else:
                    n = phases_to_run(st, slot, force or "--no-align" in argv)
                    day_complete = changed = False
                    for _ in range(n):
                        dc, ch = advance(st)
                        day_complete |= dc; changed |= ch
                        if st["status"] != "진행":
                            break
                    st["align_hold"] = (n == 0)
                    if n == 0:
                        log("정시 정렬 대기 — 다음 페이즈", next_phase(st["clock"])[1], "시는 해당 슬롯에서 진행")
                    if changed or render_all:
                        render_maps(st, day_complete, render_all)
                    st["needs_plan"] = AP.first_missing_plan(st)
                    os.makedirs(SNAP, exist_ok=True)
                    save_json(os.path.join(SNAP, f"{st['clock']['date']}T{st['clock']['hour']:02d}.json"), st)
                    log("게임 시각:", clock_label(st["clock"]), "| 상태:", st["status"], "| 다음 필요 계획:", st["needs_plan"])
            if render_all and site_only:
                render_maps(st, True, True)
            import build_site
            build_site.build(st)
            save_state(st)
            if not no_pub:
                ok = publish()
                if ok:
                    st = load_state(); st["last_published_real"] = iso_kst(); save_state(st)
    except BlockingIOError:
        log("다른 tick 실행 중 → 종료")
        return 0
    except Exception:
        log("tick 오류:\n" + traceback.format_exc())
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
