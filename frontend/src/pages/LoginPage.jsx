import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { useToast } from '../components/ui'

export default function LoginPage() {
  const [mode, setMode]         = useState('login')   // 'login' | 'signup'
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm]   = useState('')
  const [loading, setLoading]   = useState(false)
  const { login, signup }       = useAuth()
  const navigate                = useNavigate()
  const toast                   = useToast()

  async function handleSubmit(e) {
    e.preventDefault()
    setLoading(true)
    try {
      if (mode === 'login') {
        await login(username, password)
      } else {
        await signup(username, password, confirm)
      }
      navigate('/dashboard')
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{
      minHeight: '100dvh',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '2rem 1.5rem',
      gap: '2rem',
    }}>

      {/* Logo / wordmark */}
      <div style={{ textAlign: 'center' }}>
        <div style={{
          fontFamily: 'var(--font-mono)',
          fontSize: '0.7rem',
          color: 'var(--green)',
          letterSpacing: '0.3em',
          marginBottom: '0.5rem',
        }}>
          PERSONAL FINANCIAL MANAGER
        </div>
        <div style={{
          fontSize: '3rem',
          fontWeight: 800,
          letterSpacing: '-0.04em',
          lineHeight: 1,
          color: 'var(--text)',
        }}>
          PFM<span style={{ color: 'var(--green)' }}>.</span>
        </div>
      </div>

      {/* Card */}
      <div className="card fade-up" style={{ width: '100%', maxWidth: '380px' }}>

        {/* Mode toggle */}
        <div style={{
          display: 'flex',
          background: 'var(--bg3)',
          borderRadius: 'var(--radius)',
          padding: '3px',
          marginBottom: '1.5rem',
        }}>
          {['login', 'signup'].map(m => (
            <button
              key={m}
              onClick={() => setMode(m)}
              style={{
                flex: 1,
                padding: '0.5rem',
                borderRadius: 'calc(var(--radius) - 2px)',
                border: 'none',
                background: mode === m ? 'var(--green)' : 'transparent',
                color: mode === m ? '#0a0a0a' : 'var(--text2)',
                fontWeight: 700,
                fontSize: '0.8rem',
                textTransform: 'uppercase',
                letterSpacing: '0.06em',
                fontFamily: 'var(--font-ui)',
                transition: 'all 0.15s',
              }}
            >
              {m === 'login' ? 'Sign In' : 'Sign Up'}
            </button>
          ))}
        </div>

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div className="field">
            <label>Username</label>
            <input
              className="input"
              type="text"
              placeholder="Omar"
              value={username}
              onChange={e => setUsername(e.target.value)}
              required
              autoFocus
              autoCapitalize="words"
            />
          </div>

          <div className="field">
            <label>Password</label>
            <input
              className="input"
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={e => setPassword(e.target.value)}
              required
            />
          </div>

          {mode === 'signup' && (
            <div className="field">
              <label>Confirm Password</label>
              <input
                className="input"
                type="password"
                placeholder="••••••••"
                value={confirm}
                onChange={e => setConfirm(e.target.value)}
                required
              />
            </div>
          )}

          <button
            type="submit"
            className="btn btn-primary btn-full btn-lg"
            disabled={loading}
            style={{ marginTop: '0.5rem' }}
          >
            {loading
              ? <span className="spinner" style={{ width: 18, height: 18 }} />
              : mode === 'login' ? 'Sign In →' : 'Create Account →'
            }
          </button>
        </form>
      </div>

      <div style={{ color: 'var(--text3)', fontSize: '0.75rem', fontFamily: 'var(--font-mono)' }}>
        v2.0 · local · {new Date().getFullYear()}
      </div>
    </div>
  )
}
