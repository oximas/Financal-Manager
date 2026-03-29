import { useEffect, useState } from 'react'

// ── Amount display ─────────────────────────────────────────────────────────
export function Amount({ value, size = 'md', showSign = true }) {
  const abs = Math.abs(value)
  const isPos = value >= 0
  const cls = isPos ? 'amount-positive' : 'amount-negative'
  const sign = showSign ? (isPos ? '+' : '-') : ''
  const fontSize = { sm: '0.875rem', md: '1rem', lg: '1.5rem', xl: '2rem' }[size]

  return (
    <span className={`mono ${cls}`} style={{ fontSize }}>
      {sign}{abs.toLocaleString('en-EG', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
    </span>
  )
}

// ── Transaction type badge ─────────────────────────────────────────────────
export function TxBadge({ type }) {
  const cls = {
    Deposit:  'badge badge-deposit',
    Withdraw: 'badge badge-withdraw',
    Transfer: 'badge badge-transfer',
    Loan:     'badge badge-loan',
  }[type] || 'badge'
  return <span className={cls}>{type}</span>
}

// ── Loading spinner ────────────────────────────────────────────────────────
export function Spinner({ size = 20 }) {
  return <span className="spinner" style={{ width: size, height: size }} />
}

// ── Full-page loader ───────────────────────────────────────────────────────
export function PageLoader() {
  return (
    <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <Spinner size={32} />
    </div>
  )
}

// ── Toast ──────────────────────────────────────────────────────────────────
let _setToast = null
export function useToast() {
  return {
    success: msg => _setToast({ msg, type: 'success' }),
    error:   msg => _setToast({ msg, type: 'error'   }),
  }
}

export function ToastContainer() {
  const [toast, setToast] = useState(null)
  _setToast = setToast

  useEffect(() => {
    if (!toast) return
    const t = setTimeout(() => setToast(null), 2800)
    return () => clearTimeout(t)
  }, [toast])

  if (!toast) return null
  return (
    <div className={`toast toast-${toast.type}`}>
      {toast.type === 'success' ? '✓' : '✗'} {toast.msg}
    </div>
  )
}

// ── Empty state ────────────────────────────────────────────────────────────
export function EmptyState({ icon, message }) {
  return (
    <div className="empty-state">
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1">
        {icon || <path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />}
      </svg>
      <p>{message || 'Nothing here yet'}</p>
    </div>
  )
}

// ── Currency display ───────────────────────────────────────────────────────
export function Currency({ amount, className = '', size = 'md' }) {
  const isNeg = amount < 0
  const cls = `mono ${isNeg ? 'amount-negative' : 'amount-positive'} ${className}`
  const fontSize = { sm: '0.8rem', md: '0.95rem', lg: '1.4rem', xl: '2.2rem' }[size]
  return (
    <span className={cls} style={{ fontSize }}>
      {isNeg ? '-' : '+'}{Math.abs(amount).toLocaleString('en-EG', { minimumFractionDigits: 2 })} EGP
    </span>
  )
}
