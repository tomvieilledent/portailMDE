/** Modale de création ou de modification d'un événement. */

import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'

import { Button, Input, Modal, Textarea, useToast } from '../../components/ui'
import { api } from '../../lib/api'
import { shortTime } from '../../lib/calendar'
import UserPicker from '../messaging/UserPicker'
import { useAuth } from '../../auth/AuthProvider'

/** Création ou modification d'un événement (invitations à la création). */
export default function EventFormModal({ event, defaultDate, onClose }) {
  const { user } = useAuth()
  const toast = useToast()
  const queryClient = useQueryClient()
  const [values, setValues] = useState({
    title: event?.title ?? '',
    description: event?.description ?? '',
    event_date: event?.event_date ?? defaultDate,
    event_time: shortTime(event?.event_time) ?? '',
    is_public: event?.is_public ?? false,
  })
  const [invitees, setInvitees] = useState([])

  const save = useMutation({
    mutationFn: () => {
      const body = {
        title: values.title.trim(),
        description: values.description.trim() || null,
        event_date: values.event_date,
        event_time: values.event_time || null,
        is_public: values.is_public,
      }
      return event
        ? api.patch(`/events/${event.id}`, body)
        : api.post('/events', { ...body, invitee_ids: invitees })
    },
    onSuccess: () => {
      toast.success(event ? 'Événement modifié.' : 'Événement créé.')
      queryClient.invalidateQueries({ queryKey: ['events'] })
      onClose()
    },
    onError: () => toast.error('Enregistrement impossible.'),
  })

  const bind = (name) => ({
    value: values[name],
    onChange: (e) => setValues((v) => ({ ...v, [name]: e.target.value })),
  })

  return (
    <Modal open onClose={onClose} title={event ? "Modifier l'événement" : 'Nouvel événement'}>
      <form
        onSubmit={(e) => {
          e.preventDefault()
          save.mutate()
        }}
        className="grid gap-4"
      >
        <Input label="Titre" required maxLength={200} {...bind('title')} />
        <div className="grid gap-4 sm:grid-cols-2">
          <Input label="Date" type="date" required {...bind('event_date')} />
          <Input label="Heure" type="time" {...bind('event_time')} />
        </div>
        <Textarea label="Description" rows={3} {...bind('description')} />
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={values.is_public}
            onChange={(e) => setValues((v) => ({ ...v, is_public: e.target.checked }))}
          />
          Visible par tous les membres (sinon : invités uniquement)
        </label>
        {!event && <UserPicker selected={invitees} onChange={setInvitees} exclude={[user.id]} />}
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
