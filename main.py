import streamlit as st
import datetime
import time

# --- 페이지 기본 설정 ---
st.set_page_config(
    page_title="고등학생 성취감 메이커 - 레벨업 학습 플래너",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 커스텀 CSS ---
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

# --- 세션 상태 초기화 ---
if "exp" not in st.session_state:
    st.session_state.exp = 0

if "todos" not in st.session_state:
    st.session_state.todos = []

if "notes" not in st.session_state:
    st.session_state.notes = []

# --- 캐릭터 성장 로직 (이미지 URL 적용) ---
EXP_PER_TASK = 20
EXP_PER_LEVEL = 100

current_level = (st.session_state.exp // EXP_PER_LEVEL) + 1
current_level_exp = st.session_state.exp % EXP_PER_LEVEL
progress_percentage = min(current_level_exp / EXP_PER_LEVEL, 1.0)

def get_character_info(level):
    # 각 레벨별 캐릭터 이미지 URL 및 설명 설정
    # (원하는 이미지 URL이나 파일 경로 'assets/level1.png' 등으로 자유롭게 교체 가능합니다)
    if level == 1:
        return (
            "https://cdn-icons-png.flaticon.com/512/824/824239.png", 
            "알 단계", 
            "막 공부를 시작하려는 소중한 알입니다."
        )
    elif level == 2:
        return (
            "https://cdn-icons-png.flaticon.com/512/4825/4825038.png", 
            "갓 깨어난 병아리", 
            "조금씩 지식을 흡수하며 깨어났어요!"
        )
    elif level == 3:
        return (
            "https://cdn-icons-png.flaticon.com/512/3069/3069172.png", 
            "열공 병아리", 
            "책을 들고 몰입 중인 당당한 병아리!"
        )
    elif level == 4:
        return (
            "https://cdn-icons-png.flaticon.com/512/3069/3069224.png", 
            "멋진 독수리", 
            "이제 어려운 문제도 쉽게 파헤쳐요!"
        )
    else:
        return (
            "https://cdn-icons-png.flaticon.com/512/2583/2583344.png", 
            "공부의 신 독수리 왕", 
            "모든 목표를 정복한 완벽한 공부 마스터!"
        )

char_img, char_title, char_desc = get_character_info(current_level)


# --- 사이드바 메뉴 ---
st.sidebar.title("🎒 고교 학습 캐리")
st.sidebar.markdown(f"**현재 캐릭터:** **Level {current_level}**")
st.sidebar.image(char_img, width=80)
st.sidebar.progress(progress_percentage)
st.sidebar.caption(f"다음 레벨까지: {EXP_PER_LEVEL - current_level_exp} EXP 필요")

menu = st.sidebar.radio(
    "메뉴 이동:",
    ["🏠 홈 (성장 대시보드 & 투두)", "⏱️ 뽀모도로 타이머", "📝 오답 & 학습 노트", "⏳ D-Day 마인드셋"]
)


# --- 1. 홈 (성장 대시보드 & 성취감 투두리스트) ---
if menu == "🏠 홈 (성장 대시보드 & 투두)":
    st.markdown("<h1 class='main-title'>🔥 오늘 목표를 달성하고 캐릭터를 성장시켜 보세요!</h1>", unsafe_allow_html=True)
    
    col_char, col_todo = st.columns([1.2, 2])

    # [좌측] 성장하는 캐릭터 영역
    with col_char:
        st.markdown("<div class='status-card'>", unsafe_allow_html=True)
        st.markdown(f"<span class='badge'>Lv.{current_level} {char_title}</span>", unsafe_allow_html=True)
        
        # 이미지 출력 (st.image 활용)
        st.markdown("<br>", unsafe_allow_html=True)
        st.image(char_img, width=160)
        
        st.caption(f"\"{char_desc}\"")
        
        st.write("---")
        st.markdown(f"**누적 경험치:** `{st.session_state.exp} EXP`")
        st.write("📈 **레벨 진행도**")
        st.progress(progress_percentage)
        st.caption(f"{current_level_exp} / {EXP_PER_LEVEL} EXP")
        st.markdown("</div>", unsafe_allow_html=True)

    # [우측] 성취감 투두리스트 영역
    with col_todo:
        st.subheader("📌 오늘 끝낼 공부 목록")
        
        with st.form(key="add_todo_form", clear_on_submit=True):
            col_in1, col_in2 = st.columns([3, 1])
            new_task = col_in1.text_input(
                "새로운 학습 목표 (예: 수학 모의고사 1회 풀기, 영어 단어 30개)", 
                label_visibility="collapsed", 
                placeholder="달성할 공부 목표를 입력하세요!"
            )
            submit_button = col_in2.form_submit_button("추가 (+EXP)")
            
            if submit_button and new_task:
                st.session_state.todos.append({"task": new_task, "done": False})
                st.rerun()

        st.markdown("---")

        if not st.session_state.todos:
            st.info("💡 목표를 등록하고 완료할 때마다 경험치를 받아 캐릭터를 키워보세요!")
        else:
            for i, todo in enumerate(st.session_state.todos):
                c1, c2 = st.columns([0.85, 0.15])
                
                was_done = todo["done"]
                is_done = c1.checkbox(
                    f"{'~~' + todo['task'] + '~~' if was_done else todo['task']}",
                    value=was_done,
                    key=f"todo_{i}"
                )

                if is_done != was_done:
                    st.session_state.todos[i]["done"] = is_done
                    if is_done:
                        st.session_state.exp += EXP_PER_TASK
                        st.toast(f"🎉 목표 달성! +{EXP_PER_TASK} EXP 획득!", icon="✨")
                        if (st.session_state.exp // EXP_PER_LEVEL) + 1 > current_level:
                            st.balloons()
                            st.success(f"🎊 레벨 업! **Lv.{current_level + 1}** 이 되었습니다!")
                    else:
                        st.session_state.exp = max(0, st.session_state.exp - EXP_PER_TASK)
                    st.rerun()

                if c2.button("삭제", key=f"del_{i}"):
                    if todo["done"]:
                        st.session_state.exp = max(0, st.session_state.exp - EXP_PER_TASK)
                    st.session_state.todos.pop(i)
                    st.rerun()


# --- 2. 뽀모도로 타이머 ---
elif menu == "⏱️ 뽀모도로 타이머":
    st.title("⏱️ 몰입 스톱워치 (뽀모도로)")
    st.write("25분 몰입, 5분 휴식 루틴으로 공부 효율을 높이세요.")

    col1, col2 = st.columns(2)
    with col1:
        focus_time = st.number_input("집중 시간(분):", min_value=5, max_value=120, value=25, step=5)
    with col2:
        break_time = st.number_input("휴식 시간(분):", min_value=1, max_value=30, value=5, step=1)

    if st.button("🚀 타이머 시작", use_container_width=True):
        ph = st.empty()
        total_seconds = focus_time * 60
        
        while total_seconds > 0:
            mins, secs = divmod(total_seconds, 60)
            time_format = f"{mins:02d}:{secs:02d}"
            ph.markdown(f"<h1 style='text-align: center; color: #E74C3C;'>🔥 집중 시간: {time_format}</h1>", unsafe_allow_html=True)
            time.sleep(1)
            total_seconds -= 1
        
        ph.markdown("<h2 style='text-align: center; color: #2ECC71;'>🎉 수고하셨습니다! 맛있는 휴식을 취하세요!</h2>", unsafe_allow_html=True)
        st.balloons()


# --- 3. 오답 & 학습 노트 ---
elif menu == "📝 오답 & 학습 노트":
    st.title("📝 오답 및 핵심 개념 정리")
    st.write("틀린 이유나 꼭 기억해야 할 공식을 정리해 두세요.")

    with st.form("note_form", clear_on_submit=True):
        col_sub, col_title = st.columns([1, 2])
        subject = col_sub.selectbox("과목", ["국어", "수학", "영어", "한국사", "탐구(사회/과학)", "기타"])
        title = col_title.text_input("제목 (예: 수학 II 미분가능성 복습)")
        content = st.text_area("내용 요약 및 복습 키포인트", height=150)
        
        save_btn = st.form_submit_button("노트 저장")
        if save_btn:
            if title and content:
                st.session_state.notes.append({
                    "date": datetime.date.today().strftime("%Y-%m-%d"),
                    "subject": subject,
                    "title": title,
                    "content": content
                })
                st.success("노트가 저장되었습니다!")
                st.rerun()
            else:
                st.warning("제목과 내용을 입력해 주세요.")

    st.markdown("---")
    st.subheader("📚 작성한 노트 목록")
    if not st.session_state.notes:
        st.info("아직 작성된 학습 노트가 없습니다.")
    else:
        for note in reversed(st.session_state.notes):
            with st.expander(f"[{note['subject']}] {note['title']} ({note['date']})"):
                st.write(note['content'])


# --- 4. D-Day 마인드셋 ---
elif menu == "⏳ D-Day 마인드셋":
    st.title("⏳ 시험 & 목표 D-Day")
    
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        target_name = st.text_input("목표 이름", value="6월 모의고사 / 기말고사")
    with col_d2:
        target_date = st.date_input("목표 날짜", min_value=datetime.date.today())

    today = datetime.date.today()
    days_left = (target_date - today).days

    st.markdown("<br>", unsafe_allow_html=True)
    if days_left == 0:
        st.error(f"🔥 오늘은 **{target_name}** 당일입니다! 지금까지 노력한 자신을 믿으세요!")
    else:
        st.info(f"🎯 **{target_name}**까지 **D-{days_left}** 일 남았습니다. 매일 하나씩 목표를 채워가세요!")
