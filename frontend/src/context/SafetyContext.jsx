import { createContext, useContext, useReducer, useCallback } from 'react'

const SafetyContext = createContext(null)

const initialState = {
  riskScore:      0,
  riskLevel:      'SAFE',
  riskColor:      '#22c55e',
  alerts:         [],
  sensors:        {},
  equipment:      {},
  permits:        [],
  shift:          null,
  reports:        [],
  zoneBreakdown:  {},
  triggeredRules: [],
  connected:      false,
  lastUpdate:     null,
}

function reducer(state, action) {
  switch (action.type) {
    case 'SET_CONNECTED':
      return { ...state, connected: action.payload }
    case 'RISK_SCORE':
      return {
        ...state,
        riskScore:      action.payload.risk_score,
        riskLevel:      action.payload.risk_level,
        riskColor:      action.payload.color,
        triggeredRules: action.payload.triggered_rules || [],
        lastUpdate:     action.payload.timestamp,
      }
    case 'SENSOR_UPDATE': {
      const { zone, sensor_type, value } = action.payload
      return {
        ...state,
        sensors: {
          ...state.sensors,
          [zone]: { ...(state.sensors[zone] || {}), [sensor_type]: value },
        },
        lastUpdate: action.payload.timestamp,
      }
    }
    case 'ALERT': {
      const newAlert = { ...action.payload, id: Date.now().toString() }
      return { ...state, alerts: [newAlert, ...state.alerts].slice(0, 50) }
    }
    case 'EQUIPMENT_UPDATE': {
      const eq = action.payload
      return {
        ...state,
        equipment: { ...state.equipment, [eq.equipment_id]: eq },
      }
    }
    case 'REPORT_READY':
      return { ...state, reports: [action.payload, ...state.reports].slice(0, 30) }
    case 'SET_DASHBOARD':
      return {
        ...state,
        riskScore:      action.payload.global_risk_score,
        riskLevel:      action.payload.risk_level,
        riskColor:      action.payload.color,
        zoneBreakdown:  action.payload.zone_risks || {},
        triggeredRules: action.payload.triggered_rules || [],
        shift:          action.payload.current_shift,
        permits:        action.payload.permits || [],
        lastUpdate:     action.payload.last_updated,
      }
    case 'SET_ALERTS':
      return { ...state, alerts: action.payload }
    case 'SET_REPORTS':
      return { ...state, reports: action.payload }
    case 'PERMIT_UPDATE':
      return { ...state, permits: action.payload }
    case 'ACK_ALERT':
      return {
        ...state,
        alerts: state.alerts.map(a =>
          a.id === action.payload ? { ...a, acknowledged: true } : a
        ),
      }
    default:
      return state
  }
}

export function SafetyProvider({ children }) {
  const [state, dispatch] = useReducer(reducer, initialState)
  const send = useCallback((action) => dispatch(action), [])
  return (
    <SafetyContext.Provider value={{ state, dispatch: send }}>
      {children}
    </SafetyContext.Provider>
  )
}

export function useSafety() {
  return useContext(SafetyContext)
}
