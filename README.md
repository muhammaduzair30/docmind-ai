---
title: Docmind Ai
emoji: 👁
colorFrom: pink
colorTo: purple
sdk: docker
pinned: false
license: apache-2.0
short_description: DocMind AI is RAG base project
---

# DocMind AI 🧠

DocMind AI is a production-grade **Retrieval-Augmented Generation (RAG)** backend system. It allows users to securely upload documents, semantic-search across them using pgvector, and ask natural language questions answered by Google's Gemini LLM.

## Features ✨

*   **Multi-Tenancy & Security**: JWT-based authentication. Users can only query their own uploaded data.
*   **Hybrid Search**: Uses Reciprocal Rank Fusion (RRF) to combine `pgvector` semantic similarity with PostgreSQL `tsvector` keyword searches.
*   **Semantic Chunking**: Intelligently splits text by paragraphs and sentences rather than crude character counts.
*   **Async Processing**: Uses FastAPI `BackgroundTasks` to keep upload interfaces snappy while processing heavy machine-learning embeddings in the background.
*   **Observability**: Integrated standard python logging and a `/metrics` Prometheus endpoint for monitoring tools.
*   **Rate Limiting**: Protects expensive LLM routes (using `slowapi` targeting 15 req/minute).
*   **Document Management**: Fully featured APIs to list and cascade-delete documents and chunks.
*   **Robust Testing**: Integration tested via `pytest` and automatically vetted in GitHub Actions.

---

## Architecture 🏛️

*   **Web Framework**: FastAPI
*   **Database**: PostgreSQL
*   **Vector Extension**: `pgvector`
*   **ORM**: SQLAlchemy & Alembic (Migrations)
*   **Embedding Model**: SentenceTransformers (`all-MiniLM-L6-v2`)
*   **Generative AI**: Google GenAI (`gemini-2.5-flash`)

---

## Getting Started 🚀

### Option 1: Docker Compose (Easiest)

We provide a bundled Docker environment containing the API and a tuned PostgreSQL + pgvector database.

1.  Clone this repository.
2.  Set up your `.env` file in the root directory:
    ```ini
    DATABASE_URL="postgresql://postgres:password@db:5432/docmind_ai"
    GEMINI_API_KEY="your_gemini_api_key_here"
    SECRET_KEY="a_strong_random_secret_string"
    ALGORITHM="HS256"
    ```
3.  Launch the stack:
    ```bash
    docker-compose up -d --build
    ```
4.  Run database migrations inside the container:
    ```bash
    docker-compose exec api alembic upgrade head
    ```

The API will be available at `http://localhost:8000/docs`.

### Option 2: Local Development

1. Ensure you have Python 3.10+ installed and a PostgreSQL instance running natively with the **pgvector extension installed**.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run Alembic Migrations:
   ```bash
   alembic upgrade head
   ```
4. Start the server:
   ```bash
   uvicorn app.main:app --reload
   ```

---

## API Documentation 📚

FastAPI provisions an interactive Swagger UI. Once the server is running, navigate to `http://localhost:8000/docs`.

### Core Endpoints

*   `POST /api/v1/auth/register` — Create a user account.
*   `POST /api/v1/auth/login` — Get a JWT Bearer token.
*   `POST /api/v1/upload/` — Upload a PDF, DOCX, or TXT file (Background processing).
*   `POST /api/v1/query/` — Ask a question based on your uploaded documents (Rate limited).
*   `GET /api/v1/documents/` — List all documents belonging to the user.
*   `DELETE /api/v1/documents/{id}` — Delete a document and its parsed chunks.
*   `GET /metrics` — Exposes prometheus histograms and request counts.

---

## Running Tests & Linting 🧪

1.  To run the test suite using an in-memory SQLite interceptor:
    ```bash
    pytest tests/ -v
    ```
2.  To run linting:
    ```bash
    flake8 .
    mypy app/
    ```

## CI/CD ⚙️

This project includes a fully formed `.github/workflows/ci.yml` pipeline. It spins up a temporary pgvector docker container, ensuring the integration tests run against a real PostgreSQL environment on every commit to `main`.

Check out the configuration reference at https://huggingface.co/docs/hub/spaces-config-reference
