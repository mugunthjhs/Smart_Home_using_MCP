import { useState } from 'react'
import RoomView from './RoomView'
import './Dashboard.css'

function Dashboard({ devices, rooms, stats }) {
  const [selectedRoom, setSelectedRoom] = useState('all')

  const filteredDevices = selectedRoom === 'all' 
    ? devices 
    : devices.filter(d => d.room === selectedRoom)

  return (
    <div className="dashboard">
      <aside className="sidebar">
        <div className="sidebar-section">
          <h2>Rooms</h2>
          <nav className="room-nav">
            <button 
              className={`room-btn ${selectedRoom === 'all' ? 'active' : ''}`}
              onClick={() => setSelectedRoom('all')}
            >
              <span className="room-icon">🏠</span>
              <span>All Rooms</span>
              <span className="badge">{devices.length}</span>
            </button>
            
            {rooms.map(room => {
              const roomDevices = devices.filter(d => d.room === room)
              const activeDevices = roomDevices.filter(d => 
                d.state === 'on' || d.state === 'open' || d.state === 'active'
              ).length
              
              return (
                <button
                  key={room}
                  className={`room-btn ${selectedRoom === room ? 'active' : ''}`}
                  onClick={() => setSelectedRoom(room)}
                >
                  <span className="room-icon">📍</span>
                  <span>{room.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}</span>
                  {activeDevices > 0 && (
                    <span className="badge active">{activeDevices}</span>
                  )}
                </button>
              )
            })}
          </nav>
        </div>
        
        {stats && (
          <div className="sidebar-section stats-section">
            <h2>System Stats</h2>
            <div className="stat-cards">
              <div className="stat-card">
                <div className="stat-icon">💡</div>
                <div className="stat-info">
                  <div className="stat-label">Lights</div>
                  <div className="stat-value">{stats.lights.on}/{stats.lights.total}</div>
                </div>
              </div>
              
              <div className="stat-card">
                <div className="stat-icon">🔒</div>
                <div className="stat-info">
                  <div className="stat-label">Doors Locked</div>
                  <div className="stat-value">{stats.doors.locked}/{stats.doors.total}</div>
                </div>
              </div>
              
              <div className="stat-card">
                <div className="stat-icon">📱</div>
                <div className="stat-info">
                  <div className="stat-label">Total Devices</div>
                  <div className="stat-value">{stats.total_devices}</div>
                </div>
              </div>
              
              {stats.active_mode && (
                <div className="stat-card mode">
                  <div className="stat-icon">🏡</div>
                  <div className="stat-info">
                    <div className="stat-label">Mode</div>
                    <div className="stat-value">{stats.active_mode.toUpperCase()}</div>
                  </div>
                </div>
              )}
            </div>
            
            {stats.garage_open && (
              <div className="alert-box">
                <span className="alert-icon">⚠️</span>
                <span>Garage door is open!</span>
              </div>
            )}
          </div>
        )}
      </aside>

      <main className="main-content">
        <div className="content-header">
          <h2>
            {selectedRoom === 'all' 
              ? 'All Devices' 
              : selectedRoom.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())
            }
          </h2>
          <div className="device-count">
            {filteredDevices.length} device{filteredDevices.length !== 1 ? 's' : ''}
          </div>
        </div>
        
        <RoomView devices={filteredDevices} viewMode={selectedRoom} />
      </main>
    </div>
  )
}

export default Dashboard