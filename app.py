import streamlit as st
import time
import json
import re
import os

st.set_page_config(page_title="MCQ Exam App", layout="centered")

# ----------------------------------------------------
# PARSER FOR MIXED questions.txt
# ----------------------------------------------------
QUESTIONS_DIR = "questions"
def load_subjects():
    subjects = {}
    if not os.path.exists(QUESTIONS_DIR):
        return subjects

    for file in os.listdir(QUESTIONS_DIR):
        if file.endswith(".json") or file.endswith(".txt"):
            name = file.replace(".json", "").replace(".txt", "")
            name = name.replace("_", " ").title()
            subjects[name] = os.path.join(QUESTIONS_DIR, file)
    return subjects

SUBJECTS = load_subjects()
def extract_questions(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()

    questions = []

    arrays = re.findall(r'\[\s*{.*?}\s*\]', text, re.DOTALL)
    for block in arrays:
        try:
            questions.extend(json.loads(block))
        except:
            pass

    objects = re.findall(r'\{\s*"questions"\s*:\s*\[.*?\]\s*\}', text, re.DOTALL)
    for block in objects:
        try:
            data = json.loads(block)
            questions.extend(data.get("questions", []))
        except:
            pass

    return questions


# ----------------------------------------------------
# LOAD QUESTIONS
# ----------------------------------------------------
# file_path = SUBJECTS[subject]
# questions = extract_questions(file_path)

# if not questions:
#     st.error("❌ No valid questions found.")
#     st.stop()

# TOTAL = len(questions)

# ====================================================
# SESSION STATE INIT
# ====================================================
def init_session():
    defaults = {
        "subject": None,
        "questions": None,
        "index": 0,
        "responses": {},
        "reveal": {},
        "show_review": False,
        "mode": "Practice",
        "start_time": None
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_session()

# ----------------------------------------------------
# HEADER
# ----------------------------------------------------
st.title("📘 MCQ Practice & Exam Mode")


if not SUBJECTS:
    st.error("❌ No question files found in /questions folder")
    st.stop()

if st.session_state.subject is None:
    subject = st.selectbox(
        "📚 Select Subject",
        ["-- Select Subject --"] + list(SUBJECTS.keys())
    )

    if subject == "-- Select Subject --":
        st.info("Please select a subject to continue")
        st.stop()

    file_path = SUBJECTS[subject]
    questions = extract_questions(file_path)

    if not questions:
        st.error("❌ No valid MCQs found in this file")
        st.stop()

    st.session_state.subject = subject
    st.session_state.questions = questions
    st.session_state.start_time = time.time()
    st.rerun()


# ====================================================
# HEADER + MODE
# ====================================================
st.success(f"📘 Subject: **{st.session_state.subject}**")

st.session_state.mode = st.radio(
    "Mode",
    ["Practice", "Exam"],
    horizontal=True
)

if st.button("🔄 Change Subject"):
    st.session_state.clear()
    st.rerun()

questions = st.session_state.questions
TOTAL = len(questions)
# ====================================================
# TIMER (EXAM MODE)
# ====================================================
if st.session_state.mode == "Exam":
    elapsed = int(time.time() - st.session_state.start_time)
    st.info(f"⏱ Time Elapsed: {elapsed//60}:{elapsed%60:02d}")

# ====================================================
# PERFORMANCE SUMMARY
# ====================================================
attempted = len(st.session_state.responses)
correct = sum(
    1 for i, ans in st.session_state.responses.items()
    if questions[i].get("correct_option") == ans
)
accuracy = (correct / attempted * 100) if attempted else 0

with st.expander("📊 Performance Summary"):
    st.write(f"**Attempted:** {attempted} / {TOTAL}")
    st.write(f"**Correct:** {correct}")
    st.write(f"**Accuracy:** {accuracy:.2f}%")

# ----------------------------------------------------
# QUESTION JUMP (NO DOUBLE CLICK ISSUE)
# ----------------------------------------------------
q_no = st.selectbox(
    "Jump to Question",
    range(1, TOTAL + 1),
    index=st.session_state.index,
    key="jump_select"
)

if q_no - 1 != st.session_state.index:
    st.session_state.index = q_no - 1

q = questions[st.session_state.index]

# ----------------------------------------------------
# QUESTION DISPLAY
# ----------------------------------------------------
st.markdown(f"### Question {st.session_state.index + 1}")
st.markdown(f"**{q.get('question','')}**")

options = q.get("options", [])

selected = st.radio(
    "Select your answer:",
    range(1, len(options) + 1),
    index=(
        st.session_state.responses.get(st.session_state.index) - 1
        if st.session_state.index in st.session_state.responses
        else None
    ),
    format_func=lambda x: options[x - 1],
    key=f"answer_radio_{st.session_state.index}"
)

if selected is not None:
    st.session_state.responses[st.session_state.index] = selected

# ----------------------------------------------------
# REVEAL ANSWER (PER QUESTION)
# ----------------------------------------------------
if st.button("👁️ Reveal Answer", key="reveal_btn"):
    st.session_state.reveal[st.session_state.index] = True

if st.session_state.reveal.get(st.session_state.index):
    st.success(f"✅ Correct Option: {q.get('correct_option')}")
    st.markdown(f"**Explanation:** {q.get('explanation','')}")

# ----------------------------------------------------
# NAVIGATION BUTTONS
# ----------------------------------------------------
st.markdown("---")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("⬅ Previous", key="prev_btn"):
        if st.session_state.index > 0:
            st.session_state.index -= 1
            st.session_state.pop("answer_radio", None)

with col2:
    st.markdown(
        f"<p style='text-align:center;'>Question {st.session_state.index + 1} / {TOTAL}</p>",
        unsafe_allow_html=True
    )

with col3:
    if st.button("Next ➡", key="next_btn"):
        if st.session_state.index < TOTAL - 1:
            st.session_state.index += 1
            st.session_state.pop("answer_radio", None)

# ----------------------------------------------------
# REVIEW ANSWERS (HIDDEN BY DEFAULT)
# ----------------------------------------------------
st.markdown("---")

if st.button(
    "📘 Reveal Review Answers" if not st.session_state.show_review else "❌ Hide Review Answers",
    key="toggle_review"
):
    st.session_state.show_review = not st.session_state.show_review

if st.session_state.show_review:
    st.subheader("📘 Review Answers")

    for i, q in enumerate(questions):
        st.markdown(f"**Q{i+1}. {q.get('question','')}**")

        for idx, opt in enumerate(q.get("options", []), start=1):
            label = ""
            if st.session_state.responses.get(i) == idx:
                label += " 🟦 Your Answer"
            if q.get("correct_option") == idx:
                label += " ✅ Correct"

            st.markdown(f"- {idx}. {opt}{label}")

        if i in st.session_state.responses:
            if st.session_state.responses[i] == q.get("correct_option"):
                st.success("✔ Correct")
            else:
                st.error("✘ Incorrect")
        else:
            st.warning("Not Attempted")

        st.markdown(f"**Explanation:** {q.get('explanation','')}")
        st.markdown("---")