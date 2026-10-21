import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Clock, Globe, Lock } from 'lucide-react'
import { useState } from 'react'

import { useAuth } from '../../auth/AuthProvider'
import { PERMISSIONS, hasPermission } from '../../auth/permissions'
import { Badge, Button, Modal, useToast } from '../../components/ui'
import { api } from '../../lib/api'
import { formatLongDate, shortTime } from '../../lib/calendar'
import UserPicker from '../messaging/UserPicker'

const statusLabels = { pending: 'En attente', accepted: 'Accepté', declined: 'Refusé' }
const statusTones = { pending: 'neutral', accepted: 'success', declined: 'danger' }

/** Détail d'un événement ; le créateur (ou le staff formations) peut le modifier, inviter, supprimer. */
export default function EventDetailModal({ event, onClose, onEdit }) {
  const { user } = useAuth()
  const toast = useToast()
  const queryClient = useQueryClient()
  const canEdit = event.created_by === user.id || hasPermission(user, PERMISSIONS.MANAGE_TRAININGS)
  const [inviting, setInviting] = useState(false)
  const [toInvite, setToInvite] = useState([])

  const invitations = useQuery({
    queryKey: ['events', event.id, 'invitations'],
    queryFn: () => api.get(`/events/${event.id}/invitations`),
    enabled: canEdit,
  })
  const invite = useMutation({
    mutationFn: () => api.post(`/events/${event.id}/invitations`, { user_ids: toInvite }),
    onSuccess: () => {
      toast.success('Invitations envoyées.')
      setInviting(false)
      setToInvite([])
      queryClient.invalidateQueries({ queryKey: ['events', event.id, 'invitations'] })
    },
    onError: () => toast.error('Invitation impossible.'),
  })
  const remove = useMutation({
    mutationFn: () => api.delete(`/events/${event.id}`),
    onSuccess: () => {
      toast.success('Événement supprimé.')
      queryClient.invalidateQueries({ queryKey: ['events'] })
      onClose()
    },
    onError: () => toast.error('Suppression impossible.'),
  })

  const counts = (invitations.data ?? []).reduce(
    (acc, i) => ({ ...acc, [i.status]: (acc[i.status] ?? 0) + 1 }),
    {},
  )

  return (
    <Modal
      open
      onClose={onClose}
      title={event.title}
      footer={
        canEdit && (
          <>
            <Button variant="danger" loading={remove.isPending} onClick={() => remove.mutate()}>
              Supprimer
            </Button>
            <Button variant="secondary" onClick={() => onEdit(event)}>
              Modifier
            </Button>
          </>
        )
      }
    >
      <div className="space-y-4">
        <p className="flex items-center gap-2 text-sm">
          <Clock size={16} aria-hidden="true" />
          <span className="capitalize">{formatLongDate(event.event_date)}</span>
          {shortTime(event.event_time) && <span>à {shortTime(event.event_time)}</span>}
        </p>
        <p className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-400">
          {event.is_public ? <Globe size={16} /> : <Lock size={16} />}
          {event.is_public ? 'Ouvert à tous les membres' : 'Sur invitation'}
        </p>
        {event.description && <p className="text-sm whitespace-pre-wrap">{event.description}</p>}

        {canEdit && (
          <section>
            <div className="mb-2 flex items-center justify-between">
              <h3 className="text-sm font-semibold">Invités ({invitations.data?.length ?? 0})</h3>
              <Button size="sm" variant="secondary" onClick={() => setInviting((v) => !v)}>
                Inviter
              </Button>
            </div>
            <div className="flex flex-wrap gap-2">
              {Object.entries(counts).map(([status, count]) => (
                <Badge key={status} tone={statusTones[status]}>
                  {statusLabels[status]} : {count}
                </Badge>
              ))}
            </div>
            {inviting && (
              <div className="mt-3 space-y-2">
                <UserPicker selected={toInvite} onChange={setToInvite} exclude={[user.id]} />
                <Button
                  disabled={toInvite.length === 0}
                  loading={invite.isPending}
                  onClick={() => invite.mutate()}
                >
                  Envoyer les invitations
                </Button>
              </div>
            )}
          </section>
        )}
      </div>
    </Modal>
  )
}
