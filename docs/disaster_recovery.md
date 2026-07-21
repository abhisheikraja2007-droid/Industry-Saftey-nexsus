# Disaster Recovery Guide — Industrial Safety AI

> **RTO (Recovery Time Objective)**: < 5 minutes  
> **RPO (Recovery Point Objective)**: < 1 hour  
> **Last Tested**: See CI chaos test job

---

## Backup Strategy

### Automated Backups

Backups are managed via `infrastructure/backup.sh`.

Run as a cron job for automated daily backups:
```bash
# Add to crontab: backup every hour, retain last 7
0 * * * * /path/to/industrial-safety-ai/infrastructure/backup.sh >> /var/log/safety_backup.log 2>&1
```

### Backup Verification

After each backup, the script automatically verifies gzip integrity:
```
✅ Backup created: ./backups/safety_db_20240101_120000.sql.gz (512K)
✅ Backup integrity verified.
```

---

## Disaster Scenarios and Recovery

### Scenario 1: PostgreSQL Container Failure

**Symptoms**: `/ready` shows `postgres: fail`, alerts/data not loading  
**Impact**: New data cannot be persisted; reads may fail  

**Recovery Steps**:
```bash
# Step 1: Restart the container
docker compose restart postgres
sleep 15

# Step 2: Verify recovery
curl http://localhost:8000/ready
# Expected: {"ready":true,"checks":{"postgres":"ok",...}}

# Step 3: If container fails to start, check logs
docker compose logs postgres --tail=50
```

**Data Integrity Check**:
```bash
docker compose exec postgres psql -U safety_user -d safety_db \
  -c "SELECT COUNT(*) FROM alerts; SELECT COUNT(*) FROM sensors;"
```

---

### Scenario 2: Corrupt or Deleted Data Volume

**Symptoms**: PostgreSQL container fails with `data directory not found`  
**Impact**: All persisted data is lost — requires restore from backup  

**Recovery Steps**:
```bash
# Step 1: Stop all services
docker compose down

# Step 2: Remove corrupted volume (destructive!)
docker volume rm industrial-safety-ai_postgres_data

# Step 3: Start only postgres to get a fresh DB
docker compose up -d postgres
sleep 15

# Step 4: Restore from latest backup
./infrastructure/backup.sh restore ./backups/safety_db_LATEST.sql.gz

# Step 5: Run Alembic migrations to ensure schema is current
docker compose run --rm backend alembic upgrade head

# Step 6: Start remaining services
docker compose up -d

# Step 7: Verify
curl http://localhost:8000/ready
```

---

### Scenario 3: Backend Container Crash Loop

**Symptoms**: Backend keeps restarting, shows `Restarting` status  

**Recovery Steps**:
```bash
# Step 1: Check logs for root cause
docker compose logs backend --tail=100

# Step 2: Common causes:
# - Database not ready yet: wait 30s and retry
# - Missing environment variable: check .env file
# - Port conflict: check docker compose ps

# Step 3: Force recreate
docker compose up -d --force-recreate backend

# Step 4: If still failing, roll back to previous image
docker tag safety-backend:stable safety-backend:latest
docker compose up -d backend
```

---

### Scenario 4: Complete Stack Loss

**Symptoms**: All containers are stopped or host server is replaced  

**Recovery Steps** (from clean host):
```bash
# Step 1: Clone repository
git clone <repo> && cd industrial-safety-ai

# Step 2: Restore .env with secrets
cp /backup/secrets/.env .env

# Step 3: Start infrastructure first
docker compose up -d postgres redis mosquitto
sleep 30  # Wait for DBs to initialize

# Step 4: Restore database from backup
./infrastructure/backup.sh restore /backup/db/safety_db_LATEST.sql.gz

# Step 5: Run migrations
docker compose run --rm backend alembic upgrade head

# Step 6: Start all services
docker compose up -d

# Step 7: Verify full stack
curl http://localhost:8000/health
curl http://localhost:8000/ready
python backend/tests/test_e2e_workflow.py
```

**Expected Recovery Time**: < 5 minutes (RTO ✅)

---

### Scenario 5: Redis Cache Loss

**Symptoms**: Celery tasks not processing, rate limiter reset  
**Impact**: Background AI analysis may be delayed; rate limits reset  

**Recovery Steps**:
```bash
# Redis data is ephemeral (cache only) — simply restart
docker compose restart redis
sleep 10
curl http://localhost:8000/ready
# Expected: redis: ok
```

> **Note**: Redis data loss has no impact on business data — all persistent data is in PostgreSQL.

---

## Point-in-Time Recovery

For databases with WAL archiving enabled (advanced setup), you can recover to any point in time:

```bash
# 1. Find the target backup closest to the incident time
ls -lt ./backups/

# 2. Restore base backup
./infrastructure/backup.sh restore ./backups/safety_db_20240101_110000.sql.gz

# 3. Apply SQL transaction log to reach target time
# (requires WAL archiving to be configured in PostgreSQL)
```

---

## Data Integrity Verification Post-Recovery

After any restore, run these verification steps:

```bash
# 1. Schema integrity
docker compose exec postgres psql -U safety_user -d safety_db \
  -c "\dt" | grep -E "alerts|sensors|users|permits"

# 2. Row counts
docker compose exec postgres psql -U safety_user -d safety_db \
  -c "SELECT 
    (SELECT COUNT(*) FROM alerts) as alerts,
    (SELECT COUNT(*) FROM sensors) as sensors,
    (SELECT COUNT(*) FROM users) as users,
    (SELECT COUNT(*) FROM incident_reports) as reports;"

# 3. API end-to-end smoke test
curl http://localhost:8000/api/alerts
curl http://localhost:8000/api/incident-reports
curl http://localhost:8000/api/dashboard

# 4. Run full E2E test suite
python backend/tests/test_e2e_workflow.py
```

---

## Recovery Contact Checklist

When a Sev-1 incident occurs:

- [ ] 1. Identify failing service via `/ready` endpoint
- [ ] 2. Follow relevant scenario above
- [ ] 3. Verify data integrity post-recovery
- [ ] 4. Document incident in incident report via AI interface
- [ ] 5. Update backup frequency if RPO was breached
- [ ] 6. Update this document with lessons learned
