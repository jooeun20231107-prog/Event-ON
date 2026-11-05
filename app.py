# Event ON | AI 행사 설계 대시보드
# Streamlit Cloud entry point: app.py
import io
import json
import math
import random
import sqlite3
from datetime import date, time, datetime
from pathlib import Path

import streamlit as st
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage

APP_DIR = Path(__file__).resolve().parent
DB_PATH = APP_DIR / "event_on.db"

st.set_page_config(page_title="Event ON | AI 행사 설계", page_icon="🎪", layout="wide", initial_sidebar_state="expanded")

# ---------- style ----------
st.markdown("""
<style>
:root { --navy:#17324d; --blue:#2f80ed; --mint:#e9f8f4; --ink:#1e293b; }
.stApp { background:#f6f8fb; color:var(--ink); }
.block-container { padding-top:1.0rem; padding-bottom:1rem; max-width:1600px; }
h1,h2,h3 { color:#17324d; }
div[data-testid="stMetric"] { background:white; border:1px solid #e4eaf2; border-radius:12px; padding:10px 14px; }
div[data-testid="stVerticalBlockBorderWrapper"] { border-radius:14px; }
section[data-testid="stSidebar"] { background:#ffffff; border-right:1px solid #e6ebf2; }
.event-card { background:white; border:1px solid #e6ebf2; border-radius:16px; padding:18px; }
.small-note { color:#64748b; font-size:0.85rem; }
</style>
""", unsafe_allow_html=True)

# ---------- database ----------
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS projects(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            created_at TEXT NOT NULL,
            data TEXT NOT NULL
        )""")
init_db()

def save_project(data):
    title = data.get("event_name") or "이름 없는 행사"
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("INSERT INTO projects(title, created_at, data) VALUES(?,?,?)",
                     (title, datetime.now().strftime("%Y-%m-%d %H:%M"), json.dumps(data, ensure_ascii=False)))

def load_projects():
    with sqlite3.connect(DB_PATH) as conn:
        return conn.execute("SELECT id,title,created_at,data FROM projects ORDER BY id DESC").fetchall()

def delete_project(pid):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM projects WHERE id=?", (pid,))

# ---------- session defaults ----------
defaults = {
    "page": "홈", "logged_in": False, "display_name": "주은", "role": "행사 설계자",
    "selected_booth": "안내센터", "show_congestion": False, "saved_notice": "",
    "event_name": "지역 문화 축제", "event_type": "지역 축제", "purpose": "지역 주민 참여와 문화 교류",
    "venue": "실내 전시장", "visitor_count": 1000, "event_date": date.today(),
    "start_time": time(10,0), "end_time": time(18,0), "event_days": 1,
    "mood": "활기찬", "age_group": "전 연령", "indoor_outdoor": "실내",
    "ticket_type": "무료", "ticket_price": 0, "budget": 10000000,
    "extra_request": "", "facilities": ["공연장","푸드존","체험부스","휴게공간","응급의료센터","안내센터","화장실","수유실","흡연실","방송·음향실","분리수거장","주차장"]
}
for k,v in defaults.items():
    if k not in st.session_state: st.session_state[k] = v

FACILITY_INFO = {
    "주출입구":"방문객의 진입과 퇴장을 분산시키고 행사장 방향을 쉽게 안내합니다.",
    "안내센터":"행사 정보, 분실물, 문의 대응을 한곳에서 처리합니다.",
    "응급의료센터":"응급 상황에 빠르게 대응할 수 있도록 접근 가능한 위치에 둡니다.",
    "화장실":"대기열과 이동 거리를 고려해 주요 동선에서 접근하기 쉽게 배치합니다.",
    "수유실":"유아 동반 방문객이 조용하고 안전하게 이용할 수 있도록 마련합니다.",
    "휴게공간":"관람객이 쉬고 재정비할 수 있는 공간으로 주요 동선에서 조금 떨어뜨립니다.",
    "푸드존":"음식 냄새와 대기열이 체험·공연 동선에 영향을 덜 주도록 배치합니다.",
    "체험부스":"방문객이 오래 머무는 공간이므로 통로 폭과 대기 공간을 확보합니다.",
    "공연장":"관람객이 모이는 중심 시설로 출입구와 비상 동선을 고려합니다.",
    "흡연실":"비흡연 구역과 충분히 분리하고 출입구·대기열에서 떨어뜨립니다.",
    "방송·음향실":"행사 운영진이 장비를 관리하기 쉽고 공연장과 연결되는 위치가 적합합니다.",
    "분리수거장":"푸드존과 휴게공간에서 접근하기 쉽되 관람 구역과는 분리합니다.",
    "주차장":"주출입구와 연결하되 보행자 동선과 차량 동선을 분리합니다.",
    "물품보관소":"입구 인근에서 이용하기 쉽고 통행을 방해하지 않는 곳에 배치합니다.",
    "운영본부":"행사 전체를 관리할 수 있도록 주요 시설과 연락이 쉬운 곳에 둡니다.",
}

FACILITY_POS = {
    "주출입구":(0.50,0.92),"안내센터":(0.50,0.82),"응급의료센터":(0.86,0.70),
    "화장실":(0.12,0.70),"수유실":(0.16,0.52),"휴게공간":(0.82,0.48),
    "푸드존":(0.75,0.22),"체험부스":(0.30,0.25),"공연장":(0.50,0.48),
    "흡연실":(0.94,0.14),"방송·음향실":(0.62,0.40),"분리수거장":(0.88,0.28),
    "주차장":(0.50,0.02),"물품보관소":(0.30,0.82),"운영본부":(0.18,0.82)
}

def current_data():
    keys = list(defaults.keys())
    return {k: st.session_state.get(k, defaults[k]) for k in keys}

def layout_html(selected):
    # lightweight inline SVG floor plan
    svg = ['<svg viewBox="0 0 900 560" width="100%" style="background:#f8fafc;border:1px solid #dbe4ee;border-radius:14px">']
    svg.append('<rect x="40" y="35" width="820" height="475" rx="24" fill="#ffffff" stroke="#94a3b8" stroke-width="3"/>')
    svg.append('<rect x="55" y="50" width="790" height="445" rx="18" fill="#f1f5f9" stroke="#cbd5e1"/>')
    # central walkway and zones
    svg.append('<rect x="390" y="60" width="120" height="425" fill="#e2e8f0"/>')
    svg.append('<rect x="70" y="245" width="760" height="70" fill="#e2e8f0"/>')
    svg.append('<rect x="345" y="170" width="210" height="150" rx="12" fill="#dbeafe" stroke="#60a5fa"/>')
    svg.append('<text x="450" y="245" font-size="24" text-anchor="middle" fill="#1d4ed8" font-weight="bold">중앙 공연·행사 공간</text>')
    labels = {
      "주출입구":"입구","안내센터":"안내","응급의료센터":"응급","화장실":"화장실","수유실":"수유실",
      "휴게공간":"휴게","푸드존":"푸드존","체험부스":"체험","공연장":"공연장","흡연실":"흡연실",
      "방송·음향실":"방송실","분리수거장":"분리수거","주차장":"주차장","물품보관소":"보관소","운영본부":"운영본부"
    }
    colors_map = {"주출입구":"#f59e0b","응급의료센터":"#ef4444","공연장":"#2563eb","푸드존":"#f97316","체험부스":"#8b5cf6","수유실":"#ec4899"}
    for name in st.session_state.facilities:
        if name not in FACILITY_POS: continue
        x,y = FACILITY_POS[name]
        px,py = 70+x*760, 60+(1-y)*410
        fill = colors_map.get(name, "#0f766e")
        stroke = "#0f172a" if name == selected else "#ffffff"
        sw = 5 if name == selected else 2
        svg.append(f'<rect x="{px-48}" y="{py-24}" width="96" height="48" rx="9" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')
        svg.append(f'<text x="{px}" y="{py+5}" font-size="14" text-anchor="middle" fill="white" font-weight="bold">{labels.get(name,name)}</text>')
    # entry arch facing parking (schematic arrow)
    svg.append('<path d="M450 520 L450 490" stroke="#f59e0b" stroke-width="8" stroke-linecap="round"/>')
    svg.append('<path d="M438 500 L450 488 L462 500" fill="none" stroke="#f59e0b" stroke-width="8"/>')
    svg.append('<text x="450" y="545" font-size="18" text-anchor="middle" fill="#92400e" font-weight="bold">주차장 방향 주출입구</text>')
    svg.append('</svg>')
    return "".join(svg)

def make_pdf(data):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=18*mm, leftMargin=18*mm, topMargin=16*mm, bottomMargin=16*mm)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="KTitle", parent=styles["Title"], fontName="Helvetica", fontSize=20, leading=25, textColor=colors.HexColor("#17324d"), spaceAfter=8))
    styles.add(ParagraphStyle(name="KBody", parent=styles["BodyText"], fontSize=9.5, leading=14))
    story = [Paragraph("Event ON 행사 설계 보고서", styles["KTitle"]),
             Paragraph(f"작성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles["KBody"]), Spacer(1,5*mm)]
    rows = [
      ["항목","설계 내용"],
      ["행사명", str(data.get("event_name",""))],
      ["행사 유형", str(data.get("event_type",""))],
      ["목적", str(data.get("purpose",""))],
      ["장소 / 운영 환경", f'{data.get("venue","")} · {data.get("indoor_outdoor","")}'],
      ["일정", f'{data.get("event_date","")} / {data.get("event_days","")}일 / {data.get("start_time","")}~{data.get("end_time","")}'],
      ["예상 방문객", f'{int(data.get("visitor_count",0)):,}명'],
      ["대상 연령", str(data.get("age_group",""))],
      ["분위기", str(data.get("mood",""))],
      ["예산", f'{int(data.get("budget",0)):,}원'],
      ["입장료", "무료" if data.get("ticket_type")=="무료" else f'{int(data.get("ticket_price",0)):,}원'],
      ["시설", ", ".join(data.get("facilities",[]))],
      ["추가 요청", str(data.get("extra_request","없음"))],
    ]
    table = Table(rows, colWidths=[35*mm, 135*mm], repeatRows=1)
    table.setStyle(TableStyle([
      ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#17324d")),
      ("TEXTCOLOR",(0,0),(-1,0),colors.white),("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
      ("GRID",(0,0),(-1,-1),0.4,colors.HexColor("#cbd5e1")),
      ("BACKGROUND",(0,1),(0,-1),colors.HexColor("#eef4fa")),
      ("VALIGN",(0,0),(-1,-1),"TOP"),("FONTSIZE",(0,0),(-1,-1),9),
      ("LEFTPADDING",(0,0),(-1,-1),7),("RIGHTPADDING",(0,0),(-1,-1),7),
      ("TOPPADDING",(0,0),(-1,-1),6),("BOTTOMPADDING",(0,0),(-1,-1),6),
    ]))
    story += [table, Spacer(1,5*mm), Paragraph("시설 배치 원칙", styles["Heading2"])]
    notes = [
      "주출입구와 주차장 사이 보행자·차량 동선을 분리합니다.",
      "응급의료센터는 주요 행사 공간에서 접근하기 쉬운 위치에 둡니다.",
      "푸드존·체험부스의 대기열이 중앙 통로를 막지 않도록 여유 공간을 확보합니다.",
      "수유실·휴게공간은 안내 표지를 설치하고 조용한 구역에 배치합니다.",
      "실제 행사 전에는 현장 답사, 소방·전기·시설 안전 점검 및 관계 기관 확인이 필요합니다."
    ]
    story += [Paragraph("• " + n, styles["KBody"]) for n in notes]
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

# ---------- sidebar ----------
with st.sidebar:
    st.markdown("## 🎪 Event ON")
    st.caption("AI 기반 행사 자동 설계 플랫폼")
    if st.session_state.logged_in:
        st.markdown(f"**{st.session_state.display_name} ({st.session_state.role})님**")
    else:
        st.caption("로그인하지 않은 상태")
    st.divider()
    nav = st.radio("메뉴", ["홈","대시보드","AI 보고서 다운로드","저장 프로젝트","설정"], index=["홈","대시보드","AI 보고서 다운로드","저장 프로젝트","설정"].index(st.session_state.page))
    st.session_state.page = nav
    st.divider()
    with st.expander("계정"):
        if not st.session_state.logged_in:
            name = st.text_input("이름", key="login_name")
            role = st.selectbox("역할", ["행사 설계자","관리자","담당자"], key="login_role")
            if st.button("로그인", use_container_width=True):
                st.session_state.display_name = name.strip() or "사용자"
                st.session_state.role = role
                st.session_state.logged_in = True
                st.rerun()
            if st.button("회원가입", use_container_width=True):
                st.info("데모용 회원가입: 이름과 역할을 입력한 뒤 로그인 버튼을 눌러 주세요.")
        else:
            if st.button("로그아웃", use_container_width=True):
                st.session_state.logged_in = False
                st.rerun()

# ---------- home ----------
if st.session_state.page == "홈":
    st.markdown("# 🎪 Event ON")
    st.markdown("### 행사 기획부터 공간 배치와 보고서까지, 한 화면에서")
    st.markdown("<div class='small-note'>행사 정보를 입력하면 시설 구성과 배치 초안을 만들고 PDF 보고서로 저장할 수 있습니다.</div>", unsafe_allow_html=True)
    st.write("")
    c1,c2 = st.columns(2, gap="large")
    with c1:
        with st.container(border=True):
            st.markdown("## 🗺️ 대시보드")
            st.write("행사 정보 입력 · 시설 구성 · 공간 배치")
            if st.button("대시보드 열기 →", type="primary", use_container_width=True):
                st.session_state.page = "대시보드"; st.rerun()
    with c2:
        with st.container(border=True):
            st.markdown("## 📄 AI 보고서 다운로드")
            st.write("행사 계획과 시설 배치 원칙을 PDF로 정리")
            if st.button("보고서 만들기 →", use_container_width=True):
                st.session_state.page = "AI 보고서 다운로드"; st.rerun()
    st.write("")
    st.markdown("### Event ON에서 할 수 있는 일")
    a,b,c = st.columns(3)
    a.info("**행사 정보 정리**\n\n행사 유형, 일정, 방문객, 예산 입력")
    b.info("**공간 구성**\n\n필수 시설을 선택하고 배치 초안 확인")
    c.info("**보고서 출력**\n\n입력한 내용을 PDF로 내려받기")

# ---------- dashboard ----------
elif st.session_state.page == "대시보드":
    st.markdown("# 🗺️ 행사 설계 대시보드")
    st.caption("화면을 넓게 사용하도록 구성한 간결한 설계 화면입니다.")
    # top row metrics
    m1,m2,m3,m4 = st.columns(4)
    m1.metric("예상 방문객", f'{int(st.session_state.visitor_count):,}명')
    m2.metric("운영 기간", f'{int(st.session_state.event_days)}일')
    m3.metric("예산", f'{int(st.session_state.budget):,}원')
    m4.metric("선택 시설", f'{len(st.session_state.facilities)}개')
    left,right = st.columns([1.02,1.18], gap="medium")
    with left:
        with st.container(border=True):
            st.markdown("### 행사 기본 정보")
            st.text_input("행사명", key="event_name")
            st.selectbox("행사 유형", ["지역 축제","박람회","공연·콘서트","학교 행사","기업 행사","체험 행사","전시회","기타"], key="event_type")
            st.text_input("행사 목적", key="purpose")
            st.selectbox("행사 장소", ["실내 전시장","야외 광장","학교 운동장","컨벤션센터","공원","복합 행사장"], key="venue")
            q1,q2 = st.columns(2)
            q1.number_input("예상 방문객 수", min_value=1, max_value=500000, step=100, key="visitor_count")
            q2.number_input("운영 일수", min_value=1, max_value=60, key="event_days")
            q3,q4 = st.columns(2)
            q3.date_input("행사 날짜", key="event_date")
            q4.selectbox("실내 / 실외", ["실내","실외","실내·실외 혼합"], key="indoor_outdoor")
            q5,q6 = st.columns(2)
            q5.time_input("시작 시간", key="start_time")
            q6.time_input("종료 시간", key="end_time")
            q7,q8 = st.columns(2)
            q7.selectbox("분위기", ["활기찬","감성적인","전문적인","가족 친화적"], key="mood")
            q8.selectbox("예상 연령대", ["전 연령","유아·어린이","청소년","청년","성인","중장년·어르신"], key="age_group")
            q9,q10 = st.columns(2)
            q9.selectbox("입장료 유형", ["무료","유료"], key="ticket_type")
            q10.number_input("입장료(원)", min_value=0, step=1000, key="ticket_price", disabled=st.session_state.ticket_type=="무료")
            st.number_input("총 예산(원)", min_value=0, step=100000, key="budget")
            st.text_area("추가 요청사항", key="extra_request", height=65)
            if st.button("💾 행사 정보 저장", type="primary", use_container_width=True):
                save_project(current_data())
                st.success("현재 행사 정보를 저장했어.")
    with right:
        with st.container(border=True):
            st.markdown("### 행사장 배치 모형")
            st.markdown(layout_html(st.session_state.selected_booth), unsafe_allow_html=True)
            st.caption("도식은 배치 아이디어를 위한 개념도이며 실제 축척·시설 규격을 반영한 설계도는 아닙니다.")
            st.markdown("#### 시설 선택 및 배치 설명")
            choices = [x for x in st.session_state.facilities if x in FACILITY_INFO]
            if choices:
                st.selectbox("시설 선택", choices, key="selected_booth")
                st.info(FACILITY_INFO.get(st.session_state.selected_booth, "시설의 운영 목적과 동선을 고려해 배치합니다."))
            else:
                st.warning("왼쪽 설정에서 시설을 선택해 주세요.")
            with st.expander("시설 구성 편집"):
                all_fac = ["주출입구","안내센터","공연장","푸드존","체험부스","휴게공간","응급의료센터","화장실","수유실","흡연실","방송·음향실","분리수거장","주차장","물품보관소","운영본부"]
                st.session_state.facilities = st.multiselect("행사장에 포함할 시설", all_fac, default=[x for x in st.session_state.facilities if x in all_fac])
            st.checkbox("혼잡도 시뮬레이션 표시", key="show_congestion")
            if st.session_state.show_congestion:
                people = min(60, max(8, int(st.session_state.visitor_count)//20))
                dots = " ".join(["🟠" if i%4==0 else "🔵" for i in range(people)])
                st.markdown("**방문객 흐름 예시 (실시간 측정값이 아닌 시뮬레이션)**")
                st.markdown(dots)
                st.caption("실제 인원 추적·실시간 혼잡 측정 기능은 연결되어 있지 않습니다.")

# ---------- report ----------
elif st.session_state.page == "AI 보고서 다운로드":
    st.markdown("# 📄 AI 보고서 다운로드")
    data = current_data()
    st.write("현재 입력된 행사 정보로 PDF 보고서를 생성합니다.")
    with st.container(border=True):
        st.markdown("### 보고서 미리보기")
        st.write(f"**{data['event_name']}** · {data['event_type']} · {data['venue']}")
        st.write(f"예상 방문객 {int(data['visitor_count']):,}명 | {data['event_days']}일 | 예산 {int(data['budget']):,}원")
        st.write("포함 시설: " + ", ".join(data["facilities"]))
        st.caption("보고서에는 행사 개요, 일정, 예산, 시설 목록, 배치 원칙 및 안전 확인 사항이 포함됩니다.")
    try:
        pdf_bytes = make_pdf(data)
        st.download_button("⬇️ PDF 보고서 다운로드", data=pdf_bytes, file_name="Event_ON_행사설계_보고서.pdf", mime="application/pdf", type="primary")
    except Exception as e:
        st.error(f"PDF 생성 중 오류: {e}")
    if st.button("대시보드에서 정보 수정"):
        st.session_state.page = "대시보드"; st.rerun()

# ---------- saved projects ----------
elif st.session_state.page == "저장 프로젝트":
    st.markdown("# 📁 저장 프로젝트")
    projects = load_projects()
    if not projects:
        st.info("저장된 프로젝트가 없습니다. 대시보드에서 행사 정보를 저장해 주세요.")
    else:
        for pid,title,created,data_json in projects:
            with st.container(border=True):
                col1,col2,col3 = st.columns([3,2,1])
                col1.markdown(f"**{title}**")
                col2.caption(created)
                if col3.button("불러오기", key=f"load_{pid}"):
                    data = json.loads(data_json)
                    for key,value in data.items():
                        if key in defaults: st.session_state[key] = value
                    st.session_state.page = "대시보드"; st.rerun()
                if st.button("삭제", key=f"delete_{pid}"):
                    delete_project(pid); st.rerun()

# ---------- settings ----------
elif st.session_state.page == "설정":
    st.markdown("# ⚙️ 설정")
    tab1,tab2,tab3,tab4,tab5,tab6 = st.tabs(["계정 및 프로필","보고서 설정","화면 설정","AI 분석 설정","프로젝트 및 저장 관리","보안 및 계정 관리"])
    with tab1:
        st.text_input("표시 이름", key="display_name")
        st.selectbox("역할", ["행사 설계자","관리자","담당자"], key="role")
        st.text_input("소속 / 부서", key="department", value=st.session_state.get("department",""))
        st.button("프로필 저장", on_click=lambda: st.success("프로필 설정을 적용했어."))
    with tab2:
        st.checkbox("보고서에 행사장 배치 원칙 포함", value=True)
        st.checkbox("보고서에 안전 점검 안내 포함", value=True)
        st.selectbox("보고서 용지", ["A4 세로","A4 가로"])
        st.caption("PDF 보고서는 현재 A4 세로 형식으로 생성됩니다.")
    with tab3:
        st.selectbox("화면 테마", ["밝은 테마","기본 테마"])
        st.caption("현재 기본 화면은 밝은 테마입니다.")
    with tab4:
        st.slider("방문객 밀도 시뮬레이션 강도", 1, 10, 5)
        st.caption("실제 AI 예측 모델이 아닌 설정용 데모 값입니다.")
    with tab5:
        st.write(f"저장된 프로젝트: {len(load_projects())}개")
        if st.button("저장 프로젝트 모두 삭제"):
            with sqlite3.connect(DB_PATH) as conn: conn.execute("DELETE FROM projects")
            st.success("프로젝트를 삭제했어.")
    with tab6:
        st.warning("이 앱의 로그인은 데모용이며 실제 인증·암호화·권한 검증 기능이 아닙니다.")
        st.checkbox("로그인 상태 유지 (세션 동안)")
        if st.button("로그아웃"):
            st.session_state.logged_in=False; st.rerun()

st.markdown("---")
st.caption("Event ON · 행사장 배치와 PDF는 기획 보조용 초안입니다. 실제 행사 운영 전에는 현장·안전·법규 검토가 필요합니다.")
