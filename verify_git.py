import os
import requests
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("GITHUB_TOKEN")
repo = "Kaus-code/AutoIssueScrapper"

headers = {
    "Authorization": f"token {token}",
    "Accept": "application/vnd.github.v3+json"
}

print(f"Verifying token for repo: {repo}")

# Check user info
r_user = requests.get("https://api.github.com/user", headers=headers)
if r_user.status_code == 200:
    user_data = r_user.json()
    print(f"Authenticated as: {user_data.get('login')}")
else:
    print(f"Failed to authenticate: {r_user.status_code} - {r_user.text}")

# Check repo access
r_repo = requests.get(f"https://api.github.com/repos/{repo}", headers=headers)
if r_repo.status_code == 200:
    repo_data = r_repo.json()
    permissions = repo_data.get("permissions", {})
    print(f"Repo Permissions: {permissions}")
    if permissions.get("push"):
        print("✅ Token has PUSH access.")
    else:
        print("❌ Token does NOT have push access.")
else:
    print(f"Failed to access repo: {r_repo.status_code} - {r_repo.text}")
