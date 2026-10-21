/** Page de la messagerie. */

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
    <div className="grid h-full min-h-0 gap-4 lg:grid-cols-[21rem_1fr]">
      <section
        aria-label="Conversations"
        className={cn(
          'min-h-0 overflow-hidden rounded-md border border-slate-200 bg-white',
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
        className={cn(
          'min-h-0 overflow-hidden rounded-md border border-slate-200 bg-white',
          !conversationId && 'hidden lg:block',
        )}
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
