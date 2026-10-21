import { useMutation } from '@tanstack/react-query'
import { Building2, Mail, MessageSquare, Phone } from 'lucide-react'
import { Link, useNavigate } from 'react-router-dom'

import { useAuth } from '../../auth/AuthProvider'
import { Avatar, Button, Modal, uploadUrl, useToast } from '../../components/ui'
import { api } from '../../lib/api'
import { fullName } from './labels'

/** Fiche détaillée d'une personne, avec accès direct à la messagerie. */
export default function PersonModal({ person, onClose }) {
  const navigate = useNavigate()
  const toast = useToast()
  const { user } = useAuth()

  const startChat = useMutation({
    mutationFn: () => api.post('/conversations', { kind: 'direct', user_id: person.id }),
    onSuccess: (conversation) => navigate(`/messagerie/${conversation.id}`),
    onError: () => toast.error("Impossible d'ouvrir la conversation."),
  })

  if (!person) return null
  return (
    <Modal open onClose={onClose} title={fullName(person)}>
      <div className="flex flex-col items-center gap-4 text-center">
        <Avatar
          src={uploadUrl(person.avatar_path)}
          firstName={person.first_name}
          lastName={person.last_name}
          size="xl"
        />
        {person.job_title && (
          <p className="text-slate-600 dark:text-slate-400">{person.job_title}</p>
        )}
        <ul className="w-full space-y-2 text-left text-sm">
          {person.company && (
            <li className="flex items-center gap-2">
              <Building2 size={16} aria-hidden="true" />
              <Link
                to={`/entreprises/${person.company.id}`}
                className="text-brand-700 hover:underline dark:text-brand-300"
              >
                {person.company.name}
              </Link>
            </li>
          )}
          <li className="flex items-center gap-2">
            <Mail size={16} aria-hidden="true" />
            <a href={`mailto:${person.email}`} className="hover:underline">
              {person.email}
            </a>
          </li>
          {person.phone && (
            <li className="flex items-center gap-2">
              <Phone size={16} aria-hidden="true" />
              <a href={`tel:${person.phone}`} className="hover:underline">
                {person.phone}
              </a>
            </li>
          )}
        </ul>
        {person.business_card_path && (
          <img
            src={uploadUrl(person.business_card_path)}
            alt={`Carte de visite de ${fullName(person)}`}
            className="max-h-48 rounded-lg border border-slate-200 dark:border-slate-700"
          />
        )}
        {user.id !== person.id && (
          <Button
            onClick={() => startChat.mutate()}
            loading={startChat.isPending}
            className="w-full"
          >
            <MessageSquare size={16} aria-hidden="true" /> Envoyer un message
          </Button>
        )}
      </div>
    </Modal>
  )
}
