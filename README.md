# 🏃 Pace Calculator

A running pace calculator — estimate your required pace, speed, splits,
and effort zone from a target distance and finish time.

**Stack:** FastAPI (Python) backend · React (Vite) frontend · Docker Compose

---

## Project structure

```
pace-calculator/
├── backend/                    # Python / FastAPI
│   ├── app/
│   │   ├── calculator.py       # Core pace logic (pure functions)
│   │   ├── models.py           # Pydantic request/response models
│   │   └── main.py             # FastAPI app + routes
│   ├── tests/
│   │   └── test_calculator.py  # Unit tests
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env.example
├── frontend/                   # React / Vite
│   ├── src/
│   │   ├── components/
│   │   │   └── PaceCalculator.jsx
│   │   ├── api.js              # Fetch service layer
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── Dockerfile
│   ├── vite.config.js          # /api proxy → backend :8000
│   └── package.json
├── .github/
│   └── workflows/
│       └── ci.yml              # Backend tests + frontend build
├── docker-compose.yml
└── README.md
```

---

## Quickstart — Docker (recommended)

Requires [Docker Desktop](https://www.docker.com/products/docker-desktop/) or Docker + Compose.

```bash
git clone https://github.com/your-username/pace-calculator.git
cd pace-calculator

docker-compose up
```

| Service  | URL                          |
|----------|------------------------------|
| Frontend | http://localhost:5173        |
| Backend  | http://localhost:8000        |
| API docs | http://localhost:8000/docs   |

To stop: `docker-compose down`

---

## Quickstart — Manual (two terminals)

### Prerequisites

- Python 3.12+
- Node.js 20+

### Terminal 1 — Backend

```bash
cd backend

# Create and activate a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy and adjust environment variables
cp .env.example .env

# Start the dev server
uvicorn app.main:app --reload --port 8000
```

The API will be live at **http://localhost:8000**
Interactive docs (Swagger UI) at **http://localhost:8000/docs**

### Terminal 2 — Frontend

```bash
cd frontend

npm install
npm run dev
```

The app will be live at **http://localhost:5173**

> The Vite dev server proxies all `/api/*` requests to `http://localhost:8000`
> automatically — no CORS issues during development.

---

## Running tests

```bash
cd backend

# With virtual environment activated:
pytest tests/ -v

# Or directly:
python -m pytest tests/ -v
```

Expected output: **26 passed**

---

## API reference

### `POST /calculate`

Calculate pace, speed, splits, and effort zone.

**Request body**
```json
{
  "distance":    "HM",
  "finish_time": "1:45:00",
  "framework":   "1"
}
```

| Field         | Type   | Required | Values                        |
|---------------|--------|----------|-------------------------------|
| `distance`    | string | yes      | `5K`, `10K`, `HM`, `FM`      |
| `finish_time` | string | yes      | `HH:MM:SS`                   |
| `framework`   | string | no       | `1`–`4` (default: `1`)       |

**Framework options**

| Key | Name                              |
|-----|-----------------------------------|
| `1` | General / Fixed Thresholds        |
| `2` | Jack Daniels' VDOT Zones          |
| `3` | Heart Rate Zone Model (5-Zone)    |
| `4` | RPE – Rate of Perceived Exertion  |

**Response (excerpt)**
```json
{
  "pace_fmt_km":   "4:58",
  "pace_fmt_mile": "8:00",
  "speed_kmh":     12.06,
  "speed_mph":     7.49,
  "splits": [
    { "label": "1 km",       "formatted": "4:58" },
    { "label": "5K",         "formatted": "24:53" },
    { "label": "10K",        "formatted": "49:46" },
    { "label": "Half (21K)", "formatted": "1:44:59" },
    { "label": "Full (42K)", "formatted": "3:29:59" }
  ],
  "zone": {
    "level": 3,
    "label": "Moderate / Tempo",
    "framework_name": "General / Fixed Thresholds"
  },
  "all_zones": [ ... ]
}
```

### `GET /meta`

Returns all supported distances and frameworks — useful for populating UI dropdowns dynamically.

### `GET /health`

Returns `{ "status": "ok" }` — useful for container health checks.

---

## Environment variables

| Variable          | Default                   | Description                              |
|-------------------|---------------------------|------------------------------------------|
| `ALLOWED_ORIGINS` | `http://localhost:5173`   | Comma-separated CORS allowed origins     |

Copy `backend/.env.example` → `backend/.env` and adjust as needed.

---

## CI/CD

GitHub Actions runs on every push to `main` / `develop` and on pull requests:

- **Backend job** — installs dependencies, runs `pytest tests/ -v`
- **Frontend job** — installs dependencies, runs `npm run build`

See `.github/workflows/ci.yml`.

---

## Supported distances

| Key  | Distance        | km       |
|------|-----------------|----------|
| `5K` | 5 Kilometers    | 5.0      |
| `10K`| 10 Kilometers   | 10.0     |
| `HM` | Half Marathon   | 21.0975  |
| `FM` | Full Marathon   | 42.195   |

Aliases accepted: `half`, `halfmarathon`, `full`, `fullmarathon`, `marathon` (case-insensitive).
