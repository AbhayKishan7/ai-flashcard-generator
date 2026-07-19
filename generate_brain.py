import os
import json
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# 1. Load your secret API key
load_dotenv()

# 2. Define the exact 'shape' of a single Flashcard
class Flashcard(BaseModel):
    question: str = Field(description="A clear question testing a single concept.")
    answer: str = Field(description="A short, concise answer explaining the concept.")

# 3. Define the blueprint for the entire AI response
class StudyGuide(BaseModel):
    topic: str = Field(description="The general theme or subject of the notes provided.")
    flashcards: list[Flashcard] = Field(description="A list containing exactly the requested number of flashcards.")

# 4. Initialize the Gemini Client
client = genai.Client()

# Let's create some messy sample notes to test our brain on
sample_notes = """
Photosynthesis is the process used by plants to convert light energy into chemical energy. 
It takes place inside the chloroplasts, which contain chlorophyll. 
The raw ingredients needed are water, carbon dioxide, and sunlight. 
The plants produce glucose (sugar for energy) and release oxygen as a byproduct.
"""

print("🧠 Sending raw notes to Gemini 3.5...")

# 5. Tell the model to generate structure
response = client.models.generate_content(
    model='gemini-3.5-flash',
    contents=f"Generate exactly 3 study flashcards from these notes:\n\n{sample_notes}",
    config=types.GenerateContentConfig(
        response_mime_type="application/json", # Forces JSON delivery
        response_schema=StudyGuide,          # Enforces our strict blueprint structure
        temperature=0.1                      # Low temperature keeps it precise and non-random
    )
)

print("\n--- 🟢 RAW JSON RECEIVED FROM AI ---")
print(response.text)

# 6. Test parsing the data to make sure it's safely usable
try:
    data = json.loads(response.text)
    print("\n--- 🎉 PYTHON VALIDATION SUCCESSFUL ---")
    print(f"Extracted Topic: {data['topic']}")
    print(f"Successfully generated {len(data['flashcards'])} robust cards!")
except Exception as e:
    print(f"\n❌ JSON Parsing Failed: {e}")