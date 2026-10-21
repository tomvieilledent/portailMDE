/** Modale d'administration d'une session. */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Check } from 'lucide-react'
import { useState } from 'react'

import { Badge, Button, Modal, Spinner, useToast } from '../../components/ui'
import { api } from '../../lib/api'
import UserPicker from '../messaging/UserPicker'

/** Gestion d'une session par le staff : inscrits, validation de présence, invitations. */
export default function SessionAdminModal({ session, trainingId, onClose }) {
  const toast = useToast()
  const queryClient = useQueryClient()
  const [toInvite, setToInvite] = useState([])
  const base = `/training-sessions/${session.id}`

  const enrollments = useQuery({
    queryKey: ['sessions', session.id, 'enrollments'],
    queryFn: () => api.get(`${base}/enrollments`),
  })
  const complete = useMutation({
    mutationFn: (userId) => api.post(`${base}/enrollments/${userId}/complete`),
    onSuccess: () => {
      toast.success('Présence validée.')
      queryClient.invalidateQueries({ queryKey: ['sessions', session.id, 'enrollments'] })
    },
    onError: () => toast.error('Validation impossible.'),
  })
  const invite = useMutation({
    mutationFn: () => api.post(`${base}/invitations`, { user_ids: toInvite }),
    onSuccess: () => {
      toast.success('Invitations envoyées.')
      setToInvite([])
    },
    onError: () => toast.error('Invitation impossible.'),
  })
  const remove = useMutation({
    mutationFn: () => api.delete(base),
    onSuccess: () => {
      toast.success('Session supprimée.')
      queryClient.invalidateQueries({ queryKey: ['trainings', trainingId, 'sessions'] })
      onClose()
    },
    onError: () => toast.error('Suppression impossible.'),
  })

  return (
    <Modal open onClose={onClose} title="Gérer la session">
      <div className="space-y-6">
        <section>
          <h3 className="mb-2 text-sm font-semibold">Inscrits</h3>
          {enrollments.isLoading && <Spinner className="h-5 w-5" />}
          {enrollments.data?.length === 0 && (
            <p className="text-sm text-slate-500">Aucun inscrit.</p>
          )}
          <ul className="divide-y divide-slate-100 dark:divide-slate-800">
            {enrollments.data?.map((enrollment) => (
              <li key={enrollment.id} className="flex items-center gap-3 py-2 text-sm">
                <span className="flex-1">
                  {enrollment.user
                    ? [enrollment.user.first_name, enrollment.user.last_name]
                        .filter(Boolean)
                        .join(' ') || 'Participant'
                    : 'Participant'}
                </span>
                {enrollment.completed_at ? (
                  <Badge tone="success">Présent</Badge>
                ) : (
                  <Button
                    size="sm"
                    variant="secondary"
                    onClick={() => complete.mutate(enrollment.user_id)}
                  >
                    <Check size={14} aria-hidden="true" /> Valider la présence
                  </Button>
                )}
              </li>
            ))}
          </ul>
        </section>

        {!session.is_public && (
          <section className="space-y-2">
            <h3 className="text-sm font-semibold">Inviter</h3>
            <UserPicker selected={toInvite} onChange={setToInvite} />
            <Button
              disabled={toInvite.length === 0}
              loading={invite.isPending}
              onClick={() => invite.mutate()}
            >
              Envoyer les invitations
            </Button>
          </section>
        )}

        <Button variant="danger" loading={remove.isPending} onClick={() => remove.mutate()}>
          Supprimer la session
        </Button>
      </div>
    </Modal>
  )
}
