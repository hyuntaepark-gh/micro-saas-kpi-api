# 🚀 AI Executive KPI Intelligence Micro-SaaS

> Ask questions like **"Why did performance drop?"** and receive automated driver analysis, risk signals, and executive-ready AI insights.

An AI-powered analytics backend that transforms natural language questions into KPI analysis, business drivers, and decision intelligence.

This project demonstrates how modern analytics systems evolve from dashboards into **AI-driven decision engines** using a micro-SaaS architecture.

---

## 🧠 AI Executive Decision Intelligence Engine

An AI-powered KPI analytics micro-service that converts business questions into:

- Driver decomposition
- Risk scoring
- Executive insight generation

### 🔥 Core Capabilities

- 🤖 Multi-Metric AI Agent Analysis  
- 📊 Driver Decomposition Engine  
- ⚠️ Risk Signal & Decision Scoring  
- 🧠 Executive Narrative Generation  
- 🐳 Dockerized Micro-SaaS Architecture  

---

### ⚡ AI Insight Pipeline

```
User Question
→ Agent Intelligence
→ KPI Driver Analysis
→ Decision Engine
→ Executive Report
```

# 🧠 Project Overview

Traditional BI tools require manual exploration.

This system simulates an **AI analytics product** that automatically:

- Detects KPI intent from natural language
- Generates dynamic SQL queries
- Performs driver decomposition
- Calculates risk signals
- Produces executive narratives
- Stores analysis history

Example:

```
POST /ask
{
"question": "Why did performance drop?"
}
```

⬇️ Pipeline:


```
Natural Language
→ AI Agent
→ Driver Analysis
→ Decision Engine
→ Executive Report
```

---

# 🏗️ Architecture

```
User Question (/ask)
↓
Agent Intelligence Layer
↓
Metric Detection + Intent Service
↓
Dynamic SQL Builder
↓
PostgreSQL KPI Warehouse
↓
Driver Decomposition Engine
↓
Decision Signal Engine (Risk Score)
↓
Executive Report Formatter
↓
API Response + History Logging
```

---

## 🔄 AI Insight Flow

```
User Question
↓
AI Agent Router
↓
Multi-Metric Analysis
↓
Driver Summary
↓
Decision Signals (risk_score)
↓
Executive Narrative Builder
↓
Final Executive Response
```

---


---

# ⚙️ Tech Stack

## Backend

- FastAPI
- Python
- Pydantic

## Data Layer

- PostgreSQL
- Psycopg2
- Dynamic SQL Builder

## AI / Decision Intelligence

- Agent Intelligence Engine
- Driver Decomposition Service
- Risk Scoring Engine
- Executive Report Formatter
- LLM Planning Layer

## Infra

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

---

## KPI Management

- `GET /kpi`
- `POST /kpi`

---

## 🧠 AI Analytics Engine

### `POST /ask` ⭐ (Primary Entry Point)

Natural language → AI executive analysis.

Example:

```
{
"question": "Why did performance drop?"
}
```

Returns:

- multi-metric analysis
- driver_summary
- decision signals (risk_score)
- executive report

---

### `POST /analyze`

Direct KPI metric analysis.

---

## 📊 Reports

### `GET /report/monthly`

Rule-based KPI comparison.

### `POST /report/monthly-ai`

LLM-generated executive summary.

---

## 🧾 SaaS History Feature

### `GET /history`

Stores past AI analyses:

- metric
- SQL
- narrative
- risk
- recommendation
- timestamp

---

# ⚡ Quick Demo

1️⃣ Insert KPI data

```
POST /kpi
```

---

2️⃣ Ask AI:

```
POST /ask
{
"question": "Why did performance drop?"
}
```

---

3️⃣ Receive:

```
Driver analysis
Risk score
Executive narrative
```

---

# 🧪 Example Executive Output

```
{
"main_driver": "orders",
"risk_signal": "LOW",
"trend_direction": "UP",
"risk_score": 10,
"executive_takeaway":
"Revenue change is primarily driven by order volume."
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

# 🎯 Why This Project Matters

Modern analytics platforms are evolving into **decision intelligence systems**.

This project demonstrates:

- AI Agent-driven analytics
- Executive-level KPI storytelling
- Driver-based business reasoning
- Risk signal generation
- API-first AI SaaS architecture

It reflects how real companies build internal AI decision engines
on top of data warehouses.

---

# 🧩 Real-World Inspiration

Inspired by modern:

- AI Analytics Platforms
- Executive BI Automation
- Decision Intelligence Systems

---

# 🚀 Future Extensions

- Auto SQL generation from natural language
- Risk visual signals for frontend dashboards
- KPI anomaly detection
- Streaming KPI ingestion
- Frontend AI dashboard

---

# 📂 Project Structure

```
api/
├── app/
│ ├── services/
│ │ ├── agent_intelligence.py
│ │ ├── decision_service.py
│ │ ├── driver_service.py
│ │ ├── report_formatter.py
│ │ └── analyze_service.py
│ ├── schemas.py
│ └── db.py
├── llm/
├── routers/
│ ├── kpi.py
│ └── demo.py
└── main.py
```
