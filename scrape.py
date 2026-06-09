"""
scrape.py — Fetch raw review data from RateMyProfessors and Reddit.

Saves:
  documents/rmp_reviews.json   — structured professor reviews from RMP
  documents/reddit_posts.json  — posts + comments from Reddit threads
"""

import argparse
import json
import os
import time
import requests

# ── RateMyProfessors config ──────────────────────────────────────────

RMP_GRAPHQL_URL = "https://www.ratemyprofessors.com/graphql"
RMP_AUTH_HEADER = "Basic dGVzdDp0ZXN0"

# Professor IDs from planning.md
PROFESSOR_IDS = {
    "1810660": "Neal Terrel",
    "464926": "Frank Murgolo",
    "115586": "Susan Nachawati",
    "2639859": "Hailu Xu",
    "307547": "Steve Gold",
    "52818": "Darin Goldstein",
    "1287692": "Shannon Cleary",
}

# GraphQL query to fetch professor info + all ratings
RMP_QUERY = """
query TeacherRatingsPageQuery($id: ID!, $cursor: String) {
  node(id: $id) {
    ... on Teacher {
      id
      firstName
      lastName
      department
      school {
        name
      }
      ratings(first: 100, after: $cursor) {
        edges {
          node {
            comment
            class
            date
            qualityRating
            difficultyRating
            helpfulRating
            clarityRating
            wouldTakeAgain
            isForOnlineClass
            thumbsUpTotal
            thumbsDownTotal
            grade
            attendanceMandatory
          }
        }
        pageInfo {
          hasNextPage
          endCursor
        }
      }
    }
  }
}
"""


def fetch_rmp_professor(professor_id: str) -> dict:
    """Fetch all ratings for a single RMP professor, paginating if needed."""
    # RMP uses base64-encoded IDs: "Teacher-<id>"
    import base64
    encoded_id = base64.b64encode(f"Teacher-{professor_id}".encode()).decode()

    all_edges = []
    cursor = None
    professor_info = None

    while True:
        variables = {"id": encoded_id}
        if cursor:
            variables["cursor"] = cursor

        resp = requests.post(
            RMP_GRAPHQL_URL,
            json={"query": RMP_QUERY, "variables": variables},
            headers={
                "Authorization": RMP_AUTH_HEADER,
                "Content-Type": "application/json",
                "Referer": "https://www.ratemyprofessors.com/",
                "Origin": "https://www.ratemyprofessors.com",
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/126.0.0.0 Safari/537.36"
                ),
            },
        )
        resp.raise_for_status()
        data = resp.json()

        node = data.get("data", {}).get("node")
        if not node:
            print(f"  ⚠ No data returned for professor ID {professor_id}")
            break

        if professor_info is None:
            professor_info = {
                "firstName": node.get("firstName", ""),
                "lastName": node.get("lastName", ""),
                "department": node.get("department", ""),
                "school": (node.get("school") or {}).get("name", ""),
            }

        ratings = node.get("ratings", {})
        edges = ratings.get("edges", [])
        all_edges.extend(edges)

        page_info = ratings.get("pageInfo", {})
        if page_info.get("hasNextPage"):
            cursor = page_info["endCursor"]
            time.sleep(0.5)  # be polite
        else:
            break

    return {
        "professor_id": professor_id,
        "name": PROFESSOR_IDS.get(professor_id, "Unknown"),
        "info": professor_info or {},
        "ratings": [edge["node"] for edge in all_edges],
        "source_url": f"https://www.ratemyprofessors.com/professor/{professor_id}",
    }


def scrape_rmp() -> list[dict]:
    """Scrape all RMP professors and return list of professor dicts."""
    results = []
    for pid, name in PROFESSOR_IDS.items():
        print(f"Fetching RMP: {name} (ID {pid})...")
        prof_data = fetch_rmp_professor(pid)
        print(f"  Got {len(prof_data['ratings'])} ratings")
        results.append(prof_data)
        time.sleep(1)  # rate-limit courtesy
    return results


# ── Reddit config ────────────────────────────────────────────────────

REDDIT_THREADS = [
    "https://www.reddit.com/r/CSULB/comments/1o7k69s/csulb_students_which_computer_science_professors/",
    "https://www.reddit.com/r/CSULB/comments/1ejytkq/why_is_the_cs_program_bad/",
    "https://www.reddit.com/r/CSULB/comments/14kuu85/quality_of_computer_science_education_in_csulb/",
]

REDDIT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0.0.0 Safari/537.36"
)


def flatten_comments(comment_data: list, depth: int = 0) -> list[dict]:
    """Recursively flatten Reddit's nested comment tree."""
    comments = []
    for item in comment_data:
        kind = item.get("kind")
        data = item.get("data", {})

        if kind == "t1":  # comment
            comments.append({
                "author": data.get("author", "[unknown]"),
                "body": data.get("body", ""),
                "score": data.get("score", 0),
                "created_utc": data.get("created_utc", 0),
                "depth": depth,
            })
            # Recurse into replies
            replies = data.get("replies")
            if isinstance(replies, dict):
                children = replies.get("data", {}).get("children", [])
                comments.extend(flatten_comments(children, depth + 1))

        elif kind == "more":
            pass  # skip "load more" stubs

    return comments


def _create_reddit_session() -> requests.Session:
    """Create a session that first visits old.reddit.com to pick up cookies."""
    session = requests.Session()
    session.headers.update({
        "User-Agent": REDDIT_USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    })
    # Visit old.reddit.com to get session cookies
    try:
        session.get("https://old.reddit.com/", timeout=10)
        time.sleep(1)
    except Exception:
        pass  # continue anyway
    return session


def fetch_reddit_thread(url: str, session: requests.Session) -> dict:
    """Fetch a Reddit thread as JSON and extract post + comments."""
    json_url = url.rstrip("/") + ".json"
    json_url = json_url.replace("www.reddit.com", "old.reddit.com")

    retry_delays = [2, 5, 10]
    last_error = None

    for attempt in range(1 + len(retry_delays)):
        session.headers.update({
            "Accept": "application/json",
            "Referer": url.replace("www.reddit.com", "old.reddit.com"),
        })
        resp = session.get(json_url, timeout=30)

        if resp.status_code in (403, 429):
            if attempt < len(retry_delays):
                delay = retry_delays[attempt]
                print(f"  Got {resp.status_code}, retrying in {delay}s (attempt {attempt + 2}/{1 + len(retry_delays)})...")
                time.sleep(delay)
                last_error = resp
                continue
            else:
                resp.raise_for_status()
        else:
            resp.raise_for_status()
            break

    data = resp.json()

    # data[0] = post listing, data[1] = comments listing
    post_data = data[0]["data"]["children"][0]["data"]
    post = {
        "title": post_data.get("title", ""),
        "author": post_data.get("author", "[unknown]"),
        "selftext": post_data.get("selftext", ""),
        "score": post_data.get("score", 0),
        "created_utc": post_data.get("created_utc", 0),
    }

    comment_children = data[1]["data"]["children"]
    comments = flatten_comments(comment_children)

    return {
        "source_url": url,
        "post": post,
        "comments": comments,
    }


def scrape_reddit() -> list[dict]:
    """Scrape all Reddit threads and return list of thread dicts."""
    session = _create_reddit_session()
    results = []
    for url in REDDIT_THREADS:
        print(f"Fetching Reddit: {url}")
        thread = fetch_reddit_thread(url, session)
        print(f"  Got {len(thread['comments'])} comments")
        results.append(thread)
        time.sleep(3)  # Reddit rate-limit courtesy
    return results


# ── Main ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Scrape RMP and Reddit data")
    parser.add_argument("--reddit-only", action="store_true", help="Only scrape Reddit threads")
    parser.add_argument("--rmp-only", action="store_true", help="Only scrape RateMyProfessors")
    args = parser.parse_args()

    os.makedirs("documents", exist_ok=True)

    run_rmp = not args.reddit_only
    run_reddit = not args.rmp_only

    if run_rmp:
        # Scrape RMP
        print("=== Scraping RateMyProfessors ===")
        rmp_data = scrape_rmp()
        rmp_path = os.path.join("documents", "rmp_reviews.json")
        with open(rmp_path, "w", encoding="utf-8") as f:
            json.dump(rmp_data, f, indent=2, ensure_ascii=False)
        total_reviews = sum(len(p["ratings"]) for p in rmp_data)
        print(f"Saved {len(rmp_data)} professors, {total_reviews} total reviews → {rmp_path}\n")

    if run_reddit:
        # Scrape Reddit
        print("=== Scraping Reddit ===")
        reddit_data = scrape_reddit()
        reddit_path = os.path.join("documents", "reddit_posts.json")
        with open(reddit_path, "w", encoding="utf-8") as f:
            json.dump(reddit_data, f, indent=2, ensure_ascii=False)
        total_comments = sum(len(t["comments"]) for t in reddit_data)
        print(f"Saved {len(reddit_data)} threads, {total_comments} total comments → {reddit_path}\n")

    print("Done!")


if __name__ == "__main__":
    main()
