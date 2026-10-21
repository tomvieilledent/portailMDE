// Contexte d'authentification : expose `user`, `login`, `logout` à toute l'app.
// Le token vit dans localStorage (via lib/api). Au montage, si un token existe,
// on récupère le profil courant (/users/me) pour restaurer la session.

import React, { createContext, useContext, useEffect, useState } from 'react'
import { api, getToken, setTokens, clearTokens } from '../lib/api'
import { connectSocket, disconnectSocket } from '../lib/socket'

const AuthContext = createContext(null)

// Le backend n'a pas de champ `role`. L'UI distingue trois rôles :
//   - admin   : super administrateur (is_super_admin)
//   - patron  : administrateur d'une entreprise (Company.admin_id/admin_email)
//   - salarie : utilisateur simple
// Le statut « patron » n'est pas porté par l'objet user : on le déduit en
// regardant si l'utilisateur administre une entreprise (companyAdminId).
export function roleOf(user, companyAdminId = null) {
  if (!user) return 'guest'
  if (user.is_super_admin) return 'admin'
  // « patron » = administrateur d'une entreprise : soit porté explicitement par
  // le flag is_company_admin (co-responsables), soit déduit de l'entreprise
  // administrée (champ admin_id/admin_email, détecté dans companyAdminId).
  if (user.is_company_admin || companyAdminId) return 'patron'
  return 'salarie'
}

// Retrouve l'entreprise administrée par l'utilisateur (ou null).
// Best-effort : en cas d'échec réseau on retombe sur « salarie ».
async function findAdministeredCompany(user) {
  if (!user) return null
  try {
    const res = await api.getCompanies()
    const companies = Array.isArray(res) ? res : res?.companies || []
    const email = (user.email || '').toLowerCase().trim()
    const match = companies.find(
      (c) => c.admin_id === user.id || (c.admin_email || '').toLowerCase().trim() === email
    )
    return match || null
  } catch (_) {
    return null
  }
}

// Nom d'affichage + initiales, calculés une fois pour le Header.
export function displayName(user) {
  if (!user) return ''
  const full = [user.first_name, user.last_name].filter(Boolean).join(' ')
  return full || user.email
}

export function initialsOf(user) {
  if (!user) return '?'
  const full = [user.first_name, user.last_name].filter(Boolean)
  if (full.length) return full.map((p) => p[0]).join('').slice(0, 2).toUpperCase()
  return (user.email || '?').slice(0, 2).toUpperCase()
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [companyAdminId, setCompanyAdminId] = useState(null)
  const [companyAdminName, setCompanyAdminName] = useState(null)
  const [loading, setLoading] = useState(true)

  // Installe l'utilisateur authentifié + détecte son éventuel rôle « patron ».
  async function establishSession(u) {
    setUser(u)
    connectSocket()
    const company = await findAdministeredCompany(u)
    setCompanyAdminId(company?.id || null)
    setCompanyAdminName(company?.name || null)
  }

  // Restauration de session au démarrage.
  useEffect(() => {
    let cancelled = false
    async function restore() {
      if (!getToken()) {
        setLoading(false)
        return
      }
      try {
        const { user } = await api.me()
        if (!cancelled) await establishSession(user)
      } catch (err) {
        // On n'invalide la session que si le token est réellement refusé (401),
        // pas sur une coupure réseau / backend momentanément indisponible.
        if (err?.status === 401) clearTokens()
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    restore()
    return () => { cancelled = true }
  }, [])

  // Déconnexion forcée déclenchée par le client API sur un 401 authentifié.
  useEffect(() => {
    const onForcedLogout = () => { disconnectSocket(); setUser(null); setCompanyAdminId(null); setCompanyAdminName(null) }
    window.addEventListener('auth:logout', onForcedLogout)
    return () => window.removeEventListener('auth:logout', onForcedLogout)
  }, [])

  async function login(email, password) {
    const data = await api.login(email, password) // peut throw -> géré par l'appelant
    setTokens(data)
    await establishSession(data.user)
    return data.user
  }

  // Inscription : crée le compte puis connecte automatiquement l'utilisateur.
  async function register(payload) {
    const data = await api.register(payload) // {user, access_token, refresh_token}
    setTokens(data)
    await establishSession(data.user)
    return data.user
  }

  // Met à jour le profil courant (PATCH /users/me, multipart accepté) et
  // rafraîchit l'utilisateur en mémoire pour que le Header / pages suivent.
  async function updateProfile(payload) {
    const { user: updated } = await api.updateMe(payload)
    setUser(updated)
    return updated
  }

  async function logout() {
    try {
      await api.logout() // révoque le JTI côté backend
    } catch (_) {
      /* on déconnecte localement même si l'appel échoue */
    }
    disconnectSocket()
    clearTokens()
    setUser(null)
    setCompanyAdminId(null)
    setCompanyAdminName(null)
  }

  const role = roleOf(user, companyAdminId)
  // Droits du staff : un super admin les possède tous implicitement, un membre
  // « staff » porte un sous-ensemble explicite dans user.permissions.
  const permissions = user?.permissions || []
  const can = (perm) => !!user && (!!user.is_super_admin || permissions.includes(perm))
  const value = {
    user,
    loading,
    isAuthenticated: !!user,
    role,
    isAdmin: role === 'admin',
    isPatron: role === 'patron',
    isStaff: !!user?.is_staff,
    permissions,
    can,
    companyAdminId,
    companyAdminName,
    login,
    register,
    logout,
    updateProfile,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth doit être utilisé dans un <AuthProvider>')
  return ctx
}
