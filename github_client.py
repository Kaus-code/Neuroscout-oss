import os
from github import Github
from models import GitHubIssue
from typing import List
from dotenv import load_dotenv

load_dotenv()

class GitHubClient:
    def __init__(self):
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            raise ValueError("GITHUB_TOKEN not found in environment variables")
        self.gh = Github(token)

    def fetch_recent_issues(self, repo_full_name: str, limit: int = 10) -> List[GitHubIssue]:
        repo = self.gh.get_repo(repo_full_name)
        issues = repo.get_issues(state='open', sort='created', direction='desc')
        
        result = []
        count = 0
        for issue in issues:
            if issue.pull_request: # Skip PRs
                continue
            
            result.append(GitHubIssue(
                id=issue.id,
                number=issue.number,
                title=issue.title,
                body=issue.body if issue.body else "",
                html_url=issue.html_url,
                repo_name=repo_full_name
            ))
            count += 1
            if count >= limit:
                break
        
        return result
