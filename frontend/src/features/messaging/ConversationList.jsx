/** Liste des conversations de la messagerie. */

import { Plus, Users } from 'lucide-react'
import { NavLink } from 'react-router-dom'

import { Avatar, Badge, Button, Spinner, uploadUrl } from '../../components/ui'
import { cn } from '../../lib/cn'
import { conversationTitle, formatTime, previewText } from './helpers'

/** Liste des conversations avec messages non lus ; `onNew` ouvre une nouvelle conversation. */
export default function ConversationList({ conversations, loading, meId, onNew }) {
  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between border-b border-slate-200 px-4 py-3">
        <h1 className="text-xl font-semibold">Messagerie</h1>
        <Button size="sm" onClick={onNew}>
          <Plus size={16} aria-hidden="true" /> Nouveau
        </Button>
      </div>
      {loading && (
        <div className="p-4">
          <Spinner />
        </div>
      )}
      {conversations?.length === 0 && (
        <p className="p-4 text-sm text-slate-500">Aucune conversation pour le moment.</p>
      )}
      <ul className="flex-1 overflow-y-auto">
        {conversations?.map((conversation) => {
          const other = conversation.participants.find((p) => p.id !== meId)
          return (
            <li key={conversation.id}>
              <NavLink
                to={`/messagerie/${conversation.id}`}
                className={({ isActive }) =>
                  cn(
                    'relative flex items-center gap-3 border-b border-slate-100 px-4 py-3 hover:bg-slate-50',
                    isActive &&
                      'bg-brand-50 before:absolute before:inset-y-0 before:left-0 before:w-[3px] before:bg-[#7ec843]',
                  )
                }
              >
                {conversation.kind === 'group' ? (
                  <span className="bg-brand-100 text-brand-700 dark:bg-brand-900 dark:text-brand-200 inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-full">
                    <Users size={18} aria-hidden="true" />
                  </span>
                ) : (
                  <Avatar
                    src={uploadUrl(other?.avatar_path)}
                    firstName={other?.first_name}
                    lastName={other?.last_name}
                  />
                )}
                <div className="min-w-0 flex-1">
                  <div className="flex items-baseline justify-between gap-2">
                    <p
                      className={cn(
                        'truncate',
                        conversation.unread_count > 0 ? 'font-bold' : 'font-medium',
                      )}
                    >
                      {conversationTitle(conversation, meId)}
                    </p>
                    {conversation.last_message && (
                      <time className="shrink-0 text-xs text-slate-500">
                        {formatTime(conversation.last_message.created_at)}
                      </time>
                    )}
                  </div>
                  <p
                    className={cn(
                      'truncate text-sm',
                      conversation.unread_count > 0
                        ? 'font-medium text-slate-800'
                        : 'text-slate-500',
                    )}
                  >
                    {previewText(conversation.last_message)}
                  </p>
                </div>
                {conversation.unread_count > 0 && (
                  <Badge tone="brand" className="shrink-0">
                    <span className="sr-only">Non lus : </span>
                    {conversation.unread_count}
                  </Badge>
                )}
              </NavLink>
            </li>
          )
        })}
      </ul>
    </div>
  )
}
