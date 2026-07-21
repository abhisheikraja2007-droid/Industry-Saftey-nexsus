import http from 'k6/http';
import ws from 'k6/ws';
import { check, sleep } from 'k6';
import { Counter, Trend } from 'k6/metrics';

// Custom metrics
const alertsCreated = new Counter('alerts_created');
const wsMessages = new Counter('ws_messages_received');
const sensorLatency = new Trend('sensor_ingest_latency');

export const options = {
  scenarios: {
    // Smoke test: Verify basic functionality at minimal load
    smoke: {
      executor: 'constant-vus',
      vus: 1,
      duration: '30s',
      tags: { scenario: 'smoke' },
    },

    // Load test: 100 users steady state
    load: {
      executor: 'constant-vus',
      vus: 100,
      duration: '2m',
      startTime: '35s',
      tags: { scenario: 'load' },
    },

    // Spike test: Sudden surge to 500 users
    spike: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '10s', target: 500 },
        { duration: '30s', target: 500 },
        { duration: '10s', target: 0 },
      ],
      startTime: '3m',
      tags: { scenario: 'spike' },
    },

    // Soak test: 50 users for extended period
    soak: {
      executor: 'constant-vus',
      vus: 50,
      duration: '5m',
      startTime: '5m',
      tags: { scenario: 'soak' },
    },
  },
  thresholds: {
    http_req_duration: ['p(95)<500'],  // 95th percentile < 500ms (SLO)
    http_req_failed: ['rate<0.01'],    // <1% failure rate
    http_reqs: ['rate>50'],            // >50 RPS minimum throughput
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

// Sensor types used in testing
const SENSOR_TYPES = ['gas_ch4', 'gas_co', 'gas_h2s', 'temp'];
const ZONES = ['Zone-A', 'Zone-B', 'Zone-C', 'Zone-D'];

function randomFloat(min, max) {
  return Math.random() * (max - min) + min;
}

function generateSensorPayload() {
  const zone = ZONES[Math.floor(Math.random() * ZONES.length)];
  const sensorType = SENSOR_TYPES[Math.floor(Math.random() * SENSOR_TYPES.length)];
  let value;
  switch (sensorType) {
    case 'gas_ch4': value = randomFloat(0, 40); break;
    case 'gas_co':  value = randomFloat(0, 60); break;
    case 'gas_h2s': value = randomFloat(0, 10); break;
    case 'temp':    value = randomFloat(20, 95); break;
    default:        value = randomFloat(0, 100);
  }
  return JSON.stringify({
    sensor_id: `SENS-${zone}-${sensorType.toUpperCase()}`,
    sensor_type: sensorType,
    location: zone,
    zone: zone,
    value: value,
    unit: sensorType === 'temp' ? '°C' : 'ppm',
  });
}

export default function () {
  // Test: GET /health
  {
    const res = http.get(`${BASE_URL}/health`);
    check(res, {
      'health returns 200': (r) => r.status === 200,
      'health has status ok': (r) => r.json('status') === 'ok',
    });
  }

  // Test: GET /ready
  {
    const res = http.get(`${BASE_URL}/ready`);
    check(res, {
      'ready returns 200': (r) => r.status === 200,
      'ready is true': (r) => r.json('ready') === true,
    });
  }

  // Test: GET /api/dashboard
  {
    const res = http.get(`${BASE_URL}/api/dashboard`);
    check(res, {
      'dashboard returns 200': (r) => r.status === 200,
    });
  }

  // Test: POST /api/sensor-data (main load)
  {
    const start = Date.now();
    const res = http.post(`${BASE_URL}/api/sensor-data`, generateSensorPayload(), {
      headers: { 'Content-Type': 'application/json' },
    });
    sensorLatency.add(Date.now() - start);
    check(res, {
      'sensor ingest returns 200': (r) => r.status === 200,
    });
  }

  // Test: GET /api/alerts
  {
    const res = http.get(`${BASE_URL}/api/alerts`);
    check(res, {
      'alerts returns 200': (r) => r.status === 200,
      'alerts has total field': (r) => r.json('total') !== undefined,
    });
  }

  // Test: Negative value validation (should return 422)
  {
    const badPayload = JSON.stringify({
      sensor_id: 'TEST-SENSOR',
      sensor_type: 'gas_ch4',
      location: 'Zone-A',
      zone: 'Zone-A',
      value: -5.0,
      unit: 'ppm',
    });
    const res = http.post(`${BASE_URL}/api/sensor-data`, badPayload, {
      headers: { 'Content-Type': 'application/json' },
    });
    check(res, {
      'negative gas value rejected with 422': (r) => r.status === 422,
    });
  }

  sleep(0.5);
}

export function handleSummary(data) {
  return {
    'k6_load_test_results.json': JSON.stringify(data, null, 2),
    stdout: `
=== K6 Load Test Summary ===
VUs: ${data.metrics.vus_max?.values?.max || 'N/A'}
Requests: ${data.metrics.http_reqs?.values?.count || 0}
RPS: ${Math.round(data.metrics.http_reqs?.values?.rate || 0)}
P95 Latency: ${Math.round(data.metrics.http_req_duration?.values?.['p(95)'] || 0)}ms
Failure Rate: ${((data.metrics.http_req_failed?.values?.rate || 0) * 100).toFixed(2)}%
    `,
  };
}
