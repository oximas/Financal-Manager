import { createContext, useContext, useState, useCallback } from 'react'
import api from '../api/client'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try { return JSON.parse(localStorage.getItem('pfm_user')) } catch { return null }
  })

  const login = useCallback(async (username, password) => {
    const res = await api.post('/auth/login', { username, password })
    localStorage.setItem('pfm_token', res.data.access_token)
    localStorage.setItem('pfm_user', JSON.stringify({ username: res.data.username }))
    setUser({ username: res.data.username })
    return res.data
  }, [])

  const signup = useCallback(async (username, password, confirm_password) => {
    const res = await api.post('/auth/signup', { username, password, confirm_password })
    localStorage.setItem('pfm_token', res.data.access_token)
    localStorage.setItem('pfm_user', JSON.stringify({ username: res.data.username }))
    setUser({ username: res.data.username })
    return res.data
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem('pfm_token')
    localStorage.removeItem('pfm_user')
    setUser(null)
  }, [])

  return (
    <AuthContext.Provider value={{ user, login, signup, logout, isLoggedIn: !!user }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
