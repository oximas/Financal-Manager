// frontend/src/pages/TransactionsPage.jsx
import { useState, useEffect, useCallback } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { createPortal } from 'react-dom'
import api from '../api/client'
import { PageLoader, TxBadge, useToast, Spinner } from '../components/ui'
import { format } from 'date-fns'

// Safari and some mobile browsers reject "2026-02-28 07:16:49" (space instead of T)
function parseDate(str) {
  if (!str) return new Date()
  return new Date(str.replace(' ', 'T'))
}

function TxRow({ tx, onTap }) {
  const isDeposit  = tx.transaction_type === 'Deposit'
  const isWithdraw = tx.transaction_type === 'Withdraw'
  const amountColor = isDeposit ? 'var(--green)' : isWithdraw ? 'var(--red)' : 'var(--yellow)'
  const sign = isDeposit ? '+' : isWithdraw ? '-' : '↔'

  return (
    <button
      onClick={() => onTap(tx)}
      style={{
        display: 'flex', alignItems: 'center', gap: '0.75rem',
        padding: '0.875rem 0',
        borderBottom: '1px solid var(--border)',
        width: '100%', background: 'none', border: 'none',
        borderBottom: '1px solid var(--border)',
        color: 'var(--text)', textAlign: 'left', cursor: 'pointer',
      }}
    >
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
          {tx.vault_name} · {tx.category_name || '—'} · {format(parseDate(tx.date), 'MMM d, yyyy')}
        </div>
        {tx.comment && (
          <div style={{ fontSize: '0.7rem', color: 'var(--text3)', marginTop: '0.1rem', fontStyle: 'italic' }}>
            {tx.comment}
          </div>
        )}
        {tx.tags?.length > 0 && (
          <div style={{ display: 'flex', gap: '0.25rem', flexWrap: 'wrap', marginTop: '0.2rem' }}>
            {tx.tags.map(t => (
              <span key={t.tag_id} style={{
                background: 'var(--bg3)', border: '1px solid var(--border)',
                borderRadius: '4px', padding: '0 0.35rem',
                fontSize: '0.6rem', color: 'var(--text3)',
              }}>{t.tag_name}</span>
            ))}
          </div>
        )}
      </div>
      <div style={{ textAlign: 'right', flexShrink: 0 }}>
        <div className="mono" style={{ fontSize: '0.9rem', fontWeight: 700, color: amountColor }}>
          {sign}{Math.abs(tx.amount).toLocaleString('en-EG', { minimumFractionDigits: 2 })}
        </div>
        {tx.quantity && (
          <div style={{ fontSize: '0.65rem', color: 'var(--text3)' }}>
            ×{tx.quantity}
          </div>
        )}
      </div>
    </button>
  )
}

// ── Transaction detail modal ───────────────────────────────────────────────
// Rendered via createPortal so position:fixed works correctly even when
// parent .page div has an active CSS transform (from fade-up animation).
function TxModal({ tx, onClose, onUpdated, onDeleted }) {
  const [mode, setMode]         = useState('view')   // 'view' | 'edit' | 'confirm-delete'
  const [description, setDesc]  = useState(tx.description || '')
  const [comment, setComment]   = useState(tx.comment || '')
  const [busy, setBusy]         = useState(false)
  const toast                   = useToast()

  async function save() {
    setBusy(true)
    try {
      const res = await api.patch(`/transactions/${tx.transaction_id}`, { description, comment: comment || null })
      toast.success('Updated')
      onUpdated(res.data)
      setMode('view')
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Update failed')
    } finally { setBusy(false) }
  }

  async function doDelete() {
    setBusy(true)
    try {
      await api.delete(`/transactions/${tx.transaction_id}`)
      toast.success('Transaction deleted')
      onDeleted(tx.transaction_id)
      onClose()
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Delete failed')
      setBusy(false)
    }
  }

  const isDeposit  = tx.transaction_type === 'Deposit'
  const isWithdraw = tx.transaction_type === 'Withdraw'
  const amountColor = isDeposit ? 'var(--green)' : isWithdraw ? 'var(--red)' : 'var(--yellow)'
  const sign = isDeposit ? '+' : isWithdraw ? '-' : '↔'

  const modal = (
    <div
      style={{
        position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)',
        display: 'flex', alignItems: 'flex-end', justifyContent: 'center',
        zIndex: 1000,
        paddingBottom: 'env(safe-area-inset-bottom)',
      }}
      onClick={onClose}
    >
      <div
        className="card"
        style={{
          width: '100%', maxWidth: '480px',
          maxHeight: '85dvh', overflowY: 'auto',
          borderBottomLeftRadius: 0, borderBottomRightRadius: 0,
          borderBottom: 'none',
          margin: 0,
          animation: 'fadeUp 0.25s ease forwards',
        }}
        onClick={e => e.stopPropagation()}
      >
        {/* Modal header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <TxBadge type={tx.transaction_type} />
          <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
            {mode === 'view' && (
              <>
                <button
                  onClick={() => { setMode('edit'); setDesc(tx.description || ''); setComment(tx.comment || '') }}
                  style={{ background: 'none', border: '1px solid var(--border)', borderRadius: 'var(--radius)', color: 'var(--text2)', fontSize: '0.75rem', padding: '0.25rem 0.6rem', cursor: 'pointer', fontFamily: 'var(--font-ui)', fontWeight: 600 }}
                >✏ Edit</button>
                <button
                  onClick={() => setMode('confirm-delete')}
                  style={{ background: 'none', border: '1px solid var(--red)', borderRadius: 'var(--radius)', color: 'var(--red)', fontSize: '0.75rem', padding: '0.25rem 0.6rem', cursor: 'pointer', fontFamily: 'var(--font-ui)', fontWeight: 600 }}
                >🗑 Delete</button>
              </>
            )}
            <button onClick={onClose} style={{ background: 'none', border: 'none', color: 'var(--text2)', fontSize: '1.2rem', cursor: 'pointer', lineHeight: 1 }}>✕</button>
          </div>
        </div>

        {/* Amount hero */}
        <div style={{ textAlign: 'center', marginBottom: '1rem', paddingBottom: '1rem', borderBottom: '1px solid var(--border)' }}>
          <div className="mono" style={{ fontSize: '2rem', fontWeight: 700, color: amountColor }}>
            {sign}{Math.abs(tx.amount).toLocaleString('en-EG', { minimumFractionDigits: 2 })}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text3)', marginTop: '0.25rem' }}>EGP</div>
        </div>

        {/* Confirm delete mode */}
        {mode === 'confirm-delete' && (
          <div style={{ background: 'rgba(255,77,109,0.08)', border: '1px solid var(--red)', borderRadius: 'var(--radius)', padding: '1rem', marginBottom: '1rem', textAlign: 'center' }}>
            <div style={{ fontWeight: 700, color: 'var(--red)', marginBottom: '0.5rem' }}>Delete this transaction?</div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text2)', marginBottom: '0.75rem' }}>
              This will reverse the balance effect.
              {tx.transaction_type === 'Transfer' && ' Both sides of the transfer will be deleted.'}
            </div>
            <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'center' }}>
              <button onClick={() => setMode('view')} className="btn btn-ghost btn-sm" disabled={busy}>Cancel</button>
              <button onClick={doDelete} disabled={busy} style={{ background: 'var(--red)', color: '#fff', border: 'none', borderRadius: 'var(--radius)', padding: '0.4rem 1rem', fontWeight: 700, cursor: 'pointer', fontFamily: 'var(--font-ui)', fontSize: '0.875rem' }}>
                {busy ? <Spinner size={14} /> : 'Yes, delete'}
              </button>
            </div>
          </div>
        )}

        {/* Edit mode */}
        {mode === 'edit' && (
          <div style={{ marginBottom: '1rem' }}>
            <div style={{ fontSize: '0.72rem', color: 'var(--text2)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '0.4rem' }}>Description</div>
            <input
              className="input"
              value={description}
              onChange={e => setDesc(e.target.value)}
              style={{ marginBottom: '0.75rem', width: '100%' }}
            />
            <div style={{ fontSize: '0.72rem', color: 'var(--text2)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '0.4rem' }}>Comment</div>
            <textarea
              className="input"
              value={comment}
              onChange={e => setComment(e.target.value)}
              rows={2}
              style={{ width: '100%', resize: 'vertical', fontFamily: 'var(--font-ui)' }}
              placeholder="Optional note..."
            />
            <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.75rem' }}>
              <button onClick={() => setMode('view')} className="btn btn-ghost btn-sm" disabled={busy}>Cancel</button>
              <button onClick={save} className="btn btn-primary btn-sm" disabled={busy} style={{ flex: 1 }}>
                {busy ? <Spinner size={14} /> : 'Save'}
              </button>
            </div>
          </div>
        )}

        {/* Detail rows — always visible */}
        {[
          ['Description', tx.description || '—'],
          ['Vault',       tx.vault_name],
          ['Category',    tx.category_name || '—'],
          ['Quantity',    tx.quantity ? `${tx.quantity}${tx.unit_name ? ' ' + tx.unit_name : ''}` : '—'],
          ['Location',    tx.location || '—'],
          ['Comment',     tx.comment || '—'],
          ['Date',        format(parseDate(tx.date), 'PPpp')],
          ['ID',          `#${tx.transaction_id}`],
        ].map(([label, value]) => (
          <div key={label} style={{ display: 'flex', justifyContent: 'space-between', padding: '0.45rem 0', borderBottom: '1px solid var(--border)', fontSize: '0.875rem' }}>
            <span style={{ color: 'var(--text2)', flexShrink: 0 }}>{label}</span>
            <span style={{ fontWeight: 600, textAlign: 'right', maxWidth: '60%', wordBreak: 'break-word', color: 'var(--text)' }}>{value}</span>
          </div>
        ))}

        {/* Tags */}
        {tx.tags?.length > 0 && (
          <div style={{ paddingTop: '0.5rem', display: 'flex', flexWrap: 'wrap', gap: '0.3rem' }}>
            {tx.tags.map(t => (
              <span key={t.tag_id} style={{
                background: 'var(--bg3)', border: '1px solid var(--border)',
                borderRadius: '4px', padding: '0.15rem 0.5rem',
                fontSize: '0.75rem', color: 'var(--text2)',
              }}>{t.tag_name}</span>
            ))}
          </div>
        )}
      </div>
    </div>
  )

  return createPortal(modal, document.body)
}

// ── Main page ──────────────────────────────────────────────────────────────
export default function TransactionsPage() {
  const [transactions, setTransactions] = useState([])
  const [total, setTotal]               = useState(0)
  const [loading, setLoading]           = useState(true)
  const [search, setSearch]             = useState('')
  const [typeFilter, setTypeFilter]     = useState('')
  const [offset, setOffset]             = useState(0)
  const [selected, setSelected]         = useState(null)
  const [searchParams]                  = useSearchParams()
  const toast                           = useToast()
  const navigate                        = useNavigate()
  const LIMIT = 30

  const vaultFilter = searchParams.get('vault') || ''

  const load = useCallback(async (off = 0, append = false) => {
    try {
      const params = { limit: LIMIT, offset: off }
      if (search)      params.search = search
      if (typeFilter)  params.transaction_type = typeFilter
      if (vaultFilter) params.vault_name = vaultFilter
      const res = await api.get('/transactions', { params })
      setTotal(res.data.total)
      setTransactions(prev => append ? [...prev, ...res.data.transactions] : res.data.transactions)
    } catch {
      toast.error('Failed to load transactions')
    } finally {
      setLoading(false)
    }
  }, [search, typeFilter, vaultFilter])

  useEffect(() => { setOffset(0); load(0) }, [search, typeFilter, load])

  function loadMore() {
    const next = offset + LIMIT
    setOffset(next)
    load(next, true)
  }

  function handleUpdated(updatedTx) {
    setTransactions(prev => prev.map(t => t.transaction_id === updatedTx.transaction_id ? updatedTx : t))
    setSelected(updatedTx)
  }

  function handleDeleted(id) {
    setTransactions(prev => prev.filter(t => t.transaction_id !== id))
    setTotal(p => p - 1)
    setSelected(null)
  }

  if (loading) return <PageLoader />

  return (
    <div className="page fade-up">

      {/* Header */}
      <div className="page-header">
        <div className="page-title">Transactions</div>
        <button className="btn btn-primary btn-sm" onClick={() => navigate('/add')}>+ Add</button>
      </div>

      {/* Filters */}
      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
        <input
          className="input"
          placeholder="Search..."
          value={search}
          onChange={e => setSearch(e.target.value)}
          style={{ flex: 1, minWidth: '140px' }}
        />
        <select
          className="input"
          value={typeFilter}
          onChange={e => setTypeFilter(e.target.value)}
          style={{ width: 'auto', minWidth: '110px' }}
        >
          <option value="">All types</option>
          <option value="Deposit">Deposit</option>
          <option value="Withdraw">Withdraw</option>
          <option value="Transfer">Transfer</option>
        </select>
      </div>

      {vaultFilter && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem', fontSize: '0.8rem', color: 'var(--green)' }}>
          <span>Vault: <strong>{vaultFilter}</strong></span>
          <button className="btn btn-ghost btn-sm" onClick={() => navigate('/transactions')}>✕ Clear</button>
        </div>
      )}

      <div style={{ fontSize: '0.75rem', color: 'var(--text3)', fontFamily: 'var(--font-mono)', marginBottom: '0.5rem' }}>
        {total} transaction{total !== 1 ? 's' : ''}
      </div>

      {transactions.length === 0
        ? <div style={{ color: 'var(--text3)', textAlign: 'center', padding: '3rem 0' }}>Nothing found</div>
        : transactions.map(tx => <TxRow key={tx.transaction_id} tx={tx} onTap={setSelected} />)
      }

      {transactions.length < total && (
        <button className="btn btn-ghost btn-full" style={{ marginTop: '1rem' }} onClick={loadMore}>
          Load more ({total - transactions.length} remaining)
        </button>
      )}

      {selected && (
        <TxModal
          tx={selected}
          onClose={() => setSelected(null)}
          onUpdated={handleUpdated}
          onDeleted={handleDeleted}
        />
      )}
    </div>
  )
}
