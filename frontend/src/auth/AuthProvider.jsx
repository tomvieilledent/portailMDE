/** Contexte d'authentification : session de l'utilisateur, connexion et déconnexion. */

import { useQueryClient } from '@tanstack/react-query'
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'

import { api } from '../lib/api'
import { tokens } from '../lib/tokens'

/** Contexte portant la session courante. */
const AuthContext = createContext(null)

/**
 * Session de l'utilisateur : charge `/users/me` au démarrage si un jeton existe,
 * expose `login`/`logout` et se vide si l'API signale une session expirée.
 */
export function AuthProvider({ children }) {
  const queryClient = useQueryClient()
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(Boolean(tokens.access))

  const clearSession = useCallback(() => {
    tokens.clear()
    setUser(null)
    queryClient.clear()
  }, [queryClient])

  useEffect(() => {
    if (!tokens.access) return undefined
    let cancelled = false
    api
      .get('/users/me')
      .then((me) => !cancelled && setUser(me))
      .catch(() => !cancelled && clearSession())
      .finally(() => !cancelled && setLoading(false))
    return () => {
      cancelled = true
    }
  }, [clearSession])

  useEffect(() => {
    window.addEventListener('auth:logout', clearSession)
    return () => window.removeEventListener('auth:logout', clearSession)
  }, [clearSession])

  const login = useCallback(async (email, password) => {
    const pair = await api.post('/auth/login', { email, password }, { auth: false })
    tokens.set(pair)
    const me = await api.get('/users/me')
    setUser(me)
    return me
  }, [])

  const logout = useCallback(async () => {
    try {
      if (tokens.access) await api.post('/auth/logout', { refresh_token: tokens.refresh })
    } catch {
      /* la session locale est vidée dans tous les cas */
    }
    clearSession()
  }, [clearSession])

  const value = useMemo(
    () => ({ user, loading, login, logout, setUser, isAuthenticated: Boolean(user) }),
    [user, loading, login, logout],
  )
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

/** Accès à la session de l'utilisateur connecté. */
// eslint-disable-next-line react-refresh/only-export-components
export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth doit être utilisé dans un AuthProvider')
  return context
}
