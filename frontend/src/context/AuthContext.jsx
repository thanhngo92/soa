import { createContext, useContext, useState, useCallback, useEffect } from 'react'
import { getMeApi } from '../services/authService'

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

  const logout = useCallback(() => {
    localStorage.removeItem('token')
    setToken(null)
    setUser(null)
  }, [])

  // Định danh người dùng và cập nhật thông tin mới nhất từ /accounts/me
  const refreshProfile = useCallback(async () => {
    const currentToken = localStorage.getItem('token')
    if (!currentToken) return null

    try {
      const res = await getMeApi()
      const profileData = res?.data?.data
      if (profileData) {
        setUser((prev) => ({
          ...(prev || safeDecodeJwt(currentToken)),
          ...profileData,
        }))
        return profileData
      }
    } catch (err) {
      if (err.response?.status === 401) {
        logout()
      }
    }
    return null
  }, [logout])

  const login = useCallback((accessToken) => {
    localStorage.setItem('token', accessToken)
    setToken(accessToken)
    setUser(safeDecodeJwt(accessToken))
  }, [])

  // Định danh ngay khi đăng nhập/mount và gọi lặp lại mỗi 30s để cập nhật thông tin mới nhất
  useEffect(() => {
    if (!token) return

    refreshProfile()

    const intervalId = setInterval(() => {
      refreshProfile()
    }, 30000)

    return () => clearInterval(intervalId)
  }, [token, refreshProfile])

  return (
    <AuthContext.Provider
      value={{
        token,
        user,
        profile: user,
        login,
        logout,
        refreshProfile,
        refreshUser: refreshProfile,
        isAuthenticated: !!token,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuthContext() {
  return useContext(AuthContext)
}
