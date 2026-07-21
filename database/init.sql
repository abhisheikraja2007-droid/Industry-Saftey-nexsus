-- Industrial Safety AI — PostgreSQL Schema
-- Executed automatically by docker-entrypoint-initdb.d

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- ─── SENSORS ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS sensors (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sensor_id     VARCHAR(64) NOT NULL,
    sensor_type   VARCHAR(32) NOT NULL,  -- gas_ch4, gas_co, gas_h2s, temp, humidity, smoke
    location      VARCHAR(128) NOT NULL,
    zone          VARCHAR(64) NOT NULL,
    value         FLOAT NOT NULL,
    unit          VARCHAR(16) NOT NULL,
    raw_payload   JSONB,
    timestamp     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_sensors_sensor_id     ON sensors(sensor_id);
CREATE INDEX idx_sensors_zone          ON sensors(zone);
CREATE INDEX idx_sensors_timestamp     ON sensors(timestamp DESC);

-- ─── EQUIPMENT STATUS ────────────────────────────────────────
CREATE TABLE IF NOT EXISTS equipment_status (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    equipment_id  VARCHAR(64) NOT NULL,
    name          VARCHAR(128) NOT NULL,
    equipment_type VARCHAR(64) NOT NULL,
    zone          VARCHAR(64) NOT NULL,
    status        VARCHAR(32) NOT NULL,  -- online, fault, offline, maintenance
    temperature   FLOAT,
    vibration     FLOAT,
    rpm           FLOAT,
    extra         JSONB,
    timestamp     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_equipment_id          ON equipment_status(equipment_id);
CREATE INDEX idx_equipment_timestamp   ON equipment_status(timestamp DESC);

-- ─── WORK PERMITS ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS work_permits (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    permit_id     VARCHAR(64) UNIQUE NOT NULL,
    permit_type   VARCHAR(64) NOT NULL,  -- hot_work, confined_space, electrical, excavation
    location      VARCHAR(128) NOT NULL,
    zone          VARCHAR(64) NOT NULL,
    status        VARCHAR(32) NOT NULL DEFAULT 'active',  -- active, expired, cancelled, completed
    issued_by     VARCHAR(128) NOT NULL,
    worker_names  TEXT[],
    issued_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at    TIMESTAMPTZ NOT NULL,
    cancelled_at  TIMESTAMPTZ,
    notes         TEXT
);
CREATE INDEX idx_permits_zone          ON work_permits(zone);
CREATE INDEX idx_permits_status        ON work_permits(status);

-- ─── ALERTS ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS alerts (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    alert_code      VARCHAR(64) NOT NULL,
    severity        VARCHAR(16) NOT NULL,  -- WARNING, HIGH, CRITICAL
    risk_score      INT NOT NULL,
    message         TEXT NOT NULL,
    zone            VARCHAR(64),
    source_events   JSONB NOT NULL DEFAULT '[]',
    acknowledged    BOOLEAN NOT NULL DEFAULT FALSE,
    acknowledged_by VARCHAR(128),
    acknowledged_at TIMESTAMPTZ,
    resolved        BOOLEAN NOT NULL DEFAULT FALSE,
    resolved_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_alerts_severity       ON alerts(severity);
CREATE INDEX idx_alerts_acknowledged   ON alerts(acknowledged);
CREATE INDEX idx_alerts_created_at     ON alerts(created_at DESC);

-- ─── INCIDENT REPORTS ────────────────────────────────────────
CREATE TABLE IF NOT EXISTS incident_reports (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title           VARCHAR(256) NOT NULL,
    summary         TEXT NOT NULL,
    ai_explanation  TEXT,
    risk_score      INT NOT NULL,
    severity        VARCHAR(16) NOT NULL,
    zone            VARCHAR(64),
    events_involved JSONB NOT NULL DEFAULT '[]',
    recommended_actions TEXT[],
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_reports_created_at    ON incident_reports(created_at DESC);

-- ─── SHIFT LOGS ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS shift_logs (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    shift_type    VARCHAR(16) NOT NULL,  -- morning, afternoon, night
    supervisor    VARCHAR(128) NOT NULL,
    worker_count  INT NOT NULL,
    zones_active  TEXT[],
    start_time    TIMESTAMPTZ NOT NULL,
    end_time      TIMESTAMPTZ,
    notes         TEXT
);
CREATE INDEX idx_shifts_start_time     ON shift_logs(start_time DESC);

-- ─── PPE DETECTIONS ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS ppe_detections (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    camera_id       VARCHAR(64) NOT NULL,
    location        VARCHAR(128) NOT NULL,
    zone            VARCHAR(64) NOT NULL,
    ppe_status      VARCHAR(32) NOT NULL,  -- compliant, non_compliant, unknown
    workers_detected INT NOT NULL DEFAULT 0,
    violations      JSONB NOT NULL DEFAULT '[]',  -- list of missing PPE items
    confidence      FLOAT NOT NULL,
    image_path      VARCHAR(512),
    raw_detections  JSONB,
    timestamp       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_ppe_camera_id         ON ppe_detections(camera_id);
CREATE INDEX idx_ppe_timestamp         ON ppe_detections(timestamp DESC);

-- ─── SYSTEM STATE SNAPSHOTS ──────────────────────────────────
CREATE TABLE IF NOT EXISTS system_state_snapshots (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    risk_score      INT NOT NULL,
    risk_level      VARCHAR(16) NOT NULL,
    triggered_rules JSONB NOT NULL DEFAULT '[]',
    anomaly_flags   JSONB NOT NULL DEFAULT '[]',
    zone_scores     JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS users (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username      VARCHAR(128) UNIQUE NOT NULL,
    hashed_password VARCHAR(256) NOT NULL,
    role          VARCHAR(32) NOT NULL DEFAULT 'operator',
    is_active     BOOLEAN NOT NULL DEFAULT TRUE,
    failed_login_attempts INT NOT NULL DEFAULT 0,
    locked_until  TIMESTAMPTZ,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_users_username ON users(username);

CREATE TABLE IF NOT EXISTS token_blacklist (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    token         VARCHAR(512) UNIQUE NOT NULL,
    blacklisted_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_token_blacklist_token ON token_blacklist(token);
