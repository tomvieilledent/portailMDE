/** Modale de réglages d'un groupe de la messagerie. */

import { useMutation, useQueryClient } from '@tanstack/react-query'
import { UserMinus } from 'lucide-react'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { Avatar, Button, Input, Modal, uploadUrl, useToast } from '../../components/ui'
import { api } from '../../lib/api'
import { fullName } from '../directory/labels'
import UserPicker from './UserPicker'

/** Gestion d'un groupe : renommer, ajouter/retirer des membres (créateur), quitter (tous). */
export default function GroupSettingsModal({ conversation, meId, onClose }) {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const toast = useToast()
  const isOwner = conversation.creator_id === meId
  const [title, setTitle] = useState(conversation.title ?? '')
  const [toAdd, setToAdd] = useState([])

  const refresh = () => queryClient.invalidateQueries({ queryKey: ['conversations'] })
  const base = `/conversations/${conversation.id}`

  const rename = useMutation({
    mutationFn: () => api.patch(base, { title: title.trim() }),
    onSuccess: () => {
      toast.success('Groupe renommé.')
      refresh()
    },
    onError: () => toast.error('Renommage impossible.'),
  })
  const add = useMutation({
    mutationFn: () => api.post(`${base}/participants`, { user_ids: toAdd }),
    onSuccess: () => {
      setToAdd([])
      refresh()
    },
    onError: () => toast.error('Ajout impossible.'),
  })
  const removeMember = useMutation({
    mutationFn: (userId) => api.delete(`${base}/participants/${userId}`),
    onSuccess: (_, userId) => {
      refresh()
      if (userId === meId) {
        onClose()
        navigate('/messagerie')
      }
    },
    onError: () => toast.error('Action impossible.'),
  })

  return (
    <Modal open onClose={onClose} title="Paramètres du groupe">
      <div className="space-y-6">
        {isOwner && (
          <form
            onSubmit={(e) => {
              e.preventDefault()
              rename.mutate()
            }}
            className="flex items-end gap-2"
          >
            <div className="flex-1">
              <Input
                label="Nom du groupe"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
              />
            </div>
            <Button type="submit" loading={rename.isPending} disabled={!title.trim()}>
              Renommer
            </Button>
          </form>
        )}

        <section>
          <h3 className="mb-2 text-sm font-semibold">
            Membres ({conversation.participants.length})
          </h3>
          <ul className="space-y-2">
            {conversation.participants.map((person) => (
              <li key={person.id} className="flex items-center gap-3">
                <Avatar
                  src={uploadUrl(person.avatar_path)}
                  firstName={person.first_name}
                  lastName={person.last_name}
                  size="sm"
                />
                <span className="flex-1 truncate text-sm">
                  {fullName({ ...person, email: 'Utilisateur' })}
                  {person.id === meId && ' (vous)'}
                </span>
                {isOwner && person.id !== meId && (
                  <button
                    type="button"
                    aria-label={`Retirer ${person.first_name ?? ''} ${person.last_name ?? ''}`}
                    onClick={() => removeMember.mutate(person.id)}
                    className="rounded p-1 text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800"
                  >
                    <UserMinus size={16} />
                  </button>
                )}
              </li>
            ))}
          </ul>
        </section>

        {isOwner && (
          <section className="space-y-2">
            <UserPicker
              selected={toAdd}
              onChange={setToAdd}
              exclude={conversation.participants.map((p) => p.id)}
            />
            <Button
              disabled={toAdd.length === 0}
              loading={add.isPending}
              onClick={() => add.mutate()}
            >
              Ajouter {toAdd.length > 0 && `(${toAdd.length})`}
            </Button>
          </section>
        )}

        <Button variant="danger" onClick={() => removeMember.mutate(meId)}>
          Quitter le groupe
        </Button>
      </div>
    </Modal>
  )
}
