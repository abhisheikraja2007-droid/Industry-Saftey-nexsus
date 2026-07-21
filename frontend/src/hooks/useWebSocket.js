import { useEffect, useRef, useCallback } from 'react'
import { useSafety } from '../context/SafetyContext'

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws'
const RECONNECT_DELAY = 3000

export function useWebSocket() {
  const { dispatch } = useSafety()
  const wsRef       = useRef(null)
  const timerRef    = useRef(null)
  const pingRef     = useRef(null)

  const connect = useCallback(() => {
    try {
      const ws = new WebSocket(WS_URL)
      wsRef.current = ws

      ws.onopen = () => {
        dispatch({ type: 'SET_CONNECTED', payload: true })
        // Keepalive ping every 20s
        pingRef.current = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) ws.send('ping')
        }, 20000)
      }

      ws.onmessage = (e) => {
        try {
          const msg = JSON.parse(e.data)
          switch (msg.type) {
            case 'risk_score':
              dispatch({ type: 'RISK_SCORE', payload: msg.payload })
              break
            case 'sensor_update':
              dispatch({ type: 'SENSOR_UPDATE', payload: msg.payload })
              break
            case 'alert':
              dispatch({ type: 'ALERT', payload: msg.payload })
              break
            case 'equipment_update':
              dispatch({ type: 'EQUIPMENT_UPDATE', payload: msg.payload })
              break
            case 'report_ready':
              dispatch({ type: 'REPORT_READY', payload: msg.payload })
              break
            case 'permit_update':
              dispatch({ type: 'PERMIT_UPDATE', payload: msg.payload })
              break
            default:
              break
          }
        } catch (_) {}
      }

      ws.onclose = () => {
        dispatch({ type: 'SET_CONNECTED', payload: false })
        clearInterval(pingRef.current)
        // Auto-reconnect
        timerRef.current = setTimeout(connect, RECONNECT_DELAY)
      }

      ws.onerror = () => ws.close()
    } catch (e) {
      console.warn('WebSocket error:', e)
      timerRef.current = setTimeout(connect, RECONNECT_DELAY)
    }
  }, [dispatch])

  useEffect(() => {
    connect()
    return () => {
      clearTimeout(timerRef.current)
      clearInterval(pingRef.current)
      wsRef.current?.close()
    }
  }, [connect])
}
