import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
})

// Attach JWT token to every request
api.interceptors.request.use(config => {
  const token = localStorage.getItem('pfm_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// On 401, clear token and redirect to login
api.interceptors.response.use(
  res => res,
  err => {
    if (err.response?.status === 401) {
      localStorage.removeItem('pfm_token')
      localStorage.removeItem('pfm_user')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

/**
 * Trigger a CSV download for the current user's transactions.
 * @param {string|null} dateFrom  - "YYYY-MM-DD" or null for no lower bound
 * @param {string|null} dateTo    - "YYYY-MM-DD" or null for no upper bound
 */
export async function exportCSV(dateFrom = null, dateTo = null) {
  const params = {}
  if (dateFrom) params.date_from = dateFrom
  if (dateTo)   params.date_to   = dateTo

  const response = await api.get('/export/csv', {
    params,
    responseType: 'blob',   // tell axios to treat the response as a raw file
  })

  // Pull filename from Content-Disposition header if present, else use a fallback
  const disposition = response.headers['content-disposition'] || ''
  const match = disposition.match(/filename="(.+?)"/)
  const filename = match ? match[1] : `transactions_${new Date().toISOString().slice(0, 10)}.csv`

  // Create a temporary <a> and click it to trigger the browser download
  const url = URL.createObjectURL(new Blob([response.data], { type: 'text/csv' }))
  const a   = document.createElement('a')
  a.href     = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}

export default api
