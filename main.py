import streamlit as st
import datetime
import time
import json
from google import genai
from google.genai import types
from supabase import create_client, Client

# --- 1. 페이지 기본 설정 ---
st.set_page_config(
    page_title="고등학생 성취감 메이커 - AI 레벨업 학습 플래너",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. Custom CSS ---
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
    .quiz-box {
        background-color: #FFFFFF;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #E2E8F0;
        margin-bottom: 15px;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. API & DB 연결 ---
use_supabase = "SUPABASE_URL" in st.secrets and "SUPABASE_KEY" in st.secrets
if use_supabase:
    @st.cache_resource
    def init_supabase() -> Client:
        return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    supabase = init_supabase()
    USER_ID = "default_user"

# --- 4. DB 저장/로드 로직 ---
def load_data():
    if use_supabase:
        try:
            res = supabase.table("user_data").select("*").eq("user_id", USER_ID).execute()
            if res.data:
                return res.data[0]
            else:
                init_rec = {"user_id": USER_ID, "exp": 0, "todos": [], "notes": []}
                supabase.table("user_data").insert(init_rec).execute()
                return init_rec
        except Exception as e:
            st.error(f"DB 로드 실패 (로컬 세션 사용): {e}")
    return {"exp": 0, "todos": [], "notes": []}

def save_data():
    if use_supabase:
        try:
            supabase.table("user_data").update({
                "exp": st.session_state.exp,
                "todos": st.session_state.todos,
                "notes": st.session_state.notes
            }).eq("user_id", USER_ID).execute()
        except Exception as e:
            st.error(f"DB 저장 실패: {e}")

# --- 5. 세션 상태 초기화 ---
if "initialized" not in st.session_state:
    db_data = load_data()
    st.session_state.exp = db_data.get("exp", 0)
    st.session_state.todos = db_data.get("todos", [])
    st.session_state.notes = db_data.get("notes", [])
    st.session_state.initialized = True

if "quiz_data" not in st.session_state:
    st.session_state.quiz_data = None
if "user_answers" not in st.session_state:
    st.session_state.user_answers = {}
if "quiz_submitted" not in st.session_state:
    st.session_state.quiz_submitted = False

# --- 6. 레벨 & 경험치 로직 ---
EXP_PER_TASK = 20
EXP_PER_LEVEL = 100

current_level = (st.session_state.exp // EXP_PER_LEVEL) + 1
current_level_exp = st.session_state.exp % EXP_PER_LEVEL
progress_percentage = min(current_level_exp / EXP_PER_LEVEL, 1.0)

def get_character_info(level):
    if level == 1:
        return "🥚", "알 단계", "막 공부를 시작하려는 소중한 알입니다."
    elif level == 2:
        return "🐣", "갓 깨어난 병아리", "조금씩 지식을 흡수하며 깨어났어요!"
    elif level == 3:
        return "🐥", "열공 병아리", "책을 들고 몰입 중인 당당한 병아리!"
    elif level == 4:
        return "🦅", "멋진 독수리", "이제 어려운 문제도 쉽게 파헤쳐요!"
    else:
        return "👑🦅", "공부의 신 독수리 왕", "모든 목표를 정복한 완벽한 공부 마스터!"

char_icon, char_title, char_desc = get_character_info(current_level)

# --- 7. 최신 google-genai 기반 AI 문제 생성 함수 ---
def generate_ai_quiz(prompt_info, num_questions):
    with st.spinner("Gemini AI가 맞춤형 문제를 생성 중입니다..."):
        try:
            client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
            
            prompt = f"""
            너는 고등학교 전문 교사야. 아래 정보와 조건을 바탕으로 객관식 문제를 JSON 형식으로만 생성해줘.
            
            {prompt_info}
            [문제 수]: {num_questions}개

            응답은 반드시 마크다운 코드블록 없이 순수 JSON 객체 배열 형태로 작성해야 해:
            [
              {{
                "id": 1,
                "question": "문제 내용",
                "options": ["1번 보기", "2번 보기", "3번 보기", "4번 보기"],
                "answer": "정답 보기 문자열과 정확히 일치하는 텍스트",
                "explanation": "해설 내용"
              }}
            ]
            """
            
            # 최신 gemini-3.8-flash 모델 적용
            response = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            
            clean_text = response.text.strip().replace("```json", "").replace("```", "")
            quiz_json = json.loads(clean_text)
            
            st.session_state.quiz_data = quiz_json
            st.session_state.user_answers = {}
            st.session_state.quiz_submitted = False
            st.success("문제 출제가 완료되었습니다! 아래에서 풀어보세요.")
            st.rerun()
        except Exception as e:
            st.error(f"문제 생성 중 오류가 발생했습니다: {e}")

# --- 8. 사이드바 ---
st.sidebar.title("🎒 고교 학습 캐리")
st.sidebar.markdown(f"**현재 캐릭터:** {char_icon} **Level {current_level}**")
st.sidebar.progress(progress_percentage)
st.sidebar.caption(f"다음 레벨까지: {EXP_PER_LEVEL - current_level_exp} EXP 필요")

menu = st.sidebar.radio(
    "메뉴 이동:",
    ["🏠 홈 (성장 대시보드 & 투두)", "🤖 AI 맞춤 문제 풀기", "📝 오답 & 학습 노트", "⏱️ 뽀모도로 타이머", "⏳ D-Day 마인드셋"]
)

# --- 9. 메뉴별 페이지 구현 ---

# 🏠 홈 (성장 대시보드 & 투두)
if menu == "🏠 홈 (성장 대시보드 & 투두)":
    st.markdown("<h1 class='main-title'>🔥 오늘 목표를 달성하고 캐릭터를 성장시켜 보세요!</h1>", unsafe_allow_html=True)
    col_char, col_todo = st.columns([1.2, 2])

    with col_char:
        st.markdown("<div class='status-card'>", unsafe_allow_html=True)
        st.markdown(f"<span class='badge'>Lv.{current_level} {char_title}</span>", unsafe_allow_html=True)
        st.markdown(f"<div style='font-size: 5rem; margin: 15px 0;'>{char_icon}</div>", unsafe_allow_html=True)
        st.caption(f"\"{char_desc}\"")
        st.write("---")
        st.markdown(f"**누적 경험치:** `{st.session_state.exp} EXP`")
        st.write("📈 **레벨 진행도**")
        st.progress(progress_percentage)
        st.caption(f"{current_level_exp} / {EXP_PER_LEVEL} EXP")
        st.markdown("</div>", unsafe_allow_html=True)

    with col_todo:
        st.subheader("📌 오늘 끝낼 공부 목록")
        with st.form(key="add_todo_form", clear_on_submit=True):
            col_in1, col_in2 = st.columns([3, 1])
            new_task = col_in1.text_input("새로운 학습 목표", label_visibility="collapsed", placeholder="달성할 공부 목표를 입력하세요!")
            submit_button = col_in2.form_submit_button("추가 (+EXP)")
            
            if submit_button and new_task:
                st.session_state.todos.append({"task": new_task, "done": False})
                save_data()
                st.rerun()

        st.markdown("---")
        if not st.session_state.todos:
            st.info("💡 목표를 등록하고 완료할 때마다 경험치를 받아 캐릭터를 키워보세요!")
        else:
            for i, todo in enumerate(st.session_state.todos):
                c1, c2 = st.columns([0.85, 0.15])
                was_done = todo["done"]
                is_done = c1.checkbox(f"{'~~' + todo['task'] + '~~' if was_done else todo['task']}", value=was_done, key=f"todo_{i}")

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
                    save_data()
                    st.rerun()

                if c2.button("삭제", key=f"del_{i}"):
                    if todo["done"]:
                        st.session_state.exp = max(0, st.session_state.exp - EXP_PER_TASK)
                    st.session_state.todos.pop(i)
                    save_data()
                    st.rerun()

# 🤖 AI 맞춤 문제 풀기
elif menu == "🤖 AI 맞춤 문제 풀기":
    st.title("🤖 AI 맞춤 문제 출제 & 오답 재시험")
    
    tab1, tab2 = st.tabs(["🎯 키워드 기반 출제", "🔄 오답 노트 기반 재시험"])

    with tab1:
        st.write("공부한 단원이나 키워드를 입력하여 문제를 생성합니다.")
        with st.form("generate_quiz_form_keyword"):
            col_q1, col_q2 = st.columns([1, 2])
            subject = col_q1.selectbox("과목 선택", ["국어", "수학", "영어", "한국사", "사회탐구", "과학탐구"], key="kw_sub")
            topic = col_q2.text_input("공부 범위 / 핵심 내용", placeholder="예: 세포호흡과 광합성 / 수학 II 미분계수", key="kw_top")
            num_q = st.slider("문제 수", 1, 3, 2, key="kw_num")
            gen_kw_btn = st.form_submit_button("🔥 키워드로 AI 문제 만들기")

        if gen_kw_btn:
            if not topic.strip():
                st.warning("공부 범위를 입력해 주세요!")
            elif "GEMINI_API_KEY" not in st.secrets:
                st.error("Secrets에 `GEMINI_API_KEY`가 설정되어 있지 않습니다.")
            else:
                prompt_content = f"[과목]: {subject}\n[범위]: {topic}"
                generate_ai_quiz(prompt_content, num_q)

    with tab2:
        st.write("작성해 둔 **오답 노트**를 바탕으로 AI가 핵심 개념을 변형한 **재시험 문제**를 만들어 줍니다!")
        
        if not st.session_state.notes:
            st.info("📌 아직 작성된 오답 노트가 없습니다. '📝 오답 & 학습 노트' 메뉴에서 먼저 오답을 등록해 보세요!")
        else:
            with st.form("generate_quiz_form_note"):
                note_options = [f"[{n['subject']}] {n['title']} ({n['date']})" for n in st.session_state.notes]
                selected_note_str = st.selectbox("재시험을 칠 오답 노트를 선택하세요:", note_options)
                selected_idx = note_options.index(selected_note_str)
                selected_note = st.session_state.notes[selected_idx]
                
                num_q_note = st.slider("재시험 문제 수", 1, 3, 2, key="note_num")
                gen_note_btn = st.form_submit_button("🔥 선택한 오답 기반 재시험 만들기")

            if gen_note_btn:
                if "GEMINI_API_KEY" not in st.secrets:
                    st.error("Secrets에 `GEMINI_API_KEY`가 설정되어 있지 않습니다.")
                else:
                    prompt_content = f"""
                    [학생의 기존 오답 노트 데이터]
                    과목: {selected_note['subject']}
                    제목: {selected_note['title']}
                    오답 및 개념 정리 내용: {selected_note['content']}
                    
                    위 오답 노트 내용의 핵심 개념과 학생이 틀린 지점을 철저히 분석하여, 해당 개념을 확실히 이해했는지 점검할 수 있는 변형 및 유사 문제를 출제해줘.
                    """
                    generate_ai_quiz(prompt_content, num_q_note)

    if st.session_state.quiz_data:
        st.markdown("---")
        st.subheader("📝 AI 실전 테스트")

        for q in st.session_state.quiz_data:
            st.markdown(f"<div class='quiz-box'><b>Q{q['id']}. {q['question']}</b></div>", unsafe_allow_html=True)
            user_choice = st.radio(
                "정답을 선택하세요:", 
                q["options"], 
                key=f"q_{q['id']}", 
                disabled=st.session_state.quiz_submitted
            )
            st.session_state.user_answers[q["id"]] = user_choice
            st.write("")

        if not st.session_state.quiz_submitted:
            if st.button("💯 답안 제출 및 채점하기", use_container_width=True):
                st.session_state.quiz_submitted = True
                st.rerun()
        else:
            st.markdown("### 📊 채점 결과")
            correct_count = 0
            
            for q in st.session_state.quiz_data:
                user_ans = st.session_state.user_answers.get(q["id"])
                is_correct = (user_ans == q["answer"])
                
                if is_correct:
                    correct_count += 1
                    st.success(f"✅ **Q{q['id']}번 정답!** (선택: {user_ans})")
                else:
                    st.error(f"❌ **Q{q['id']}번 오답!** (선택: {user_ans} / 정답: {q['answer']})")
                
                with st.expander(f"💡 Q{q['id']}번 해설 보기"):
                    st.write(q["explanation"])

            gained_exp = correct_count * 10
            if gained_exp > 0:
                st.session_state.exp += gained_exp
                save_data()
                st.toast(f"🎉 {correct_count}문제 정답! +{gained_exp} EXP 획득!", icon="✨")
                st.balloons()

# 📝 오답 & 학습 노트
elif menu == "📝 오답 & 학습 노트":
    st.title("📝 오답 및 개념 정리 노트")
    st.write("이곳에 정리한 오답 노트는 **'🤖 AI 맞춤 문제 풀기'** 메뉴에서 변형 재시험 문제로 바로 출제할 수 있습니다!")

    with st.form("note_form", clear_on_submit=True):
        c_s, c_t = st.columns([1, 2])
        subject = c_s.selectbox("과목", ["국어", "수학", "영어", "한국사", "사회탐구", "과학탐구", "기타"])
        title = c_t.text_input("제목 (예: 수학 II 미분가능성 복습 / 과학 세포호흡)")
        content = st.text_area("복습할 내용 및 틀린 이유 요약", height=150)
        
        if st.form_submit_button("노트 저장"):
            if title and content:
                st.session_state.notes.append({
                    "date": datetime.date.today().strftime("%Y-%m-%d"),
                    "subject": subject,
                    "title": title,
                    "content": content
                })
                save_data()
                st.success("노트가 저장되었습니다!")
                st.rerun()
            else:
                st.warning("제목과 내용을 모두 입력해 주세요.")

    st.markdown("---")
    st.subheader("📚 작성한 오답 노트 목록")
    if not st.session_state.notes:
        st.info("아직 작성된 오답 노트가 없습니다.")
    else:
        for note in reversed(st.session_state.notes):
            with st.expander(f"[{note['subject']}] {note['title']} ({note['date']})"):
                st.write(note['content'])

# ⏱️ 뽀모도로 타이머
elif menu == "⏱️ 뽀모도로 타이머":
    st.title("⏱️ 몰입 스톱워치")
    st.write("25분 몰입 후 5분 휴식 루틴을 가집니다.")
    focus_t = st.number_input("집중 시간(분):", min_value=5, max_value=120, value=25, step=5)

    if st.button("🚀 타이머 시작", use_container_width=True):
        ph = st.empty()
        tot_sec = focus_t * 60
        while tot_sec > 0:
            m, s = divmod(tot_sec, 60)
            ph.markdown(f"<h1 style='text-align: center; color: #E74C3C;'>🔥 남은 시간: {m:02d}:{s:02d}</h1>", unsafe_allow_html=True)
            time.sleep(1)
            tot_sec -= 1
        ph.markdown("<h2 style='text-align: center; color: #2ECC71;'>🎉 집중 종료! 수고하셨습니다.</h2>", unsafe_allow_html=True)
        st.balloons()

# ⏳ D-Day 마인드셋
elif menu == "⏳ D-Day 마인드셋":
    st.title("⏳ 시험 D-Day")
    c_d1, c_d2 = st.columns(2)
    t_name = c_d1.text_input("목표 이름", value="6월 모의고사")
    t_date = c_d2.date_input("목표 날짜", min_value=datetime.date.today())
    days_left = (t_date - datetime.date.today()).days

    st.markdown("<br>", unsafe_allow_html=True)
    if days_left == 0:
        st.error(f"🔥 오늘은 **{t_name}** 당일입니다!")
    else:
        st.info(f"🎯 **{t_name}**까지 **D-{days_left}** 일 남았습니다.")
