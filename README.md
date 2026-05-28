# RAG Knowledge Base

A robust, full-stack Retrieval-Augmented Generation (RAG) knowledge base built with FastAPI, LangChain, FAISS, and a premium React/Vite frontend.

## 🏗 Architecture Diagram

```mermaid
graph TD
    subgraph Frontend
        React[React/Vite SPA]
        Tailwind[Tailwind CSS]
    end

    subgraph Backend
        FastAPI[FastAPI]
        Auth[JWT Authentication]
        FAISS[(FAISS Vector DB)]
        LLM[LangChain + Gemini]
    end

    User([User]) -->|Upload PDF| React
    User -->|Ask Question| React
    React -->|POST /upload (JWT)| FastAPI
    React -->|POST /ask/stream (JWT)| FastAPI
    
    FastAPI -->|Extract Text & Embed| FAISS
    FastAPI -->|Search Vectors| FAISS
    FastAPI -->|RAG Context & Stream| LLM
```

## 🛠 Tech Stack

- **Frontend**: React 18, Vite, Tailwind CSS, Axios, Lucide React
- **Backend**: FastAPI, Python 3.11, PyJWT
- **AI/ML**: LangChain, Google Generative AI (Gemini 1.5 Flash), Sentence-Transformers
- **Database**: FAISS (Facebook AI Similarity Search)
- **Deployment**: Docker, Docker Compose

## 🚀 Setup Instructions

### Option 1: Docker (Recommended)

1. Ensure you have Docker and Docker Compose installed.
2. Create a `.env` file in the root directory and add your API keys:
   ```env
   GOOGLE_API_KEY=your_gemini_api_key_here
   SECRET_KEY=your_random_secret_string_for_jwt
   ```
3. Run the following command:
   ```bash
   docker-compose up --build
   ```
4. Access the frontend at `http://localhost:3000` and the API at `http://localhost:8000`.

### Option 2: Local Setup

**Backend:**
1. Navigate to the root directory.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the server:
   ```bash
   uvicorn app.main:app --reload
   ```

**Frontend:**
1. Navigate to the `frontend` directory.
2. Install dependencies:
   ```bash
   npm install
   ```
3. Run the Vite dev server:
   ```bash
   npm run dev
   ```

## 📚 API Documentation

Once the backend is running, you can view the auto-generated Swagger UI at `http://localhost:8000/docs`.

### Key Endpoints:

- `POST /login`: Accepts `username` and `password` (form data), returns a JWT `access_token`.
- `POST /upload`: Upload a PDF document. Requires `Bearer` token.
- `POST /ask/stream`: Ask a question. Requires `Bearer` token. Streams back server-sent events with chunks of AI response and source metadata.

## 🧪 Default Test User
- **Username**: testuser
- **Password**: password123