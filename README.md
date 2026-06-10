# The Unofficial Guide — Project 1

> **How to use this template:**
> Complete each section _after_ you've built and tested the corresponding part of your system.
> Do not write placeholder text — if a section isn't done yet, leave it blank and come back.
> Every section below is required for submission. One-liners will not receive full credit.

---

## Domain

Student reviews of Computer Science professors at California State University, Long Beach (CSULB). This knowledge is valuable because the official course catalog and department website only describe what a course covers, never how it is taught, how difficult the exams are, or which professors students recommend. Students need practical answers like "which professor should I take for CECS 323?" or "how heavy is the workload?" that only come from other students' experiences on RateMyProfessors and Reddit.

---

## Document Sources

| #   | Source                                            | Type   | URL or file path                                                                                  |
| --- | ------------------------------------------------- | ------ | ------------------------------------------------------------------------------------------------- |
| 1   | Prof. Neal Terrel — RateMyProfessors              | RMP    | https://www.ratemyprofessors.com/professor/1810660                                                |
| 2   | Prof. Frank Murgolo — RateMyProfessors            | RMP    | https://www.ratemyprofessors.com/professor/464926                                                 |
| 3   | Prof. Susan Nachawati — RateMyProfessors          | RMP    | https://www.ratemyprofessors.com/professor/115586                                                 |
| 4   | Prof. Hailu Xu — RateMyProfessors                 | RMP    | https://www.ratemyprofessors.com/professor/2639859                                                |
| 5   | Prof. Steve Gold — RateMyProfessors               | RMP    | https://www.ratemyprofessors.com/professor/307547                                                 |
| 6   | Prof. Darin Goldstein — RateMyProfessors          | RMP    | https://www.ratemyprofessors.com/professor/52818                                                  |
| 7   | r/CSULB — "Which CS professors do you recommend?" | Reddit | https://www.reddit.com/r/CSULB/comments/1o7k69s/csulb_students_which_computer_science_professors/ |
| 8   | r/CSULB — "Why is the CS program bad?"            | Reddit | https://www.reddit.com/r/CSULB/comments/1ejytkq/why_is_the_cs_program_bad/                        |
| 9   | r/CSULB — "Quality of CS education in CSULB"      | Reddit | https://www.reddit.com/r/CSULB/comments/14kuu85/quality_of_computer_science_education_in_csulb/   |
| 10  | Prof. Shannon Cleary — RateMyProfessors           | RMP    | https://www.ratemyprofessors.com/professor/1287692                                                |

---

## Chunking Strategy

**Chunk size:** One review = one chunk for RMP; one comment or post = one chunk for Reddit. Most chunks are 150–300 tokens (roughly 600–1200 characters). A hard cap of 1200 characters triggers splitting for long Reddit posts.

**Overlap:** 150 characters (~30–50 tokens), applied only when a long Reddit post is split across chunk boundaries. RMP reviews are never split so they have no overlap.

**Why these choices fit your documents:** Most RMP reviews are 1–4 sentences. Splitting a short review would destroy its meaning. Reddit comments can be longer and discuss multiple topics (e.g., midterm format in one paragraph, final format in another), so overlap preserves context at split points. Preprocessing includes stripping HTML tags/entities from RMP text and removing markdown artifacts (links, bold/italic, headings, blockquotes) from Reddit text. Deleted comments, removed posts, and bot messages are filtered out. Each chunk is prefixed with structured metadata (e.g., `[RMP review for Neal Terrel — CECS323 | Quality: 5/5, Difficulty: 4/5]`) so the chunk is self-contained.

**Final chunk count:** 731

---

## Embedding Model

**Model used:** `all-MiniLM-L6-v2` via sentence-transformers. It is fast, runs locally with no API cost, and produces 384-dimensional embeddings with a 256-token context window which is sufficient for our short review chunks.

**Production tradeoff reflection:** A stronger model like would distinguish sentiment and nuance more reliably (e.g., recognizing that "free-response" is relevant to a query about exam format even when the chunk's overall theme is difficulty). An API-hosted model like OpenAI `text-embedding-3-large` would remove the 256-token cap, allowing long Reddit posts to be embedded whole without splitting. The tradeoff is latency (API round-trips) and cost. For a production system serving real CSULB students, the improved retrieval accuracy would likely justify the cost.

---

## Grounded Generation

**System prompt grounding instruction:** The system prompt tells the LLM: "Answer ONLY based on the student reviews provided below. Do not use outside knowledge about professors or courses." It also instructs: "If even ONE review contains a direct answer to the question, use it. Only say 'I don't have enough information in the reviews to answer that' when NONE of the reviews address the question at all." This prevents both hallucination and over-refusal. Retrieved chunks are formatted as a numbered list with professor and course metadata so the LLM can distinguish which review says what:

```
[1] (Professor: Neal Terrel, Course: CECS323)
[RMP review for Neal Terrel — CECS323 | Quality: 5/5, Difficulty: 3/5] ...
```

**How source attribution is surfaced in the response:** Source attribution is programmatic, not parsed from LLM output. After the LLM generates its answer, the system deduplicates the retrieved chunks' metadata (source_url, source_type, professor) and appends clickable source links below the answer. This ensures sources are always accurate and never hallucinated by the model.

---

## Evaluation Report

| #   | Question                                                                       | Expected answer             | System response (summarized)                                                                                                                                                                                        | Retrieval quality  | Response accuracy |
| --- | ------------------------------------------------------------------------------ | --------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------ | ----------------- |
| 1   | Are Prof. Neal Terrel's exams multiple-choice or free-response in CECS 323?    | Free response               | The system retrieved 8 CECS323 reviews for Terrel but the specific chunk mentioning "free-response" ranked 28th (outside top-k). The system responded that it didn't have enough information to confirm the format. | Partially relevant | Inaccurate        |
| 2   | Is attendance mandatory for CECS 491B with Professor Frank Murgolo?            | Yes                         | The system retrieved relevant Murgolo reviews and correctly stated that attendance is mandatory.                                                                                                                    | Relevant           | Accurate          |
| 3   | Which professor would you not recommend for CECS174 for a beginner programmer? | Susan Nachawati             | The system retrieved reviews mentioning Nachawati and other professors, and identified her as one students would not recommend for beginners.                                                                       | Relevant           | Accurate          |
| 4   | How heavy is the workload for Neal Terrel's classes?                           | Very heavy                  | The system retrieved multiple Terrel reviews describing heavy workload, projects, and time-consuming assignments. Correctly summarized as very heavy.                                                               | Relevant           | Accurate          |
| 5   | How difficult is Neal Terrel's 491B class?                                     | He doesn't teach this class | The system correctly indicated it did not have reviews for Terrel teaching 491B.                                                                                                                                    | Relevant           | Accurate          |

**Retrieval quality:** Relevant / Partially relevant / Off-target
**Response accuracy:** Accurate / Partially accurate / Inaccurate

---

## Failure Case Analysis

**Question that failed:** "Are Prof. Neal Terrel's exams multiple-choice or free-response in CECS 323?"

**What the system returned:** The system said it didn't have enough information to confirm the exam format, even though a chunk in the dataset explicitly states "His tests are all free-response and insanely difficult."

**Root cause (tied to a specific pipeline stage):** This is a **retrieval** failure. The relevant chunk (chunk containing "free-response") ranked 28th out of 731 with a cosine distance of 0.4265, well outside the top-k=8 window. The embedding model (`all-MiniLM-L6-v2`) encoded the chunk's dominant semantic meaning as "difficulty complaint" rather than "exam format description" because the phrase "free-response" is a small detail within a longer negative review. The query asks specifically about format, but the embedding captures overall topic, not specific details. Meanwhile, 8 other CECS323/Terrel chunks that discuss general quality and difficulty ranked higher because their embeddings are closer to the query's mention of "exams" and "CECS 323."

**What you would change to fix it:** Use a stronger embedding model that better captures fine-grained details within chunks. Alternatively, supplement semantic search with keyword-based retrieval so that the exact term "free-response" in the chunk would boost its ranking when the query also contains "free-response."

---

## Spec Reflection

**One way the spec helped you during implementation:** The planning doc's chunking strategy — one review = one chunk with structured metadata prefixes — directly shaped the pipeline. Having decided upfront that each RMP review would be its own chunk with a `[RMP review for ... | Quality/Difficulty]` prefix meant the implementation was straightforward: iterate over ratings, prepend the prefix, and emit.

**One way your implementation diverged from the spec, and why:** The spec planned for top-k of 6–10, and the implementation settled on k=8. During testing, this turned out to be too small for some queries where the answer was buried in a lower-ranked chunk (e.g., the exam format question where the relevant chunk ranked 28th). The spec didn't anticipate that the embedding model would rank chunks by dominant theme rather than specific details, which is a gap that would have required hybrid search or a larger k to address.

---

## AI Usage

**Instance 1**

- _What I gave the AI:_ I gave Claude my Chunking Strategy and Retrieval Approach sections from planning.md, along with the existing pipeline.py chunk format, and asked it to implement rag.py with embedding into ChromaDB, retrieval, and Groq-based generation.
- _What it produced:_ A complete rag.py with functions for loading chunks, building a persistent ChromaDB vector store with cosine similarity, embedding with SentenceTransformer, retrieval with top-k, and a full ask() pipeline that retrieves chunks, generates an answer via Groq, and programmatically attaches deduplicated source links.
- _What I changed or overrode:_ I adjusted the system prompt's refusal threshold — the original prompt was too conservative, telling the LLM to refuse when it didn't have "enough" information, which caused it to refuse even when relevant reviews were present. I changed it to only refuse when NONE of the reviews address the question.

**Instance 2**

- _What I gave the AI:_ I gave Claude the full implementation plan for Milestones 4 and 5 (embedding, retrieval, generation, and Streamlit interface) along with the existing codebase structure and chunk format.
- _What it produced:_ A Streamlit app (app.py) with cached vector store initialization, a text input for queries, a spinner during processing, markdown-rendered answers, and clickable source links grouped by source type and professor.
- _What I changed or overrode:_ I tested the evaluation queries and discovered a retrieval failure where the "free-response" chunk ranked 28th instead of within top-8. This revealed a limitation of the MiniLM embedding model rather than a code issue, which I documented in the Failure Case Analysis.
