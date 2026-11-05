# Event ON - single-file Streamlit deployment
import base64 as _b64
import zlib as _zl
from pathlib import Path as _Path

_APP_DIR = _Path(__file__).resolve().parent
_DIST = _APP_DIR / "_eventon_ui"
_DIST.mkdir(exist_ok=True)
_BUNDLE_B64 = (_Path(__file__).resolve().parent / "dashboard.b64").read_text(encoding="ascii")
(_DIST / "index.html").write_bytes(_zl.decompress(_b64.b64decode(_BUNDLE_B64)))

_EMBEDDED_ASSETS = __import__("json").loads((_Path(__file__).resolve().parent / "home_assets.json").read_text(encoding="utf-8"))

def _load_asset(filename):
    return _EMBEDDED_ASSETS[filename]

import re
import streamlit as st
import sqlite3
import hashlib
import secrets
import json
import io
from pathlib import Path
from datetime import datetime

APP_DIR = Path(__file__).resolve().parent
DB_PATH = APP_DIR / "event_on.db"


_ASSET_DIR = _APP_DIR / "eventon_assets"
def _load_asset(filename):
    """Load bundled assets without requiring an external assets folder."""
    if filename in _EMBEDDED_ASSETS:
        return _EMBEDDED_ASSETS[filename]
    asset_path = _ASSET_DIR / filename
    if asset_path.is_file():
        return asset_path.read_text(encoding="utf-8")
    raise FileNotFoundError(
        f"필요한 리소스를 찾을 수 없습니다: {filename}. "
        "내장 리소스가 포함된 원본 app.py 파일을 사용해 주세요."
    )

st.set_page_config(page_title="Event ON", page_icon="🎪", layout="wide", initial_sidebar_state="expanded")

# -------------------- Theme --------------------
st.markdown("""
<style>
.stApp { background:#f6f8fc; color:#17233c; }
.block-container { padding-top:1.5rem; padding-bottom:3rem; max-width:1440px; }
[data-testid="stSidebar"] {
  background:#ffffff;
  border-right:0;
}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color:#526582; }
[data-testid="stSidebar"] hr { border-color:rgba(255,255,255,.16); }
[data-testid="stSidebar"] div.stButton > button {
  background:#fff !important;
  color:#172b4d !important;
  border:1px solid #e0e7f4 !important;
  text-align:left;
  border-radius:12px;
  min-height:2.7rem;
  font-weight:750;
  margin:.12rem 0;
  box-shadow:0 2px 6px rgba(0,0,0,.05);
}
[data-testid="stSidebar"] div.stButton > button p,
[data-testid="stSidebar"] div.stButton > button span,
[data-testid="stSidebar"] div.stButton > button div {
  color:#172b4d !important;
  border:0 !important;
  border-radius:0 !important;
  box-shadow:none !important;
  background:transparent !important;
  margin:0 !important;
  padding:0 !important;
}
[data-testid="stSidebar"] div.stButton>button:hover {
  background:#eaf0ff !important; border-color:#a9beff !important; color:#244bd0 !important;
}
[data-testid="stSidebar"] div.stButton > button[kind="primary"] {
  background:#dfe8ff !important;
  border-color:#a8bdff !important;
  color:#2347bd !important;
}
[data-testid="stSidebar"] div.stButton > button[kind="primary"] p,
[data-testid="stSidebar"] div.stButton > button[kind="primary"] span,
[data-testid="stSidebar"] div.stButton > button[kind="primary"] div {
  color:#2347bd !important;
  background:transparent !important;
  border:0 !important;
  box-shadow:none !important;
  margin:0 !important;
  padding:0 !important;
}
.brand-link {
  display:block; text-decoration:none !important; cursor:pointer; padding:.2rem 0 .4rem;
  color:#172b4d !important; font-size:1.8rem; font-weight:900; letter-spacing:-.07em; line-height:1.1;
}
.brand-link span { color:#8db0ff; }
.brand-sub { color:#64748b; font-size:.65rem; letter-spacing:.14em; font-weight:800; }
.sidebar-label { color:#91a5c8; font-size:.68rem; font-weight:850; letter-spacing:.15em; margin:.8rem 0 .3rem; }
.sidebar-user { background:rgba(255,255,255,.09); border:1px solid rgba(255,255,255,.13); border-radius:15px; padding:.9rem; margin-top:.4rem; }
.sidebar-user-name { font-weight:800; color:#172b4d; }
.sidebar-user-role { font-size:.8rem; color:#b8c7e2; margin-top:.15rem; }
.hero {
  background:linear-gradient(120deg,#fff 0%,#eef3ff 62%,#e7eeff 100%);
  border:1px solid #e2e9fb; border-radius:26px; padding:clamp(1.5rem,4vw,3.2rem);
  box-shadow:0 14px 40px rgba(39,68,130,.06); margin-bottom:1.5rem;
}
.eyebrow { color:#315be8; font-size:.76rem; font-weight:900; letter-spacing:.15em; }
.hero h1 { font-size:clamp(2.1rem,4.5vw,3.7rem); line-height:1.1; letter-spacing:-.055em; color:#172b4d; margin:.7rem 0 1rem; }
.hero p { font-size:1rem; color:#5c6b84; max-width:750px; line-height:1.85; }
.feature-card { background:#fff; border:1px solid #e5eaf4; border-radius:22px; padding:1.5rem; height:240px; box-sizing:border-box; overflow:auto; box-shadow:0 8px 28px rgba(29,52,96,.045); }
.feature-icon { display:inline-flex; width:48px; height:48px; border-radius:15px; align-items:center; justify-content:center; background:#edf2ff; font-size:1.45rem; margin-bottom:.85rem; }
.feature-card h3 { color:#1d2d50; margin:0 0 .55rem; }
.feature-card p { color:#687791; line-height:1.7; font-size:.93rem; }
.placeholder { background:#fff; border:1.5px dashed #c9d4e6; border-radius:22px; padding:2.4rem 1.5rem; min-height:260px; text-align:center; }
.report-hero { background:linear-gradient(120deg,#152747,#315be8); color:white; border-radius:22px; padding:1.8rem 2rem; margin-bottom:1.1rem; }
.report-hero h2 { color:white; margin:.3rem 0 .6rem; }
.report-hero p { color:#dce6ff; line-height:1.7; }
.metric-card { background:#fff; border:1px solid #e5eaf4; border-radius:16px; padding:1rem 1.1rem; min-height:100px; }
.metric-label { color:#75829a; font-size:.82rem; }
.metric-value { color:#1d2d50; font-size:1.35rem; font-weight:850; margin-top:.3rem; }
div.stButton>button { border-radius:12px; min-height:2.65rem; font-weight:700; }
div.stButton>button[kind="primary"] { background:#315be8; border-color:#315be8; color:#fff; }
div[data-testid="stForm"] { background:#fff; padding:1.2rem; border:1px solid #e5eaf4; border-radius:18px; }
.small-muted { color:#7b8798; font-size:.84rem; }
</style>
""", unsafe_allow_html=True)

# -------------------- Database --------------------
def db_connect():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with db_connect() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE COLLATE NOCASE,
            display_name TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT '기획자',
            salt TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS user_settings (
            user_id INTEGER PRIMARY KEY,
            settings_json TEXT NOT NULL DEFAULT '{}',
            FOREIGN KEY(user_id) REFERENCES users(id)
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            project_name TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )""")
        conn.commit()

def hash_password(password, salt_hex=None):
    salt = bytes.fromhex(salt_hex) if salt_hex else secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 260_000)
    return salt.hex(), digest.hex()

def verify_password(password, salt_hex, expected_hash):
    _, candidate = hash_password(password, salt_hex)
    return secrets.compare_digest(candidate, expected_hash)

def create_user(username, display_name, role, password):
    salt, password_hash = hash_password(password)
    try:
        with db_connect() as conn:
            cur = conn.execute("INSERT INTO users (username,display_name,role,salt,password_hash) VALUES (?,?,?,?,?)",
                               (username.strip(), display_name.strip(), role, salt, password_hash))
            user_id = cur.lastrowid
            conn.execute("INSERT INTO user_settings(user_id,settings_json) VALUES (?,?)", (user_id, json.dumps(default_settings(), ensure_ascii=False)))
            conn.commit()
        return True, "회원가입이 완료됐어요. 로그인해 주세요."
    except sqlite3.IntegrityError:
        return False, "이미 사용 중인 아이디예요."

def authenticate(username, password):
    with db_connect() as conn:
        user = conn.execute("SELECT * FROM users WHERE username=? COLLATE NOCASE", (username.strip(),)).fetchone()
    if user and verify_password(password, user["salt"], user["password_hash"]):
        return dict(user)
    return None

def default_settings():
    return {
        "department": "", "company": "", "report_format": "PDF", "report_detail": "상세",
        "include_recommendations": True, "include_risks": True, "theme": "라이트",
        "compact": False, "analysis_level": "균형", "audience_flow": True,
        "accessibility": True, "notifications": True
    }

def get_settings(user_id):
    if not user_id:
        return default_settings()
    with db_connect() as conn:
        row = conn.execute("SELECT settings_json FROM user_settings WHERE user_id=?", (user_id,)).fetchone()
    if not row:
        return default_settings()
    try:
        data = default_settings()
        data.update(json.loads(row["settings_json"]))
        return data
    except Exception:
        return default_settings()

def save_settings(user_id, settings):
    if not user_id:
        return
    with db_connect() as conn:
        conn.execute("""INSERT INTO user_settings(user_id,settings_json) VALUES (?,?)
            ON CONFLICT(user_id) DO UPDATE SET settings_json=excluded.settings_json""",
            (user_id, json.dumps(settings, ensure_ascii=False)))
        conn.commit()

def save_project(user_id, name, payload):
    with db_connect() as conn:
        conn.execute("INSERT INTO projects(user_id,project_name,payload_json) VALUES (?,?,?)",
                     (user_id, name, json.dumps(payload, ensure_ascii=False)))
        conn.commit()

init_db()
for k, v in {"page":"홈","logged_in":False,"user_id":None,"username":"","display_name":"","role":""}.items():
    if k not in st.session_state: st.session_state[k] = v
if "report_data" not in st.session_state: st.session_state.report_data = {}

# 실제 저장된 화면 설정 적용
_current_settings = get_settings(st.session_state.user_id)
if _current_settings.get("theme") == "다크":
    st.markdown("""
    <style>
    .stApp { background:#101827 !important; color:#e8edf7 !important; }
    [data-testid="stMain"] .stMarkdown, [data-testid="stMain"] label,
    [data-testid="stMain"] p, [data-testid="stMain"] h1, [data-testid="stMain"] h2,
    [data-testid="stMain"] h3, [data-testid="stMain"] h4 { color:#e8edf7 !important; }
    [data-testid="stMain"] div[data-testid="stForm"],
    [data-testid="stMain"] .feature-card, [data-testid="stMain"] .metric-card {
      background:#1a2639 !important; border-color:#33435e !important; color:#e8edf7 !important;
    }
    [data-testid="stMain"] input, [data-testid="stMain"] textarea,
    [data-testid="stMain"] [data-baseweb="select"] > div {
      background:#26344b !important; color:#f3f6fc !important; border-color:#425575 !important;
    }
    </style>
    """, unsafe_allow_html=True)
if _current_settings.get("compact"):
    st.markdown("""
    <style>
    .block-container { padding-top:.65rem !important; padding-bottom:1.2rem !important; }
    [data-testid="stMain"] div[data-testid="stVerticalBlock"] { gap:.65rem; }
    [data-testid="stMain"] .feature-card { height:220px; min-height:220px; padding:1rem; }
    </style>
    """, unsafe_allow_html=True)

def go(page):
    if page == "대시보드":
        st.session_state["dashboard_entry_version"] = st.session_state.get("dashboard_entry_version", 0) + 1
    st.session_state.page = page

# -------------------- Sidebar --------------------
def render_sidebar():
    with st.sidebar:
        # Streamlit reruns on clicks; this link uses query params to route the brand home.
        st.markdown('<a class="brand-link" href="?page=home" target="_self">Event <span>ON</span></a><div class="brand-sub">PLAN SMART. RUN BETTER.</div>', unsafe_allow_html=True)
        st.write("")
        st.markdown('<div class="sidebar-label">WORKSPACE</div>', unsafe_allow_html=True)
        routes = [("⌂", "홈", "홈"), ("▦", "대시보드", "대시보드"), ("▤", "보고서", "보고서")]
        for icon, label, pg in routes:
            if st.button(f"{icon}   {label}", key=f"nav_{pg}", use_container_width=True,
                         type="primary" if st.session_state.page == pg else "secondary"):
                go(pg); st.rerun()
        st.markdown('<div class="sidebar-label">PREFERENCES</div>', unsafe_allow_html=True)
        if st.button("⚙   설정", key="nav_settings", use_container_width=True,
                     type="primary" if st.session_state.page == "설정" else "secondary"):
            go("설정"); st.rerun()
        st.markdown('<style>\n[data-testid="stSidebarUserContent"]{min-height:calc(100dvh - 4rem);display:flex;flex-direction:column}\n[data-testid="stSidebarUserContent"] > [data-testid="stVerticalBlock"]{flex:1;min-height:calc(100dvh - 5rem)}\n[data-testid="stSidebarUserContent"] [data-testid="stVerticalBlock"]:has(> .st-key-sidebar_account){min-height:calc(100dvh - 5rem)}\n.st-key-sidebar_account{margin-top:auto!important;padding-top:24px;padding-bottom:12px;flex-shrink:0}\n</style>', unsafe_allow_html=True)
        with st.container(key="sidebar_account"):
            if st.session_state.logged_in:
                name = st.session_state.display_name or st.session_state.username
                st.markdown(f'<div class="sidebar-user"><div class="sidebar-user-name">● &nbsp; {name}님</div><div class="sidebar-user-role">{st.session_state.role}</div></div>', unsafe_allow_html=True)
                if st.button("로그아웃", key="logout", use_container_width=True):
                    for k,v in {"logged_in":False,"user_id":None,"username":"","display_name":"","role":"","page":"홈"}.items():
                        st.session_state[k]=v
                    st.rerun()
            else:
                st.markdown('<div class="sidebar-label">YOUR ACCOUNT</div>', unsafe_allow_html=True)
                if st.button("↗   로그인 / 회원가입", key="nav_login", use_container_width=True):
                    go("로그인"); st.rerun()

# Query param brand navigation
try:
    qp = st.query_params.get("page")
    if qp == "home":
        st.session_state.page = "홈"
        st.query_params.clear()
except Exception:
    pass

# -------------------- Pages --------------------
def render_home():
    with st.container(key='clean_home'):
        st.markdown('<div class="clean-copy"><span>EVENT PLANNING WORKSPACE</span><h1>좋은 행사의 시작,<br>명확한 설계에서.</h1><p>행사 기획부터 공간 배치까지, Event ON.</p></div>',unsafe_allow_html=True)
        with st.container(key='clean_start'):
            if st.button('설계 시작하기　→',type='primary',key='clean_start_btn'):go('대시보드');st.rerun()
    st.markdown(REAL_FEATURES_HTML,unsafe_allow_html=True)





def render_dashboard():
    import dashboard
    dashboard.main()



def format_formal_report(markdown_text: str) -> str:
    """보고서 번호 체계를 1. → 가. → 1) 순서로 만들고, 각 항목을 별도 줄에 표시한다.

    Markdown 미리보기에서 한 줄로 합쳐지지 않도록 각 줄 끝에 Markdown 강제 줄바꿈
    공백 두 개를 넣는다. 항목 앞 들여쓰기는 Markdown 코드 블록으로 해석될 수 있어 쓰지 않는다.
    """
    out = []
    main_no = 0
    sub_no = 0
    detail_no = 0
    hangul = "가나다라마바사아자차카타파하"

    for raw in markdown_text.splitlines():
        stripped = raw.strip()
        if not stripped:
            out.append("")
            continue

        if stripped.startswith("# "):
            rendered = stripped[2:].strip()
        elif stripped.startswith("## "):
            main_no += 1
            sub_no = 0
            detail_no = 0
            title = re.sub(r"^\d+[.)]\s*", "", stripped[3:].strip())
            rendered = f"{main_no}. {title}"
        elif stripped.startswith("### "):
            sub_no += 1
            detail_no = 0
            title = re.sub(r"^[가-하]\.\s*", "", stripped[4:].strip())
            marker = f"{hangul[sub_no - 1]}." if sub_no <= len(hangul) else f"({sub_no})"
            rendered = f"　{marker} {title}"
        elif re.match(r"^[-*]\s+", stripped):
            detail_no += 1
            item = re.sub(r"^[-*]\s+", "", stripped)
            item = re.sub(r"^\[\s*\]\s*", "□ ", item)
            rendered = f"　　{detail_no}) {item}"
        elif stripped == "---":
            rendered = "---"
        else:
            rendered = stripped

        # Markdown hard line break: Streamlit 미리보기에서 항목마다 다음 줄로 내려가게 함.
        out.append(rendered + "  ")
    return "\n".join(out)


def _numbering_smoke_test():
    sample = "# 테스트 보고서\\n## 추진 목적\\n### 추진 배경\\n- 행사 필요성\\n- 운영 목표"
    result = format_formal_report(sample)
    expected = ["1. 추진 목적", "가. 추진 배경", "1) 행사 필요성", "2) 운영 목표"]
    return all(item in result for item in expected), result


def build_report_text(d, settings):
    """행사 입력값과 사용자 설정을 반영해 실제 업무용 보고서 초안을 작성."""
    event_name = d.get("event_name") or "행사 운영 계획"
    event_type = d.get("event_type", "기타")
    purpose = d.get("purpose", "행사 목적 미입력")
    venue = d.get("venue", "미정")
    event_date = d.get("date", "미정")
    hours = d.get("hours", "미정")
    visitors = int(d.get("visitors", 0) or 0)
    budget = d.get("budget", "미정")
    audience = d.get("audience", "전 연령")
    mood = d.get("mood", "전문적인")
    facilities = d.get("facilities", "기본 안내 시설")
    detail = settings.get("report_detail", "상세")
    analysis = settings.get("analysis_level", "균형")

    lines = [
        f"# {event_name} 행사 운영 계획 보고서",
        f"**작성일:** {datetime.now().strftime('%Y년 %m월 %d일')}",
        "**작성 도구:** Event ON 행사 기획 지원",
        "",
        "## 추진 개요",
        "### 추진 목적",
        f"- {purpose}",
        "### 추진 방향",
        f"- 행사 유형과 주요 대상({audience})의 특성을 고려해 프로그램과 안내 방식을 구성합니다.",
        f"- 행사 분위기는 '{mood}'를 기준으로 통일하고, 방문객 편의와 안전을 함께 고려합니다.",
        "",
        "## 행사 개요",
        "### 행사 기본 정보",
        f"- 행사명: {event_name}",
        f"- 행사 유형: {event_type}",
        f"- 행사 일시: {event_date} / {hours}",
        f"- 행사 장소: {venue}",
        f"- 주요 대상: {audience}",
        f"- 예상 방문객: {visitors:,}명",
        f"- 소요 예산: {budget}",
        "### 운영 시설",
        f"- 필요 시설: {facilities}",
        "",
        "## 세부 추진 계획",
        "### 사전 준비",
        "- 행사 담당자별 업무와 의사결정 담당자를 지정하고, 행사 전 공유 회의를 진행합니다.",
        "- 장소 사용 가능 시간, 시설 설치 조건, 전력·통신 환경 및 반입 절차를 확인합니다.",
        "- 프로그램별 준비 완료 시각과 점검 담당자를 정하고, 변경 사항을 공유할 연락 체계를 마련합니다.",
        "### 현장 운영",
        "- 개장 전 안내 표지, 접수 장비, 시설 상태 및 비상구 주변의 장애물 여부를 확인합니다.",
        "- 입장 안내, 프로그램 진행, 시설 관리, 방문객 문의 대응 업무를 구분해 운영합니다.",
        "- 운영 중 주요 문의와 현장 이슈를 기록하고, 필요한 경우 책임자에게 즉시 보고합니다.",
        "### 종료 및 사후 정리",
        "- 방문객 퇴장 흐름을 안내하고, 혼잡이 발생하는 구간에는 현장 인력을 배치합니다.",
        "- 시설과 장비를 확인하고 분실물·폐기물·대여 물품을 정리합니다.",
        "- 방문객 수, 문의 내용, 운영상 문제 및 개선 의견을 기록해 결과 검토 자료로 활용합니다.",
    ]

    if detail in ("표준", "상세"):
        lines += [
            "",
            "## 인력 및 역할 운영",
            "### 업무 분장",
            "- 총괄 담당: 전체 일정과 현장 의사결정, 유관 담당자 간 조정을 맡습니다.",
            "- 안내·접수 담당: 입장 확인, 행사 안내, 문의 응대 및 대기 줄 관리를 맡습니다.",
            "- 시설·프로그램 담당: 시설 상태와 프로그램 진행 상황을 점검하고 문제 발생 시 공유합니다.",
            "- 안전 담당: 비상 통로와 혼잡 구역을 확인하고 비상 연락 절차를 숙지합니다.",
            "### 운영 커뮤니케이션",
            "- 행사 전 담당자 연락망과 보고 기준을 공유하고, 현장 변경 사항은 동일한 안내 체계로 전달합니다.",
            "- 실제 인력 수와 근무 시간은 행사 규모, 장소 조건 및 프로그램 수를 확인한 뒤 확정합니다.",
        ]

    if settings.get("include_recommendations", True):
        lines += [
            "",
            "## 운영 개선 및 권장 사항",
            "### 방문객 경험 개선",
            "- 입구, 접수대, 주요 프로그램, 휴게 시설 및 출구의 안내 표지를 일관된 방식으로 배치합니다.",
            "- 반복 문의가 예상되는 정보는 안내판 또는 온라인 안내 페이지에 미리 제공합니다.",
            "- 대기 공간과 휴식 공간을 구분해 통행 흐름을 유지하고 방문객이 머무를 장소를 확보합니다.",
            "### 운영 효율 개선",
            "- 프로그램별 담당자와 준비 완료 시각을 정해 현장 지연 가능성을 줄입니다.",
            "- 행사 종료 후 방문객 수, 대기 시간, 자주 발생한 문의 및 운영 문제를 정리해 다음 행사에 반영합니다.",
        ]

    if settings.get("audience_flow", True):
        lines += [
            "",
            "## 방문객 동선 계획",
            "### 기본 동선 원칙",
            "- 입구에서 접수·주요 프로그램·휴게 시설·출구로 이어지는 이동 흐름이 자연스럽게 연결되도록 안내합니다.",
            "- 대기 줄이 주 통로와 비상 통로를 막지 않도록 대기 공간을 별도로 검토합니다.",
            "- 실제 공간 배치가 확정되면 교차 지점과 혼잡 예상 구역을 현장에서 확인하고 안내 인력을 배치합니다.",
        ]

    if settings.get("accessibility", True):
        lines += [
            "",
            "## 접근성 및 편의 지원",
            "### 이용 편의 확인",
            "- 이동 약자도 접근할 수 있는 출입 경로와 시설 이용 가능 여부를 사전에 확인합니다.",
            "- 안내 표지는 읽기 쉬운 글자 크기와 명확한 색상 대비를 적용하고, 주요 분기점에 반복 배치합니다.",
            "- 필요한 경우 휴게 공간, 가족 편의 시설 및 현장 문의 지원 방법을 안내합니다.",
        ]

    if settings.get("include_risks", True):
        lines += [
            "",
            "## 위험 요소 및 대응 계획",
            "### 혼잡 및 안전사고",
            "- 예상 상황: 입장·접수 구역이나 인기 프로그램 주변에 방문객이 집중될 수 있습니다.",
            "- 대응 방안: 대기 공간과 통행 공간을 구분하고, 혼잡 시 현장 안내 인력을 추가 배치합니다.",
            "### 응급 상황",
            "- 예상 상황: 방문객의 건강 이상이나 시설 이용 중 응급 상황이 발생할 수 있습니다.",
            "- 대응 방안: 비상 연락 체계와 응급 지원 위치를 사전에 공유하고, 현장 담당자의 보고 절차를 확인합니다.",
            "### 일정 지연 및 장비 문제",
            "- 예상 상황: 프로그램 준비 지연이나 음향·전력·통신 장비 문제가 발생할 수 있습니다.",
            "- 대응 방안: 사전 점검을 실시하고, 지연 시 안내 문구와 대체 진행 순서를 마련합니다.",
        ]

    lines += [
        "",
        "## 행사 당일 점검 사항",
        "### 개장 전",
        "- [ ] 출입구·비상구·주요 통로와 안내 표지 확인",
        "- [ ] 접수 장비, 음향·전력·통신 장비 점검",
        "- [ ] 담당자별 역할과 비상 연락망 공유",
        "### 운영 중",
        "- [ ] 방문객 흐름과 대기 구역 확인",
        "- [ ] 시설 상태 및 주요 프로그램 진행 상황 점검",
        "- [ ] 현장 이슈 기록 및 책임자 공유",
        "### 종료 후",
        "- [ ] 방문객 퇴장 안내 및 시설·장비 정리",
        "- [ ] 분실물·폐기물·대여 물품 확인",
        "- [ ] 운영 결과와 개선 사항 기록",
        "",
        "## 기대 효과",
        "### 기대 성과",
        "- 행사 준비와 현장 운영의 역할을 구체화해 운영 과정의 혼선을 줄일 수 있습니다.",
        "- 안내 체계와 동선 관리 기준을 사전에 마련해 방문객 편의와 안전을 높일 수 있습니다.",
        "- 행사 종료 후 운영 기록을 축적해 향후 행사 기획과 개선에 활용할 수 있습니다.",
        "",
        "## 작성 시 유의 사항",
        "- 본 문서는 입력된 정보를 바탕으로 작성한 행사 운영 계획 초안입니다.",
        "- 실제 인력 배치, 예산 집행, 공간 배치 및 안전 조치는 현장 조건과 관계 기준을 확인한 뒤 확정해야 합니다.",
    ]

    if detail == "요약" or analysis == "간결":
        # 요약 설정은 핵심 항목 중심으로 구성
        keep_main = {
            "추진 개요", "행사 개요", "세부 추진 계획",
            "운영 개선 및 권장 사항", "위험 요소 및 대응 계획",
            "행사 당일 점검 사항", "기대 효과", "작성 시 유의 사항"
        }
        filtered = []
        active = False
        for line in lines:
            if line.startswith("# "):
                filtered.append(line)
            elif line.startswith("## "):
                title = line[3:].strip()
                active = title in keep_main
                if active:
                    filtered.append(line)
            elif active:
                filtered.append(line)
        lines = filtered
    elif analysis == "세부 분석":
        lines += [
            "",
            "## 추가 검토 필요 사항",
            "### 현장 확정 전 확인",
            "- 행사장 실측 도면, 수용 가능 인원, 통로 폭 및 실제 시설 위치는 별도 확인이 필요합니다.",
            "- 실제 인력 수, 단가별 예산, 프로그램별 소요 시간 및 비상 대응 담당자는 확정 정보에 따라 보완해야 합니다.",
        ]

    return "\n".join(lines)

def create_pdf(report_text, title):
    # PDF generation with ReportLab. Font fallback keeps Korean readable where a CJK font is available.
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
    from reportlab.lib.units import mm
    from xml.sax.saxutils import escape
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, rightMargin=18*mm, leftMargin=18*mm, topMargin=18*mm, bottomMargin=18*mm)
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont
    pdfmetrics.registerFont(UnicodeCIDFont('HYSMyeongJo-Medium'))
    styles = getSampleStyleSheet()
    for style in styles.byName.values():style.fontName='HYSMyeongJo-Medium'

    styles.add(ParagraphStyle(name="CoverTitle", parent=styles["Title"], fontName="HYSMyeongJo-Medium", fontSize=22, leading=28, textColor=colors.HexColor("#2447a8"), alignment=TA_LEFT, spaceAfter=10))
    styles.add(ParagraphStyle(name="Section", parent=styles["Heading2"], fontSize=13, leading=18, textColor=colors.HexColor("#2447a8"), spaceBefore=10, spaceAfter=5))
    styles.add(ParagraphStyle(name="BodyCustom", parent=styles["BodyText"], fontSize=9.5, leading=14, spaceAfter=4))
    story=[]
    for line in report_text.splitlines():
        if line.startswith("# "):
            story.append(Paragraph(escape(line[2:]), styles["CoverTitle"]))
        elif line.startswith("## "):
            story.append(Spacer(1,5))
            story.append(Paragraph(escape(line[3:]), styles["Section"]))
        elif line.startswith("### "):
            story.append(Paragraph("<b>" + escape(line[4:]) + "</b>", styles["BodyCustom"]))
        elif re.match(r"^\s*\d+\.\s+", line):
            story.append(Spacer(1, 4))
            story.append(Paragraph("<b>" + escape(line.strip()) + "</b>", styles["Section"]))
        elif re.match(r"^\s*[가-하]\.\s+", line):
            story.append(Paragraph("<b>" + escape(line.strip()) + "</b>", styles["BodyCustom"]))
        elif re.match(r"^\s*\d+\)\s+", line):
            story.append(Paragraph(escape(line.strip()), styles["BodyCustom"]))
        elif line.startswith("- "):
            story.append(Paragraph("• " + escape(line[2:]), styles["BodyCustom"]))
        elif line.startswith("**") and line.endswith("**"):
            story.append(Paragraph("<b>"+escape(line.strip("*"))+"</b>", styles["BodyCustom"]))
        elif line == "---":
            story.append(Spacer(1,8))
        elif line.strip():
            story.append(Paragraph(escape(line), styles["BodyCustom"]))
        else:
            story.append(Spacer(1,3))
    doc.build(story)
    return buf.getvalue()

# Superseded by standard document renderer below.

def render_settings():
    st.markdown('<div class="eyebrow">PREFERENCES</div>',unsafe_allow_html=True)
    st.title("설정")
    settings=get_settings(st.session_state.user_id)
    tabs=st.tabs(["계정 및 프로필","보고서 설정","화면 설정","AI 분석 설정","프로젝트 및 저장 관리","보안 및 계정 관리"])

    with tabs[0]:
        st.subheader("계정 및 프로필")
        if st.session_state.logged_in:
            with st.form("profile_form"):
                display=st.text_input("표시 이름",value=st.session_state.display_name)
                role=st.selectbox("역할",["기획자","관리자","팀원","상사"],index=["기획자","관리자","팀원","상사"].index(st.session_state.role) if st.session_state.role in ["기획자","관리자","팀원","상사"] else 0)
                department=st.text_input("부서",value=settings.get("department",""))
                company=st.text_input("회사 / 기관",value=settings.get("company",""))
                save=st.form_submit_button("프로필 저장",type="primary")
            if save:
                with db_connect() as conn:
                    conn.execute("UPDATE users SET display_name=?,role=? WHERE id=?",(display.strip() or st.session_state.username,role,st.session_state.user_id)); conn.commit()
                settings.update({"department":department,"company":company}); save_settings(st.session_state.user_id,settings)
                st.session_state.display_name=display.strip() or st.session_state.username; st.session_state.role=role
                st.success("프로필을 저장했어요."); st.rerun()
        else:
            st.info("프로필을 수정하려면 먼저 로그인해 주세요.")

    with tabs[1]:
        st.subheader("보고서 설정")
        with st.form("report_settings_form"):
            fmt=st.selectbox("기본 보고서 형식",["PDF","Markdown"],index=["PDF","Markdown"].index(settings.get("report_format","PDF")))
            detail=st.selectbox("보고서 상세 수준",["요약","표준","상세"],index=["요약","표준","상세"].index(settings.get("report_detail","상세")))
            recommendations=st.checkbox("운영 개선 제안 포함",value=settings.get("include_recommendations",True))
            risks=st.checkbox("위험 요소 및 대응 방안 포함",value=settings.get("include_risks",True))
            if st.form_submit_button("보고서 설정 저장",type="primary"):
                settings.update({"report_format":fmt,"report_detail":detail,"include_recommendations":recommendations,"include_risks":risks})
                save_settings(st.session_state.user_id,settings)
                st.success("보고서 설정을 저장했어요." if st.session_state.logged_in else "로그인하지 않아 설정을 계정에 저장할 수 없어요. 로그인 후 다시 저장해 주세요.")
                if st.session_state.logged_in: st.rerun()

    with tabs[2]:
        st.subheader("화면 설정")
        with st.form("screen_settings_form"):
            theme=st.selectbox("테마",["라이트","다크"],index=["라이트","다크"].index(settings.get("theme","라이트")))
            compact=st.checkbox("간격을 좁게 표시",value=settings.get("compact",False))
            if st.form_submit_button("화면 설정 저장",type="primary"):
                settings.update({"theme":theme,"compact":compact}); save_settings(st.session_state.user_id,settings)
                st.success("화면 설정을 저장했어요. 테마와 간격 설정을 적용합니다." if st.session_state.logged_in else "로그인하지 않아 설정을 계정에 저장할 수 없어요. 로그인 후 다시 저장해 주세요.")
                if st.session_state.logged_in: st.rerun()

    with tabs[3]:
        st.subheader("AI 분석 설정")
        with st.form("ai_settings_form"):
            level=st.selectbox("분석 성향",["간결","균형","세부 분석"],index=["간결","균형","세부 분석"].index(settings.get("analysis_level","균형")))
            flow=st.checkbox("방문객 동선 관련 제안 포함",value=settings.get("audience_flow",True))
            access=st.checkbox("접근성 및 편의 사항 검토",value=settings.get("accessibility",True))
            notify=st.checkbox("생성 완료 안내 표시",value=settings.get("notifications",True))
            if st.form_submit_button("AI 분석 설정 저장",type="primary"):
                settings.update({"analysis_level":level,"audience_flow":flow,"accessibility":access,"notifications":notify})
                save_settings(st.session_state.user_id,settings)
                st.success("AI 분석 설정을 저장했어요. 다음 보고서 생성부터 반영됩니다." if st.session_state.logged_in else "로그인하지 않아 설정을 계정에 저장할 수 없어요. 로그인 후 다시 저장해 주세요.")
                if st.session_state.logged_in: st.rerun()

    with tabs[4]:
        st.subheader("프로젝트 및 저장 관리")
        if not st.session_state.logged_in:
            st.info("프로젝트 저장 및 목록 확인은 로그인 후 이용할 수 있습니다.")
        else:
            with db_connect() as conn:
                projects=conn.execute("SELECT id,project_name,created_at FROM projects WHERE user_id=? ORDER BY id DESC",(st.session_state.user_id,)).fetchall()
            st.write(f"저장된 프로젝트: **{len(projects)}개**")
            if projects:
                for p in projects:
                    c1,c2=st.columns([4,1])
                    c1.write(f"**{p['project_name']}**  ·  {p['created_at']}")
                    if c2.button("삭제",key=f"del_project_{p['id']}"):
                        with db_connect() as conn:
                            conn.execute("DELETE FROM projects WHERE id=? AND user_id=?",(p["id"],st.session_state.user_id)); conn.commit()
                        st.rerun()
                with db_connect() as conn:
                    rows=conn.execute("SELECT project_name,payload_json,created_at FROM projects WHERE user_id=? ORDER BY id DESC",(st.session_state.user_id,)).fetchall()
                export=[dict(name=r["project_name"],created_at=r["created_at"],data=json.loads(r["payload_json"])) for r in rows]
                st.download_button("전체 프로젝트 백업 다운로드 (JSON)",data=json.dumps(export,ensure_ascii=False,indent=2).encode("utf-8"),file_name="Event_ON_projects_backup.json",mime="application/json")
            else:
                st.caption("아직 저장된 프로젝트가 없습니다. 보고서를 생성하면 프로젝트가 자동 저장됩니다.")

    with tabs[5]:
        st.subheader("보안 및 계정 관리")
        if not st.session_state.logged_in:
            st.info("비밀번호 변경 및 계정 삭제는 로그인 후 이용할 수 있습니다.")
        else:
            with st.form("password_change_form"):
                current=st.text_input("현재 비밀번호",type="password")
                new1=st.text_input("새 비밀번호 (4자 이상)",type="password")
                new2=st.text_input("새 비밀번호 확인",type="password")
                change=st.form_submit_button("비밀번호 변경",type="primary")
            if change:
                user=authenticate(st.session_state.username,current) if current else None
                if not user: st.error("현재 비밀번호가 올바르지 않습니다.")
                elif len(new1)<4: st.error("새 비밀번호는 4자 이상이어야 합니다.")
                elif new1!=new2: st.error("새 비밀번호가 서로 일치하지 않습니다.")
                else:
                    salt,ph=hash_password(new1)
                    with db_connect() as conn:
                        conn.execute("UPDATE users SET salt=?,password_hash=? WHERE id=?",(salt,ph,st.session_state.user_id)); conn.commit()
                    st.success("비밀번호를 변경했어요.")
            st.divider()
            st.warning("계정 삭제 시 계정과 저장된 프로젝트가 삭제됩니다. 이 작업은 되돌릴 수 없습니다.")
            confirm=st.checkbox("계정을 영구 삭제하는 것에 동의합니다.",key="confirm_delete_account")
            if st.button("내 계정 삭제",type="secondary",disabled=not confirm,key="delete_account"):
                with db_connect() as conn:
                    conn.execute("DELETE FROM projects WHERE user_id=?",(st.session_state.user_id,))
                    conn.execute("DELETE FROM user_settings WHERE user_id=?",(st.session_state.user_id,))
                    conn.execute("DELETE FROM users WHERE id=?",(st.session_state.user_id,))
                    conn.commit()
                for k,v in {"logged_in":False,"user_id":None,"username":"","display_name":"","role":"","page":"홈"}.items(): st.session_state[k]=v
                st.success("계정과 연결된 프로젝트를 삭제했어요."); st.rerun()

def main():
    page=st.session_state.page
    st.markdown(build_all_css(page),unsafe_allow_html=True)
    with st.container(key='clean_nav'):
        _in=st.session_state.get('logged_in')
        _cols=st.columns([3,1,1.2,1.2,1,1.4,1.1] if _in else [3,1,1.2,1.2,1,1.5],vertical_alignment='center')
        a,b,c,d,e,f=_cols[:6]
        
        if a.button('Event ON',key='brand_home',use_container_width=False):go('홈');st.rerun()
        for col,label,route in [(b,'홈','홈'),(c,'대시보드','대시보드'),(d,'보고서','보고서'),(e,'설정','설정'),(f,'내 계정' if st.session_state.get('logged_in') else '로그인 / 가입','설정' if st.session_state.get('logged_in') else '로그인')]:
            if col.button(label,key='clean_nav_'+route,use_container_width=True):go(route);st.rerun()
        if _in:
            if _cols[6].button('로그아웃',key='clean_logout',use_container_width=True):
                for k,v in {'logged_in':False,'user_id':None,'username':'','display_name':'','role':'','page':'홈'}.items():st.session_state[k]=v
                st.rerun()
    if page=='홈':render_home()
    elif page=='대시보드':
        render_dashboard()
    elif page=='보고서':render_report()
    elif page=='설정':render_settings()
    elif page=='로그인':render_auth()
    else:render_home()



@st.dialog("로그인 / 회원가입", width="small")
def _render_auth_modal():
    st.markdown('<div class="auth-eyebrow">YOUR ACCOUNT</div>',unsafe_allow_html=True)
    login_tab,signup_tab=st.tabs(["로그인","회원가입"])
    with login_tab:
        with st.form("login_form"):
            username=st.text_input("아이디",placeholder="아이디를 입력하세요")
            password=st.text_input("비밀번호",type="password",placeholder="비밀번호")
            submitted=st.form_submit_button("로그인",type="primary",use_container_width=True)
        if submitted:
            user=authenticate(username,password) if username.strip() and password else None
            if user:
                st.session_state.logged_in=True; st.session_state.user_id=user["id"]; st.session_state.username=user["username"]
                st.session_state.display_name=user["display_name"]; st.session_state.role=user["role"]; st.session_state.page="홈"
                st.success("로그인했어요."); st.rerun()
            else: st.error("아이디 또는 비밀번호를 확인해 주세요.")
    with signup_tab:
        with st.form("signup_form"):
            username=st.text_input("아이디",placeholder="아이디를 입력하세요")
            display=st.text_input("표시 이름")
            role=st.text_input("역할",placeholder="예: 기획자, 팀장, 디자이너, 외부 협력사")
            pw1=st.text_input("비밀번호 (4자 이상)",type="password")
            pw2=st.text_input("비밀번호 확인",type="password")
            submitted=st.form_submit_button("회원가입",type="primary",use_container_width=True)
        if submitted:
            if not username.strip() or not display.strip() or not role.strip() or not pw1: st.error("모든 항목을 입력해 주세요.")
            elif len(username.strip())<3: st.error("아이디는 3자 이상이어야 합니다.")
            elif len(pw1)<4: st.error("비밀번호는 4자 이상이어야 합니다.")
            elif pw1!=pw2: st.error("비밀번호가 일치하지 않습니다.")
            else:
                ok,msg=create_user(username,display,role,pw1)
                (st.success if ok else st.error)(msg)

def render_auth():
    render_home()
    _render_auth_modal()


def linked_report(snapshot):
    c=snapshot.get('config',{}); fs=snapshot.get('facilities',[]); m=snapshot.get('metricsSummary',{}); x=snapshot.get('xaiReport',{})
    budget=float(c.get('budget',0))*1350; cost=sum(float(f.get('cost',0)) for f in fs)*1350
    lines=[f"# {c.get('eventName','행사')} 설계·운영 검토 보고서",f"작성 기준: {snapshot.get('updatedAt','미확인')} · 마지막 동기화 결과",'',
    '## 1. 행사 개요',f"- 행사 목적: {c.get('purpose') or '미입력'}",f"- 행사 유형: {', '.join(c.get('eventTypes',[])) or c.get('eventType','미입력')} (첫 유형을 주 유형으로 배치)",
    f"- 장소: {c.get('location') or '미입력'} / {c.get('venueType','미입력')}",f"- 운영시간: {c.get('startTime','미정')} ~ {c.get('endTime','미정')} (종료가 더 이르면 익일 종료)",f"- 예상 방문객: {c.get('expectedAttendance',0):,}명",f"- 분위기: {c.get('mood','미입력')} / 전 연령층: {'예' if c.get('allAges') else '아니오'}",f"- 배치 모형: {c.get('venueLayoutModel','standard')} / 출입구 요청: {c.get('entranceCount','미입력')}개 / 후보안: {c.get('candidateCount',4)}개",'',
    '## 2. 현재 설계 명세',f"- 행사장 외접 크기: {c.get('venueWidth',0):,.2f} × {c.get('venueDepth',0):,.2f}m",f"- 현재 시설 수: {len(fs)}개",f"- 시나리오: {snapshot.get('contingency','normal')} / 배치 모드: {snapshot.get('activeLayoutMode','original')}",'', '## 3. 예산 검토',f"- 입력 예산: {'미정' if c.get('budgetUnknown') else f'{budget/10000:,.1f}만 원'}",f"- 현재 시설 설치비 합계 (모델 추정): {cost/10000:,.1f}만 원"]
    if not c.get('budgetUnknown') and budget>0:
        lines += [f"- 예산 사용률: {cost/budget*100:,.1f}%",f"- 예산 대비 차액: {(budget-cost)/10000:,.1f}만 원",'- 검토 결과: '+('예산 초과 — 시설 규모·종류 또는 예산 재검토 필요.' if cost>budget else '시설비 합계는 입력 예산 이내. 전체 운영비 충족을 의미하지 않음.')]
    else: lines+=['- 예산 미정으로 예산 적합 여부를 판정하지 않습니다. 대시보드의 예산 점수는 임시 계산값이므로 사용하지 마세요.']
    lines+=['- 단가는 원본 모델의 USD 단위를 고정 환산계수 1,350원으로 환산한 가정값입니다. 실시간 환율·견적이 아닙니다. 인건비·보험·전력·철거 등의 포함 여부를 별도 확인해야 합니다.','', '## 4. 현재 분석 결과 (가정 기반)']
    for key,label,unit in [('venueAreaSqm','부지 면적','m²'),('usableAreaSqm','보행·체류 가용 면적','m²'),('referenceCapacity','모델 참고 수용량','명'),('peakDensity','모의 피크 밀집도','명/m²'),('avgWaitMinutes','모의 평균 대기시간','분'),('avgWalkDistance','모의 평균 보행거리','m')]:
        value=m.get(key);lines.append(f"- {label}: {value if value is not None else '미산출'} {unit if value is not None else ''}")
    for k,v in m.get('scores',{}).items():
        if k=='budget' and c.get('budgetUnknown'):continue
        lines.append(f'- 모델 평가점수 {k}: {v}/100 (안전 인증 점수 아님)')
    lines+=['','## 5. 설명 가능한 설계 근거']
    if x.get('executiveSummary'):lines.append(str(x['executiveSummary']))
    for v in x.get('placementRationales',[]):lines.append('- '+str(v))
    lines+=['','## 6. 사용자 요청 부스와 배치 명세']
    for r in c.get('customElements',[]):lines.append(f"- 요청: {r.get('nameKo','')} / {r.get('category')} / {r.get('width')} × {r.get('depth')}m / {r.get('count')}개")
    for f in fs:
        p=f.get('position',{});d=f.get('dimensions',{});lines.append(f"- 배치: {f.get('nameKo') or f.get('name','시설')} / {f.get('category')} / 중심 X {p.get('x')} · Z {p.get('z')}m / {d.get('width')} × {d.get('depth')} × {d.get('height')}m / 모델 정원 {f.get('capacity','미산출')}명 / 추정 시설비 {float(f.get('cost',0))*1350/10000:,.1f}만원")
    lines+=['','## 7. 운영 전 확인사항 및 한계','- 현장 도면과 좌표를 대조하여 시설 겹침·외곽 이탈·대기줄 점유·비상 동선을 확인하세요. 요청한 부스 수와 실제 배치 수가 다른 경우 공간 제약 및 배치 결과를 검토하세요.','- 의료 진입, 안내 인력, 장애인 접근, 전기·화재 대책 및 실제 견적을 현장 전문가와 검토하세요.','- 수치는 실측이 아닌 모델 가정 기반 시나리오 결과입니다. 실제 군중 행동·대기시간·피난시간을 보증하지 않으며 법령 적합성이나 안전 인증을 의미하지 않습니다.','- 본 보고서는 현재 설계 데이터를 정리한 규칙 기반 보고서입니다. 외부 생성형 AI API는 이 Streamlit 배포본에 연결되지 않았습니다.','- 원본 대시보드에 수록된 문헌·기준·설계 근거는 별도 원문 검증 전 참고자료로만 사용하세요.']
    return '\n'.join(lines)

# Superseded by standard document renderer below.

def render_dashboard():
    import streamlit.components.v1 as native

    component=native.declare_component('eventon_designer_fullzip',path=str(_DIST))
    value=component(controls=st.session_state.get('dashboard_controls',{'deviceMode':'laptop','dragMode':'rotate'}),saved=st.session_state.get('dashboard_snapshot'),key='eventon_live_designer_fullzip_'+str(st.session_state.get('dashboard_entry_version',0)),default=None)
    if isinstance(value,dict) and isinstance(value.get('config'),dict) and isinstance(value.get('facilities'),list):
        st.session_state.dashboard_snapshot=value
        st.caption('보고서 반영 시각: '+str(value.get('updatedAt','미확인')))




_basic_linked_report=linked_report

def report_findings(snapshot):
    from collections import Counter
    c=snapshot.get('config',{});fs=snapshot.get('facilities',[]);findings=[]
    cost=sum(float(f.get('cost',0)) for f in fs)*1350
    budget=float(c.get('budget',0))*1350
    if not c.get('budgetUnknown') and budget>0 and cost>budget:
        findings.append(('최우선','예산 초과',f'시설비 추정액 {cost/10000:,.1f}만원이 예산 {budget/10000:,.1f}만원보다 {(cost-budget)/10000:,.1f}만원 높음','시설·운영 담당','필수 기능을 유지하면서 선택 시설의 규격·수량을 조정하고 실제 견적 및 누락 운영비를 확보','재배치 후 비용 재계산 및 견적 대조'))
    counts=Counter(f.get('category') for f in fs)
    for key,label in [('entrance','출입구'),('medical','의료지원'),('restroom','화장실')]:
        if not counts[key]:findings.append(('우선 검토',label+' 시설 미배치','현재 배치 목록에서 해당 분류를 찾지 못함','설계·운영 담당','현장 제공 시설 존재 여부 확인 후 필요 시설과 접근 경로 반영','현장 도면과 운영계획 대조'))
    for r in c.get('customElements',[]):
        name=r.get('nameKo','');actual=sum(1 for f in fs if name and name in str(f.get('nameKo') or f.get('name','')))
        if actual!=r.get('count'):findings.append(('확인 필요','요청 부스 수량 대조',f"{name}: 요청 {r.get('count')}개, 이름 포함 매칭 {actual}개 (자동 이름 매칭은 오탐 가능)",'시설 담당','시설 ID·이름·크기와 공간 제약을 대조','요청 목록과 배치 명세 수동 대조'))
    return findings

def linked_report(snapshot):
    from collections import Counter
    c=snapshot.get('config',{});fs=snapshot.get('facilities',[]);m=snapshot.get('metricsSummary',{})
    findings=report_findings(snapshot)
    text=_basic_linked_report(snapshot)
    # Place decision summary and provenance before the details.
    intro=['## 검토 요약 및 의사결정','- 결론: 현장 적용 승인 여부는 판정 보류. 현재 보고서는 설계안 검토용이며 실측·견적·운영계획 확인이 필요합니다.',f'- 현재 자동 대조에서 확인한 검토 항목: {len(findings)}건. 0건이어도 안전·적합성을 의미하지 않습니다.','- 예상 방문객 입력은 누적 방문객인지 동시 재실 인원인지 명시되지 않았습니다. 재실 인원·시간대별 입퇴장 자료를 확보하기 전 실제 혼잡 예측으로 사용하지 마세요.','','## 자료 출처·가정·검증 범위','- 사용자 입력: 행사명·목적·방문객·예산·장소 조건. 현장 실측 또는 독립 검증된 사실로 간주하지 않습니다.','- 모델 출력 (ASSUMPTION): 시설 좌표·단가·참고 정원·혼잡·대기 및 점수. 단가와 시뮬레이션은 실제 견적·관측 기록과 대조 전입니다.','- 미확인 (MISSING): 실측 부지 경계·통로 유효폭·경사·시설 처리량·실제 견적·운영 인력·교통 연계 용량. 값이 없다고 양호로 판정하지 않습니다.','- 참고자료: 사용자 제공 「AI 행사장 자동 설계·분석: 실제 자료 기반 지식 데이터베이스 구축 가이드」 2·5·7~12쪽과 「행사장 설계와 군중 안전 원문 검토 및 국내외 행사 분석」 2·6쪽의 자료 구분·검증 한계 원칙을 보고서 구조에 반영했습니다. 논문 원문 재검증이나 모델 추가 학습을 수행했다는 의미는 아닙니다.','- 참고자료의 법령·사례 수치나 타 행사 성능을 이 행사의 적용 기준·검증 성능으로 전용하지 않았습니다.','']
    parts=text.split('\n',1);text=parts[0]+'\n\n'+'\n'.join(intro)+'\n'+(parts[1] if len(parts)>1 else '')
    text+='\n\n## 8. 문제점·개선 조치·재검증 계획\n'
    if findings:
        for i,(priority,title,evidence,owner,action,verify) in enumerate(findings,1):
            text+=f'\n### {i}. [{priority}] {title}\n- 근거: {evidence}\n- 제안 담당 역할 (미지정): {owner}\n- 개선 조치: {action}\n- 확인 방법: {verify}\n- 상태: 미확인·조치 전. 완료 기한과 실제 책임자는 운영자가 지정해야 합니다.\n'
    else:text+='- 현재 자동 대조에서 추가 항목이 검출되지 않았습니다. 공간·동선·안전 전반을 검사한 결과는 아닙니다.\n'
    text+='\n## 9. 시설 구성 및 비용 집중도\n'
    counts=Counter(f.get('category','미분류') for f in fs)
    for k,n in sorted(counts.items()):
        total=sum(float(f.get('cost',0)) for f in fs if f.get('category','미분류')==k)*1350
        text+=f'- {k}: {n}개 / 가정 기반 시설비 {total/10000:,.1f}만원\n'
    text+='\n## 10. 운영 단계별 점검 계획 (실행안 초안)\n- 개최 전: 실측 경계와 시설 배치를 대조하고 출입·의료 접근·접근성 경로를 현장에서 확인합니다. 미해결 항목의 담당자와 완료 여부를 기록합니다.\n- 입장 피크: 구역별 입장·퇴장·재실 인원과 대기줄 위치를 관찰하고, 실제 운영계획에 따른 유입 조절·안내 절차를 확인합니다. 특정 밀도 한 값으로 안전 여부를 단정하지 않습니다.\n- 프로그램 전환: 인기 시설의 체류와 교차 흐름을 함께 관찰하고, 대기 공간이 통로를 침범하면 배치·운영 방식을 재검토합니다.\n- 종료 직후: 행사장 출구뿐 아니라 외부 역·정류장·주차장으로 이어지는 대기 공간과 이동 연결부도 확인합니다.\n- 행사 후: 예측과 실제 방문·대기·비용 차이를 같은 단위·시간 구간으로 비교하고, 근거 자료와 수정 이력을 다음 설계에 반영합니다.\n'
    return text


# Enterprise reporting: numerical evidence stays in Python, narration via Gemini is optional.
_previous_default_settings=default_settings
_previous_render_settings=render_settings

def default_settings():
    return {**_previous_default_settings(),'report_audience':'팀장','report_style':'~함 / ~임','report_template':'','report_reference':''}

def enterprise_settings():
    return {**get_settings(st.session_state.user_id),**st.session_state.get('guest_report_settings',{})} if not st.session_state.user_id else get_settings(st.session_state.user_id)

def report_settings_form():
    cfg=enterprise_settings()
    st.caption('계정별 작성 설정임. 회사 전체 공유 양식은 아님. 참고 예시는 개인정보·영업비밀을 제거한 텍스트만 입력하세요.')
    with st.form('enterprise_report_settings'):
        audience=st.text_input('보고 대상',cfg.get('report_audience','팀장'),max_chars=100)
        style=st.text_input('문체',cfg.get('report_style','~함 / ~임'),max_chars=100)
        template=st.text_area('회사별 목차·작성 규칙',cfg.get('report_template',''),max_chars=12000)
        reference=st.text_area('비식별 승인 보고서 예시',cfg.get('report_reference',''),max_chars=18000)
        if st.form_submit_button('기업 보고서 작성 설정 저장'):
            cfg.update(report_audience=audience,report_style=style,report_template=template,report_reference=reference)
            if st.session_state.user_id:save_settings(st.session_state.user_id,cfg)
            else:st.session_state.guest_report_settings=cfg
            st.success('계정에 저장함.' if st.session_state.user_id else '현재 세션에 저장함. 영구 저장은 로그인 필요함.')

def render_settings():
    _previous_render_settings()
    st.divider()
    st.subheader('대시보드 조작 설정')
    prefs=st.session_state.get('dashboard_controls',{'deviceMode':'laptop','dragMode':'rotate'})
    mode=st.radio('기기 모드',['노트북','태블릿·펜'],index=0 if prefs.get('deviceMode')=='laptop' else 1,horizontal=True,key='dashboard_device_setting')
    drag=st.radio('마우스 드래그 동작',['회전','이동'],index=0 if prefs.get('dragMode')=='rotate' else 1,horizontal=True,key='dashboard_drag_setting')
    st.session_state.dashboard_controls={'deviceMode':'laptop' if mode=='노트북' else 'tablet','dragMode':'rotate' if drag=='회전' else 'pan'}
    st.caption('대시보드로 돌아가면 적용됩니다. 노트북: WASD·방향키로 선택 시설 이동, 마우스로 회전/이동. 태블릿: 터치·펜 조작.')
    # Enterprise authoring settings section removed as requested.

# External narrative connection removed.

def report_fingerprint(snapshot,settings):
    import hashlib
    # Exclude clock-only metadata, but retain actual changing metrics.
    data={k:v for k,v in snapshot.items() if k!='updatedAt'}
    opts={k:settings.get(k) for k in ['report_audience','report_style','report_template','report_reference']}
    return hashlib.sha256(json.dumps([data,opts],ensure_ascii=False,sort_keys=True,default=str).encode()).hexdigest()

REPORT_SECTIONS=['보고 요약','행사 추진 개요','행사장 설계안','예산 검토','분석 결과 및 해석','운영 위험 및 보완 계획','종합 검토 및 요청사항']

# External narrative connection removed.

def enterprise_report(snapshot,settings,narrative=None):
    c=snapshot.get('config',{});fs=snapshot.get('facilities',[]);m=snapshot.get('metricsSummary',{})
    def clean(v):return str(v).replace('|','／').replace('\n',' ')
    def table(rows):return '\n'.join(['|항목|값·근거|','|---|---|']+[f'|{clean(k)}|{clean(v)}|' for k,v in rows])
    budget=float(c.get('budget',0))*1350;cost=sum(float(f.get('cost',0)) for f in fs)*1350
    findings=report_findings(snapshot)
    out=[f"# {clean(c.get('eventName','행사'))} 행사 설계·운영 검토 보고서",f"보고 대상: {clean(settings.get('report_audience','팀장'))}",f"동기화 기준: {clean(snapshot.get('updatedAt','확인 필요'))}",'작성 구분: '+('AI 서술 + Python 기준 수치' if narrative else '규칙 기반 검토 초안'), '']
    defaults=[ '가. 검토 목적: 현재 설계안의 예산·시설·모의 분석을 검토함.\n나. 핵심 검토 결과: '+('추가 보완 사항이 확인됨.' if findings else '자동 대조에서 추가 항목이 검출되지 않았으나 현장 검증은 미완료임.')+'\n다. 결정 요청: 현장 조사·실제 견적 확보 및 미해결 조치 담당 지정 여부를 요청함.',
    '행사 목적 및 대상은 입력 자료를 기준으로 확인함. 누적 방문객과 동시 재실 인원 구분은 확인 필요함.',
    '배치 명세를 기준으로 시설 구성을 검토함. 이동·대기 동선의 실제 유효폭 및 비상 접근은 현장 확인 필요함.',
    ('모델 시설비가 입력 예산을 초과하여 시설 범위 또는 예산 재검토가 필요함.' if cost>budget and not c.get('budgetUnknown') else '실제 견적과 비용 포함 범위를 추가 확인해야 함.')+' 모델 시설비는 전체 행사 운영비가 아님.',
    '밀집도·대기·보행 지표는 모의 분석값임. 실측·안전 인증 또는 실제 피난 성능을 의미하지 않음.',
    '가. 문제·점검사항: 아래 자동 대조 항목 및 현장 조건을 확인해야 함.\n나. 조치: 예산·시설·동선 검토 후 재배치 및 재계산함.\n다. 담당자: 지정 필요. 조치 기한: 지정 필요.',
    '현 단계에서 현장 적용 승인 여부는 판단 보류함. 실측·견적·운영 인력·관계기관 검토가 확인된 뒤 설계를 확정하도록 요청함.']
    for i,title in enumerate(REPORT_SECTIONS,1):
        out += [f'## {i}. {title}',narrative.get(f's{i}',defaults[i-1]) if narrative else defaults[i-1]]
        if i==2:out += [table([('행사명 [입력]',c.get('eventName','미정')),('목적 [입력]',c.get('purpose','확인 필요')),('장소 [입력]',c.get('location','확인 필요')),('시간 [입력]',f"{c.get('startTime','미정')} ~ {c.get('endTime','미정')}"),('예상 방문객 [입력]',f"{c.get('expectedAttendance','확인 필요')}명"),('가로 × 세로 [입력]',f"{c.get('venueWidth','?')} × {c.get('venueDepth','?')}m")])]
        if i==3:out += [table([('현재 배치 시설 수 [계산]',len(fs)),('배치 모드',snapshot.get('activeLayoutMode','확인 필요')),('조건',snapshot.get('contingency','normal'))])]
        if i==4:out += [table([('입력 예산','미정' if c.get('budgetUnknown') else f'{budget:,.0f}원'),('시설비 합계 [모델 가정]',f'{cost:,.0f}원'),('예산 사용률','판정 보류' if c.get('budgetUnknown') or budget<=0 else f'{cost/budget*100:,.2f}%'),('환산 계수 [고정 가정]','1 USD = 1,350원. 실시간 환율·실제 견적 아님'),('미포함·포함 미확인 비용','인건비·보험·세금·운송·전력·설치·철거·허가 비용 확인 필요')])]
        if i==5:out += [table([(k+' [모델·모의]',m.get(k,'미산출')) for k in ['peakDensity','avgWaitMinutes','avgWalkDistance','venueAreaSqm','usableAreaSqm','referenceCapacity']])]
        if i==6:
            for row in findings:out.append('- '+clean(row[1])+': '+clean(row[2])+' / 제안 조치: '+clean(row[4])+' / 담당자·기한: 지정 필요')
        out.append('')
    out+=['## 별첨 — 전체 시설 배치 명세',table([(f.get('nameKo') or f.get('name','시설'),json.dumps({'id':f.get('id'),'position':f.get('position'),'dimensions':f.get('dimensions'),'cost_USD_model':f.get('cost')},ensure_ascii=False)) for f in fs]),'## 별첨 — 분석 지표 상세',table([(k,json.dumps(v,ensure_ascii=False)) for k,v in m.items()]),'## 별첨 — 비용 산출 기준 및 가정','- 시설비는 배치 객체별 모델 비용 합계에 고정 환산계수를 곱한 값임. 견적·정산·현장 계측값과 대조 전임.','- 입력 자료·참고 문서의 내용은 데이터임. 수록 문헌·법령 적용 여부를 독립 검증한 보고서가 아님.','- 회사 목차 요청은 AI 서술 참고에 활용하되 수치 검증용 공통 목차·별첨은 유지함. 자동 검사 통과도 사실 정확성 보증은 아니므로 제출 전 검토 필요함.']
    return '\n\n'.join(out)

# Superseded by standard document renderer below.

st.markdown('\n<style>\n[data-testid="stSidebar"]{background:#15253e!important;border-right:1px solid #263b59!important}\n[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p{color:#c3cfe0!important}\n[data-testid="stSidebar"] .brand-link{color:#ffffff!important;padding:12px 0 8px;font-size:30px;letter-spacing:-1.3px}\n[data-testid="stSidebar"] .brand-link span{color:#8eb5ff!important}\n[data-testid="stSidebar"] .brand-sub{color:#a9bbd4!important;font-size:10px;letter-spacing:1.7px}\n[data-testid="stSidebar"] .sidebar-label{color:#93aac9!important;letter-spacing:1.7px;font-size:10px;margin-top:28px;margin-bottom:10px}\n[data-testid="stSidebar"] div.stButton>button{background:#1d314e!important;border:1px solid #2d4464!important;color:#e1e9f7!important;border-radius:10px;min-height:46px;box-shadow:none!important;margin:3px 0}\n[data-testid="stSidebar"] div.stButton>button :is(p,span,div){color:#e1e9f7!important}\n[data-testid="stSidebar"] div.stButton>button:hover{background:#2b4466!important;border-color:#759bcb!important}\n[data-testid="stSidebar"] div.stButton>button[kind="primary"]{background:#dce9ff!important;border-color:#dce9ff!important;box-shadow:inset 4px 0 #477de1!important}\n[data-testid="stSidebar"] div.stButton>button[kind="primary"] :is(p,span,div){color:#173962!important}\n[data-testid="stSidebar"] .sidebar-user{background:#203650;border-color:#354d6b}\n[data-testid="stSidebar"] .sidebar-user-name{color:#fff!important}\n.hero{background:#edf3fb;border:1px solid #dce5f1;border-left:5px solid #4379d8;border-radius:20px;padding:clamp(24px,4vw,48px);box-shadow:none}\n.hero h1{font-size:clamp(30px,4vw,48px);letter-spacing:-1.8px;line-height:1.25;margin:18px 0;color:#152d4c}\n.hero p{font-size:15px;line-height:1.9;color:#536780}\n.eyebrow{font-size:11px;letter-spacing:1.8px;color:#3766ac}\n.home-flow{margin-top:28px;padding-top:18px;border-top:1px solid #d3dfee;color:#46648b;font-size:12px;line-height:2;overflow-wrap:anywhere}\n.feature-card{box-sizing:border-box;min-height:278px;padding:28px;border:1px solid #dce5f1;border-radius:18px;background:#fff;box-shadow:0 8px 24px #17365108;display:flex;flex-direction:column}\n.feature-icon{border-radius:12px;background:#edf3fb;color:#3767ad;width:44px;height:44px;margin-bottom:16px}\n.card-kicker{font-size:10px;letter-spacing:1.5px;color:#647e9e;margin-bottom:8px;font-weight:700}\n.feature-card h3{font-size:23px;letter-spacing:-.7px;margin-bottom:12px}\n.feature-card p{font-size:14px;line-height:1.8;color:#61738a;margin:0}\n@media(max-width:640px){.feature-card{min-height:250px;padding:22px}.hero h1{letter-spacing:-1px}.home-flow{font-size:11px}}\n</style>\n', unsafe_allow_html=True)

st.markdown('<style>\n/* Account dialog only: the embedded design workspace is untouched. */\n[data-testid="stDialog"] [role="dialog"]{width:calc(100% - 32px)!important;max-width:460px!important;border:1px solid #dce5f2!important;border-radius:22px!important;box-shadow:0 28px 90px #10244245!important;background:#fff!important;color:#172b4d!important;padding:8px!important}\n[data-testid="stDialog"]::backdrop,div[data-baseweb="modal"]::backdrop{background:rgba(18,32,53,.40)!important;backdrop-filter:blur(5px)}\ndiv[data-baseweb="modal"]{backdrop-filter:blur(5px);background-color:rgba(18,32,53,.34)!important}\n[data-testid="stDialog"] h3{font-size:23px!important;letter-spacing:-.7px;margin-bottom:4px!important;color:#172b4d!important}\n[data-testid="stDialog"] [data-testid="stForm"]{padding:16px!important;border:1px solid #e2e9f3!important;border-radius:14px!important;background:#f9fbfe!important}\n[data-testid="stDialog"] [data-baseweb="tab-list"]{gap:20px!important}\n[data-testid="stDialog"] [data-baseweb="tab-highlight"]{background:#386aca!important}\n[data-testid="stDialog"] [aria-selected="true"]{color:#2859b5!important;font-weight:750!important}\n[data-testid="stDialog"] [data-testid="stFormSubmitButton"] button{background:#315fae!important;border:1px solid #315fae!important;color:white!important;min-height:44px;border-radius:10px}\n[data-testid="stDialog"] [data-testid="stFormSubmitButton"] button p{color:white!important}\n[data-testid="stDialog"] input{background:#fff!important;color:#172b4d!important}\n[data-testid="stDialog"] label p{color:#405575!important;font-size:13px!important}\n[data-testid="stDialog"] [data-testid="stVerticalBlock"]{gap:12px}\n</style>',unsafe_allow_html=True)

st.markdown('<style>\n[data-testid="stDialog"] [role="dialog"]{max-width:560px!important;border-radius:26px!important;padding:16px!important;max-height:calc(100dvh - 32px)!important;overflow-y:auto!important}\n[data-testid="stDialog"] [data-testid="stDialogContainer"]{max-height:calc(100dvh - 32px);overflow-y:auto}\n[data-testid="stDialog"] h2{font-size:26px!important;color:#182d50!important;letter-spacing:-.8px}\n.auth-eyebrow{font-size:12px;font-weight:800;letter-spacing:2px;color:#3b60ff;margin:0 0 8px}\n[data-testid="stDialog"] [data-baseweb="tab-list"]{display:flex!important;gap:0!important;border-bottom:1px solid #e6ecf5}\n[data-testid="stDialog"] [data-baseweb="tab"]{flex:1!important;justify-content:center!important;font-size:17px!important;min-height:52px;font-weight:750;color:#8a9ebd}\n[data-testid="stDialog"] [data-baseweb="tab-highlight"]{background:#365cff!important;height:3px!important}\n[data-testid="stDialog"] [data-testid="stForm"]{background:transparent!important;border:0!important;padding:14px 0 0!important;box-shadow:none!important}\n[data-testid="stDialog"] [data-baseweb="input"]{border:1px solid #dce4f2!important;border-radius:14px!important;background:white!important;min-height:51px}\n[data-testid="stDialog"] input{min-height:48px!important;font-size:16px!important;padding-left:14px!important}\n[data-testid="stDialog"] label p{font-size:14px!important;font-weight:700!important;color:#344966!important}\n[data-testid="stDialog"] [data-testid="stFormSubmitButton"] button{background:#3159ef!important;border-color:#3159ef!important;border-radius:14px!important;min-height:52px!important;box-shadow:0 3px 6px #234bcc20!important;margin-top:8px}\n[data-testid="stDialog"] [data-testid="stFormSubmitButton"] button p{font-size:17px!important;font-weight:750!important}\n[data-testid="stSidebarUserContent"]> [data-testid="stVerticalBlock"]{display:flex!important;flex-direction:column!important;min-height:calc(100dvh - 4rem)!important}\n[data-testid="stSidebarUserContent"] [data-testid="stVerticalBlock"]:has(> .st-key-sidebar_account){display:flex!important;flex-direction:column!important;min-height:calc(100dvh - 4rem)!important}\n.st-key-sidebar_account{margin-top:auto!important;border-top:1px solid #3b4e69;padding-top:12px!important;padding-bottom:8px!important}\n@media(max-width:600px){[data-testid="stDialog"] [role="dialog"]{padding:8px!important;border-radius:22px!important;width:calc(100% - 24px)!important}}\n</style>',unsafe_allow_html=True)

st.markdown('<style>\n:root{--eo-ink:#142843;--eo-blue:#315eea;--eo-muted:#60718a;--eo-line:#e0e7f1}\n.stApp{background:#f5f7fb!important;color:var(--eo-ink)}\n.block-container{max-width:1460px!important;padding:2rem 3rem 3.5rem!important}\nh1,h2,h3,h4{letter-spacing:-.035em}h2{font-size:26px!important}h3{font-size:21px!important}\n[data-testid="stSidebar"]{background:linear-gradient(180deg,#0b1529,#142641)!important;border-right:1px solid #263852!important}\n[data-testid="stSidebar"] .brand-link{font-size:32px!important;font-weight:900!important;letter-spacing:-1.6px;padding:12px 8px!important}\n[data-testid="stSidebar"] .brand-link span{color:#8aaeff!important}\n[data-testid="stSidebar"] .brand-sub{font-size:9px!important;letter-spacing:1.8px!important;margin-left:8px;color:#a3b5d1!important}\n[data-testid="stSidebar"] .sidebar-label{font-size:10px!important;letter-spacing:2px!important;color:#a1b2ce!important;margin:26px 10px 10px!important}\n[data-testid="stSidebar"] div.stButton>button{border:0!important;border-radius:11px!important;background:transparent!important;box-shadow:none!important;min-height:48px!important;margin:3px 0!important;padding:10px 16px!important}\n[data-testid="stSidebar"] div.stButton>button :is(p,span,div){color:#d5deee!important;font-size:14px!important}\n[data-testid="stSidebar"] div.stButton>button:hover{background:#243956!important}\n[data-testid="stSidebar"] div.stButton>button[kind="primary"]{background:#e7efff!important;box-shadow:inset 3px 0 #5f89ff!important}\n[data-testid="stSidebar"] div.stButton>button[kind="primary"] :is(p,span,div){color:#2147b5!important}\n.st-key-sidebar_account{margin-top:auto!important;border-top:1px solid #36465e;padding-top:16px!important}\n[data-testid="stMain"] button{border-radius:11px!important;transition:background .15s,box-shadow .15s}\n[data-testid="stMain"] button[kind="primary"]{background:#315eea!important;border:1px solid #315eea!important;color:white!important;min-height:46px!important;box-shadow:0 4px 10px #315eea18!important}\n[data-testid="stMain"] button[kind="primary"] p{color:white!important}\n[data-testid="stMain"] [data-testid="stForm"]{border:1px solid var(--eo-line)!important;border-radius:18px!important;padding:24px!important;background:#fff}\n[data-testid="stMain"] [data-baseweb="input"],[data-testid="stMain"] [data-baseweb="select"]>div{border-radius:10px!important}\n[data-testid="stMain"] [data-testid="stMetric"]{background:white;border:1px solid var(--eo-line);border-radius:16px;padding:18px}\n[data-testid="stMain"] [data-testid="stExpander"]{border:1px solid var(--eo-line);border-radius:14px;background:#fff}\n[data-testid="stMain"] [data-baseweb="tab-list"]{gap:12px;border-bottom:1px solid var(--eo-line);flex-wrap:wrap}\n[data-testid="stMain"] [data-baseweb="tab"]{font-weight:700;padding:12px 5px}\n[data-testid="stMain"] [data-baseweb="tab-highlight"]{background:#315eea}\n.eo-top{display:flex;justify-content:space-between;gap:14px;align-items:center;margin:0 0 24px;padding-bottom:20px;border-bottom:1px solid var(--eo-line);font-size:10px;letter-spacing:1.5px;color:#61728c}\n.eo-pill{background:#e9efff;color:#3558b1;padding:7px 12px;border-radius:50px;font-size:11px;letter-spacing:0}\n.eo-hero{background:linear-gradient(120deg,#10284c,#1e4382);padding:46px;border-radius:24px;display:grid;grid-template-columns:1.25fr 1fr;gap:32px;align-items:center;color:white;overflow:hidden}\n.eo-kicker{font-size:10px;letter-spacing:1.8px;font-weight:800;color:#54729e}\n.eo-hero .eo-kicker{color:#a8c3ff}.eo-hero h1{color:white!important;font-size:clamp(32px,3.8vw,52px)!important;line-height:1.2;margin:20px 0!important;letter-spacing:-2px!important}\n.eo-hero p{color:#d6e3f8!important;font-size:14px;line-height:1.9;margin-bottom:25px}\n.eo-tags{display:flex;gap:8px;flex-wrap:wrap}.eo-tags span{font-size:10px;border:1px solid #6882a9;border-radius:6px;padding:6px 9px;color:#e1eaff}\n.eo-map{background:linear-gradient(#ffffff09 1px,transparent 1px),linear-gradient(90deg,#ffffff09 1px,transparent 1px),#193967;background-size:22px 22px;border:1px solid #6384b8;border-radius:16px;padding:22px;transform:rotate(-4deg);box-shadow:0 18px 38px #04132c55}\n.eo-map-title{font-size:9px;letter-spacing:1.4px;color:#bad0f1;margin-bottom:20px}.eo-stage{text-align:center;background:#dce8ff;color:#214679;padding:15px;border-radius:7px;font-size:10px;letter-spacing:3px;font-weight:800;margin:0 28px 22px}.eo-booths{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}.eo-booths i{display:block;text-align:center;padding:14px 8px;background:#3b6097;border:1px solid #88a9df;border-radius:5px;color:#e6efff;font-size:10px;font-style:normal}.eo-route{font-size:8px;letter-spacing:1px;text-align:center;color:#bed5fc;margin-top:23px}.eo-visual-note{font-size:9px;color:#c1d2eb;text-align:center;margin-top:23px}\n.st-key-eo_hero_actions{margin:18px 0 22px!important}\n.eo-current{display:flex;justify-content:space-between;align-items:center;gap:14px;border:1px solid var(--eo-line);border-radius:14px;background:white;padding:18px 22px;margin:0 0 34px}.eo-current strong{display:block;font-size:16px;margin-top:7px;overflow-wrap:anywhere}.eo-state{font-size:11px;color:#536d94;background:#edf3fc;padding:8px 11px;border-radius:8px;flex-shrink:0}\n.eo-section{display:flex;justify-content:space-between;align-items:center;gap:12px;margin:34px 0 18px}.eo-section h2{font-size:23px!important;margin:0!important;padding:0!important;color:#172e4d}.eo-section>span{font-size:11px;color:#63738c}\n.eo-card{height:270px;background:white;border:1px solid var(--eo-line);border-radius:18px;padding:25px;display:flex;flex-direction:column}.eo-card-top{display:flex;align-items:center;justify-content:space-between;gap:12px;color:#6b7e9b;font-size:10px;letter-spacing:1px}.eo-icon{display:flex;align-items:center;justify-content:center;width:43px;height:43px;background:#eef3ff;color:#315eea;border-radius:12px;font-size:23px}.eo-card h3{font-size:23px!important;margin:20px 0 10px!important;padding:0!important}.eo-card p{font-size:13px;line-height:1.8;color:#60718a;max-width:460px;margin:0}.eo-card-foot{margin-top:auto;padding-top:14px;border-top:1px solid #edf1f7;font-size:10px;color:#667a99}\n.eo-process{display:grid;grid-template-columns:repeat(3,1fr);border:1px solid var(--eo-line);border-radius:18px;overflow:hidden;background:white}.eo-process>div{padding:24px;border-right:1px solid #e5ebf5}.eo-process>div:last-child{border:0}.eo-process b{font-size:12px;color:#315eea}.eo-process h4{font-size:16px!important;margin:14px 0 8px!important;padding:0!important}.eo-process p{font-size:12px;color:#60718a;line-height:1.8;margin:0}\n.eo-footer{border-top:1px solid var(--eo-line);margin-top:40px;padding-top:23px;color:#62738d}.eo-footer strong{font-size:17px;color:#2a4264}.eo-footer span{font-size:9px;letter-spacing:1.4px;margin-left:14px}.eo-footer p{font-size:10px;line-height:1.8;margin-top:10px}\n[data-testid="stDialog"] [role="dialog"]{border:1px solid #dce5f4!important;border-radius:22px!important;padding:22px!important;max-width:480px!important;box-shadow:0 24px 100px #091b3e40!important}\n[data-testid="stDialog"] [data-testid="stForm"]{padding:8px 0!important;border:0!important}\n[data-testid="stDialog"] [data-testid="stFormSubmitButton"] button{background:#315eea!important;border-color:#315eea!important;min-height:48px!important}\n@media(max-width:1100px){.eo-hero{padding:30px;gap:24px}.eo-card{height:290px}.block-container{padding:1.5rem 1.7rem 3rem!important}}\n@media(max-width:760px){.eo-hero{grid-template-columns:1fr;padding:27px}.eo-visual{max-width:360px;width:100%;margin:12px auto 0}.eo-hero h1{font-size:36px!important}.eo-process{grid-template-columns:1fr}.eo-process>div{border-right:0;border-bottom:1px solid var(--eo-line)}.eo-current{align-items:flex-start;flex-direction:column}.eo-section{align-items:flex-start;flex-direction:column}.eo-card{height:auto;min-height:270px}.eo-top{font-size:9px}.block-container{padding:1.3rem 1rem 2.5rem!important}}\n</style>',unsafe_allow_html=True)

PREMIUM_HOME_CSS = _load_asset("PREMIUM_HOME_CSS.txt")

CLEAN_SLIDE_ONE = _load_asset("CLEAN_SLIDE_ONE.txt")
CLEAN_SLIDE_TWO = _load_asset("CLEAN_SLIDE_TWO.txt")
CLEAN_GLOBAL_CSS='<style>\n[data-testid="stSidebar"],[data-testid="stSidebarCollapsedControl"],header[data-testid="stHeader"]{display:none!important}\n.block-container{width:100%!important;max-width:none!important;padding:86px 24px 24px!important}\n.st-key-clean_nav{position:fixed!important;top:0;left:0;right:0;z-index:900;background:#fff;border-bottom:1px solid #e4e8ef;padding:14px 4%!important;min-height:72px}\n.clean-logo{font-size:27px;font-weight:850;letter-spacing:-1px;color:#20324b}.clean-logo b{color:#327ad0}\n.st-key-clean_nav button{background:transparent!important;border:0!important;box-shadow:none!important;padding:8px 3px!important;min-height:36px!important}.st-key-clean_nav button p{font-size:12px!important;color:#344762!important}\n[data-testid="stMain"] iframe{width:100%!important;max-width:none!important}\n@media(max-width:640px){.block-container{padding:110px 10px 20px!important}.st-key-clean_nav{padding:8px 12px!important}.st-key-clean_nav [data-testid="stHorizontalBlock"]{flex-wrap:wrap!important;gap:2px!important}.st-key-clean_nav [data-testid="stColumn"]{min-width:0!important;flex:1 1 15%!important;width:auto!important}.st-key-clean_nav [data-testid="stColumn"]:first-child{flex:1 1 100%!important}.st-key-clean_nav button p{font-size:10px!important}.clean-logo{font-size:24px}}\n</style>'
CLEAN_HOME_CSS = _load_asset("CLEAN_HOME_CSS.txt")
REAL_FEATURES_HTML = _load_asset("REAL_FEATURES_HTML.txt")
REQUEST_LAYOUT_CSS='<style>\n/* Home is a full-height slide followed by the requested feature section. */\n.st-key-clean_home{position:relative!important;inset:auto!important;height:100dvh!important;min-height:650px!important;width:100%!important}\n.st-key-clean_home>.stElementContainer{min-width:0}\n.real-features{background:#fff;padding:72px 6% 50px;color:#172d49}.real-intro{text-align:center;margin-bottom:42px}.real-intro>span{font-size:10px;letter-spacing:2px;color:#43749e}.real-intro h2{font-size:32px!important;letter-spacing:-1px;margin:14px 0!important;color:#172d49!important}.real-intro p{font-size:13px;color:#697c91!important}.real-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:24px}.real-grid img{display:block;width:100%;height:190px;object-fit:cover;border-radius:3px}.real-grid article small{font-size:10px;color:#65819e;display:block;margin:20px 0 8px}.real-grid article h3{font-size:21px!important;margin:0 0 12px!important;padding:0!important;color:#1e3654!important}.real-grid article p{font-size:12px;line-height:1.8;color:#63758b!important}.real-note{text-align:right;font-size:9px;color:#77889a!important;margin-top:28px}\n/* Account drawer */\n[data-testid="stDialog"] [role="dialog"]{position:fixed!important;inset:0 0 0 auto!important;transform:none!important;margin:0!important;width:440px!important;max-width:100vw!important;height:100dvh!important;max-height:100dvh!important;border-radius:0!important;padding:42px 30px!important;overflow-y:auto!important;box-sizing:border-box!important;border:0!important;box-shadow:-20px 0 70px #07192b30!important}\n[data-testid="stDialog"] [data-testid="stDialogContainer"]{max-height:none!important}\n@media(max-width:700px){.real-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}\n@media(max-width:540px){.real-features{padding:45px 6%}.real-grid{gap:24px 14px}.real-grid img{height:135px}.real-intro h2{font-size:24px!important}.real-grid article h3{font-size:18px!important}.real-grid article p{font-size:11px}.st-key-clean_home{min-height:620px!important}[data-testid="stDialog"] [role="dialog"]{width:100vw!important;padding:30px 22px!important}}\n</style>'
EIGHT_CSS='<style>:root{--eo-blue:#297b86;--eo-ink:#16363e} .block-container{max-width:none!important;width:100%!important} [data-testid="stMain"] button[kind="primary"], [data-testid="stDialog"] [data-testid="stFormSubmitButton"] button{background:#277986!important;border-color:#277986!important}.st-key-clean_nav{min-height:54px!important;padding:6px 3%!important;background:#153e46!important}.st-key-clean_nav button{min-height:30px!important}.st-key-clean_nav button p,.clean-logo,.clean-logo b{color:#fff!important}.st-key-clean_home{height:100dvh!important;min-height:100dvh!important}.st-key-clean_start{z-index:30!important}.clean-copy h1{color:#fff!important}.real-features{background:#f3f7f6!important}.real-intro>span,.real-grid article small{color:#327b83!important}[data-testid="stMain"] [data-baseweb="tab-highlight"]{background:#297b86!important}</style>'
THREE_LAYOUT_CSS='<style>.dashboard-nav-spacer{height:76px;width:100%}.st-key-clean_nav{height:64px!important;min-height:64px!important;box-sizing:border-box!important;overflow:visible!important}.st-key-clean_nav [data-testid="stHorizontalBlock"]{align-items:center!important}.st-key-clean_nav button{white-space:nowrap!important}.st-key-clean_nav [data-testid="stColumn"]{min-width:0!important}.st-key-clean_nav [data-testid="stButton"]{margin:0!important}@media(max-width:640px){.st-key-clean_nav{height:106px!important;min-height:106px!important}.dashboard-nav-spacer{height:118px!important}}</style>'
SIX_LAYOUT_CSS='<style>.st-key-clean_nav{background:transparent!important;border-bottom:0!important;box-shadow:none!important}.st-key-clean_nav button{background:transparent!important}.st-key-clean_nav button p{color:#fff!important;font-weight:750!important;text-shadow:0 1px 3px #15394c}.st-key-clean_nav .st-key-brand_home button p{font-size:30px!important;font-weight:900!important;letter-spacing:-1px}.dashboard-nav-spacer{height:70px!important}</style>'
FIVE_FINAL_CSS='<style>.st-key-clean_nav{background:#203b46!important;height:58px!important;min-height:58px!important;padding:5px 3%!important;border:0!important;box-shadow:none!important;box-sizing:border-box!important}.st-key-clean_nav button{min-height:38px!important}.st-key-clean_nav button p{color:white!important}.st-key-clean_nav [data-testid="stHorizontalBlock"]{gap:8px!important;align-items:center!important}.st-key-clean_home{margin:0!important;top:0!important}.st-key-clean_nav:after{display:none!important}.dashboard-nav-spacer{height:68px!important}[data-testid="stMainBlockContainer"]{padding-top:0!important}.st-key-clean_home{position:relative!important;height:100dvh!important}.st-key-clean_nav .st-key-brand_home button p{font-size:30px!important;font-weight:900!important}@media(max-width:640px){.st-key-clean_nav{height:100px!important;min-height:100px!important}.dashboard-nav-spacer{height:110px!important}}</style>'
NO_UPWARD_BOUNCE_CSS='<style>html,body,.stApp,[data-testid="stMain"],[data-testid="stAppViewContainer"]{overscroll-behavior-y:none!important}</style>'

FINAL_BASE_CSS = """<style>
.stApp [data-testid="stElementContainer"]:has(> [data-testid="stMarkdownContainer"] style),
.stApp .stElementContainer:has(> [data-testid="stMarkdownContainer"] style){display:none!important}
html,body,.stApp,[data-testid="stAppViewContainer"],[data-testid="stMain"]{overscroll-behavior-y:none!important}
.stApp header[data-testid="stHeader"],.stApp [data-testid="stSidebar"],.stApp [data-testid="stSidebarCollapsedControl"],.stApp [data-testid="stToolbar"]{display:none!important}
.stApp .st-key-clean_nav{position:fixed!important;top:0!important;left:0!important;right:0!important;z-index:900!important;height:46px!important;min-height:46px!important;max-height:46px!important;padding:0 3%!important;margin:0!important;background:#203b46!important;border:0!important;box-shadow:none!important;box-sizing:border-box!important;display:flex!important;align-items:center!important;overflow:hidden!important}
.stApp .st-key-clean_nav [data-testid="stHorizontalBlock"]{width:100%!important;gap:6px!important;align-items:center!important;flex-wrap:nowrap!important;margin:0!important}
.stApp .st-key-clean_nav [data-testid="stColumn"]{min-width:0!important}
.stApp .st-key-clean_nav [data-testid="stElementContainer"],.stApp .st-key-clean_nav [data-testid="stButton"]{margin:0!important;padding:0!important}
.stApp .st-key-clean_nav button{background:transparent!important;border:0!important;box-shadow:none!important;min-height:32px!important;height:32px!important;padding:0 6px!important;white-space:nowrap!important}
.stApp .st-key-clean_nav button p{color:#fff!important;font-size:12px!important;font-weight:700!important;text-shadow:none!important;line-height:1!important}
.stApp .st-key-clean_nav .st-key-brand_home button p{font-size:21px!important;font-weight:900!important;letter-spacing:-.8px!important}
.stApp [data-testid="stMainBlockContainer"],.stApp .block-container{max-width:none!important;width:100%!important;padding:62px 28px 24px!important}
@media(max-width:640px){.stApp .st-key-clean_nav{padding:0 8px!important}.stApp .st-key-clean_nav button p{font-size:10px!important}.stApp .st-key-clean_nav .st-key-brand_home button p{font-size:16px!important}.stApp [data-testid="stMainBlockContainer"],.stApp .block-container{padding:58px 10px 20px!important}}
</style>"""
FINAL_HOME_CSS = """<style>
.stApp{background:#f3f7f6!important}
.stApp [data-testid="stMainBlockContainer"],.stApp .block-container{padding:46px 0 0!important}
.stApp [data-testid="stMainBlockContainer"]>[data-testid="stVerticalBlock"]{gap:0!important}
.stApp .st-key-clean_home{position:relative!important;inset:auto!important;top:auto!important;width:100%!important;height:auto!important;min-height:420px!important;margin:0!important;overflow:hidden!important;z-index:1!important}
.stApp .clean-copy{left:10vw!important;top:24%!important}
.stApp .st-key-clean_start{left:10vw!important;top:61%!important;bottom:auto!important}
.stApp .st-key-clean_controls{bottom:22px!important}
</style>"""
FINAL_DASH_CSS = """<style>
/* 대시보드: 전체 페이지 확대/축소 없이 입력 항목을 여러 열로 재배치 */
.stApp{background:#f4f7f7!important}
.stApp [data-testid="stMainBlockContainer"],.stApp .block-container{padding:46px 18px 14px!important}
.stApp [data-testid="stMainBlockContainer"]>[data-testid="stVerticalBlock"]{gap:0!important}
.stApp .dashboard-nav-spacer{display:none!important}

/* 입력 카드의 바깥 여백만 조정하고 글씨/입력창 크기는 유지 */
#eventon-input-card{
  width:100%!important;max-width:none!important;box-sizing:border-box!important;
  margin:0 auto!important;padding:16px 18px!important;
  min-height:0!important;overflow:visible!important;
}
#eventon-input-card h1{font-size:26px!important;line-height:1.25!important;margin:0 0 12px!important}

/* 폼 안의 기본 grid를 3열로 재배치해 세로 길이를 줄임 */
#eventon-input-card .grid{
  display:grid!important;
  grid-template-columns:repeat(3,minmax(220px,1fr))!important;
  gap:12px 16px!important;
  align-items:start!important;
}
#eventon-input-card .grid > *{min-width:0!important}
#eventon-input-card label,
#eventon-input-card [data-slot="label"]{font-size:14px!important;line-height:1.35!important}
#eventon-input-card input,
#eventon-input-card select,
#eventon-input-card textarea,
#eventon-input-card button{font-size:14px!important;box-sizing:border-box!important}
#eventon-input-card input,
#eventon-input-card select{min-height:40px!important}
#eventon-input-card textarea{min-height:72px!important}
#eventon-input-card button{min-height:40px!important;white-space:normal!important}

/* 화면이 좁으면 2열, 모바일에서는 1열로 자연스럽게 변경 */
@media(max-width:1100px){
  #eventon-input-card .grid{grid-template-columns:repeat(2,minmax(220px,1fr))!important}
}
@media(max-width:700px){
  .stApp [data-testid="stMainBlockContainer"],.stApp .block-container{padding:58px 10px 12px!important}
  #eventon-input-card{padding:12px!important}
  #eventon-input-card .grid{grid-template-columns:minmax(0,1fr)!important}
}
/* 대시보드: 브라우저 페이지 자체 스크롤을 없애고 작업영역을 뷰포트 안에 고정 */
html:has(.st-key-clean_nav),body:has(.st-key-clean_nav),.stApp:has(.st-key-clean_nav),
[data-testid="stAppViewContainer"]:has(.st-key-clean_nav){height:auto!important;max-height:none!important;overflow:visible!important}
.stApp:has(.st-key-clean_nav) [data-testid="stMain"],
.stApp:has(.st-key-clean_nav) [data-testid="stMainBlockContainer"],
.stApp:has(.st-key-clean_nav) .block-container{height:auto!important;max-height:auto!important;overflow:hidden!important;box-sizing:border-box!important}
.stApp:has(.st-key-clean_nav) [data-testid="stMainBlockContainer"]>[data-testid="stVerticalBlock"]{height:auto!important;min-height:0!important;overflow:visible!important}
.stApp:has(.st-key-clean_nav) [data-testid="stMain"] iframe{max-height:none!important}
</style>"""
def build_all_css(page):
    parts=[CLEAN_GLOBAL_CSS,REQUEST_LAYOUT_CSS,EIGHT_CSS,NO_UPWARD_BOUNCE_CSS]
    if page=='홈':
        slide=st.session_state.get('clean_home_slide',0)%2
        parts.append(CLEAN_HOME_CSS.replace('SLIDE_IMAGE',CLEAN_SLIDE_ONE if slide==0 else CLEAN_SLIDE_TWO))
    parts.append(FINAL_BASE_CSS)
    if page=='홈':parts.append(FINAL_HOME_CSS)
    elif page=='대시보드':parts.append(FINAL_DASH_CSS)
    css=''.join(parts)
    css=re.sub(r'</?style>','',css)
    css=re.sub(r'/\*.*?\*/','',css,flags=re.S)
    css=re.sub(r'\s*\n\s*',' ',css)
    return '<style>'+css+'</style>'


_REPORT_RESOURCES = {'행사_계획서_양식.md': '# 행사 계획서 표준 양식\n\n## 1. 기본 정보\n- 행사명: \n- 주최: \n- 주관: \n- 후원: \n- 일시: \n- 장소: \n- 형태: 오프라인 / 온라인 / 하이브리드\n- 대상: \n- 예상 참석 인원: \n- 담당 부서: \n- 담당자: \n- 연락처: \n- 작성일: \n\n## 2. 추진 배경 및 목적\n- 배경: \n- 목적: \n- 기대 효과: \n\n## 3. 행사 목표 및 KPI\n| 목표 | 지표 | 목표값 | 측정 방법 |\n|---|---|---:|---|\n|  |  |  |  |\n\n## 4. 세부 일정\n| 시간 | 프로그램 | 내용 | 담당 | 장소 | 비고 |\n|---|---|---|---|---|---|\n|  |  |  |  |  |  |\n\n## 5. 운영 계획\n- 접수 및 안내: \n- 프로그램 운영: \n- 장비: \n- 케이터링: \n- 안전 및 응급 대응: \n- 교통·주차: \n\n## 6. 홍보 계획\n| 단계 | 기간 | 채널 | 콘텐츠 | 담당 | 목표 |\n|---|---|---|---|---|---|\n| 사전 홍보 |  |  |  |  |  |\n| 행사 안내 |  |  |  |  |  |\n| 사후 홍보 |  |  |  |  |  |\n\n## 7. 예산 계획\n| 구분 | 항목 | 내용 | 수량 | 단가 | 금액 | 산출 근거 |\n|---|---|---|---:|---:|---:|---|\n| 수입 |  |  |  |  |  |  |\n| 지출 | 장소 |  |  |  |  |  |\n| 지출 | 연사료 |  |  |  |  |  |\n| 지출 | 홍보 |  |  |  |  |  |\n| 지출 | 물품 |  |  |  |  |  |\n| 지출 | 케이터링 |  |  |  |  |  |\n| 지출 | 비상예비비 |  |  |  |  |  |\n| **합계** |  |  |  |  |  |  |\n\n## 8. 인력 운영\n| 역할 | 담당자 | 업무 | 연락처 |\n|---|---|---|---|\n| 총괄 |  |  |  |\n| 운영 |  |  |  |\n| 홍보 |  |  |  |\n| 재무 |  |  |  |\n| 안전 |  |  |  |\n\n## 9. 리스크 관리\n| 리스크 | 가능성 | 영향 | 예방책 | 비상 대응 |\n|---|---|---|---|---|\n|  |  |  |  |  |\n\n## 10. 승인 및 협조 요청\n- 승인 필요 사항: \n- 협조 부서: \n- 제출 기한: \n- 승인자: \n\n## 11. 첨부자료\n- 프로그램 초안\n- 예산 세부내역\n- 장소 도면\n- 연사 프로필\n- 협력기관 협의 내용\n', '참고_원문_목록.csv': '발행기관,문서명,URL,유형,핵심 참고점\nSmartsheet,Event Proposal Template,https://www.smartsheet.com/sites/default/files/2024-07/ic-event-proposal-template-12095_pdf.pdf,행사 제안서,장소·케이터링·AV·교통·예산 구조\nEventdex,Post Event Report Template,https://www.eventdex.com/guides/post-event-report-template/,사후 보고서,"목표-지표-결과, 피드백, 예산, 개선안"\nVanco,Post Event Report Template,https://www.vancopayments.com/hubfs/Post_Event_Report_Template_Formatted%20(2).docx,사후 보고서,"참석, 재정, 성과, 교훈, 후속조치"\nTalgov,Post Event Report Outline,https://www.talgov.com/Uploads/Public/Documents/cra/fy21_post_event.pdf,공공 행사 보고서,"요약, 일정, 활동 설명, 권고"\n행정안전부,보고서 작성 매뉴얼,https://dams.pa.go.kr/dams/DOCUMENT/2026/06/23/DOC/SRC/0A04202606231407567873595010834.pdf,공공 보고서,"간결성, 통계, 의사결정 정리"\nSVC,Event Report Format,https://svc.ac.in/SVC_MAIN/DownloadCenter/Student/EventReportFormat2024.pdf,대학 행사 보고서,기본정보·방법론·성과 구조\nGTEC,학생집단행사 안전확보 운영지침,https://www.gtec.ac.kr/ajaxfile/CmnFileCpnt/fileView.do?gbn=p01&SITE_NO=2&MENU_NO=940&CONTENTS_NO=2&TYPE_CODE=C0601,학생회 행사 보고서,행사계획서·결과보고서 표준 항목\nSVC,Farewell 2025 Event Report,https://www.svc.ac.in/public/contentfile/39161892174944286885.pdf,실제 대학 행사 보고서,실제 행사 보고서 작성 예시\nSVC,NEXUS 2024 Event Report,https://www.svc.ac.in/SVC_MAIN/FineArts/Reports/NEXUS2024.pdf,실제 대형 축제 보고서,다일간 행사·참여 규모·성과 서술\nvFairs,How to Create a Post-Event Report,https://www.vfairs.com/blog/post-event-report/,컨퍼런스 보고서,KPI·피드백·개선점 중심\nCanberra,Post Event Report Template,https://events.canberra.com.au/Documents/Planning-and-resources/Post_Event_Report_Template.docx,행사 리뷰,설문·전략 권고\nDownstate,Event Summary Form,https://www.downstate.edu/education-training/student-services/student-organizations/_documents/event_summary_fillable_form.pdf,학생단체 행사 요약,"목표 달성, 문제점, 재진행 권고"\nSouth Florida State College,Event Activity Report,https://www.southflorida.edu/wp-content/uploads/2025/08/event-activity-report-Revised-7.7.2025.pdf,학생 행사·모금 보고서,"수입·지출, 목표 달성, 개선점"\nBonsai,Event Proposal Templates,https://www.hellobonsai.com/proposal-template/event,행사 제안서,"개요, 목표, 3단계 범위, 비용, 승인"\nAdobe Express,Event Proposal Templates,https://www.adobe.com/express/templates/proposal/event,행사 제안서,"예산, 일정, 인력, 게스트, 홍보"\n', '행사_계획서_보고서_마스터_가이드.md': '# 행사 계획서·보고서 작성 마스터 가이드\n(프로그램 학습용 코퍼스)\n\n## 1. 문서의 목적과 구분\n\n| 구분 | 행사 계획서 | 행사 보고서 |\n|---|---|---|\n| 작성 시점 | 행사 전 | 행사 후 |\n| 핵심 질문 | 무엇을, 왜, 어떻게 할 것인가 | 무엇이, 얼마나, 어떻게 이루어졌는가 |\n| 필수 요소 | 목적, 대상, 일정, 예산, 역할, 리스크 | 실적, 성과, 비용, 피드백, 개선안 |\n| 판단 기준 | 실행 가능성·승인 가능성 | 목표 달성도·재현 가능성 |\n\n행사 계획서는 승인과 실행 준비를 위한 문서이며, 보고서는 목표 대비 결과를 검증하고 다음 행사의 개선 근거를 만드는 문서다. [web:2][web:14][web:16]\n\n## 2. 작성 원칙\n\n1. **결론 먼저**: 첫 장 또는 첫 문단에 목적·핵심 결과·권고를 압축한다. [web:2][web:7]\n2. **정량 우선**: 참석자 수, 만족도, 예산 집행률, 홍보 도달률 등 수치를 반드시 제시한다. [web:2][web:14]\n3. **목표-지표-결과 대응**: 계획서의 목표는 보고서의 평가 지표와 1:1로 연결한다. [web:2]\n4. **사실과 해석 분리**: ‘참석자 120명’은 사실, ‘행사가 성공적이었다’는 해석이므로 근거를 붙인다. [web:5]\n5. **문제와 개선책 세트**: 문제만 쓰지 말고 원인, 대응, 담당자, 기한까지 쓴다. [web:2][web:5]\n6. **증빙 첨부**: 사진, 참가자 명단, 영수증, 설문 원자료, 언론 보도 등을 부록으로 남긴다. [web:13][web:23]\n7. **독자 맞춤**: 승인자에게는 예산·리스크·승인 필요사항을, 경영진에게는 성과·투자 대비 효과를 강조한다. [web:2]\n\n## 3. 행사 계획서 표준 구조\n\n### 3.1 표지·기본 정보\n- 행사명\n- 주최·주관·후원\n- 행사 일시 및 장소\n- 대상·예상 참석 인원\n- 담당 부서·담당자·연락처\n- 작성일 및 승인란\n\n### 3.2 행사 개요\n- 추진 배경\n- 행사 목적\n- 기대 효과\n- 행사 형태: 오프라인·온라인·하이브리드 [web:17][web:27]\n\n### 3.3 목표 및 성과지표\n목표는 측정 가능한 형태로 쓴다.\n\n예시:\n- 참석자 150명 달성\n- 사전 설문 만족도 4.5/5.0 이상\n- 홍보 콘텐츠 도달 10,000회\n- 참가자 피드백 수집 80건 이상\n\n### 3.4 세부 일정\n시간대별 프로그램을 분 단위로 작성한다.\n\n| 시간 | 내용 | 담당 | 장소 | 비고 |\n|---|---|---|---|---|\n| 13:00-13:30 | 접수 | 운영팀 | 로비 | 명단 확인 |\n| 13:30-13:45 | 개회사 | 진행자 | 강당 | |\n| 13:45-14:30 | 기조강연 | 연사 | 강당 | |\n\n행사 당일 타임라인과 활동별 설명은 공공 보고서 양식에서도 핵심 항목으로 요구된다. [web:4]\n\n### 3.5 운영 계획\n- 프로그램 구성\n- 연사·출연자·협력기관\n- 접수 및 안내\n- 좌석·동선·안전\n- 장비: 음향, 영상, 조명, 인터넷\n- 케이터링\n- 교통 및 주차\n- 비상 연락체계\n\n행사 제안서 양식들은 장소, 케이터링, AV 장비, 교통·주차, 예산을 표준 항목으로 다룬다. [web:1][web:12]\n\n### 3.6 홍보 계획\n- 홍보 목표\n- 채널: SNS, 이메일, 포스터, 언론, 제휴 채널\n- 콘텐츠 일정\n- 홍보 지표: 도달, 클릭, 신청 전환\n\n### 3.7 예산 계획\n| 항목 | 내용 | 예산 | 산출 근거 |\n|---|---|---:|---|\n| 장소 대여 | 대관료 |  | |\n| 연사료 | 강연·출연 |  | |\n| 물품 | 현수막·굿즈 |  | |\n| 케이터링 | 다과·식사 |  | |\n| 홍보 | 디자인·광고 |  | |\n| 비상예비비 | 5~10% |  | |\n| **합계** |  |  | |\n\n예산 항목에는 장소, 식음료, 장비, 홍보, 기타 비용이 포함되며, 계획 대비 실제 지출 차이를 설명하는 것이 보고서의 핵심이다. [web:1][web:2]\n\n### 3.8 인력 및 역할\n| 역할 | 담당자 | 주요 업무 | 비상 연락처 |\n|---|---|---|---|\n| 총괄 |  | 전체 일정·승인 |  |\n| 운영 |  | 접수·안내·동선 |  |\n| 홍보 |  | 콘텐츠·SNS |  |\n| 재무 |  | 예산·정산 |  |\n| 안전 |  | 안전·응급 대응 |  |\n\n### 3.9 리스크 및 대응\n| 리스크 | 가능성 | 영향 | 예방책 | 비상 대응 |\n|---|---|---|---|---|\n| 우천 | 중 | 고 | 실내 대체 장소 확보 | 당일 안내 문자 발송 |\n| 연사 불참 | 낮 | 고 | 예비 연사 확보 | 사전 녹화 영상 활용 |\n| 예산 초과 | 중 | 중 | 견적 3곳 비교 | 비상예비비 사용 |\n\n### 3.10 승인 및 협조 사항\n- 승인 필요 항목\n- 협조 부서\n- 제출 기한\n- 의사결정 권한\n\n## 4. 행사 보고서 표준 구조\n\n### 4.1 Executive Summary\n한 페이지 이내로 다음을 쓴다.\n- 행사 목적 한 문장\n- 핵심 결과 3개, 숫자 포함\n- 가장 큰 교훈 1개\n- 반복·변경·중단 권고와 이유 [web:2]\n\n### 4.2 목표 대비 성과\n| 목표 | 지표 | 목표값 | 실제값 | 달성 여부 | 원인 분석 |\n|---|---|---:|---:|---|---|\n| 참석자 확보 | 참석자 수 | 150명 | 132명 | 88% | 당일 우천 |\n| 만족도 | 평균 점수 | 4.5 | 4.6 | 달성 | 프로그램 만족 |\n\n### 4.3 참석 및 신청 실적\n- 신청자 수\n- 실참자 수\n- 불참률\n- 참가자 유형\n- 신청 추이\n- 데이터 제한 사항 [web:2][web:5]\n\n### 4.4 프로그램 운영 결과\n- 예정 프로그램 대비 실제 진행\n- 회차별 참여도\n- 가장 인기 있었던 세션\n- 운영상 변경 사항과 사유 [web:4][web:23]\n\n### 4.5 참가자 피드백\n- 설문 응답 수\n- 전체 만족도\n- 좋았던 점\n- 아쉬웠던 점\n- 대표 의견 3~5개, 비판 의견 포함 [web:2][web:7]\n\n### 4.6 예산 집행 및 정산\n| 항목 | 계획 | 집행 | 차액 | 차액 사유 |\n|---|---:|---:|---:|---|\n| 장소 |  |  |  |  |\n| 홍보 |  |  |  |  |\n| 물품 |  |  |  |  |\n| 케이터링 |  |  |  |  |\n| **합계** |  |  |  |  |\n\n승인된 예산과 실제 지출을 함께 제시하고, 큰 차이의 원인을 설명해야 한다. [web:2][web:13]\n\n### 4.7 잘된 점\n- 무엇이 효과적이었는가\n- 어떤 근거가 있는가\n- 다음 행사에서도 유지할 것인가\n\n### 4.8 개선 필요 사항\n| 문제 | 원인 | 개선책 | 담당자 | 기한 |\n|---|---|---|---|---|\n| 접수 대기 | 인력 부족 | 키오스크 도입 | 운영팀 | 다음 행사 2주 전 |\n\n### 4.9 후속 조치\n- 참가자 감사 메일\n- 자료 공유\n- 스폰서 보고\n- 콘텐츠 재활용\n- 차기 행사 검토 [web:2]\n\n### 4.10 부록\n- 사진\n- 참가자 명단\n- 설문 문항·원자료\n- 영수증·세금계산서\n- 언론 보도\n- SNS 캡처\n- 프로그램북\n- 현장 사진 [web:13][web:23]\n\n## 5. 실제 사례에서 배울 구조\n\n### 5.1 대학 행사 보고서 사례\n대학 행사 보고서는 보통 행사명, 날짜, 학과·동아리, 담당자, 시간, 장소, 참가자 수, 온라인·오프라인 여부, 활동 요약, 방법론, 연사, 성과를 표 형태로 정리한다. [web:17][web:27][web:28]\n\n예시 구조:\n- 행사명: NEXUS 2024\n- 기간: 3일\n- 주관: Fine Arts Association 및 Student Union\n- 참가 규모: 5,000명 이상, 전체 방문 약 30,000명\n- 내용: 부스, 공연, 대회, DJ·밴드 공연\n- 성과: 학생 간 교류, 문화 참여 기회 제공 [web:28]\n\n### 5.2 공공기관 행사보고서 사례\n공공기관 매뉴얼은 행사 개요, 목적·배경, 일시·장소, 안건, 참석자, 홍보 방식, 말씀자료 요약, 통계, 의사결정 사항을 강조한다. 분량은 보통 1~2페이지 내외로 간결하게 유지한다. [web:16]\n\n### 5.3 학생회 행사결과보고서 사례\n한 대학의 행사결과보고서 양식은 행사명, 행사기간, 참가인원, 장소, 개선·건의·요구사항, 특이사항을 기본 항목으로 둔다. [web:25]\n\n### 5.4 상업 행사 보고서 사례\n상업·컨퍼런스형 보고서는 Executive Summary, 목표·KPI, 등록·참석, 프로그램 참여, 설문, 스폰서, 예산, 교훈, 후속 조치를 표준으로 삼는다. [web:2][web:14]\n\n## 6. 문장 작성 규칙\n\n### 6.1 좋은 문장\n- “참석자 132명 중 118명이 재참여 의사를 표명했다.”\n- “홍보 비용이 계획보다 12% 초과되었으며, 유료 광고 확대가 주요 원인이었다.”\n- “접수 대기 문제를 줄이기 위해 다음 행사부터 QR 사전 체크인을 도입한다.”\n\n### 6.2 피해야 할 문장\n- “행사가 대성공이었다.”\n- “많은 사람이 참여했다.”\n- “전반적으로 좋았다.”\n- “다음에는 더 잘하겠다.”\n\n이유: 수치, 근거, 원인, 개선책이 없어 판단과 후속 조치가 불가능하다. [web:2][web:5]\n\n## 7. 품질 체크리스트\n\n### 계획서 체크리스트\n- 목적이 한 문장으로 명확한가\n- 목표가 측정 가능한가\n- 일정이 시간 단위로 구체적인가\n- 예산에 산출 근거가 있는가\n- 담당자와 비상연락망이 있는가\n- 리스크와 대응책이 있는가\n- 승인 필요사항이 명시되었는가\n\n### 보고서 체크리스트\n- 목표 대비 실적을 수치로 비교했는가\n- 예산 계획과 집행을 대비했는가\n- 참가자 피드백을 포함했는가\n- 문제 원인과 개선책을 함께 썼는가\n- 개선책에 담당자와 기한이 있는가\n- 증빙자료를 첨부했는가\n- 다음 행사에 바로 쓸 수 있는 권고가 있는가 [web:2][web:16]\n\n## 8. 프로그램 학습용 출력 규칙\n\n프로그램은 사용자 입력을 받아 다음 순서로 문서를 생성한다.\n\n1. 문서 유형 판별: 계획서 또는 보고서\n2. 필수 정보 확인: 행사명, 일시, 장소, 대상, 목적, 예산, 담당자\n3. 누락 정보 질문: 최대 5개까지만\n4. 표준 구조에 따라 초안 생성\n5. 수치가 없는 성과 문장은 임의로 만들지 않고 `[입력 필요]`로 표시\n6. 목표·지표·결과를 표로 연결\n7. 문제점에는 반드시 원인·개선책·담당자·기한을 붙임\n8. 마지막에 품질 체크리스트 점검 결과 제시\n\n## 9. 참고 원문 목록\n\n| 유형 | 문서 | 핵심 참고점 |\n|---|---|---|\n| 행사 제안서 | Smartsheet Event Proposal Template | 장소·케이터링·AV·교통·예산 구조 [web:1] |\n| 사후 보고서 | Eventdex Post Event Report Template | 목표-지표-결과, 피드백, 예산, 개선안 [web:2] |\n| 사후 보고서 | Vanco Post Event Report Template | 참석 유형, 재정, 성과, 교훈, 후속조치 [web:3] |\n| 공공 보고서 | 행정안전부 보고서 작성 매뉴얼 | 간결성, 통계, 의사결정 정리 [web:16] |\n| 대학 양식 | SVC Event Report Format | 행사 기본정보·방법론·성과 구조 [web:17] |\n| 학생회 양식 | GTEC 행사결과보고서 | 참가인원, 개선·건의, 특이사항 [web:25] |\n| 학생회 사례 | SVC Farewell 2025 | 실제 행사 보고서 작성 예시 [web:27] |\n| 대형 축제 사례 | SVC NEXUS 2024 | 다일간 행사·참여 규모·성과 서술 [web:28] |\n| 컨퍼런스 가이드 | vFairs Post-Event Report | KPI·피드백·개선점 중심 구성 [web:14] |\n| 행사 리뷰 | Canberra Post Event Report Template | 설문·전략 권고 중심 [web:7] |\n', '행사_결과보고서_양식.md': '# 행사 결과보고서 표준 양식\n\n## 1. 기본 정보\n- 행사명: \n- 일시: \n- 장소: \n- 형태: 오프라인 / 온라인 / 하이브리드\n- 주최·주관: \n- 담당자: \n- 보고일: \n\n## 2. Executive Summary\n- 행사 목적: \n- 핵심 결과 1: \n- 핵심 결과 2: \n- 핵심 결과 3: \n- 주요 교훈: \n- 향후 권고: \n\n## 3. 목표 대비 성과\n| 목표 | 지표 | 목표값 | 실제값 | 달성률 | 원인 분석 |\n|---|---|---:|---:|---:|---|\n|  |  |  |  |  |  |\n\n## 4. 참석 실적\n| 구분 | 계획 | 실제 | 비고 |\n|---|---:|---:|---|\n| 신청자 |  |  |  |\n| 실참자 |  |  |  |\n| 불참자 |  |  |  |\n| 불참률 |  |  |  |\n\n- 참가자 구성: \n- 신청 추이: \n- 데이터 제한: \n\n## 5. 프로그램 운영 결과\n| 시간 | 예정 프로그램 | 실제 진행 | 참여 현황 | 특이사항 |\n|---|---|---|---|---|\n|  |  |  |  |  |\n\n- 가장 참여도가 높았던 프로그램: \n- 운영 변경 사항: \n- 변경 사유: \n\n## 6. 참가자 피드백\n- 설문 배포 기간: \n- 응답 수: \n- 응답률: \n- 전체 만족도: \n\n| 평가 항목 | 평균 점수 | 주요 의견 |\n|---|---:|---|\n| 전체 만족도 |  |  |\n| 프로그램 |  |  |\n| 운영 |  |  |\n| 장소·시설 |  |  |\n\n### 좋았던 점\n- \n- \n\n### 아쉬웠던 점\n- \n- \n\n### 대표 의견\n1. \n2. \n3. \n\n## 7. 예산 집행 및 정산\n| 구분 | 계획 | 집행 | 차액 | 차액 사유 |\n|---|---:|---:|---:|---|\n| 수입 |  |  |  |  |\n| 장소 |  |  |  |  |\n| 연사료 |  |  |  |  |\n| 홍보 |  |  |  |  |\n| 물품 |  |  |  |  |\n| 케이터링 |  |  |  |  |\n| **합계** |  |  |  |  |\n\n## 8. 잘된 점\n| 항목 | 내용 | 근거 | 유지 여부 |\n|---|---|---|---|\n|  |  |  |  |\n\n## 9. 개선 필요 사항\n| 문제 | 원인 | 개선책 | 담당자 | 기한 |\n|---|---|---|---|---|\n|  |  |  |  |  |\n\n## 10. 후속 조치\n| 조치 | 담당자 | 기한 | 상태 |\n|---|---|---|---|\n| 참가자 감사 메일 |  |  |  |\n| 자료 공유 |  |  |  |\n| 스폰서 보고 |  |  |  |\n| 차기 행사 검토 |  |  |  |\n\n## 11. 첨부자료\n- 사진\n- 참가자 명단\n- 설문 원자료\n- 영수증·세금계산서\n- 언론 보도\n- SNS 캡처\n- 프로그램북\n', '프로그램_학습용_지시문.md': '# 행사 계획서·보고서 생성 프로그램 학습용 지시문\n\n당신은 행사 계획서와 행사 결과보고서를 작성하는 전문 어시스턴트다.\n\n## 역할\n사용자가 제공한 정보를 바탕으로 다음 문서를 작성한다.\n1. 행사 계획서\n2. 행사 결과보고서\n3. 행사 제안서\n4. 행사 예산서\n5. 행사 운영 매뉴얼\n6. 사후 개선 보고서\n\n## 절대 규칙\n1. 사실이 확인되지 않은 수치를 만들어내지 않는다.\n2. 참석자 수, 만족도, 비용, 매출 등 수치가 없으면 `[입력 필요]`로 표시한다.\n3. 목표, 지표, 목표값, 실제값, 달성 여부를 반드시 표로 연결한다.\n4. 문제점을 쓸 때는 원인, 개선책, 담당자, 기한을 함께 제시한다.\n5. 계획서에는 실행 가능성과 승인 포인트를 강조한다.\n6. 보고서에는 성과, 근거, 교훈, 후속 조치를 강조한다.\n7. 문장은 간결하고 능동태로 쓴다.\n8. “대성공”, “많은 참여”, “좋았다” 같은 추상적 표현만 쓰지 않는다.\n9. 모든 성과 주장에는 근거를 붙인다.\n10. 마지막에 누락 정보와 품질 점검 결과를 제시한다.\n\n## 필수 입력 정보\n- 행사명\n- 행사 목적\n- 일시\n- 장소 또는 온라인 플랫폼\n- 대상 및 예상 인원\n- 주최·주관\n- 예산\n- 담당자\n- 주요 프로그램\n- 성과 지표\n- 참가자 피드백, 보고서인 경우\n\n## 계획서 출력 순서\n1. 기본 정보\n2. 추진 배경 및 목적\n3. 목표 및 KPI\n4. 세부 일정\n5. 운영 계획\n6. 홍보 계획\n7. 예산 계획\n8. 인력 운영\n9. 리스크 관리\n10. 승인 및 협조 요청\n11. 첨부자료\n\n## 보고서 출력 순서\n1. 기본 정보\n2. Executive Summary\n3. 목표 대비 성과\n4. 참석 실적\n5. 프로그램 운영 결과\n6. 참가자 피드백\n7. 예산 집행 및 정산\n8. 잘된 점\n9. 개선 필요 사항\n10. 후속 조치\n11. 첨부자료\n\n## 출력 형식\n- 기본 형식: Markdown\n- 표는 가능한 한 모든 정량 정보를 표로 정리\n- Executive Summary는 200~400자\n- 전체 보고서는 필요에 따라 2~10페이지 분량\n- 사용자가 요청하면 HWP·Word·PDF용 구조로 변환 가능한 형태로 제공\n\n## 품질 점검\n출력 마지막에 다음을 점검한다.\n- 목적 명확성\n- 목표 측정 가능성\n- 일정 구체성\n- 예산 근거\n- 책임자 명시\n- 리스크 대응\n- 성과 근거\n- 개선책 실행 가능성\n- 증빙자료 준비 여부\n'}
# Offline template-based event document workflow.
def _report_cell(value):
    if value is None or str(value).strip() == '':
        return '[입력 필요]'
    return str(value).replace('|', '\\|').replace('\n', ' ')


def _report_number(value):
    try:
        value = float(str(value).replace(',', '').strip())
        return value if value >= 0 and value == value and value != float('inf') else None
    except (ValueError, TypeError):
        return None


def build_standard_document(kind, fields, snapshot=None):
    """Fill the supplied standard template, leaving unknown facts explicitly empty."""
    snapshot = snapshot or {}
    c = snapshot.get('config') or {}
    template = _REPORT_RESOURCES['행사_계획서_양식.md' if kind == '행사 계획서' else '행사_결과보고서_양식.md']
    values = dict(fields)
    values['행사 목적'] = fields.get('목적', '')
    values['주최·주관'] = ' / '.join(v for v in [fields.get('주최'), fields.get('주관')] if v)
    values['보고일'] = fields.get('작성일', '')
    values['예상 참석 인원'] = fields.get('예상 참석 인원', '')
    lines = []
    section = ''
    for line in template.splitlines():
        if line.startswith('## '):
            section = line
        match = re.match(r'^- ([^:]+):\s*(.*)$', line)
        if match:
            label, original = match.groups()
            value = values.get(label, '')
            line = '- ' + label + ': ' + _report_cell(value)
        elif line.startswith('|') and not ('-' in line and re.match(r'^\|[\s:|\-]+\|$', line)):
            cells = line.split('|')[1:-1]
            line = '| ' + ' | '.join(cell.strip() or '[입력 필요]' for cell in cells) + ' |'
        elif line.strip() == '-' or re.match(r'^\d+\.\s*$', line):
            line = line.rstrip() + ' [입력 필요]'
        elif section.startswith('## 11.') and line.startswith('- '):
            line += ': [첨부 여부 확인]'
        lines.append(line)
    text = '\n'.join(lines)
    if kind == '행사 계획서':
        text = text.replace('# 행사 계획서 표준 양식', '# ' + _report_cell(fields.get('행사명')) + ' 행사 계획서', 1)
        text = text.replace('| 목표 | 지표 | 목표값 | 측정 방법 |\n|---|---|---:|---|\n| [입력 필요] | [입력 필요] | [입력 필요] | [입력 필요] |',
            '| 목표 | 지표 | 목표값 | 실제값 | 달성 여부 | 측정 방법 |\n|---|---|---:|---:|---|---|\n| 참석 목표 | 참석자 수 | '+_report_cell(fields.get('예상 참석 인원'))+' | 행사 전·미측정 | 행사 후 평가 | 출입 기록 |')
    else:
        text = text.replace('# 행사 결과보고서 표준 양식', '# ' + _report_cell(fields.get('행사명')) + ' 행사 결과보고서', 1)
        actual = _report_number(fields.get('실참자 수'))
        target = _report_number(fields.get('예상 참석 인원'))
        registered = _report_number(fields.get('신청자 수'))
        rate = f'{actual/target*100:.1f}%' if actual is not None and target is not None and target > 0 else '[입력 필요]'
        text = text.replace('| [입력 필요] | [입력 필요] | [입력 필요] | [입력 필요] | [입력 필요] | [입력 필요] |',
            '| 참석 목표 | 참석자 수 | '+_report_cell(target)+' | '+_report_cell(actual)+' | '+rate+' | [입력 필요] |', 1)
        text = text.replace('| 실참자 | [입력 필요] | [입력 필요] | [입력 필요] |', '| 실참자 | '+_report_cell(target)+' | '+_report_cell(actual)+' | 사용자 입력 |')
        text = text.replace('| 신청자 | [입력 필요] | [입력 필요] | [입력 필요] |', '| 신청자 | [입력 필요] | '+_report_cell(registered)+' | 사용자 입력 |')
        if registered is not None and actual is not None and registered >= actual:
            no_show = registered-actual
            no_show_rate = f'{no_show/registered*100:.1f}%' if registered > 0 else '산출 불가(신청자 0명)'
            text = text.replace('| 불참자 | [입력 필요] | [입력 필요] | [입력 필요] |', '| 불참자 | [입력 필요] | '+str(no_show)+' | 신청자−실참자 |')
            text = text.replace('| 불참률 | [입력 필요] | [입력 필요] | [입력 필요] |', '| 불참률 | [입력 필요] | '+no_show_rate+' | 불참자/신청자 |')
        elif registered is not None and actual is not None:
            text += '\n\n> 실참자가 신청자보다 많습니다. 현장 등록 포함 여부를 확인하세요. 불참률은 산출하지 않았습니다.'
    if snapshot:
        fs = snapshot.get('facilities') or []
        info = ['','## 설계 데이터 참고 부록','- 출처: 대시보드 마지막 동기화 데이터',
                '- 동기화 시각: '+_report_cell(snapshot.get('updatedAt')),
                '- 시설 수: '+str(len(fs))+'개',
                '- 설계·시뮬레이션 값은 실제 참석 실적 또는 실제 집행비가 아닙니다.']
        if not c.get('budgetUnknown') and _report_number(c.get('budget')) is not None:
            info.append('- 설계 입력 예산(고정 환산 가정): '+f'{float(c["budget"])*1350:,.0f}'+'원 (USD × 1,350원, 실시간 환율·확정 견적 아님)')
        info += ['','| 시설 | 분류 | 규격(m) |','|---|---|---|']
        for f in fs:
            d=f.get('dimensions') or {}
            info.append('| '+_report_cell(f.get('nameKo') or f.get('name'))+' | '+_report_cell(f.get('category'))+' | '+_report_cell(d.get('width'))+' × '+_report_cell(d.get('depth'))+' × '+_report_cell(d.get('height'))+' |')
        text += '\n'+'\n'.join(info)
    text = re.sub(r'(?m)^## 9\. 리스크 관리', '## 9. 리스크 관리', text)
    return text


def report_quality_appendix(text):
    missing = []
    section = ''
    for line in text.splitlines():
        if line.startswith('## '): section = line[3:]
        if '[입력 필요]' in line or '[첨부 여부 확인]' in line:
            label = section + (' · '+line[2:].split(':')[0] if line.startswith('- ') else ' · 표/세부 항목')
            if label not in missing: missing.append(label)
    abstract = [word for word in ['대성공', '많은 참여', '전반적으로 좋았다'] if word in text]
    checks = [
        ('표준 문서 구조', '적용'),
        ('미입력 정보', f'{len(missing)}개 항목군 보완 필요' if missing else '표시된 미입력 항목 없음'),
        ('실제 성과·비용 근거', '작성자 증빙 대조 필요'),
        ('문제-원인-개선책-담당자-기한', '표준 항목 적용 · 내용 검토 필요'),
        ('설계값과 실적 분리', '설계 참고 부록 구분'),
        ('목적·KPI·일정·예산 근거·책임자·리스크', '각 섹션의 입력 및 산출 근거 확인 필요'),
        ('추상적인 성과 표현', '근거 보완 필요: '+', '.join(abstract) if abstract else '지정 표현 미검출'),
        ('증빙자료', '첨부 여부 및 개인정보 확인 필요'),
    ]
    appendix = '\n\n## 누락 정보 및 품질 점검\n'
    appendix += '\n'.join('- '+x for x in missing) if missing else '- 미입력 표시는 없습니다. 사실 검증 완료를 의미하지 않습니다.'
    appendix += '\n\n| 점검 항목 | 결과 |\n|---|---|\n' + '\n'.join('| '+a+' | '+b+' |' for a,b in checks)
    return text+appendix


def render_report():
    _restore_standard_draft()
    st.title('행사 계획서 · 결과보고서')
    st.caption('제공된 표준 양식과 작성 규칙을 적용합니다. 입력하지 않은 수치나 성과는 만들지 않습니다.')
    snapshot = st.session_state.get('dashboard_snapshot') or {}
    c = snapshot.get('config') or {}
    if not snapshot:
        st.info('동기화된 설계가 없어도 직접 입력하여 문서를 작성할 수 있습니다.')
    kind = st.selectbox('문서 유형', ['행사 계획서','행사 결과보고서'], key='standard_report_kind')
    with st.expander('기본 정보 입력', expanded=True):
        defaults = {
            '행사명':c.get('eventName',''), '일시':'', '장소':c.get('location',''),
            '주최':'','주관':'','후원':'','형태':'오프라인','대상':'',
            '예상 참석 인원':str(c['expectedAttendance']) if c.get('expectedAttendance') is not None else '',
            '담당 부서':'','담당자':st.session_state.get('display_name',''), '연락처':'',
            '작성일':datetime.now().strftime('%Y-%m-%d'),'목적':c.get('purpose',''),
            '배경':'','기대 효과':'', '신청자 수':'','실참자 수':'','응답 수':'','전체 만족도':''}
        fields = {}
        cols = st.columns(2)
        for i,(label,default) in enumerate(defaults.items()):
            fields[label] = cols[i%2].text_input(label, value=str(default or ''), key='standard_base_'+label)
    seed = build_standard_document(kind, fields, snapshot)
    version = hashlib.sha256(seed.encode()).hexdigest()[:16]
    st.caption('아래 각 항목을 펼쳐 표와 내용을 직접 보완하세요. 기본 정보를 변경하면 해당 정보 기준 초안으로 전환됩니다.')
    parts = re.split(r'(?m)(?=^## )', seed)
    edited = [parts[0]]
    for i,part in enumerate(parts[1:]):
        heading, _, body = part.partition('\n')
        with st.expander(heading[3:]):
            edited_body = st.text_area('항목 내용 (표는 Markdown 형식으로 편집)',value=body,height=260,key=f'standard_section_{version}_{i}')
            edited.append(heading+'\n'+edited_body)
    text = report_quality_appendix('\n'.join(edited))
    with st.expander('작성 규칙 · 참고자료 5개'):
        st.markdown('**적용 기준:** 미확인 수치 미생성, 목표-지표-실적 대응, 문제-원인-개선책-담당자-기한 연결, 누락 정보 점검. 참고 링크는 사용자 제공 목록이며 원문 검증 완료를 의미하지 않습니다.')
        st.markdown(_REPORT_RESOURCES['프로그램_학습용_지시문.md'])
        st.markdown(_REPORT_RESOURCES['행사_계획서_보고서_마스터_가이드.md'])
        import csv
        rows = list(csv.DictReader(io.StringIO(_REPORT_RESOURCES['참고_원문_목록.csv'].lstrip('\ufeff'))))
        st.dataframe(rows, use_container_width=True)
        for name, content in _REPORT_RESOURCES.items():
            st.download_button(name, content.encode('utf-8-sig' if name.endswith('.csv') else 'utf-8'),file_name=name,key='standard_resource_'+name)
    st.subheader('문서 미리보기')
    st.markdown(text)
    st.download_button('Markdown 다운로드',text.encode('utf-8'),file_name='Event_ON_'+kind.replace(' ','_')+'.md',mime='text/markdown')
    try:
        st.download_button('PDF 다운로드',create_pdf(text,kind),file_name='Event_ON_'+kind.replace(' ','_')+'.pdf',mime='application/pdf')
    except Exception as exc:
        st.warning('PDF 생성 실패: '+str(exc)+' · Markdown 다운로드를 이용해 주세요.')
    backup = {'document_type':kind,'fields':fields,'markdown':text,'snapshot':snapshot}
    st.download_button('작성 내용 백업 (JSON)',json.dumps(backup,ensure_ascii=False,indent=2).encode('utf-8'),file_name='Event_ON_document_backup.json',mime='application/json')
    uploaded = st.file_uploader('작성 내용 백업 복원',type=['json'],key='standard_restore_file')
    if uploaded is not None and st.button('백업 복원'):
        try:
            restored = json.load(uploaded)
            if not isinstance(restored.get('fields'),dict) or not isinstance(restored.get('markdown'),str):
                raise ValueError('Event ON 문서 백업 JSON이 아닙니다.')
            st.session_state['_pending_standard_restore'] = restored
            st.rerun()
        except (ValueError,TypeError,KeyError) as exc:
            st.error('복원 실패: '+str(exc))


def _restore_standard_draft():
    restored = st.session_state.pop('_pending_standard_restore',None)
    if not restored: return
    for label,value in restored['fields'].items(): st.session_state['standard_base_'+label]=str(value or '')
    kind = restored.get('document_type','행사 계획서')
    if kind not in ['행사 계획서','행사 결과보고서']: kind='행사 계획서'
    st.session_state['standard_report_kind']=kind
    snapshot = restored.get('snapshot') or {}
    if snapshot: st.session_state['dashboard_snapshot']=snapshot
    seed = build_standard_document(kind,restored['fields'],snapshot)
    version = hashlib.sha256(seed.encode()).hexdigest()[:16]
    parts = re.split(r'(?m)(?=^## )',restored['markdown'].split('\n\n## 누락 정보 및 품질 점검')[0])
    for i,part in enumerate(parts[1:]):
        st.session_state[f'standard_section_{version}_{i}']=part.partition('\n')[2]


_original_build_all_css = build_all_css
def build_all_css(page):
    css = _original_build_all_css(page)
    css += '<style>html,body,.stApp,[data-testid="stAppViewContainer"]{height:auto!important;max-height:none!important;overflow-y:auto!important}.stApp [data-testid="stMain"],.stApp [data-testid="stMainBlockContainer"],.stApp .block-container,.stApp [data-testid="stMainBlockContainer"]>[data-testid="stVerticalBlock"]{height:auto!important;max-height:none!important;overflow:visible!important}.stApp [data-testid="stMain"] iframe{max-height:none!important}.stApp .block-container{padding-top:62px!important}</style>'
    if page=='홈':
        css += '<style>.stApp .st-key-clean_home{position:relative!important;inset:auto!important;min-height:0!important;height:auto!important;aspect-ratio:16/9!important;background-size:100% 100%!important;background-position:center top!important}.stApp .st-key-clean_home:hover{background-image:linear-gradient(90deg,#07131e85,#07131e15),url(data:image/jpeg;base64,'+CLEAN_SLIDE_TWO+')!important}.st-key-clean_controls{display:none!important}.stApp .clean-copy{top:24%!important}.stApp .st-key-clean_start{top:65%!important}@media(max-width:640px){.clean-copy h1{font-size:clamp(18px,4.4vw,30px)!important}.clean-copy p{font-size:10px!important}.clean-copy>span{font-size:7px!important}.stApp .st-key-clean_start button{min-height:28px!important;padding:2px 10px!important}.stApp .st-key-clean_start button p{font-size:10px!important}}</style>'
    return css



_scroll_build_all_css = build_all_css
def build_all_css(page):
    css = _scroll_build_all_css(page)
    return css + '<style>\nhtml body .stApp:has(.st-key-clean_nav) [data-testid="stMain"]{height:100dvh!important;max-height:none!important;overflow-y:auto!important;overflow-x:hidden!important}\nhtml body .stApp:has(.st-key-clean_nav) [data-testid="stMainBlockContainer"],html body .stApp:has(.st-key-clean_nav) .block-container,html body .stApp:has(.st-key-clean_nav) [data-testid="stMainBlockContainer"]>[data-testid="stVerticalBlock"]{height:auto!important;max-height:none!important;overflow:visible!important}\nhtml body .stApp:has(.st-key-clean_nav) [data-testid="stMain"] iframe{height:auto;max-height:none!important;min-height:700px}\n</style>'


def render_home():
    import html as _html
    with st.container(key='home_v3'):
        left,right=st.columns([0.9,1.25],gap='large',vertical_alignment='center')
        with left:
            st.markdown('<div class="home-v3-copy"><span>EVENT PLANNING WORKSPACE</span><h1>좋은 행사의 시작,<br>명확한 설계에서.</h1><p>행사 기획부터 공간 배치, 운영 검토와 보고서까지.<br>Event ON에서 차근차근 준비하세요.</p></div>',unsafe_allow_html=True)
            if st.button('설계 시작하기 →',key='home_v3_start',type='primary'):go('대시보드');st.rerun()
        with right:
            st.markdown('<div class="home-v3-photo"><img class="photo-first" alt="도면으로 행사 공간을 기획하는 모습" src="data:image/jpeg;base64,'+CLEAN_SLIDE_ONE+'"><img class="photo-second" alt="행사 공간을 함께 검토하는 모습" src="data:image/jpeg;base64,'+CLEAN_SLIDE_TWO+'"></div>',unsafe_allow_html=True)
    st.markdown(REAL_FEATURES_HTML,unsafe_allow_html=True)

def build_all_css(page):
    return '<style>\nheader[data-testid="stHeader"],[data-testid="stSidebar"],[data-testid="stSidebarCollapsedControl"]{display:none!important}\nhtml,body{overflow:auto!important}.stApp,[data-testid="stAppViewContainer"]{height:100%!important;max-height:none!important;overflow:hidden!important}\n.stApp [data-testid="stMain"]{height:100dvh!important;max-height:100dvh!important;overflow-y:auto!important;overflow-x:hidden!important}\n.stApp [data-testid="stMainBlockContainer"],.stApp .block-container{height:auto!important;max-height:none!important;overflow:visible!important;padding:104px 5vw 48px!important;max-width:1600px!important;margin:0 auto!important}\n.stApp [data-testid="stMainBlockContainer"]>[data-testid="stVerticalBlock"]{height:auto!important;max-height:none!important;overflow:visible!important;gap:24px!important}\n.st-key-clean_nav{position:fixed!important;top:0;left:0;right:0;z-index:900;background:#fff!important;border-bottom:1px solid #e0e8e9;padding:12px 4vw!important;min-height:68px!important}\n.st-key-clean_nav button{background:transparent!important;border:0!important;box-shadow:none!important}.st-key-clean_nav button p{color:#193a40!important;font-size:13px!important}\n.st-key-home_v3{padding:36px 0 54px!important}.home-v3-copy span{color:#277986;font-size:11px;letter-spacing:2px;font-weight:800}.home-v3-copy h1{color:#17373d!important;font-size:clamp(32px,3.5vw,56px)!important;letter-spacing:-2px;line-height:1.25!important;margin:20px 0!important}.home-v3-copy p{color:#60777b!important;line-height:1.9!important;font-size:15px!important;margin-bottom:22px!important}\n.st-key-home_v3 button[kind="primary"]{background:#277986!important;border:0!important;border-radius:10px!important;padding:12px 24px!important;min-height:48px!important}.st-key-home_v3 button[kind="primary"] p{color:white!important}\n.home-v3-photo{position:relative;aspect-ratio:16/9;width:100%;border-radius:20px;overflow:hidden;background:#e9eff0;box-shadow:0 18px 45px #17373d14}.home-v3-photo img{display:block;width:100%;height:100%;object-fit:contain}.home-v3-photo .photo-second{position:absolute;inset:0;opacity:0;transition:opacity .35s}.home-v3-photo:hover .photo-second{opacity:1}\n.stApp [data-testid="stMain"] iframe{width:100%!important;height:900px!important;max-height:none!important;border:1px solid #dbe5e6!important;border-radius:12px}\n.real-features{padding:32px 0!important}.real-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:20px}.real-grid article{background:white;border-radius:16px;overflow:hidden;padding:16px}.real-grid img{width:100%;height:auto;object-fit:contain}.real-intro{margin-bottom:24px}.stApp{background:#f4f7f7!important}\n@media(max-width:700px){.stApp .block-container{padding:100px 16px 32px!important}.st-key-home_v3 [data-testid="stHorizontalBlock"]{flex-direction:column!important}.st-key-home_v3 [data-testid="stColumn"]{width:100%!important;flex:1 1 100%!important}.real-grid{grid-template-columns:1fr}.home-v3-copy h1{font-size:34px!important}.st-key-clean_nav{padding:8px!important}.st-key-clean_nav button p{font-size:10px!important}}\n</style>'

if __name__ == '__main__':
    main()
