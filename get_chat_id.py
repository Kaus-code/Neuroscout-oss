import requests, os
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("TELEGRAM_BOT_TOKEN")
print(f"Token: {token}")

r = requests.get(f"https://api.telegram.org/bot{token}/getUpdates", timeout=10)
data = r.json()

if data.get("ok") and data.get("result"):
    for update in data["result"]:
        if "message" in update:
            chat = update["message"]["chat"]
            print(f"Chat ID: {chat['id']}")
            print(f"From: {chat.get('first_name', 'N/A')}")
else:
    print(f"No updates found. Response: {data}")
