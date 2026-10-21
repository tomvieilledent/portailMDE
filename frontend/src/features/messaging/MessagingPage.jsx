import { MessageSquare } from 'lucide-react'
import { useState } from 'react'
import { useParams } from 'react-router-dom'

import { useAuth } from '../../auth/AuthProvider'
import { EmptyState } from '../../components/ui'
import { cn } from '../../lib/cn'
import ConversationList from './ConversationList'
import MessageThread from './MessageThread'
import NewConversationModal from './NewConversationModal'
import { useConversations } from './queries'

/** Messagerie : liste des conversations à gauche, fil de discussion à droite (plein écran sur mobile). */
export default function MessagingPage() {
  const { conversationId } = useParams()
  const { user } = useAuth()
  const { data: conversations, isLoading, isError } = useConversations()
  const [creating, setCreating] = useState(false)
  const current = conversations?.find((c) => c.id === conversationId)

  return (
    <div className="-m-4 grid h-[calc(100vh-3.5rem)] overflow-hidden bg-white sm:-m-6 lg:grid-cols-[22rem_1fr] dark:bg-slate-900">
      <section
        aria-label="Conversations"
        className={cn(
          'border-r border-slate-200 dark:border-slate-800',
          conversationId && 'hidden lg:block',
        )}
      >
        <ConversationList
          conversations={conversations}
          loading={isLoading}
          meId={user.id}
          onNew={() => setCreating(true)}
        />
        {isError && (
          <p role="alert" className="p-4 text-sm">
            Impossible de charger les conversations.
          </p>
        )}
      </section>

      <section
        aria-label="Discussion"
        className={cn('min-h-0', !conversationId && 'hidden lg:block')}
      >
        {current ? (
          <MessageThread key={current.id} conversation={current} meId={user.id} />
        ) : (
          <div className="flex h-full items-center justify-center p-6">
            <EmptyState
              icon={MessageSquare}
              title={
                conversationId && !isLoading
                  ? 'Conversation introuvable'
                  : 'Sélectionnez une conversation'
              }
            />
          </div>
        )}
      </section>
      {creating && <NewConversationModal onClose={() => setCreating(false)} />}
    </div>
  )
}
