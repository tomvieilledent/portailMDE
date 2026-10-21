/** Page cible d'une notification selon son type. */
export function notificationTarget(notification) {
  const data = notification.data ?? {}
  if (data.conversation_id) return `/messagerie/${data.conversation_id}`
  if (notification.kind?.startsWith('invitation')) return '/agenda'
  return null
}
