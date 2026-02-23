import os
import sys
import time
import warnings
from dotenv import load_dotenv

# Suppress warnings for cleaner output
warnings.filterwarnings("ignore")

from github_client import GitHubClient
from ai_engine import AIEngine
from storage import Storage
from notifier import TelegramNotifier

load_dotenv()

REPOS = [
    "langchain-ai/langgraph",
    "crewAIInc/crewAI",
    "pytorch/pytorch",
    "google-gemini/cookbook",
    "n8n-io/n8n",
    "aden-hive/hive",
    "calcom/cal.com"
]

def run_scout(test_repo=None):
    print("Initializing Issue Scout...")
    try:
        gh_client = GitHubClient()
        ai_engine = AIEngine()
        storage = Storage()
        notifier = TelegramNotifier()
    except Exception as init_err:
        print(f"Initialization Error: {init_err}")
        return

    repos_to_check = [test_repo] if test_repo else REPOS
    
    for repo_name in repos_to_check:
        print(f"\nChecking repo: {repo_name}...")
        try:
            issues = gh_client.fetch_recent_issues(repo_name, limit=20)
            found_something = False
            for issue in issues:
                try:
                    if storage.is_processed(issue.id):
                        continue
                    
                    print(f"Analyzing: {issue.title}")
                    analysis = ai_engine.analyze_issue(issue)
                    
                    # FLAW FIX: Only mark as processed if we actually got a valid analysis
                    # If it's an AI Error, we want to try again next time (or at least not hide it)
                    if "AI Error" not in analysis.reasoning:
                        if analysis.is_expert_level:
                            print(f"-> Found expert-level issue! Score: {analysis.fit_score}")
                            notifier.notify(issue, analysis)
                            found_something = True
                        else:
                            print(f"-> Discarded: {analysis.reasoning[:50]}...")
                        
                        storage.mark_processed(issue.id)
                    else:
                        print(f"-> Skipped due to analysis failure: {analysis.reasoning}")
                    
                    time.sleep(1) # Delay between Gemini calls
                except Exception as issue_err:
                    print(f"Error processing issue {issue.id}: {issue_err}")
            
            if not found_something:
                print("No new expert-level issues found in this batch.")

        except Exception as e:
            print(f"Error checking {repo_name}: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        run_scout("langchain-ai/langchain")
    else:
        while True:
            run_scout()
            print("\nCycle complete. Sleeping for 1 hour...")
            time.sleep(3600)
