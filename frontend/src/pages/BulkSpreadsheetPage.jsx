import { useState, useEffect, useRef, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../api/client'
import { Spinner, PageLoader } from '../components/ui'

/*
  Keyboard nav:
  - Enter  → move DOWN  (stay in same column — fill a whole column fast)
  - Tab    → move RIGHT (go to next column)
  - Arrows → navigate freely
  Dropdowns are full native <select> — keyboard works out of the box.
  Transfer adds to_username + to_vault columns automatically.
*/

const BASE_COLS = [
  { key: 'transaction_type', label: 'Type',     width: 100, type: 'select' },
  { key: 'description',      label: 'Desc',      width: 160, type: 'text'   },
  { key: 'amount',           label: 'Amount',    width: 90,  type: 'number' },
  { key: 'vault_name',       label: 'Vault',     width: 110, type: 'select' },
  { key: 'category',         label: 'Category',  width: 110, type: 'select' },
  { key: 'comment',          label: 'Comment',   width: 130, type: 'text'   },
  { key: 'date',             label: 'Date',      width: 160, type: 'datetime-local' },
]
const TRANSFER_COLS = [
  { key: 'to_username', label: 'To User',  width: 110, type: 'text' },
  { key: 'to_vault',    label: 'To Vault', width: 110, type: 'text' },
]

function makeRow(defaults = {}) {
  return { transaction_type:'Withdraw', description:'', amount:'', vault_name: defaults.vault_name||'', category: defaults.category||'', comment:'', date:'', to_username:'', to_vault:'', _err:{} }
}

function formatDate(d) {
  if (!d) return undefined
  const s = d.replace('T',' ')
  return s.length===16 ? s+':00' : s
}

export default function BulkSpreadsheetPage() {
  const [vaults, setVaults]       = useState([])
  const [categories, setCats]     = useState([])
  const [loading, setLoading]     = useState(true)
  const [rows, setRows]           = useState([])
  const [sel, setSel]             = useState({ r:0, c:0 })
  const [submitting, setSub]      = useState(false)
  const [errors, setErrors]       = useState([])
  const [result, setResult]       = useState(null)
  const cellRefs                  = useRef({})
  const navigate                  = useNavigate()
  const hasTransfer               = rows.some(r => r.transaction_type === 'Transfer')
  const COLS                      = hasTransfer ? [...BASE_COLS, ...TRANSFER_COLS] : BASE_COLS

  useEffect(() => {
    Promise.all([api.get('/vaults'), api.get('/categories')])
      .then(([v, c]) => {
        setVaults(v.data); setCats(c.data)
        const def = { vault_name: v.data[0]?.vault_name||'', category: c.data[0]?.category_name||'' }
        setRows(Array.from({length:5}, () => makeRow(def)))
      }).finally(() => setLoading(false))
  }, [])

  // Focus the selected cell
  useEffect(() => {
    const el = cellRefs.current[`${sel.r}-${sel.c}`]
    if (el) el.focus()
  }, [sel])

  function addRows(n=5) {
    const def = { vault_name: vaults[0]?.vault_name||'', category: categories[0]?.category_name||'' }
    setRows(prev => [...prev, ...Array.from({length:n}, ()=>makeRow(def))])
  }

  function updateCell(r, key, val) {
    setRows(prev => prev.map((row, i) => {
      if (i !== r) return row
      const next = { ...row, [key]: val, _err: { ...row._err, [key]: undefined } }
      // Auto-fill vault and category from previous row if empty
      return next
    }))
    setErrors([])
  }

  const move = useCallback((dr, dc) => {
    setSel(prev => {
      let r = prev.r + dr, c = prev.c + dc
      if (r >= rows.length) { addRows(3); r = rows.length }
      r = Math.max(0, Math.min(r, rows.length - 1 + (dr>0?3:0)))
      c = Math.max(0, Math.min(c, COLS.length - 1))
      return { r, c }
    })
  }, [rows.length, COLS.length])

  function handleKey(e, r, c) {
    if (e.key === 'Enter') { e.preventDefault(); move(1, 0) }
    else if (e.key === 'Tab') { e.preventDefault(); if (c < COLS.length-1) move(0,1); else move(1, -(COLS.length-1)) }
    else if (e.key === 'ArrowDown'  && e.ctrlKey) { e.preventDefault(); move(1,0) }
    else if (e.key === 'ArrowUp'    && e.ctrlKey) { e.preventDefault(); move(-1,0) }
  }

  async function submit() {
    setSub(true); setErrors([])
    setRows(prev => prev.map(r => ({ ...r, _err:{} })))
    try {
      // Filter out completely empty rows
      const filled = rows.filter(r => r.description || r.amount)
      if (!filled.length) { setSub(false); return }
      const payload = filled.map((r,i) => ({
        row_number: i+1, transaction_type: r.transaction_type,
        vault_name: r.vault_name, amount: parseFloat(r.amount)||0,
        category: r.category||undefined, description: r.description||'',
        comment: r.comment||undefined, date: formatDate(r.date),
        to_username: r.to_username||undefined, to_vault: r.to_vault||undefined,
      }))
      const val = await api.post('/bulk/validate', { rows: payload })
      if (!val.data.is_valid) {
        const errMap = {}
        for (const e of val.data.errors) { const ri=e.row_number-1; if(!errMap[ri]) errMap[ri]={}; errMap[ri][e.field]=e.message }
        setRows(prev => prev.map((r,i) => ({ ...r, _err: errMap[i]||{} })))
        setErrors(val.data.errors); setSub(false); return
      }
      const res = await api.post('/bulk/submit', { rows: payload })
      setResult(res.data)
    } catch(err) {
      setErrors([{ row_number:0, message: err.response?.data?.detail||'Failed' }])
    } finally { setSub(false) }
  }

  function renderCell(row, r, col, c) {
    const isSel = sel.r===r && sel.c===c
    const hasErr = !!row._err?.[col.key]
    const style = {
      width: '100%', height: 34, padding: '0 8px',
      background: isSel ? 'rgba(0,255,198,0.08)' : hasErr ? 'rgba(255,77,109,0.1)' : 'transparent',
      border: 'none',
      outline: isSel ? '2px solid var(--green)' : hasErr ? '1px solid var(--red)' : 'none',
      outlineOffset: '-1px',
      color: 'var(--text)', fontSize: '0.82rem',
      fontFamily: col.type==='number' ? 'var(--font-mono)' : 'var(--font-ui)',
      cursor: 'pointer', boxSizing: 'border-box',
    }
    const common = {
      ref: el => { cellRefs.current[`${r}-${c}`] = el },
      style,
      onFocus: () => setSel({ r, c }),
      onKeyDown: e => handleKey(e, r, c),
      title: hasErr ? row._err[col.key] : undefined,
    }

    if (col.type === 'select') {
      let options = []
      if (col.key === 'transaction_type') options = ['Deposit','Withdraw','Transfer']
      else if (col.key === 'vault_name')  options = vaults.map(v=>v.vault_name)
      else if (col.key === 'category')    options = categories.map(c=>c.category_name)
      return (
        <select {...common} value={row[col.key]} onChange={e => updateCell(r, col.key, e.target.value)}>
          {options.map(o => <option key={o} value={o}>{o}</option>)}
        </select>
      )
    }
    return (
      <input
        {...common}
        type={col.type}
        value={row[col.key]}
        onChange={e => updateCell(r, col.key, e.target.value)}
        placeholder={col.type==='number' ? '0.00' : ''}
      />
    )
  }

  if (loading) return <PageLoader />
  if (result) return (
    <div style={{ flex:1,display:'flex',flexDirection:'column',alignItems:'center',justifyContent:'center',gap:'1rem',padding:'2rem',textAlign:'center' }}>
      <div style={{ fontSize:'3rem' }}>✓</div>
      <div style={{ color:'var(--green)',fontWeight:700 }}>Done! {result.successful} added · {result.failed} failed</div>
      <button className="btn btn-primary" onClick={() => navigate('/dashboard')}>Dashboard</button>
      <button className="btn btn-ghost" onClick={() => setResult(null)}>Add more</button>
    </div>
  )

  const filledCount = rows.filter(r => r.description || r.amount).length

  return (
    <div style={{ display:'flex',flexDirection:'column',flex:1,padding:'0 0 6rem' }}>
      <div className="page-header" style={{ padding:'1.25rem 1rem 0.75rem',position:'sticky',top:0,background:'rgba(10,10,10,0.95)',backdropFilter:'blur(20px)',zIndex:10,borderBottom:'1px solid var(--border)' }}>
        <div style={{ display:'flex',alignItems:'center',justifyContent:'space-between' }}>
          <div className="page-title">Bulk — Spreadsheet</div>
          <button className="btn btn-ghost btn-sm" onClick={() => navigate('/bulk/list')}>List mode →</button>
        </div>
        <div style={{ fontSize:'0.65rem',color:'var(--text3)',fontFamily:'var(--font-mono)',marginTop:'0.35rem' }}>
          Enter = down · Tab = right · Empty rows are skipped on submit
        </div>
      </div>

      {/* Scrollable table */}
      <div style={{ overflowX:'auto', flex:1 }}>
        <table style={{ borderCollapse:'collapse', minWidth: COLS.reduce((s,c)=>s+c.width,0)+50 }}>
          <thead style={{ position:'sticky',top:0,zIndex:5,background:'var(--bg2)' }}>
            <tr style={{ borderBottom:'2px solid var(--border)' }}>
              <th style={{ width:40,padding:'0.4rem 8px',color:'var(--text3)',fontSize:'0.6rem',fontFamily:'var(--font-mono)',textAlign:'center',borderRight:'1px solid var(--border)' }}>#</th>
              {COLS.map(col => (
                <th key={col.key} style={{ width:col.width,padding:'0.4rem 8px',color:'var(--text2)',fontSize:'0.62rem',fontFamily:'var(--font-mono)',textTransform:'uppercase',letterSpacing:'0.08em',textAlign:'left',borderRight:'1px solid var(--border)',fontWeight:700 }}>
                  {col.label}
                </th>
              ))}
              <th style={{ width:36 }}></th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row, r) => {
              const hasAnyErr = Object.values(row._err||{}).some(Boolean)
              return (
                <tr key={r} style={{ borderBottom:'1px solid var(--border)', background: hasAnyErr?'rgba(255,77,109,0.04)': sel.r===r?'rgba(0,255,198,0.02)':'transparent' }}>
                  <td style={{ textAlign:'center',color:'var(--text3)',fontSize:'0.62rem',fontFamily:'var(--font-mono)',padding:'0 4px',borderRight:'1px solid var(--border)' }}>{r+1}</td>
                  {COLS.map((col, c) => (
                    <td key={col.key} style={{ padding:0,borderRight:'1px solid var(--border)',width:col.width }}>
                      {renderCell(row, r, col, c)}
                    </td>
                  ))}
                  <td style={{ padding:'0 4px',textAlign:'center' }}>
                    <button onClick={() => setRows(prev=>prev.filter((_,i)=>i!==r))} style={{ background:'none',border:'none',color:'var(--text3)',cursor:'pointer',fontSize:'0.85rem' }}>✕</button>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {/* Footer */}
      <div style={{ padding:'0.75rem 1rem',borderTop:'1px solid var(--border)',background:'var(--bg)',display:'flex',flexDirection:'column',gap:'0.5rem',position:'sticky',bottom:'4.5rem' }}>
        <button className="btn btn-ghost btn-sm" style={{ alignSelf:'flex-start' }} onClick={() => addRows(5)}>+ 5 rows</button>

        {errors.length > 0 && (
          <div style={{ background:'rgba(255,77,109,0.1)',border:'1px solid rgba(255,77,109,0.3)',borderRadius:'var(--radius)',padding:'0.6rem 0.75rem' }}>
            {errors.slice(0,4).map((e,i) => <div key={i} style={{ color:'var(--red)',fontSize:'0.75rem' }}>{e.row_number>0?`Row ${e.row_number}: `:''}{e.message}</div>)}
            {errors.length>4 && <div style={{ color:'var(--text3)',fontSize:'0.7rem' }}>+{errors.length-4} more</div>}
          </div>
        )}

        <button className="btn btn-primary btn-full" onClick={submit} disabled={submitting||!filledCount} style={{ fontSize:'0.9rem',padding:'0.7rem' }}>
          {submitting ? <Spinner size={16}/> : `Submit ${filledCount} row${filledCount!==1?'s':''} →`}
        </button>
      </div>
    </div>
  )
}
