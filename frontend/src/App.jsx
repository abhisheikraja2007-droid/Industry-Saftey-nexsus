import { Routes, Route } from 'react-router-dom'
import { SafetyProvider } from './context/SafetyContext'
import { useWebSocket } from './hooks/useWebSocket'
import { useApi } from './hooks/useApi'

import TopBar from './components/TopBar'
import Sidebar from './components/Sidebar'
import Dashboard from './pages/Dashboard'
import Alerts from './pages/Alerts'
import PPEDetectionFeed from './pages/PPEDetectionFeed'
import IncidentReports from './pages/IncidentReports'
import HistoricalTrends from './pages/HistoricalTrends'
import WorkPermits from './pages/WorkPermits'

function AppContent() {
  // Init WebSocket and API polling integrations
  useWebSocket()
  useApi(true)

  return (
    <div className="app-layout">
      <div className="sidebar-wrapper">
        <Sidebar />
      </div>
      <div className="main-wrapper">
        <div className="topbar-wrapper">
          <TopBar />
        </div>
        <main className="main-content fade-in">
          <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/alerts" element={<Alerts />} />
          <Route path="/cctv" element={<PPEDetectionFeed />} />
          <Route path="/reports" element={<IncidentReports />} />
          <Route path="/history" element={<HistoricalTrends />} />
          <Route path="/permits" element={<WorkPermits />} />
        </Routes>
        </main>
      </div>
    </div>
  )
}

export default function App() {
  return (
    <SafetyProvider>
      <AppContent />
    </SafetyProvider>
  )
}
