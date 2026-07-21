# Release & Rollback Strategy — Industrial Safety AI

> This document defines the release management process, deployment strategies,
> version tagging, and rollback checklist for production deployments.

---

## Release Process

### Version Tagging

We follow [Semantic Versioning](https://semver.org): **MAJOR.MINOR.PATCH**

| Bump | When |
|------|------|
| MAJOR | Breaking API changes or DB schema incompatibility |
| MINOR | New features, non-breaking additions |
| PATCH | Bug fixes, security patches, dependency updates |

```bash
# Tag a release
git tag -a v1.2.3 -m "Release v1.2.3 — add WebSocket reconnection"
git push origin v1.2.3
```

### Release Notes Format

```markdown
## v1.2.3 — 2024-01-15

### Features
- Added WebSocket automatic reconnection with exponential backoff

### Bug Fixes
- Fixed sensor validation not rejecting negative gas values

### Security
- Updated PyJWT to 2.8.0 (CVE-2024-XXXX)

### Database Migrations
- Migration `0002_add_ppe_table.py` — adds `ppe_events` table
- Rollback: `alembic downgrade -1`
```

---

## Deployment Strategies

### Strategy 1: Rolling Update (Default — Minimal Downtime)

Used for non-breaking changes.

```bash
# 1. Pull latest and run DB migrations first
git pull origin main
docker compose run --rm backend alembic upgrade head

# 2. Rebuild and restart only the changed service
docker compose up -d --no-deps --build backend

# 3. Verify health probes within 30 seconds
./infrastructure/verify_deployment.sh

# 4. If unhealthy, rollback immediately
# (see Rollback section)
```

**Expected downtime**: 0-5 seconds during container restart.

### Strategy 2: Blue-Green Deployment (Major Releases)

Used for breaking changes or major schema migrations.

```
Internet → Load Balancer → [BLUE: Current Production]
                         → [GREEN: New Version (being deployed)]
```

```bash
# 1. Deploy GREEN on alternate ports
docker compose -f docker-compose.green.yml up -d

# 2. Run full E2E test suite against GREEN
BASE_URL=http://localhost:8001 python backend/tests/test_e2e_workflow.py

# 3. Run load test against GREEN
k6 run -e BASE_URL=http://localhost:8001 infrastructure/load_test/k6_load_test.js

# 4. Switch traffic (update Nginx upstream)
sed -i 's/localhost:8000/localhost:8001/' nginx.conf
docker exec nginx nginx -s reload

# 5. Monitor GREEN for 15 minutes via Grafana

# 6. Decommission BLUE
docker compose -f docker-compose.blue.yml down
```

---

## Pre-Deployment Checklist

Before every production release:

- [ ] All unit tests pass locally (`pytest backend/tests/`)
- [ ] All integration tests pass (`pytest backend/tests/ -m integration`)
- [ ] E2E workflow tests pass (`python backend/tests/test_e2e_workflow.py`)
- [ ] Coverage ≥ 90% backend, ≥ 80% frontend
- [ ] Security scan passes (`bandit -r backend/ -ll`)
- [ ] Dependency audit passes (`pip-audit -r backend/requirements.txt`)
- [ ] Docker image builds without errors
- [ ] Alembic migration tested on a staging database
- [ ] API schema validated (`curl /openapi.json | python -m json.tool`)
- [ ] Release notes written
- [ ] Version tag created

---

## Rollback Checklist

If deployment fails (health probes not passing within 2 minutes):

- [ ] 1. Immediately revert to previous image
  ```bash
  docker compose stop backend
  docker tag safety-backend:previous safety-backend:latest
  docker compose up -d backend
  ```

- [ ] 2. Roll back Alembic migration if schema changed
  ```bash
  docker compose run --rm backend alembic downgrade -1
  ```

- [ ] 3. Verify `/ready` returns HTTP 200 with all checks `"ok"`
  ```bash
  curl -f http://localhost:8000/ready
  ```

- [ ] 4. Verify dashboard loads at http://localhost:3000

- [ ] 5. Notify team of rollback via incident channel

- [ ] 6. Open post-mortem ticket

---

## Service Level Objectives (SLOs) — Measurement

### Availability
- **Target**: ≥ 99.9% (≤ 8.7 hours downtime per year)
- **Measured**: Prometheus `up` metric for backend container
- **Alert**: PagerDuty alert if `up == 0` for > 2 minutes

### Latency
- **Target**: P95 < 500ms, P99 < 2000ms
- **Measured**: `http_request_duration_seconds` histogram in Prometheus
- **Alert**: Fire if P95 > 750ms for 5 consecutive minutes

### Error Rate
- **Target**: < 1% HTTP 5xx responses
- **Measured**: `http_requests_total{status="5xx"}` / `http_requests_total`
- **Alert**: Fire if error rate > 1% for 3 consecutive minutes

### Alert Generation
- **Target**: ≤ 2 seconds from sensor reading to alert creation
- **Measured**: Custom `alert_generation_latency_seconds` metric
- **Alert**: Fire if median > 5 seconds

---

## Recovery Objectives

| Metric | Target | Procedure |
|--------|--------|-----------|
| **RTO** (Recovery Time Objective) | < 5 minutes | Container restart → health probe |
| **RPO** (Recovery Point Objective) | < 1 hour | Hourly automated backups |
| **MTTR** (Mean Time to Recover) | < 10 minutes | On-call runbook |
| **MTBF** (Mean Time Between Failures) | > 30 days | Chaos testing baseline |
