import React from 'react'

export default function Sidebar({
  sessions,
  activeSessionId,
  onSelectSession,
  onNewSession,
}) {
  return (
    <div
      className="flex flex-col h-full w-64 shrink-0 transition-all duration-300 hidden md:flex"
      style={{
        background: 'var(--glass-bg)',
        borderRight: '1px solid var(--border)',
        backdropFilter: 'blur(20px)',
        WebkitBackdropFilter: 'blur(20px)',
      }}
    >
      <div className="p-4 flex items-center justify-between" style={{ borderBottom: '1px solid var(--border)' }}>
        <h2 className="text-sm font-semibold tracking-wide" style={{ color: 'var(--text-1)' }}>Chat History</h2>
        <button
          onClick={onNewSession}
          className="p-1.5 rounded-md hover:bg-black/5 dark:hover:bg-white/10 transition-colors"
          title="New Chat"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ color: 'var(--text-1)' }}>
            <line x1="12" y1="5" x2="12" y2="19" />
            <line x1="5" y1="12" x2="19" y2="12" />
          </svg>
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-2 space-y-1">
        {sessions.map(session => (
          <button
            key={session.id}
            onClick={() => onSelectSession(session.id)}
            className="w-full text-left px-3 py-2 rounded-lg transition-colors text-sm truncate"
            style={{
              background: activeSessionId === session.id ? 'var(--input-bg)' : 'transparent',
              color: activeSessionId === session.id ? 'var(--text-1)' : 'var(--text-2)',
              border: activeSessionId === session.id ? '1px solid var(--border)' : '1px solid transparent'
            }}
          >
            {session.title || "New Chat"}
            <div className="text-[10px] opacity-60 mt-0.5">
              {new Date(session.created_at).toLocaleDateString()}
            </div>
          </button>
        ))}
        {sessions.length === 0 && (
          <div className="text-xs text-center py-4" style={{ color: 'var(--text-2)' }}>
            No chat history
          </div>
        )}
      </div>
    </div>
  )
}
