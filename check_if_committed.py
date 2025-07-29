import os
from datetime import datetime, timezone

import requests

import os
from datetime import datetime, timezone
import requests

def is_contribution_event(event: dict) -> bool:
    """잔디에 반영되는 이벤트인지 확인"""
    allowed_event_types = {
        "PushEvent",         # 커밋
        "PullRequestEvent",  # PR 생성
        "IssuesEvent",       # 이슈 생성
        "PullRequestReviewEvent",  # PR 리뷰
        "DiscussionEvent"    # Discussions 참여 (optional)
    }

    if event["type"] not in allowed_event_types:
        return False

    # created_at이 오늘 날짜인지 확인
    created_at = event.get("created_at", "")
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return created_at.startswith(today_str)

def has_contribution_today(github_username: str, token: str) -> bool:
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }
    url = f"https://api.github.com/users/{github_username}/events/public"

    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        print(f"❌ GitHub API 호출 실패: {resp.status_code}")
        return False

    events = resp.json()
    for event in events:
        if is_contribution_event(event):
            print(f"✅ 잔디 반영 활동 발견: {event['type']} at {event['created_at']}")
            return True

    print("🚫 오늘 잔디에 반영될 활동 없음.")
    return False


if __name__ == "__main__":
    github_username = os.getenv("GITHUB_USER_NAME")  # 예: "gogumaC"
    github_token = os.getenv("GH_TOKEN")

    if not github_username or not github_token:
        print("❗ 환경 변수 GITHUB_USER_NAME 또는 GH_TOKEN이 설정되지 않았습니다.")
        exit(1)

    committed = has_contribution_today(github_username, github_token)
    if committed:
        exit(1)  # 종료. 이미 커밋했음
    else:
        exit(0)  # 커밋 안함. 계속 진행해도 됨
