import os
import requests
from models import GitHubIssue, IssueAnalysis
from dotenv import load_dotenv

load_dotenv()

class TelegramNotifier:
    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")

    def notify(self, issue: GitHubIssue, analysis: IssueAnalysis):
        # Using HTML parse mode to avoid Markdown character escaping issues
        message = (
            f"🚀 <b>New Expert Issue Found!</b>\n\n"
            f"📍 <b>Repo:</b> {issue.repo_name}\n"
            f"🔗 <b>Issue:</b> <a href='{issue.html_url}'>{issue.title}</a>\n\n"
            f"📊 <b>Fit Score:</b> {analysis.fit_score}/10\n"
            f"💡 <b>Strategy:</b> {analysis.implementation_strategy}\n\n"
            f"🧐 <b>Reasoning:</b> {analysis.reasoning}"
        )
        
        if not self.bot_token or not self.chat_id:
            print("-" * 20)
            print(message.replace("<b>", "").replace("</b>", "").replace("<a href='", "").replace("'>", " - ").replace("</a>", ""))
            print("-" * 20)
            return

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "HTML"
        }
        
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            print(f"Successfully sent notification for issue {issue.number}")
        except Exception as e:
            print(f"Failed to send Telegram notification: {e}")
