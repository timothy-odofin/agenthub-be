# RAG Pipeline: Retrieval-Augmented Generation

> **Beginner-Friendly Guide**: Learn how to give LLMs access to your own data using RAG (Retrieval-Augmented Generation)

## Table of Contents
- [What is RAG?](#what-is-rag)
- [Why RAG Matters](#why-rag-matters)
- [How RAG Works](#how-rag-works)
- [Key Components](#key-components)
- [The RAG Pipeline](#the-rag-pipeline)
- [AgentHub Implementation](#agenthub-implementation)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

---

## What is RAG?

**RAG (Retrieval-Augmented Generation)** = A technique that allows LLMs to access and use external knowledge.

### The Problem RAG Solves

```python
# Without RAG 
User: "What was our Q3 revenue?"
LLM: "I don't have access to your company's financial data."

# With RAG 
User: "What was our Q3 revenue?"
RAG: [Searches your documents] → [Finds Q3 report] → [Sends to LLM]
LLM: "According to your Q3 report, revenue was $2.3M..."
```

### Simple Analogy

**RAG is like giving an LLM a library card:**

```
Without RAG:
┌──────────────┐
│ LLM │ "I only know what I was trained on"
│ (Memory) │ (Training data from 2023 or earlier)
└──────────────┘

With RAG:
┌──────────────┐ ┌──────────────────────┐
│ LLM │ ←── │ Your Documents │
│ (Memory) │ │ - PDFs, docs, wikis │
│ │ │ - Real-time data │
│ │ │ - Private info │
└──────────────┘ └──────────────────────┘
```

---

## Why RAG Matters

### Use Cases

1. **Company Knowledge Base**
```
Question: "What is our vacation policy?"
RAG finds: Company handbook (page 42)
Answer: "According to the handbook, employees receive 20 days..."
```

2. **Customer Support**
```
Question: "How do I reset my password?"
RAG finds: Help center article #147
Answer: "To reset your password: 1) Click 'Forgot Password'..."
```

3. **Research & Analysis**
```
Question: "What did the 2024 climate report say about emissions?"
RAG finds: Scientific paper (section 3.2)
Answer: "The report indicates emissions decreased by 12%..."
```

4. **Code Documentation**
```
Question: "How do I use the authentication API?"
RAG finds: API docs + code examples
Answer: "Here's how to authenticate: [code example]"
```

### Benefits

| Benefit | Description |
|---------|-------------|
| **Accurate** | LLM uses your actual data, not guesses |
| ** Current** | Access to real-time/recent information |
| **Private** | Works with confidential data |
| **Cost-effective** | No need to retrain entire model |
| **Updatable** | Add new docs anytime |

---

## How RAG Works

### The 3-Step Process

```
1. RETRIEVE → 2. AUGMENT → 3. GENERATE

Find relevant Add context LLM creates
documents to query answer
```

### Detailed Flow

```
User Question: "What is our return policy?"
↓
┌─────────────────────────────────────────────┐
│ Step 1: RETRIEVE │
├─────────────────────────────────────────────┤
│ • Convert question to embedding │
│ • Search vector database │
│ • Find most similar documents │
│ │
│ Found: "Return Policy.pdf" (page 2) │
└─────────────────────────────────────────────┘
↓
┌─────────────────────────────────────────────┐
│ Step 2: AUGMENT │
├─────────────────────────────────────────────┤
│ • Take retrieved content │
│ • Combine with original question │
│ • Create enhanced prompt │
│ │
│ Prompt: "Based on this policy document: │
│ [content]... answer: What is our return │
│ policy?" │
└─────────────────────────────────────────────┘
↓
┌─────────────────────────────────────────────┐
│ Step 3: GENERATE │
├─────────────────────────────────────────────┤
│ • LLM reads the retrieved content │
│ • Generates answer using that context │
│ • Returns response to user │
│ │
│ Answer: "Our return policy allows returns │
│ within 30 days of purchase..." │
└─────────────────────────────────────────────┘
```

---

## Key Components

### 1. Document Chunking

**Problem**: Documents are too large to fit in LLM context window

**Solution**: Break documents into smaller, manageable pieces (chunks)

```python
# Large document (10,000 words)
document = "The company was founded in 1995... [9,950 more words]"

# Chunked into smaller pieces
chunks = [
"The company was founded in 1995...", # Chunk 1 (500 words)
"Our mission is to innovate...", # Chunk 2 (500 words)
"Products include software...", # Chunk 3 (500 words)
# ... 17 more chunks
]
```

**Chunk Size Guidelines:**

| Chunk Size | Best For | Trade-offs |
|------------|----------|------------|
| **Small (200-500 tokens)** | Precise retrieval | May lose context |
| **Medium (500-1000 tokens)** | Balanced | Recommended |
| **Large (1000-2000 tokens)** | Preserving context | Less precise |

**AgentHub Example:**
```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
chunk_size=1000, # 1000 characters per chunk
chunk_overlap=200, # 200 characters overlap
separators=["\n\n", "\n", " ", ""]
)

chunks = splitter.split_text(document)
```

### 2. Embeddings

**Embeddings** = Converting text into numerical vectors that capture meaning

```python
# Text
"The cat sat on the mat"

# Embedding (simplified - actual embeddings are 1536+ dimensions)
[0.23, 0.67, -0.12, 0.89, ...] # 1536 numbers

# Similar text has similar embeddings
"A feline rested on the rug"
[0.25, 0.64, -0.10, 0.91, ...] # Close to above!
```

**Why Embeddings Matter:**

```
Traditional Search (Keywords):
Query: "How to reset password"
Finds: Documents with exact words "reset" and "password"
Misses: "Change your login credentials" 

Semantic Search (Embeddings):
Query: "How to reset password"
Finds: All documents about password/login/credentials 
```

**AgentHub Embedding Providers:**
```python
# From: src/app/core/constants.py
class EmbeddingType(str, Enum):
OPENAI = "openai" # text-embedding-ada-002 (1536 dims)
HUGGINGFACE = "huggingface" # Various models
COHERE = "cohere" # Multilingual support
VERTEX = "vertex" # Google Cloud
```

**Creating Embeddings:**
```python
from app.db.vector.embeddings.embedding import EmbeddingFactory
from app.core.constants import EmbeddingType

# Get embedding model
embedding_model = EmbeddingFactory.get_embedding_model(
EmbeddingType.OPENAI
)

# Embed text
vector = embedding_model.embed_query("What is machine learning?")
# Result: [0.023, -0.012, ..., 0.045] # 1536 numbers
```

### 3. Vector Database

**Vector Database** = Storage system optimized for similarity search on embeddings

```python
# Traditional Database (SQL)
SELECT * FROM docs WHERE title = 'Machine Learning'
# Exact match only

# Vector Database
SEARCH_SIMILAR(query_embedding, top_k=5)
# Finds 5 most similar documents by meaning!
```

**How Vector Search Works:**

```
1. Store documents with embeddings:
┌────────────────────────────────────────┐
│ Document | Embedding │
├────────────────────────────────────────┤
│ "ML is AI subset" | [0.2, 0.8, ...] │
│ "DL uses neural" | [0.3, 0.7, ...] │
│ "Python language" | [0.9, 0.1, ...] │
└────────────────────────────────────────┘

2. Query with embedding:
Query: "What is machine learning?"
Embedding: [0.21, 0.79, ...]

3. Find closest matches (by vector distance):
"ML is AI subset" (distance: 0.05) ← Very close!
"DL uses neural" (distance: 0.12) ← Close
"Python language" (distance: 0.85) ← Far
```

**AgentHub Vector DB:**
```python
# From: src/app/db/vector/pgvector.py
@VectorDBRegistry.register(VectorDBType.PGVECTOR)
class PgVectorDB(VectorDB):
"""PostgreSQL with pgvector extension for similarity search."""

async def save_and_embed(
self, 
embedding_type: EmbeddingType, 
docs: List[Document]
) -> List[str]:
"""Store documents with their embeddings."""
# Generates embeddings and stores them

async def similarity_search(
self,
query: str,
k: int = 4,
embedding_type: EmbeddingType = EmbeddingType.OPENAI
) -> List[Document]:
"""Find k most similar documents to query."""
# Returns relevant documents
```

**Distance Metrics:**

| Metric | Formula | Best For |
|--------|---------|----------|
| **Cosine** | Angle between vectors | Text, general use |
| **Euclidean** | Straight-line distance | Spatial data |
| **Inner Product** | Dot product | When vectors are normalized |

### 4. Retrieval

**Retrieval** = Finding the most relevant documents for a query

```python
# User query
query = "How do I deploy to production?"

# Retrieval process
1. Convert query to embedding
2. Search vector database
3. Return top K most similar chunks

# Results (K=3)
results = [
"To deploy to production, run: docker-compose up...", # Score: 0.92
"Production environment requires environment vars...", # Score: 0.87
"Before deploying, ensure tests pass...", # Score: 0.81
]
```

**Retrieval Strategies:**

| Strategy | Description | Use Case |
|----------|-------------|----------|
| **Similarity Search** | Find most similar docs | General RAG |
| **MMR** (Max Marginal Relevance) | Similar but diverse results | Avoid redundancy |
| **Hybrid Search** | Combine keyword + semantic | Best accuracy |
| **Metadata Filtering** | Filter by properties | Narrow search |

**AgentHub Retrieval:**
```python
# Basic similarity search
from app.db.vector.pgvector import PgVectorDB

vector_db = PgVectorDB()
results = await vector_db.similarity_search(
query="What is the return policy?",
k=4, # Return top 4 most relevant chunks
embedding_type=EmbeddingType.OPENAI
)

# Results contain relevant document chunks
for doc in results:
print(f"Content: {doc.page_content}")
print(f"Metadata: {doc.metadata}")
```

---

## The RAG Pipeline

### Full Pipeline Visualization

```
┌─────────────────────────────────────────────────────────────┐
│ INGESTION PHASE │
│ (Done Once/Periodically) │
└─────────────────────────────────────────────────────────────┘
│
↓
┌────────────┐ ┌─────────────┐ ┌──────────────┐
│ Raw Docs │ → │ Chunk │ → │ Embed & │
│ │ │ Documents │ │ Store │
│ - PDFs │ │ │ │ │
│ - Docs │ │ 1. Split │ │ 1. Generate │
│ - HTML │ │ text │ │ vectors │
│ - Code │ │ 2. Preserve │ │ 2. Save to │
└────────────┘ │ context │ │ vector DB │
└─────────────┘ └──────────────┘

┌─────────────────────────────────────────────────────────────┐
│ QUERY PHASE │
│ (Every User Query) │
└─────────────────────────────────────────────────────────────┘
│
↓
┌────────────┐ ┌─────────────┐ ┌──────────────┐
│User Query │ → │ Embed │ → │ Search │
│ │ │ Query │ │ Vector DB │
│"What is │ │ │ │ │
│the return │ │ Convert to │ │ Find top K │
│policy?" │ │ vector │ │ similar docs │
└────────────┘ └─────────────┘ └──────────────┘
│
↓
┌────────────┐ ┌─────────────┐ ┌──────────────┐
│ Return │ ← │ Generate │ ← │ Augment │
│ Answer │ │ Response │ │ Prompt │
│ │ │ │ │ │
│"Our return │ │ LLM creates │ │ Add context │
│policy..." │ │ answer │ │ to query │
└────────────┘ └─────────────┘ └──────────────┘
```

### Phase 1: Ingestion (Indexing)

**Happens once when adding new documents**

```python
# 1. Load documents
from langchain.document_loaders import PyPDFLoader

loader = PyPDFLoader("company_handbook.pdf")
documents = loader.load()

# 2. Split into chunks
from langchain.text_splitter import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
chunk_size=1000,
chunk_overlap=200
)
chunks = splitter.split_documents(documents)

# 3. Create embeddings and store
from app.db.vector.pgvector import PgVectorDB
from app.core.constants import EmbeddingType

vector_db = PgVectorDB()
await vector_db.save_and_embed(
embedding_type=EmbeddingType.OPENAI,
docs=chunks
)
```

### Phase 2: Query (Retrieval + Generation)

**Happens every time a user asks a question**

```python
# 1. User asks question
user_query = "What is the vacation policy?"

# 2. Retrieve relevant documents
results = await vector_db.similarity_search(
query=user_query,
k=3, # Top 3 most relevant chunks
embedding_type=EmbeddingType.OPENAI
)

# 3. Build context from results
context = "\n\n".join([doc.page_content for doc in results])

# 4. Create augmented prompt
prompt = f"""Based on the following context, answer the question.

Context:
{context}

Question: {user_query}

Answer:"""

# 5. Generate response using LLM
from app.llm.factory.llm_factory import LLMFactory

llm = LLMFactory.get_default_llm()
response = await llm.generate(
messages=[prompt],
temperature=0.3
)

print(response.content)
# Output: "According to the company handbook, employees receive 20 days..."
```

---

## AgentHub Implementation

### Complete RAG Example

```python
"""
Complete RAG implementation using AgentHub components.
"""

from app.db.vector.pgvector import PgVectorDB
from app.llm.factory.llm_factory import LLMFactory
from app.core.constants import EmbeddingType, LLMProvider
from langchain.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from app.core.utils.logger import get_logger

logger = get_logger(__name__)


class RAGSystem:
"""Simple RAG system using AgentHub."""

def __init__(self):
self.vector_db = PgVectorDB()
self.llm = LLMFactory.get_llm(LLMProvider.OPENAI)
self.embedding_type = EmbeddingType.OPENAI

async def ingest_documents(self, file_paths: list[str]):
"""
Ingest documents into the RAG system.

Args:
file_paths: List of file paths to ingest
"""
all_chunks = []

for file_path in file_paths:
# Load document
loader = TextLoader(file_path)
documents = loader.load()

# Split into chunks
splitter = RecursiveCharacterTextSplitter(
chunk_size=1000,
chunk_overlap=200,
separators=["\n\n", "\n", " ", ""]
)
chunks = splitter.split_documents(documents)
all_chunks.extend(chunks)

# Store in vector database
doc_ids = await self.vector_db.save_and_embed(
embedding_type=self.embedding_type,
docs=all_chunks
)

logger.info(f"Ingested {len(all_chunks)} chunks from {len(file_paths)} files")
return doc_ids

async def query(self, question: str, k: int = 3) -> str:
"""
Query the RAG system.

Args:
question: User's question
k: Number of relevant chunks to retrieve

Returns:
Generated answer
"""
# 1. Retrieve relevant documents
relevant_docs = await self.vector_db.similarity_search(
query=question,
k=k,
embedding_type=self.embedding_type
)

# 2. Build context
context = "\n\n".join([
f"[Source {i+1}]:\n{doc.page_content}"
for i, doc in enumerate(relevant_docs)
])

# 3. Create prompt
prompt = f"""You are a helpful assistant. Answer the question based only on the provided context.
If the answer is not in the context, say "I don't have enough information to answer that."

Context:
{context}

Question: {question}

Answer:"""

# 4. Generate response
response = await self.llm.generate(
messages=[prompt],
temperature=0.3,
max_tokens=500
)

# 5. Log usage
logger.info(f"Query used {response.usage['total_tokens']} tokens")

return response.content


# Usage example
async def main():
# Initialize RAG system
rag = RAGSystem()

# Ingest documents
await rag.ingest_documents([
"docs/company_handbook.txt",
"docs/policies.txt",
"docs/faq.txt"
])

# Query the system
answer = await rag.query("What is the vacation policy?")
print(answer)
# Output: "According to the company handbook, employees receive..."


if __name__ == "__main__":
import asyncio
asyncio.run(main())
```

### Advanced: RAG with Metadata Filtering

```python
async def query_with_filter(
self, 
question: str, 
document_type: str = None,
date_range: tuple = None
) -> str:
"""Query with metadata filtering."""

# Build filter
filters = {}
if document_type:
filters["type"] = document_type
if date_range:
filters["date"] = {"$gte": date_range[0], "$lte": date_range[1]}

# Retrieve with filters
relevant_docs = await self.vector_db.similarity_search(
query=question,
k=3,
filters=filters # Only search specific documents
)

# ... rest of RAG pipeline
```

---

## Best Practices

### 1. Chunk Size Selection

```python
# Too small (loses context)
chunk_size = 100

# Too large (loses precision)
chunk_size = 5000

# Balanced
chunk_size = 1000
chunk_overlap = 200 # Preserve context at boundaries
```

### 2. Overlap Between Chunks

```python
# Without overlap 
"...end of sentence." | "Start of new..."
↑ Context lost!

# With overlap 
"...end of sentence. Start of new..."
"end of sentence. Start of new concept..."
↑ Context preserved!
```

### 3. Retrieve Enough Context

```python
# Too few results (might miss relevant info)
k = 1

# Balanced (usually sufficient)
k = 3-5

# Too many (noise, higher cost)
k = 20
```

### 4. Use Appropriate Temperature

```python
# RAG responses should be based on facts
response = await llm.generate(
messages=[augmented_prompt],
temperature=0.1-0.3 # Low temperature for factual accuracy
)
```

### 5. Validate Source Content

```python
# Always check if relevant docs were found
relevant_docs = await vector_db.similarity_search(query, k=3)

if not relevant_docs:
return "I don't have any information about that topic."

# Check similarity scores if available
if relevant_docs[0].metadata.get("score", 1.0) < 0.5:
return "I found some related information, but I'm not confident it fully answers your question."
```

### 6. Include Source Citations

```python
# Build response with sources
context = ""
for i, doc in enumerate(relevant_docs):
context += f"\n[Source {i+1}]: {doc.page_content}"
context += f"\n(From: {doc.metadata.get('source', 'Unknown')})\n"

# LLM can now reference sources
prompt = f"""Answer the question and cite your sources using [Source N] notation.

{context}

Question: {question}"""

# Response will include: "According to [Source 1], the policy states..."
```

### 7. Monitor and Log

```python
# Track RAG performance
logger.info(f"Query: {question}")
logger.info(f"Retrieved docs: {len(relevant_docs)}")
logger.info(f"Tokens used: {response.usage['total_tokens']}")
logger.info(f"Response time: {elapsed_time}ms")
```

---

## Troubleshooting

### Issue 1: Irrelevant Results

**Problem**: RAG returns off-topic documents

**Solutions**:
```python
# 1. Improve chunk quality
splitter = RecursiveCharacterTextSplitter(
chunk_size=1000,
chunk_overlap=200,
separators=["\n\n", "\n", ".", " "] # Better boundaries
)

# 2. Use metadata filtering
results = await vector_db.similarity_search(
query=question,
filters={"category": "HR_policies"} # Narrow scope
)

# 3. Increase similarity threshold
if doc.metadata.get("score") < 0.7:
continue # Skip low-relevance results
```

### Issue 2: Incomplete Answers

**Problem**: LLM doesn't use all retrieved context

**Solutions**:
```python
# 1. Retrieve more documents
k = 5 # Instead of 3

# 2. Explicitly instruct LLM
prompt = f"""IMPORTANT: Read ALL the context carefully before answering.
Use information from multiple sources if needed.

Context:
{context}

Question: {question}"""

# 3. Use larger context window model
llm = LLMFactory.get_llm(LLMProvider.ANTHROPIC) # Claude has 100K context
```

### Issue 3: High Costs

**Problem**: RAG is expensive to run

**Solutions**:
```python
# 1. Limit retrieved documents
k = 2 # Fewer docs = less context = lower cost

# 2. Use cheaper embedding model
embedding_type = EmbeddingType.HUGGINGFACE # Free/cheaper

# 3. Use cheaper LLM for RAG
llm = LLMFactory.get_llm(LLMProvider.GROQ) # Fast and cheap

# 4. Cache frequent queries
cache = {}
if question in cache:
return cache[question]
```

### Issue 4: Slow Response Time

**Problem**: RAG takes too long to respond

**Solutions**:
```python
# 1. Use faster embedding model
embedding_type = EmbeddingType.OPENAI # text-embedding-ada-002 is fast

# 2. Use faster LLM
llm = LLMFactory.get_llm(LLMProvider.GROQ) # Ultra-fast inference

# 3. Optimize vector search
# - Use appropriate distance metric (cosine is fast)
# - Index your vector database
# - Use approximate nearest neighbor (ANN) algorithms

# 4. Stream responses
async for chunk in llm.stream(prompt):
yield chunk # Start showing results immediately
```

### Issue 5: Outdated Information

**Problem**: RAG uses old documents

**Solutions**:
```python
# 1. Regularly re-ingest documents
import schedule

async def refresh_documents():
await rag.ingest_documents(file_paths)

schedule.every().day.at("02:00").do(refresh_documents)

# 2. Use timestamp metadata
await vector_db.save_and_embed(
docs=chunks,
metadata={"last_updated": datetime.now().isoformat()}
)

# 3. Filter by recency
results = await vector_db.similarity_search(
query=question,
filters={"last_updated": {"$gte": "2024-01-01"}}
)
```

---

## Performance Optimization

### Embedding Caching

```python
# Cache embeddings for repeated queries
embedding_cache = {}

def get_cached_embedding(text: str):
if text not in embedding_cache:
embedding_cache[text] = embedding_model.embed_query(text)
return embedding_cache[text]
```

### Batch Processing

```python
# Ingest multiple documents efficiently
async def batch_ingest(file_paths: list[str], batch_size: int = 10):
for i in range(0, len(file_paths), batch_size):
batch = file_paths[i:i+batch_size]
await rag.ingest_documents(batch)
```

### Async Operations

```python
# Parallel retrieval from multiple sources
import asyncio

results = await asyncio.gather(
vector_db1.similarity_search(query, k=2),
vector_db2.similarity_search(query, k=2),
vector_db3.similarity_search(query, k=2)
)
all_docs = [doc for result in results for doc in result]
```

---

## Next Steps

Now that you understand RAG, explore:

1. **[LLM Basics](./llm-basics.md)** - Understand the generation component
2. **[Vector Database Guide](../guides/vector-databases.md)** - Deep dive into vector search
3. **[Build a RAG Chatbot Tutorial](../tutorials/rag-chatbot.md)** - Hands-on implementation

---

## Quick Reference

### RAG Checklist

- [ ] Documents chunked appropriately (1000 tokens, 200 overlap)
- [ ] Embeddings generated and stored in vector DB
- [ ] Similarity search retrieves relevant docs (k=3-5)
- [ ] Context is augmented into prompt clearly
- [ ] LLM temperature is low (0.1-0.3) for factual accuracy
- [ ] Source citations included in responses
- [ ] Edge cases handled (no results, low confidence)
- [ ] Performance monitored (tokens, latency)

### AgentHub RAG Components

| Component | Location | Purpose |
|-----------|----------|---------|
| **Vector DB** | `src/app/db/vector/pgvector.py` | Store & search embeddings |
| **Embeddings** | `src/app/db/vector/embeddings/` | Convert text to vectors |
| **LLM Factory** | `src/app/llm/factory/llm_factory.py` | Get LLM instances |
| **Document Loaders** | LangChain | Load various file types |
| **Text Splitter** | LangChain | Chunk documents |

---

## Glossary

| Term | Definition |
|------|------------|
| **Chunk** | Small piece of a larger document |
| **Embedding** | Numerical vector representation of text |
| **Vector Database** | DB optimized for similarity search |
| **Similarity Search** | Find documents by semantic similarity |
| **Context Window** | Maximum text LLM can process at once |
| **Retrieval** | Finding relevant documents for a query |
| **Augmentation** | Adding retrieved context to prompt |
| **Generation** | LLM creating response based on context |

---

**Additional Resources:**
- [LangChain RAG Tutorial](https://python.langchain.com/docs/use_cases/question_answering/)
- [Pinecone RAG Guide](https://www.pinecone.io/learn/retrieval-augmented-generation/)
- [OpenAI Embeddings Guide](https://platform.openai.com/docs/guides/embeddings)

**Need Help?**
- See [RAG Tutorial](../tutorials/rag-chatbot.md)
- Check [Architecture Docs](../architecture/overview.md) for more implementations
- Ask in [Discussions](https://github.com/timothy-odofin/agenthub-be/discussions)
