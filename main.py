import streamlit as st
import datetime
import pandas as pd
import time

# --- 페이지 기본 설정 ---
st.set_page_config(
    page_title="AI 학생 학습 도우미",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 세션 상태(Session State) 초기화 ---
if "todos" not in st.session_state:
    st.session_state.todos = []

if "notes" not in st.session_state:
    st.session_state.notes = []

# --- 사이드바 메뉴 ---
st.sidebar.title("🎓 학습 도우미 메뉴")
menu = st.sidebar.radio(
    "원하는 기능을 선택하세요:",
    ["🏠 홈 & 대시보드", "⏱️ 뽀모도로 / 공부 스톱워치", "📅 학습 플래너 (To-Do)", "📝 학습 정리 노트", "⏳ D-Day 계산기"]
)

st.sidebar.markdown("---")
st.sidebar.info("💡 앞으로 피드백을 주시면 새로운 기능과 디자인을 계속 추가할 수 있습니다!")

# --- 1. 홈 & 대시보드 ---
if menu == "🏠 홈 & 대시보드":
    st.title("👋 환영합니다! 오늘도 열공해봐요!")
    st.subheader("오늘의 학습 대시보드")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="남은 할 일", value=f"{len([t for t in st.session_state.todos if not t['done']])} 개")
    with col2:
        st.metric(label="완료한 할 일", value=f"{len([t for t in st.session_state.todos if t['done']])} 개")
    with col3:
        st.metric(label="작성한 학습 노트", value=f"{len(st.session_state.notes)} 개")

    st.markdown("---")
    st.markdown("### 📌 오늘의 한 마디")
    st.success("“성공은 매일 반복되는 작은 노력들의 합이다.” – 로버트 콜리어")

# --- 2. 뽀모도로 / 공부 스톱워치 ---
elif menu == "⏱️ 뽀모도로 / 공부 스톱워치":
    st.title("⏱️ 뽀모도로 타이머")
    st.write("25분 동안 집중해서 공부하고 5분간 휴식해보세요!")

    timer_minutes = st.number_input("집중 시간(분 단위):", min_value=1, max_value=120, value=25)
    
    if st.button("🚀 타이머 시작"):
        ph = st.empty()
        total_seconds = timer_minutes * 60
        
        while total_seconds > 0:
            mins, secs = divmod(total_seconds, 60)
            time_format = f"{mins:02d}:{secs:02d}"
            ph.header(f"⏳ 남은 시간: {time_format}")
            time.sleep(1)
            total_seconds -= 1
        
        ph.subheader("🎉 시간 종료! 참 잘했어요. 잠시 휴식을 취하세요.")
        st.balloons()

# --- 3. 학습 플래너 (To-Do List) ---
elif menu == "📅 학습 플래너 (To-Do)":
    st.title("📅 투두리스트 & 학습 플래너")
    
    # 새 할 일 추가
    with st.form(key="add_todo_form", clear_on_submit=True):
        new_task = st.text_input("새로운 할 일을 입력하세요:")
        submit_button = st.form_submit_button(label="추가")
        
        if submit_button and new_task:
            st.session_state.todos.append({"task": new_task, "done": False})
            st.rerun()

    st.markdown("### 📋 할 일 목록")
    if not st.session_state.todos:
        st.info("아직 등록된 할 일이 없습니다.")
    else:
        for i, todo in enumerate(st.session_state.todos):
            col1, col2 = st.columns([0.8, 0.2])
            is_done = col1.checkbox(todo["task"], value=todo["done"], key=f"todo_{i}")
            st.session_state.todos[i]["done"] = is_done
            
            if col2.button("삭제", key=f"del_{i}"):
                st.session_state.todos.pop(i)
                st.rerun()

# --- 4. 학습 정리 노트 ---
elif menu == "📝 학습 정리 노트":
    st.title("📝 학습 정리 노트")
    
    subject = st.text_input("과목명:")
    title = st.text_input("노트 제목:")
    content = st.text_area("내용 요약 및 핵심 정리:", height=200)
    
    if st.button("노트 저장"):
        if subject and title and content:
            st.session_state.notes.append({
                "date": datetime.date.today().strftime("%Y-%m-%d"),
                "subject": subject,
                "title": title,
                "content": content
            })
            st.success("노트가 저장되었습니다!")
        else:
            st.warning("과목명, 제목, 내용을 모두 입력해 주세요.")

    st.markdown("---")
    st.subheader("📚 저장된 학습 노트")
    if not st.session_state.notes:
        st.info("저장된 노트가 없습니다.")
    else:
        for idx, note in enumerate(reversed(st.session_state.notes)):
            with st.expander(f"[{note['subject']}] {note['title']} ({note['date']})"):
                st.write(note['content'])

# --- 5. D-Day 계산기 ---
elif menu == "⏳ D-Day 계산기":
    st.title("⏳ 시험 & 목표 D-Day 계산기")
    
    target_name = st.text_input("목표 또는 시험 이름 (예: 중간고사, 수능, 자격증 시험):", value="중간고사")
    target_date = st.date_input("목표 날짜 선택:", min_value=datetime.date.today())
    
    today = datetime.date.today()
    days_left = (target_date - today).days
    
    if days_left == 0:
        st.error(f"🚨 오늘은 **{target_name}** 당일입니다! 파이팅!")
    else:
        st.success(f"🎯 **{target_name}**까지 **D-{days_left}** 일 남았습니다!")
