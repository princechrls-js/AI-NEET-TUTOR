# 🚀 AI NEET Coaching Backend Documentation

This document serves as a comprehensive study guide for the backend architecture and the technology stack. It breaks down **what** every technology is and exactly **why** we chose it for building this specific AI coaching platform.

---

## 🏗️ Core Application Architecture

### 1. Python 3.11+
* **What it is:** A versatile, high-level programming language.
* **Why we use it:** Python is the undisputed king of Artificial Intelligence and Data Science. It has the most mature ecosystem (LangChain, HuggingFace, PyTorch) for processing text and interacting with LLMs.

### 2. FastAPI
* **What it is:** A modern, high-performance web framework used for building APIs.
* **Why we use it:** 
  * **Speed:** It is one of the fastest Python frameworks available (built on Starlette and Pydantic).
  * **Async Execution:** It natively supports `async`/`await`, which is crucial when your API spends most of its time waiting for the Database or LLM to respond.
  * **Auto-Documentation:** It automatically generates a beautiful interactive dashboard (Swagger UI) at `http://127.0.0.1:8000/docs`, making testing endpoints effortless.

### 3. Uvicorn
* **What it is:** An ASGI (Asynchronous Server Gateway Interface) web server.
* **Why we use it:** FastAPI is just the framework. Uvicorn is the engine that actually runs the code on a specific port and handles the low-level TCP connections concurrently.

---

## 🗄️ Database & Storage

### 4. Supabase (PostgreSQL)
* **What it is:** An open-source Firebase alternative built on top of a standard PostgreSQL database.
* **Why we use it:** We need a robust relational database to store users, chat histories, and PDF documents. PostgreSQL is the industry standard for reliability.

### 5. pgvector
* **What it is:** An extension installed inside PostgreSQL that turns it into a Vector Database.
* **Why we use it:** AI fundamentally understands text as "Embeddings" (lists of floating-point numbers). `pgvector` allows us to store these embeddings and perform "cosine similarity" searches mathematically. Finding the most relevant paragraph from a textbook becomes a single SQL query: `ORDER BY embedding <-> query_embedding`. It prevents us from needing to buy and manage a secondary database like Pinecone.

### 6. Redis
* **What it is:** An open-source, in-memory key-value data store.
* **Why we use it:** It stores data purely in RAM (rendering it extremely fast). We use it for two massive performance upgrades:
  * **Response Caching:** When a student asks the same question twice, we pull the answer from Redis instantly (0.01 seconds) instead of waiting for the LLM to generate it again (saving API costs and time).
  * **Rate Limiting:** We use a "Lua Script Token Bucket" algorithm to track precisely how many times a user hits our API per minute. Memory reads/writes in Redis are atom-fast, which is required for rate limiters.

---

## 🧠 Artificial Intelligence (RAG Pipeline)

*Our backend relies on a sophisticated AI methodology known as **RAG (Retrieval-Augmented Generation)**. RAG prevents the AI from hallucinating by forcing it to read our verified textbooks before answering.*

### 7. LangChain
* **What it is:** A framework for developing applications powered by LLMs.
* **Why we use it:** It provides ready-to-use abstractions. Specifically, we use `RecursiveCharacterTextSplitter` to intelligently slice entire PDF textbooks into overlapping "chunks" (paragraphs) without cutting sentences in half.

### 8. HuggingFace Embeddings (`all-MiniLM-L6-v2`)
* **What it is:** A machine learning model that converts English text into 384-dimensional mathematical vectors.
* **Why we use it:** It operates extremely fast, runs entirely on your local machine, and costs $0. Other APIs (like OpenAI `text-embedding-ada-002`) cost money for every single PDF page uploaded.

### 9. OpenRouter AI
* **What it is:** An aggregator API that provides access to hundreds of different LLMs (GPT-4o, Claude 3, Llama).
* **Why we use it:** It eliminates vendor lock-in. Instead of being stuck with OpenAI, OpenRouter lets us instantly swap to a different, potentially cheaper or smarter AI model by just changing a single string in our `config.py`.

### 10. PyMuPDF (`fitz`)
* **What it is:** A high-performance Python library for parsing PDF documents.
* **Why we use it:** It is orders of magnitude faster and more accurate at extracting raw text and retaining reading order than alternatives like PyPDF2.

---

## 🔒 Security & Authentication

### 11. JSON Web Tokens (JWT) & `python-jose`
* **What it is:** An open standard for securely transmitting information between the server and the frontend as a digitally signed JSON object.
* **Why we use it:** JWTs are **stateless**. Rather than doing a costly database lookup every time a user makes a request to check if they are logged in, the server simply verifies the cryptographic signature on the token. If it's valid, the user is authenticated. 

### 12. Bcrypt (`bcrypt` library)
* **What it is:** A cryptographic password-hashing function.
* **Why we use it:** If the database is ever compromised, hackers cannot read the users' passwords. Bcrypt automatically applies a cryptographic "salt" (random data) to the password and hashes it through multiple iterations, making brute-force guessing computationally impossible.

### 13. Role-Based Access Control (RBAC) via FastAPI Dependencies
* **What it is:** A design pattern to restrict system access to authorized users.
* **Why we use it:** To differentiate between Students (who can only ask questions and take quizzes) and Admins (who can upload PDFs to the AI's brain and manage user data). We easily enforce this by adding `Depends(require_admin)` to specific FastAPI endpoints, halting execution immediately if the requester lacks the correct role.

---

## 📦 Infrastructure

### 14. Docker & Docker Compose
* **What it is:** A platform that packages software into standardized units called "containers."
* **Why we use it:** It guarantees "It works on my machine" translates to "It works *everywhere*." We use `docker-compose.yml` to spin up our Redis server entirely isolated from the host OS, meaning you don't have to manually install Redis on your Windows machine to make the rate-limiting work.

---

## 🌊 Data Flow: How It All Comes Together (The "Ask" flow)

1. The frontend sends an HTTP POST request to `127.0.0.1:8000/ask` with a JWT in the `Authorization` header.
2. **FastAPI** catches the request.
3. The `Depends(rate_limit)` middleware asks **Redis** if this user has asked >5 questions this minute. If yes, it aborts.
4. The `Depends(get_current_user)` function cryptographically verifies the JWT using the `python-jose` library.
5. The request moves to `rag_service.py`. It converts the user's string question into a vector using **HuggingFace Embeddings**.
6. The vector is sent via a SQL query to **Supabase/pgvector**. The database mathematically compares vectors and hands back the top 3 most relevant PDF chunks.
7. An AI prompt is built using the user's question and the retrieved text, and is streamed to the **OpenRouter LLM API**.
8. The final answer is streamed back through **Uvicorn/FastAPI** to the user!
