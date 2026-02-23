import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

def test_models():
    api_key = os.getenv("GEMINI_API_KEY")
    genai.configure(api_key=api_key)
    
    print("Listing models...")
    available_models = []
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                available_models.append(m.name)
    except Exception as e:
        print(f"Error listing models: {e}")
        return

    print(f"Found {len(available_models)} models supporting generateContent.")
    
    # Try gemini-1.5-flash variants first
    priority_models = ['models/gemini-1.5-flash', 'models/gemini-1.5-flash-latest', 'models/gemini-pro']
    models_to_try = [m for m in priority_models if m in available_models]
    # Add everything else
    models_to_try.extend([m for m in available_models if m not in priority_models])

    for model_name in models_to_try:
        print(f"Testing model: {model_name}...")
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content("hi")
            print(f"SUCCESS with {model_name}: {response.text}")
            break
        except Exception as e:
            print(f"FAILED with {model_name}: {e}")

if __name__ == "__main__":
    test_models()
