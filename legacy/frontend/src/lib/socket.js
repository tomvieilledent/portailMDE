// Singleton Socket.IO : une seule connexion partagée par l'app.
// L'auth se fait via le token JWT passé dans `auth` à la connexion
// (le backend le vérifie dans handle_connect).

import { io } from 'socket.io-client'
import { getToken } from './api'

// En dev, on se connecte à l'origine courante (Vite relaie /socket.io vers
// le backend). VITE_SOCKET_URL permet de forcer une URL absolue si besoin.
const BASE = import.meta.env.VITE_SOCKET_URL || undefined

let socket = null

// Ouvre (ou réutilise) la connexion. À appeler une fois l'utilisateur connecté.
export function connectSocket() {
  const token = getToken()
  if (!token) return null
  if (socket && socket.connected) return socket
  if (!socket) {
    socket = io(BASE, {
      auth: { token },
      autoConnect: false,
      transports: ['websocket', 'polling'],
    })
  } else {
    socket.auth = { token }
  }
  if (!socket.connected) socket.connect()
  return socket
}

export function getSocket() {
  return socket
}

export function disconnectSocket() {
  if (socket) {
    socket.disconnect()
    socket = null
  }
}
