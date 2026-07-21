# Hackathon Demo Script

Follow these steps to demonstrate the Industrial Safety Intelligence System during a presentation or review.

## Setup
1. Spin up the docker containers:
   ```bash
   docker-compose up --build
   ```
2. Open the dashboard at `http://localhost:3000`. Verify that the telemetry shows normal status (green, low risk score).

## Step-by-Step Scenario Playback
Run the scenario runner inside the simulator container:
```bash
docker-compose exec simulator python scenario_runner.py --speed 1.0
```

### Scripted Stages to Highlight:
1. **Normal Baseline**: Point out that the gauge displays a safe score (< 30) and the floorplan shows green zones.
2. **CH4 Rise**: Emphasize how sensor cards update to reflect the increasing gas presence in Zone-D.
3. **Hot-Work Incident**: Watch the active rules panel. The system flags the conflict between **hot work** (welding) and **combustible gases** (**GAS_HOT_WORK** rule). The risk indicator changes to Warning (yellow).
4. **Ventilation Failure**: Point out the mechanical fault report for the exhaust fan. The system triggers the critical compound hazard rule **GAS_FAN_OFF**.
5. **Shift Overlap**: Show the shift information section showing a transition. Mid-incident entry triggers **SHIFT_FAULT_GAS**.
6. **PPE Vision Violation**: Navigate to the `/cctv` tab and highlight the YOLOv8 mock overlay identifying workers without hardhats.
7. **Report Generation**: Navigate to `/reports`. The system has automatically generated a report containing AI summaries, root causes, and specific actions.
