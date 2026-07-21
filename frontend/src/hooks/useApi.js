import { useEffect, useCallback } from 'react'
import { useSafety } from '../context/SafetyContext'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export function useApi(enablePolling = false) {
  const { dispatch } = useSafety()

  const fetchDashboard = useCallback(async () => {
    try {
      const res  = await fetch(`${API}/api/dashboard`)
      const data = await res.json()
      dispatch({ type: 'SET_DASHBOARD', payload: data })
    } catch (e) {
      console.warn('Dashboard fetch failed:', e)
    }
  }, [dispatch])

  const fetchAlerts = useCallback(async () => {
    try {
      const res  = await fetch(`${API}/api/alerts`)
      const data = await res.json()
      dispatch({ type: 'SET_ALERTS', payload: data.alerts || [] })
    } catch (e) {}
  }, [dispatch])

  const fetchReports = useCallback(async () => {
    try {
      const res  = await fetch(`${API}/api/incident-reports`)
      const data = await res.json()
      dispatch({ type: 'SET_REPORTS', payload: data.reports || [] })
    } catch (e) {}
  }, [dispatch])

  const acknowledgeAlert = useCallback(async (id) => {
    try {
      await fetch(`${API}/api/alerts/${id}/acknowledge`, { method: 'PATCH' })
      dispatch({ type: 'ACK_ALERT', payload: id })
    } catch (e) {}
  }, [dispatch])

  const generateReport = useCallback(async (zone = 'Zone-D', riskScore = 85) => {
    try {
      await fetch(`${API}/api/incident-report/generate`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ zone, risk_score: riskScore }),
      })
    } catch (e) {}
  }, [])

  const ingestSensor = useCallback(async (data) => {
    try {
      await fetch(`${API}/api/sensor-data`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify(data),
      })
    } catch (e) {}
  }, [])

  const getAuthToken = useCallback(async () => {
    let token = localStorage.getItem('token')
    if (token) return token
    try {
      const res = await fetch(`${API}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: 'admin', password: 'adminpass' })
      })
      const data = await res.json()
      if (data.access_token) {
        localStorage.setItem('token', data.access_token)
        return data.access_token
      }
    } catch (e) {
      console.error('Auto login failed', e)
    }
    return null
  }, [])

  const createPermit = useCallback(async (permitData) => {
    let token = await getAuthToken()
    const headers = { 'Content-Type': 'application/json' }
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }
    let res = await fetch(`${API}/api/permits`, {
      method: 'POST',
      headers,
      body: JSON.stringify(permitData)
    })
    if (res.status === 401) {
      localStorage.removeItem('token')
      const newToken = await getAuthToken()
      if (newToken) {
        const retryHeaders = {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${newToken}`
        }
        res = await fetch(`${API}/api/permits`, {
          method: 'POST',
          headers: retryHeaders,
          body: JSON.stringify(permitData)
        })
      }
    }
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}))
      throw new Error(errData.detail || 'Failed to create permit')
    }
    const newPermit = await res.json()
    await fetchDashboard()
    return newPermit;
  }, [getAuthToken, fetchDashboard])

  // Initial data load (only at layout root level)
  useEffect(() => {
    if (!enablePolling) return

    fetchDashboard()
    fetchAlerts()
    fetchReports()
    
    // Polling fallback every 10s (WebSocket is primary)
    const interval = setInterval(() => {
      fetchDashboard()
      fetchAlerts()
      fetchReports()
    }, 10000)
    return () => clearInterval(interval)
  }, [enablePolling, fetchDashboard, fetchAlerts, fetchReports])

  return { fetchDashboard, fetchAlerts, fetchReports, acknowledgeAlert, generateReport, ingestSensor, createPermit }
}
