import { useQueryClient } from '@tanstack/react-query'
import { useRef } from 'react'

import { useAuth } from '../auth/AuthProvider'
import { useRealtime } from './useRealtime'

/** Réactions globales aux événements temps réel : rafraîchit les listes et joue un son. */
export default function RealtimeEffects() {
  const queryClient = useQueryClient()
  const { user } = useAuth()
  const sound = useRef(null)

  useRealtime('message.new', (event) => {
    queryClient.invalidateQueries({ queryKey: ['conversations'] })
    if (event.message.author_id === user.id) return
    try {
      sound.current ??= new Audio('/notification.mp3')
      sound.current.play()?.catch(() => {})
    } catch {
      /* lecture audio indisponible */
    }
  })
  useRealtime('conversation.created', () =>
    queryClient.invalidateQueries({ queryKey: ['conversations'] }),
  )
  useRealtime('conversation.updated', () =>
    queryClient.invalidateQueries({ queryKey: ['conversations'] }),
  )
  useRealtime('message.deleted', () =>
    queryClient.invalidateQueries({ queryKey: ['conversations'] }),
  )
  return null
}
