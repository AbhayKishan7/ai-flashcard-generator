import os
from google import genai
from dotenv import load_dotenv

# Load the .env file
load_dotenv()

# Initialize the Gemini client (it automatically looks for GEMINI_API_KEY)
client = genai.Client()

# Change 'gemini-2.5-flash' to 'gemini-3.5-flash'
response = client.models.generate_content(
    model='gemini-3.5-flash',
    contents='Explain the word "Token" in AI in one sentence.',
)
print("\n--- API Test Success! ---")
print(response.text)