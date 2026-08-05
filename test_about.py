import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('GEMINI_API_KEY')

# Test resume text
test_resume = """
Shreya Gupta is a BBA student at University of Lucknow. 
Skills: Communication, MS Excel, MS PowerPoint.
Languages: English, Hindi.
Currently pursuing business administration.
"""

prompt = f"""
Parse this resume and return ONLY valid JSON.
The 'about' field must contain a professional summary.

Return JSON:
{{
    "about": "professional summary here",
    "skills": [],
    "languages": [],
    "education": ""
}}

Resume: {test_resume}
"""

url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key={API_KEY}"
payload = {"contents": [{"parts": [{"text": prompt}]}]}

response = requests.post(url, json=payload)
result = response.json()
response_text = result['candidates'][0]['content']['parts'][0]['text']

print("Raw response:")
print(response_text)
print("\n" + "="*50)

# Clean and parse
clean = response_text.strip()
if clean.startswith('```json'):
    clean = clean[7:]
if clean.startswith('```'):
    clean = clean[3:]
if clean.endswith('```'):
    clean = clean[:-3]

data = json.loads(clean)
print("\nParsed data:")
print(json.dumps(data, indent=2))