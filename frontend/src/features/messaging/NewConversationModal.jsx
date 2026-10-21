/** Modale de création d'une conversation. */

import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { useAuth } from '../../auth/AuthProvider'
import { Button, Input, Modal, useToast } from '../../components/ui'
import { api } from '../../lib/api'
import UserPicker from './UserPicker'

/** Nouvelle conversation : directe (1 personne) ou groupe nommé (plusieurs). */
export default function NewConversationModal({ onClose }) {
  const { user } = useAuth()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const toast = useToast()
  const [group, setGroup] = useState(false)
  const [title, setTitle] = useState('')
  const [selected, setSelected] = useState([])

  const create = useMutation({
    mutationFn: () =>
      group
        ? api.post('/conversations', { kind: 'group', title: title.trim(), user_ids: selected })
        : api.post('/conversations', { kind: 'direct', user_id: selected[0] }),
    onSuccess: (conversation) => {
      queryClient.invalidateQueries({ queryKey: ['conversations'] })
      onClose()
      navigate(`/messagerie/${conversation.id}`)
    },
    onError: () => toast.error('Création impossible.'),
  })

  const ready = group ? title.trim() && selected.length > 0 : selected.length === 1

  return (
    <Modal
      open
      onClose={onClose}
      title="Nouvelle conversation"
      footer={
        <>
          <Button variant="secondary" onClick={onClose}>
            Annuler
          </Button>
          <Button disabled={!ready} loading={create.isPending} onClick={() => create.mutate()}>
            Créer
          </Button>
        </>
      }
    >
      <div className="space-y-4">
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={group}
            onChange={(e) => {
              setGroup(e.target.checked)
              setSelected([])
            }}
          />
          Groupe de discussion
        </label>
        {group && (
          <Input
            label="Nom du groupe"
            value={title}
            maxLength={200}
            onChange={(e) => setTitle(e.target.value)}
          />
        )}
        <UserPicker
          selected={selected}
          onChange={setSelected}
          exclude={[user.id]}
          single={!group}
        />
      </div>
    </Modal>
  )
}
