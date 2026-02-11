# 🚀 AI Micro-SaaS KPI Insight Engine

> Ask questions like **"Why did revenue drop last quarter?"** and get automated SQL analysis + executive AI insights.

An AI-powered analytics micro-service that converts natural language questions into  
data-driven SQL analysis and executive-ready KPI narratives.

This Dockerized FastAPI backend demonstrates how modern analytics platforms
combine **data engineering, business logic, and LLM-driven insights**
into a production-style micro SaaS architecture.

---

# 🧠 Project Overview

Traditional dashboards require manual exploration.

This system simulates an **AI analytics product** that automatically:

- Parses business questions
- Generates SQL queries
- Retrieves KPI data
- Produces executive insights
- Stores analysis history

Example:

```
POST /ask
"Why did revenue drop last quarter?"
```

⬇️ Automatically performs:

```
Natural Language → Metric Detection → SQL Builder → KPI Analysis → AI Narrative
```

---

# 🏗️ Architecture

```
User Question (/ask)
↓
AI Parser (Metric + Range Detection)
↓
Analytics Service Layer
↓
Dynamic SQL Builder
↓
PostgreSQL KPI Warehouse
↓
LLM Insight Generator
↓
API Response + History Logging
```

---

## 🔄 AI Insight Flow

```
User Question
↓
AI Parser (/ask)
↓
Metric + Range Detection
↓
Dynamic SQL Builder
↓
PostgreSQL KPI Warehouse
↓
LLM Narrative Generator
↓
Executive Insight API Response
```

---

# ⚙️ Tech Stack

Backend:

- FastAPI
- Python
- Pydantic

Data Layer:

- PostgreSQL
- Psycopg2

AI / Analytics:

- Natural Language KPI Parsing
- Dynamic SQL Generation Engine
- Executive Narrative Generation

Infra:

- Docker
- Docker Compose

---

# 🔌 API Endpoints

## Base

- `GET /`
- `GET /health`

---

## Discovery

### `GET /meta`

Returns supported:

- metrics
- ranges
- styles

Example:

```
{
"metrics": ["revenue","orders","customers","aov"],
"ranges": ["last_2_months","last_3_months","last_6_months","ytd"]
}
```

---

## KPI Management

- `GET /kpi`
- `POST /kpi`

---

## AI Analytics

### `POST /ask` ⭐ (AI Entry Point)

Natural language → automatic KPI analysis.

Example:

```
{
"question": "Why did revenue drop recently?"
}
```


Returns:

- parsed metric/range
- generated SQL
- KPI data
- executive narrative

---

### `POST /analyze`

Direct metric analysis.

Example:

```
{
"metric": "revenue",
"range": "last_3_months",
"style": "executive"
}
```


---

## Reports

### `GET /report/monthly`

Rule-based KPI comparison.

### `POST /report/monthly-ai`

AI-generated monthly executive summary.

---

## History (SaaS Feature)

### `GET /history`

Returns past analyses with:

- metric
- SQL
- narrative
- risk
- recommendation
- timestamp

---

## ⚡ Quick Demo

1️⃣ Ask a business question

```
POST /ask
{
"question": "Why did revenue drop last quarter?"
}
```

---

2️⃣ API automatically:

- Detects KPI metric
- Builds SQL query
- Retrieves warehouse data
- Generates AI narrative insights

---

# 🧪 Example AI Insight Output

```
{
"narrative": "Revenue decreased mainly due to declining orders.",
"risk": "Customer acquisition slowdown detected.",
"recommendation": "Focus on acquisition campaigns and conversion optimization."
}
```

---

# 🐳 Run with Docker

```
docker compose up --build
```

Swagger UI:

```
http://localhost:8000/docs
```


---

# 📂 Project Structure

```
api/
├── app/
│ ├── services/
│ │ ├── analyze_service.py
│ │ ├── report_service.py
│ │ ├── kpi_service.py
│ │ ├── ask_service.py
│ │ └── log_service.py
│ ├── schemas.py
│ ├── db.py
│ └── main.py
├── db/
│ └── init.sql
└── docker-compose.yml
```

---

# 🎯 Why This Project Matters

This project demonstrates a real-world evolution of analytics systems:

Instead of dashboards only, analytics becomes an **API-first product**.

Key capabilities shown:

- Dynamic SQL generation
- AI-driven business insight automation
- Analytics micro-service architecture
- Natural language analytics interfaces
- History logging for SaaS-style analytics products

This design reflects how modern companies build
AI-assisted decision intelligence platforms.

---

## 🧩 Real-World Design Inspiration

This project reflects how modern analytics platforms evolve from dashboards
into AI-powered decision engines, enabling stakeholders to interact with
data through natural language instead of manual analysis.

---

# 🚀 Future Extensions

- LLM-based metric detection (full AI parser)
- Multi-metric AI agent analysis
- Streaming KPI ingestion
- Frontend SaaS dashboard
