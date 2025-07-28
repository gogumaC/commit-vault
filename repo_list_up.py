import datetime
import json
import os
import re
import shutil
import subprocess

import requests


def run(cmd, cwd=None):
    print(f"> {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print("ERROR:", result.stderr)
        raise RuntimeError(f"Command failed: {cmd}")
    return result.stdout.strip()


def consume_commit(url):

    repo_name = url.split("/")[-1].replace(".git", "")
    repo_dir = os.path.join(BASE_DIR, repo_name)

    os.makedirs(repo_dir, exist_ok=True)
    if not os.path.exists(repo_dir):
        run(f"git clone {url}", cwd=BASE_DIR)

    run(f"git fetch origin", cwd=BASE_DIR)

    run("git checkout main", cwd=repo_dir)
    run("git pull origin main", cwd=repo_dir)

    run("git checkout draft", cwd=repo_dir)
    run("git pull origin draft", cwd=repo_dir)

    log = run("git log main..draft --oneline", cwd=repo_dir)

    commits = log.splitlines()

    if not commits:
        print("✅ No new commits to process.")
        return False

    first_commit = commits[-1].split()[0]
    print("🔍 First draft commit after main:", first_commit)

    # 3. cherry-pick to main
    run("git checkout main", cwd=repo_dir)
    run(f"git cherry-pick {first_commit}", cwd=repo_dir)

    # 4. amend로 시간 갱신
    now = datetime.datetime.now().isoformat()
    run(f'git commit --amend --no-edit --date="{now}"', cwd=repo_dir)

    # 5. draft 브랜치 main 기준으로 리베이스
    run("git checkout draft", cwd=repo_dir)
    run("git rebase main", cwd=repo_dir)

    # 6. push main, draft
    run("git checkout main", cwd=repo_dir)
    run("git push origin main", cwd=repo_dir)

    run("git checkout draft", cwd=repo_dir)
    run("git push origin draft", cwd=repo_dir)

    print("✅ 자동 커밋 및 rebase 완료.")
    last_commit_hash = run("git rev-parse HEAD", cwd=repo_dir)
    commit_msg = run("git log -1 --pretty=%B", cwd=repo_dir)
    commit_date = run("git log -1 --format=%cd", cwd=repo_dir)

    print("🚀 새 커밋 정보:")
    print(f"🔑 Commit: {last_commit_hash}")
    print(f"📝 Message: {commit_msg}")
    print(f"🕒 Date: {commit_date}")
    return True


GITHUB_TOKEN = os.getenv("GH_TOKEN")  # GitHub Personal Access Token
# GITHUB_USERNAME = "yubin"
BASE_DIR = "./repos"

headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}

query = """
{
  viewer {
    repositories(first: 100, affiliations: OWNER, isFork: false) {
      nodes {
        nameWithOwner
        sshUrl
      }
    }
  }
}
"""

response = requests.post(
    "https://api.github.com/graphql", json={"query": query}, headers=headers
)
data = response.json()

if response.status_code != 200:
    print("Error:", data.get("message", "Unknown error"))
    print(json.dumps(data, indent=2))
    exit(1)


repo_urls = [node["sshUrl"] for node in data["data"]["viewer"]["repositories"]["nodes"]]

for url in repo_urls:
    print(f"Processing repository: {url}")
    try:
        if consume_commit(url):
            # main 브랜치에 푸시한 후, 마지막 커밋 정보 출력
            print(f"✅ Successfully processed {url}")
        else:
            print(f"❌ No new commits to process for {url}")
    except Exception as e:
        print(f"❗ Error processing {url}: {e}")
