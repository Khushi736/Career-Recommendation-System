import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('GEMINI_API_KEY')
print(f"Testing API Key: {API_KEY[:15]}...")

# List all available models first
list_url = f"https://generativelanguage.googleapis.com/v1/models?key={API_KEY}"
print(f"\n📡 Getting available models...")
response = requests.get(list_url)

if response.status_code == 200:
    models = response.json().get('models', [])
    print(f"✅ Available models:")
    for model in models:
        if 'generateContent' in model.get('supportedGenerationMethods', []):
            print(f"  - {model['name']}")
    
    # Use the first available model
    if models:
        model_name = models[0]['name']
        print(f"\n📡 Testing with: {model_name}")
        
        url = f"https://generativelanguage.googleapis.com/v1/{model_name}:generateContent?key={API_KEY}"
        payload = {"contents": [{"parts": [{"text": "Say 'Hello' from CV parser"}]}]}
        
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ API is working!")
        else:
            print(f"❌ Failed: {response.text}")
else:
    print(f"❌ Cannot list models: {response.text}")