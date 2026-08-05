import os
import requests
import PyPDF2
import json
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('GEMINI_API_KEY')
print(f"✅ API Key loaded: {API_KEY[:15]}...")

# Test with your actual resume
resume_path = "uploads/Resume.pdf"  # Update path to your resume

if os.path.exists(resume_path):
    # Extract text
    text = ""
    with open(resume_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            text += page.extract_text() or ""
    
    print(f"📝 Extracted {len(text)} characters")
    
    # Call API
    prompt = f"""
    Parse this resume and return ONLY valid JSON:
    {{
        "about": "about yourself",
        "skills": ["skill1", "skill2"],
        "interests": ["interest1"],
        "languages": ["language1"],
        "work_experience": "work summary",
        "education": "degree",
        "certifications": "certs",
        "projects": "projects",
        "achievements": "achievements",
        "linkedin_url": "",
        "github_url": ""
    }}
    
    Resume: {text[:3000]}
    """
    
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key={API_KEY}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        result = response.json()
        response_text = result['candidates'][0]['content']['parts'][0]['text']
        print("✅ API Response received!")
        print(f"Response: {response_text[:500]}")
        
        # Try to parse JSON
        try:
            clean = response_text.strip()
            if clean.startswith('```json'):
                clean = clean[7:]
            if clean.startswith('```'):
                clean = clean[3:]
            if clean.endswith('```'):
                clean = clean[:-3]
            data = json.loads(clean)
            print("\n✅ Successfully parsed JSON!")
            print(json.dumps(data, indent=2))
        except:
            print("\n⚠️ Could not parse JSON")
    else:
        print(f"❌ Error: {response.text}")
else:
    print(f"Resume not found at {resume_path}")