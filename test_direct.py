import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

def test_direct():
    api_key = os.getenv("GEMINI_API_KEY")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    headers = {'Content-Type': 'application/json'}
    data = {
        "contents": [{
            "parts": [{"text": "Write a short poem about a scout."}]
        }]
    }
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_direct()
