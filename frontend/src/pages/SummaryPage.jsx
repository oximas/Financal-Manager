import { useState, useEffect } from 'react'
import api from '../api/client'
import { PageLoader } from '../components/ui'
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis,
  Tooltip, ResponsiveContainer, Cell, Legend
} from 'recharts'
import { format, subDays, subMonths, startOfMonth, endOfMonth } from 'date-fns'

const GREEN  = '#00ffc6'
const RED    = '#ff4d6d'
const YELLOW = '#ffd166'
const COLORS = ['#00ffc6','#ffd166','#ff4d6d','#818cf8','#fb923c','#34d399','#f472b6','#60a5fa','#a78bfa','#4ade80']

const RANGES = [
  { label: 'This month',  key: 'this_month'  },
  { label: 'Last month',  key: 'last_month'  },
  { label: '30 days',     key: '30d'         },
  { label: '90 days',     key: '90d'         },
  { label: 'All time',    key: 'all'         },
  { label: 'Custom',      key: 'custom'      },
]

function getDateRange(key) {
  const now = new Date()
  switch (key) {
    case 'this_month':  return { start: format(startOfMonth(now), 'yyyy-MM-dd'), end: format(now, 'yyyy-MM-dd') }
    case 'last_month':  {
      const lm = subMonths(now, 1)
      return { start: format(startOfMonth(lm), 'yyyy-MM-dd'), end: format(endOfMonth(lm), 'yyyy-MM-dd') }
    }
    case '30d': return { start: format(subDays(now, 30), 'yyyy-MM-dd'), end: format(now, 'yyyy-MM-dd') }
    case '90d': return { start: format(subDays(now, 90), 'yyyy-MM-dd'), end: format(now, 'yyyy-MM-dd') }
    default:    return { start: null, end: null }
  }
}

function StatCard({ label, value, sub, color }) {
  return (
    <div className="card" style={{ flex: 1, minWidth: 0 }}>
      <div style={{ fontSize: '0.65rem', color: 'var(--text2)', fontFamily: 'var(--font-mono)', letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: '0.4rem' }}>{label}</div>
      <div className="mono" style={{ fontSize: '1.15rem', fontWeight: 700, color: color || 'var(--text)' }}>{value}</div>
      {sub && <div style={{ fontSize: '0.7rem', color: 'var(--text3)', marginTop: '0.2rem' }}>{sub}</div>}
    </div>
  )
}

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: 6, padding: '0.6rem 0.9rem', fontSize: '0.8rem' }}>
      <div style={{ color: 'var(--text2)', marginBottom: '0.3rem', fontFamily: 'var(--font-mono)' }}>{label}</div>
      {payload.map((p, i) => (
        <div key={i} style={{ color: p.color, fontFamily: 'var(--font-mono)' }}>
          {p.name}: {Number(p.value).toLocaleString('en-EG', { minimumFractionDigits: 0 })}
        </div>
      ))}
    </div>
  )
}

export default function SummaryPage() {
  const [range, setRange]         = useState('this_month')
  const [customStart, setCS]      = useState('')
  const [customEnd, setCE]        = useState('')
  const [data, setData]           = useState(null)
  const [loading, setLoading]     = useState(true)

  function load(r, cs, ce) {
    setLoading(true)
    let params = {}
    if (r === 'custom') {
      if (cs) params.start_date = cs
      if (ce) params.end_date   = ce
    } else {
      const { start, end } = getDateRange(r)
      if (start) params.start_date = start
      if (end)   params.end_date   = end
    }
    api.get('/analytics', { params })
      .then(res => setData(res.data))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load(range, customStart, customEnd) }, [])

  function applyRange(r) {
    setRange(r)
    if (r !== 'custom') load(r)
  }

  const fmt = n => Number(n || 0).toLocaleString('en-EG', { minimumFractionDigits: 0 })
  const t   = data?.totals || {}

  // Insights generator
  const insights = []
  if (data) {
    if (t.savings_rate > 30)  insights.push({ icon: '🟢', text: `Saving ${t.savings_rate}% of income — strong month` })
    if (t.savings_rate < 0)   insights.push({ icon: '🔴', text: `Spending exceeded income by ${fmt(Math.abs(t.net))} EGP` })
    if (data.category_breakdown[0]) insights.push({ icon: '📊', text: `Biggest spend: ${data.category_breakdown[0].category} at ${fmt(data.category_breakdown[0].amount)} EGP` })
    if (data.monthly?.length > 1) {
      const worst = [...data.monthly].sort((a, b) => a.net - b.net)[0]
      if (worst) insights.push({ icon: '📉', text: `Worst month: ${worst.month} (net ${fmt(worst.net)} EGP)` })
    }
    if (data.top_transactions[0]) insights.push({ icon: '💸', text: `Biggest single expense: ${data.top_transactions[0].description} — ${fmt(data.top_transactions[0].amount)} EGP` })
  }

  return (
    <div className="page fade-up">
      <div className="page-header">
        <div className="page-title">Summary</div>
      </div>

      {/* Range selector */}
      <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap', marginBottom: '1.25rem' }}>
        {RANGES.map(r => (
          <button key={r.key} onClick={() => applyRange(r.key)} style={{
            padding: '0.35rem 0.75rem', borderRadius: 20,
            border: `1px solid ${range === r.key ? 'var(--green)' : 'var(--border)'}`,
            background: range === r.key ? 'var(--green-dim)' : 'transparent',
            color: range === r.key ? 'var(--green)' : 'var(--text2)',
            fontSize: '0.75rem', fontWeight: 600, cursor: 'pointer',
            fontFamily: 'var(--font-ui)', transition: 'all 0.15s',
          }}>
            {r.label}
          </button>
        ))}
      </div>

      {/* Custom date inputs */}
      {range === 'custom' && (
        <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem', alignItems: 'flex-end' }}>
          <div className="field" style={{ flex: 1 }}>
            <label>From</label>
            <input className="input" type="date" value={customStart} onChange={e => setCS(e.target.value)} />
          </div>
          <div className="field" style={{ flex: 1 }}>
            <label>To</label>
            <input className="input" type="date" value={customEnd} onChange={e => setCE(e.target.value)} />
          </div>
          <button className="btn btn-primary btn-sm" onClick={() => load('custom', customStart, customEnd)}>
            Apply
          </button>
        </div>
      )}

      {loading ? <PageLoader /> : !data ? null : (
        <>
          {/* Totals row */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', marginBottom: '1rem' }}>
            <StatCard label="Income"   value={`${fmt(t.income)} EGP`}   color={GREEN} />
            <StatCard label="Expenses" value={`${fmt(t.expenses)} EGP`} color={RED}   />
            <StatCard label="Net"      value={`${fmt(t.net)} EGP`}      color={t.net >= 0 ? GREEN : RED} />
            <StatCard label="Savings rate" value={`${t.savings_rate}%`} color={t.savings_rate >= 0 ? GREEN : RED} sub={`${t.tx_count} transactions`} />
          </div>

          {/* Balance over time */}
          {data.balance_history?.length > 1 && (
            <div className="card" style={{ marginBottom: '1rem' }}>
              <div style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--text2)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '0.75rem' }}>
                Balance Over Time
              </div>
              <ResponsiveContainer width="100%" height={160}>
                <LineChart data={data.balance_history}>
                  <XAxis dataKey="month" tick={{ fill: '#555', fontSize: 10 }} tickLine={false} axisLine={false} />
                  <YAxis hide />
                  <Tooltip content={<CustomTooltip />} />
                  <Line type="monotone" dataKey="balance" stroke={GREEN} strokeWidth={2} dot={false} name="Balance" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Monthly income vs expenses */}
          {data.monthly?.length > 0 && (
            <div className="card" style={{ marginBottom: '1rem' }}>
              <div style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--text2)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '0.75rem' }}>
                Income vs Expenses
              </div>
              <ResponsiveContainer width="100%" height={160}>
                <BarChart data={data.monthly} barGap={2}>
                  <XAxis dataKey="month" tick={{ fill: '#555', fontSize: 10 }} tickLine={false} axisLine={false} />
                  <YAxis hide />
                  <Tooltip content={<CustomTooltip />} />
                  <Bar dataKey="income"   name="Income"   fill={GREEN} radius={[3,3,0,0]} />
                  <Bar dataKey="expenses" name="Expenses" fill={RED}   radius={[3,3,0,0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Category breakdown */}
          {data.category_breakdown?.length > 0 && (
            <div className="card" style={{ marginBottom: '1rem' }}>
              <div style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--text2)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '0.75rem' }}>
                Spending by Category
              </div>
              {data.category_breakdown.map((c, i) => {
                const pct = t.expenses > 0 ? (c.amount / t.expenses * 100).toFixed(1) : 0
                return (
                  <div key={c.category} style={{ marginBottom: '0.6rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', marginBottom: '0.2rem' }}>
                      <span style={{ color: 'var(--text)' }}>{c.category}</span>
                      <span className="mono" style={{ color: COLORS[i % COLORS.length] }}>{fmt(c.amount)} EGP <span style={{ color: 'var(--text3)' }}>({pct}%)</span></span>
                    </div>
                    <div style={{ height: 4, background: 'var(--bg3)', borderRadius: 2 }}>
                      <div style={{ height: '100%', width: `${pct}%`, background: COLORS[i % COLORS.length], borderRadius: 2, transition: 'width 0.4s ease' }} />
                    </div>
                  </div>
                )
              })}
            </div>
          )}

          {/* Vault breakdown */}
          {data.vault_breakdown?.length > 0 && (
            <div className="card" style={{ marginBottom: '1rem' }}>
              <div style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--text2)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '0.75rem' }}>
                Vault Balances
              </div>
              <ResponsiveContainer width="100%" height={Math.max(100, data.vault_breakdown.length * 36)}>
                <BarChart data={data.vault_breakdown} layout="vertical" barSize={16}>
                  <XAxis type="number" hide />
                  <YAxis dataKey="vault_name" type="category" tick={{ fill: '#888', fontSize: 11 }} tickLine={false} axisLine={false} width={80} />
                  <Tooltip content={<CustomTooltip />} />
                  <Bar dataKey="balance" name="Balance" radius={[0,3,3,0]}>
                    {data.vault_breakdown.map((v, i) => (
                      <Cell key={i} fill={v.balance >= 0 ? GREEN : RED} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Insights */}
          {insights.length > 0 && (
            <div className="card" style={{ marginBottom: '1rem' }}>
              <div style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--text2)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '0.75rem' }}>
                Insights
              </div>
              {insights.map((ins, i) => (
                <div key={i} style={{ display: 'flex', gap: '0.6rem', padding: '0.5rem 0', borderBottom: i < insights.length - 1 ? '1px solid var(--border)' : 'none', fontSize: '0.85rem' }}>
                  <span>{ins.icon}</span>
                  <span style={{ color: 'var(--text2)' }}>{ins.text}</span>
                </div>
              ))}
            </div>
          )}

          {/* Top expenses */}
          {data.top_transactions?.length > 0 && (
            <div className="card" style={{ marginBottom: '1rem' }}>
              <div style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--text2)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '0.75rem' }}>
                Biggest Expenses
              </div>
              {data.top_transactions.map((tx, i) => (
                <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '0.5rem 0', borderBottom: i < data.top_transactions.length - 1 ? '1px solid var(--border)' : 'none' }}>
                  <div>
                    <div style={{ fontSize: '0.85rem', fontWeight: 600 }}>{tx.description}</div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text2)' }}>{tx.category} · {tx.vault} · {tx.date}</div>
                  </div>
                  <div className="mono" style={{ color: RED, fontSize: '0.9rem', fontWeight: 700 }}>
                    -{fmt(tx.amount)}
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  )
}
