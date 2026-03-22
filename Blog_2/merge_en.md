# Retrieval: The Universal Key in the Age of AI

---

## Introduction

The explosion of Large Language Models (**LLMs**) has marked a new era in human-machine interaction. However, during real-world implementation, developers and researchers face two major hurdles: **knowledge cutoff** (the obsolescence of training data) and **hallucination**.

To significantly reduce these issues, the concept of **Retrieval** has become an indispensable component in many modern AI systems, serving as an "anchor" that helps keep systems grounded in reality and improve accuracy. This article is a synthesis from five professional perspectives, ranging from theoretical foundations to system architecture, with the goal of providing a comprehensive view of retrieval infrastructure in the AI era.

---

## Part 1: The Essence of Retrieval in the AI Ecosystem

In traditional computer science, **Retrieval** is often understood simply as querying a structured dataset to find exact matches. However, in the context of modern Artificial Intelligence, this concept has evolved into a more complex process: **Searching for content based on semantic and contextual correlation.**

### 1.1. From "Rote Memorization" to "Selective Research"

Traditional AI models operate based on knowledge compressed within weights during the training process. This is analogous to a student attempting to memorize an entire library.

In contrast, an integrated Retrieval system equips AI with the capabilities of a researcher: when a query is received, instead of only searching through finite memory, it accesses a large external repository to find the most relevant documents. This allows the system to reach real-time data and internal documents that the model never encountered during pre-training.

### 1.2. The Role of Retrieval in Mitigating Hallucination

One of the most important applications of Retrieval is providing a **"Source of Truth."** When a language model is supplied with relevant text segments (context) through the retrieval process, its task shifts from *free-form content creation* to *information synthesis and extraction*.

> **Core Principle:** The output quality of an AI system depends strongly on the accuracy and relevance of the data retrieved at the input stage.

It is important to note that Retrieval does not eliminate hallucination entirely. It helps reduce it significantly when the retrieved data is good, the context is sufficiently clear, and the prompt is designed properly.

### 1.3. Basic Structure of a Modern Retrieval System

A standard Retrieval workflow goes beyond simple searching and includes three strategic stages:

1. **Representation:** Transforming natural language queries into formats that computers can understand. In the current era, these are typically mathematical vectors (*embeddings*).
2. **Similarity Scoring:** Using distance or similarity functions to determine how close a query is to documents. Common methods include:
   - **Cosine Similarity:** Measuring the angle between two vectors in a multi-dimensional space.
   - **Euclidean Distance:** Measuring the distance between two vector points.
   - **Dot Product:** Commonly used in many modern embedding systems.
3. **Filtering & Ranking:** Selecting the top $k$ results with the highest correlation scores to be fed into the language model (*generator*).

Understanding this foundation is essential before diving deeper into NLP techniques and vector database architectures in the following sections.

---

## Part 2: From Keywords to Meaning — How AI Changed the Way We Search
*(Perspective of an NLP Engineer)*

Let’s imagine you go to Google and type: **“how to lose weight effectively”**. This is a familiar example, but it helps us understand how search systems have evolved over time.

### Traditional approach: keyword-based search

In the past, search systems worked in a fairly straightforward way: they looked for documents that contained the exact words you typed, such as “lose weight” or “effective”.

- Documents containing these keywords more frequently were usually ranked higher.
- Documents that did not include those exact words, even if relevant, could be ranked lower or ignored.

In other words, the system mostly focused on matching surface words rather than understanding the content itself.

### The limitation of this approach

Consider an article titled **“How to stay fit and burn fat safely.”** Its content is clearly related to losing weight and improving health.

However, because it does not explicitly contain the phrase “lose weight,” a traditional search system might not rank it highly. As a result, users could miss useful information simply because of different wording.

### A new approach: semantic search

Modern systems take a different approach. Instead of only matching keywords, they try to understand the user’s actual intent behind the query.

- When you search for “lose weight,” the system may interpret it more broadly as interest in fat burning, healthy eating, or exercise.
- This allows it to return results that may not share the same words, but are still highly relevant.

The key difference is that the system is no longer just “reading words,” but starting to “understand meaning.”

### A simple way to think about it

One easy way to visualize this is to imagine that each sentence or paragraph is represented based on its meaning.

- Content with similar meanings is placed close together.
- Content with different topics is placed further apart.

For example, phrases like **“lose weight”**, **“burn fat”**, and **“eat clean”** all relate to a similar concept, so they are considered close to each other even though the wording is different.

### A quick comparison

| Approach | Main idea | When it works best |
|---------|----------|------------------|
| Keyword-based | Matches exact words | When searching for specific terms like product names or code |
| Semantic search | Understands meaning | When asking questions or exploring general knowledge |

Each approach has its own strengths and limitations. Semantic search is not always better than lexical search; for queries that require exact matching, such as product codes, system errors, proper nouns, or code snippets, keyword-based search often remains highly effective.

### What happens in practice today

In modern systems, people usually do not rely on only one approach. Instead, they combine both methods.

- Keyword matching helps ensure precision at the surface level.
- Understanding meaning helps improve relevance and flexibility.

This combination allows systems to be both accurate and adaptable in different situations.

### Conclusion

The shift from keyword-based search to meaning-based search is a major step forward. It allows machines not only to process text but also to get closer to understanding what users actually want to find.

This shift also lays the foundation for modern AI systems such as chatbots and virtual assistants, where understanding the question is just as important as generating the answer.

---

## Part 3: The Data "Preprocessing" Pipeline
*(From a Data Architect's Perspective)*

If Retrieval is the “search engine,” then data is the “input ingredient.” And just like in cooking, if ingredients are not prepared properly, even a strong system will struggle to produce the best result.

An effective Retrieval system does not start with the model. It starts with how you **prepare the data**. This process usually revolves around three core steps: **Chunking → Embedding → Indexing**.

### 3.1. Chunking – Splitting While Preserving Meaning

AI models do not “read” text the way humans do. If you feed the system a document that is dozens of pages long, two issues often appear:

- **Context overflow**
- **Dilution of important information**

So the first step is to **split documents into chunks**.

**Common chunking methods:**

1. **Fixed-size chunking**

<p align="center"><img src="phan3_HoangAnh/img3.1.png" width="700"></p>

Split text by a fixed size (characters/words/tokens), often with `overlap` to reduce abrupt context breaks.  
Pros: Easy to implement and good for batch processing.  
Cons: Important sentences or ideas can be split in half.

2. **Semantic chunking**

<p align="center"><img src="phan3_HoangAnh/img3.2.png" width="700"></p>

Split by semantic units (sentences/paragraphs), then use embeddings + similarity to merge related parts.  
Pros: Chunks are more coherent, improving retrieval accuracy.  
Cons: Depends on choosing a good similarity threshold and requires more compute.

3. **Recursive chunking**

<p align="center"><img src="phan3_HoangAnh/img3.3.png" width="700"></p>

Split by natural boundaries first (`\n\n`, `\n`, spaces); if still too long, keep splitting recursively.  
Pros: Balances semantic integrity with size limits.  
Cons: More complex to implement than fixed-size chunking.

4. **Document structure-based chunking**

<p align="center"><img src="phan3_HoangAnh/img3.4.png" width="700"></p>

Use document structure (headings, sections, lists, tables, paragraphs) as chunk boundaries.  
Pros: Preserves the original logical structure well.  
Cons: Depends on well-structured documents; chunk sizes may be uneven.

5. **LLM-based chunking**

<p align="center"><img src="phan3_HoangAnh/img3.5.png" width="700"></p>

Use an LLM to determine chunk boundaries by topic or complete semantic units.  
Pros: Has very strong potential semantic quality.  
Cons: More expensive, slower, and dependent on prompt quality and context window.

**Key insight:** There is no absolute “best” method. In practice, strong systems often use **hybrid chunking** to balance quality, speed, and cost.

### 3.2. Embedding – Turning Language into Coordinates

After creating chunks, the next step is converting them into a format machines can “understand” and compare: **vector embeddings**.

An embedding model (such as `text-embedding-3`) transforms each text chunk into a vector in a high-dimensional space.

This allows the system to:

- Measure **semantic similarity**
- Retrieve text with similar meaning even when keywords do not exactly match

**Practical example (Embedding):**

Assume the system has 3 chunks:

- `C1`: “How to cook pho bo at home”
- `C2`: “Guide to making traditional pho”
- `C3`: “Motorbike maintenance tips for rainy season”

With the query: “How can I cook delicious pho bo?”

- `sim(query, C1) = 0.91`
- `sim(query, C2) = 0.88`
- `sim(query, C3) = 0.15`

Result: the system prioritizes `C1` and `C2` because they are semantically closer, even though the wording is not identical.

<p align="center"><img src="phan3_HoangAnh/img3.6.png" width="700"></p>

**Key insight:** Embedding is the bridge between **human language** and the **mathematics of machine learning**.

### 3.3. Indexing – Organizing for Millisecond Search

Once you have vectors, you need a place to store and retrieve them quickly. That is where a **Vector Database** comes in.

Popular options include:

- Pinecone
- Milvus
- Weaviate

Unlike traditional databases (SQL), vector databases are optimized for:

- **Approximate Nearest Neighbor (ANN) search**
- Handling millions to billions of vectors with low latency

**The indexing process includes:**

- Storing vectors + metadata (source, title, timestamp, etc.)
- Building index structures to speed up search
- Optimizing similarity queries (cosine similarity, dot product, etc.)

**Practical example (Indexing + Retrieval):**

Assume you have indexed 1 million chunks of internal documents. When a user asks, **“How does the 30-day refund policy work?”**

1. The question is embedded into `q_vector`
2. The vector DB uses an ANN index to find the nearest `top-k` vectors in milliseconds
3. It returns the most relevant chunks, for example:
   - `chunk_2451` (score `0.93`) - refund policy section
   - `chunk_8712` (score `0.89`) - eligibility conditions
   - `chunk_1022` (score `0.84`) - exception cases

These chunks are then passed into the LLM context to generate the final answer.

<p align="center"><img src="phan3_HoangAnh/img3.7.png" width="700"></p>

When users ask a question:

1. The question is embedded into a vector
2. The system finds nearest vectors in the database
3. The system returns the most relevant chunks

## Good Retrieval Starts with Good Data

These three steps form the foundation of the entire Retrieval pipeline:

- **Chunking** → Determines *how AI “sees” data*
- **Embedding** → Determines *how AI “understands” data*
- **Indexing** → Determines *how fast AI can find data*

If you do this well, you have already determined a large part of the retrieval quality of a later RAG system.

A memorable quote in the Data Architect world:

> “Garbage in, garbage out — and for Retrieval: *bad chunks lead to bad search; weak embeddings lead to wrong understanding.*”

---

## Part 4: RAG — The Practical Peak of Retrieval
*(From an AI Developer’s Perspective)*

If Part 2 explained **how search evolved**, and Part 3 explained **how data is prepared**, then Part 4 is where everything comes together in real products:

**RAG (Retrieval-Augmented Generation)**.

RAG is not a brand-new model. It is an architecture that combines:

- A **Retriever** (to fetch relevant knowledge)
- A **Generator** (LLM) (to produce the final answer)

Instead of forcing the LLM to answer only from memory, we let it read the right documents at the right time.

---

### 4.1. Why RAG matters in real products

A pure LLM setup often faces 3 issues:

1. **Hallucination:** answers sound fluent but can be wrong.
2. **Knowledge cutoff:** the model may not know new or internal data.
3. **No traceability:** it is hard to show which documents support an answer.

RAG helps address these issues in the following ways:

- Grounds answers in retrieved documents.
- Keeps knowledge up to date by updating the data store, without retraining the model.
- Enables source citation to improve trust.

### 4.2. Core RAG flow (end-to-end)

```text
User Question
   ↓
Embed query
   ↓
Vector DB retrieval (top-k chunks)
   ↓
(Optional) Rerank retrieved chunks
   ↓
Build final prompt with context
   ↓
LLM generates answer + citations
```

In implementation terms, RAG usually has 4 modules:

- `ingestion`: chunk + embed + index documents.
- `retrieval`: fetch relevant chunks for each query.
- `prompting`: compose instructions + context + question.
- `generation`: call the LLM and format the response.

### 4.3. A minimal implementation blueprint

#### Step A — Retrieve context

- Convert user query to embedding.
- Search the vector database (`top_k = 5` or `10`).
- Filter by metadata (product, language, date).

#### Step B — Compose prompt safely

- Add a clear system rule: “Answer only using provided context.”
- Put retrieved chunks into a `CONTEXT` block.
- Include fallback behavior: “If context is insufficient, say so.”

#### Step C — Generate + cite

- Ask the model to return:
  - a concise answer
  - cited sources (`doc_id`, title, link)

This structure helps reduce “creative but wrong” outputs significantly.

### 4.4. Practical example

**User asks:**

> “How does the 30-day refund policy work for digital products?”

**Retriever returns:**

- `policy_refund_v2.md` (refund conditions)
- `faq_payments.md` (exceptions)
- `terms_service.md` (regional limitations)

**LLM receives a prompt containing these chunks** and returns:

- the policy applies within 30 days if usage criteria are met,
- exceptions for specific plans,
- links to official policy documents.

Without RAG, the model might produce a generic answer. With RAG, the answer stays grounded in real system documents.

### 4.5. Engineering trade-offs you will face

1. **Latency vs quality**
   - More retrieved chunks can improve recall but slow generation.
2. **Chunk size vs context integrity**
   - Too small loses meaning; too large wastes tokens.
3. **Cost vs reliability**
   - Reranking and larger context windows improve quality but increase cost.

A common production setup:

- Hybrid retrieval (BM25 + vector)
- Top 20 recall → rerank to top 5
- Grounded prompt + citation output

### 4.6. How to evaluate a RAG system

Do not evaluate only by “the answer sounds good.” Track:

- **Retrieval Recall@k:** did we fetch truly relevant chunks?
- **Groundedness/Faithfulness:** does the answer match the context?
- **Citation accuracy:** are references correct and useful?
- **Latency (P95)** and **cost per request**

Good RAG is a system problem, not just a model problem.

### Conclusion of Part 4

RAG is the bridge between organizational knowledge and LLM reasoning.

From an AI Developer’s viewpoint, the key lesson is:

> The best answer is not the most fluent one — it is the one that is **correct, grounded, and traceable**.

That is why RAG remains one of the most practical and effective Retrieval applications in modern AI products.

---

## Part 5: Challenges & the Future of Retrieval
*(From the Perspective of a Product Manager)*

### Introduction

The previous four parts have painted a complete picture of Retrieval — from foundational concepts, the evolution of search techniques, and the data processing pipeline, to its most powerful application: RAG. But no technology is perfect.

As a product manager, the question I always ask is not *“How does this technology work?”* but rather *“Where does this technology fail, and what comes next?”*

### Current Challenges

#### 1. Latency — The Silent Enemy of User Experience

A Retrieval system must execute a series of tasks in an instant:

```text
[User query]
      ↓
  Embedding query
      ↓
  Vector similarity search
      ↓
  Fetch & rerank documents
      ↓
  Send context → LLM generate
      ↓
  [Answer]
```

Every step takes time. If total response time exceeds 2–3 seconds, users start losing patience. This is a major technical challenge, especially when the database contains millions of vectors.

Approaches currently being explored or widely deployed include:

- Approximate Nearest Neighbor (ANN) for faster search, accepting a small margin of error.
- Caching results for frequently asked queries.
- Streaming responses so users can see the answer being generated in real time.

#### 2. Noise — "Garbage In, Garbage Out"

Retrieval is only as strong as the data it fetches. In practice, the system may:

- Return passages that *appear relevant* but do not actually answer the question.
- Pull outdated or contradictory information from multiple sources.
- Be “fooled” by terms that overlap semantically but differ in context.

> Real-world example: A user asks about *“a 30-day refund policy”*, but the system retrieves a passage about *“a 30-month warranty policy”* — two entirely different topics.

When an LLM receives incorrect context, it does not “know” that the information is noisy — and may answer incorrectly with a high degree of confidence.

#### 3. Chunking & Context Window Issues

As discussed in Part 3, splitting text into chunks is necessary — but it is also a double-edged sword. Chunks that are too small lose context; chunks that are too large dilute meaning and waste tokens unnecessarily.

There is currently no single “golden formula” that applies to every type of data.

### What Does the Future Look Like?

#### Hybrid Search — Taking the Best of Both Worlds

The AI community is moving toward **Hybrid Search** — a combination of:

| Method | Strengths | Weaknesses |
|---|---|---|
| Lexical Search (BM25) | Precise with specific keywords, product codes, and proper nouns | Does not understand meaning |
| Semantic Search (Vector Search) | Understands intent and context | May miss important keywords |
| Hybrid Search | Leverages both | More complex to implement |

Hybrid Search is not about choosing one or the other. It runs both approaches in parallel, then uses an algorithm like **Reciprocal Rank Fusion (RRF)** to merge the results.

#### Reranking — The Fine Filter at the Final Stage

Even when Retrieval returns 20 passages, not all of them carry equal value. **Reranking** is an additional step that uses a specialized model (such as Cohere Rerank or a Cross-encoder) to:

1. Re-read each pair *(query — passage)*.
2. Score the actual degree of relevance.
3. Re-order the results before passing them to the LLM.

Reranking adds latency, but often improves answer quality significantly — a trade-off that many production AI products are willing to make.

#### Agentic Retrieval — When AI Decides How to Search

A newer trend is giving AI the ability to plan its own retrieval process. Rather than a single search pass, an AI agent can:

- Decompose a complex question into multiple sub-queries.
- Perform multiple rounds of Retrieval, each refined based on previous results.
- Self-evaluate: *“Do I have enough information to answer this?”*

This is the direction of systems such as Deep Research and Agentic RAG, and it is currently considered a highly promising direction for next-generation retrieval systems.

### A Product Perspective

As someone who builds products, I have come to realize that Retrieval is not only a technical problem — it is also an experience design problem:

- When should citations be shown to build user trust?
- How should the system handle cases where no relevant information is found?
- What metrics should be used to measure Retrieval quality in a real product?

> One key insight: users do not care about vectors or embeddings. They care about one thing — is the answer correct, and is it fast?

### Conclusion of Part 5

Retrieval is maturing rapidly. The challenges around latency, noise, and chunking are gradually being addressed through Hybrid Search, Reranking, and Agentic Retrieval.

But the biggest lesson from a product management perspective is this: the best technology is not the most complex one — it is the one that solves the right problem for the user in a reliable and consistent way.

Retrieval is the foundation — and that foundation is becoming stronger over time.

---

## References

- Viblo, *Optimizing RAG: Exploring 5 Effective Chunking Strategies You Should Know*  
  https://viblo.asia/p/toi-uu-hoa-rag-kham-pha-5-chien-luoc-chunking-hieu-qua-ban-can-biet-EvbLbPGW4nk
