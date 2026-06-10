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

**Sample chunks:**

1. **RMP — Neal Terrel, CECS449** (source: ratemyprofessors.com/professor/1810660)
   > `[RMP review for Neal Terrel — CECS449 | Quality: 5/5, Difficulty: 3/5] 449 was a challenging course, but it is also one of the most engaging classes I've taken throughout my entire time at college. Professor Terrell provides all the resources to be successful and assigns the topics into meaningful, hands-on projects. Professor Terrell cares for his students & its been a pleasure being in his class. MY GOAT`

2. **RMP — Frank Murgolo, CECS323** (source: ratemyprofessors.com/professor/464926)
   > `[RMP review for Frank Murgolo — CECS323 | Quality: 3/5, Difficulty: 2/5] No homework just quizzes. He just doesn't seem to care much. His quizzes are made through chatgpt. Easy class but you wont learn much`

3. **RMP — Susan Nachawati, 174** (source: ratemyprofessors.com/professor/115586)
   > `[RMP review for Susan Nachawati — 174 | Quality: 1/5, Difficulty: 5/5] Nobody can understand her class`

4. **Reddit post — r/CSULB** (source: reddit.com/r/CSULB/comments/1o7k69s)
   > `[Reddit post: "CSULB students: Which Computer Science professors do you recommend or not recommend"] I'm trying to plan my next semester and wanted to hear people's experiences with CS professors at CSULB. How's Professor Ehsan Yaghmaei? Would you recommend him or not? Also open to hearing which professors you think are good or bad for core CS classes in general (CECS 448, 328, 326, etc.). Thanks!`

5. **Reddit comment — r/CSULB** (source: reddit.com/r/CSULB/comments/1o7k69s)
   > `[Reddit comment on: "CSULB students: Which Computer Science professors do you recommend or not recommend"] S tier: Terrell, Winter, Moon A tier: Hailu Xu, Goldstein, Ebert, Jurgenson, Sayadi B tier: Gold, Phuong Nguyen, Murgolo, Lackpour C tier: Nachawati D tier: Ghaforyfard (for CS), Qudrat F tier: Brown, Link, Uuh ...`

---

## Embedding Model

**Model used:** `all-MiniLM-L6-v2` via sentence-transformers. It is fast, runs locally with no API cost, and produces 384-dimensional embeddings with a 256-token context window which is sufficient for our short review chunks.

**Production tradeoff reflection:** A stronger model like would distinguish sentiment and nuance more reliably (e.g., recognizing that "free-response" is relevant to a query about exam format even when the chunk's overall theme is difficulty). An API-hosted model like OpenAI `text-embedding-3-large` would remove the 256-token cap, allowing long Reddit posts to be embedded whole without splitting. The tradeoff is latency (API round-trips) and cost. For a production system serving real CSULB students, the improved retrieval accuracy would likely justify the cost.

**Retrieval test examples:**

**Query 1:** "How heavy is the workload for Neal Terrel's classes?"

| Rank | Distance | Professor | Course | Chunk preview |
|------|----------|-----------|--------|---------------|
| 1 | 0.4551 | Neal Terrel | CECS328 | "Lectures are funny and informative. Workload is fairly modest, and while the tests are difficult he's not a harsh grader..." |
| 2 | 0.4565 | Neal Terrel | CECS323 | "The lectures, HW, and projects prepare you for the exam. Nothing should be surprising if you put in the work..." |
| 3 | 0.4567 | Neal Terrel | CECS323 | "This man is an A+ teacher and he expects as much as he gives. I had no trouble getting an A in his class because doing the homework..." |
| 4 | 0.4577 | Neal Terrel | CECS475 | "Neal is goated. But if you're looking for an easy A, you HAVE to put in the effort. No curving. Required to PASS ALL projects..." |
| 5 | 0.4775 | Neal Terrel | CECS282 | "Honestly, hands down one of the best professors I've ever taken..." |

All 5 results are for the correct professor (Neal Terrel) across multiple courses, which is appropriate since the query asks about "his classes" in general. The chunks discuss workload, effort level, and grading — directly relevant to the question. Distances are all below 0.5, indicating good semantic similarity.

**Query 2:** "Is attendance mandatory for CECS 491B with Professor Frank Murgolo?"

| Rank | Distance | Professor | Course | Chunk preview |
|------|----------|-----------|--------|---------------|
| 1 | 0.3965 | Frank Murgolo | CECS491B | "I took him for Senior Project. He's a very easy grader and passionate about student projects. We had daily check-ins..." |
| 2 | 0.4017 | Frank Murgolo | CECS343 | "One of the easiest A's you can get. Everything is open note and open internet. He doesn't grade attendance..." |
| 3 | 0.4046 | Frank Murgolo | CECS323 | "Great professor and an even better person. Very nice and very helpful..." |

The top result is a CECS491B review for Murgolo — an exact match for course and professor. The second result mentions attendance policy for a different Murgolo course, which provides useful context. Distances are tighter (0.39–0.40) than the previous query, showing strong relevance.

**Query 3:** "Which professor would you not recommend for CECS174 for a beginner programmer?"

| Rank | Distance | Professor | Course | Chunk preview |
|------|----------|-----------|--------|---------------|
| 1 | 0.3648 | Neal Terrel | CECS174 | "Among everyone I've talked to about CECS professors, all agree that you should always take Neal Terrell..." |
| 2 | 0.3922 | Steve Gold | CECS325 | "An amazing and very experienced professor..." |
| 3 | 0.3975 | Neal Terrel | CECS174 | "He is really good at what he teaches and probably one of the better CECS professors..." |
| 4 | 0.4012 | Steve Gold, Darin Goldstein | general | "Goldstein is a great prof for 328, his lectures are really interactive..." |
| 5 | 0.4112 | Susan Nachawati | CECS100 | "She is okay at teaching. Her lectures can be a bit overwhelming at times..." |

---

## Grounded Generation

**System prompt grounding instruction:** The system prompt tells the LLM: "Answer ONLY based on the student reviews provided below. Do not use outside knowledge about professors or courses." It also instructs: "If even ONE review contains a direct answer to the question, use it. Only say 'I don't have enough information in the reviews to answer that' when NONE of the reviews address the question at all." This prevents both hallucination and over-refusal. Retrieved chunks are formatted as a numbered list with professor and course metadata so the LLM can distinguish which review says what:

```
[1] (Professor: Neal Terrel, Course: CECS323)
[RMP review for Neal Terrel — CECS323 | Quality: 5/5, Difficulty: 3/5] ...
```

**How source attribution is surfaced in the response:** Source attribution is programmatic, not parsed from LLM output. After the LLM generates its answer, the system deduplicates the retrieved chunks' metadata (source_url, source_type, professor) and appends clickable source links below the answer. This ensures sources are always accurate and never hallucinated by the model.

**Example response 1:**

> **Q:** How heavy is the workload for Neal Terrel's classes?
>
> **A:** The workload for Neal Terrel's classes is generally considered moderate. Review [1] describes the workload as "fairly modest", while reviews [2], [3], and [5] suggest that the workload can be challenging, but manageable with effort. Review [3] mentions that doing the homework prepares students for tests, and review [5] notes that there is a lab every week, but the workload is still doable. Review [4] warns that an "easy A" requires effort, and review [8] mentions that projects only take a weekend to complete. Overall, the workload is not extremely heavy, but it does require consistent effort to keep up with the coursework.
>
> **Sources:**
> - [RMP — Neal Terrel](https://www.ratemyprofessors.com/professor/1810660)

**Example response 2:**

> **Q:** Is attendance mandatory for CECS 491B with Professor Frank Murgolo?
>
> **A:** According to review [1], attendance is mandatory for CECS 491B with Professor Frank Murgolo, but he is understanding if you miss class due to an emergency.
>
> **Sources:**
> - [RMP — Frank Murgolo](https://www.ratemyprofessors.com/professor/464926)
> - [RMP — Neal Terrel](https://www.ratemyprofessors.com/professor/1810660)

**Out-of-scope query example:**

> **Q:** What is the best restaurant near CSULB?
>
> **A:** I don't have enough information in the reviews to answer that.

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

## Query Interface

The interface is a Streamlit web app (`streamlit run app.py`).

**Input:** A single text field where the user types a natural-language question about CSULB CS professors or courses.

**Output:** A markdown-rendered answer followed by a list of clickable source links (each labeled with source type and professor name).

**Sample interaction transcript:**

```
User types: "Is attendance mandatory for CECS 491B with Professor Frank Murgolo?"

[spinner: "Searching reviews and generating answer..."]

Answer:
  According to review [1], attendance is mandatory for CECS 491B with
  Professor Frank Murgolo, but he is understanding if you miss class
  due to an emergency.

Sources:
  - RMP — Frank Murgolo  →  ratemyprofessors.com/professor/464926
  - RMP — Neal Terrel    →  ratemyprofessors.com/professor/1810660
```

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
