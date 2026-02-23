import os
import google.generativeai as genai
from dotenv import load_dotenv
import traceback

load_dotenv()

def test_ai():
    api_key = os.getenv("GEMINI_API_KEY")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    print(f"Using models: {[m.name for m in genai.list_models()]}")
    try:
        response = model.generate_content("Hello, are you working?")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error Type: {type(e)}")
        print(f"Error Message: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    test_ai()
