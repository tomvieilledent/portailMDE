import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'

import { Button, Input, Modal, Select, Textarea, useToast } from '../../components/ui'
import { api } from '../../lib/api'
import { TRAINING_KINDS } from './queries'

/** Création / modification d'une formation (réservé à `manage_trainings`). */
export default function TrainingFormModal({ training, onClose }) {
  const toast = useToast()
  const queryClient = useQueryClient()
  const [values, setValues] = useState({
    title: training?.title ?? '',
    description: training?.description ?? '',
    category: training?.category ?? '',
    kind: training?.kind ?? 'formation',
  })
  const save = useMutation({
    mutationFn: () => {
      const body = {
        title: values.title.trim(),
        description: values.description.trim() || null,
        category: values.category.trim() || null,
        kind: values.kind,
      }
      return training ? api.patch(`/trainings/${training.id}`, body) : api.post('/trainings', body)
    },
    onSuccess: () => {
      toast.success(training ? 'Formation modifiée.' : 'Formation créée.')
      queryClient.invalidateQueries({ queryKey: ['trainings'] })
      onClose()
    },
    onError: () => toast.error('Enregistrement impossible.'),
  })
  const bind = (name) => ({
    value: values[name],
    onChange: (e) => setValues((v) => ({ ...v, [name]: e.target.value })),
  })

  return (
    <Modal open onClose={onClose} title={training ? 'Modifier la formation' : 'Nouvelle formation'}>
      <form
        onSubmit={(e) => {
          e.preventDefault()
          save.mutate()
        }}
        className="grid gap-4"
      >
        <Input label="Titre" required maxLength={200} {...bind('title')} />
        <div className="grid gap-4 sm:grid-cols-2">
          <Select label="Type" {...bind('kind')}>
            {Object.entries(TRAINING_KINDS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </Select>
          <Input label="Catégorie" maxLength={100} {...bind('category')} />
        </div>
        <Textarea label="Description" {...bind('description')} />
        <div className="flex justify-end gap-2">
          <Button variant="secondary" onClick={onClose}>
            Annuler
          </Button>
          <Button type="submit" loading={save.isPending}>
            Enregistrer
          </Button>
        </div>
      </form>
    </Modal>
  )
}
