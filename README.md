# 🚀 Micro SaaS KPI API

A Dockerized FastAPI-based micro SaaS analytics API that generates
KPI insights, revenue driver analysis, and narrative business reports
directly from a PostgreSQL data warehouse.

This project demonstrates how backend data engineering,
analytics logic, and executive-style reporting can be combined
into a production-style microservice.

---

## 🧠 Project Concept

Instead of building dashboards only,
this API transforms raw KPI data into:

- Revenue Driver Analysis
- Narrative KPI Reports
- Trend Insights
- SaaS-style Business Recommendations

The goal is to simulate how modern analytics products
automatically generate insights for decision-makers.

---

## 🏗️ Architecture

FastAPI (API Layer)
↓
Service Layer (Analytics Logic)
↓
PostgreSQL (KPI Data Store)
↓
Dockerized Deployment

Tech Stack:

- FastAPI
- PostgreSQL
- Docker / Docker Compose
- Psycopg2
- Pydantic

---

## 🔌 API Endpoints

### Health & Base

- `GET /`
- `GET /health`

### KPI Management

- `GET /kpi`
- `POST /kpi`

### Reports

- `GET /report/monthly`
- `GET /report/latest`

### Analytics

- `POST /analyze`

---

## 🧪 Example Insight Output
{
"summary": "Revenue increased mainly due to changes in order volume.",
"risk": "AOV dropped materially (possible discounting).",
"recommendation": "Focus on acquisition and conversion funnel."
}

---

## 🐳 Run with Docker

docker compose up --build


Swagger UI:

http://localhost:8000/docs

---

## 🎯 Why This Project Matters

This project goes beyond SQL analytics.

It shows how data engineers and analytics engineers can:

- Turn KPI tables into API products
- Deliver automated business insights
- Build analytics micro-services
- Bridge backend engineering with decision intelligence

---

## 📂 Project Structure

api/
app/
services/
kpi_service.py
report_service.py
analyze_service.py
schemas.py
db.py
main.py
db/
init.sql
docker-compose.yml
