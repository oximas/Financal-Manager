import { useState, useEffect } from 'react'
import api from '../api/client'
import { PageLoader, useToast, Spinner } from '../components/ui'

export default function VaultsPage() {
  const [vaults, setVaults]     = useState([])
  const [loading, setLoading]   = useState(true)
  const [newName, setNewName]   = useState('')
  const [adding, setAdding]     = useState(false)
  const toast = useToast()

  async function load() {
    const res = await api.get('/vaults')
    setVaults(res.data)
    setLoading(false)
  }
  useEffect(() => { load() }, [])

  async function addVault(e) {
    e.preventDefault()
    if (!newName.trim()) return
    setAdding(true)
    try {
      await api.post('/vaults', { vault_name: newName.trim() })
      setNewName('')
      toast.success(`Vault "${newName}" created`)
      load()
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to create vault')
    } finally { setAdding(false) }
  }

  async function deleteVault(name) {
    if (!confirm(`Delete vault "${name}"? It must have a zero balance.`)) return
    try {
      await api.delete(`/vaults/${encodeURIComponent(name)}`)
      toast.success(`Vault "${name}" deleted`)
      load()
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Cannot delete vault')
    }
  }

  const totalBalance = vaults.reduce((s, v) => s + v.balance, 0)

  if (loading) return <PageLoader />

  return (
    <div className="page fade-up">
      <div className="page-header">
        <div className="page-title">Vaults</div>
        <span className="mono" style={{ fontSize: '0.85rem', color: 'var(--green)' }}>
          {totalBalance.toLocaleString('en-EG', { minimumFractionDigits: 2 })} EGP
        </span>
      </div>

      {/* Add vault form */}
      <form onSubmit={addVault} style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.5rem' }}>
        <input className="input" placeholder="New vault name..." value={newName}
          onChange={e => setNewName(e.target.value)} style={{ flex: 1 }} />
        <button type="submit" className="btn btn-primary" disabled={adding}>
          {adding ? <Spinner size={16} /> : '+ Add'}
        </button>
      </form>

      {/* Vault list */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
        {vaults.map(v => (
          <div key={v.vault_id} className="card" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div>
              <div style={{ fontWeight: 700, fontSize: '0.95rem' }}>{v.vault_name}</div>
              <div className="mono" style={{
                fontSize: '1.1rem', marginTop: '0.2rem',
                color: v.balance > 0 ? 'var(--green)' : v.balance < 0 ? 'var(--red)' : 'var(--text2)',
              }}>
                {v.balance.toLocaleString('en-EG', { minimumFractionDigits: 2 })} EGP
              </div>
            </div>
            {v.balance === 0 && (
              <button className="btn btn-danger btn-sm" onClick={() => deleteVault(v.vault_name)}>
                Delete
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
