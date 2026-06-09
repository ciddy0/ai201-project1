"""
pipeline.py — Load raw JSON from documents/, clean, chunk, and inspect.

Produces a list of chunks, each with:
  {text, professor, course, source_url, source_type}
"""

import json
import os
import re
import html


# ── Loading ──────────────────────────────────────────────────────────

def load_rmp_reviews(path: str = "documents/rmp_reviews.json") -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_reddit_posts(path: str = "documents/reddit_posts.json") -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ── Cleaning ─────────────────────────────────────────────────────────

def clean_rmp_text(text: str) -> str:
    """Strip HTML tags and entities from RMP review text."""
    text = html.unescape(text)
    text = re.sub(r"<[^>]+>", "", text)  # strip HTML tags
    text = re.sub(r"\s+", " ", text).strip()
    return text


def clean_reddit_text(text: str) -> str:
    """Strip markdown artifacts and clean Reddit text."""
    text = html.unescape(text)
    # Remove markdown links: [text](url) → text
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    # Remove bold/italic markers
    text = re.sub(r"\*{1,3}([^*]+)\*{1,3}", r"\1", text)
    # Remove heading markers
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    # Remove blockquote markers
    text = re.sub(r"^>\s?", "", text, flags=re.MULTILINE)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def is_deleted_or_bot(text: str, author: str) -> bool:
    """Check if a Reddit comment is deleted, removed, or from a bot."""
    if text.strip().lower() in ("[deleted]", "[removed]", ""):
        return True
    bot_indicators = ["i am a bot", "i'm a bot", "beep boop", "automod"]
    text_lower = text.lower()
    if any(indicator in text_lower for indicator in bot_indicators):
        return True
    bot_authors = ["AutoModerator", "[deleted]"]
    if author in bot_authors:
        return True
    return False


# ── Chunking ─────────────────────────────────────────────────────────

MAX_CHUNK_CHARS = 1200
OVERLAP_CHARS = 150  # ~30-50 tokens


def split_long_text(text: str, max_chars: int = MAX_CHUNK_CHARS,
                    overlap: int = OVERLAP_CHARS) -> list[str]:
    """Split text exceeding max_chars with overlap. Tries to break on sentences."""
    if len(text) <= max_chars:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = start + max_chars

        # Try to break at a sentence boundary
        if end < len(text):
            # Look for sentence-ending punctuation near the end
            for sep in [". ", "! ", "? ", "\n"]:
                last_sep = text.rfind(sep, start + max_chars // 2, end)
                if last_sep != -1:
                    end = last_sep + len(sep)
                    break

        chunks.append(text[start:end].strip())
        start = end - overlap

    return chunks


def chunk_rmp(professors: list[dict]) -> list[dict]:
    """One review = one chunk. Each chunk gets professor + course metadata."""
    chunks = []
    for prof in professors:
        name = prof["name"]
        source_url = prof["source_url"]

        for rating in prof["ratings"]:
            text = clean_rmp_text(rating.get("comment", ""))
            if not text:
                continue  # drop empty reviews

            course = rating.get("class", "Unknown")
            quality = rating.get("qualityRating", "N/A")
            difficulty = rating.get("difficultyRating", "N/A")

            # Prepend a short context line so the chunk stands alone
            chunk_text = (
                f"[RMP review for {name} — {course} | "
                f"Quality: {quality}/5, Difficulty: {difficulty}/5] "
                f"{text}"
            )

            chunks.append({
                "text": chunk_text,
                "professor": name,
                "course": course,
                "source_url": source_url,
                "source_type": "rmp",
            })

    return chunks


# Known CSULB CS professors for Reddit mention detection
KNOWN_PROFESSORS = [
    "terrel", "murgolo", "nachawati", "nachwati",
    "xu", "hailu", "gold", "goldstein", "cleary",
    "shah", "shatto", "monge", "todd",
]

PROFESSOR_FULL_NAMES = {
    "terrel": "Neal Terrel",
    "murgolo": "Frank Murgolo",
    "nachawati": "Susan Nachawati",
    "nachwati": "Susan Nachawati",
    "xu": "Hailu Xu",
    "hailu": "Hailu Xu",
    "gold": "Steve Gold",
    "goldstein": "Darin Goldstein",
    "cleary": "Shannon Cleary",
}


def extract_professor_from_text(text: str) -> str:
    """Try to identify which professor a Reddit comment is about."""
    text_lower = text.lower()
    mentioned = []
    for prof in KNOWN_PROFESSORS:
        if prof in text_lower:
            full = PROFESSOR_FULL_NAMES.get(prof)
            if full and full not in mentioned:
                mentioned.append(full)
    if len(mentioned) == 1:
        return mentioned[0]
    elif len(mentioned) > 1:
        return ", ".join(mentioned)
    return "various"


def chunk_reddit(threads: list[dict]) -> list[dict]:
    """One comment = one chunk, with long text splitting."""
    chunks = []

    for thread in threads:
        source_url = thread["source_url"]
        post = thread["post"]
        title = post.get("title", "")

        # Process the post body itself
        body = clean_reddit_text(post.get("selftext", ""))
        if body and not is_deleted_or_bot(body, post.get("author", "")):
            professor = extract_professor_from_text(body)
            parts = split_long_text(body)
            for part in parts:
                chunk_text = f"[Reddit post: \"{title}\"] {part}"
                chunks.append({
                    "text": chunk_text,
                    "professor": professor,
                    "course": "general",
                    "source_url": source_url,
                    "source_type": "reddit",
                })

        # Process comments
        for comment in thread["comments"]:
            text = clean_reddit_text(comment.get("body", ""))
            author = comment.get("author", "")
            if not text or is_deleted_or_bot(text, author):
                continue

            professor = extract_professor_from_text(text)
            parts = split_long_text(text)
            for part in parts:
                chunk_text = f"[Reddit comment on: \"{title}\"] {part}"
                chunks.append({
                    "text": chunk_text,
                    "professor": professor,
                    "course": "general",
                    "source_url": source_url,
                    "source_type": "reddit",
                })

    return chunks


# ── Inspection ───────────────────────────────────────────────────────

def inspect_chunks(chunks: list[dict]):
    """Print representative samples and quality flags."""
    print(f"\n{'='*60}")
    print(f"TOTAL CHUNKS: {len(chunks)}")
    print(f"{'='*60}")

    # Count by source type
    rmp_count = sum(1 for c in chunks if c["source_type"] == "rmp")
    reddit_count = sum(1 for c in chunks if c["source_type"] == "reddit")
    print(f"  RMP chunks:    {rmp_count}")
    print(f"  Reddit chunks: {reddit_count}")

    # Show 5 representative chunks (mix of RMP and Reddit)
    print(f"\n{'─'*60}")
    print("5 REPRESENTATIVE CHUNKS:")
    print(f"{'─'*60}")

    # Pick 3 RMP + 2 Reddit (or as many as available)
    rmp_chunks = [c for c in chunks if c["source_type"] == "rmp"]
    reddit_chunks = [c for c in chunks if c["source_type"] == "reddit"]

    samples = []
    # Spread across different professors for RMP
    seen_profs = set()
    for c in rmp_chunks:
        if c["professor"] not in seen_profs and len(samples) < 3:
            samples.append(c)
            seen_profs.add(c["professor"])
    # Add Reddit samples
    for c in reddit_chunks:
        if len(samples) < 5:
            samples.append(c)

    for i, chunk in enumerate(samples, 1):
        text_preview = chunk["text"][:300]
        if len(chunk["text"]) > 300:
            text_preview += "..."
        print(f"\n  [{i}] source={chunk['source_type']} | "
              f"professor={chunk['professor']} | course={chunk['course']}")
        print(f"      chars={len(chunk['text'])}")
        print(f"      text: {text_preview}")

    # Flag quality issues
    print(f"\n{'─'*60}")
    print("QUALITY FLAGS:")
    print(f"{'─'*60}")

    too_short = [c for c in chunks if len(c["text"]) < 50]
    too_long = [c for c in chunks if len(c["text"]) > 1200]

    if too_short:
        print(f"  ⚠ {len(too_short)} chunks under 50 chars:")
        for c in too_short[:3]:
            print(f"    - [{c['source_type']}] \"{c['text'][:80]}\"")
    else:
        print("  ✓ No chunks under 50 chars")

    if too_long:
        print(f"  ⚠ {len(too_long)} chunks over 1200 chars:")
        for c in too_long[:3]:
            print(f"    - [{c['source_type']}] {len(c['text'])} chars, "
                  f"professor={c['professor']}")
    else:
        print("  ✓ No chunks over 1200 chars")

    # Check chunk count is in expected range
    if len(chunks) < 50:
        print(f"  ⚠ Total chunk count ({len(chunks)}) is below 50 — may need more sources")
    elif len(chunks) > 2000:
        print(f"  ⚠ Total chunk count ({len(chunks)}) exceeds 2000 — consider filtering")
    else:
        print(f"  ✓ Chunk count ({len(chunks)}) is in the 50-2000 range")

    print()


# ── Main ─────────────────────────────────────────────────────────────

def main():
    rmp_path = os.path.join("documents", "rmp_reviews.json")
    reddit_path = os.path.join("documents", "reddit_posts.json")

    if not os.path.exists(rmp_path) or not os.path.exists(reddit_path):
        print("ERROR: Raw JSON files not found in documents/.")
        print("Run scrape.py first to fetch the data.")
        return

    print("Loading raw data...")
    professors = load_rmp_reviews(rmp_path)
    threads = load_reddit_posts(reddit_path)

    print("Chunking RMP reviews...")
    rmp_chunks = chunk_rmp(professors)

    print("Chunking Reddit posts...")
    reddit_chunks = chunk_reddit(threads)

    all_chunks = rmp_chunks + reddit_chunks

    inspect_chunks(all_chunks)

    # Save chunks for downstream use (milestone 4)
    chunks_path = os.path.join("documents", "chunks.json")
    with open(chunks_path, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(all_chunks)} chunks → {chunks_path}")


if __name__ == "__main__":
    main()
