import { useState, useEffect, useRef, useCallback } from 'react'

function useWebSocket(url) {
  const [lastMessage, setLastMessage] = useState(null)
  const [isConnected, setIsConnected] = useState(false)
  const ws = useRef(null)
  const reconnectTimeout = useRef(null)

  const connect = useCallback(() => {
    try {
      ws.current = new WebSocket(url)

      ws.current.onopen = () => {
        console.log('✅ WebSocket connected')
        setIsConnected(true)
      }

      ws.current.onmessage = (event) => {
        const data = JSON.parse(event.data)
        console.log('📨 WebSocket message:', data)
        setLastMessage(data)
      }

      ws.current.onerror = (error) => {
        console.error('❌ WebSocket error:', error)
      }

      ws.current.onclose = () => {
        console.log('🔌 WebSocket disconnected')
        setIsConnected(false)
        
        // Attempt to reconnect after 3 seconds
        reconnectTimeout.current = setTimeout(() => {
          console.log('🔄 Attempting to reconnect...')
          connect()
        }, 3000)
      }
    } catch (error) {
      console.error('Failed to connect:', error)
    }
  }, [url])

  useEffect(() => {
    connect()

    // Cleanup on unmount
    return () => {
      if (reconnectTimeout.current) {
        clearTimeout(reconnectTimeout.current)
      }
      if (ws.current) {
        ws.current.close()
      }
    }
  }, [connect])

  return { lastMessage, isConnected }
}

export default useWebSocket