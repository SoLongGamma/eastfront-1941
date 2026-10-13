#!/usr/bin/env python3
"""동부전선 상황도 생성기 (대체역사 워게임).

사용법:  /workspace/eastfront/.venv/bin/python /workspace/eastfront/draw_map.py
매 턴마다 아래 DATA BLOCK(전선·포위망·화살표·라벨)만 수정하면 된다.
좌표는 모두 (경도, 위도) 순서. 지도 데이터: Natural Earth (ne/ 폴더, 없으면 자동 다운로드).
"""
import json, math, os, subprocess

# =====================================================================
# DATA BLOCK — 턴마다 여기만 고치면 됨
# =====================================================================
TITLE = "동부전선 상황도 — 1941.7.5 (2주차 종료 / 3주차 명령)"
SUBTITLE = "전선: 7.5 기준 · 화살표: 3주차(7.6–7.12) 수신 명령에 따른 계획 기동"
FOOTNOTE = "대체역사 워게임 판정 기준, 전선은 개략도"
OUTFILE = "/workspace/eastfront/map_1941-07-05.png"
EXTENT = (18.5, 37.5, 45.8, 60.3)          # lon_min, lon_max, lat_min, lat_max
FIG_PX = (1600, 1850)
DPI = 150

# 도시: (이름, 경도, 위도, dx pt, dy pt, ha, 주요도시 여부)
CITIES = [
    ("레닌그라드", 30.31, 59.94, 7, -2, "left", True),
    ("탈린", 24.75, 59.44, 0, 7, "center", True),
    ("타르투", 26.72, 58.38, 6, 3, "left", False),
    ("파르누", 24.50, 58.39, -6, 3, "right", False),
    ("리가", 24.11, 56.95, -7, 0, "right", True),
    ("다우가프필스\n(드빈스크)", 26.54, 55.87, 0, -9, "center", False),
    ("레제크네", 27.33, 56.51, -6, -2, "right", False),
    ("오스트로프", 28.35, 57.34, 7, -4, "left", False),
    ("프스코프", 28.33, 57.82, 7, 2, "left", False),
    ("오포치카", 28.65, 56.71, 6, -5, "left", False),
    ("노보르제프", 29.33, 57.03, 6, 2, "left", False),
    ("폴로츠크", 28.79, 55.49, 6, 3, "left", False),
    ("비텝스크", 30.20, 55.19, 6, 3, "left", False),
    ("레펠", 28.70, 54.88, 2, -10, "left", False),
    ("민스크", 27.56, 53.90, 0, 7, "center", True),
    ("보리소프", 28.50, 54.23, 6, 2, "left", False),
    ("보브루이스크", 29.22, 53.14, 6, -1, "left", False),
    ("모길료프", 30.34, 53.91, 6, 0, "left", False),
    ("스몰렌스크", 32.04, 54.78, 6, 0, "left", True),
    ("비아위스토크", 23.16, 53.13, -6, 4, "right", False),
    ("브레스트", 23.69, 52.10, -9, 2, "right", False),
    ("노보그루도크", 25.83, 53.60, 0, 7, "center", False),
    ("로브노", 26.25, 50.62, -6, 2, "right", False),
    ("노보그라드-볼린스키", 27.62, 50.59, 0, 9, "center", False),
    ("지토미르", 28.66, 50.25, 6, -4, "left", False),
    ("코로스텐", 28.64, 50.95, 6, -3, "left", False),
    ("키예프", 30.52, 50.45, 7, 0, "left", True),
    ("리보프", 24.03, 49.84, 0, -10, "center", True),
    ("모길료프-포돌스키", 27.80, 48.45, 7, 2, "left", False),
    ("오데사", 30.73, 46.48, 7, 0, "left", True),
]

# 전선 (북→남 연속). style: solid=확정 전선, loose=불명확·접촉 단절
FRONT = [
    dict(style="solid", pts=[(24.15, 58.10), (25.0, 58.02), (25.8, 58.00), (26.4, 58.08),
                             (26.95, 58.10), (27.50, 57.98)]),
    dict(style="loose", pts=[(27.50, 57.98), (27.62, 57.70), (27.85, 57.45), (28.02, 57.28)]),
    dict(style="solid", pts=[(28.02, 57.28), (28.08, 57.05), (28.15, 56.75), (28.10, 56.45),
                             (28.05, 56.15), (28.15, 55.85), (28.30, 55.60), (28.35, 55.35),
                             (28.30, 55.10), (28.25, 54.85), (28.15, 54.55), (28.32, 54.25),
                             (28.55, 53.90), (28.80, 53.55), (28.95, 53.20), (28.85, 52.85)]),
    dict(style="loose", pts=[(28.85, 52.85), (28.30, 52.45), (27.60, 52.00), (27.00, 51.60),
                             (26.75, 51.25)]),
    dict(style="solid", pts=[(26.75, 51.25), (27.00, 50.95), (27.35, 50.75), (27.45, 50.55),
                             (27.35, 50.40), (26.90, 50.32), (26.40, 50.28), (25.80, 50.18),
                             (25.15, 50.12), (24.50, 50.18), (23.90, 50.12), (23.45, 49.92),
                             (23.15, 49.65), (22.85, 49.30), (22.70, 49.05), (23.30, 48.75),
                             (24.00, 48.35), (24.70, 47.95), (25.40, 47.90), (26.00, 47.98),
                             (26.60, 48.15), (26.95, 48.20), (27.25, 47.95), (27.48, 47.85),
                             (27.38, 47.62), (27.62, 47.42), (27.88, 47.30), (27.86, 47.08),
                             (28.05, 46.85), (28.20, 46.50), (28.15, 46.00), (28.20, 45.50)]),
]
# 독일 통제 다각형을 닫는 점들 (전선 남쪽 끝 → 서쪽 바깥 → 리가만 → 전선 북쪽 시작)
GERMAN_CLOSURE = [(18.0, 45.5), (18.0, 57.78), (21.5, 57.78), (22.3, 57.82), (23.5, 57.86)]

# 소련군 포위망 (타원, 해칭)
POCKETS = [
    dict(lon=23.68, lat=52.09, rx=0.17, ry=0.10, label="요새 항전 중",
         lx=23.05, ly=51.88, ha="center"),
    dict(lon=24.15, lat=53.20, rx=0.55, ry=0.27, label="비아위스토크 내부 포위망\n(축소 중)",
         lx=24.15, ly=52.62, ha="center"),
    dict(lon=26.95, lat=53.75, rx=0.75, ry=0.33, label="민스크 포위망\n(13군 등 · 누수 큼)",
         lx=25.75, ly=54.22, ha="center"),
]

# 화살표. side: de=독일(파랑 점선), su=소련(빨강 점선), esc=탈출로(빨강 점점선)
ARROWS = [
    dict(side="de", pts=[(27.55, 56.95), (28.22, 57.28), (28.30, 57.72)], label="4기갑집단(41군단)\n→ 프스코프", lx=26.45, ly=57.02, ha="center"),
    dict(side="de", pts=[(24.95, 57.62), (24.62, 58.25)], label=None),
    dict(side="de", pts=[(25.85, 57.62), (26.45, 58.25)], label="18군 → 에스토니아 남부", lx=25.35, ly=57.5, ha="center"),
    dict(side="de", pts=[(27.30, 56.25), (27.85, 56.52), (28.45, 56.62)], label="16군 → 오포치카", lx=27.05, ly=56.12, ha="center"),
    dict(side="de", pts=[(27.25, 54.47), (28.22, 54.28)], label="3기갑집단\n(보리소프 맞은편 집결)", lx=27.35, ly=54.7, ha="center"),
    dict(side="de", pts=[(27.95, 53.36), (28.85, 53.20)], label="2기갑집단\n(보브루이스크 맞은편)", lx=27.85, ly=53.2, ha="right"),
    dict(side="de", pts=[(26.45, 50.68), (27.20, 50.58), (27.75, 50.48), (28.50, 50.28)], label="1기갑집단\n→ 지토미르", lx=25.75, ly=50.95, ha="center"),
    dict(side="de", pts=[(27.15, 47.70), (27.55, 48.02), (27.72, 48.36)], label="11군·루마니아군\n→ 모길료프-포돌스키", lx=26.4, ly=47.45, ha="center"),
    dict(side="su", pts=[(30.05, 55.08), (29.45, 54.98), (28.85, 54.90)], label="20군 5·7기계화\n→ 레펠 반격", lx=30.15, ly=54.7, ha="left"),
    dict(side="su", pts=[(28.85, 57.62), (28.45, 57.50), (28.10, 57.36)], label="1기계화군단", lx=29.0, ly=57.62, ha="left"),
    dict(side="su", pts=[(29.25, 56.98), (28.70, 56.92), (28.15, 56.92)], label="27군·21기계화", lx=29.0, ly=56.82, ha="left"),
    dict(side="su", pts=[(28.45, 49.98), (28.0, 50.08), (27.60, 50.30)], label="24기계화", lx=28.5, ly=49.86, ha="left"),
    dict(side="su", pts=[(28.45, 51.25), (27.85, 51.16), (27.32, 51.0)], label="5군 삼림 기습", lx=28.5, ly=51.30, ha="left"),
    dict(side="su", pts=[(28.75, 48.15), (28.15, 48.05), (27.62, 47.95)], label="16기계화(예비)", lx=28.8, ly=48.0, ha="left"),
    dict(side="esc", pts=[(25.95, 53.35), (26.40, 52.85), (27.60, 52.60), (28.75, 52.72)], label="3·10군 탈출로\n(중장비 유기)", lx=26.85, ly=52.4, ha="center"),
]

# 요새지대 (스탈린선 등)
FORTS = [
    [(28.22, 57.95), (28.27, 57.60), (28.40, 57.25), (28.45, 57.05)],
    [(28.52, 56.85), (28.45, 56.50), (28.40, 56.15)],
    [(28.55, 55.75), (28.62, 55.45), (28.75, 55.25)],
    [(27.72, 51.00), (27.66, 50.75), (27.70, 50.40), (27.82, 50.15)],
    [(27.40, 48.62), (27.80, 48.40), (28.25, 48.27)],
]

# 부대 라벨: (텍스트, 경도, 위도, 측: de/su, 크기: big/small)
UNITS = [
    ("북부집단군", 24.6, 55.85, "de", "big"),
    ("중부집단군", 24.8, 52.0, "de", "big"),
    ("남부집단군", 24.5, 51.25, "de", "big"),
    ("북서전선", 31.3, 58.45, "su", "big"),
    ("서부전선", 31.6, 53.35, "su", "big"),
    ("남서전선", 30.9, 49.35, "su", "big"),
    ("8군", 25.7, 58.65, "su", "small"),
    ("11군 잔존·41소총군단", 29.65, 57.99, "su", "small"),
    ("6·26군 (리보프 돌출부)", 24.75, 49.45, "su", "small"),
    ("12군", 26.4, 48.55, "su", "small"),
    ("17군", 22.55, 50.35, "de", "small"),
    ("6군", 25.0, 50.42, "de", "small"),
    ("4·9군", 24.6, 53.75, "de", "small"),
]

# 하천 라벨: (텍스트, 경도, 위도, 회전각)
RIVER_LABELS = [
    ("다우가바(서드비나)강", 25.35, 56.48, -33),
    ("벨리카야강", 29.25, 56.30, 0),
    ("베레지나강", 29.25, 53.72, -62),
    ("드네프르강", 30.62, 52.75, -82),
    ("슬루치강", 27.20, 49.85, 70),
    ("드네스트르강", 29.05, 47.40, -50),
    ("프루트강", 28.45, 46.25, -85),
    ("네만강", 23.6, 54.45, 0),
    ("부크강", 23.42, 51.45, 85),
    ("프리퍄트강", 26.6, 51.95, 0),
]
KEY_RIVERS = {"Daugava", "Velikaya", "Byarezina", "Berezina", "Dnepr", "Dnepre", "Dnipro",
              "Sluch", "Dniester", "Prut", "Neman", "Bug", "Zakhidnyy Buh", "Pripyat", "Prypyat"}
AREA_LABELS = [("프리퍄트 습지", 26.0, 51.62), ("발트해", 20.3, 56.6), ("흑해", 32.0, 46.1),
               ("리가만", 23.3, 57.55), ("페이푸스호", 27.55, 58.72)]

# 1941.6.22 국경 (개략)
BORDER_1941 = [(21.07, 55.95), (21.55, 55.83), (21.9, 55.55), (22.1, 55.10), (22.6, 55.05),
               (22.8, 54.80), (23.45, 54.40), (23.2, 54.10), (22.75, 53.85), (22.2, 53.55),
               (21.9, 53.20), (22.0, 52.65), (22.9, 52.30), (23.6, 52.10), (23.62, 51.60),
               (23.9, 51.10), (24.1, 50.60), (24.0, 50.40), (23.4, 50.20), (22.8, 49.95),
               (22.77, 49.78), (22.5, 49.50), (22.6, 49.10), (23.1, 48.80), (24.5, 48.30),
               (25.3, 47.85), (26.0, 47.95), (26.6, 48.15), (26.95, 48.22), (27.27, 47.86),
               (27.80, 47.21), (28.25, 46.48), (28.2, 45.9), (28.2, 45.5)]

# =====================================================================
# 이하 렌더링 코드 (보통 수정 불필요)
# =====================================================================
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager, patheffects as pe
from matplotlib.patches import Ellipse, Patch, PathPatch
from matplotlib.lines import Line2D
from matplotlib.path import Path
from shapely.geometry import shape, box, Polygon, LineString, MultiPolygon
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
NE = os.path.join(HERE, "ne")
NE_FILES = ["ne_50m_land", "ne_50m_admin_0_countries", "ne_10m_lakes",
            "ne_10m_rivers_lake_centerlines", "ne_10m_rivers_europe"]
FONT_DIR = "/usr/share/fonts/truetype/sand-box/google/Nanum Gothic/"

C_SEA, C_LAND = "#d4e6f1", "#f4f0e6"
C_DE, C_SU = "#8fa6c1", "#e7a29b"
C_DE_ARROW, C_SU_ARROW = "#123f8c", "#b3121b"
C_FRONT = "#7a0000"
C_RIVER = "#3d7fb5"


def ensure_data():
    os.makedirs(NE, exist_ok=True)
    for f in NE_FILES:
        p = os.path.join(NE, f + ".geojson")
        if not os.path.exists(p):
            url = f"https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/{f}.geojson"
            subprocess.run(["curl", "-sfL", "-o", p, url], check=True)


def load(name, bbox):
    feats = []
    with open(os.path.join(NE, name + ".geojson")) as fh:
        for f in json.load(fh)["features"]:
            try:
                g = shape(f["geometry"])
            except Exception:
                continue
            if g.is_empty or not g.intersects(bbox):
                continue
            feats.append((f["properties"], g.intersection(bbox)))
    return feats


def polys(g):
    if g.is_empty:
        return []
    if isinstance(g, Polygon):
        return [g]
    if isinstance(g, MultiPolygon):
        return list(g.geoms)
    return [p for p in getattr(g, "geoms", []) if isinstance(p, Polygon)]


def lines(g):
    if g.is_empty:
        return []
    if isinstance(g, LineString):
        return [g]
    out = []
    for p in getattr(g, "geoms", []):
        out += lines(p)
    return out


def fill(ax, g, **kw):
    for p in polys(g):
        verts, codes = [], []
        for ring in [p.exterior] + list(p.interiors):
            cs = list(ring.coords)
            verts += cs
            codes += [Path.MOVETO] + [Path.LINETO] * (len(cs) - 2) + [Path.CLOSEPOLY]
        ax.add_patch(PathPatch(Path(verts, codes), **kw))


def smooth(pts, n=3):
    if len(pts) < 3:
        return pts
    for _ in range(n):
        new = [pts[0]]
        for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
            new += [(0.75 * x0 + 0.25 * x1, 0.75 * y0 + 0.25 * y1),
                    (0.25 * x0 + 0.75 * x1, 0.25 * y0 + 0.75 * y1)]
        new.append(pts[-1])
        pts = new
    return pts


def halo(w=2.5, c="white"):
    return [pe.withStroke(linewidth=w, foreground=c)]


def main():
    ensure_data()
    for fn in os.listdir(FONT_DIR):
        if fn.endswith(".ttf"):
            font_manager.fontManager.addfont(os.path.join(FONT_DIR, fn))
    plt.rcParams["font.family"] = "NanumGothic"
    plt.rcParams["axes.unicode_minus"] = False

    x0, x1, y0, y1 = EXTENT
    bbox = box(x0 - 1, y0 - 1, x1 + 1, y1 + 1)
    land = unary_union([g for _, g in load("ne_50m_land", bbox)])
    countries = load("ne_50m_admin_0_countries", bbox)
    finland = unary_union([g for p, g in countries if p.get("ADMIN") in ("Finland", "Sweden")])
    lakes = [g for p, g in load("ne_10m_lakes", bbox) if g.area > 0.004]
    rivers = load("ne_10m_rivers_lake_centerlines", bbox) + load("ne_10m_rivers_europe", bbox)

    front_pts = []
    for seg in FRONT:
        for p in seg["pts"]:
            if not front_pts or front_pts[-1] != p:
                front_pts.append(p)
    de_poly = Polygon(front_pts + GERMAN_CLOSURE).buffer(0)
    de_area = land.intersection(de_poly).difference(finland)
    su_area = land.intersection(bbox).difference(de_poly).difference(finland)

    W, H = FIG_PX[0] / DPI, FIG_PX[1] / DPI
    fig = plt.figure(figsize=(W, H), dpi=DPI)
    aspect = 1 / math.cos(math.radians((y0 + y1) / 2))
    map_h_in = H - 0.95 - 1.55
    map_w_in = map_h_in / ((y1 - y0) * aspect) * (x1 - x0)
    ax = fig.add_axes([(W - map_w_in) / 2 / W, 1.55 / H, map_w_in / W, map_h_in / H])
    ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_aspect(aspect)
    ax.set_facecolor(C_SEA)

    fill(ax, land, facecolor=C_LAND, edgecolor="#6d6d6d", lw=0.6, zorder=1)
    fill(ax, de_area, facecolor=C_DE, edgecolor="none", alpha=0.75, zorder=2)
    fill(ax, su_area, facecolor=C_SU, edgecolor="none", alpha=0.6, zorder=2)
    fill(ax, land, facecolor="none", edgecolor="#555555", lw=0.6, zorder=3)
    for g in lakes:
        fill(ax, g, facecolor=C_SEA, edgecolor=C_RIVER, lw=0.4, zorder=3)
    for props, g in rivers:
        name = props.get("name") or ""
        key = name in KEY_RIVERS
        for ln in lines(g):
            xs, ys = ln.xy
            ax.plot(xs, ys, color=C_RIVER, lw=1.25 if key else 0.5, alpha=0.95 if key else 0.6,
                    zorder=4, solid_capstyle="round")

    # grid
    ax.set_xticks(range(math.ceil(x0), int(x1) + 1, 2))
    ax.set_yticks(range(math.ceil(y0), int(y1) + 1, 2))
    ax.set_xticklabels([f"{v}°E" for v in ax.get_xticks().astype(int)], fontsize=8)
    ax.set_yticklabels([f"{v}°N" for v in ax.get_yticks().astype(int)], fontsize=8)
    ax.grid(color="#999999", lw=0.3, ls=":", zorder=4.5)
    ax.tick_params(length=2, top=True, right=True, labeltop=False, labelright=False)

    bx, by = zip(*BORDER_1941)
    ax.plot(bx, by, color="#444444", lw=1.0, ls=(0, (1, 1.5)), zorder=5)
    for f in FORTS:
        fx, fy = zip(*f)
        ax.plot(fx, fy, color="#6b4423", lw=6, alpha=0.4, solid_capstyle="round", zorder=5)

    for name, lo, la, rot in RIVER_LABELS:
        ax.text(lo, la, name, fontsize=7, color="#1b5a8c", style="italic", rotation=rot,
                ha="center", va="center", zorder=6, path_effects=halo(2, C_LAND))
    for name, lo, la in AREA_LABELS:
        ax.text(lo, la, name, fontsize=9 if name in ("발트해", "흑해") else 7.5, color="#4a6f8a",
                style="italic", ha="center", va="center", zorder=6, path_effects=halo(2, "#eef5fa"))

    # front
    for seg in FRONT:
        fx, fy = zip(*seg["pts"])
        if seg["style"] == "solid":
            ax.plot(fx, fy, color=C_FRONT, lw=2.8, zorder=8, solid_joinstyle="round",
                    path_effects=[pe.withStroke(linewidth=4.4, foreground="black")])
        else:
            ax.plot(fx, fy, color=C_FRONT, lw=2.2, ls=(0, (4, 2.5)), zorder=8)

    for pk in POCKETS:
        e = Ellipse((pk["lon"], pk["lat"]), 2 * pk["rx"], 2 * pk["ry"], facecolor=(0.85, 0.25, 0.25, 0.35),
                    edgecolor="#8b0000", hatch="////", lw=1.4, zorder=9)
        ax.add_patch(e)
        ax.text(pk["lx"], pk["ly"], pk["label"], fontsize=7.5, color="#7a0000", ha=pk["ha"],
                va="center", zorder=12, fontweight="bold", path_effects=halo(2.5))

    for a in ARROWS:
        col = C_DE_ARROW if a["side"] == "de" else C_SU_ARROW
        ls = (0, (1.2, 1.6)) if a["side"] == "esc" else (0, (3.2, 1.8))
        lw = 1.8 if a["side"] == "esc" else 2.6
        pts = smooth(a["pts"])
        xs, ys = zip(*pts)
        ax.plot(xs[:-1], ys[:-1], color=col, lw=lw, ls=ls, zorder=10, dash_capstyle="butt",
                path_effects=[pe.withStroke(linewidth=lw + 1.6, foreground="white")])
        (ax_, ay_), (bx_, by_) = a["pts"][-2], a["pts"][-1]
        L = math.hypot((bx_ - ax_) / aspect, by_ - ay_) or 1
        back = 0.08
        tail = (bx_ - (bx_ - ax_) / L * back, by_ - (by_ - ay_) / L * back)
        ax.annotate("", xy=(bx_, by_), xytext=tail, zorder=11,
                    arrowprops=dict(arrowstyle="-|>,head_length=1.0,head_width=0.55", color=col, lw=0,
                                    mutation_scale=9 if a["side"] != "esc" else 7,
                                    shrinkA=0, shrinkB=0,
                                    path_effects=[pe.withStroke(linewidth=1.5, foreground="white")]))
        if a.get("label"):
            ax.text(a["lx"], a["ly"], a["label"], fontsize=7.5, color=col, ha=a["ha"], va="center",
                    zorder=12, fontweight="bold", path_effects=halo(2.5))

    for name, lo, la, dx, dy, ha, major in CITIES:
        ax.plot(lo, la, marker="s" if major else "o", ms=5.5 if major else 4, mfc="black", mec="white",
                mew=0.8, zorder=13)
        ax.annotate(name, (lo, la), xytext=(dx, dy), textcoords="offset points", ha=ha, va="center",
                    fontsize=8.5 if major else 7.5, fontweight="bold" if major else "normal",
                    zorder=14, path_effects=halo(2.6), linespacing=0.95)

    for text, lo, la, side, size in UNITS:
        col = C_DE_ARROW if side == "de" else C_SU_ARROW
        big = size == "big"
        ax.text(lo, la, text, fontsize=10 if big else 7.5, fontweight="heavy" if big else "bold",
                color=col, ha="center", va="center", zorder=12, alpha=0.95,
                bbox=dict(boxstyle="round,pad=0.25", fc="white", ec=col, lw=0.8, alpha=0.8) if big else None,
                path_effects=None if big else halo(2.5))

    # scale bar (200 km at 47N)
    lat_s = 46.25; lon_s = 34.3
    dlon = 200 / (111.32 * math.cos(math.radians(lat_s)))
    ax.plot([lon_s, lon_s + dlon], [lat_s, lat_s], color="black", lw=3, zorder=12, solid_capstyle="butt")
    ax.plot([lon_s, lon_s + dlon / 2], [lat_s, lat_s], color="white", lw=1.6, zorder=12, solid_capstyle="butt")
    ax.text(lon_s + dlon / 2, lat_s + 0.15, "200 km", fontsize=7.5, ha="center", zorder=12, path_effects=halo())

    fig.text(0.5, 1 - 0.38 / H, TITLE, ha="center", va="center", fontsize=16, fontweight="heavy")
    fig.text(0.5, 1 - 0.70 / H, SUBTITLE, ha="center", va="center", fontsize=9, color="#333333")

    handles = [
        Line2D([], [], color=C_FRONT, lw=2.8, path_effects=[pe.withStroke(linewidth=4.4, foreground="black")],
               label="전선 (7.5 기준, 개략)"),
        Line2D([], [], color=C_FRONT, lw=2.2, ls=(0, (4, 2.5)), label="전선 불명확 · 접촉 단절 구간"),
        Patch(facecolor=C_DE, alpha=0.75, label="독일·추축 통제 지역"),
        Patch(facecolor=C_SU, alpha=0.6, label="소련 통제 지역"),
        Patch(facecolor=(0.85, 0.25, 0.25, 0.35), edgecolor="#8b0000", hatch="////", label="소련군 포위망 / 고립 거점"),
        Line2D([], [], color="#6b4423", lw=6, alpha=0.4, label="요새지대 (스탈린선 등)"),
        Line2D([], [], color=C_DE_ARROW, lw=2.6, ls=(0, (4.5, 2.5)), marker=">", markevery=[-1], ms=6,
               label="독일군 3주차 계획 공세"),
        Line2D([], [], color=C_SU_ARROW, lw=2.6, ls=(0, (4.5, 2.5)), marker=">", markevery=[-1], ms=6,
               label="소련군 3주차 계획 반격"),
        Line2D([], [], color=C_SU_ARROW, lw=1.8, ls=(0, (1.2, 1.6)), marker=">", markevery=[-1], ms=5,
               label="소련 잔존군 탈출로"),
        Line2D([], [], color="#444444", lw=1.0, ls=(0, (1, 1.5)), label="1941.6.22 국경 (개략)"),
        Line2D([], [], color=C_RIVER, lw=1.25, label="주요 하천"),
        Line2D([], [], color="black", marker="s", ls="none", ms=5.5, mec="white", label="주요 도시 / 도시"),
    ]
    fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, 0.42 / H), ncol=3,
               fontsize=8.5, frameon=True, framealpha=1, edgecolor="#888888", handlelength=3.2,
               columnspacing=1.8, borderpad=0.7)
    fig.text(0.5, 0.18 / H, FOOTNOTE + "  ·  지도: Natural Earth (해안·하천), 국경·전선은 수작업 근사",
             ha="center", va="center", fontsize=8, color="#444444")
    fig.savefig(OUTFILE, dpi=DPI)
    print("saved", OUTFILE)


if __name__ == "__main__":
    main()
