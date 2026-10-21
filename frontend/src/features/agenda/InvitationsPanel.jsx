/** Panneau des invitations reçues. */

import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Check, X } from 'lucide-react'

import { Badge, Button, Card, useToast } from '../../components/ui'
import { api } from '../../lib/api'
import { useMyInvitations } from './queries'

/** Invitations reçues (événements et sessions) : accepter ou refuser. */
export default function InvitationsPanel() {
  const { data } = useMyInvitations()
  const toast = useToast()
  const queryClient = useQueryClient()
  const respond = useMutation({
    mutationFn: ({ id, status }) => api.post(`/invitations/${id}/respond`, { status }),
    onSuccess: () => {
      toast.success('Réponse enregistrée.')
      queryClient.invalidateQueries({ queryKey: ['invitations'] })
    },
    onError: () => toast.error('Réponse impossible.'),
  })

  const pending = (data ?? []).filter((i) => i.status === 'pending')
  if (pending.length === 0) return null

  return (
    <Card className="mb-6">
      <h2 className="mb-3 flex items-center gap-2 text-lg font-semibold">
        Invitations <Badge tone="brand">{pending.length}</Badge>
      </h2>
      <ul className="divide-y divide-slate-100 dark:divide-slate-800">
        {pending.map((invitation) => (
          <li key={invitation.id} className="flex items-center gap-3 py-2">
            <span className="flex-1 truncate text-sm">
              {invitation.target_title ?? 'Invitation'}
              <span className="text-slate-500">
                {invitation.session_id ? ' (session de formation)' : ' (événement)'}
              </span>
            </span>
            <Button
              size="sm"
              aria-label={`Accepter ${invitation.target_title}`}
              onClick={() => respond.mutate({ id: invitation.id, status: 'accepted' })}
            >
              <Check size={14} aria-hidden="true" /> Accepter
            </Button>
            <Button
              size="sm"
              variant="secondary"
              aria-label={`Refuser ${invitation.target_title}`}
              onClick={() => respond.mutate({ id: invitation.id, status: 'declined' })}
            >
              <X size={14} aria-hidden="true" /> Refuser
            </Button>
          </li>
        ))}
      </ul>
    </Card>
  )
}
