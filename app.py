import os
import json
import traceback
import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai.types import Part
from pydantic import BaseModel, Field

load_dotenv()

st.set_page_config(
    page_title="AI Flashcard Generator",
    page_icon="⚡",
    layout="centered"
)

try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
except Exception:
    API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    st.error("❌ Gemini API key not found. Add GEMINI_API_KEY to Streamlit Secrets or your .env file.")
    st.stop()

client = genai.Client(api_key=API_KEY)

class Flashcard(BaseModel):
    question: str = Field(description="A clear question.")
    answer: str = Field(description="A concise answer.")

class StudyGuide(BaseModel):
    topic: str
    flashcards: list[Flashcard]

if "flashcards_data" not in st.session_state:
    st.session_state.flashcards_data = None
if "download_text" not in st.session_state:
    st.session_state.download_text = ""

st.title("⚡ AI Flashcard Generator")
st.write("Upload notes, PDFs or images and generate AI flashcards.")
st.divider()

uploaded_file = st.file_uploader(
    "Upload PDF / Image / TXT",
    type=["pdf","png","jpg","jpeg","txt"]
)

user_notes = st.text_area(
    "Or paste your notes",
    height=180
)

num_cards = st.slider(
    "Number of Flashcards",
    3,
    10,
    5
)

if st.button("Generate Flashcards", type="primary"):

    if uploaded_file is None and not user_notes.strip():
        st.warning("Please upload a file or paste notes.")
        st.stop()

    with st.spinner("Generating Flashcards..."):

        try:

            contents = [
                f"Generate exactly {num_cards} flashcards from the following material."
            ]

            if uploaded_file is not None:
                contents.append(
                    Part.from_bytes(
                        data=uploaded_file.read(),
                        mime_type=uploaded_file.type
                    )
                )

            if user_notes.strip():
                contents.append(user_notes)

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=contents,
                config=types.GenerateContentConfig(
                    temperature=0.2,
                    response_mime_type="application/json",
                    response_schema=StudyGuide
                )
            )

            data = json.loads(response.text)

            st.session_state.flashcards_data = data

            txt = f"Topic: {data['topic']}\n\n"

            for i, card in enumerate(data["flashcards"],1):
                txt += f"Card {i}\n"
                txt += f"Q: {card['question']}\n"
                txt += f"A: {card['answer']}\n\n"

            st.session_state.download_text = txt

        except Exception:
            st.error(traceback.format_exc())

if st.session_state.flashcards_data:

    data = st.session_state.flashcards_data

    st.success(f"### 📚 {data['topic']}")

    for i, card in enumerate(data["flashcards"],1):

        st.markdown(f"### 🗂️ Card {i}")
        st.info(card["question"])

        with st.expander("Show Answer"):
            st.success(card["answer"])

    st.download_button(
        "📥 Download Flashcards",
        st.session_state.download_text,
        file_name="flashcards.txt",
        mime="text/plain",
        use_container_width=True
    )
