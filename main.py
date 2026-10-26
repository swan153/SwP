import streamlit as st
import datetime
import time

# --- 페이지 기본 설정 ---
st.set_page_config(
    page_title="고등학생 성취감 메이커 - 레벨업 학습 플래너",
    page_icon="🐣",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 커스텀 CSS (귀엽고 깔끔한 UI) ---
st.markdown("""
    <style>
    .main-title {
        font-size: 2.2rem;
        font-weight: bold;
        color: #2C3E50;
        text-align: center;
        margin-bottom: 20px;
    }
    .status-card {
        background-color: #F8F9FA;
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        text-align: center;
    }
    .character-stage {
        font-size: 5rem;
        margin: 10px 0;
    }
    .badge {
        display: inline-block;
        background-color: #FFEAA7;
        color: #D35400;
        padding: 5px 12px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 0.9rem;
    }
    </style>
""", unsafe_allow_html=True)

# --- 세션 상태(Session State) 초기화 ---
if "exp" not in st.session_state:
    st.session_state.exp = 0  # 총 경험치

if "todos" not in st.session_state:
    st.session_state.todos = []

if "notes" not in st.session_state:
    st.session_state.notes = []

# --- 캐릭터 성장 관련 시스템 로직 ---
EXP_PER_TASK = 20      # 할 일 1개 완료 시 얻는 EXP
EXP_PER_LEVEL = 100    # 레벨업에 필요한 EXP

current_level = (st.session_state.exp // EXP_PER_LEVEL) + 1
current_level_exp = st.session_state.exp % EXP_PER_LEVEL
progress_percentage = min(current_level_exp / EXP_PER_LEVEL, 1.0)

# 캐릭터 단계 결정 (레벨에 따른 성장)
def get_character_info(level):
    if level == 1:
        return "🥚", "알 단계", "막 공부를 시작하려는 소중한 알입니다."
    elif level == 2:
        return "🐣", "갓 깨어난 병아리", "조금씩 지식을 흡수하며 깨어났어요!"
    elif level == 3:
        return "🐥", "열공 병아리", "책을 들고 열공 중인 당당한 병아리!"
    elif level == 4:
        return "🦅", "멋진 아기 독수리", "이제 난이도 있는 문제도 쉽게 풀어요!"
    else:
        return "👑🦅", "상승하는 독수리 왕", "모든 목표를 파괴하는 완벽한 공부 마스터!"
