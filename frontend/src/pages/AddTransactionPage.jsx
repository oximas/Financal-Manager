// frontend/src/pages/AddTransactionPage.jsx
import { useState, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import api from '../api/client'
import { PageLoader, Spinner, useToast } from '../components/ui'

function formatDate(dateStr) {
  if (!dateStr) return undefined
  const s = dateStr.replace('T', ' ')
  return s.length === 16 ? s + ':00' : s
}

const TX_TYPES = ['deposit', 'withdraw', 'transfer']
const DEFAULT_FORM = {
  vault_name: '', amount: '', category: '', description: '',
  comment: '', quantity: '', unit: '', date: '',
  to_username: '', to_vault: '', location: '', tag_ids: [],
}
const STORAGE_KEY = 'pfm_add_form'

// ── Tag picker (shared by Single and Bulk forms) ───────────────────────────
function TagPicker({ tags, selected, onChange }) {
  function toggle(id) {
    onChange(selected.includes(id) ? selected.filter(x => x !== id) : [...selected, id])
  }
  if (!tags.length) return (
    <div style={{ fontSize: '0.78rem', color: 'var(--text3)' }}>No tags yet — add some in Settings</div>
  )
  return (
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.35rem' }}>
      {tags.map(t => {
        const active = selected.includes(t.tag_id)
        return (
          <button key={t.tag_id} type="button" onClick={() => toggle(t.tag_id)} style={{
            background: active ? 'var(--green-dim)' : 'var(--bg3)',
            border: `1px solid ${active ? 'var(--green)' : 'var(--border)'}`,
            borderRadius: 'var(--radius)', padding: '0.2rem 0.6rem',
            fontSize: '0.78rem', color: active ? 'var(--green)' : 'var(--text2)',
            cursor: 'pointer', fontFamily: 'var(--font-ui)',
            fontWeight: active ? 700 : 400, transition: 'all 0.12s',
          }}>
            {t.tag_name}
          </button>
        )
      })}
    </div>
  )
}

// ── Single form ────────────────────────────────────────────────────────────
function SingleForm({ vaults, categories, units, users, tags }) {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()

  const [type, setType] = useState(() =>
    searchParams.get('type') || localStorage.getItem('pfm_add_type') || 'withdraw'
  )
  const [form, setForm] = useState(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY)
      if (saved) return { ...DEFAULT_FORM, ...JSON.parse(saved) }
    } catch {}
    return { ...DEFAULT_FORM }
  })
  const [toVaults, setToVaults]     = useState([])
  const [submitting, setSubmitting] = useState(false)
  const [error, setError]           = useState('')
  const [success, setSuccess]       = useState(false)
  const [showAdvanced, setShowAdvanced] = useState(false)

  const set = (k, v) => setForm(p => {
    const next = { ...p, [k]: v }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(next))
    return next
  })

  function changeType(t) { setType(t); setError(''); localStorage.setItem('pfm_add_type', t) }
  function clearSaved()  { localStorage.removeItem(STORAGE_KEY); localStorage.removeItem('pfm_add_type') }

  useEffect(() => {
    setForm(prev => {
      const next = { ...prev }
      if (!prev.vault_name && vaults.length)     next.vault_name = vaults[0].vault_name
      if (!prev.category   && categories.length) next.category   = categories[0].category_name
      localStorage.setItem(STORAGE_KEY, JSON.stringify(next))
      return next
    })
  }, [vaults, categories])

  useEffect(() => {
    if (!form.to_username) { setToVaults([]); return }
    api.get(`/users/${encodeURIComponent(form.to_username)}/vaults`)
      .then(r => { setToVaults(r.data); set('to_vault', r.data[0]?.vault_name || '') })
      .catch(() => { setToVaults([]); set('to_vault', '') })
  }, [form.to_username])

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    const amount = parseFloat(form.amount)
    if (!amount || amount <= 0) { setError('Amount must be a positive number'); return }
    setSubmitting(true)
    try {
      const date = formatDate(form.date)
      let tx = null
      if (type === 'deposit') {
        const res = await api.post('/transactions/deposit', {
          vault_name: form.vault_name, amount,
          category: form.category, description: form.description,
          comment: form.comment || undefined,
          location: form.location || undefined, date,
        })
        tx = res.data
      } else if (type === 'withdraw') {
        const res = await api.post('/transactions/withdraw', {
          vault_name: form.vault_name, amount,
          category: form.category, description: form.description,
          comment: form.comment || undefined,
          quantity: form.quantity ? parseFloat(form.quantity) : undefined,
          unit: form.unit || undefined,
          location: form.location || undefined, date,
        })
        tx = res.data
      } else if (type === 'transfer') {
        const res = await api.post('/transactions/transfer', {
          from_vault: form.vault_name, to_username: form.to_username,
          to_vault: form.to_vault, amount,
          description: form.description || 'Transfer',
          comment: form.comment || undefined, date,
        })
        tx = res.data.from_transaction
      }
      // Apply tags (not for transfer)
      if (tx && form.tag_ids?.length && type !== 'transfer') {
        await Promise.all(
          form.tag_ids.map(tid => api.post(`/transactions/${tx.transaction_id}/tags/${tid}`))
        )
      }
      clearSaved()
      setSuccess(true)
      setTimeout(() => navigate('/dashboard'), 800)
    } catch (err) {
      const detail = err.response?.data?.detail
      setError(typeof detail === 'string' ? detail : JSON.stringify(detail) || 'Failed')
    } finally { setSubmitting(false) }
  }

  if (success) return (
    <div style={{ flex:1, display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center', gap:'1rem', minHeight:'50vh' }}>
      <div style={{ fontSize:'3rem' }}>✓</div>
      <div style={{ color:'var(--green)', fontWeight:700 }}>Transaction added!</div>
    </div>
  )

  const advancedCount = (form.location ? 1 : 0) + (form.tag_ids?.length || 0)

  return (
    <>
      <div style={{ display:'flex', background:'var(--bg3)', borderRadius:'var(--radius)', padding:'3px', marginBottom:'1.5rem' }}>
        {TX_TYPES.map(t => (
          <button key={t} onClick={() => changeType(t)} type="button" style={{
            flex:1, padding:'0.5rem', borderRadius:'calc(var(--radius) - 2px)', border:'none',
            background: type===t ? (t==='deposit'?'var(--green)':t==='withdraw'?'var(--red)':'var(--yellow)') : 'transparent',
            color: type===t ? '#0a0a0a' : 'var(--text2)',
            fontWeight:700, fontSize:'0.75rem', textTransform:'uppercase', letterSpacing:'0.06em',
            fontFamily:'var(--font-ui)', transition:'all 0.15s', cursor:'pointer',
          }}>{t}</button>
        ))}
      </div>

      {error && (
        <div style={{ background:'rgba(255,77,109,0.1)', border:'1px solid rgba(255,77,109,0.3)', borderRadius:'var(--radius)', padding:'0.75rem 1rem', color:'var(--red)', fontSize:'0.875rem', marginBottom:'1rem' }}>
          ✗ {error}
        </div>
      )}

      <form onSubmit={handleSubmit} style={{ display:'flex', flexDirection:'column', gap:'1rem' }}>

        <div className="field">
          <label>{type==='transfer' ? 'From Vault' : 'Vault'}</label>
          <select className="input" value={form.vault_name} onChange={e => set('vault_name', e.target.value)} required>
            {vaults.map(v => <option key={v.vault_id} value={v.vault_name}>{v.vault_name} — {v.balance.toLocaleString('en-EG',{minimumFractionDigits:2})} EGP</option>)}
          </select>
        </div>

        <div className="field">
          <label>Amount (EGP)</label>
          <input className="input mono" type="number" step="0.01" min="0.01" placeholder="0.00"
            value={form.amount} onChange={e => set('amount', e.target.value)} required />
        </div>

        {type !== 'transfer' && (
          <div className="field">
            <label>Category</label>
            {categories.length === 0
              ? <div style={{ color:'var(--red)', fontSize:'0.8rem', padding:'0.5rem 0' }}>No categories — add some in Settings first</div>
              : <select className="input" value={form.category} onChange={e => set('category', e.target.value)} required>
                  {categories.map(c => <option key={c.category_id} value={c.category_name}>{c.category_name}</option>)}
                </select>
            }
          </div>
        )}

        <div className="field">
          <label>Description {type==='transfer' && <span style={{ color:'var(--text3)' }}>(optional)</span>}</label>
          <input className="input" type="text"
            placeholder={type==='transfer' ? 'Transfer reason...' : 'What was this for?'}
            value={form.description} onChange={e => set('description', e.target.value)}
            required={type !== 'transfer'} />
        </div>

        {type === 'withdraw' && (
          <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:'0.75rem' }}>
            <div className="field">
              <label>Qty <span style={{ color:'var(--text3)' }}>(opt)</span></label>
              <input className="input mono" type="number" step="0.01" min="0" placeholder="1"
                value={form.quantity} onChange={e => set('quantity', e.target.value)} />
            </div>
            <div className="field">
              <label>Unit <span style={{ color:'var(--text3)' }}>(opt)</span></label>
              <select className="input" value={form.unit} onChange={e => set('unit', e.target.value)}>
                <option value="">—</option>
                {units.map(u => <option key={u.unit_id} value={u.unit_name}>{u.unit_name}</option>)}
              </select>
            </div>
          </div>
        )}

        {type === 'transfer' && (
          <>
            <div className="field">
              <label>To User</label>
              <select className="input" value={form.to_username} onChange={e => set('to_username', e.target.value)} required>
                <option value="">— select user —</option>
                {users.map(u => <option key={u.user_id} value={u.username}>{u.username}</option>)}
              </select>
            </div>
            <div className="field">
              <label>To Vault</label>
              {!form.to_username
                ? <div style={{ color:'var(--text3)', fontSize:'0.8rem', padding:'0.5rem 0' }}>Select a user first</div>
                : toVaults.length === 0
                  ? <div style={{ color:'var(--red)', fontSize:'0.8rem', padding:'0.5rem 0' }}>This user has no vaults</div>
                  : <select className="input" value={form.to_vault} onChange={e => set('to_vault', e.target.value)} required>
                      {toVaults.map(v => <option key={v.vault_id} value={v.vault_name}>{v.vault_name} — {v.balance.toLocaleString('en-EG',{minimumFractionDigits:2})} EGP</option>)}
                    </select>
              }
            </div>
          </>
        )}

        <div className="field">
          <label>Comment <span style={{ color:'var(--text3)' }}>(opt)</span></label>
          <input className="input" type="text" placeholder="Extra notes..."
            value={form.comment} onChange={e => set('comment', e.target.value)} />
        </div>

        <div className="field">
          <label>Date <span style={{ color:'var(--text3)' }}>(opt — defaults to now)</span></label>
          <input className="input" type="datetime-local"
            value={form.date} onChange={e => set('date', e.target.value)} />
        </div>

        {/* Advanced section */}
        <div style={{ borderTop:'1px solid var(--border)', paddingTop:'0.75rem' }}>
          <button type="button" onClick={() => setShowAdvanced(p => !p)} style={{
            background:'none', border:'none', color:'var(--text2)', fontSize:'0.78rem',
            fontWeight:700, cursor:'pointer', textTransform:'uppercase', letterSpacing:'0.06em',
            fontFamily:'var(--font-ui)', display:'flex', alignItems:'center', gap:'0.4rem', padding:0,
          }}>
            <span style={{ transition:'transform 0.2s', display:'inline-block', transform: showAdvanced ? 'rotate(90deg)' : 'rotate(0deg)' }}>▶</span>
            Advanced
            {advancedCount > 0 && (
              <span style={{ background:'var(--green)', color:'#0a0a0a', borderRadius:'10px', padding:'0 0.4rem', fontSize:'0.65rem', fontWeight:800 }}>
                {advancedCount}
              </span>
            )}
          </button>

          {showAdvanced && (
            <div style={{ display:'flex', flexDirection:'column', gap:'0.9rem', marginTop:'0.9rem' }}>
              <div className="field">
                <label>Location <span style={{ color:'var(--text3)' }}>(opt)</span></label>
                <input className="input" type="text" placeholder="e.g. Carrefour, Online..."
                  value={form.location} onChange={e => set('location', e.target.value)} />
              </div>
              {type !== 'transfer' && (
                <div className="field">
                  <label>Tags <span style={{ color:'var(--text3)' }}>(opt)</span></label>
                  <TagPicker tags={tags} selected={form.tag_ids || []} onChange={ids => set('tag_ids', ids)} />
                </div>
              )}
            </div>
          )}
        </div>

        <div style={{ display:'flex', gap:'0.5rem', marginTop:'0.5rem' }}>
          <button type="button" className="btn btn-ghost"
            onClick={() => { setForm({...DEFAULT_FORM}); clearSaved() }}>
            Clear
          </button>
          <button type="submit" className="btn btn-primary" style={{ flex:1 }}
            disabled={submitting || (type !== 'transfer' && categories.length === 0)}>
            {submitting ? <Spinner size={18} /> : `Add ${type.charAt(0).toUpperCase() + type.slice(1)} →`}
          </button>
        </div>
      </form>
    </>
  )
}

// ── Bulk form ──────────────────────────────────────────────────────────────
const BULK_EMPTY = {
  transaction_type:'Withdraw', vault_name:'', amount:'', category:'',
  description:'', comment:'', quantity:'', unit:'', date:'',
  location:'', tag_ids:[],
}

function BulkForm({ vaults, categories, units, tags }) {
  const navigate = useNavigate()
  const [rows, setRows]         = useState([])
  const [form, setForm]         = useState({...BULK_EMPTY})
  const [editIdx, setEditIdx]   = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const [errors, setErrors]     = useState([])
  const [result, setResult]     = useState(null)
  const [showAdvanced, setShowAdvanced] = useState(false)
  const set = (k, v) => setForm(p => ({...p, [k]: v}))

  useEffect(() => {
    setForm(p => ({
      ...p,
      vault_name: p.vault_name || vaults[0]?.vault_name || '',
      category:   p.category   || categories[0]?.category_name || '',
    }))
  }, [vaults, categories])

  function addOrUpdate(e) {
    e.preventDefault()
    if (!form.amount || !form.vault_name) return
    if (editIdx !== null) {
      setRows(prev => prev.map((r, i) => i === editIdx ? {...form} : r))
      setEditIdx(null)
    } else {
      setRows(prev => [...prev, {...form}])
      setForm(p => ({...p, amount:'', description:'', comment:'', quantity:'', location:'', tag_ids:[]}))
    }
    setErrors([])
  }
  function startEdit(i) { setEditIdx(i); setForm({...rows[i]}) }
  function copyRow(i)   { setEditIdx(null); setForm({...rows[i], amount:'', description:''}) }
  function removeRow(i) {
    setRows(prev => prev.filter((_,idx) => idx !== i))
    if (editIdx === i) { setEditIdx(null); setForm({...BULK_EMPTY}) }
    setErrors([])
  }
  function cancelEdit() { setEditIdx(null); setForm(p => ({...p, amount:'', description:'', comment:'', quantity:'', location:'', tag_ids:[]})) }

  async function validateAndSubmit() {
    if (!rows.length) return
    setSubmitting(true); setErrors([])
    try {
      const payload = rows.map((r, i) => ({
        row_number: i+1, transaction_type: r.transaction_type, vault_name: r.vault_name,
        amount: parseFloat(r.amount), category: r.category || undefined,
        description: r.description || '', comment: r.comment || undefined,
        quantity: r.quantity ? parseFloat(r.quantity) : undefined,
        unit: r.unit || undefined, date: formatDate(r.date),
        location: r.location || undefined,
        tag_ids: r.tag_ids?.length ? r.tag_ids : undefined,
      }))
      const val = await api.post('/bulk/validate', {rows: payload})
      if (!val.data.is_valid) { setErrors(val.data.errors); setSubmitting(false); return }
      const res = await api.post('/bulk/submit', {rows: payload})
      setResult(res.data)
    } catch (err) {
      setErrors([{row_number:0, message: err.response?.data?.detail || 'Failed'}])
    } finally { setSubmitting(false) }
  }

  const totalNet = rows.reduce((s, r) =>
    s + (r.transaction_type==='Deposit'?1:r.transaction_type==='Withdraw'?-1:0) * (parseFloat(r.amount)||0), 0)

  const advancedCount = (form.location ? 1 : 0) + (form.tag_ids?.length || 0)

  if (result) return (
    <div style={{ flex:1,display:'flex',flexDirection:'column',alignItems:'center',justifyContent:'center',gap:'1rem',padding:'2rem',textAlign:'center' }}>
      <div style={{ fontSize:'3rem' }}>✓</div>
      <div style={{ color:'var(--green)',fontWeight:700,fontSize:'1.2rem' }}>Done! {result.successful} added · {result.failed} failed</div>
      <button className="btn btn-primary" onClick={() => navigate('/dashboard')}>Dashboard</button>
      <button className="btn btn-ghost" onClick={() => {setResult(null);setRows([])}}>Add more</button>
    </div>
  )

  return (
    <>
      <div className="card" style={{ marginBottom:'1rem', border: editIdx!==null ? '1px solid var(--green)' : '1px solid var(--border)' }}>
        <form onSubmit={addOrUpdate} style={{ display:'flex',flexDirection:'column',gap:'0.6rem' }}>

          {/* Type + Vault */}
          <div style={{ display:'grid',gridTemplateColumns:'1fr 1fr',gap:'0.5rem' }}>
            <div className="field"><label>Type</label>
              <select className="input" value={form.transaction_type} onChange={e => set('transaction_type', e.target.value)}>
                <option>Deposit</option><option>Withdraw</option><option>Transfer</option>
              </select>
            </div>
            <div className="field"><label>Vault</label>
              <select className="input" value={form.vault_name} onChange={e => set('vault_name', e.target.value)}>
                {vaults.map(v => <option key={v.vault_id} value={v.vault_name}>{v.vault_name} ({v.balance.toFixed(0)})</option>)}
              </select>
            </div>
          </div>

          {/* Amount + Category */}
          <div style={{ display:'grid',gridTemplateColumns:'1fr 1fr',gap:'0.5rem' }}>
            <div className="field"><label>Amount</label>
              <input className="input mono" type="number" step="0.01" min="0.01" placeholder="0.00"
                value={form.amount} onChange={e => set('amount', e.target.value)} required autoFocus />
            </div>
            <div className="field"><label>Category</label>
              <select className="input" value={form.category} onChange={e => set('category', e.target.value)}>
                {categories.map(c => <option key={c.category_id} value={c.category_name}>{c.category_name}</option>)}
              </select>
            </div>
          </div>

          {/* Description */}
          <div className="field"><label>Description</label>
            <input className="input" type="text" placeholder="What was this?"
              value={form.description} onChange={e => set('description', e.target.value)} />
          </div>

          {/* Qty + Unit — only for Withdraw */}
          {form.transaction_type === 'Withdraw' && (
            <div style={{ display:'grid',gridTemplateColumns:'1fr 1fr',gap:'0.5rem' }}>
              <div className="field"><label>Qty (opt)</label>
                <input className="input mono" type="number" step="0.01" min="0"
                  value={form.quantity} onChange={e => set('quantity', e.target.value)} />
              </div>
              <div className="field"><label>Unit (opt)</label>
                <select className="input" value={form.unit} onChange={e => set('unit', e.target.value)}>
                  <option value="">—</option>
                  {units.map(u => <option key={u.unit_id} value={u.unit_name}>{u.unit_name}</option>)}
                </select>
              </div>
            </div>
          )}

          {/* Comment + Date */}
          <div className="field"><label>Comment (opt)</label>
            <input className="input" type="text" value={form.comment} onChange={e => set('comment', e.target.value)} />
          </div>
          <div className="field"><label>Date (opt)</label>
            <input className="input" type="datetime-local" value={form.date} onChange={e => set('date', e.target.value)} />
          </div>

          {/* Advanced section */}
          <div style={{ borderTop:'1px solid var(--border)', paddingTop:'0.6rem' }}>
            <button type="button" onClick={() => setShowAdvanced(p => !p)} style={{
              background:'none', border:'none', color:'var(--text2)', fontSize:'0.72rem',
              fontWeight:700, cursor:'pointer', textTransform:'uppercase', letterSpacing:'0.06em',
              fontFamily:'var(--font-ui)', display:'flex', alignItems:'center', gap:'0.35rem', padding:0,
            }}>
              <span style={{ transition:'transform 0.2s', display:'inline-block', transform: showAdvanced ? 'rotate(90deg)' : 'rotate(0deg)' }}>▶</span>
              Advanced
              {advancedCount > 0 && (
                <span style={{ background:'var(--green)', color:'#0a0a0a', borderRadius:'10px', padding:'0 0.35rem', fontSize:'0.6rem', fontWeight:800 }}>
                  {advancedCount}
                </span>
              )}
            </button>

            {showAdvanced && (
              <div style={{ display:'flex', flexDirection:'column', gap:'0.6rem', marginTop:'0.6rem' }}>
                <div className="field">
                  <label>Location <span style={{ color:'var(--text3)' }}>(opt)</span></label>
                  <input className="input" type="text" placeholder="e.g. Carrefour, Online..."
                    value={form.location} onChange={e => set('location', e.target.value)} />
                </div>
                {form.transaction_type !== 'Transfer' && (
                  <div className="field">
                    <label>Tags <span style={{ color:'var(--text3)' }}>(opt)</span></label>
                    <TagPicker tags={tags} selected={form.tag_ids || []} onChange={ids => set('tag_ids', ids)} />
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Add / Save button */}
          <div style={{ display:'flex',gap:'0.5rem',marginTop:'0.25rem' }}>
            {editIdx !== null && <button type="button" className="btn btn-ghost" onClick={cancelEdit}>Cancel</button>}
            <button type="submit" className="btn btn-primary" style={{ flex:1 }}>
              {editIdx !== null ? '✓ Save edit' : '+ Add to list'}
            </button>
          </div>
        </form>
      </div>

      {rows.length > 0 && <>
        <div style={{ display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:'0.5rem' }}>
          <div style={{ fontSize:'0.7rem',color:'var(--text2)',fontWeight:700,textTransform:'uppercase',letterSpacing:'0.08em' }}>{rows.length} rows</div>
          <div className="mono" style={{ fontSize:'0.85rem',color:totalNet>=0?'var(--green)':'var(--red)',fontWeight:700 }}>
            Net: {totalNet>=0?'+':''}{totalNet.toLocaleString('en-EG',{minimumFractionDigits:2})} EGP
          </div>
        </div>
        {rows.map((r, i) => {
          const isD=r.transaction_type==='Deposit', isW=r.transaction_type==='Withdraw'
          const color=isD?'var(--green)':isW?'var(--red)':'var(--yellow)'
          const isEditing=editIdx===i
          const rowExtra = [r.location, r.tag_ids?.length > 0 ? `${r.tag_ids.length} tag${r.tag_ids.length>1?'s':''}` : null].filter(Boolean).join(' · ')
          return (
            <div key={i} style={{ display:'flex',alignItems:'center',gap:'0.5rem',padding:'0.6rem 0.75rem',background:isEditing?'var(--green-dim)':'var(--bg3)',borderRadius:'var(--radius)',border:`1px solid ${isEditing?'var(--green)':'var(--border)'}`,marginBottom:'0.4rem' }}>
              <span style={{ fontSize:'0.65rem',fontFamily:'var(--font-mono)',color:'var(--text3)',minWidth:18 }}>#{i+1}</span>
              <span style={{ fontSize:'0.65rem',fontWeight:700,color,minWidth:52,textTransform:'uppercase' }}>{r.transaction_type}</span>
              <div style={{ flex:1,minWidth:0 }}>
                <div style={{ fontSize:'0.8rem',fontWeight:600,overflow:'hidden',textOverflow:'ellipsis',whiteSpace:'nowrap' }}>{r.description||'—'}</div>
                <div style={{ fontSize:'0.65rem',color:'var(--text2)' }}>
                  {r.vault_name} · {r.category||'—'}
                  {rowExtra && <> · <span style={{ color:'var(--text3)' }}>{rowExtra}</span></>}
                </div>
              </div>
              <span className="mono" style={{ color,fontWeight:700,fontSize:'0.8rem',flexShrink:0 }}>
                {isD?'+':isW?'-':'↔'}{Number(r.amount).toLocaleString('en-EG',{minimumFractionDigits:2})}
              </span>
              <button onClick={() => startEdit(i)} style={{ background:'none',border:'none',color:'var(--text2)',cursor:'pointer',fontSize:'0.85rem',padding:'2px 4px' }}>✏️</button>
              <button onClick={() => copyRow(i)}   style={{ background:'none',border:'none',color:'var(--text2)',cursor:'pointer',fontSize:'0.85rem',padding:'2px 4px' }}>📋</button>
              <button onClick={() => removeRow(i)} style={{ background:'none',border:'none',color:'var(--text3)',cursor:'pointer',fontSize:'1rem',  padding:'2px 4px' }}>✕</button>
            </div>
          )
        })}
        {errors.length > 0 && (
          <div style={{ background:'rgba(255,77,109,0.1)',border:'1px solid rgba(255,77,109,0.3)',borderRadius:'var(--radius)',padding:'0.75rem',marginTop:'0.75rem' }}>
            {errors.map((e,i) => <div key={i} style={{ color:'var(--red)',fontSize:'0.8rem',marginBottom:'0.2rem' }}>{e.row_number>0?`Row ${e.row_number}: `:''}{e.message || e.field}</div>)}
          </div>
        )}
        <button className="btn btn-primary btn-full" style={{ marginTop:'1rem' }} onClick={validateAndSubmit} disabled={submitting}>
          {submitting ? <Spinner size={16}/> : `Submit ${rows.length} transaction${rows.length!==1?'s':''} →`}
        </button>
        <button className="btn btn-ghost btn-full" style={{ marginTop:'0.4rem' }} onClick={() => {setRows([]);setErrors([])}}>Clear all</button>
      </>}
    </>
  )
}

// ── Root page ──────────────────────────────────────────────────────────────
export default function AddTransactionPage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const [tab, setTab] = useState(() => searchParams.get('tab') === 'bulk' ? 'bulk' : 'single')

  const [vaults, setVaults]         = useState([])
  const [categories, setCategories] = useState([])
  const [units, setUnits]           = useState([])
  const [users, setUsers]           = useState([])
  const [tags, setTags]             = useState([])
  const [loading, setLoading]       = useState(true)

  useEffect(() => {
    Promise.all([
      api.get('/vaults'), api.get('/categories'),
      api.get('/units'),  api.get('/users'), api.get('/tags'),
    ]).then(([v, c, u, us, t]) => {
      setVaults(v.data); setCategories(c.data); setUnits(u.data)
      setUsers(us.data); setTags(t.data)
    }).catch(() => {}).finally(() => setLoading(false))
  }, [])

  if (loading) return <PageLoader />

  return (
    <div className="page fade-up">
      <div className="page-header">
        <div className="page-title">Add</div>
        <button className="btn btn-ghost btn-sm" onClick={() => navigate(-1)}>← Back</button>
      </div>

      {/* Single / Bulk tab switcher */}
      <div style={{ display:'flex', background:'var(--bg3)', borderRadius:'var(--radius)', padding:'3px', marginBottom:'1.5rem' }}>
        {['single','bulk'].map(t => (
          <button key={t} onClick={() => setTab(t)} type="button" style={{
            flex:1, padding:'0.5rem', borderRadius:'calc(var(--radius) - 2px)', border:'none',
            background: tab===t ? 'var(--bg2)' : 'transparent',
            color: tab===t ? 'var(--text)' : 'var(--text2)',
            fontWeight: tab===t ? 700 : 500,
            fontSize:'0.8rem', textTransform:'uppercase', letterSpacing:'0.06em',
            fontFamily:'var(--font-ui)', transition:'all 0.15s', cursor:'pointer',
            boxShadow: tab===t ? '0 0 0 1px var(--border)' : 'none',
          }}>{t === 'single' ? 'Single' : 'Bulk'}</button>
        ))}
      </div>

      {tab === 'single'
        ? <SingleForm vaults={vaults} categories={categories} units={units} users={users} tags={tags} />
        : <BulkForm   vaults={vaults} categories={categories} units={units} tags={tags} />
      }
    </div>
  )
}
