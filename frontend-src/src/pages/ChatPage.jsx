import { useState, useEffect, useRef, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import TopBar from '../components/TopBar'
import MessageList from '../components/MessageList'
import ChatInput from '../components/ChatInput'
import Sidebar from '../components/Sidebar'

const DONE_SENTINEL = '[DONE]'

function useWebSocket(token, sessionId, onChunk, onStatusChange) {
  const wsRef = useRef(null)
  const reconnectTimer = useRef(null)

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.close(1000)
    }
    
    if (!token) return

    onStatusChange('connecting')

    const proto = location.protocol === 'https:' ? 'wss:' : 'ws:'
    let url = `${proto}//${location.host}/ws/chat?token=${encodeURIComponent(token)}`
    if (sessionId) {
      url += `&session_id=${sessionId}`
    }
    
    const ws = new WebSocket(url)
    wsRef.current = ws

    ws.onopen    = () => onStatusChange('online')
    ws.onmessage = (e) => onChunk(e.data)
    ws.onclose   = (e) => {
      onStatusChange('offline')
      if (e.code === 1008) {
        onStatusChange('expired')
      } else if (e.code !== 1000) {
        reconnectTimer.current = setTimeout(connect, 3000)
      }
    }
    ws.onerror = () => onStatusChange('error')
  }, [token, sessionId, onChunk, onStatusChange])

  useEffect(() => {
    connect()
    return () => {
      clearTimeout(reconnectTimer.current)
      wsRef.current?.close(1000)
    }
  }, [connect])

  const send = useCallback((text) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(text)
    }
  }, [])

  return { send }
}

export default function ChatPage() {
  const navigate = useNavigate()
  const token    = localStorage.getItem('zylo_token') ?? ''
  const username = localStorage.getItem('zylo_username') ?? 'You'

  const [messages, setMessages]     = useState([])
  const [wsStatus, setWsStatus]     = useState('offline')
  const [isStreaming, setIsStreaming] = useState(false)
  const [sessions, setSessions] = useState([])
  const [activeSessionId, setActiveSessionId] = useState(null)

  // Fetch all sessions on mount
  const fetchSessions = useCallback(async () => {
    try {
      const res = await fetch('/api/chat/sessions', {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (res.ok) {
        const data = await res.json()
        setSessions(data)
        if (data.length > 0 && !activeSessionId) {
          setActiveSessionId(data[0].id)
        }
      }
    } catch (err) {
      console.error("Failed to fetch sessions", err)
    }
  }, [token, activeSessionId])

  useEffect(() => {
    fetchSessions()
  }, [fetchSessions])

  // Fetch messages when active session changes
  useEffect(() => {
    if (!activeSessionId) {
      setMessages([])
      return
    }
    
    async function fetchMessages() {
      try {
        const res = await fetch(`/api/chat/sessions/${activeSessionId}/messages`, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
        if (res.ok) {
          const data = await res.json()
          setMessages(data.map(m => ({
            id: m.id,
            text: m.content,
            type: m.role === 'model' ? 'bot' : 'user',
            streaming: false
          })))
        }
      } catch (err) {
        console.error("Failed to fetch messages", err)
      }
    }
    fetchMessages()
  }, [activeSessionId, token])

  const createNewSession = () => {
    setActiveSessionId(null)
    setMessages([])
  }

  // Append a brand-new message bubble
  const addMessage = useCallback((text, type) => {
    setMessages(prev => [...prev, { id: Date.now() + Math.random(), text, type, streaming: false }])
  }, [])

  // Start a streaming bot bubble (empty, will be filled token-by-token)
  const startBotStream = useCallback(() => {
    const id = Date.now() + Math.random()
    setMessages(prev => [...prev, { id, text: '', type: 'bot', streaming: true }])
    setIsStreaming(true)
    return id
  }, [])

  // Append a token chunk to the last streaming bubble
  const appendToLastBot = useCallback((chunk) => {
    setMessages(prev => {
      const copy = [...prev]
      const last = copy[copy.length - 1]
      if (last?.streaming) {
        copy[copy.length - 1] = { ...last, text: last.text + chunk }
      }
      return copy
    })
  }, [])

  // Mark the last streaming bubble as complete
  const finishBotStream = useCallback(() => {
    setMessages(prev => {
      const copy = [...prev]
      const last = copy[copy.length - 1]
      if (last?.streaming) {
        copy[copy.length - 1] = { ...last, streaming: false }
      }
      return copy
    })
    setIsStreaming(false)
  }, [])

  // Track whether we have an active streaming bubble
  const streamingRef = useRef(false)

  const handleChunk = useCallback((data) => {
    if (data.startsWith('[SESSION_ID:')) {
      const newId = parseInt(data.replace('[SESSION_ID:', '').replace(']', ''))
      setActiveSessionId(newId)
      fetchSessions() // to refresh sidebar
      return
    }
    // First non-DONE message after quiet period → start a new bubble
    if (data === DONE_SENTINEL) {
      finishBotStream()
      streamingRef.current = false
      return
    }
    if (!streamingRef.current) {
      startBotStream()
      streamingRef.current = true
    }
    appendToLastBot(data)
  }, [startBotStream, appendToLastBot, finishBotStream, fetchSessions])

  const handleStatus = useCallback((status) => {
    setWsStatus(status)
    if (status === 'expired') {
      addMessage('⚠ Session expired. Redirecting to login…', 'system')
      localStorage.removeItem('zylo_token')
      localStorage.removeItem('zylo_username')
      setTimeout(() => navigate('/login', { replace: true }), 1800)
    } else if (status === 'error') {
      addMessage('Connection error — check the backend.', 'system')
    }
  }, [addMessage, navigate])

  const { send } = useWebSocket(token, activeSessionId, handleChunk, handleStatus)

  function handleSend(text) {
    if (!text.trim() || wsStatus !== 'online' || isStreaming) return
    streamingRef.current = false
    addMessage(text, 'user')
    send(text)
  }

  function handleLogout() {
    localStorage.removeItem('zylo_token')
    localStorage.removeItem('zylo_username')
    navigate('/login', { replace: true })
  }

  return (
    <div className="flex flex-col h-screen overflow-hidden">
      <TopBar username={username} wsStatus={wsStatus} onLogout={handleLogout} />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar
          sessions={sessions}
          activeSessionId={activeSessionId}
          onSelectSession={setActiveSessionId}
          onNewSession={createNewSession}
        />
        <div className="flex flex-col flex-1 min-w-0">
          <MessageList messages={messages} username={username} />
          <ChatInput onSend={handleSend} disabled={wsStatus !== 'online'} isStreaming={isStreaming} />
        </div>
      </div>
    </div>
  )
}
