/** Bouton d'intérêt pour une formation. */

import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Star } from 'lucide-react'

import { cn } from '../../lib/cn'
import { api } from '../../lib/api'
import { useToast } from '../../components/ui'

/** Étoile « Cette formation m'intéresse » (favori). */
export default function InterestButton({ trainingId, active }) {
  const queryClient = useQueryClient()
  const toast = useToast()
  const toggle = useMutation({
    mutationFn: () =>
      active
        ? api.delete(`/trainings/${trainingId}/interest`)
        : api.put(`/trainings/${trainingId}/interest`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['trainings', 'mine'] }),
    onError: () => toast.error('Action impossible.'),
  })
  return (
    <button
      type="button"
      aria-pressed={active}
      aria-label={active ? 'Retirer des favoris' : 'Ajouter aux favoris'}
      onClick={(event) => {
        event.preventDefault()
        toggle.mutate()
      }}
      className="rounded-full p-1.5 hover:bg-slate-100 dark:hover:bg-slate-800"
    >
      <Star
        size={18}
        className={cn(active ? 'fill-amber-400 text-amber-400' : 'text-slate-500')}
        aria-hidden="true"
      />
    </button>
  )
}
