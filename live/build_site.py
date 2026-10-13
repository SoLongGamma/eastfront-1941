#!/usr/bin/env python3
"""state.json → site/index.html (단일 페이지, 데이터 인라인) + site/state.json(공개 사본)."""
import html, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *  # noqa

E = html.escape
AX_FULL = {"north": ("북부축", "북부집단군", "북서전선"), "center": ("중부축", "중부집단군", "서부전선"),
           "south": ("남부축", "남부집단군", "남서전선")}


def fmt_real(s):
    if not s:
        return "—"
    return s[:16].replace("T", " ") + " KST"


def build(st=None):
    st = st or load_state()
    v = st["maps"].get("version", 0)
    clk = clock_label(st["clock"])
    status = ("명령 대기" if st.get("awaiting_orders") else "일시정지") if st.get("paused") else st.get("status", "진행")
    badges = []
    if st.get("mode") == "broadcast" and not st.get("paused"):
        badges.append('<span class="badge live">● 방송 중</span>')
    cls = {"진행": "ok", "판정 대기": "wait", "명령 대기": "wait", "일시정지": "pause"}.get(status, "ok")
    badges.append(f'<span class="badge {cls}">{E(status)}</span>')
    updated = fmt_real(st.get("last_tick_real") or st.get("seeded_real"))
    maps_t = st["maps"].get("tactical_game_time") or clk

    def img(kind, axis=None):
        f = f"maps/{kind}_{axis}.png" if axis else f"maps/{kind}.png"
        alt = (AX_FULL[axis][0] + " " if axis else "") + {"tactical": "전술도", "operational": "전역도", "theater": "전체 전선도"}[kind]
        return f'<figure><a href="{f}?v={v}" target="_blank"><img loading="lazy" src="{f}?v={v}" alt="{E(alt)}"></a><figcaption>{E(alt)}</figcaption></figure>'

    tact = "".join(img("tactical", a) for a in AXES)
    oper = "".join(img("operational", a) for a in AXES)
    thea = img("theater")

    dice_today = {r["axis"]: r for r in (st.get("day") or {}).get("dice", [])}
    cards = []
    for a in AXES:
        name, de, su = AX_FULL[a]
        o = st["orders"].get(a, {})
        L = st["losses"].get(a, {})
        d = dice_today.get(a)
        dice_html = f'<span class="dice" title="오늘 주사위 (독일 공세 기준 d20)">오늘 🎲 {d["roll"]} ({E(d.get("band", ""))})</span>' if d else ""
        ld = st.get("last_day") or {}
        summ = (ld.get("summary") or {}).get(a)
        summ_date = ld.get("date", "")
        cards.append(f"""
<section class="card">
 <h3>{name} {dice_html}</h3>
 <p class="sit">{E(st['situation'].get(a, ''))}</p>
 {f'<p class="summ">{E(summ_date[5:].replace("-", "."))} 판정 결과: {E(summ)}</p>' if summ else ''}
 <div class="orders">
  <div class="de"><h4>{de} 명령</h4><ul>{''.join(f'<li>{E(x)}</li>' for x in o.get('de', []))}</ul></div>
  <div class="su"><h4>{su} 명령</h4><ul>{''.join(f'<li>{E(x)}</li>' for x in o.get('su', []))}</ul></div>
 </div>
 <p class="loss">누적 손실 <b>게임 추정치</b>: <span class="de">{E(L.get('de_text', ''))}</span> · <span class="su">{E(L.get('su_text', ''))}</span></p>
</section>""")

    evs = list(reversed(st["events"][-40:]))
    ev_html = "".join(
        f'<li class="ev {E(e.get("kind", "event"))}"><span class="gt">{E(e["game_time"])}</span>'
        f'<span class="ax ax-{E(e["axis"])}">{E(AXIS_KO.get(e["axis"], e["axis"]))}</span>{E(e["text"])}</li>' for e in evs)

    page = f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>동부전선 1941 라이브 — {E(clk)}</title>
<meta name="description" content="대체역사 동부전선 1941 라이브 워게임 — 주사위와 AI 심판 판정으로 진행">
<noscript><meta http-equiv="refresh" content="60"></noscript>
<style>
:root{{--bg:#0d1110;--panel:#151b19;--line:#2a3430;--ink:#d8ddd2;--dim:#8d9a92;--amber:#e0b04a;--de:#7fa6e6;--su:#ef7d72;--ok:#5fbf6f}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 "Noto Sans KR","Malgun Gothic","Apple SD Gothic Neo",system-ui,sans-serif;
 background-image:repeating-linear-gradient(0deg,rgba(255,255,255,.015) 0 1px,transparent 1px 3px)}}
header{{padding:14px 16px 10px;border-bottom:2px solid var(--amber);background:linear-gradient(#141a17,#0d1110)}}
.top{{display:flex;flex-wrap:wrap;gap:8px;align-items:center;justify-content:space-between}}
h1{{margin:0;font-size:19px;letter-spacing:.04em}} h1 small{{color:var(--amber);font-weight:600;font-size:12px;margin-left:6px;letter-spacing:.15em}}
.clock{{font-family:ui-monospace,Consolas,monospace;font-size:26px;color:var(--amber);letter-spacing:.06em}}
.meta{{color:var(--dim);font-size:12.5px;margin-top:4px}}
.badge{{display:inline-block;padding:2px 9px;border-radius:3px;font-size:12px;font-weight:700;margin-left:6px;border:1px solid}}
.badge.live{{color:#fff;background:#b3121b;border-color:#ff5a5a;animation:blink 1.6s infinite}}
.badge.ok{{color:var(--ok);border-color:var(--ok)}} .badge.wait{{color:var(--amber);border-color:var(--amber)}} .badge.pause{{color:#aaa;border-color:#777}}
@keyframes blink{{50%{{opacity:.55}}}}
main{{max-width:1180px;margin:0 auto;padding:12px}}
.tabs input{{display:none}}
.tabs label{{display:inline-block;padding:8px 14px;margin-right:4px;border:1px solid var(--line);border-bottom:none;background:#111715;color:var(--dim);cursor:pointer;font-weight:700;border-radius:4px 4px 0 0}}
.tabs input:checked+label{{background:var(--panel);color:var(--amber);border-color:var(--amber)}}
.pane{{display:none;border:1px solid var(--line);background:var(--panel);padding:10px;border-radius:0 4px 4px 4px}}
#t1:checked~.p1,#t2:checked~.p2,#t3:checked~.p3{{display:block}}
.pane .note{{color:var(--dim);font-size:12.5px;margin:0 0 8px}}
figure{{margin:0 0 12px}} figure img{{width:100%;height:auto;display:block;border:1px solid #333;background:#ddd}}
figcaption{{font-size:12px;color:var(--dim);margin-top:3px}}
.grid{{max-width:1050px;margin:0 auto}} .p3 figure{{max-width:1050px;margin:0 auto}}
h2{{font-size:15px;color:var(--amber);letter-spacing:.1em;border-bottom:1px solid var(--line);padding-bottom:4px;margin:22px 0 10px}}
.cards{{display:grid;gap:10px}} @media(min-width:900px){{.cards{{grid-template-columns:repeat(3,1fr)}}}}
.card{{background:var(--panel);border:1px solid var(--line);border-left:3px solid var(--amber);padding:10px 12px;border-radius:3px}}
.card h3{{margin:0 0 6px;font-size:16px}} .dice{{float:right;font-size:12.5px;color:var(--amber);font-weight:600}}
.sit{{margin:0 0 6px;font-size:13.5px}} .summ{{margin:0 0 6px;font-size:13px;color:#e9d9a8}}
.orders h4{{margin:6px 0 2px;font-size:12.5px}} .orders .de h4{{color:var(--de)}} .orders .su h4{{color:var(--su)}}
.orders ul{{margin:0;padding-left:17px;font-size:12.5px;color:#c2c9c0}} .orders li{{margin:1px 0}}
.loss{{font-size:12px;color:var(--dim);margin:8px 0 0}} .loss .de{{color:var(--de)}} .loss .su{{color:var(--su)}}
ul.log{{list-style:none;margin:0;padding:0;font-size:13.5px}}
.log li{{padding:6px 4px;border-bottom:1px dashed var(--line)}}
.log .gt{{font-family:ui-monospace,Consolas,monospace;color:var(--amber);margin-right:8px;font-size:12px}}
.log .ax{{display:inline-block;min-width:34px;text-align:center;font-size:11px;padding:0 5px;margin-right:7px;border:1px solid #556;border-radius:2px;color:#cfd}}
.log .ax-north{{border-color:#4f7cc1}} .log .ax-center{{border-color:#b49b3b}} .log .ax-south{{border-color:#b45b4b}}
.log li.wait{{color:var(--amber)}} .log li.system,.log li.turn{{color:#aeb9b1}}
.about{{font-size:12.5px;color:var(--dim);background:#111614;border:1px solid var(--line);padding:10px 12px;border-radius:3px}}
footer{{text-align:center;color:#5f6b64;font-size:11.5px;padding:18px}}
</style></head>
<body>
<header><div class="top">
 <h1>동부전선 1941 <small>LIVE · 대체역사 워게임</small></h1>
 <div>{''.join(badges)}</div>
</div>
<div class="clock" id="clock">게임 시각 {E(clk)}</div>
<div class="meta">턴 {st.get('turn')} ({E(st.get('turn_range', ''))}) · 실시간 1분 = 게임 1일 · 4주마다 명령 라운드 · 마지막 갱신 {E(updated)}</div>
</header>
<main>
<div class="tabs">
 <input type="radio" name="t" id="t1" checked><label for="t1">전술</label>
 <input type="radio" name="t" id="t2"><label for="t2">전역</label>
 <input type="radio" name="t" id="t3"><label for="t3">전체</label>
 <div class="pane p1"><p class="note">축별 확대 전술도 — 1분(게임 1일)마다 갱신. 기준 {E(maps_t)}. 이미지를 누르면 원본 크기.</p><div class="grid">{tact}</div></div>
 <div class="pane p2"><p class="note">축별 전역도 — 1분(게임 1일)마다 갱신. 기준 {E(st['maps'].get('operational_game_time') or '—')}.</p><div class="grid">{oper}</div></div>
 <div class="pane p3"><p class="note">전체 전선도 — 1분(게임 1일)마다 갱신. 기준 {E(st['maps'].get('theater_game_time') or '—')}.</p>{thea}</div>
</div>

<h2>■ 최근 전황 로그</h2>
<ul class="log">{ev_html}</ul>

<h2>■ 축별 상황 · 현재 명령</h2>
<div class="cards">{''.join(cards)}</div>

<h2>■ 이 페이지는</h2>
<div class="about">
1941년 6월 22일 실제 전력·배치에서 출발하는 <b>대체역사 시뮬레이션</b>입니다. 독일 3개 집단군과 소련 3개 전선의 지휘 봇이 명령을 내고,
<b>심판</b>(현재 절차 판정 엔진)이 전력비·보급·지형·날씨·항공 등을 따져 개연성을 판단한 뒤 <b>주사위</b>(d20: 1~5 불리 · 6~15 기본 · 16~20 유리, 축마다)로 결과를 정합니다.
실제 역사는 기본 경향으로만 참고하므로 결과는 역사와 달라질 수 있습니다. 전선·부대 위치는 개략이며, 손실·전투력 수치는 모두 <b>게임 추정치</b>입니다.
현재 진행 방식: {('방송 모드' if st.get('mode') == 'broadcast' else '자동 진행')}. 페이지는 약 60초마다 자동 새로고침됩니다.
</div>
</main>
<footer>동부전선 1941 라이브 · 지도 데이터 Natural Earth · 생성 {E(fmt_real(iso_kst()))}</footer>
<script>
(function(){{
 var k='ef-tab';
 try{{var t=localStorage.getItem(k)||location.hash.slice(1); if(t&&document.getElementById(t)) document.getElementById(t).checked=true;}}catch(e){{}}
 document.querySelectorAll('.tabs input').forEach(function(r){{r.addEventListener('change',function(){{try{{localStorage.setItem(k,r.id)}}catch(e){{}}; history.replaceState(null,'','#'+r.id);}})}});
 setTimeout(function(){{location.reload()}},60000);
}})();
</script>
</body></html>
"""
    os.makedirs(SITE, exist_ok=True)
    tmp = os.path.join(SITE, ".index.tmp")
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(page)
    os.replace(tmp, os.path.join(SITE, "index.html"))
    pub = {k: st[k] for k in ("clock", "turn", "paused", "mode", "status", "fronts", "pockets", "units", "arrows",
                              "orders", "losses", "situation", "events", "maps") if k in st}
    pub["clock_label"] = clk
    pub["last_tick_real"] = st.get("last_tick_real")
    save_json(os.path.join(SITE, "state.json"), pub)
    return os.path.join(SITE, "index.html")


if __name__ == "__main__":
    print(build())
