#!/usr/bin/env python3
"""state.json → 지도 PNG (전술/전역/전체). draw_map.py 스타일을 재사용·리팩터.
사용: .venv/bin/python live/render.py [tactical|operational|theater|all] [north|center|south]
"""
import math, os, pickle, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *  # noqa

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager, patheffects as pe
from matplotlib.patches import Ellipse, Patch, PathPatch
from matplotlib.lines import Line2D
from matplotlib.path import Path
from shapely.geometry import shape, box, Polygon, LineString, MultiPolygon
from shapely.ops import unary_union

NE = os.path.join(ROOT, "ne")
FONT_DIR = "/usr/share/fonts/truetype/sand-box/google/Nanum Gothic/"
THEATER_EXTENT = (18.5, 37.5, 45.8, 60.3)

C_SEA, C_LAND = "#d4e6f1", "#f4f0e6"
C_DE, C_SU = "#8fa6c1", "#e7a29b"
C_DE_ARROW, C_SU_ARROW = "#123f8c", "#b3121b"
C_FRONT = "#7a0000"
C_RIVER = "#3d7fb5"

# 도시: (이름, 경도, 위도, dx pt, dy pt, ha, 주요도시, 최소 표시 등급 0=전체도 1=전역 2=전술)
CITIES = [
    ("레닌그라드", 30.31, 59.94, 7, -2, "left", True, 0),
    ("탈린", 24.75, 59.44, 0, 7, "center", True, 0),
    ("나르바", 28.19, 59.38, 6, 2, "left", False, 1),
    ("타르투", 26.72, 58.38, 6, 3, "left", False, 0),
    ("파르누", 24.50, 58.39, -6, 3, "right", False, 0),
    ("발미에라", 25.43, 57.54, 6, 3, "left", False, 2),
    ("리가", 24.11, 56.95, -7, 0, "right", True, 0),
    ("다우가프필스\n(드빈스크)", 26.54, 55.87, 0, -9, "center", False, 0),
    ("레제크네", 27.33, 56.51, -6, -2, "right", False, 0),
    ("오스트로프", 28.35, 57.34, 7, -4, "left", False, 0),
    ("프스코프", 28.33, 57.82, 7, 2, "left", False, 0),
    ("오포치카", 28.65, 56.71, 6, -5, "left", False, 0),
    ("노보르제프", 29.33, 57.03, 6, 2, "left", False, 0),
    ("세베시", 28.49, 56.29, 6, -2, "left", False, 2),
    ("벨리키예루키", 30.53, 56.34, 6, 0, "left", False, 1),
    ("폴로츠크", 28.79, 55.49, 6, 3, "left", False, 0),
    ("비텝스크", 30.20, 55.19, 6, 3, "left", False, 0),
    ("레펠", 28.70, 54.88, 2, -10, "left", False, 0),
    ("민스크", 27.56, 53.90, 0, 7, "center", True, 0),
    ("보리소프", 28.50, 54.23, 6, 2, "left", False, 0),
    ("오르샤", 30.42, 54.51, 6, 0, "left", False, 1),
    ("보브루이스크", 29.22, 53.14, 6, -1, "left", False, 0),
    ("모길료프", 30.34, 53.91, 6, 0, "left", False, 0),
    ("스몰렌스크", 32.04, 54.78, 6, 0, "left", True, 0),
    ("스톨프치", 26.73, 53.48, 0, -9, "center", False, 2),
    ("슬루츠크", 27.56, 53.03, 6, -3, "left", False, 2),
    ("비아위스토크", 23.16, 53.13, -6, 4, "right", False, 0),
    ("브레스트", 23.69, 52.10, -9, 2, "right", False, 0),
    ("노보그루도크", 25.83, 53.60, 0, 7, "center", False, 0),
    ("루츠크", 25.33, 50.75, -6, 2, "right", False, 1),
    ("두브노", 25.73, 50.40, 0, -9, "center", False, 2),
    ("로브노", 26.25, 50.62, -6, 2, "right", False, 0),
    ("노보그라드-볼린스키", 27.62, 50.59, 5, -9, "left", False, 0),
    ("지토미르", 28.66, 50.25, 6, -4, "left", False, 0),
    ("코로스텐", 28.64, 50.95, 6, -3, "left", False, 0),
    ("올렙스크", 27.66, 51.22, 0, 8, "center", False, 2),
    ("베르디체프", 28.58, 49.89, 6, -3, "left", False, 1),
    ("키예프", 30.52, 50.45, 7, 0, "left", True, 0),
    ("리보프", 24.03, 49.84, 0, -10, "center", True, 0),
    ("빈니차", 28.47, 49.23, 6, 0, "left", False, 1),
    ("모길료프-포돌스키", 27.80, 48.45, 7, 2, "left", False, 0),
    ("키시너우", 28.86, 47.01, 6, 0, "left", False, 1),
    ("오데사", 30.73, 46.48, 7, 0, "left", True, 0),
    ("카자틴", 28.83, 49.72, 6, 3, "left", False, 2),
    ("쥐메린카", 28.11, 49.04, -6, 0, "right", False, 1),
    ("우만", 30.22, 48.75, 6, 0, "left", False, 0),
    ("키로보그라드", 32.26, 48.51, 6, 0, "left", False, 0),
    ("크레멘추크", 33.42, 49.07, 6, 2, "left", False, 0),
    ("체르카시", 32.06, 49.44, 6, 2, "left", False, 1),
    ("드네프로페트롭스크", 35.04, 48.46, 6, 3, "left", True, 0),
    ("자포로지예", 35.14, 47.84, 6, -3, "left", False, 0),
    ("니콜라예프", 31.99, 46.97, 6, 0, "left", False, 0),
    ("하르코프", 36.23, 49.99, 6, 0, "left", True, 0),
    ("스탈리노", 37.80, 48.00, 6, 0, "left", False, 0),
    ("마리우폴", 37.55, 47.10, 6, -3, "left", False, 0),
    ("고멜", 30.98, 52.43, 6, 0, "left", False, 0),
    ("브랸스크", 34.37, 53.25, 6, 0, "left", False, 0),
]
RIVER_LABELS = [
    ("다우가바(서드비나)강", 25.35, 56.48, -33), ("벨리카야강", 29.25, 56.30, 0),
    ("베레지나강", 29.25, 53.72, -62), ("드네프르강", 30.62, 52.75, -82),
    ("슬루치강", 27.20, 49.85, 70), ("드네스트르강", 29.05, 47.40, -50),
    ("프루트강", 28.45, 46.25, -85), ("네만강", 23.6, 54.45, 0),
    ("부크강", 23.42, 51.45, 85), ("프리퍄트강", 26.6, 51.95, 0),
]
KEY_RIVERS = {"Daugava", "Velikaya", "Byarezina", "Berezina", "Dnepr", "Dnepre", "Dnipro",
              "Sluch", "Dniester", "Prut", "Neman", "Bug", "Zakhidnyy Buh", "Pripyat", "Prypyat"}
AREA_LABELS = [("프리퍄트 습지", 26.0, 51.62), ("발트해", 20.3, 56.6), ("흑해", 32.0, 46.1),
               ("리가만", 23.3, 57.55), ("페이푸스호", 27.55, 58.72)]
BORDER_1941 = [(21.07, 55.95), (21.55, 55.83), (21.9, 55.55), (22.1, 55.10), (22.6, 55.05),
               (22.8, 54.80), (23.45, 54.40), (23.2, 54.10), (22.75, 53.85), (22.2, 53.55),
               (21.9, 53.20), (22.0, 52.65), (22.9, 52.30), (23.6, 52.10), (23.62, 51.60),
               (23.9, 51.10), (24.1, 50.60), (24.0, 50.40), (23.4, 50.20), (22.8, 49.95),
               (22.77, 49.78), (22.5, 49.50), (22.6, 49.10), (23.1, 48.80), (24.5, 48.30),
               (25.3, 47.85), (26.0, 47.95), (26.6, 48.15), (26.95, 48.22), (27.27, 47.86),
               (27.80, 47.21), (28.25, 46.48), (28.2, 45.9), (28.2, 45.5)]

# ---------------------------------------------------------------- geodata (cached)
_GEO = None


def _load(name, bbox):
    feats = []
    with open(os.path.join(NE, name + ".geojson")) as fh:
        for f in json.load(fh)["features"]:
            try:
                g = shape(f["geometry"])
            except Exception:
                continue
            if g.is_empty or not g.intersects(bbox):
                continue
            feats.append((f["properties"].get("name") or f["properties"].get("ADMIN") or "", g.intersection(bbox)))
    return feats


def geo():
    global _GEO
    if _GEO is not None:
        return _GEO
    os.makedirs(CACHE, exist_ok=True)
    pk = os.path.join(CACHE, "geo_v1.pkl")
    if os.path.exists(pk):
        with open(pk, "rb") as fh:
            _GEO = pickle.load(fh)
        return _GEO
    x0, x1, y0, y1 = THEATER_EXTENT
    bbox = box(x0 - 2, y0 - 2, x1 + 2, y1 + 2)
    land = unary_union([g for _, g in _load("ne_50m_land", bbox)])
    countries = _load("ne_50m_admin_0_countries", bbox)
    finland = unary_union([g for n, g in countries if n in ("Finland", "Sweden")])
    lakes = [g for _, g in _load("ne_10m_lakes", bbox) if g.area > 0.002]
    rivers = [(n in KEY_RIVERS, g) for n, g in
              _load("ne_10m_rivers_lake_centerlines", bbox) + _load("ne_10m_rivers_europe", bbox)]
    _GEO = dict(land=land, finland=finland, lakes=lakes, rivers=rivers)
    with open(pk, "wb") as fh:
        pickle.dump(_GEO, fh)
    return _GEO


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
    pts = [tuple(p) for p in pts]
    if len(pts) < 3:
        return pts
    for _ in range(n):
        new = [pts[0]]
        for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
            new += [(0.75 * x0 + 0.25 * x1, 0.75 * y0 + 0.25 * y1), (0.25 * x0 + 0.75 * x1, 0.25 * y0 + 0.75 * y1)]
        new.append(pts[-1])
        pts = new
    return pts


def halo(w=2.5, c="white"):
    return [pe.withStroke(linewidth=w, foreground=c)]


_FONTS = False


def fonts():
    global _FONTS
    if _FONTS:
        return
    for fn in os.listdir(FONT_DIR):
        if fn.endswith(".ttf"):
            font_manager.fontManager.addfont(os.path.join(FONT_DIR, fn))
    plt.rcParams["font.family"] = "NanumGothic"
    plt.rcParams["axes.unicode_minus"] = False
    _FONTS = True


def front_chain(st):
    pts = []
    for a in AXES:
        for seg in st["fronts"].get(a, []):
            for p in seg["pts"]:
                p = tuple(p)
                if not pts or pts[-1] != p:
                    pts.append(p)
    return pts


# NATO 비슷한 부대 기호 (사각 프레임 + 병과 기호)
_RECT = Path([(-1.5, -1), (1.5, -1), (1.5, 1), (-1.5, 1), (-1.5, -1)], [1, 2, 2, 2, 79])
_X = Path([(-1.5, -1), (1.5, 1), (-1.5, 1), (1.5, -1)], [1, 2, 1, 2])
_t = [i / 24 * 2 * math.pi for i in range(25)]
_ELL = Path([(0.95 * math.cos(a), 0.55 * math.sin(a)) for a in _t], [1] + [2] * 24)
_GAR = Path([(-1.5, -1), (1.5, -1), (-1.5, -0.45), (1.5, -0.45)], [1, 2, 1, 2])


def unit_marker(ax, lo, la, side, kind, ms, z=13):
    fc = "#c9d7ea" if side == "de" else "#f6c7c2"
    ec = C_DE_ARROW if side == "de" else C_SU_ARROW
    ax.plot(lo, la, marker=_RECT, ms=ms, mfc=fc, mec=ec, mew=1.6, zorder=z, ls="none")
    glyphs = {"armor": [_ELL], "mech": [_ELL, _X], "inf": [_X], "garrison": [_X, _GAR]}.get(kind, [])
    for g in glyphs:
        ax.plot(lo, la, marker=g, ms=ms, mfc="none", mec=ec, mew=1.1, zorder=z + 0.1, ls="none")


def str_color(s):
    if s is None:
        return "#333333"
    return "#1d6b2f" if s >= 75 else ("#9a6a00" if s >= 50 else "#a01010")


KIND_CFG = {
    #            fig_w, dpi, title, unit_ms, unit_fs, city_lvl, arrow_fs, scale_km
    "tactical": dict(w=10.0, dpi=140, ms=15, fs=8.6, lvl=2, afs=8.2, km=50, grid=1, city_fs=8.2, river_fs=8),
    "operational": dict(w=10.5, dpi=135, ms=10, fs=6.9, lvl=1, afs=7.6, km=100, grid=2, city_fs=7.8, river_fs=7.5),
    "theater": dict(w=10.67, dpi=150, ms=0, fs=7.5, lvl=0, afs=7.5, km=200, grid=2, city_fs=7.5, river_fs=7),
}
KIND_KO = {"tactical": "전술도", "operational": "전역도", "theater": "전체 전선도"}


def render(st, kind, axis, outfile):
    fonts()
    G = geo()
    cfg = KIND_CFG[kind]
    if kind == "theater":
        x0, x1, y0, y1 = THEATER_EXTENT
    else:
        x0, x1, y0, y1 = st["views"][kind][axis]
    aspect = 1 / math.cos(math.radians((y0 + y1) / 2))
    W = cfg["w"]
    top_in, bot_in, side_in = 0.95, (1.25 if kind != "theater" else 1.55), 0.45
    map_w = W - 2 * side_in
    map_h = map_w * (y1 - y0) * aspect / (x1 - x0)
    H = map_h + top_in + bot_in
    fig = plt.figure(figsize=(W, H), dpi=cfg["dpi"])
    ax = fig.add_axes([side_in / W, bot_in / H, map_w / W, map_h / H])
    ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_aspect(aspect)
    ax.set_facecolor(C_SEA)
    vb = box(x0 - 0.3, y0 - 0.3, x1 + 0.3, y1 + 0.3)

    land = G["land"].intersection(vb)
    de_poly = Polygon(front_chain(st) + [tuple(p) for p in st["german_closure"]]).buffer(0)
    de_area = land.intersection(de_poly).difference(G["finland"])
    su_area = land.difference(de_poly).difference(G["finland"])
    fill(ax, land, facecolor=C_LAND, edgecolor="#6d6d6d", lw=0.6, zorder=1)
    fill(ax, de_area, facecolor=C_DE, edgecolor="none", alpha=0.75, zorder=2)
    fill(ax, su_area, facecolor=C_SU, edgecolor="none", alpha=0.6, zorder=2)
    fill(ax, land, facecolor="none", edgecolor="#555555", lw=0.6, zorder=3)
    for g in G["lakes"]:
        if g.intersects(vb):
            fill(ax, g.intersection(vb), facecolor=C_SEA, edgecolor=C_RIVER, lw=0.4, zorder=3)
    zoom = 1.0 if kind == "theater" else (1.35 if kind == "operational" else 1.8)
    for key, g in G["rivers"]:
        if not g.intersects(vb):
            continue
        for ln in lines(g.intersection(vb)):
            xs, ys = ln.xy
            ax.plot(xs, ys, color=C_RIVER, lw=(1.25 if key else 0.5) * min(zoom, 1.4),
                    alpha=0.95 if key else 0.6, zorder=4, solid_capstyle="round")

    step = cfg["grid"]
    ax.set_xticks([v for v in range(math.ceil(x0), int(x1) + 1) if v % step == 0])
    ax.set_yticks([v for v in range(math.ceil(y0), int(y1) + 1) if v % step == 0])
    ax.set_xticklabels([f"{v}°E" for v in ax.get_xticks().astype(int)], fontsize=8)
    ax.set_yticklabels([f"{v}°N" for v in ax.get_yticks().astype(int)], fontsize=8)
    ax.grid(color="#999999", lw=0.3, ls=":", zorder=4.5)
    ax.tick_params(length=2, top=True, right=True, labeltop=False, labelright=False)

    bx, by = zip(*BORDER_1941)
    ax.plot(bx, by, color="#444444", lw=1.0, ls=(0, (1, 1.5)), zorder=5)
    for f in st.get("forts", []):
        fx, fy = zip(*f["pts"])
        ax.plot(fx, fy, color="#6b4423", lw=6 * min(zoom, 1.5), alpha=0.4, solid_capstyle="round", zorder=5)

    T = dict(clip_on=True)
    for name, lo, la, rot in RIVER_LABELS:
        ax.text(lo, la, name, fontsize=cfg["river_fs"], color="#1b5a8c", style="italic", rotation=rot,
                ha="center", va="center", zorder=6, path_effects=halo(2, C_LAND), **T)
    for name, lo, la in AREA_LABELS:
        ax.text(lo, la, name, fontsize=9 if name in ("발트해", "흑해") else 7.5, color="#4a6f8a",
                style="italic", ha="center", va="center", zorder=6, path_effects=halo(2, "#eef5fa"), **T)

    for a in AXES:
        for seg in st["fronts"].get(a, []):
            fx, fy = zip(*seg["pts"])
            if seg.get("style", "solid") == "solid":
                ax.plot(fx, fy, color=C_FRONT, lw=2.8 * min(zoom, 1.3), zorder=8, solid_joinstyle="round",
                        path_effects=[pe.withStroke(linewidth=4.4 * min(zoom, 1.3), foreground="black")])
            else:
                ax.plot(fx, fy, color=C_FRONT, lw=2.2 * min(zoom, 1.3), ls=(0, (4, 2.5)), zorder=8)

    for pk in st.get("pockets", []):
        e = Ellipse((pk["lon"], pk["lat"]), 2 * pk["rx"], 2 * pk["ry"], facecolor=(0.85, 0.25, 0.25, 0.35),
                    edgecolor="#8b0000", hatch="////", lw=1.4, zorder=9)
        ax.add_patch(e)
        if pk.get("label"):
            ax.text(pk.get("lx", pk["lon"]), pk.get("ly", pk["lat"] - pk["ry"] - 0.15), pk["label"],
                    fontsize=cfg["afs"], color="#7a0000", ha=pk.get("ha", "center"), va="center", zorder=12,
                    fontweight="bold", path_effects=halo(2.5), **T)

    for a in st.get("arrows", []):
        if kind != "theater" and a.get("axis") not in (axis, None) and kind == "tactical":
            pass  # 전술도도 이웃 축 화살표는 그대로 그림(범위 밖은 잘림)
        col = C_DE_ARROW if a["side"] == "de" else C_SU_ARROW
        ls = (0, (1.2, 1.6)) if a["side"] == "esc" else (0, (3.2, 1.8))
        lw = (1.8 if a["side"] == "esc" else 2.6) * min(zoom, 1.3)
        (ax_, ay_), (bx_, by_) = a["pts"][-2], a["pts"][-1]
        L = math.hypot((bx_ - ax_) / aspect, by_ - ay_) or 1
        back = 0.08 * (x1 - x0) / 19.0
        tail = (bx_ - (bx_ - ax_) / L * back, by_ - (by_ - ay_) / L * back)
        pts = smooth([tuple(p) for p in a["pts"][:-1]] + [tail])
        xs, ys = zip(*pts)
        ax.plot(xs, ys, color=col, lw=lw, ls=ls, zorder=10, dash_capstyle="butt",
                path_effects=[pe.withStroke(linewidth=lw + 1.6, foreground="white")])
        ax.annotate("", xy=(bx_, by_), xytext=tail, zorder=11,
                    arrowprops=dict(arrowstyle="-|>,head_length=1.0,head_width=0.55", color=col, lw=0,
                                    mutation_scale=(9 if a["side"] != "esc" else 7) * min(zoom, 1.5),
                                    shrinkA=0, shrinkB=0,
                                    path_effects=[pe.withStroke(linewidth=1.5, foreground="white")]))
        linked = a.get("unit") and any(u["id"] == a["unit"] for u in st.get("units", []))
        if kind != "theater" and linked:
            if a.get("goal") and kind == "tactical":
                ux, uy = (bx_ - ax_) / L / aspect, (by_ - ay_) / L
                n = math.hypot(ux, uy) or 1
                ux, uy = ux / n, uy / n
                ha = "left" if ux > 0.35 else ("right" if ux < -0.35 else "center")
                off = a.get("goal_off") or (ux * 11, uy * 11 + (0 if ha != "center" else 3 * (1 if uy > 0 else -1)))
                if a.get("goal_off"):
                    ha = "center"
                ax.annotate(a["goal"], (bx_, by_), xytext=off,
                            textcoords="offset points", ha=ha, va="center", fontsize=cfg["afs"] - 0.4,
                            color=col, style="italic", fontweight="bold", zorder=12, path_effects=halo(2.5),
                            annotation_clip=True)
        elif a.get("label"):
            ax.text(a["lx"], a["ly"], a["label"], fontsize=cfg["afs"], color=col, ha=a.get("ha", "center"),
                    va="center", zorder=12, fontweight="bold", path_effects=halo(2.5), **T)

    for name, lo, la, dx, dy, ha, major, lvl in CITIES:
        if lvl > cfg["lvl"] or not (x0 < lo < x1 and y0 < la < y1):
            continue
        ax.plot(lo, la, marker="s" if major else "o", ms=5.5 if major else 4, mfc="black", mec="white",
                mew=0.8, zorder=13)
        ax.annotate(name, (lo, la), xytext=(dx, dy), textcoords="offset points", ha=ha, va="center",
                    fontsize=cfg["city_fs"] + (1 if major else 0), fontweight="bold" if major else "normal",
                    zorder=14, path_effects=halo(2.6), linespacing=0.95, annotation_clip=True)

    arrow_units = {a.get("unit") for a in st.get("arrows", []) if a.get("label")}
    for u in st.get("units", []):
        lo, la = u["lon"], u["lat"]
        if not (x0 < lo < x1 and y0 < la < y1):
            continue
        col = C_DE_ARROW if u["side"] == "de" else C_SU_ARROW
        if u["echelon"] == "group":
            ax.text(lo, la, u["name"], fontsize=10 if kind == "theater" else 9.5, fontweight="heavy", color=col,
                    ha="center", va="center", zorder=12, alpha=0.95,
                    bbox=dict(boxstyle="round,pad=0.25", fc="white", ec=col, lw=0.8, alpha=0.85), **T)
            continue
        if kind == "theater":
            if u["echelon"] == "army" and u["id"] not in arrow_units:
                ax.text(lo, la, u["name"], fontsize=7.2, fontweight="bold", color=col, ha="center", va="center",
                        zorder=12, path_effects=halo(2.5), **T)
            continue
        unit_marker(ax, lo, la, u["side"], u["kind"], cfg["ms"])
        s = u.get("strength")
        dx, dy = u.get("dx", 0), u.get("dy", -14)
        sc = 1.0 if kind == "tactical" else 0.8
        ha = "left" if dx > 3 else ("right" if dx < -3 and abs(dy) < 6 else "center")
        txt = u["name"] + (f"  {s}%" if s is not None else "")
        ax.annotate(txt, (lo, la), xytext=(dx * sc, dy * sc), textcoords="offset points", ha=ha, va="center",
                    fontsize=cfg["fs"], fontweight="bold", color=col, zorder=14, path_effects=halo(2.6),
                    annotation_clip=True)

    # 축척
    km = cfg["km"]
    lat_s = y0 + (y1 - y0) * 0.035
    dlon = km / (111.32 * math.cos(math.radians(lat_s)))
    lon_s = x1 - (x1 - x0) * 0.03 - dlon
    ax.plot([lon_s, lon_s + dlon], [lat_s, lat_s], color="black", lw=3, zorder=15, solid_capstyle="butt")
    ax.plot([lon_s, lon_s + dlon / 2], [lat_s, lat_s], color="white", lw=1.6, zorder=15, solid_capstyle="butt")
    ax.text(lon_s + dlon / 2, lat_s + (y1 - y0) * 0.012, f"{km} km", fontsize=7.5, ha="center", va="bottom",
            zorder=15, path_effects=halo())

    clk = clock_label(st["clock"])
    axis_ko = "" if kind == "theater" else f"{AXIS_KO[axis]}축 "
    title = f"{axis_ko}{KIND_KO[kind]} — {clk}"
    sub = {"tactical": "1분(게임 1일)마다 갱신 · 부대 마커 옆 %는 추정 전투력",
           "operational": "1분(게임 1일)마다 갱신 · 화살표: 현재 유효 명령에 따른 기동",
           "theater": "1분(게임 1일)마다 갱신 · 전선은 개략도"}[kind]
    fig.text(0.5, 1 - 0.36 / H, title, ha="center", va="center", fontsize=15 if kind != "theater" else 16,
             fontweight="heavy")
    fig.text(0.5, 1 - 0.68 / H, "대체역사 시뮬레이션 · " + sub, ha="center", va="center", fontsize=8.8,
             color="#333333")

    handles = [
        Line2D([], [], color=C_FRONT, lw=2.8, path_effects=[pe.withStroke(linewidth=4.4, foreground="black")], label="전선 (개략)"),
        Line2D([], [], color=C_FRONT, lw=2.2, ls=(0, (4, 2.5)), label="불명확·접촉 단절 구간"),
        Patch(facecolor=C_DE, alpha=0.75, label="독일·추축 통제"),
        Patch(facecolor=C_SU, alpha=0.6, label="소련 통제"),
        Patch(facecolor=(0.85, 0.25, 0.25, 0.35), edgecolor="#8b0000", hatch="////", label="포위망 / 고립 거점"),
        Line2D([], [], color="#6b4423", lw=6, alpha=0.4, label="요새지대 (스탈린선 등)"),
        Line2D([], [], color=C_DE_ARROW, lw=2.6, ls=(0, (4.5, 2.5)), marker=">", markevery=[-1], ms=6, label="독일군 계획 기동"),
        Line2D([], [], color=C_SU_ARROW, lw=2.6, ls=(0, (4.5, 2.5)), marker=">", markevery=[-1], ms=6, label="소련군 계획 기동"),
        Line2D([], [], color=C_SU_ARROW, lw=1.8, ls=(0, (1.2, 1.6)), marker=">", markevery=[-1], ms=5, label="소련 잔존군 탈출로"),
    ]
    if kind != "theater":
        handles += [
            Line2D([], [], marker=_RECT, ms=11, mfc="#c9d7ea", mec=C_DE_ARROW, mew=1.4, ls="none", label="독일 부대 (타원=기갑, X=보병)"),
            Line2D([], [], marker=_RECT, ms=11, mfc="#f6c7c2", mec=C_SU_ARROW, mew=1.4, ls="none", label="소련 부대 (타원+X=기계화)"),
            Line2D([], [], color="#444444", lw=1.0, ls=(0, (1, 1.5)), label="1941.6.22 국경"),
        ]
    else:
        handles += [Line2D([], [], color="#444444", lw=1.0, ls=(0, (1, 1.5)), label="1941.6.22 국경 (개략)"),
                    Line2D([], [], color=C_RIVER, lw=1.25, label="주요 하천"),
                    Line2D([], [], color="black", marker="s", ls="none", ms=5.5, mec="white", label="주요 도시 / 도시")]
    fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, 0.30 / H), ncol=4 if kind != "theater" else 3,
               fontsize=7.8, frameon=True, framealpha=1, edgecolor="#888888", handlelength=2.6,
               columnspacing=1.2, borderpad=0.5)
    fig.text(0.5, 0.12 / H, "대체역사 워게임(주사위+절차 판정) · 손실·전투력은 게임 추정치 · 지도: Natural Earth",
             ha="center", va="center", fontsize=7.5, color="#444444")
    os.makedirs(os.path.dirname(outfile), exist_ok=True)
    tmp = outfile + ".tmp.png"
    fig.savefig(tmp, dpi=cfg["dpi"])
    plt.close(fig)
    os.replace(tmp, outfile)
    return outfile


def map_path(kind, axis=None):
    return os.path.join(SITE_MAPS, f"{kind}_{axis}.png" if axis else f"{kind}.png")


def render_kind(st, kind, axes=None):
    out = []
    if kind == "theater":
        out.append(render(st, "theater", None, map_path("theater")))
    else:
        for a in axes or AXES:
            out.append(render(st, kind, a, map_path(kind, a)))
    return out


if __name__ == "__main__":
    st = load_state()
    kinds = ["tactical", "operational", "theater"] if len(sys.argv) < 2 or sys.argv[1] == "all" else [sys.argv[1]]
    axes = [sys.argv[2]] if len(sys.argv) > 2 else None
    for k in kinds:
        for p in render_kind(st, k, axes):
            print("saved", p)
