import os
from github import Github
from dotenv import load_dotenv
import traceback

load_dotenv()

def test_gh():
    token = os.getenv("GITHUB_TOKEN")
    gh = Github(token)
    try:
        repo = gh.get_repo("langchain-ai/langchain")
        print(f"Repo found: {repo.full_name}")
        issues = repo.get_issues(state='open')
        for i in issues[:2]:
            print(f"Issue: {i.title}")
    except Exception as e:
        traceback.print_exc()

if __name__ == "__main__":
    test_gh()
