import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../api/client'
import { Spinner, PageLoader } from '../components/ui'

function formatDate(d) {
  if (!d) return undefined
  const s = d.replace('T', ' ')
  return s.length === 16 ? s + ':00' : s
}

const EMPTY = { transaction_type: 'Withdraw', vault_name: '', amount: '', category: '', description: '', comment: '', quantity: '', unit: '', date: '' }

export default function BulkListPage() {
  const [vaults, setVaults]         = useState([])
  const [categories, setCategories] = useState([])
  const [units, setUnits]           = useState([])
  const [loading, setLoading]       = useState(true)
  const [rows, setRows]             = useState([])
  const [form, setForm]             = useState({ ...EMPTY })
  const [editIdx, setEditIdx]       = useState(null) // null = adding new, number = editing existing
  const [submitting, setSubmitting] = useState(false)
  const [errors, setErrors]         = useState([])
  const [result, setResult]         = useState(null)
  const navigate = useNavigate()
  const set = (k, v) => setForm(p => ({ ...p, [k]: v }))

  useEffect(() => {
    Promise.all([api.get('/vaults'), api.get('/categories'), api.get('/units')])
      .then(([v, c, u]) => {
        setVaults(v.data); setCategories(c.data); setUnits(u.data)
        setForm(p => ({ ...p, vault_name: v.data[0]?.vault_name || '', category: c.data[0]?.category_name || '' }))
      }).finally(() => setLoading(false))
  }, [])

  function addOrUpdate(e) {
    e.preventDefault()
    if (!form.amount || !form.vault_name) return
    if (editIdx !== null) {
      setRows(prev => prev.map((r, i) => i === editIdx ? { ...form } : r))
      setEditIdx(null)
    } else {
      setRows(prev => [...prev, { ...form }])
      // Keep everything EXCEPT amount/description/comment/qty — user usually varies those
      setForm(p => ({ ...p, amount: '', description: '', comment: '', quantity: '' }))
    }
    setErrors([])
  }

  function startEdit(i) {
    setEditIdx(i)
    setForm({ ...rows[i] })
  }

  function copyRow(i) {
    setEditIdx(null)
    setForm({ ...rows[i], amount: '', description: '' }) // copy type/vault/cat but clear amount+desc
  }

  function removeRow(i) {
    setRows(prev => prev.filter((_, idx) => idx !== i))
    if (editIdx === i) { setEditIdx(null); setForm({ ...EMPTY }) }
    setErrors([])
  }

  function cancelEdit() { setEditIdx(null); setForm(p => ({ ...p, amount: '', description: '', comment: '', quantity: '' })) }

  async function validateAndSubmit() {
    if (!rows.length) return
    setSubmitting(true); setErrors([])
    try {
      const payload = rows.map((r, i) => ({
        row_number: i + 1, transaction_type: r.transaction_type, vault_name: r.vault_name,
        amount: parseFloat(r.amount), category: r.category || undefined,
        description: r.description || '', comment: r.comment || undefined,
        quantity: r.quantity ? parseFloat(r.quantity) : undefined,
        unit: r.unit || undefined, date: formatDate(r.date),
      }))
      const val = await api.post('/bulk/validate', { rows: payload })
      if (!val.data.is_valid) { setErrors(val.data.errors); setSubmitting(false); return }
      const res = await api.post('/bulk/submit', { rows: payload })
      setResult(res.data)
    } catch (err) {
      setErrors([{ row_number: 0, message: err.response?.data?.detail || 'Failed' }])
    } finally { setSubmitting(false) }
  }

  const totalNet = rows.reduce((s, r) => s + (r.transaction_type === 'Deposit' ? 1 : r.transaction_type === 'Withdraw' ? -1 : 0) * (parseFloat(r.amount) || 0), 0)

  if (loading) return <PageLoader />
  if (result) return (
    <div style={{ flex:1,display:'flex',flexDirection:'column',alignItems:'center',justifyContent:'center',gap:'1rem',padding:'2rem',textAlign:'center' }}>
      <div style={{ fontSize:'3rem' }}>✓</div>
      <div style={{ color:'var(--green)',fontWeight:700,fontSize:'1.2rem' }}>Done! {result.successful} added · {result.failed} failed</div>
      <button className="btn btn-primary" onClick={() => navigate('/dashboard')}>Dashboard</button>
      <button className="btn btn-ghost" onClick={() => { setResult(null); setRows([]) }}>Add more</button>
    </div>
  )

  return (
    <div className="page fade-up">
      <div className="page-header">
        <div className="page-title">{editIdx !== null ? `Editing row ${editIdx + 1}` : 'Bulk — List'}</div>
        <button className="btn btn-ghost btn-sm" onClick={() => navigate('/bulk/spreadsheet')}>Spreadsheet →</button>
      </div>

      {/* Form */}
      <div className="card" style={{ marginBottom:'1rem', border: editIdx !== null ? '1px solid var(--green)' : '1px solid var(--border)' }}>
        <form onSubmit={addOrUpdate} style={{ display:'flex',flexDirection:'column',gap:'0.6rem' }}>
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
          <div style={{ display:'grid',gridTemplateColumns:'1fr 1fr',gap:'0.5rem' }}>
            <div className="field"><label>Amount</label>
              <input className="input mono" type="number" step="0.01" min="0.01" placeholder="0.00" value={form.amount} onChange={e => set('amount', e.target.value)} required autoFocus />
            </div>
            <div className="field"><label>Category</label>
              <select className="input" value={form.category} onChange={e => set('category', e.target.value)}>
                {categories.map(c => <option key={c.category_id} value={c.category_name}>{c.category_name}</option>)}
              </select>
            </div>
          </div>
          <div className="field"><label>Description</label>
            <input className="input" type="text" placeholder="What was this?" value={form.description} onChange={e => set('description', e.target.value)} />
          </div>
          {form.transaction_type === 'Withdraw' && (
            <div style={{ display:'grid',gridTemplateColumns:'1fr 1fr',gap:'0.5rem' }}>
              <div className="field"><label>Qty (opt)</label>
                <input className="input mono" type="number" step="0.01" min="0" value={form.quantity} onChange={e => set('quantity', e.target.value)} />
              </div>
              <div className="field"><label>Unit (opt)</label>
                <select className="input" value={form.unit} onChange={e => set('unit', e.target.value)}>
                  <option value="">—</option>
                  {units.map(u => <option key={u.unit_id} value={u.unit_name}>{u.unit_name}</option>)}
                </select>
              </div>
            </div>
          )}
          <div className="field"><label>Comment (opt)</label>
            <input className="input" type="text" value={form.comment} onChange={e => set('comment', e.target.value)} />
          </div>
          <div className="field"><label>Date (opt)</label>
            <input className="input" type="datetime-local" value={form.date} onChange={e => set('date', e.target.value)} />
          </div>
          <div style={{ display:'flex',gap:'0.5rem',marginTop:'0.25rem' }}>
            {editIdx !== null && <button type="button" className="btn btn-ghost" onClick={cancelEdit}>Cancel</button>}
            <button type="submit" className="btn btn-primary" style={{ flex:1 }}>
              {editIdx !== null ? '✓ Save edit' : '+ Add to list'}
            </button>
          </div>
        </form>
      </div>

      {/* List */}
      {rows.length > 0 && <>
        <div style={{ display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:'0.5rem' }}>
          <div style={{ fontSize:'0.7rem',color:'var(--text2)',fontWeight:700,textTransform:'uppercase',letterSpacing:'0.08em' }}>{rows.length} rows</div>
          <div className="mono" style={{ fontSize:'0.85rem',color:totalNet>=0?'var(--green)':'var(--red)',fontWeight:700 }}>
            Net: {totalNet>=0?'+':''}{totalNet.toLocaleString('en-EG',{minimumFractionDigits:2})} EGP
          </div>
        </div>

        {rows.map((r, i) => {
          const isDeposit = r.transaction_type==='Deposit', isWithdraw=r.transaction_type==='Withdraw'
          const color = isDeposit?'var(--green)':isWithdraw?'var(--red)':'var(--yellow)'
          const isEditing = editIdx === i
          return (
            <div key={i} style={{ display:'flex',alignItems:'center',gap:'0.5rem',padding:'0.6rem 0.75rem',background:isEditing?'var(--green-dim)':'var(--bg3)',borderRadius:'var(--radius)',border:`1px solid ${isEditing?'var(--green)':'var(--border)'}`,marginBottom:'0.4rem' }}>
              <span style={{ fontSize:'0.65rem',fontFamily:'var(--font-mono)',color:'var(--text3)',minWidth:18 }}>#{i+1}</span>
              <span style={{ fontSize:'0.65rem',fontWeight:700,color,minWidth:52,textTransform:'uppercase' }}>{r.transaction_type}</span>
              <div style={{ flex:1,minWidth:0 }}>
                <div style={{ fontSize:'0.8rem',fontWeight:600,overflow:'hidden',textOverflow:'ellipsis',whiteSpace:'nowrap' }}>{r.description||'—'}</div>
                <div style={{ fontSize:'0.65rem',color:'var(--text2)' }}>{r.vault_name} · {r.category||'—'}</div>
              </div>
              <span className="mono" style={{ color,fontWeight:700,fontSize:'0.8rem',flexShrink:0 }}>
                {isDeposit?'+':isWithdraw?'-':'↔'}{Number(r.amount).toLocaleString('en-EG',{minimumFractionDigits:2})}
              </span>
              {/* Actions */}
              <button title="Edit" onClick={() => startEdit(i)} style={{ background:'none',border:'none',color:'var(--text2)',cursor:'pointer',fontSize:'0.85rem',padding:'2px 4px' }}>✏️</button>
              <button title="Copy" onClick={() => copyRow(i)} style={{ background:'none',border:'none',color:'var(--text2)',cursor:'pointer',fontSize:'0.85rem',padding:'2px 4px' }}>📋</button>
              <button title="Remove" onClick={() => removeRow(i)} style={{ background:'none',border:'none',color:'var(--text3)',cursor:'pointer',fontSize:'1rem',padding:'2px 4px' }}>✕</button>
            </div>
          )
        })}

        {errors.length > 0 && (
          <div style={{ background:'rgba(255,77,109,0.1)',border:'1px solid rgba(255,77,109,0.3)',borderRadius:'var(--radius)',padding:'0.75rem',marginTop:'0.75rem' }}>
            {errors.map((e,i) => <div key={i} style={{ color:'var(--red)',fontSize:'0.8rem',marginBottom:'0.2rem' }}>{e.row_number>0?`Row ${e.row_number}: `:''}{e.message}</div>)}
          </div>
        )}

        <button className="btn btn-primary btn-full btn-lg" style={{ marginTop:'1rem' }} onClick={validateAndSubmit} disabled={submitting}>
          {submitting ? <Spinner size={16}/> : `Submit ${rows.length} transaction${rows.length!==1?'s':''} →`}
        </button>
        <button className="btn btn-ghost btn-full" style={{ marginTop:'0.4rem' }} onClick={() => { setRows([]); setErrors([]) }}>Clear all</button>
      </>}
    </div>
  )
}
