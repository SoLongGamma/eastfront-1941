"""공용 유틸: 경로, state.json 입출력(원자적 저장 + 잠금), 시간 계산."""
import contextlib, datetime as dt, fcntl, json, os, tempfile
from zoneinfo import ZoneInfo

LIVE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(LIVE)
STATE = os.path.join(LIVE, "state.json")
PLANS = os.path.join(LIVE, "plans")
SITE = os.path.join(LIVE, "site")
SITE_MAPS = os.path.join(SITE, "maps")
CACHE = os.path.join(LIVE, "cache")
LOCK = os.path.join(LIVE, ".tick.lock")
KST = ZoneInfo("Asia/Seoul")
AXES = ["north", "center", "south"]
AXIS_KO = {"north": "북부", "center": "중부", "south": "남부", "all": "전체"}
SIDE_KO = {"de": "독일", "su": "소련"}
HOURS = [6, 12, 18, 24]


def now_kst():
    return dt.datetime.now(KST)


def iso_kst(t=None):
    return (t or now_kst()).strftime("%Y-%m-%dT%H:%M:%S+09:00")


def slot_kst(t=None):
    """현재 15분 슬롯(KST) 문자열 — 틱 멱등성 키."""
    t = t or now_kst()
    t = t.replace(minute=t.minute - t.minute % 15, second=0, microsecond=0)
    return t.strftime("%Y-%m-%dT%H:%M+09:00")


def load_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def save_json(path, obj):
    d = os.path.dirname(path)
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".tmp-", suffix=".json")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    os.chmod(tmp, 0o644)
    os.replace(tmp, path)


def load_state():
    return load_json(STATE)


def save_state(st):
    save_json(STATE, st)


@contextlib.contextmanager
def state_lock(blocking=True):
    fh = open(LOCK, "w")
    try:
        fcntl.flock(fh, fcntl.LOCK_EX | (0 if blocking else fcntl.LOCK_NB))
    except BlockingIOError:
        fh.close()
        raise
    try:
        yield
    finally:
        fcntl.flock(fh, fcntl.LOCK_UN)
        fh.close()


# ---- 게임 시계 ---------------------------------------------------------------
# clock = {"date": "1941-07-06", "hour": 0}   hour ∈ {0, 6, 12, 18}
# 24시 키프레임 적용 후에는 다음 날 00시로 넘어간다.
def clock_label(c):
    d = dt.date.fromisoformat(c["date"])
    return f"{d.year}.{d.month}.{d.day} {c['hour']:02d}:00"


def clock_short(c):
    d = dt.date.fromisoformat(c["date"])
    return f"{d.month}.{d.day} {c['hour']:02d}:00"


def next_phase(c):
    """현재 시계에서 다음 페이즈로 갈 때 적용할 (계획 날짜, 키프레임 시각, 새 시계)."""
    h = c["hour"] + 6
    if h == 24:
        nd = (dt.date.fromisoformat(c["date"]) + dt.timedelta(days=1)).isoformat()
        return c["date"], 24, {"date": nd, "hour": 0}
    return c["date"], h, {"date": c["date"], "hour": h}


def game_stamp(date, hour):
    """이벤트용 게임 시각 문자열 (24시는 그날 24:00으로 표기)."""
    d = dt.date.fromisoformat(date)
    return f"{d.year}.{d.month}.{d.day} {hour:02d}:00"


def plan_path(date):
    return os.path.join(PLANS, f"{date}.json")
