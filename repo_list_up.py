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

    if not os.path.exists(repo_dir):
        run(f"git clone {url}", cwd=BASE_DIR)
    else:
        run("git fetch origin", cwd=repo_dir)

    run(f"git config user.name {USER_NAME}", cwd=repo_dir)
    run(f"git config user.email {USER_EMAIL}", cwd=repo_dir)

    print(run("git remote show origin", cwd=repo_dir))  ## 디버깅용

    # main 브랜치가 최신인지 확인
    run("git checkout main", cwd=repo_dir)
    run("git pull origin main", cwd=repo_dir)

    # draft 브랜치가 최신인지 확인
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
    try:
        run(f"git cherry-pick {first_commit}", cwd=repo_dir)
    except RuntimeError as e:
        if "cherry-pick is now empty" in str(e):
            print("⚠️  변경사항 없음 — cherry-pick 건너뜀")
            run("git cherry-pick --skip", cwd=repo_dir)
            return False
        else:
            raise

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
    run("git push origin draft --force", cwd=repo_dir)

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
USER_NAME = os.getenv("GITHUB_USER_NAME")
USER_EMAIL = os.getenv("GITHUB_USER_EMAIL")
# GITHUB_USERNAME = "yubin"
BASE_DIR = "./repos"
os.makedirs(BASE_DIR, exist_ok=True)

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

    refs = run(f"git ls-remote --heads {url} draft", cwd=BASE_DIR)

    if not refs.strip():
        print(f"❌ draft 브랜치 없음: {url}")
        continue

    print(f"Processing repository: {url}")
    try:
        if consume_commit(url):
            # main 브랜치에 푸시한 후, 마지막 커밋 정보 출력
            print(f"✅ Successfully processed {url}")
            break  # 성공적으로 처리된 경우 루프 종료
        else:
            print(f"❌ No new commits to process for {url}")
    except Exception as e:
        print(f"❗ Error processing {url}: {e}")
