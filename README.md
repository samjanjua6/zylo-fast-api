# Zylo English Learning AI — Chat & Tutor System

A highly resilient, full-stack chatbot application featuring a **FastAPI backend** powered by **Groq AI (Llama 3.3 & Llama Guard)**, a PostgreSQL database, Google OAuth 2.0, and a premium **React + Tailwind CSS** frontend.

---

## Key Features

1.  **AI English Tutor Persona**: Programmed to provide patient, beginner-friendly explanations in structured, bullet-pointed formatting.
2.  **Google OAuth 2.0 & JWT**: Supports traditional credentials as well as seamless Google Sign-in. Secures REST endpoints and WebSocket connections with signed JSON Web Tokens (JWT).
3.  **Real-time Streaming WebSockets**: Streams response content token-by-token directly to the user bubble.
4.  **Llama Guard Moderation**: Automatically filters user queries through Groq's `llama-guard-3-8b` safety classifier model before hitting the main LLM.
5.  **Token Usage Dashboard**: Estimates prompt/completion token count and tracks API cost in real-time, toggled directly under bot response bubbles.
6.  **Expontential Retry-with-Backoff**: Keeps connection requests stable using retry mechanisms with backoff and jitter during Groq rate limits (429) or timeouts.
7.  **Persisted Theme System**: Clean default **Light Mode** (White canvas, Sky Blue and Sunshine Yellow brand highlights, Dark Blue-Gray text) and **Dark Mode** toggle stored in localStorage.

---

## Directory Overview

```text
zylo-fast-api/
├── app/                        # FastAPI Backend Code
│   ├── auth/                   # Traditional Login, Signup & Google OAuth Router
│   ├── chat/                   # Prompts, WebSocket Router & LLM Logic
│   ├── core/                   # DB Config, Security Utility, and Token Guards
│   ├── users/                  # User DB Model & Profile Router
│   └── main.py                 # App entry point (mounts SPA & API routes)
├── frontend-src/               # React Frontend Source Code (Vite + Tailwind)
│   ├── src/
│   │   ├── components/         # Sidebar, MessageList, TopBar UI blocks
│   │   ├── contexts/           # Light/Dark Theme Context
│   │   ├── pages/              # Landing, Login, and Chat pages
│   │   └── App.jsx             # React routing & Private guards
│   └── vite.config.js          # Port proxies for dev
├── frontend/
│   └── dist/                   # Compiled static bundle files served by FastAPI
└── requirements.txt
```

---

## Setup & Local Installation

### 1. Requirements
*   Python 3.11+
*   Node.js 18+ (for building React)
*   PostgreSQL database running locally

### 2. Backend Setup
1.  Create and activate a virtual environment:
    ```powershell
    python -m venv .venv
    .venv\Scripts\Activate.ps1
    ```
2.  Install requirements:
    ```powershell
    pip install -r requirements.txt
    ```
3.  Create your local `.env` file:
    ```powershell
    copy .env.example .env
    ```
4.  Fill in your API credentials:
    *   `GROQ_API_KEY`: Groq Cloud API access key.
    *   `GOOGLE_CLIENT_ID` & `GOOGLE_CLIENT_SECRET`: Credentials from Google Cloud Console.
    *   `GOOGLE_REDIRECT_URI`: Set to `http://localhost:8000/auth/google/callback` for local development.

### 3. Frontend Compilation
1.  Navigate to the frontend source, install dependencies, and compile:
    ```powershell
    cd frontend-src
    npm install
    npm run build
    cd ..
    ```
    *This creates the production assets in `frontend/dist/` for FastAPI to serve.*

### 4. Running the Server
Run the Uvicorn server:
```powershell
uvicorn app.main:app --reload
```
Open your browser and navigate to:
*   **Landing Page**: `http://localhost:8000/`
*   **Sign In / Sign Up**: `http://localhost:8000/login`
*   **AI Chat Workspace**: `http://localhost:8000/chat`
*   **Interactive API Docs (Swagger)**: `http://localhost:8000/docs`

---

## Testing & Verification
Tests use SQLite in-memory, avoiding the need for a live Postgres connection during verification:
```powershell
pytest -v
```
