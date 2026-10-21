/** Demande d'une formation non programmée : « Cette formation m'intéresse ». */

import { useMutation, useQueryClient } from '@tanstack/react-query'

import { Button, useToast } from '../../components/ui'
import { api } from '../../lib/api'

/** Bascule « Cette formation m'intéresse » ; l'équipe voit les demandes et planifie la session. */
export default function InterestButton({ trainingId, active, size = 'md' }) {
  const queryClient = useQueryClient()
  const toast = useToast()
  const toggle = useMutation({
    mutationFn: () =>
      active
        ? api.delete(`/trainings/${trainingId}/interest`)
        : api.put(`/trainings/${trainingId}/interest`),
    onSuccess: () => {
      toast.success(
        active
          ? 'Demande retirée.'
          : 'Demande enregistrée : vous serez prévenu(e) dès que la formation sera programmée.',
      )
      queryClient.invalidateQueries({ queryKey: ['trainings'] })
    },
    onError: () => toast.error('Action impossible.'),
  })
  return (
    <Button
      size={size}
      variant={active ? 'secondary' : 'primary'}
      aria-pressed={active}
      loading={toggle.isPending}
      onClick={(event) => {
        event.preventDefault()
        toggle.mutate()
      }}
    >
      {active ? '✓ Demande enregistrée (retirer)' : "Cette formation m'intéresse"}
    </Button>
  )
}
