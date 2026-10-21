import { fullName } from '../directory/labels'

/** Nom affiché d'une conversation : titre du groupe, ou nom de l'interlocuteur. */
export function conversationTitle(conversation, meId) {
  if (conversation.kind === 'group') return conversation.title ?? 'Groupe'
  const other = conversation.participants.find((p) => p.id !== meId)
  return other ? fullName({ ...other, email: 'Utilisateur' }) : 'Conversation'
}

/** Résumé du dernier message pour la liste. */
export function previewText(message) {
  if (!message) return 'Aucun message'
  if (message.content) return message.content
  return message.file_name ? `📎 ${message.file_name}` : ''
}

export function formatTime(iso) {
  const date = new Date(iso)
  const sameDay = date.toDateString() === new Date().toDateString()
  return sameDay
    ? date.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
    : date.toLocaleDateString('fr-FR', { day: '2-digit', month: 'short' })
}
