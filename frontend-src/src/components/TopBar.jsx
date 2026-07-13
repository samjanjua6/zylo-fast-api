import ThemeToggle from './ThemeToggle'

const STATUS_CONFIG = {
  online:     { dot: 'bg-emerald-400 shadow-[0_0_0_3px_rgba(52,211,153,0.2)] animate-pulse', label: 'Connected' },
  connecting: { dot: 'bg-amber-400 animate-pulse', label: 'Connecting…' },
  offline:    { dot: 'bg-slate-500', label: 'Disconnected' },
  error:      { dot: 'bg-red-400', label: 'Error' },
  expired:    { dot: 'bg-red-400', label: 'Session expired' },
}

export default function TopBar({ username, wsStatus, onLogout }) {
  const { dot, label } = STATUS_CONFIG[wsStatus] ?? STATUS_CONFIG.offline
  const initial = username.charAt(0).toUpperCase()

  return (
    <header
      className="flex items-center gap-4 px-6 py-3.5 shrink-0"
      style={{
        background:    'var(--glass-bg)',
        borderBottom:  '1px solid var(--border)',
        backdropFilter:'blur(20px)',
        WebkitBackdropFilter: 'blur(20px)',
      }}
    >
      {/* Brand */}
      <div className="flex items-center gap-2.5">
        <span className="text-xl leading-none" aria-hidden>⚡</span>
        <span className="text-lg font-bold bg-gradient-to-r from-indigo-400 to-violet-400 bg-clip-text text-transparent tracking-tight">
          Zylo
        </span>
        <span className="w-px h-4 mx-1" style={{ background: 'var(--border)' }} aria-hidden />
        <span className="text-xs" style={{ color: 'var(--text-2)' }}>AI Chat</span>
      </div>

      {/* WS status */}
      <div className="flex items-center gap-2 ml-auto" aria-live="polite">
        <span className={`w-2 h-2 rounded-full shrink-0 ${dot}`} aria-hidden />
        <span className="text-xs" style={{ color: 'var(--text-2)' }}>{label}</span>
      </div>

      {/* Theme toggle + user */}
      <div className="flex items-center gap-3 ml-4">
        <ThemeToggle />

        <div
          className="w-7 h-7 rounded-full flex items-center justify-center text-xs font-semibold text-white shrink-0 uppercase"
          style={{ background: 'linear-gradient(135deg, #6366f1, #8b5cf6)' }}
          aria-hidden
        >
          {initial}
        </div>
        <span className="text-sm hidden sm:block" style={{ color: 'var(--text-1)' }}>{username}</span>

        <button
          onClick={onLogout}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs transition-all duration-150"
          style={{
            color:       'var(--text-2)',
            border:      '1px solid var(--border)',
            background:  'transparent',
          }}
          onMouseEnter={e => { e.currentTarget.style.color = '#f87171'; e.currentTarget.style.borderColor = 'rgba(248,113,113,0.3)' }}
          onMouseLeave={e => { e.currentTarget.style.color = 'var(--text-2)'; e.currentTarget.style.borderColor = 'var(--border)' }}
        >
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
            <polyline points="16 17 21 12 16 7" />
            <line x1="21" y1="12" x2="9" y2="12" />
          </svg>
          Sign out
        </button>
      </div>
    </header>
  )
}
