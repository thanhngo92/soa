import { createContext, useContext, useState, useCallback } from 'react'

const AuthContext = createContext(null)

function safeDecodeJwt(t) {
  if (!t || typeof t !== 'string') return null
  try {
    const parts = t.split('.')
    if (parts.length < 2) return null
    const base64 = parts[1].replace(/-/g, '+').replace(/_/g, '/')
    const decodedStr = decodeURIComponent(
      atob(base64)
        .split('')
        .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
    )
    return JSON.parse(decodedStr)
  } catch {
    return null
  }
}

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem('token'))
  const [user, setUser]   = useState(() => safeDecodeJwt(localStorage.getItem('token')))

  const login = useCallback((accessToken) => {
    localStorage.setItem('token', accessToken)
    setToken(accessToken)
    setUser(safeDecodeJwt(accessToken))
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem('token')
    setToken(null)
    setUser(null)
  }, [])

  return (
    <AuthContext.Provider value={{ token, user, login, logout, isAuthenticated: !!token }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuthContext() {
  return useContext(AuthContext)
}
