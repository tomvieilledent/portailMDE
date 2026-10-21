/** Modale de création ou de modification d'une formation. */

import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useEffect, useMemo, useState } from 'react'

import { Button, ImageUpload, Input, Modal, Select, Textarea, useToast } from '../../components/ui'
import { api } from '../../lib/api'
import { uploadUrl } from '../../lib/uploads'
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
    link: training?.link ?? '',
  })
  const [picture, setPicture] = useState(null) // plaquette choisie, téléversée à l'enregistrement
  const preview = useMemo(() => (picture ? URL.createObjectURL(picture) : null), [picture])
  useEffect(() => () => preview && URL.revokeObjectURL(preview), [preview])
  const save = useMutation({
    mutationFn: async () => {
      const body = {
        title: values.title.trim(),
        description: values.description.trim() || null,
        category: values.category.trim() || null,
        kind: values.kind,
        link: values.link.trim() || null,
      }
      const saved = await (training
        ? api.patch(`/trainings/${training.id}`, body)
        : api.post('/trainings', body))
      if (picture) {
        const form = new FormData()
        form.append('file', picture)
        await api.put(`/trainings/${saved.id}/picture`, form)
      }
      return saved
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
        <Textarea label="Description détaillée" rows={8} {...bind('description')} />
        <Input
          label="Lien (page de la formation, inscription…)"
          type="url"
          placeholder="https://"
          maxLength={512}
          {...bind('link')}
        />
        <ImageUpload
          label="Image ou plaquette de la formation"
          preview={
            preview || training?.picture_path ? (
              <img
                src={preview ?? uploadUrl(training.picture_path)}
                alt=""
                className="h-16 w-24 rounded-md border border-slate-200 object-cover"
              />
            ) : null
          }
          onSelect={setPicture}
        />
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
