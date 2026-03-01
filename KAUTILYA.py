
import streamlit as st
from openai import OpenAI
from pypdf import PdfReader
from streamlit_mic_recorder import mic_recorder

# ------------------ CONFIG ------------------

st.set_page_config(page_title="KAUTILYA", layout="wide")

# ------------------ API CLIENTS ------------------

# OpenRouter → Chat + Quiz
router_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="USE_YOUR_API_KEY"
)



# ------------------ SESSION STATE ------------------

def init_state():

    defaults = {

        "messages": [],
        "quiz_question": None,
        "quiz_options": [],
        "quiz_answer": None,
        "quiz_explanation": None,
        "quiz_score": 0,
        "pdf_text": "",
        "pdf_uploaded": False,
        "voice_text": None

    }

    for key, value in defaults.items():

        if key not in st.session_state:
            st.session_state[key] = value


init_state()

# ------------------ PDF TEXT EXTRACTION ------------------

def extract_pdf_text(files):

    text = ""

    for file in files:

        pdf = PdfReader(file)

        for page in pdf.pages:

            content = page.extract_text()

            if content:
                text += content + "\n"

    return text


# ------------------ QUIZ RESET ------------------

def reset_quiz():

    st.session_state.quiz_question = None
    st.session_state.quiz_options = []
    st.session_state.quiz_answer = None
    st.session_state.quiz_explanation = None


# ------------------ SIDEBAR ------------------

st.sidebar.title(" Student Profile")

student_name = st.sidebar.text_input("Student Name")

topic = st.sidebar.selectbox(

    "Select Topic",

    [
        "Mathematics",
        "Physics",
        "Chemistry",
        "Biology",
        "Computer Science",
        "General Studies",
    ],
)
class_level = st.sidebar.selectbox(
    "Class Level",
    ["6", "7", "8", "9", "10", "11", "12"]
)

difficulty = st.sidebar.selectbox(
    "Difficulty",
    ["Easy", "Medium", "Hard"]
)
# ------------------ PDF UPLOAD ------------------

st.sidebar.subheader(" Upload Study Material")

uploaded_files = st.sidebar.file_uploader(

    "Upload PDF(s)",

    type="pdf",

    accept_multiple_files=True

)

if uploaded_files:

    st.session_state.pdf_text = extract_pdf_text(uploaded_files)

    st.session_state.pdf_uploaded = True

    st.sidebar.success("PDF uploaded successfully!")

# ------------------ QUIZ GENERATION ------------------

if st.sidebar.button("Generate Quiz Question"):
    prompt = f"""
You are an expert academic question paper setter.

Generate ONE MCQ question.

Topic: {topic}
Class Level: {class_level}
Difficulty: {difficulty}

Rules:
- Match the intellectual level of Class {class_level}
- If Easy → basic definitions
- If Medium → conceptual application
- If Hard → analytical, tricky, or calculation-based
- Options must be realistic and confusing
- Only ONE correct answer

STRICT FORMAT (no extra text):

Question: ...
A) ...
B) ...
C) ...
D) ...
Correct Answer: A/B/C/D
Explanation: ...
"""
      


    response = router_client.chat.completions.create(

        model="openai/gpt-3.5-turbo",

        messages=[{"role": "user", "content": prompt}]

    )

    data = response.choices[0].message.content

    lines = data.split("\n")

    question = ""
    options = []
    answer = ""
    explanation = ""

    for line in lines:

        line = line.strip()

        if line.lower().startswith("question"):
            question = line

        elif line.startswith(("A)", "B)", "C)", "D)")):
            options.append(line)

        elif "correct answer" in line.lower():
            answer = line.split(":")[-1].strip()

        elif "explanation" in line.lower():
            explanation = line.split(":",1)[-1].strip()

    st.session_state.quiz_question = question
    st.session_state.quiz_options = options
    st.session_state.quiz_answer = answer
    st.session_state.quiz_explanation = explanation


# ------------------ CONTROL BUTTONS ------------------

if st.sidebar.button("Clear Chat"):

    st.session_state.messages = []
    st.rerun()

if st.sidebar.button("Start Over"):

    st.session_state.messages = []
    st.session_state.quiz_score = 0
    st.session_state.pdf_text = ""
    st.session_state.pdf_uploaded = False

    reset_quiz()

    st.rerun()
st.sidebar.subheader("Language")

language = st.sidebar.selectbox(
    "Response Language",
    ["Auto Detect", "English", "Hindi"]
)
# ------------------ SCORE DISPLAY ------------------

st.sidebar.metric("Score", st.session_state.quiz_score)

# ------------------ TITLE ------------------

st.title("KAUTILYA")
st.markdown("### Your Personal AI Tutor")

if student_name:

    st.success(f"Welcome {student_name}!")

else:

    st.info("Enter your name to begin.")

# ------------------ QUIZ DISPLAY ------------------

if st.session_state.quiz_question:

    st.subheader("Quiz Question")

    st.write(st.session_state.quiz_question)

    selected = st.radio(

        "Choose answer:",

        st.session_state.quiz_options

    )

    if st.button("Submit Answer"):

        if selected[0] == st.session_state.quiz_answer:

            st.success("Correct!")

            st.session_state.quiz_score += 1

        else:

            st.error(
                f"Wrong. Correct answer: {st.session_state.quiz_answer}"
            )

        st.info(st.session_state.quiz_explanation)




# ------------------ CHAT HISTORY ------------------

for msg in st.session_state.messages:

    with st.chat_message(msg["role"]):

        st.markdown(msg["content"])


# ------------------ CHAT INPUT ------------------

prompt = st.chat_input("Ask your question...")

if st.session_state.voice_text:

    prompt = st.session_state.voice_text
    st.session_state.voice_text = None


# ------------------ AI RESPONSE ------------------
# -------- LANGUAGE INSTRUCTION --------

# 
# Language instruction
if language == "Auto Detect":
    language_instruction = """
Detect the language of the student's question.
Reply in the SAME language.

IMPORTANT:
- If Hindi → reply in proper Devanagari script (हिंदी)
- If English → reply in English
- Do NOT translate unless asked
"""
else:
    if language == "Hindi":
        language_instruction = """
Reply strictly in Hindi using proper Devanagari script (हिंदी लिपि).
Do NOT use Roman Hindi.
"""
    else:
        language_instruction = f"""
Reply strictly in {language}.
"""

# Then include it in system prompt
system_prompt = f"""
You are KAUTILYA AI tutor.

{language_instruction}

Student: {student_name}
Topic: {topic}

Explain clearly step-by-step.
"""
if prompt:

    st.session_state.messages.append(

        {"role": "user", "content": prompt}

    )

    with st.chat_message("user"):

        st.markdown(prompt)

    # PDF MODE

    if st.session_state.pdf_uploaded:
        system_prompt = f"""
You are KAUTILYA AI tutor.

STRICT RULE:

Answer ONLY using uploaded material.

If answer not found, say:
"Answer not found in uploaded material."

{language_instruction}

Material:
{st.session_state.pdf_text[:12000]}
"""



    else:
        system_prompt = f"""
You are KAUTILYA AI tutor.

Student: {student_name}
Topic: {topic}

Explain clearly step-by-step.

{language_instruction}
"""



    response = router_client.chat.completions.create(

        model="openai/gpt-3.5-turbo",

        messages=[

            {"role": "system", "content": system_prompt},

            {"role": "user", "content": prompt}

        ]

    )

    reply = response.choices[0].message.content

    st.session_state.messages.append(

        {"role": "assistant", "content": reply}

    )

    with st.chat_message("assistant"):

        st.markdown(reply)
