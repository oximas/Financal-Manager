// frontend/src/pages/SettingsPage.jsx
import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import api, { exportCSV } from '../api/client'
import { useAuth } from '../contexts/AuthContext'
import { PageLoader, useToast, Spinner } from '../components/ui'
import VaultManager from '../components/VaultManager'

// ── Reusable inline-edit chip ──────────────────────────────────────────────
function EditableChip({ name, managing, onRename, onDelete }) {
  const [mode, setMode]   = useState('view')
  const [value, setValue] = useState(name)
  const [busy, setBusy]   = useState(false)

  useEffect(() => {
    if (!managing) { setMode('view'); setValue(name) }
  }, [managing])

  async function save() {
    if (!value.trim() || value.trim() === name) { setMode('view'); return }
    setBusy(true)
    await onRename(value.trim())
    setBusy(false)
    setMode('view')
  }

  async function doDelete() {
    setBusy(true)
    await onDelete()
  }

  if (mode === 'edit') {
    return (
      <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.3rem' }}>
        <input
          autoFocus
          value={value}
          onChange={e => setValue(e.target.value)}
          onKeyDown={e => { if (e.key === 'Enter') save(); if (e.key === 'Escape') setMode('view') }}
          style={{
            background: 'var(--bg3)', border: '1px solid var(--green)',
            borderRadius: 'var(--radius)', padding: '0.2rem 0.5rem',
            color: 'var(--text)', fontSize: '0.8rem', fontFamily: 'var(--font-ui)',
            width: `${Math.max(value.length + 2, 8)}ch`,
          }}
        />
        <button onClick={save} disabled={busy} style={chipActionStyle('var(--green)')}>
          {busy ? '…' : '✓'}
        </button>
        <button onClick={() => { setMode('view'); setValue(name) }} style={chipActionStyle('var(--text3)')}>
          ✕
        </button>
      </span>
    )
  }

  if (mode === 'confirm-delete') {
    return (
      <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.3rem' }}>
        <span style={chipBaseStyle}>{name}</span>
        <button onClick={doDelete} disabled={busy} style={chipActionStyle('var(--red)')}>
          {busy ? '…' : 'Delete?'}
        </button>
        <button onClick={() => setMode('view')} style={chipActionStyle('var(--text3)')}>
          Cancel
        </button>
      </span>
    )
  }

  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.2rem' }}>
      <span style={chipBaseStyle}>{name}</span>
      {managing && <>
        <button onClick={() => { setMode('edit'); setValue(name) }} style={chipIconStyle} title="Rename">✏</button>
        <button onClick={() => setMode('confirm-delete')} style={{ ...chipIconStyle, color: 'var(--red)' }} title="Delete">🗑</button>
      </>}
    </span>
  )
}

const chipBaseStyle = {
  background: 'var(--bg3)', border: '1px solid var(--border)',
  borderRadius: 'var(--radius)', padding: '0.25rem 0.6rem',
  fontSize: '0.8rem', color: 'var(--text2)',
}
const chipIconStyle = {
  background: 'none', border: 'none', cursor: 'pointer',
  color: 'var(--text3)', fontSize: '0.75rem', padding: '0.1rem 0.2rem',
  lineHeight: 1, transition: 'color 0.15s',
}
function chipActionStyle(color) {
  return {
    background: 'none', border: `1px solid ${color}`, borderRadius: 'var(--radius)',
    color, cursor: 'pointer', fontSize: '0.72rem', padding: '0.15rem 0.4rem',
    fontFamily: 'var(--font-ui)', fontWeight: 600, transition: 'all 0.15s',
  }
}

// ── Section component ──────────────────────────────────────────────────────
function ManagedSection({ title, items, idKey, nameKey, addPlaceholder, onAdd, onRename, onDelete }) {
  const [newName, setNewName] = useState('')
  const [saving, setSaving]   = useState(false)
  const [managing, setManaging] = useState(false)
  const toast = useToast()

  async function handleAdd(e) {
    e.preventDefault()
    if (!newName.trim()) return
    setSaving(true)
    try {
      await onAdd(newName.trim())
      setNewName('')
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to add')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="card" style={{ marginBottom: '1.25rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
        <div style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--text2)', letterSpacing: '0.08em', textTransform: 'uppercase' }}>
          {title}
          <span style={{ marginLeft: '0.5rem', color: 'var(--text3)', fontWeight: 400 }}>({items.length})</span>
        </div>
        <button
          onClick={() => setManaging(m => !m)}
          style={{
            background: managing ? 'var(--green-dim)' : 'none',
            border: `1px solid ${managing ? 'var(--green)' : 'var(--border)'}`,
            borderRadius: 'var(--radius)', padding: '0.2rem 0.6rem',
            color: managing ? 'var(--green)' : 'var(--text3)',
            fontSize: '0.7rem', fontWeight: 700, cursor: 'pointer',
            fontFamily: 'var(--font-ui)', transition: 'all 0.15s',
          }}
        >
          {managing ? 'Done' : 'Manage'}
        </button>
      </div>

      {items.length === 0 ? (
        <div style={{ color: 'var(--text3)', fontSize: '0.8rem', marginBottom: '0.75rem' }}>None yet</div>
      ) : (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem', marginBottom: '0.75rem' }}>
          {items.map(item => (
            <EditableChip
              key={item[idKey]}
              name={item[nameKey]}
              managing={managing}
              onRename={async (newName) => {
                try { await onRename(item[idKey], newName) }
                catch (err) { toast.error(err.response?.data?.detail || 'Rename failed') }
              }}
              onDelete={async () => {
                try { await onDelete(item[idKey]) }
                catch (err) { toast.error(err.response?.data?.detail || 'Delete failed') }
              }}
            />
          ))}
        </div>
      )}

      <form onSubmit={handleAdd} style={{ display: 'flex', gap: '0.5rem' }}>
        <input
          className="input"
          placeholder={addPlaceholder}
          value={newName}
          onChange={e => setNewName(e.target.value)}
          style={{ flex: 1 }}
        />
        <button type="submit" className="btn btn-ghost btn-sm" disabled={saving}>
          {saving ? <Spinner size={14} /> : 'Add'}
        </button>
      </form>
    </div>
  )
}

// ── Export Data section ────────────────────────────────────────────────────
function ExportSection() {
  const toast = useToast()

  // "all" | "range"
  const [mode, setMode]       = useState('all')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo]     = useState('')
  const [busy, setBusy]         = useState(false)

  async function handleExport() {
    setBusy(true)
    try {
      const from = mode === 'range' ? dateFrom || null : null
      const to   = mode === 'range' ? dateTo   || null : null
      await exportCSV(from, to)
      toast.success('Download started')
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Export failed')
    } finally {
      setBusy(false)
    }
  }

  const rangeInvalid = mode === 'range' && dateFrom && dateTo && dateFrom > dateTo

  return (
    <div className="card" style={{ marginBottom: '1.25rem' }}>
      <div style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--text2)', letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: '0.75rem' }}>
        Export Data
      </div>

      {/* Mode toggle */}
      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.75rem' }}>
        {['all', 'range'].map(m => (
          <button
            key={m}
            onClick={() => setMode(m)}
            style={{
              background: mode === m ? 'var(--green-dim)' : 'none',
              border: `1px solid ${mode === m ? 'var(--green)' : 'var(--border)'}`,
              borderRadius: 'var(--radius)', padding: '0.25rem 0.75rem',
              color: mode === m ? 'var(--green)' : 'var(--text3)',
              fontSize: '0.75rem', fontWeight: 600, cursor: 'pointer',
              fontFamily: 'var(--font-ui)', transition: 'all 0.15s',
            }}
          >
            {m === 'all' ? 'All time' : 'Date range'}
          </button>
        ))}
      </div>

      {/* Date inputs — only visible in range mode */}
      {mode === 'range' && (
        <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.75rem', flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem', flex: 1, minWidth: '130px' }}>
            <label style={{ fontSize: '0.7rem', color: 'var(--text3)' }}>From</label>
            <input
              type="date"
              className="input"
              value={dateFrom}
              onChange={e => setDateFrom(e.target.value)}
              style={{ fontSize: '0.8rem' }}
            />
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem', flex: 1, minWidth: '130px' }}>
            <label style={{ fontSize: '0.7rem', color: 'var(--text3)' }}>To</label>
            <input
              type="date"
              className="input"
              value={dateTo}
              onChange={e => setDateTo(e.target.value)}
              style={{ fontSize: '0.8rem' }}
            />
          </div>
        </div>
      )}

      {rangeInvalid && (
        <div style={{ fontSize: '0.75rem', color: 'var(--red)', marginBottom: '0.5rem' }}>
          "From" date must be before "To" date.
        </div>
      )}

      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ fontSize: '0.75rem', color: 'var(--text3)' }}>
          Format: CSV · All transactions
        </div>
        <button
          className="btn btn-ghost btn-sm"
          onClick={handleExport}
          disabled={busy || rangeInvalid}
          style={{ minWidth: '90px' }}
        >
          {busy ? <Spinner size={14} /> : '↓ Download'}
        </button>
      </div>
    </div>
  )
}

// ── Main page ──────────────────────────────────────────────────────────────
export default function SettingsPage() {
  const [categories, setCategories] = useState([])
  const [units, setUnits]           = useState([])
  const [tags, setTags]             = useState([])
  const [loading, setLoading]       = useState(true)
  const [showVaultMgr, setShowVaultMgr] = useState(false)
  const { user, logout }            = useAuth()
  const toast                       = useToast()
  const navigate                    = useNavigate()

  const load = useCallback(async () => {
    try {
      const [c, u, t] = await Promise.all([
        api.get('/categories'),
        api.get('/units'),
        api.get('/tags'),
      ])
      setCategories(c.data)
      setUnits(u.data)
      setTags(t.data)
    } catch { toast.error('Failed to load settings') }
    finally { setLoading(false) }
  }, [])

  useEffect(() => { load() }, [load])

  async function addCategory(name) {
    const res = await api.post('/categories', { category_name: name })
    setCategories(p => [...p, res.data].sort((a, b) => a.category_name.localeCompare(b.category_name)))
    toast.success('Category added')
  }
  async function renameCategory(id, name) {
    const res = await api.patch(`/categories/${id}`, { name })
    setCategories(p => p.map(c => c.category_id === id ? res.data : c).sort((a, b) => a.category_name.localeCompare(b.category_name)))
    toast.success('Renamed')
  }
  async function deleteCategory(id) {
    await api.delete(`/categories/${id}`)
    setCategories(p => p.filter(c => c.category_id !== id))
    toast.success('Category deleted')
  }

  async function addUnit(name) {
    const res = await api.post('/units', { unit_name: name })
    setUnits(p => [...p, res.data].sort((a, b) => a.unit_name.localeCompare(b.unit_name)))
    toast.success('Unit added')
  }
  async function renameUnit(id, name) {
    const res = await api.patch(`/units/${id}`, { name })
    setUnits(p => p.map(u => u.unit_id === id ? res.data : u).sort((a, b) => a.unit_name.localeCompare(b.unit_name)))
    toast.success('Renamed')
  }
  async function deleteUnit(id) {
    await api.delete(`/units/${id}`)
    setUnits(p => p.filter(u => u.unit_id !== id))
    toast.success('Unit deleted')
  }

  async function addTag(name) {
    const res = await api.post('/tags', { tag_name: name })
    setTags(p => [...p, res.data].sort((a, b) => a.tag_name.localeCompare(b.tag_name)))
    toast.success('Tag added')
  }
  async function renameTag(id, name) {
    const res = await api.patch(`/tags/${id}`, { name })
    setTags(p => p.map(t => t.tag_id === id ? res.data : t).sort((a, b) => a.tag_name.localeCompare(b.tag_name)))
    toast.success('Renamed')
  }
  async function deleteTag(id) {
    await api.delete(`/tags/${id}`)
    setTags(p => p.filter(t => t.tag_id !== id))
    toast.success('Tag deleted')
  }

  if (loading) return <PageLoader />

  return (
    <div className="page fade-up">
      <div className="page-header">
        <div className="page-title">Settings</div>
      </div>

      {/* Account */}
      <div className="card" style={{ marginBottom: '1.25rem' }}>
        <div style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--text2)', letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: '0.75rem' }}>
          Account
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <div style={{ fontWeight: 700 }}>{user?.username}</div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text2)', marginTop: '0.2rem', fontFamily: 'var(--font-mono)' }}>
              Signed in
            </div>
          </div>
          <button className="btn btn-danger btn-sm" onClick={() => { logout(); navigate('/login') }}>
            Sign out
          </button>
        </div>
      </div>

      {/* Export */}
      <ExportSection />

      {/* Categories */}
      <ManagedSection
        title="Categories"
        items={categories}
        idKey="category_id"
        nameKey="category_name"
        addPlaceholder="New category..."
        onAdd={addCategory}
        onRename={renameCategory}
        onDelete={deleteCategory}
      />

      {/* Units */}
      <ManagedSection
        title="Units"
        items={units}
        idKey="unit_id"
        nameKey="unit_name"
        addPlaceholder="New unit..."
        onAdd={addUnit}
        onRename={renameUnit}
        onDelete={deleteUnit}
      />

      {/* Tags */}
      <ManagedSection
        title="Tags"
        items={tags}
        idKey="tag_id"
        nameKey="tag_name"
        addPlaceholder="New tag..."
        onAdd={addTag}
        onRename={renameTag}
        onDelete={deleteTag}
      />

      {/* Vaults */}
      <div className="card" style={{ marginBottom: '1.25rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--text2)', letterSpacing: '0.08em', textTransform: 'uppercase' }}>
            Vaults
          </div>
          <button className="btn btn-ghost btn-sm" onClick={() => setShowVaultMgr(true)} style={{ fontSize: '0.75rem' }}>
            Manage
          </button>
        </div>
        <div style={{ fontSize: '0.8rem', color: 'var(--text3)', marginTop: '0.5rem' }}>
          Create, rename, or delete vaults. Deleting a vault with balance lets you withdraw or transfer funds first.
        </div>
      </div>

      {/* Version */}
      <div style={{ textAlign: 'center', color: 'var(--text3)', fontSize: '0.75rem', fontFamily: 'var(--font-mono)', padding: '1rem 0' }}>
        PFM v0.3.5 · FastAPI + React PWA
      </div>

      {showVaultMgr && (
        <VaultManager onClose={() => setShowVaultMgr(false)} onChanged={() => {}} />
      )}
    </div>
  )
}
