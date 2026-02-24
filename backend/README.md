# QuantCAI Backend

High-performance, production-ready FastAPI backend for the QuantCAI Quantum AI Learning Platform.

## 🏗 Architecture Overview

The backend is structured for scalability, maintainability, and ease of use for both human developers and AI agents.

```
backend/
├── core/                # Infrastructure & Boilerplate
│   ├── auth.py         # JWT, OAuth2, Bcrypt hashing
│   ├── database.py     # SQLAlchemy engine & session setup
│   └── logger.py       # Dual-stream logging (File + Database)
├── services/            # Business & Technical Logic
│   ├── ai.py           # LangGraph-based AI Chat & Tools
│   └── quantum.py      # Qiskit-powered Quantum Simulation Engine
├── routers/             # API Endpoints (FastAPI)
│   ├── admin.py        # Admin panel & User management
│   ├── auth.py         # Authentication (Login/Register)
│   ├── chat.py         # AI Assistant (Streaming SSE)
│   ├── circuit.py      # Quantum Circuit execution
│   └── ...             # community, content, health, users
├── models.py            # Unified Database Models (SQLAlchemy)
├── main.py              # Entry point & Middleware configuration
└── requirements.txt     # Production dependencies
```

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- PostgreSQL (or SQLite for development)
- Google AI API Key (for Gemini/LangGraph features)

### Installation
1. Clone the repository.
2. Navigate to `/backend`.
3. Create a virtual environment: `python -m venv .venv`
4. Activate it:
   - Windows: `.venv\Scripts\activate`
   - macOS/Linux: `source .venv/bin/activate`
5. Install dependencies: `pip install -r requirements.txt`

### Configuration
Create a `.env` file based on `.env.example`:
```env
DATABASE_URL=postgresql://user:pass@localhost:5432/quantcai
AUTH_SECRET_KEY=your_very_secret_64_char_hex_key
GOOGLE_API_KEY=AIzaSy...
ALLOWED_ORIGINS=http://127.0.0.1:5173,http://localhost:5173
```

### Running the Server
```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```
API Documentation: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## 🚢 Production Deployment

For production, it is recommended to use the provided `Dockerfile` or a production-grade ASGI server like `gunicorn`:

```bash
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:8000
```

Ensure `ENV=production` and `ALLOWED_ORIGINS` are set correctly in your production environment variables.

## 🤖 Guidelines for AI Agents

QuantCAI is designed to be **AI-First**. When working on this codebase:

1.  **Strict Typing**: Always use Type Hints. Leverage Pydantic models for request/response validation.
2.  **Modular Logic**: Keep `routers/` thin. Place complex logic in `services/`.
3.  **Database Patterns**: 
    - Use `models.py` as the Single Source of Truth for schemas.
    - Always use `current_user` dependency for authorized endpoints.
4.  **Logging**: Use the centralized logger. Prefer `logger.info()` for audit trails and `logger.error()` for exceptions.
5.  **Streaming**: AI Chat uses Server-Sent Events (SSE). Maintain the LangGraph structure in `services/ai.py`.

## 🛠 Feature Modules

- **Quantum Engine**: Integrates Qiskit to simulate circuits and calculate statevectors. Supports noisy simulation.
- **AI Assistant**: A stateful LangGraph agent with tool-calling capabilities (visualizer, circuit builder).
- **Proactive Security**: Includes rate-limiting (SlowAPI), account lockout policies, and hardened CORS/CSP headers.
- **Audit Logging**: Every critical action and error is mirrored to the `logtable` in the database for admin review.

---
*Built for the future of Quantum Learning.*
