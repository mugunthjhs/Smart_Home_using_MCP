import DeviceCard from './DeviceCard'
import './RoomView.css'

function RoomView({ devices, viewMode }) {
  if (devices.length === 0) {
    return (
      <div className="empty-state">
        <div className="empty-icon">📭</div>
        <h3>No devices found</h3>
        <p>There are no devices in this location.</p>
      </div>
    )
  }

  // If viewing all rooms, group by room
  if (viewMode === 'all') {
    const devicesByRoom = devices.reduce((acc, device) => {
      const room = device.room || 'Other'
      if (!acc[room]) acc[room] = []
      acc[room].push(device)
      return acc
    }, {})

    return (
      <div className="room-view">
        {Object.entries(devicesByRoom).sort().map(([room, roomDevices]) => (
          <div key={room} className="room-section">
            <h3 className="room-title">
              <span className="room-title-icon">📍</span>
              {room.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
              <span className="room-device-count">{roomDevices.length}</span>
            </h3>
            <div className="device-grid">
              {roomDevices.map(device => (
                <DeviceCard key={device.id} device={device} />
              ))}
            </div>
          </div>
        ))}
      </div>
    )
  }

  // Single room view
  return (
    <div className="room-view">
      <div className="device-grid">
        {devices.map(device => (
          <DeviceCard key={device.id} device={device} />
        ))}
      </div>
    </div>
  )
}

export default RoomView