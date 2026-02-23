import './DeviceCard.css'

function DeviceCard({ device }) {
  const properties = device.properties || {}
  
  const getDeviceIcon = (type) => {
    const icons = {
      light: '💡',
      temperature_sensor: '🌡️',
      motion_sensor: '👁️',
      blinds: '🪟',
      thermostat: '🌡️',
      garage: '🚗',
      lock: '🔒',
      fish_feeder: '🐠',
      ev_charger: '🔌',
      sprinkler: '💧',
      fan: '💨'
    }
    return icons[type] || '📱'
  }

  const getStateColor = (type, state) => {
    if (state === 'on' || state === 'open' || state === 'active' || state === 'unlocked') {
      return 'var(--success)'
    }
    if (state === 'off' || state === 'closed' || state === 'locked') {
      return 'var(--text-muted)'
    }
    if (state === 'feeding' || state === 'charging') {
      return 'var(--warning)'
    }
    if (state === 'partial') {
      return 'var(--accent)'
    }
    return 'var(--text-muted)'
  }

  const isActive = () => {
    const activeStates = ['on', 'open', 'active', 'motion', 'charging', 'feeding', 'unlocked']
    return activeStates.includes(device.state)
  }

  const renderDeviceDetails = () => {
    switch (device.type) {
      case 'light':
        return (
          <>
            {properties.brightness !== undefined && (
              <div className="detail">
                <span className="detail-label">Brightness:</span>
                <span className="detail-value">{properties.brightness}%</span>
                <div className="brightness-bar">
                  <div 
                    className="brightness-fill" 
                    style={{width: `${properties.brightness}%`}}
                  ></div>
                </div>
              </div>
            )}
            {properties.color_temp && (
              <div className="detail">
                <span className="detail-label">Color Temp:</span>
                <span className="detail-value">{properties.color_temp}K</span>
              </div>
            )}
          </>
        )
      
      case 'temperature_sensor':
        return (
          <div className="detail temperature">
            <div className="temperature-reading">
              {properties.value}°{properties.unit}
            </div>
          </div>
        )
      
      case 'blinds':
        return (
          <div className="detail">
            <span className="detail-label">Position:</span>
            <span className="detail-value">{properties.position}%</span>
            <div className="brightness-bar">
              <div 
                className="brightness-fill" 
                style={{width: `${properties.position}%`}}
              ></div>
            </div>
          </div>
        )
      
      case 'thermostat':
        return (
          <>
            <div className="detail">
              <span className="detail-label">Target:</span>
              <span className="detail-value">{properties.target_temp}°F</span>
            </div>
            <div className="detail">
              <span className="detail-label">Current:</span>
              <span className="detail-value">{properties.current_temp}°F</span>
            </div>
            <div className="detail">
              <span className="detail-label">Mode:</span>
              <span className="detail-value mode-badge">{properties.mode}</span>
            </div>
          </>
        )
      
      case 'fan':
        return (
          <div className="detail">
            <span className="detail-label">Speed:</span>
            <span className="detail-value">{properties.speed}/3</span>
          </div>
        )
      
      case 'ev_charger':
        return (
          <>
            <div className="detail">
              <span className="detail-label">Battery:</span>
              <span className="detail-value">{properties.battery_level}%</span>
              <div className="brightness-bar">
                <div 
                  className="brightness-fill" 
                  style={{width: `${properties.battery_level}%`}}
                ></div>
              </div>
            </div>
            <div className="detail">
              <span className="detail-value">
                {properties.charging ? '⚡ Charging...' : '🔌 Not charging'}
              </span>
            </div>
          </>
        )
      
      case 'fish_feeder':
        return properties.last_fed && (
          <div className="detail small">
            Last fed: {new Date(properties.last_fed).toLocaleTimeString()}
          </div>
        )
      
      case 'sprinkler':
        return properties.duration && device.state === 'on' && (
          <div className="detail">
            <span className="detail-label">Duration:</span>
            <span className="detail-value">{properties.duration} min</span>
          </div>
        )
      
      case 'motion_sensor':
        return properties.last_motion && (
          <div className="detail small">
            Last motion: {new Date(properties.last_motion).toLocaleTimeString()}
          </div>
        )
      
      default:
        return null
    }
  }

  return (
    <div className={`device-card ${isActive() ? 'active' : ''}`}>
      <div className="device-header">
        <div className="device-icon">{getDeviceIcon(device.type)}</div>
        <div 
          className="device-status-dot"
          style={{ backgroundColor: getStateColor(device.type, device.state) }}
        />
      </div>
      
      <div className="device-body">
        <h4 className="device-type">
          {device.type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
        </h4>
        
        <div 
          className="device-state"
          style={{ color: getStateColor(device.type, device.state) }}
        >
          {device.state.replace('_', ' ').toUpperCase()}
        </div>
        
        <div className="device-details">
          {renderDeviceDetails()}
        </div>
      </div>
      
      <div className="device-footer">
        <span className="device-id">{device.id}</span>
      </div>
    </div>
  )
}

export default DeviceCard