# Industrial Safety Intelligence System — API Documentation

This document outlines the REST and WebSocket endpoints provided by the FastAPI backend.

## Base URL
- Local Development: `http://localhost:8000`
- WebSockets: `ws://localhost:8000`

---

## 📡 REST Endpoints

### 🔬 Sensors

#### Ingest Sensor Reading
* **POST** `/api/sensor-data`
* **Request Body**:
  ```json
  {
    "sensor_id": "CH4-Zone-D",
    "sensor_type": "gas_ch4",
    "location": "Zone D Storage Wall",
    "zone": "Zone-D",
    "value": 28.5,
    "unit": "ppm"
  }
  ```
* **Response**: `200 OK`

#### Get Latest Readings
* **GET** `/api/sensors`
* **Response**:
  ```json
  {
    "sensors": {
      "Zone-D": {
        "gas_ch4": 28.5,
        "gas_co": 12.0
      }
    },
    "timestamp": "2026-07-05T15:30:00Z"
  }
  ```

#### Get Facility Heatmap
* **GET** `/api/sensors/heatmap`
* **Response**: Returns zone-by-zone calculated risk scores and alert statuses.

---

### ⚙️ Equipment

#### Ingest Equipment Status
* **POST** `/api/equipment-status`
* **Request Body**:
  ```json
  {
    "equipment_id": "FAN-01",
    "name": "Exhaust Fan Zone-D",
    "equipment_type": "fan",
    "zone": "Zone-D",
    "status": "online",
    "temperature": 65.2,
    "vibration": 0.8
  }
  ```

---

### 📝 Work Permits

#### Create Permit
* **POST** `/api/permits`
* **Request Body**:
  ```json
  {
    "permit_type": "hot_work",
    "location": "Zone-D Sub-station 3",
    "zone": "Zone-D",
    "issued_by": "Ahmed Al-Rashid",
    "worker_names": ["Worker-442"],
    "expires_at": "2026-07-05T19:30:00Z"
  }
  ```

---

## 🔌 WebSocket updates
* **Endpoint**: `/ws`
* Real-time events are pushed automatically on this socket to keep dashboard UI state in sync.
