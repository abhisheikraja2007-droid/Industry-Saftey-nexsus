import RiskGauge from '../components/RiskGauge'
import FacilityHeatmap from '../components/FacilityHeatmap'
import SensorPanel from '../components/SensorPanel'
import AlertsPanel from '../components/AlertsPanel'
import EquipmentPanel from '../components/EquipmentPanel'
import WorkPermitPanel from '../components/WorkPermitPanel'
import ShiftInfo from '../components/ShiftInfo'

export default function Dashboard() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-4)' }}>
      {/* Risk Gauge, Heatmap and Alert Center */}
      <div className="grid-3" style={{ alignItems: 'stretch' }}>
        <RiskGauge />
        <FacilityHeatmap />
        <AlertsPanel />
      </div>

      {/* Sensor panel */}
      <SensorPanel />

      {/* Equipment, Permits, Shift info */}
      <div className="grid-3">
        <EquipmentPanel />
        <WorkPermitPanel />
        <ShiftInfo />
      </div>
    </div>
  )
}
