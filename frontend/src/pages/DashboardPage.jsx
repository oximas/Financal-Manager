// frontend/src/pages/DashboardPage.jsx
import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../api/client'
import { useAuth } from '../contexts/AuthContext'
import { PageLoader, TxBadge, useToast, Spinner } from '../components/ui'
import { format } from 'date-fns'
import VaultManager from '../components/VaultManager'

// Safari rejects "2026-02-28 07:16:49" (space instead of T)
function parseDate(str) {
  if (!str) return new Date()
  return new Date(str.replace(' ', 'T'))
}

function VaultCard({ vault, currency, onClick }) {
  return (
    <button
      onClick={onClick}
      style={{
        background: 'var(--bg2)',
        border: '1px solid var(--border)',
        borderRadius: 'var(--radius2)',
        padding: '1rem',
        textAlign: 'left',
        cursor: 'pointer',
        transition: 'border-color 0.15s, transform 0.15s',
        minWidth: '140px',
        flex: '0 0 auto',
      }}
      onMouseEnter={e => { e.currentTarget.style.borderColor = 'var(--green)'; e.currentTarget.style.transform = 'translateY(-2px)' }}
      onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--border)'; e.currentTarget.style.transform = 'translateY(0)' }}
    >
      <div style={{ fontSize: '0.7rem', color: 'var(--text2)', fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: '0.5rem' }}>
        {vault.vault_name}
      </div>
      <div className="mono" style={{
        fontSize: '1.1rem', fontWeight: 700,
        color: vault.balance > 0 ? 'var(--green)' : vault.balance < 0 ? 'var(--red)' : 'var(--text2)',
      }}>
        {vault.balance.toLocaleString('en-EG', { minimumFractionDigits: 2 })}
      </div>
      <div style={{ fontSize: '0.65rem', color: 'var(--text3)', marginTop: '0.2rem' }}>{currency}</div>
    </button>
  )
}

function TxRow({ tx }) {
  const isDeposit  = tx.transaction_type === 'Deposit'
  const isWithdraw = tx.transaction_type === 'Withdraw'
  const amountColor = isDeposit ? 'var(--green)' : isWithdraw ? 'var(--red)' : 'var(--yellow)'
  const sign = isDeposit ? '+' : isWithdraw ? '-' : '↔'

  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: '0.75rem',
      padding: '0.75rem 0', borderBottom: '1px solid var(--border)',
    }}>
      <div style={{
        width: 36, height: 36, borderRadius: '50%', flexShrink: 0,
        background: isDeposit ? 'rgba(0,255,198,0.1)' : isWithdraw ? 'rgba(255,77,109,0.1)' : 'rgba(255,209,102,0.1)',
        display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1rem',
      }}>
        {isDeposit ? '↓' : isWithdraw ? '↑' : '↔'}
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontSize: '0.875rem', fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {tx.description || '—'}
        </div>
        <div style={{ fontSize: '0.7rem', color: 'var(--text2)', marginTop: '0.1rem' }}>
          {tx.vault_name} · {tx.category_name || 'Uncategorized'}
        </div>
      </div>
      <div style={{ textAlign: 'right', flexShrink: 0 }}>
        <div className="mono" style={{ fontSize: '0.9rem', fontWeight: 700, color: amountColor }}>
          {sign}{Math.abs(tx.amount).toLocaleString('en-EG', { minimumFractionDigits: 2 })}
        </div>
        <div style={{ fontSize: '0.65rem', color: 'var(--text3)', marginTop: '0.1rem' }}>
          {format(parseDate(tx.date), 'MMM d')}
        </div>
      </div>
    </div>
  )
}

// ── Undo confirm inline widget ─────────────────────────────────────────────
function UndoButton({ tx, onDone }) {
  const [mode, setMode] = useState('idle')   // 'idle' | 'confirm' | 'busy'
  const toast = useToast()

  if (!tx) return null

  async function doUndo() {
    setMode('busy')
    try {
      await api.delete(`/transactions/${tx.transaction_id}`)
      toast.success(`Undid: ${tx.description || tx.transaction_type}`)
      onDone()
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Undo failed')
      setMode('idle')
    }
  }

  if (mode === 'idle') {
    return (
      <button
        className="btn btn-ghost btn-sm"
        onClick={() => setMode('confirm')}
        style={{ fontSize: '0.72rem', color: 'var(--text3)', border: '1px solid var(--border)' }}
      >
        ↩ Undo last
      </button>
    )
  }

  if (mode === 'confirm') {
    return (
      <span style={{ display: 'inline-flex', gap: '0.4rem', alignItems: 'center' }}>
        <span style={{ fontSize: '0.72rem', color: 'var(--text2)' }}>
          Delete <strong style={{ color: 'var(--text)' }}>{tx.description || tx.transaction_type}</strong>?
        </span>
        <button
          onClick={doUndo}
          style={{ background: 'var(--red)', color: '#fff', border: 'none', borderRadius: 'var(--radius)', padding: '0.2rem 0.6rem', fontSize: '0.72rem', fontWeight: 700, cursor: 'pointer', fontFamily: 'var(--font-ui)' }}
        >Yes</button>
        <button
          onClick={() => setMode('idle')}
          style={{ background: 'none', border: '1px solid var(--border)', borderRadius: 'var(--radius)', padding: '0.2rem 0.5rem', fontSize: '0.72rem', color: 'var(--text2)', cursor: 'pointer', fontFamily: 'var(--font-ui)' }}
        >No</button>
      </span>
    )
  }

  // busy
  return <Spinner size={16} />
}

// ── Main page ──────────────────────────────────────────────────────────────
export default function DashboardPage() {
  const [data, setData]             = useState(null)
  const [loading, setLoading]       = useState(true)
  const [showVaultMgr, setShowVaultMgr] = useState(false)
  const { user, logout }            = useAuth()
  const navigate              = useNavigate()
  const toast                 = useToast()
  const currency              = localStorage.getItem('pfm_currency') || 'EGP'

  const load = useCallback(() => {
    setLoading(true)
    api.get('/dashboard')
      .then(r => setData(r.data))
      .catch(() => toast.error('Failed to load dashboard'))
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => { load() }, [load])

  if (loading) return <PageLoader />

  const { total_balance, vaults, recent_transactions, monthly_summary } = data || {}
  const lastTx = recent_transactions?.[0] || null

  return (
    <div className="page fade-up">

      {/* Header */}
      <div className="page-header">
        <div>
          <div style={{ fontSize: '0.7rem', color: 'var(--text2)', fontFamily: 'var(--font-mono)', letterSpacing: '0.1em' }}>
            WELCOME BACK
          </div>
          <div style={{ fontSize: '1.2rem', fontWeight: 800, letterSpacing: '-0.02em' }}>
            {user?.username}
          </div>
        </div>
        <button className="btn btn-ghost btn-sm" onClick={() => { logout(); navigate('/login') }}>
          Sign out
        </button>
      </div>

      {/* Total balance hero */}
      <div style={{
        background: 'linear-gradient(135deg, var(--bg2) 0%, #0f1f17 100%)',
        border: '1px solid var(--border)',
        borderRadius: 'var(--radius2)',
        padding: '1.5rem',
        marginBottom: '1.25rem',
        position: 'relative',
        overflow: 'hidden',
      }}>
        <div style={{
          position: 'absolute', top: -40, right: -40,
          width: 120, height: 120,
          background: 'radial-gradient(circle, rgba(0,255,198,0.12) 0%, transparent 70%)',
          pointerEvents: 'none',
        }} />
        <div style={{ fontSize: '0.7rem', color: 'var(--text2)', fontFamily: 'var(--font-mono)', letterSpacing: '0.12em', marginBottom: '0.5rem' }}>
          TOTAL BALANCE
        </div>
        <div className="mono glow" style={{ fontSize: '2.4rem', fontWeight: 700, color: 'var(--green)', lineHeight: 1 }}>
          {total_balance?.toLocaleString('en-EG', { minimumFractionDigits: 2 })}
        </div>
        <div style={{ fontSize: '0.75rem', color: 'var(--text3)', marginTop: '0.4rem' }}>{currency}</div>
      </div>

      {/* Monthly summary */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '0.5rem', marginBottom: '1.25rem' }}>
        {[
          { label: 'Income',   value: monthly_summary?.income,   color: 'var(--green)' },
          { label: 'Expenses', value: monthly_summary?.expenses, color: 'var(--red)' },
          { label: 'Net',      value: monthly_summary?.net,      color: (monthly_summary?.net ?? 0) >= 0 ? 'var(--green)' : 'var(--red)' },
        ].map(item => (
          <div key={item.label} className="card" style={{ padding: '0.75rem', textAlign: 'center' }}>
            <div style={{ fontSize: '0.6rem', color: 'var(--text2)', fontFamily: 'var(--font-mono)', letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: '0.4rem' }}>
              {item.label}
            </div>
            <div className="mono" style={{ fontSize: '0.85rem', fontWeight: 700, color: item.color }}>
              {(item.value || 0).toLocaleString('en-EG', { minimumFractionDigits: 0 })}
            </div>
          </div>
        ))}
      </div>

      {/* Vaults horizontal scroll */}
      <div style={{ marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
          <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text2)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
            Vaults
          </div>
          <button className="btn btn-ghost btn-sm" onClick={() => setShowVaultMgr(true)}>Manage</button>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem', overflowX: 'auto', paddingBottom: '0.5rem' }}>
          {vaults?.map(v => (
            <VaultCard key={v.vault_id} vault={v} currency={currency}
              onClick={() => navigate(`/transactions?vault=${v.vault_name}`)} />
          ))}
        </div>
      </div>

      {/* Quick actions */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '0.5rem', marginBottom: '1.5rem' }}>
        {[
          { label: 'Deposit',  icon: '↓', path: '/add?type=deposit'  },
          { label: 'Withdraw', icon: '↑', path: '/add?type=withdraw' },
          { label: 'Transfer', icon: '↔', path: '/add?type=transfer' },
        ].map(a => (
          <button
            key={a.label}
            onClick={() => navigate(a.path)}
            style={{
              background: 'var(--bg2)', border: '1px solid var(--border)',
              borderRadius: 'var(--radius)', padding: '0.875rem 0.5rem',
              color: 'var(--text)', display: 'flex', flexDirection: 'column',
              alignItems: 'center', gap: '0.4rem', fontSize: '1.2rem',
              cursor: 'pointer', transition: 'border-color 0.15s, background 0.15s',
              fontFamily: 'var(--font-ui)',
            }}
            onMouseEnter={e => { e.currentTarget.style.borderColor = 'var(--green)'; e.currentTarget.style.background = 'var(--green-dim)' }}
            onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--border)'; e.currentTarget.style.background = 'var(--bg2)' }}
          >
            <span>{a.icon}</span>
            <span style={{ fontSize: '0.7rem', fontWeight: 600, letterSpacing: '0.04em', textTransform: 'uppercase', color: 'var(--text2)' }}>{a.label}</span>
          </button>
        ))}
      </div>

      {/* Recent transactions */}
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem', flexWrap: 'wrap', gap: '0.4rem' }}>
          <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text2)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
            Recent
          </div>
          <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', flexWrap: 'wrap' }}>
            <UndoButton tx={lastTx} onDone={load} />
            <button className="btn btn-ghost btn-sm" onClick={() => navigate('/transactions')}>See all</button>
          </div>
        </div>

        {recent_transactions?.length === 0 && (
          <div style={{ color: 'var(--text3)', fontSize: '0.875rem', padding: '2rem 0', textAlign: 'center' }}>
            No transactions yet — add your first one!
          </div>
        )}

        {recent_transactions?.map(tx => (
          <TxRow key={tx.transaction_id} tx={tx} />
        ))}
      </div>

      {showVaultMgr && (
        <VaultManager
          onClose={() => setShowVaultMgr(false)}
          onChanged={load}
        />
      )}

    </div>
  )
}
