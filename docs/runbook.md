# Operations Runbook — Industrial Safety AI

> **Version**: 1.0.0 | **Last Updated**: 2024-01-01  
> **Maintained by**: Platform Engineering  
> **SLA**: 99.9% uptime | P95 latency < 500ms

---

## Table of Contents
1. [Service Overview](#service-overview)
2. [Architecture Diagram](#architecture-diagram)
3. [Environment Setup](#environment-setup)
4. [Startup Procedures](#startup-procedures)
5. [Health Checks](#health-checks)
6. [Common Alerts and Responses](#common-alerts-and-responses)
7. [Deployment Procedures](#deployment-procedures)
8. [Rollback Procedures](#rollback-procedures)
9. [Scaling Guidelines](#scaling-guidelines)
10. [On-Call Contacts](#on-call-contacts)

---

## 1. Service Overview

| Component | Technology | Port | Purpose |
|-----------|-----------|------|---------|
| Backend API | FastAPI + Uvicorn | 8000 | REST API, WebSocket, ML inference |
| Frontend | React + Nginx | 3000 / 3443 | Dashboard UI |
| Database | PostgreSQL 16 | 5432 | Persistent data store |
| Cache | Redis 7 | 6379 | Celery broker, session cache |
| Message Queue | Mosquitto MQTT | 1883 | IoT sensor ingestion |
| Metrics | Prometheus | 9090 | Metrics scraping |
| Visualization | Grafana | 3001 | Dashboards |

---

## 2. Architecture Diagram

```
IoT Sensors ─► Mosquitto MQTT ─► Backend (FastAPI)
                                       │
                     ┌─────────────────┼─────────────────┐
                     ▼                 ▼                   ▼
               PostgreSQL           Redis              Prometheus
               (Persistence)     (Celery)             (Metrics)
                                                           │
                                                        Grafana
                                                     (Dashboards)
                     │
                  WebSocket
                     │
               React Dashboard
```

---

## 3. Environment Setup

### Required Environment Variables

| Variable | Default | Required | Description |
|----------|---------|----------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://...` | **Yes** | PostgreSQL async URL |
| `REDIS_URL` | `redis://redis:6379/0` | **Yes** | Redis connection URL |
| `JWT_SECRET` | *(none)* | **Yes** | Comma-separated keys for rotation |
| `OPENAI_API_KEY` | *(empty)* | No | GPT-4 incident report generation |
| `MQTT_BROKER` | `mosquitto` | No | MQTT broker hostname |
| `LOG_LEVEL` | `INFO` | No | `DEBUG`/`INFO`/`WARNING`/`ERROR` |
| `GRAFANA_PASSWORD` | `admin` | No | Grafana admin password |

### JWT Key Rotation

Rotate JWT secrets **without downtime** using a comma-separated list:
```bash
# During rotation: old key still validates existing tokens
JWT_SECRET=new-primary-key,old-key-being-retired

# After 7 days (all refresh tokens expired): remove old key
JWT_SECRET=new-primary-key
```

---

## 4. Startup Procedures

### Fresh Start (Empty Environment)

```bash
# 1. Clone the repository
git clone <repo> && cd industrial-safety-ai

# 2. Configure secrets
cp .env.example .env
# Edit .env with real values — especially JWT_SECRET and OPENAI_API_KEY

# 3. Build and launch all services
docker compose up --build -d

# 4. Verify all services are healthy
docker compose ps
curl http://localhost:8000/health
curl http://localhost:8000/ready

# 5. Check logs
docker compose logs backend --tail=50
```

### Verify Startup
```bash
# All three probes should return HTTP 200
curl -sf http://localhost:8000/health && echo "✅ Health OK"
curl -sf http://localhost:8000/ready  && echo "✅ Ready OK"
curl -sf http://localhost:8000/live   && echo "✅ Live OK"

# Prometheus should scrape backend metrics
curl -sf http://localhost:9090/-/ready && echo "✅ Prometheus OK"

# Grafana should be up
curl -sf http://localhost:3001/api/health && echo "✅ Grafana OK"
```

---

## 5. Health Checks

### Probe Endpoints

| Endpoint | Purpose | Expected |
|----------|---------|---------|
| `GET /health` | Basic liveness | `{"status":"ok"}` |
| `GET /ready` | DB+Redis+MQTT check | `{"ready":true,"checks":{...}}` |
| `GET /live` | Disk space check | `{"alive":true,"disk_free_pct":XX}` |
| `GET /metrics` | Prometheus metrics | Prometheus text format |

### Interpreting `/ready` Response

```json
{
  "ready": true,
  "checks": {
    "postgres": "ok",
    "redis": "ok",
    "mqtt": "ok"
  }
}
```

If any check is `"fail: <error>"`, the container is not ready to serve traffic.

---

## 6. Common Alerts and Responses

### 🔴 SEV-1: Backend is Down

**Symptoms**: `/health` returns non-200 or times out  
**Response**:
```bash
docker compose logs backend --tail=100
docker compose restart backend
# If still failing:
docker compose down && docker compose up -d
```

### 🔴 SEV-1: PostgreSQL is Down

**Symptoms**: `/ready` shows `postgres: fail`  
**Response**:
```bash
docker compose restart postgres
docker compose logs postgres --tail=50
# Verify data volume
docker volume ls | grep postgres_data
```

### 🟡 SEV-2: High Risk Score (> 80)

**Symptoms**: Dashboard shows critical alert; `current_risk_score` metric > 80  
**Response**:
1. Check active alerts in dashboard at http://localhost:3000
2. Trigger evacuation protocol if compound hazard detected
3. Acknowledge alerts after investigation
4. Generate AI incident report for audit trail

### 🟡 SEV-2: Rate Limit Exceeded

**Symptoms**: API returns 429 responses  
**Response**:
- Check for automated scripts or DDoS patterns
- Increase `default_limits` in SlowAPI if legitimate traffic surge
- Block offending IPs at the load balancer level

### 🟡 SEV-2: Low Disk Space

**Symptoms**: `/live` returns `{"alive":false,"disk_free_pct":< 5}`  
**Response**:
```bash
# Run backup and clean up old data
./infrastructure/backup.sh
docker system prune -f
# Check PostgreSQL table sizes
docker exec postgres psql -U safety_user -d safety_db -c "SELECT relname, pg_size_pretty(pg_total_relation_size(relid)) FROM pg_stat_user_tables ORDER BY pg_total_relation_size(relid) DESC;"
```

---

## 7. Deployment Procedures

### Rolling Update (No Downtime)

```bash
# 1. Pull latest changes
git pull origin main

# 2. Build new backend image
docker build -t safety-backend:new -f Dockerfile.backend .

# 3. Run Alembic migrations before swapping containers
docker compose run --rm backend alembic upgrade head

# 4. Deploy new backend container
docker compose up -d --no-deps --build backend

# 5. Verify health probes pass
sleep 30 && curl -sf http://localhost:8000/ready
```

### Blue-Green Deployment (Production)

```bash
# 1. Start new "green" stack on different ports
docker compose -f docker-compose.green.yml up -d

# 2. Run smoke tests against green stack
BASE_URL=http://localhost:8001 python backend/tests/test_e2e_workflow.py

# 3. Switch load balancer to green stack
# (update Nginx upstream to point to green)

# 4. Monitor for 15 minutes

# 5. Remove old "blue" stack
docker compose -f docker-compose.blue.yml down
```

---

## 8. Rollback Procedures

### Application Rollback

```bash
# 1. Identify previous image
docker images safety-backend --format "table {{.Tag}}\t{{.CreatedAt}}"

# 2. Roll back to previous version
docker compose stop backend
docker tag safety-backend:previous safety-backend:latest
docker compose up -d backend

# 3. Roll back DB migration (one step)
docker compose run --rm backend alembic downgrade -1

# 4. Verify
curl -sf http://localhost:8000/ready
```

### Database Rollback from Backup

See [Disaster Recovery Guide](./disaster_recovery.md) for full procedure.

---

## 9. Scaling Guidelines

### Vertical Scaling

Update `docker-compose.yml` resource limits:
```yaml
backend:
  deploy:
    resources:
      limits:
        cpus: '2.0'
        memory: 2G
```

### Horizontal Scaling

For multiple backend replicas, ensure:
- A shared Redis instance for session data
- Sticky sessions at the load balancer
- Prometheus federation for multi-instance scraping

---

## 10. Service Level Objectives (SLOs)

| Metric | Target | Alert Threshold |
|--------|--------|----------------|
| API Availability | ≥ 99.9% | < 99.5% |
| P95 API Latency | < 500ms | > 750ms |
| P99 API Latency | < 2000ms | > 3000ms |
| WebSocket Delivery | ≥ 99.9% | < 99% |
| Alert Generation Latency | < 2s | > 5s |
| DB Recovery (RTO) | < 5 min | > 10 min |
| Data Loss (RPO) | < 1 hour | > 4 hours |
