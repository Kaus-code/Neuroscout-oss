import os
import time
from github import Github
from dotenv import load_dotenv

load_dotenv()

def benchmark():
    token = os.getenv("GITHUB_TOKEN")
    print(f"[{time.ctime()}] Initializing GitHub client...")
    gh = Github(token)
    
    repo_name = "langchain-ai/langchain"
    print(f"[{time.ctime()}] Fetching repo {repo_name}...")
    try:
        repo = gh.get_repo(repo_name)
        print(f"[{time.ctime()}] Repo found. Fetching issues...")
        
        # Accessing the iterator
        issues = repo.get_issues(state='open', sort='created', direction='desc')
        
        print(f"[{time.ctime()}] Iterator created. Fetching first 5 non-PR issues...")
        count = 0
        for issue in issues:
            print(f"[{time.ctime()}] Checking issue #{issue.number}")
            if issue.pull_request:
                print(f"[{time.ctime()}] Skipping PR #{issue.number}")
                continue
            print(f"[{time.ctime()}] Match: {issue.title}")
            count += 1
            if count >= 5:
                break
        print(f"[{time.ctime()}] Done.")
    except Exception as e:
        print(f"[{time.ctime()}] Error: {e}")

if __name__ == "__main__":
    benchmark()
