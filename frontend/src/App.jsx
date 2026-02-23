import { useState, useEffect } from 'react'
import './App.css'
import Dashboard from './components/Dashboard'
import useWebSocket from './hooks/useWebSocket'

const API_URL = 'http://localhost:8000'
const WS_URL = 'ws://localhost:8000/ws'

function App() {
  const [devices, setDevices] = useState([])
  const [rooms, setRooms] = useState([])
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)

  // Connect to WebSocket
  const { lastMessage, isConnected } = useWebSocket(WS_URL)

  // Fetch initial data
  useEffect(() => {
    fetchDevices()
    fetchRooms()
    fetchStats()
  }, [])

  // Handle WebSocket updates
  useEffect(() => {
    if (lastMessage) {
      handleRealtimeUpdate(lastMessage)
    }
  }, [lastMessage])

  const fetchDevices = async () => {
    try {
      const response = await fetch(`${API_URL}/api/devices`)
      const data = await response.json()
      setDevices(data)
      setLoading(false)
    } catch (error) {
      console.error('Error fetching devices:', error)
      setLoading(false)
    }
  }

  const fetchRooms = async () => {
    try {
      const response = await fetch(`${API_URL}/api/rooms`)
      const data = await response.json()
      setRooms(data)
    } catch (error) {
      console.error('Error fetching rooms:', error)
    }
  }

  const fetchStats = async () => {
    try {
      const response = await fetch(`${API_URL}/api/stats`)
      const data = await response.json()
      setStats(data)
    } catch (error) {
      console.error('Error fetching stats:', error)
    }
  }

  const handleRealtimeUpdate = (update) => {
    console.log('Handling update:', update)
    
    if (update.type === 'device_update') {
      setDevices(prevDevices => {
        return prevDevices.map(device => {
          // Update specific device
          if (update.device_id && device.id === update.device_id) {
            return {
              ...device,
              state: update.state || device.state,
              properties: update.properties || device.properties
            }
          }
          
          // Update by room and type
          if (update.room && update.device_type && 
              device.room === update.room && 
              device.type === update.device_type) {
            return {
              ...device,
              state: update.state || device.state,
              properties: update.properties || device.properties
            }
          }
          
          return device
        })
      })
      
      // Refresh stats
      fetchStats()
    } else if (update.type === 'full_refresh') {
      // Full refresh after mode change
      fetchDevices()
      fetchStats()
    } else if (update.type === 'mode_change') {
      // Mode changed
      console.log('Mode changed:', update.mode)
      fetchStats()
    }
  }

  if (loading) {
    return (
      <div className="loading">
        <div className="loading-spinner"></div>
        <p>Loading home automation system...</p>
      </div>
    )
  }

  return (
    <div className="App">
      <header>
        <div className="header-content">
          <h1>🏠 Smart Home Dashboard</h1>
          <div className="header-info">
            <div className="connection-status">
              <span className={`status-dot ${isConnected ? 'connected' : 'disconnected'}`}></span>
              <span>{isConnected ? 'Connected' : 'Disconnected'}</span>
            </div>
            {stats && (
              <div className="quick-stats">
                <span className="stat">💡 {stats.lights.on}/{stats.lights.total}</span>
                <span className="stat">🔒 {stats.doors.locked}/{stats.doors.total}</span>
                {stats.garage_open && <span className="stat alert">⚠️ Garage Open</span>}
              </div>
            )}
          </div>
        </div>
      </header>
      
      <Dashboard devices={devices} rooms={rooms} stats={stats} />
    </div>
  )
}

export default App