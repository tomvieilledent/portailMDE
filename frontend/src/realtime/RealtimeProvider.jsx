/** Fournisseur de la connexion temps réel (WebSocket). */

import { useEffect, useMemo, useRef } from 'react'

import { useAuth } from '../auth/AuthProvider'
import { api } from '../lib/api'
import { tokens } from '../lib/tokens'
import { RealtimeContext } from './context'

const PING_MS = 25_000

/**
 * Connexion WebSocket unique vers `/api/v1/ws` tant que l'utilisateur est connecté.
 * Reconnexion automatique (délai croissant) ; les composants s'abonnent par type d'événement.
 */
export function RealtimeProvider({ children }) {
  const { user } = useAuth()
  const listeners = useRef(new Map())

  const value = useMemo(
    () => ({
      subscribe(type, handler) {
        const set = listeners.current.get(type) ?? new Set()
        set.add(handler)
        listeners.current.set(type, set)
        return () => set.delete(handler)
      },
    }),
    [],
  )

  const userId = user?.id
  useEffect(() => {
    if (!userId) return undefined
    let socket
    let pingTimer
    let retryTimer
    let attempt = 0
    let closed = false

    async function connect() {
      // Un appel authentifié renouvelle au besoin le jeton avant d'ouvrir le socket.
      await api.get('/users/me').catch(() => {})
      if (closed || !tokens.access) return
      const scheme = window.location.protocol === 'https:' ? 'wss' : 'ws'
      socket = new WebSocket(
        `${scheme}://${window.location.host}/api/v1/ws?token=${encodeURIComponent(tokens.access)}`,
      )
      socket.onopen = () => {
        attempt = 0
        pingTimer = setInterval(() => socket.send('ping'), PING_MS)
      }
      socket.onmessage = (event) => {
        let data
        try {
          data = JSON.parse(event.data)
        } catch {
          return
        }
        listeners.current.get(data.type)?.forEach((handler) => handler(data))
      }
      socket.onclose = () => {
        clearInterval(pingTimer)
        if (closed) return
        attempt += 1
        retryTimer = setTimeout(connect, Math.min(30_000, 1000 * 2 ** attempt))
      }
    }

    connect()
    return () => {
      closed = true
      clearInterval(pingTimer)
      clearTimeout(retryTimer)
      socket?.close()
    }
  }, [userId])

  return <RealtimeContext.Provider value={value}>{children}</RealtimeContext.Provider>
}
