import os
import requests
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("TELEGRAM_BOT_TOKEN")
chat_id = os.getenv("TELEGRAM_CHAT_ID")

print(f"Bot Token: {token}")
print(f"Chat ID: {chat_id}")

# Step 1: Check bot identity
print("\n--- Testing Bot Identity ---")
try:
    r = requests.get(f"https://api.telegram.org/bot{token}/getMe", timeout=10)
    print(f"Status: {r.status_code}")
    print(f"Response: {r.json()}")
except Exception as e:
    print(f"Error: {e}")

# Step 2: Send test message
print("\n--- Sending Test Message ---")
try:
    r = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={"chat_id": chat_id, "text": "🚀 Issue Scout is LIVE! This is a test notification."},
        timeout=10
    )
    print(f"Status: {r.status_code}")
    print(f"Response: {r.json()}")
except Exception as e:
    print(f"Error: {e}")
