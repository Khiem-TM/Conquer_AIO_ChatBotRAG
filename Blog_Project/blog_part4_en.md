## Part 4 – RAG Core Owner: Context Assembly, Prompting, and Citation Answers

If you view the RAG pipeline as a production line:

- Person 1 handles ingesting and normalizing documents,
- Person 2 handles embedding + indexing,
- Person 3 handles retrieval (finding the right chunks),
- **Person 4 (RAG Core)** is the final editor: assembling context, designing prompts for the LLM, calling the model, and returning answers with clear **citations**.

---

### 1. The role of RAG Core in the overall architecture

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

### 2. Context assembly: preparing what the LLM sees

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

### 3. Prompt design: talking to the LLM to reduce hallucination

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

### 4. LLM generation and timeout/fallback behavior

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

### 5. Citation building: letting users verify the answer

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

### 6. API contract with the frontend: how lane 4 talks to the UI

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

### 7. Beyond prompt design: other ways RAG Core reduces hallucination

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

### 8. Beginner‑friendly recap of Person 4’s lane

You can summarize the RAG Core lane with four keywords:

1. **Context** – receive ranked chunks from Retrieval and assemble them into a context block.
2. **Prompt** – craft a clear prompt that forces the model to rely on context.
3. **LLM** – call the model with timeout and safe fallback handling.
4. **Citation** – return structured evidence so users can verify the answer.

Once you understand Person 4’s responsibilities, you will see that a RAG pipeline is more than “just calling an LLM with documents” – it is a carefully designed flow that goes **from context → prompt → grounded answer**.

