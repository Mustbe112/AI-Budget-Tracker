# AI Budget Tracker

An intelligent personal finance backend. Users record income and expenses, manage budgets, scan receipts, detect unusual spending, forecast future costs, and receive AI-generated saving advice.

> **Status:** the backend is built step by step (see [Roadmap](#roadmap)). This README describes the target design and setup, and is updated as each step lands.

## Table of contents

1. [Features](#features)
2. [System architecture](#system-architecture)
3. [Workflow](#workflow)
4. [Database design](#database-design)
5. [AI recommendation flow](#ai-recommendation-flow)
6. [Tech stack and dependency versions](#tech-stack-and-dependency-versions)
7. [Project structure](#project-structure)
8. [Setup guide](#setup-guide)
9. [Environment variables](#environment-variables)
10. [Running the backend](#running-the-backend)
11. [API reference](#api-reference)
12. [Algorithms](#algorithms)
13. [Testing](#testing)
14. [Security](#security)
15. [Team and responsibilities](#team-and-responsibilities)
16. [Roadmap](#roadmap)
17. [Troubleshooting](#troubleshooting)

## Features

- Add, edit, and delete expenses and income
- Daily, weekly, and monthly budgets with overspending checks
- Receipt scanning: upload, extract, review, then confirm
- Reports by day, week, month, and category, plus period comparison
- Anomaly detection for unusual expenses
- Spending forecast based on a moving average
- AI explanations, saving tips, and a chat about your own spending
- JWT login, hashed passwords, and strict per-user data access

Design rules that apply everywhere:

- All money values use `Decimal` in Python and `NUMERIC` in PostgreSQL, never floats.
- The LLM never calculates money. Python calculates, the LLM only explains.
- OCR and AI are optional. The core backend runs without them.
- Unconfirmed OCR results are never saved as transactions.

## System architecture

Each diagram is a PNG image in `docs/images/`, so it displays in any viewer. The Mermaid source is included under each image for easy editing.

![System architecture](docs/images/architecture.png)

<details>
<summary>Editable Mermaid source</summary>

```mermaid
flowchart LR
    subgraph Client["Client"]
        FE["React Frontend"]
    end
    subgraph API["FastAPI Backend (Uvicorn)"]
        SEC["Core<br/>JWT auth, config, security"]
        RT["Routers<br/>expenses, income, budgets,<br/>reports, analysis, receipts, ai"]
        SV["Services<br/>business logic"]
        AL["Algorithms<br/>budget, IQR, statistics,<br/>moving average"]
        SEC -.-> RT
        RT --> SV --> AL
    end
    subgraph Data["Data"]
        DB[("PostgreSQL<br/>SQLAlchemy + Alembic")]
    end
    subgraph Optional["Optional modules (backend runs without them)"]
        OCR["PaddleOCR<br/>receipt OCR"]
        LLM["LLM provider<br/>Groq API"]
    end
    FE <-->|"REST / JSON, Bearer JWT"| RT
    SV <-->|"user-scoped SQL"| DB
    SV -.->|"image"| OCR
    SV -.->|"verified data only"| LLM
```

</details>

| Layer | Responsibility |
|---|---|
| React frontend | User interface; talks to the backend over REST and JSON |
| Routers | HTTP endpoints, request and response schemas, status codes |
| Services | Business logic; the only layer that touches the database, OCR, and LLM |
| Algorithms | Pure Python calculations (budget, IQR, statistics, forecast) |
| PostgreSQL | Persistent storage via SQLAlchemy; schema versioned by Alembic |
| PaddleOCR (optional) | Reads text from receipt images |
| LLM provider (optional) | Groq API for explanations and chat |

Dependency direction is one-way: `routers -> services -> algorithms / database`. Algorithms never import the database or the web framework, which keeps them easy to test.

## Workflow

![User workflow](docs/images/workflow.png)

<details>
<summary>Editable Mermaid source</summary>

```mermaid
flowchart TD
    A(["User signs in<br/>JWT issued"]) --> B{"Add an expense"}
    B -->|manual| C["Enter manually<br/>POST /expenses"]
    B -->|receipt| D["Upload receipt<br/>POST /receipts/upload"]
    D --> E["Extract with OCR<br/>POST /receipts/extract<br/>merchant, date, total"]
    E --> F["User reviews and edits"]
    F --> G["Confirm<br/>POST /receipts/confirm"]
    C --> H["Expense saved<br/>Decimal / NUMERIC"]
    G --> H
    H --> I["Budget check<br/>GET /budgets/check"]
    I -->|exceeded| J["Overspending alert"]
    I -->|within budget| K["Analysis and reports<br/>anomalies, forecast, summary"]
    J --> K
    K --> L["AI recommendations<br/>POST /ai/recommendations"]
```

</details>

1. The user registers or logs in and receives a JWT.
2. An expense is added manually, or through the receipt flow: upload, OCR extract, user review, confirm.
3. The saved expense is checked against the user's budgets.
4. If a budget is exceeded, an overspending alert is returned.
5. Reports and analysis (anomalies, forecast, summary) are available at any time.
6. AI recommendations are generated from the verified analysis results.

## Database design

![Entity relationship diagram](docs/images/erd.png)

<details>
<summary>Editable Mermaid source</summary>

```mermaid
erDiagram
    USERS ||--o{ EXPENSES : has
    USERS ||--o{ INCOME : has
    USERS ||--o{ BUDGETS : has
    USERS ||--o{ SAVINGS_GOALS : has

    USERS {
        int id PK
        string username UK
        string email UK
        string password_hash
        datetime created_at
    }
    EXPENSES {
        int id PK
        int user_id FK
        string category
        numeric amount "NUMERIC(12,2)"
        string description
        string merchant
        date expense_date
        datetime created_at
    }
    INCOME {
        int id PK
        int user_id FK
        numeric amount "NUMERIC(12,2)"
        string source
        date date
    }
    BUDGETS {
        int id PK
        int user_id FK
        string category
        numeric amount "NUMERIC(12,2)"
        string period "daily, weekly, monthly"
        date start_date
        date end_date
    }
    SAVINGS_GOALS {
        int id PK
        int user_id FK
        string goal_name
        numeric target_amount "NUMERIC(12,2)"
        numeric current_amount "NUMERIC(12,2)"
        date target_date
    }
```

</details>

- Every table links to `users` through `user_id`, and every query filters by the authenticated user.
- Money columns use `NUMERIC(12, 2)`.
- Planned constraints: amounts must be greater than zero, budget period must be `daily`, `weekly`, or `monthly`, and `end_date` must not be before `start_date`.
- Schema changes go through Alembic migrations, never manual edits.

## AI recommendation flow

![AI recommendation flow](docs/images/ai_flow.png)

<details>
<summary>Editable Mermaid source</summary>

```mermaid
flowchart LR
    Q(["User question or<br/>recommendation request"]) --> API["FastAPI<br/>/ai/recommendations<br/>/ai/chat"]
    API --> DB[("PostgreSQL<br/>only this user's rows")]
    DB --> PY["Python algorithms<br/>Decimal math: totals,<br/>overage, trends"]
    PY --> V["Verified summary<br/>JSON"]
    V --> LLM["LLM<br/>Groq API"]
    LLM --> ANS(["Explanation and<br/>saving tips"])
    LLM -.->|"error or timeout"| FB["Return calculated results only"]
```

</details>

1. The endpoint loads only the signed-in user's records.
2. Python algorithms produce verified numbers (totals, overage, trends).
3. Only that verified summary is sent to the LLM.
4. The LLM writes the explanation. If it is unavailable or times out, the API returns the calculated results without the text.

Example: daily food budget ฿150, actual spending ฿220. Python computes the ฿70 overage and the status `Exceeded`; the LLM turns that into plain advice.

## Tech stack and dependency versions

Versions below were the latest stable releases when this README was written. Pin them in `requirements.txt` so every team member gets the same environment.

### Runtime

| Tool | Version | Purpose |
|---|---|---|
| Python | 3.12 (3.11 also fine) | Language |
| PostgreSQL | 16 or newer | Database |

### Python packages

| Package | Version | Purpose |
|---|---|---|
| fastapi | 0.163.1 | Web framework and OpenAPI docs |
| uvicorn | 0.54.0 | ASGI server |
| sqlalchemy | 2.1.8 | ORM |
| alembic | 1.20.1 | Database migrations |
| psycopg2-binary | 2.9.13 | PostgreSQL driver |
| pydantic | 2.14.3 | Data validation |
| pydantic-settings | 2.16.3 | Environment-based config |
| PyJWT | 2.15.1 | JWT creation and verification |
| bcrypt | 5.0.0 | Password hashing |
| python-multipart | 0.0.33 | File upload parsing |
| python-dotenv | 1.2.4 | Loads `.env` |
| numpy | 2.5.4 | Quartiles for IQR |
| pillow | 13.0.0 | Image validation |
| groq | 1.7.0 | Groq API client (optional) |
| paddleocr | 3.7.0 | Receipt OCR (optional) |
| paddlepaddle | 3.3.1 | PaddleOCR engine (optional) |
| pytest | 9.2.0 | Testing |

Optional packages are kept in `requirements-optional.txt` so the core backend installs quickly and runs without OCR or AI.

## Project structure

```
backend/
├── app/
│   ├── main.py                  # App creation and router registration only
│   ├── core/
│   │   ├── config.py            # Settings from environment variables
│   │   └── security.py          # Password hashing, JWT helpers
│   ├── database/
│   │   ├── connection.py        # Engine, session, get_db dependency
│   │   └── models.py            # SQLAlchemy models
│   ├── schemas/                 # Pydantic request/response models
│   │   ├── expense.py
│   │   ├── income.py
│   │   ├── budget.py
│   │   └── report.py
│   ├── routers/                 # HTTP layer
│   │   ├── auth.py
│   │   ├── expenses.py
│   │   ├── income.py
│   │   ├── budgets.py
│   │   ├── reports.py
│   │   ├── analysis.py
│   │   ├── receipts.py
│   │   └── ai.py
│   ├── services/                # Business logic and integrations
│   │   ├── expense_service.py
│   │   ├── budget_service.py
│   │   ├── report_service.py
│   │   ├── notification_service.py
│   │   ├── ai_service.py        # Groq / mock
│   │   └── ocr_service.py       # PaddleOCR / mock
│   ├── algorithms/              # Pure calculations, no DB or web imports
│   │   ├── budget_calculator.py
│   │   ├── anomaly_detection.py
│   │   ├── spending_analysis.py
│   │   └── spending_forecast.py
│   └── tests/
│       ├── test_expenses.py
│       ├── test_budgets.py
│       └── test_algorithms.py
├── alembic/                     # Migration scripts
├── docs/images/                 # Diagram images used in this README
├── requirements.txt
├── requirements-optional.txt
├── .env.example
└── README.md
```

`auth.py` and `ai.py` routers are added to the suggested structure because login and AI endpoints need a home.

## Setup guide

### 1. Prerequisites

- Python 3.11 or 3.12
- PostgreSQL 16 or newer
- Git
- Optional: a Groq API key (create one in the Groq console)

### 2. Clone and create a virtual environment

```bash
git clone <your-repository-url>
cd ai-budget-tracker/backend

python -m venv .venv
source .venv/bin/activate        # macOS / Linux
.venv\Scripts\activate           # Windows (PowerShell)
```

### 3. Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt

# Optional: receipt OCR and AI clients
pip install -r requirements-optional.txt
```

### 4. Create the database

```bash
psql -U postgres
```

```sql
CREATE USER budget_user WITH PASSWORD 'change_me';
CREATE DATABASE budget_tracker OWNER budget_user;
\q
```

### 5. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` (see [Environment variables](#environment-variables)). Never commit `.env`.

### 6. Run migrations

```bash
alembic upgrade head
```

To create a new migration after changing models:

```bash
alembic revision --autogenerate -m "describe the change"
alembic upgrade head
```

### 7. Optional: set up the Groq API

Create an API key in the Groq console, then set these in `.env`:

```env
AI_PROVIDER=groq
GROQ_API_KEY=your_key_here
GROQ_MODEL=<model name from the Groq console>
```

Without a key, set `AI_PROVIDER=mock` and the AI endpoints return calculated results with a placeholder message. Never commit your key to GitHub.

## Environment variables

`.env.example`:

```env
# App
APP_ENV=development
SECRET_KEY=replace_with_a_long_random_string
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Database
DATABASE_URL=postgresql+psycopg2://budget_user:change_me@localhost:5432/budget_tracker

# Receipt OCR: paddle | mock
OCR_PROVIDER=mock
MAX_UPLOAD_MB=5

# AI: groq | mock
AI_PROVIDER=mock
GROQ_API_KEY=
GROQ_MODEL=

# Analysis
ANOMALY_MIN_HISTORY=10
FORECAST_WINDOW_DAYS=5
```

Generate a secret key:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

## Running the backend

```bash
uvicorn app.main:app --reload --port 8000
```

| URL | Description |
|---|---|
| http://localhost:8000/docs | Swagger UI (try endpoints in the browser) |
| http://localhost:8000/redoc | ReDoc |
| http://localhost:8000/openapi.json | OpenAPI schema for frontend tooling |

## API reference

All endpoints except `/auth/*` require the header `Authorization: Bearer <token>`.

### Authentication

| Method | Path | Description |
|---|---|---|
| POST | `/auth/register` | Create an account |
| POST | `/auth/login` | Get a JWT |

### Expenses

| Method | Path | Description |
|---|---|---|
| POST | `/expenses` | Create an expense |
| GET | `/expenses` | List expenses |
| GET | `/expenses/{id}` | Get one expense |
| PUT | `/expenses/{id}` | Update an expense |
| DELETE | `/expenses/{id}` | Delete an expense |

### Income

| Method | Path | Description |
|---|---|---|
| POST | `/income` | Add income |
| GET | `/income` | List income |
| PUT | `/income/{id}` | Update income |
| DELETE | `/income/{id}` | Delete income |

### Budgets

| Method | Path | Description |
|---|---|---|
| POST | `/budgets` | Create a budget |
| GET | `/budgets` | List budgets |
| PUT | `/budgets/{id}` | Update a budget |
| DELETE | `/budgets/{id}` | Delete a budget |
| GET | `/budgets/check` | Check budget status |

### Reports

| Method | Path | Description |
|---|---|---|
| GET | `/reports/daily` | Daily spending report |
| GET | `/reports/weekly` | Weekly spending report |
| GET | `/reports/monthly` | Monthly spending report |
| GET | `/reports/categories` | Spending by category |
| GET | `/reports/comparison` | Compare two periods |

### Analysis

| Method | Path | Description |
|---|---|---|
| GET | `/analysis/overspending` | Budgets that were exceeded |
| GET | `/analysis/anomalies` | Unusual expenses |
| GET | `/analysis/forecast` | Spending forecast |
| GET | `/analysis/summary` | Spending analysis summary |

### Receipts

| Method | Path | Description |
|---|---|---|
| POST | `/receipts/upload` | Upload a receipt image |
| POST | `/receipts/extract` | Run OCR and return structured data |
| POST | `/receipts/confirm` | Save reviewed data as an expense |

### AI

| Method | Path | Description |
|---|---|---|
| POST | `/ai/recommendations` | Personalized saving recommendations |
| POST | `/ai/chat` | Ask about your spending history |

### Sample requests

Register and log in:

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "somchai", "email": "somchai@example.com", "password": "StrongPass123"}'

curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "somchai", "password": "StrongPass123"}'
```

```json
{ "access_token": "<jwt>", "token_type": "bearer" }
```

Create an expense:

```bash
curl -X POST http://localhost:8000/expenses \
  -H "Authorization: Bearer <jwt>" \
  -H "Content-Type: application/json" \
  -d '{"category": "food", "amount": "90.00", "description": "Dinner", "merchant": "Local Cafe", "expense_date": "2026-11-16"}'
```

```json
{
  "id": 1,
  "category": "food",
  "amount": "90.00",
  "description": "Dinner",
  "merchant": "Local Cafe",
  "expense_date": "2026-11-16"
}
```

Check budgets:

```bash
curl "http://localhost:8000/budgets/check?period=daily&category=food" \
  -H "Authorization: Bearer <jwt>"
```

```json
{
  "category": "food",
  "period": "daily",
  "budget": "150.00",
  "total_spent": "220.00",
  "remaining": "-70.00",
  "overspent_by": "70.00",
  "status": "exceeded"
}
```

Extract a receipt (the result is only a draft until confirmed):

```json
{
  "merchant": "Local Cafe",
  "date": "2026-11-16",
  "total": "90.00",
  "confidence": 0.87,
  "needs_review": true
}
```

Common error format:

```json
{ "detail": "Expense not found" }
```

| Status | Meaning |
|---|---|
| 200 / 201 | Success / created |
| 400 | Bad request (for example, an unreadable receipt) |
| 401 | Missing or invalid token |
| 404 | Record not found, or it belongs to another user |
| 413 | Uploaded file too large |
| 422 | Validation error |
| 503 | OCR or AI service unavailable |

The sample bodies above show the intended contract; the exact fields are finalized in Swagger UI as each router is built.

## Algorithms

All algorithms live in `app/algorithms/`, use `Decimal`, and have no database or web dependencies.

| Algorithm | File | Summary |
|---|---|---|
| Budget calculation | `budget_calculator.py` | Total spent, remaining, overspending, status for daily, weekly, monthly, and category budgets |
| IQR anomaly detection | `anomaly_detection.py` | Per category: `IQR = Q3 - Q1`, upper bound `Q3 + 1.5 * IQR`; flags only, never rejects or deletes; returns "insufficient data" when history is short |
| Statistical analysis | `spending_analysis.py` | Total, average daily, category totals, percentage change, budget utilization; safe when the previous value is zero |
| Moving-average forecast | `spending_forecast.py` | Average of the last N days (configurable window) plus a trend direction |

Worked examples:

- Budget: breakfast 50 + lunch 80 + dinner 90 = 220 against a 150 budget. Overspending 70, remaining -70, status `exceeded`.
- Change: food 800 last week and 1,000 this week gives +25%.
- Forecast: 100, 120, 150, 130, 200 with a 5-day window gives 140.

Forecasts are estimates, not guaranteed future spending, and the API response says so.

## Testing

```bash
pytest -v
```

Planned coverage:

- Create, read, update, delete expenses
- Budget calculations and overspending detection
- Daily, weekly, and monthly reports
- IQR anomaly detection and moving-average forecasting with realistic baht amounts
- Invalid input and unauthorized requests
- OCR and AI failure handling (the backend must keep working)

Tests use a separate database and the `mock` OCR and AI providers, so no external service is needed.

## Security

- Passwords are hashed with bcrypt; plain-text passwords are never stored or returned.
- JWT authentication with an expiry time.
- Every query is filtered by the authenticated user, so one user cannot read another user's records.
- Pydantic validates all input; uploads are checked for type and size.
- Secrets live in environment variables; `.env` is in `.gitignore`.
- The LLM only receives the signed-in user's verified summary.

## Team and responsibilities

| Member | Area | Owns |
|---|---|---|
| 1 | Project coordination | Scope, schedule, integration |
| 2 | Backend and algorithms | FastAPI, services, algorithms, API contract |
| 3 | Database | PostgreSQL schema, migrations |
| 4 | Receipt OCR | PaddleOCR extraction behind `ocr_service.py` |
| 5 | AI recommendations | Prompts and LLM integration behind `ai_service.py` |
| 6 | Frontend | React interface using the API contract |

Integration contracts:

- **Frontend:** use `/openapi.json` or Swagger UI as the source of truth.
- **OCR:** implement the `ocr_service` interface and return `merchant`, `date`, `total`, `confidence`.
- **AI:** implement the `ai_service` interface; it receives a verified summary and returns text.
- **Database:** models and migrations are shared; changes go through Alembic.

## Roadmap

- [ ] 1. Architecture and folder structure
- [ ] 2. Project setup and dependencies
- [ ] 3. Database models and connection
- [ ] 4. Expense and budget APIs
- [ ] 5. Four algorithms
- [ ] 6. Reports and analysis APIs
- [ ] 7. OCR and AI service interfaces
- [ ] 8. Authentication and security
- [ ] 9. Automated tests
- [ ] 10. Final setup and run instructions

## Troubleshooting

| Problem | Fix |
|---|---|
| `connection refused` to PostgreSQL | Make sure PostgreSQL is running and `DATABASE_URL` host, port, user, and password are correct |
| `alembic` cannot find models | Run it from the `backend/` folder and check `alembic/env.py` imports `app.database.models` |
| `ModuleNotFoundError: app` | Run commands from the `backend/` folder |
| OCR endpoint returns 503 | Install `requirements-optional.txt` and set `OCR_PROVIDER=paddle`, or use `mock` |
| AI endpoint returns 503 | Set a valid `GROQ_API_KEY` and check your internet connection, or use `AI_PROVIDER=mock` |
| `401 Unauthorized` | Log in again and send `Authorization: Bearer <token>` |
| PaddlePaddle fails to install | Use Python 3.11 or 3.12 and a 64-bit environment |

## License

Add a license before making the repository public (for example, MIT).
