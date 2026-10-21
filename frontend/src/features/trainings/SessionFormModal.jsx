/** Modale de programmation d'une session. */

import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'

import { Button, Input, Modal, useToast } from '../../components/ui'
import { api } from '../../lib/api'

/** `datetime-local` (heure locale) → ISO UTC attendu par l'API. */
const toIso = (local) => new Date(local).toISOString()

/** Programmation d'une session (date, capacité, lieu ou lien visio, visibilité). */
export default function SessionFormModal({ trainingId, onClose }) {
  const toast = useToast()
  const queryClient = useQueryClient()
  const [values, setValues] = useState({
    start_at: '',
    end_at: '',
    max_participants: 10,
    location: '',
    link: '',
    is_public: true,
  })
  const save = useMutation({
    mutationFn: () =>
      api.post(`/trainings/${trainingId}/sessions`, {
        start_at: toIso(values.start_at),
        end_at: toIso(values.end_at),
        max_participants: Number(values.max_participants),
        location: values.location.trim() || null,
        link: values.link.trim() || null,
        is_public: values.is_public,
      }),
    onSuccess: () => {
      toast.success('Session créée.')
      queryClient.invalidateQueries({ queryKey: ['trainings', trainingId, 'sessions'] })
      onClose()
    },
    onError: () => toast.error('Création impossible.'),
  })
  const bind = (name) => ({
    value: values[name],
    onChange: (e) => setValues((v) => ({ ...v, [name]: e.target.value })),
  })
  const invalidDates = values.start_at && values.end_at && values.end_at < values.start_at

  return (
    <Modal open onClose={onClose} title="Nouvelle session">
      <form
        onSubmit={(e) => {
          e.preventDefault()
          save.mutate()
        }}
        className="grid gap-4"
      >
        <div className="grid gap-4 sm:grid-cols-2">
          <Input label="Début" type="datetime-local" required {...bind('start_at')} />
          <Input
            label="Fin"
            type="datetime-local"
            required
            error={invalidDates ? 'La fin doit suivre le début.' : undefined}
            {...bind('end_at')}
          />
        </div>
        <Input label="Places" type="number" min={1} required {...bind('max_participants')} />
        <Input label="Lieu" {...bind('location')} />
        <Input label="Lien visio" type="url" placeholder="https://" {...bind('link')} />
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={values.is_public}
            onChange={(e) => setValues((v) => ({ ...v, is_public: e.target.checked }))}
          />
          Ouverte à tous (sinon : sur invitation)
        </label>
        <div className="flex justify-end gap-2">
          <Button variant="secondary" onClick={onClose}>
            Annuler
          </Button>
          <Button type="submit" loading={save.isPending} disabled={Boolean(invalidDates)}>
            Créer
          </Button>
        </div>
      </form>
    </Modal>
  )
}
