# AI-Powered Industrial Safety Intelligence System

Centralized AI safety intelligence system correlating data from independent safety subsystems (gas sensors, CCTV, work permits, equipment monitors, shifts) to detect compound hazards in real-time.

## 🚀 Setup & Execution

### Prerequisites
- Docker Desktop must be installed and running on your host machine.

### Quick Start
1. Copy the environment file template:
   ```bash
   cp .env.example .env
   ```
2. Start the full application stack:
   ```bash
   docker-compose up --build
   ```
3. Once running, access the dashboard at:
   - React Frontend: `http://localhost:3000`
   - FastAPI Backend Documentation: `http://localhost:8000/docs`

### 🎭 Live Hackathon Demo Walkthrough
Run the scenario runner to play back the 9-step compound hazard scenario:
```bash
docker-compose exec simulator python scenario_runner.py --speed 1.0
```
Watch the real-time changes unfold on the dashboard:
- Step 1: Normal operations.
- Step 2: CH4 begins rising in Zone-D.
- Step 3: Hot-work permit is issued, triggering warning rule **GAS_HOT_WORK**.
- Step 4: Exhaust fan reports a fault, stopping ventilation, triggering **GAS_FAN_OFF**.
- Step 5: Shift handover occurs, triggering **SHIFT_FAULT_GAS**.
- Step 6: CCTV reports a worker without a hardhat, triggering **PPE_ZONE**.
- Step 7: CO rises above 50 ppm, risk score jumps to **CRITICAL**.
- Step 8: LLM auto-generates a detailed incident report with remediation actions.
- Step 9: Operator resolves the issue; values return to normal.
