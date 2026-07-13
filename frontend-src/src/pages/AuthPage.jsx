import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import LoginForm from '../components/LoginForm'
import SignupForm from '../components/SignupForm'
import ThemeToggle from '../components/ThemeToggle'

const glass = {
  background:    'var(--glass-bg)',
  border:        '1px solid var(--border)',
  backdropFilter:'blur(24px)',
  WebkitBackdropFilter: 'blur(24px)',
  boxShadow:     'var(--shadow)',
}

function SegmentedControl({ mode, onChange }) {
  return (
    <div
      role="tablist"
      className="flex p-1 rounded-xl mb-7"
      style={{ background: 'var(--glass-input)', border: '1px solid var(--border-s)' }}
    >
      {['login', 'signup'].map((m) => (
        <button
          key={m}
          role="tab"
          aria-selected={mode === m}
          onClick={() => onChange(m)}
          className="flex-1 py-2 text-sm font-medium rounded-lg transition-all duration-200 relative"
          style={{ color: mode === m ? 'var(--text-1)' : 'var(--text-2)' }}
        >
          {mode === m && (
            <motion.span
              layoutId="pill-active"
              className="absolute inset-0 rounded-lg"
              style={{ background: 'var(--pill-active)' }}
              transition={{ type: 'spring', stiffness: 300, damping: 25 }}
            />
          )}
          <span className="relative z-10">{m === 'login' ? 'Sign In' : 'Sign Up'}</span>
        </button>
      ))}
    </div>
  )
}

function Alert({ alert }) {
  if (!alert) return null
  const isSuccess = alert.type === 'success'
  return (
    <motion.div
      initial={{ opacity: 0, y: -6 }}
      animate={{ opacity: 1, y: 0 }}
      role="alert"
      className="mb-5 px-4 py-3 rounded-xl text-sm border"
      style={{
        background: isSuccess ? 'rgba(52,211,153,0.08)' : 'rgba(239,68,68,0.08)',
        borderColor: isSuccess ? 'rgba(52,211,153,0.2)' : 'rgba(239,68,68,0.2)',
        color: isSuccess ? '#34d399' : '#f87171',
      }}
    >
      {alert.message}
    </motion.div>
  )
}

export default function AuthPage() {
  const [mode, setMode] = useState('login')
  const [alert, setAlert] = useState(null)
  const navigate = useNavigate()

  if (localStorage.getItem('zylo_token')) {
    navigate('/chat', { replace: true })
    return null
  }

  function handleModeChange(next) { setAlert(null); setMode(next) }

  function handleLoginSuccess(data) {
    localStorage.setItem('zylo_token', data.access_token)
    localStorage.setItem('zylo_username', data.user.username)
    navigate('/chat', { replace: true })
  }

  function handleSignupSuccess(username) {
    setAlert({ type: 'success', message: `✓ Account "${username}" created — sign in now.` })
    setMode('login')
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4 relative overflow-hidden">
      {/* Theme toggle (fixed top-right) */}
      <div className="fixed top-5 right-5 z-50">
        <ThemeToggle />
      </div>

      <div className="relative w-full max-w-sm">
        {/* Brand */}
        <motion.header
          initial={{ opacity: 0, y: -16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ type: 'spring', stiffness: 150, damping: 15 }}
          className="flex items-center justify-center gap-2.5 mb-7"
        >
          <span className="text-2xl leading-none" aria-hidden>⚡</span>
          <span className="text-[1.65rem] font-bold bg-gradient-to-r from-indigo-400 to-violet-400 bg-clip-text text-transparent tracking-tight">
            Zylo
          </span>
        </motion.header>

        {/* Card */}
        <motion.main
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ type: 'spring', stiffness: 120, damping: 14, delay: 0.1 }}
          style={glass}
          className="rounded-3xl p-8"
        >
          <SegmentedControl mode={mode} onChange={handleModeChange} />

          <Alert alert={alert} />

          <AnimatePresence mode="wait">
            <motion.div
              key={mode}
              initial={{ opacity: 0, x: mode === 'login' ? -12 : 12 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: mode === 'login' ? 12 : -12 }}
              transition={{ duration: 0.18 }}
            >
              {mode === 'login' ? (
                <LoginForm
                  onSuccess={handleLoginSuccess}
                  onError={(msg) => setAlert({ type: 'error', message: msg })}
                />
              ) : (
                <SignupForm
                  onSuccess={handleSignupSuccess}
                  onError={(msg) => setAlert({ type: 'error', message: msg })}
                />
              )}
            </motion.div>
          </AnimatePresence>
        </motion.main>

        <p className="text-center text-xs mt-5" style={{ color: 'var(--text-3)' }}>
          Secured with JWT · Powered by FastAPI
        </p>
      </div>
    </div>
  )
}
