## 1. Part 1 – Data Owner: Building the document ingestion pipeline (Ingest)

![Ingestion pipeline overview](images/part1_ingest_overview.png)

In a Retrieval‑Augmented Generation (RAG) system, the ingestion stage strongly influences answer quality. The goal of ingestion is to turn raw documents into clean, structured text + metadata that can later be chunked, embedded, indexed, and retrieved with citations.

This project’s MVP ingestion workflow focuses on **text‑based documents** (PDF, DOCX, TXT, MD) and follows a single, consistent pipeline to reduce operational complexity.

---

### 1.1. Pipeline overview

The ingestion workflow can be summarized into three main stages:

1. **Loading**: Collect documents from different formats and locations.
2. **Splitting**: Break long content into chunks that fit LLM context windows and retrieval needs.
3. **Indexing handoff**: Provide chunk‑ready text + consistent metadata so the indexing layer can build embeddings and an index.

---

### 1.2. Key concepts (beginner‑friendly)

- **Document loading**: Read files and extract text (handling multiple formats reliably).
- **Text splitting**: Chunk size and overlap are tuned to preserve meaning and avoid losing context at chunk boundaries.
- **Metadata**: Store minimal but useful identifiers (document id, file name, updated timestamp, etc.) to support later citation and debugging.

---

### 1.3. Why Part 1 matters

If ingestion is unstable (bad parsing, inconsistent metadata, poor chunking), retrieval quality drops and the LLM is more likely to hallucinate. A stable Part 1 makes Parts 2–4 measurably better and makes Part 5 (end‑to‑end demo) much easier.


## 2. Part 2 – Embedding + Indexing Owner: Building a Searchable Index

![Embedding + Indexing overview](images/part2_embedding_indexing.png)

In the RAG chatbot architecture, the **Embedding + Indexing** lane (Person 2) is the bridge between ingested data and the Retrieval layer. If Person 1 focuses on “getting documents into the system and normalizing them”, Person 2 is responsible for turning those text chunks into **searchable vectors** and storing them in a **consistent index** ready for retrieval.

---

### 2.1. What is Embedding and why do we need it?

**Embedding** is the process of converting each text chunk into a fixed‑length vector of real numbers. The key idea:

- Texts that are **similar in meaning** should end up with vectors that are **close to each other** in vector space.
- The user’s question is also embedded into a vector, so it can be compared against all chunk vectors.

You can think of embedding as “translating text into coordinates in a high‑dimensional space”. When the user asks a question, the system:

1. Embeds the question into a vector.
2. Compares this vector with all chunk vectors in the index.
3. Selects the chunks whose vectors are closest to the question vector (i.e., most semantically similar).

This is the foundation of **semantic search** – searching by meaning instead of exact keyword matches.

---

### 2.2. Why is Indexing necessary?

Without indexing, every single question would require the system to:

- read all documents again,
- re-split them into chunks,
- re-embed everything,
- and then compare all vectors.

This is **too slow** and impractical for non‑trivial document collections.

**Indexing** solves this by:

- storing in advance:
  - `chunk_id` → `text` (original content),
  - `chunk_id` → `vector` (embedding),
  - metadata like `source_id`, `source_name`, file path, timestamps…
- organizing everything into a **snapshot index** that the Retrieval layer can load and query efficiently.

In this project, the index can be stored as a **local JSON** or backed by systems like **Qdrant**. Regardless of storage backend, the core idea is:

> “Every chunk in the system has a vector, clear metadata, and all of it is stored in a consistent structure that retrieval can search quickly.”

---

### 2.3. The critical principle: Consistency between Embedding and Index

Person 2 must always care about **consistency**:

- Vectors for chunks and for questions must be created using the **same embedding configuration**:
  - same model (e.g. `llama3.1:8b`),
  - same backend (`ollama` vs a simple fallback).
- If you change the embedding model but **do not** rebuild the index, old and new vectors will effectively live in different “coordinate systems”, making similarity scores unreliable.

In the project’s lane description, this maps to:

- “Finalize embedding model, vector dimensions, payload schema…”
- “Index is built correctly after ingest; delete/update does not corrupt the index; have a clear rebuild plan…”

Practically, Person 2 must decide:

- When a **full rebuild** is required.
- When an **incremental sync** is enough.

---

### 2.4. Index lifecycle: Full rebuild vs Incremental sync

An index is not built once and forgotten. It has a full **lifecycle**:

#### 2.4.1 Full rebuild – constructing the index from scratch

This operation “does everything again”:

- Scan the entire `data_input` directory.
- Read each file, split into chunks.
- Call the embedding backend to get vectors for **all** chunks.
- Write a new snapshot index that replaces the old one.

Typical use cases:

- First‑time initialization.
- Embedding model changes (`embedding_model` updated).
- Chunking logic changes (split strategy, chunk size…).
- You want a clean index after significant ingest changes.

#### 2.4.2 Incremental sync – updating without rebuilding everything

This operation saves time and resources:

1. Scan the `data_input` directory to get the current file list.
2. Compare with the previous index snapshot:
   - new files → add to index,
   - deleted files → remove their chunks from index,
   - modified files (different `updated_at` timestamp) → re-embed only these files’ chunks.
3. Keep chunks from unchanged files as they are.

This is how Person 2 addresses the requirement for **incremental updates** while avoiding unnecessary heavy rebuilds.

#### 2.4.3 Delete source – removing a single document from the index

Besides rebuild and sync, Person 2 usually supports:

- Deleting a specific `source_id` from the index.
- Automatically removing all chunks associated with that source.

This avoids full rebuilds when the user just wants to remove a few documents.

---

### 2.5. Embedding backend in this project: Ollama + fallback

In `Conquer_AIO_ChatBotRAG`, embeddings are designed to:

- **Prefer Ollama**:
  - When the `Ollama` endpoint is available, the system calls its embedding API.
  - Resulting vectors generally have strong semantic quality for search.
- **Fallback to simple hashed embeddings** when the local environment is limited:
  - A lightweight hashing technique is used to build fixed‑size vectors.
  - The purpose is:
    - to keep **Person 2’s pipeline runnable** on most local machines,
    - to avoid heavy external dependencies for simple demos.

For beginners:

- Treat the fallback as a “demo mode” that lets you run the full pipeline.
- For real deployments, configure a more powerful embedding model (for example, via Ollama).

---

### 2.6. Index payload and handoff to Retrieval (Person 3)

Once the index is built, Person 2 must ensure the snapshot contains:

- **Source-level metadata**:
  - each file mapped to a `source_id`,
  - names, paths, last modified timestamps.
- **Chunk-level records**:
  - `source_id`, `source_name`,
  - `chunk_id`,
  - `text`,
  - `vector`.
- Index metadata like:
  - `embedding_backend`,
  - `embedding_model`,
  - `built_at` timestamp.

This is effectively the “handoff contract” from lane 2 to lane 3:

- Retrieval does not need to know how embeddings were computed.
- Retrieval just needs:
  - a list of chunks with text + vectors,
  - metadata that is rich enough for filtering, debugging, and reporting.

---

### 2.7. Beginner‑friendly recap

You can summarize Person 2’s responsibilities in three key points:

1. **Embedding**: Convert text into vectors so that semantically similar texts are close in vector space.
2. **Indexing**: Store vectors and metadata into a structured snapshot that retrieval can query efficiently.
3. **Consistency & lifecycle**:
   - Rebuild the index when the embedding model or chunking logic changes.
   - Use incremental sync when only a subset of documents is added/updated/removed.

Once you understand lane 2, it becomes much clearer how a RAG chatbot can “remember” document content and find the right passages within a few hundred milliseconds when a user asks a question.


## 3. Part 3 - Retrieval Owner: Designing Hybrid Retrieval for the RAG Chatbot

![Hybrid Retrieval overview](images/part3_retrieval_overview.png)

### 3.1. The role of Retrieval in this project

<p align="center"><img src="imgpart3.png" width="760"></p>
<p align="center"><em>Figure 3.1. Retrieval.</em></p>

In this project architecture, Retrieval is the layer between **Indexing** and **RAG Core**:

1. Receive the `index snapshot` from `IndexingService`.
2. Retrieve the most relevant chunks for the user question.
3. Re-rank results to reduce noise before passing context to the LLM prompt.

The handoff to RAG Core happens in `app/rag_core/context/context_builder.py`: it only returns final chunks with `source_id`, `source_name`, `chunk_id`, `text`, and `score`.

### 3.2. Implemented retrieval pipeline

The main implementation is in `app/retrieval/hybrid/__init__.py` with the `HybridRetriever` class.

#### 3.2.1. Build/refresh the retrieval internal index

- Call `indexing_service.sync_index()` to synchronize the latest data.
- Get the snapshot via `get_index_snapshot()`.
- Normalize chunk payloads into `IndexedChunk` (`chunk_id`, `source_id`, `source_name`, `text`, `vector`, `metadata`).
- Remove exact duplicates with fingerprint `sha1(normalize_text(text))`.
- Rebuild keyword-channel statistics: term frequency, IDF, and average document length.

#### 3.2.2. Query expansion

The retriever uses rule-based query expansion (`QUERY_EXPANSION_RULES`) to improve recall for specific domain phrases such as:

- `giấy phép` -> `license`, `licensed`
- `khóa học` -> `course`, `curriculum`
- `mô đun/module` -> `resume`, `cover letter`, `interview`, ...

#### 3.2.3. Hybrid retrieval (Keyword + Vector)

Hybrid search combines keyword-search results and vector-search results. Its main advantages are:

- Search efficiency: Sparse retrieval (keyword search) finds results based on lexical overlap, while dense retrieval (vector search) uses more complex representations (for example neural embeddings) to compare texts.
- Accuracy: Sparse retrieval is often strong for exact term matching, while dense retrieval can provide better semantic matching from learned representations.
- Result diversity: Combining sparse and dense retrieval provides a richer set of results, from lexical matches to semantic matches.
- Flexibility: The balance between sparse and dense retrieval can be tuned based on application needs and data characteristics.

##### 3.2.3.1. Keyword search

- Uses a lightweight in-house BM25 implementation (`_keyword_search`), without external dependencies.
- Tokenization goes through `normalize_text()` + regex `\w+` (file `app/retrieval/text_utils.py`).

##### 3.2.3.2. Vector search

This is a content search technique using vector embeddings to compute similarity.

- Embed the query using `EmbeddingService.embed_query()` with the same backend used during indexing.
- Compute cosine similarity against each chunk vector (`_cosine_similarity`).

#### 3.2.4. Fusion with weighted RRF

The two channels are fused with weighted Reciprocal Rank Fusion:

- `keyword_weight = 0.45`
- `vector_weight = 0.55`
- `rrf_k = 60`

Idea: a chunk ranked high in either channel gets rewarded, making ranking more stable than relying on one absolute score.

#### 3.2.5. Noise reduction before reranking

1. **Near-duplicate removal** using token-level Jaccard (`dedup_jaccard_threshold = 0.88`) within the same source.
2. **Candidate pool** limited by `rerank_pool_k`.

#### 3.2.6. Heuristic rerank

The reranker in `app/retrieval/reranker/__init__.py` scores by feature combination:

- `fused_norm`: normalized fusion score
- `coverage`: query token coverage inside the chunk
- `phrase_hit`: whether the normalized query appears as an exact phrase in the chunk
- `source_score`: source relevance score from rules
- `length_score`: preference for reasonable chunk length

Current linear formula:

`final_score = 0.44*fused_norm + 0.22*coverage + 0.08*phrase_hit + 0.22*source_score + 0.04*length_score`

Besides boosting the right domain source, the system also applies a **mismatch penalty** (`source_mismatch_penalty_factor = 0.15`) when a query triggers a source hint but the chunk source is off-domain.

#### 3.2.7. Threshold + source priority + fallback

- Filter by `min_context_score = 0.08`.
- If filtered results are empty: fallback to top reranked candidates to avoid empty context.
- `source_priority_enabled = True`: when query matches source-priority rules, preferred-domain sources are promoted if they pass `source_priority_min_score = 0.14`.

#### 3.2.8. Output to RAG Core

Final output is a list of `RetrievedChunk` including:

- `chunk_id`, `source_id`, `source_name`, `text`
- `final_score`
- component scores: `fused_score`, `keyword_score`, `vector_score`
- per-channel ranks + `features` for debugging

### 3.3. Official retrieval configuration (default)

Defined in `app/shared/configs/settings.py`:

- `retrieval_top_k = 5`
- `retrieval_candidate_top_k = 30`
- `retrieval_rerank_pool_k = 20`
- `retrieval_keyword_weight = 0.45`
- `retrieval_vector_weight = 0.55`
- `retrieval_rrf_k = 60`
- `retrieval_min_context_score = 0.08`
- `retrieval_dedup_jaccard_threshold = 0.88`
- `retrieval_source_priority_enabled = True`
- `retrieval_source_priority_min_score = 0.14`
- `retrieval_source_mismatch_penalty_factor = 0.15`
- `retrieval_debug = False`

Benchmark/quality gate:

- `retrieval_benchmark_top_k = 5`
- `retrieval_quality_hit_rate_threshold = 0.75`
- `retrieval_quality_mrr_threshold = 0.55`
- `retrieval_stability_runs = 2`

### 3.4. Benchmark and Definition of Done

Benchmark script: `app/retrieval/benchmark`.

Run command:

```bash
python3 -m app.retrieval.benchmark --top-k 5 --output reports/retrieval_report.json
```

Current sample report at `Project/reports/retrieval_report.json`:

- `total_questions`: **31**
- `hit_rate_at_k`: **0.9355**
- `precision_at_k`: **0.4258**
- `mean_reciprocal_rank (MRR)`: **0.9032**
- `passes_quality_gate`: **true**
- `stable_across_runs`: **true** (`stability_runs = 2`)
- `miss_buckets`: `source_not_hit: 1`, `keyword_not_hit: 1`


### 3.5. Hit/miss debugging mechanism

When `debug=True`, `HybridRetriever` returns `RetrievalDebugInfo` including:

- Hit counts per channel: keyword/vector/fused
- Number of chunks dropped by dedup and threshold
- Top chunk IDs at each stage
- Used query variants
- `miss_reason` when no relevant output is found

Main `miss_reason` values in code:

- `no_indexed_chunks`
- `no_keyword_or_vector_hits`
- `all_candidates_below_threshold`
- `vector_channel_empty`
- `keyword_channel_empty`
- `rerank_removed_all_candidates`

Additionally, the benchmark layer assigns analysis buckets such as `source_not_hit`, `keyword_not_hit`, and `relevant_chunk_outside_top_k`.

### 3.6. Conclusion from the Retrieval Owner perspective

The retrieval part of this project follows a practical MVP approach while staying extensible:

- **Hybrid search** balances precision and semantic recall.
- **Fusion + rerank + dedup + source-priority** reduce noisy context.
- **Benchmark + quality gate + stability check** provide measurable quality tracking.


## 4. Part 4 – RAG Core Owner: Context Assembly, Prompting, and Citation Answers

![RAG Core overview](images/part4_rag_core_overview.png)

If you view the RAG pipeline as a production line:

- Person 1 handles ingesting and normalizing documents,
- Person 2 handles embedding + indexing,
- Person 3 handles retrieval (finding the right chunks),
- **Person 4 (RAG Core)** is the final editor: assembling context, designing prompts for the LLM, calling the model, and returning answers with clear **citations**.

---

### 4.1. The role of RAG Core in the overall architecture

From a workflow perspective, RAG Core sits right after Retrieval:

1. The user asks a question via the frontend.
2. The backend calls Retrieval to get a ranked list of relevant chunks.
3. RAG Core:
   - assembles these chunks into a **context block**,
   - builds a **structured prompt**,
   - calls the LLM to generate an answer,
   - constructs a **citation list** for the frontend to display.

The key point: RAG Core **does not replace Retrieval**. Instead, it turns Retrieval’s output into a **grounded answer** that is explicitly tied to the ingested documents.

---

### 4.2. Context assembly: preparing what the LLM sees

Retrieval returns a list of chunks, each typically containing:

- `source_id`, `source_name` – the document source,
- `chunk_id` – the specific segment identifier,
- `text` – the actual content,
- `score` – a relevance score.

RAG Core must:

1. Select a subset of chunks (top‑k) so that the context does not exceed the LLM’s context window.
2. Arrange these chunks into a clear **context block**, usually with:
   - `[1], [2], …` labels,
   - source information, chunk id, and score,
   - the full text of each chosen chunk.

The goal of this step:

- Provide the LLM with a context that is **rich enough**, but not overwhelming.
- Give Person 4 control over “which information is fed into the prompt”.

---

### 4.3. Prompt design: talking to the LLM to reduce hallucination

The prompt is the “instruction sheet” for the LLM. A good prompt usually has:

1. **Role and behavior instructions** – for example:
   - “You are an AI assistant for a RAG system…”
   - “Answer based on the provided context…”
2. **Question section** – the user’s original question.
3. **Context section** – the retrieved chunks.
4. **Answering guidelines** – such as:
   - Answer in a specific language (e.g. Vietnamese).
   - Prefer information that appears in the context.
   - If context is insufficient, clearly state uncertainty.
   - Do not invent facts outside the context.

These constraints are the main tools for **reducing hallucination**:

- The LLM is encouraged not to make things up.
- It is forced to rely on the supplied context.
- It is allowed to say “I’m not sure” when evidence is missing.

In the lane description, this corresponds to:

- “Design the official prompt and context assembly.”
- “Reduce hallucination with context constraints…”

---

### 4.4. LLM generation and timeout/fallback behavior

Once the prompt is ready, RAG Core:

1. Sends it to the LLM (for example, a model served via Ollama).
2. Waits for a response within a configured timeout.

If the LLM responds in time:

- The returned text becomes the `answer`.

If the LLM is too slow or fails (timeout):

- RAG Core returns a **safe fallback message**, such as:
  - explaining that the model took too long,
  - suggesting to try a shorter question or a smaller `top_k`.

From Person 4’s perspective, this is crucial:

- Never leave the frontend “hanging” when the model misbehaves.
- Always give the user a graceful response with instructions on what to do next.

---

### 4.5. Citation building: letting users verify the answer

A strong RAG answer **not only gives the conclusion**, but also:

- shows **where that conclusion came from**.

That is why lane 4 must build a list of **citations**. Each citation typically includes:

- `source_id`, `source_name` – identifying the original document,
- `chunk_id` – the specific section,
- `score` – a relevance score,
- `snippet` – a shortened text fragment that is readable.

Why use **snippets instead of full text**?

- The UI stays cleaner and more focused.
- Users can quickly preview the evidence.
- If needed, they can still open the full document knowing exactly which part was used.

In this project, citations are the contract from RAG Core to the frontend:

- The backend returns a citation list.
- The frontend renders citation badges/cards so users can hover and see snippets.

---

### 4.6. API contract with the frontend: how lane 4 talks to the UI

From the frontend’s point of view, the chat endpoint (for example `/api/v1/chat`) returns a response containing:

- `answer`: the final answer text,
- `citations`: an array of citation objects (when enabled),
- `model`: the LLM model name,
- `latency_ms`: processing time,
- `conversation_id`: an identifier for this chat session.

Thanks to this clear contract:

- The frontend only needs to render these fields to get a full chat UI.
- Lane 4 can evolve its internal logic (prompt structure, context strategy) without breaking the interface.

---

### 4.7. Beyond prompt design: other ways RAG Core reduces hallucination

While a good prompt is necessary, lane 4 can also:

- Limit how many chunks go into the LLM (to avoid noisy or diluted context).
- Prioritize chunks with higher scores and trustworthy sources.
- Implement fallbacks when:
  - Retrieval fails to return meaningful context.
  - The LLM does not respond or produces an error.

Over time, Person 4 can collaborate with Persons 3 and 5 to:

- Define what a “grounded answer” means for the project.
- Build a demo question set to validate quality.
- Add logging/benchmarks to understand when and why hallucination happens.

---

### 4.8. Beginner‑friendly recap of Person 4’s lane

You can summarize the RAG Core lane with four keywords:

1. **Context** – receive ranked chunks from Retrieval and assemble them into a context block.
2. **Prompt** – craft a clear prompt that forces the model to rely on context.
3. **LLM** – call the model with timeout and safe fallback handling.
4. **Citation** – return structured evidence so users can verify the answer.

Once you understand Person 4’s responsibilities, you will see that a RAG pipeline is more than “just calling an LLM with documents” – it is a carefully designed flow that goes **from context → prompt → grounded answer**.


## 5. Part 5 – Eval/DevOps + Lightweight Frontend Owner: Making the System Truly End-to-End

![End-to-end overview](images/part5_end_to_end.png)

In a real‑world RAG chatbot project, “running end‑to‑end” is just as important as “clever algorithms” or “powerful models”. **Person 5 (Eval/DevOps + Lightweight Frontend)** is responsible for:

- ensuring the system can **run locally** or via **Docker**,
- providing **basic tests and checks** to avoid broken demos,
- and delivering a **simple but usable web UI** so beginners can try the chatbot quickly.

---

### 5.1. Big picture: Backend + Frontend in the GitHub repo

In this repo, you can think of the system as three main characters:

- **Frontend**: where users upload documents, chat, and inspect citations.
- **Backend API**: orchestrates ingest → retrieval → RAG Core.
- **LLM runtime** (e.g., Ollama): runs the model that generates answers.

What makes the product feel “alive” is not the technology list, but the **user journey**:

> Upload documents → the system prepares knowledge → ask questions → get answers with sources → users trust it and keep using it.

So Person 5 focuses on one outcome: **user confidence**:

1. Confidence that the system reliably runs end‑to‑end (no “it just hangs” moments).
2. Confidence that answers are grounded (citations are consistent and useful).

---

### 5.2. DevOps: Using Docker Compose to spin up the system

DevOps for an MVP does not need to be “fancy”, but it should follow three principles:

1. **Reproducible**: a new machine can follow the guide and get the same result.
2. **Ready‑aware**: services should expose readiness signals so you don’t have to guess.
3. **Low friction**: fewer manual steps means fewer human errors.

Docker Compose fits this goal well: it bundles the main services (LLM + backend) into a repeatable startup flow with healthchecks and environment configuration.  
Exact commands are listed in **Section 6** so this section stays concept‑first.

---

### 5.3. Health check: knowing whether the backend is “alive”

For beginners, trustworthy systems often start with a simple question:

> “Is it running?”

A **health check** is the standardized answer. It helps:

- DevOps confirm the service is ready to accept requests.
- Frontend avoid calling APIs that are not ready yet.
- Demo flows start at the right time (upload/ingest/chat).

A good health endpoint typically includes: status, timestamp, and model info—so you can catch “it runs, but with the wrong configuration” early.

---

### 5.4. Eval: Smoke tests and system checks for the RAG chatbot

Evaluation in an MVP is not “grading the model” yet. The more practical goal is:

1. **Protect the demo experience**: avoid basic issues that destroy user trust.
2. **Protect the knowledge pipeline**: ingest/index/retrieval/chat should not break mid‑flow.

So smoke checks should answer questions like:

- Is the environment OK (Python/Node, required packages)?
- Can we reach the LLM runtime?
- Is the backend up and healthy?
- Do we have documents to ingest?
- Does chat return an answer *and* citations in a consistent format?

This is like checking electricity and water before opening a shop: not glamorous, but essential.

---

### 5.5. Frontend: Chat UI and document management for beginners

A “lightweight” frontend does not mean “poor UI”. It means:

- focus on the **three core user actions**,
- and make them clear, predictable, and low‑friction.

Those three actions are:

1. **Bring knowledge in** (upload documents).
2. **Ask and receive** (chat).
3. **Trust and verify** (citations/snippets).

Three UX details that make a big difference for beginners:

- **Visible state**: uploading, ingesting, answering—so users know what’s happening.
- **Friendly fallbacks**: when something fails, tell users what to do next.
- **Readable citations**: short snippets + clear sources are enough to build trust.

---

### 5.6. API integration: how the frontend talks to the backend

What matters most is not “how many endpoints”, but a **stable contract**:

- Frontend needs to know what to send, what it receives, and what error structure looks like.
- Backend must keep response formats consistent so the UI remains reliable.

For beginners, it’s enough to remember four API flows:

1. **Health**: readiness check.
2. **Upload/Ingest**: bring knowledge in.
3. **Chat**: ask and get the answer.
4. **Citations/History**: verify evidence and revisit past messages.

The concrete run steps and commands live in **Section 6** to keep this part concept‑first.

---

### 5.7. End‑to‑end flow: from a user’s perspective

For a beginner‑friendly blog, the end‑to‑end flow should feel like a story about building trust:

1. **Start**: the system signals readiness (health is OK).
2. **Ingest knowledge**: the user uploads documents (upload/ingest).
3. **Ask**: the user asks a question and sees the answer appear smoothly (streaming).
4. **Verify**: citations show “this answer came from your documents”.
5. **Repeat**: new questions and new documents still work consistently.

Only when users complete this loop do they truly feel “this is a document Q&A chatbot”, not a generic chatbot.

---

### 5.8. Beginner‑friendly recap of Person 5’s lane

You can summarize lane 5 in three main responsibilities:

1. **Eval** – provide smoke tests and system checks to ensure “all pieces are running”.
2. **DevOps** – standardize how the system is launched (Docker, healthchecks, environment guides).
3. **Lightweight frontend** – deliver a simple but complete UI:
   - upload documents,
   - follow ingest/integration flow,
   - chat with documents and inspect citations.

Thanks to Person 5, the RAG chatbot project is not just theoretically sound on paper, but becomes a concrete product that beginners can **run, use, and evaluate end‑to‑end**.


## 6. Quick guide to run the project (EN)

### 6.1. Running with Docker (recommended for quick demo)

Requirements:

- **Docker** and **Docker Compose** installed.

Steps:

1. Open a terminal in the `Project/` directory of the repo.
2. Start the stack:

   ```bash
   cd Project
   docker compose -f docker/docker-compose.yml up -d
   ```

3. Wait until:
   - The **Ollama** container is healthy (model pulled successfully),
   - The **API** container is healthy (healthcheck `/health` passes).
4. Verify backend health:

   - Open `http://localhost:8000/health` in your browser.
   - If you see `status: ok` → backend is running.

5. Start the frontend:

   ```bash
   cd ../frontend
   npm install
   npm run dev
   ```

6. Open `http://localhost:3000` to access the chat UI, upload documents, and start asking questions.

### 6.2. Running locally without Docker

Requirements:

- Python 3.11+, Node.js 16+.

Step 1 – Backend environment:

```bash
cd Project
python -m venv venv
venv\Scripts\activate  # Windows
# or: source venv/bin/activate  (macOS/Linux)

pip install -r requirements.txt
```

Step 2 – Run Ollama and pull the model:

```bash
ollama serve
ollama pull llama3.1:8b
```

Make sure Ollama is listening on `http://localhost:11434`.

Step 3 – Run the FastAPI backend:

```bash
cd Project
python -m uvicorn app.api.main:app --host 0.0.0.0 --port 8000 --reload
```

Check:

- Open `http://localhost:8000/health` → expect `status: ok`.
- Open `http://localhost:8000/docs` → Swagger UI.

Step 4 – Prepare data and ingest:

1. Create a `data_input/` directory in `Project/` if it does not exist.
2. Place your documents (PDF/DOCX/TXT/MD) inside `data_input/`.
3. Use the ingest API (e.g. `POST /api/v1/ingest`) or CLI/indexing scripts (if available) to build the index.

Step 5 – Run the frontend:

```bash
cd ../frontend
npm install
npm run dev
```

By default, the frontend expects the backend at `http://localhost:8000`. If you change the backend port, update the corresponding environment variable in the frontend config (`VITE_API_URL` or equivalent).

After these steps, you can:

- Upload documents,
- Trigger ingest/index,
- Ask questions and view answers with citations directly in the web UI.


## 7. References (EN)

> Tip: Keep this at the end so beginners can explore later.



- FastAPI: `https://fastapi.tiangolo.com/`
- Vite: `https://vitejs.dev/guide/`
- Tailwind CSS: `https://tailwindcss.com/docs`
- Ollama: `https://ollama.com/`
- LangChain: `https://python.langchain.com/`
