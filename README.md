# QueryLens — Natural Language to SQL Query Engine

[![Next.js](https://img.shields.io/badge/Next.js-16-black.svg)](https://nextjs.org/)
[![React](https://img.shields.io/badge/React-19-blue.svg)](https://react.dev/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688.svg)](https://fastapi.tiangolo.com/)
[![Google Gemini](https://img.shields.io/badge/Gemini-2.0%20Flash-4285F4.svg)](https://ai.google.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

QueryLens is a modern, production-grade full-stack application that transforms conversational natural language inquiries into safe, optimized SQL queries over structured tabular datasets and CSV files. Powered by **Google Gemini** and backed by **FastAPI** and **Next.js**, QueryLens streamlines data discovery and ad-hoc analytical workflows.

---

## 🌟 Key Features

- **Drag-and-Drop CSV Ingestion**: Instant schema inference and automated SQLite table generation with type detection.
- **Natural Language to SQL**: Converts plain English questions into valid, syntactically correct SQL queries via Google Gemini (`gemini-2.0-flash`).
- **AST-Based Safety & Guardrails**: Enforces read-only execution (`SELECT` only), strictly blocking `INSERT`, `UPDATE`, `DELETE`, `DROP`, and SQL injection patterns.
- **Deep Data Profiling & Statistics**: Computes null distribution, cardinality, numeric bounds (min, max, mean, median), text lengths, and automated quality indicators (`PRIMARY_KEY_CANDIDATE`, `HIGH_NULLS`, `CONSTANT`).
- **SQL Execution Plan Analysis**: Integrated SQLite query planning with `EXPLAIN` to detect full table scans and recommend index optimizations.
- **Data Export Engine**: Export tabular query results directly to CSV or structured JSON formats.
- **Interactive Query Results**: Paginated, sortable tabular view with execution metadata, elapsed execution time, and row counts.
- **Audit & History Log**: Real-time query history tracking with generated SQL snippets and execution outcomes.
- **Modern Dark UI**: Engineered with Next.js 16, React 19, Tailwind CSS, Lucide icons, and shadcn/ui primitives.
- **Per-User LLM Configuration**: Customizable API keys and model selection options with secure client-side storage policies.

---


## 🛠️ Tech Stack

- **Frontend**: Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS, shadcn/ui
- **Backend**: FastAPI, SQLAlchemy 2.0, SQLite, Pandas, Google Gemini SDK (`google-genai`), SlowAPI (Rate Limiting)
- **Validation & Parsing**: Pydantic v2, SQLGlot
- **Testing & Tooling**: Pytest, Vitest/TypeScript, Docker & Docker Compose, uv package manager

---

## 🚀 Quick Start

### 1. Prerequisites
- **Python**: 3.10+ (with [`uv`](https://docs.astral.sh/uv/) recommended)
- **Node.js**: 18+ (`pnpm` or `npm`)
- **Google Gemini API Key**: [Get an API Key](https://aistudio.google.com/)

### 2. Clone Repository
```bash
git clone https://github.com/Pankaj2512/QueryLens.git
cd QueryLens
```

### 3. Environment Configuration
Create a `.env.local` file in the root directory:
```bash
cp .env.example .env.local
```

Configure your environment:
```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.0-flash
ALLOW_CLIENT_LLM_CONFIG=true
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 4. Run with Docker Compose (Recommended)
```bash
docker compose up -d
```
- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000`
- Interactive API Docs: `http://localhost:8000/docs`

---

### 5. Local Manual Setup

#### Backend Setup
```bash
cd backend
# Using uv (fastest)
uv run python -m uvicorn main:app --reload --port 8000

# Or using standard pip / virtualenv
python3 -m venv .venv
source .venv/bin/activate
pip install -r ../requirements.txt
uvicorn main:app --reload --port 8000
```

#### Frontend Setup
In a separate terminal:
```bash
# Using pnpm
pnpm install
pnpm dev

# Or using npm
npm install
npm run dev
```

---

## 📖 How It Works

1. **Upload Dataset**: Drag & drop any CSV file into the upload zone or use the manual table builder.
2. **Select Active Table**: Pick a table from your active SQLite database.
3. **Inspect Schema**: View detected columns, inferred SQL types, and row statistics.
4. **Ask Questions**: Ask questions naturally, e.g.:
   - *"Show the top 5 transactions by value in Q3."*
   - *"What is the average transaction amount grouped by category?"*
   - *"Find all customers who made a purchase over $500 in 2024."*
5. **Analyze Results**: Review the generated SQL and inspect the returned data table.

---

## 🔌 API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` or `/health` | Liveness and health check |
| `GET` | `/health/ready` | Readiness check (validates database connection) |
| `GET` | `/health/full` | Detailed system diagnostics & database stats |
| `POST` | `/upload` | Upload CSV dataset and initialize database table |
| `GET` | `/tables` | List all uploaded and active database tables |
| `GET` | `/schema/{table_name}` | Fetch column definitions and types for a table |
| `POST` | `/query` | Synthesize SQL from natural language and execute query |
| `GET` | `/history` | Retrieve past query execution history |

Interactive Swagger documentation is available at `http://localhost:8000/docs`.

---

## 🛡️ Security & Safety Layer

- **Read-Only Enforcement**: Queries must parse as valid `SELECT` statements. Data modification language (`INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `TRUNCATE`) is blocked at both the LLM prompt and SQL parsing level.
- **SQL Injection Prevention**: Safe parameter wrapping and subquery execution sandbox.
- **CORS Protection**: Explicit frontend origin filtering.
- **Rate Limiting**: Configured endpoints protected by SlowAPI against abuse.

---

## 📁 Repository Structure

```
QueryLens/
├── app/                        # Next.js 16 app directory (App Router)
│   ├── page.tsx               # Primary dashboard interface
│   ├── layout.tsx             # Root layout & global metadata
│   └── globals.css            # Tailwind & shadcn styles
├── components/                # React UI components
│   ├── chat-interface.tsx     # Conversational NL prompt input
│   ├── file-upload-panel.tsx  # Drag-and-drop CSV handler
│   ├── query-results.tsx      # Paginated result data table
│   ├── schema-viewer.tsx      # Table schema inspector
│   ├── gemini-settings.tsx    # Per-user model configuration modal
│   └── ui/                    # Reusable shadcn/ui primitives
├── hooks/                     # Custom hooks
│   └── use-query-lens.ts      # Core state orchestration & API hook
├── backend/                   # FastAPI backend service
│   ├── main.py                # FastAPI routes & endpoints
│   ├── models.py              # SQLAlchemy database models
│   ├── database.py            # SQLite data execution & CSV importer
│   ├── llm.py                 # Google Gemini prompt & SQL generator
│   ├── health.py              # Health check & diagnostics probes
│   ├── error_handlers.py      # Custom exceptions & handlers
│   ├── config.py              # Application settings
│   └── test_main.py           # Pytest test suite
├── docker-compose.yml         # Container composition
├── Dockerfile                 # Multi-stage production build
├── requirements.txt           # Python backend dependencies
└── pyproject.toml             # Python package configuration
```

---

## 🧪 Testing

Run backend test suite:
```bash
cd backend
pytest test_main.py -v
```

---

## 📄 License

Distributed under the [MIT License](LICENSE).
