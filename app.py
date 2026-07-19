import streamlit as st
import json
from google import genai
from google.genai import types
from google.genai.types import Part
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# 1. Load API Key environment variables
load_dotenv()

# 2. Page Configuration
st.set_page_config(
    page_title="AI Flashcard Generator",
    page_icon="⚡",
    layout="centered"
)

# 3. Define the structural "contract" for the AI's output
class Flashcard(BaseModel):
    question: str = Field(description="A clear question targeting a core concept.")
    answer: str = Field(description="A concise answer explaining the concept simply.")

class StudyGuide(BaseModel):
    topic: str = Field(description="The overarching theme of the text or document.")
    flashcards: list[Flashcard] = Field(description="A list of generated flashcards.")

# --- SESSION STATE INITIALIZATION ---
if "flashcards_data" not in st.session_state:
    st.session_state.flashcards_data = None
if "download_text" not in st.session_state:
    st.session_state.download_text = ""

# 4. Main Visual Header
st.title("⚡ AI Flashcard Generator")
st.write("Upload a file or paste your raw study notes below, select your deck size, and turn chaos into study cards.")
st.markdown("---")

# 5. User Inputs Section
st.subheader("📝 Step 1: Provide Your Study Material")

# File uploader for PDFs, Images, and Text files
uploaded_file = st.file_uploader(
    label="Upload study files (PDF, PNG, JPG, TXT):",
    type=["pdf", "png", "jpg", "jpeg", "txt"]
)

# Text area fallback
user_notes = st.text_area(
    label="Or paste text notes directly:",
    height=150,
    placeholder="Example: The water cycle involves evaporation, condensation, and precipitation..."
)

st.subheader("⚙️ Step 2: Customize Settings")
num_cards = st.slider(
    label="How many flashcards would you like?",
    min_value=3,
    max_value=10,
    value=5
)

st.markdown("###")

# 6. The Connected Trigger Button
if st.button("Generate Flashcards", type="primary"):
    # Ensure the user provided either an uploaded file OR text notes
    if not uploaded_file and not user_notes.strip():
        st.warning("⚠️ Please provide some study material (paste notes or upload a file) first before generating!")
    else:
        with st.spinner("🧠 Gemini is analyzing your material and structuring flashcards..."):
            try:
                # Initialize Gemini client
                client = genai.Client()
                
                # Build the base request prompt content list
                contents_payload = [f"Generate exactly {num_cards} study flashcards from this study material."]

                # Case A: User uploaded a file
                if uploaded_file is not None:
                    file_bytes = uploaded_file.read()
                    file_mime = uploaded_file.type
                    
                    # Convert raw bytes into a format Gemini natively understands
                    file_part = Part.from_bytes(
                        data=file_bytes,
                        mime_type=file_mime
                    )
                    contents_payload.append(file_part)
                
                # Case B: User also added/appended text notes
                if user_notes.strip():
                    contents_payload.append(f"\nAdditional Context / Notes:\n{user_notes}")

                # Make the live multimodal API call
                response = client.models.generate_content(
                    model="gemini-3.5-flash",
                    contents=contents_payload,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=StudyGuide,
                        temperature=0.2
                    )
                )

                # Convert JSON response and commit to persistent state memory
                data = json.loads(response.text)
                st.session_state.flashcards_data = data

                # Prepare and save download text string to memory
                download_text = f"STUDY GUIDE: {data['topic']}\n"
                download_text += "=" * 30 + "\n\n"
                for i, card in enumerate(data["flashcards"], 1):
                    download_text += f"Card {i}\nQ: {card['question']}\nA: {card['answer']}\n"
                    download_text += "-" * 20 + "\n"
                
                st.session_state.download_text = download_text

            except Exception as e:
                st.error(f"Something went wrong: {e}")

# --- 7. RENDERING SECTION ---
if st.session_state.flashcards_data is not None:
    data = st.session_state.flashcards_data
    
    st.markdown("---")
    st.success(f"✨ Topic: **{data['topic']}**")

    # Render out the flashcards
    for i, card in enumerate(data["flashcards"], 1):
        card_html = f'<div style="background-color: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 20px; margin-bottom: 15px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);"><span style="background-color: #ffe0b2; color: #e65100; font-weight: bold; padding: 4px 8px; border-radius: 6px; font-size: 0.85rem;">🗂️ CARD {i}</span><p style="font-size: 1.1rem; font-weight: 600; color: #ffffff; margin-top: 12px; margin-bottom: 8px;"><strong>Question:</strong> {card["question"]}</p></div>'
        st.markdown(card_html, unsafe_allow_html=True)

        with st.expander("👁️ Reveal Answer"):
            st.success(card["answer"])

    st.markdown("###")

    # Download Button
    st.download_button(
        label="📥 Download Flashcards as Text File",
        data=st.session_state.download_text,
        file_name=f"{data['topic'].lower().replace(' ', '_')}_flashcards.txt",
        mime="text/plain",
        use_container_width=True
    )