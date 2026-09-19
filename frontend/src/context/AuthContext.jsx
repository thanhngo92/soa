import { createContext, useContext, useState, useCallback } from 'react'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem('token'))
  const [user, setUser]   = useState(() => {
    try {
      const t = localStorage.getItem('token')
      if (!t) return null
      return JSON.parse(atob(t.split('.')[1]))   // decode JWT payload
    } catch {
      return null
    }
  })

  const login = useCallback((accessToken) => {
    localStorage.setItem('token', accessToken)
    setToken(accessToken)
    try {
      setUser(JSON.parse(atob(accessToken.split('.')[1])))
    } catch {
      setUser(null)
    }
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
