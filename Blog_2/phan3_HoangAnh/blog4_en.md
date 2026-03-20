# 3. The Data "Preprocessing" Pipeline (From a Data Architect's Perspective)

If Retrieval is the “search engine,” then data is the “input ingredient.” And just like cooking, if ingredients are not prepared well, even the best kitchen setup will not produce a great dish.

An effective Retrieval system does not start with the model. It starts with how you **prepare the data**. This process usually revolves around three core steps: **Chunking → Embedding → Indexing**.

## 3.1. Chunking – Splitting While Preserving Meaning

AI models do not “read” text the way humans do. If you feed the system a document that is dozens of pages long, two issues often appear:

* **Context overflow**
* **Dilution of important information**

So the first step is to **split documents into chunks**.

**Common chunking methods:**

1. **Fixed-size chunking**  

<p align="center"><img src="img3.1.png" width="700"></p>

Split text by a fixed size (characters/words/tokens), often with `overlap` to reduce abrupt context breaks.  
Pros: Easy to implement and good for batch processing.  
Cons: Important sentences or ideas can be split in half.

2. **Semantic chunking**  

<p align="center"><img src="img3.2.png" width="700"></p>

Split by semantic units (sentences/paragraphs), then use embeddings + similarity to merge related parts.  
Pros: Chunks are more coherent, improving retrieval accuracy.  
Cons: Depends on choosing a good similarity threshold and requires more compute.

3. **Recursive chunking**  

<p align="center"><img src="img3.3.png" width="700"></p>

Split by natural boundaries first (`\n\n`, `\n`, spaces); if still too long, keep splitting recursively.  
Pros: Balances semantic integrity with size limits.  
Cons: More complex to implement than fixed-size chunking.

4. **Document structure-based chunking**  


<p align="center"><img src="img3.4.png" width="700"></p>

Use document structure (headings, sections, lists, tables, paragraphs) as chunk boundaries.  
Pros: Preserves the original logical structure well.  
Cons: Depends on well-structured documents; chunk sizes may be uneven.

5. **LLM-based chunking**  

<p align="center"><img src="img3.5.png" width="700"></p>

Use an LLM to determine chunk boundaries by complete topics/semantic meaning.  
Pros: Highest potential semantic quality.  
Cons: More expensive, slower, and dependent on prompt quality and context window.

**Key insight:** There is no absolute “best” method. In practice, strong systems often use **hybrid chunking** to balance quality, speed, and cost.

## 3.2. Embedding – Turning Language into Coordinates

After creating chunks, the next step is converting them into a format machines can “understand” and compare: **vector embeddings**.

An embedding model (such as `text-embedding-3`) transforms each text chunk into a vector in a high-dimensional space.

This allows the system to:

* Measure **semantic similarity**
* Retrieve text with similar meaning even when keywords do not exactly match

**Practical example (Embedding):**

Assume the system has 3 chunks:

* `C1`: “How to cook pho bo at home”
* `C2`: “Guide to making traditional pho”
* `C3`: “Motorbike maintenance tips for rainy season”

With the query: “How can I cook delicious pho bo?”

* `sim(query, C1) = 0.91`
* `sim(query, C2) = 0.88`
* `sim(query, C3) = 0.15`

Result: the system prioritizes `C1` and `C2` because they are semantically closer, even though wording is not identical.


<p align="center"><img src="img3.6.png" width="700"></p>

**Key insight:**
Embedding is the bridge between **human language** and the **mathematics of machine learning**.


## 3.3. Indexing – Organizing for Millisecond Search

Once you have vectors, you need a place to store and retrieve them quickly. That is where a **Vector Database** comes in.

Popular options include:

* Pinecone
* Milvus
* Weaviate

Unlike traditional databases (SQL), vector databases are optimized for:

* **Approximate Nearest Neighbor (ANN) search**
* Handling millions to billions of vectors with low latency

**The indexing process includes:**

* Storing vectors + metadata (source, title, timestamp, etc.)
* Building index structures to speed up search
* Optimizing similarity queries (cosine similarity, dot product, etc.)

**Practical example (Indexing + Retrieval):**

Assume you have indexed 1 million chunks of internal documents. When a user asks, “How does the 30-day refund policy work?”

1. The question is embedded into `q_vector`
2. The vector DB uses an ANN index to find the nearest `top-k` vectors in milliseconds
3. It returns the most relevant chunks, for example:
   * `chunk_2451` (score `0.93`) - refund policy section
   * `chunk_8712` (score `0.89`) - eligibility conditions
   * `chunk_1022` (score `0.84`) - exception cases

These chunks are then passed into the LLM context to generate the final answer.

<p align="center"><img src="img3.7.png" width="700"></p>

When users ask a question:

1. The question is embedded into a vector
2. The system finds nearest vectors in the database
3. The system returns the most relevant chunks


## Good Retrieval Starts with Good Data

These three steps form the foundation of the entire Retrieval pipeline:

* **Chunking** → Determines *how AI “sees” data*
* **Embedding** → Determines *how AI “understands” data*
* **Indexing** → Determines *how fast AI can find data*

If you do this well, you have already solved more than 70% of the quality challenges in a later RAG system.

A memorable quote in the Data Architect world:

> “Garbage in, garbage out — and for Retrieval: *bad chunks lead to bad search; weak embeddings lead to wrong understanding.*”

Reference: https://viblo.asia/p/toi-uu-hoa-rag-kham-pha-5-chien-luoc-chunking-hieu-qua-ban-can-biet-EvbLbPGW4nk