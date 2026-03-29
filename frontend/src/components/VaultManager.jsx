// frontend/src/components/VaultManager.jsx
// Reusable vault CRUD modal — used in both Dashboard and Settings.
// Props:
//   onClose()          — close the modal
//   onChanged()        — called after any mutation so parent can reload
//
// PORTAL: rendered directly on document.body via createPortal so that
// position:fixed works correctly even when a parent has transform (fade-up).
import { useState, useEffect } from 'react'
import { createPortal } from 'react-dom'
import api from '../api/client'
import { useToast, Spinner } from './ui'

// Convert "2026-03-01T10:30" (datetime-local) to "2026-03-01 10:30:00"
function formatDate(s) {
  if (!s) return undefined
  const r = s.replace('T', ' ')
  return r.length === 16 ? r + ':00' : r
}

// ── One vault row inside the manager ──────────────────────────────────────
function VaultRow({ vault, allVaults, onMutated }) {
  const [mode, setMode]       = useState('view') // 'view'|'rename'|'delete'
  const [newName, setNewName] = useState(vault.vault_name)
  const [action, setAction]   = useState('withdraw')  // 'withdraw'|'transfer'
  const [transferTo, setTransferTo] = useState('')
  const [showMore, setShowMore]     = useState(false)
  const [extraDesc, setExtraDesc]   = useState('')
  const [extraComment, setExtraComment] = useState('')
  const [extraDate, setExtraDate]   = useState('')
  const [busy, setBusy]       = useState(false)
  const toast = useToast()
  const isMain = vault.vault_name.toLowerCase() === 'main'
  const hasBalance = vault.balance !== 0
  const otherVaults = allVaults.filter(v => v.vault_id !== vault.vault_id)

  // Pre-select first other vault for transfer
  useEffect(() => {
    if (otherVaults.length) setTransferTo(otherVaults[0].vault_name)
  }, [allVaults])

  function resetDeleteState() {
    setAction('withdraw'); setShowMore(false)
    setExtraDesc(''); setExtraComment(''); setExtraDate('')
  }

  async function doRename() {
    if (!newName.trim() || newName.trim() === vault.vault_name) { setMode('view'); return }
    setBusy(true)
    try {
      await api.patch(`/vaults/${encodeURIComponent(vault.vault_name)}`, { new_name: newName.trim() })
      toast.success('Vault renamed')
      onMutated()
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Rename failed')
    } finally { setBusy(false) }
  }

  async function doDelete() {
    setBusy(true)
    try {
      if (!hasBalance) {
        await api.delete(`/vaults/${encodeURIComponent(vault.vault_name)}`)
      } else {
        await api.post(`/vaults/${encodeURIComponent(vault.vault_name)}/force-delete`, {
          action,
          transfer_to: action === 'transfer' ? transferTo : undefined,
          description: extraDesc.trim() || undefined,
          comment:     extraComment.trim() || undefined,
          date:        formatDate(extraDate) || undefined,
        })
      }
      toast.success(`Vault "${vault.vault_name}" deleted`)
      onMutated()
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Delete failed')
      setBusy(false)
    }
  }

  return (
    <div style={{
      borderBottom: '1px solid var(--border)',
      padding: '0.75rem 0',
    }}>
      {/* Name + balance row */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: mode !== 'view' ? '0.75rem' : 0 }}>
        <div>
          <span style={{ fontWeight: 700, fontSize: '0.95rem' }}>{vault.vault_name}</span>
          {isMain && <span style={{ marginLeft: '0.4rem', fontSize: '0.65rem', color: 'var(--text3)', fontFamily: 'var(--font-mono)' }}>MAIN · PROTECTED</span>}
          <div className="mono" style={{
            fontSize: '0.85rem', marginTop: '0.1rem',
            color: vault.balance > 0 ? 'var(--green)' : vault.balance < 0 ? 'var(--red)' : 'var(--text3)',
          }}>
            {vault.balance.toLocaleString('en-EG', { minimumFractionDigits: 2 })} EGP
          </div>
        </div>

        {/* Action buttons — only in view mode */}
        {mode === 'view' && (
          <div style={{ display: 'flex', gap: '0.4rem' }}>
            {/* Main vault: no rename, no delete */}
            {!isMain && (
              <>
                <button onClick={() => { setMode('rename'); setNewName(vault.vault_name) }} style={btnStyle('var(--border)', 'var(--text2)')}>
                  ✏ Rename
                </button>
                <button onClick={() => { setMode('delete'); resetDeleteState() }} style={btnStyle('var(--red)', 'var(--red)')}>
                  🗑 Delete
                </button>
              </>
            )}
          </div>
        )}
      </div>

      {/* Rename form */}
      {mode === 'rename' && (
        <div style={{ display: 'flex', gap: '0.4rem', alignItems: 'center' }}>
          <input
            autoFocus
            className="input"
            value={newName}
            onChange={e => setNewName(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter') doRename(); if (e.key === 'Escape') setMode('view') }}
            style={{ flex: 1 }}
          />
          <button onClick={doRename} disabled={busy} style={btnStyle('var(--green)', 'var(--green)')}>
            {busy ? <Spinner size={12} /> : '✓ Save'}
          </button>
          <button onClick={() => setMode('view')} style={btnStyle('var(--border)', 'var(--text3)')}>
            Cancel
          </button>
        </div>
      )}

      {/* Delete form */}
      {mode === 'delete' && (
        <div style={{
          background: 'rgba(255,77,109,0.06)', border: '1px solid rgba(255,77,109,0.3)',
          borderRadius: 'var(--radius)', padding: '0.75rem',
        }}>
          {!hasBalance ? (
            // Zero balance — simple confirm
            <>
              <div style={{ fontSize: '0.85rem', color: 'var(--text2)', marginBottom: '0.75rem' }}>
                Delete <strong style={{ color: 'var(--text)' }}>{vault.vault_name}</strong>? This cannot be undone.
              </div>
              <div style={{ display: 'flex', gap: '0.4rem' }}>
                <button onClick={() => setMode('view')} style={btnStyle('var(--border)', 'var(--text3)')}>Cancel</button>
                <button onClick={doDelete} disabled={busy} style={{ ...btnStyle('var(--red)', '#fff'), background: 'var(--red)' }}>
                  {busy ? <Spinner size={12} /> : 'Yes, delete'}
                </button>
              </div>
            </>
          ) : (
            // Has balance — must choose what to do with money first
            <>
              <div style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--red)', marginBottom: '0.5rem' }}>
                Balance is {vault.balance.toLocaleString('en-EG', { minimumFractionDigits: 2 })} EGP
              </div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text2)', marginBottom: '0.75rem' }}>
                What should happen to the money before deleting?
              </div>

              {/* Action picker */}
              <div style={{ display: 'flex', gap: '0.4rem', marginBottom: '0.75rem' }}>
                {['withdraw', 'transfer'].map(a => (
                  <button key={a} onClick={() => setAction(a)} style={{
                    flex: 1, padding: '0.4rem', borderRadius: 'var(--radius)',
                    border: `1px solid ${action === a ? 'var(--green)' : 'var(--border)'}`,
                    background: action === a ? 'var(--green-dim)' : 'transparent',
                    color: action === a ? 'var(--green)' : 'var(--text2)',
                    fontWeight: 600, fontSize: '0.78rem', cursor: 'pointer',
                    fontFamily: 'var(--font-ui)', textTransform: 'uppercase', letterSpacing: '0.05em',
                  }}>
                    {a === 'withdraw' ? '↑ Withdraw all' : '↔ Transfer to'}
                  </button>
                ))}
              </div>

              {/* Transfer target picker */}
              {action === 'transfer' && (
                <select
                  className="input"
                  value={transferTo}
                  onChange={e => setTransferTo(e.target.value)}
                  style={{ marginBottom: '0.75rem', width: '100%' }}
                >
                  {otherVaults.map(v => (
                    <option key={v.vault_id} value={v.vault_name}>
                      {v.vault_name} — {v.balance.toLocaleString('en-EG', { minimumFractionDigits: 2 })} EGP
                    </option>
                  ))}
                </select>
              )}

              {/* Summary line */}
              <div style={{ fontSize: '0.75rem', color: 'var(--text3)', marginBottom: '0.5rem' }}>
                {action === 'withdraw'
                  ? `Will withdraw ${vault.balance.toLocaleString('en-EG', { minimumFractionDigits: 2 })} EGP, then delete vault.`
                  : `Will transfer ${vault.balance.toLocaleString('en-EG', { minimumFractionDigits: 2 })} EGP to "${transferTo}", then delete vault.`
                }
              </div>

              {/* More options toggle */}
              <button
                type="button"
                onClick={() => setShowMore(p => !p)}
                style={{
                  background: 'none', border: 'none', color: 'var(--text2)',
                  fontSize: '0.75rem', fontWeight: 700, cursor: 'pointer',
                  fontFamily: 'var(--font-ui)', textTransform: 'uppercase',
                  letterSpacing: '0.06em', padding: '0.25rem 0',
                  display: 'flex', alignItems: 'center', gap: '0.3rem',
                  marginBottom: showMore ? '0.75rem' : '0.75rem',
                }}
              >
                <span style={{ transition: 'transform 0.2s', display: 'inline-block', transform: showMore ? 'rotate(90deg)' : 'none' }}>▶</span>
                More options
              </button>

              {/* Expanded advanced options */}
              {showMore && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem', marginBottom: '0.75rem', paddingBottom: '0.75rem', borderBottom: '1px solid rgba(255,77,109,0.2)' }}>
                  <div>
                    <div style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--text2)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '0.3rem' }}>
                      Description <span style={{ color: 'var(--text3)', fontWeight: 400 }}>(overrides auto)</span>
                    </div>
                    <input
                      className="input"
                      placeholder={action === 'withdraw' ? `Vault deletion — ${vault.vault_name}` : `Vault deletion — transfer`}
                      value={extraDesc}
                      onChange={e => setExtraDesc(e.target.value)}
                      style={{ width: '100%' }}
                    />
                  </div>
                  <div>
                    <div style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--text2)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '0.3rem' }}>
                      Comment <span style={{ color: 'var(--text3)', fontWeight: 400 }}>(opt)</span>
                    </div>
                    <input
                      className="input"
                      placeholder="Extra notes..."
                      value={extraComment}
                      onChange={e => setExtraComment(e.target.value)}
                      style={{ width: '100%' }}
                    />
                  </div>
                  <div>
                    <div style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--text2)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '0.3rem' }}>
                      Date <span style={{ color: 'var(--text3)', fontWeight: 400 }}>(opt — defaults to now)</span>
                    </div>
                    <input
                      className="input"
                      type="datetime-local"
                      value={extraDate}
                      onChange={e => setExtraDate(e.target.value)}
                      style={{ width: '100%' }}
                    />
                  </div>
                </div>
              )}

              <div style={{ display: 'flex', gap: '0.4rem' }}>
                <button onClick={() => setMode('view')} style={btnStyle('var(--border)', 'var(--text3)')}>Cancel</button>
                <button onClick={doDelete} disabled={busy || (action === 'transfer' && !transferTo)} style={{ ...btnStyle('var(--red)', '#fff'), background: 'var(--red)', flex: 1 }}>
                  {busy ? <Spinner size={12} /> : 'Confirm & Delete'}
                </button>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  )
}

function btnStyle(borderColor, color) {
  return {
    background: 'none', border: `1px solid ${borderColor}`,
    borderRadius: 'var(--radius)', color,
    fontSize: '0.75rem', fontWeight: 600, padding: '0.3rem 0.6rem',
    cursor: 'pointer', fontFamily: 'var(--font-ui)',
    display: 'inline-flex', alignItems: 'center', gap: '0.2rem',
    whiteSpace: 'nowrap',
  }
}

// ── Add vault form ─────────────────────────────────────────────────────────
function AddVaultForm({ onAdded }) {
  const [name, setName]   = useState('')
  const [busy, setBusy]   = useState(false)
  const toast = useToast()

  async function submit() {
    if (!name.trim()) return
    setBusy(true)
    try {
      await api.post('/vaults', { vault_name: name.trim() })
      toast.success(`Vault "${name}" created`)
      setName('')
      onAdded()
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to create vault')
    } finally { setBusy(false) }
  }

  return (
    <div style={{ display: 'flex', gap: '0.5rem', paddingTop: '0.75rem' }}>
      <input
        className="input"
        placeholder="New vault name..."
        value={name}
        onChange={e => setName(e.target.value)}
        onKeyDown={e => { if (e.key === 'Enter') submit() }}
        style={{ flex: 1 }}
      />
      <button
        className="btn btn-primary btn-sm"
        disabled={busy || !name.trim()}
        onClick={submit}
      >
        {busy ? <Spinner size={14} /> : '+ Add'}
      </button>
    </div>
  )
}

// ── Main exported modal — rendered via portal on document.body ─────────────
export default function VaultManager({ onClose, onChanged }) {
  const [vaults, setVaults]   = useState([])
  const [loading, setLoading] = useState(true)
  const toast = useToast()

  async function load() {
    try {
      const res = await api.get('/vaults')
      setVaults(res.data)
    } catch { toast.error('Failed to load vaults') }
    finally { setLoading(false) }
  }

  useEffect(() => { load() }, [])

  function handleMutated() {
    load()
    onChanged()
  }

  const sheet = (
    // Overlay — covers full viewport regardless of page scroll/transform
    <div
      style={{
        position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        zIndex: 1000,
        padding: '1rem',
      }}
      onClick={onClose}
    >
      {/* Sheet */}
      <div
        className="card"
        style={{
          width: '100%', maxWidth: '480px',
          maxHeight: '85dvh', overflowY: 'auto',
          borderRadius: 'var(--radius)',
          margin: 0,
          animation: 'fadeUp 0.25s ease forwards',
        }}
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
          <div style={{ fontWeight: 800, fontSize: '1rem' }}>Manage Vaults</div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', color: 'var(--text2)', fontSize: '1.2rem', cursor: 'pointer', lineHeight: 1 }}>✕</button>
        </div>

        {loading ? (
          <div style={{ textAlign: 'center', padding: '2rem 0', color: 'var(--text3)' }}>Loading...</div>
        ) : (
          <>
            {vaults.map(v => (
              <VaultRow
                key={v.vault_id}
                vault={v}
                allVaults={vaults}
                onMutated={handleMutated}
              />
            ))}
            <AddVaultForm onAdded={handleMutated} />
          </>
        )}
      </div>
    </div>
  )

  return createPortal(sheet, document.body)
}
