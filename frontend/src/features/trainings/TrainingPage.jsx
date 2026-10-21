import { useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, CalendarClock, FileText, Link2, MapPin, Plus, Users } from 'lucide-react'
import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { useAuth } from '../../auth/AuthProvider'
import { PERMISSIONS, hasPermission } from '../../auth/permissions'
import PageHeader from '../../components/layout/PageHeader'
import { Badge, Button, Card, EmptyState, Spinner, useToast } from '../../components/ui'
import { api } from '../../lib/api'
import { uploadUrl } from '../../lib/uploads'
import InterestButton from './InterestButton'
import SessionAdminModal from './SessionAdminModal'
import SessionFormModal from './SessionFormModal'
import TrainingFormModal from './TrainingFormModal'
import {
  TRAINING_KINDS,
  formatDateTime,
  useMyEnrollments,
  useTraining,
  useTrainingSessions,
} from './queries'

function SessionRow({ session, trainingId, canManage, onManage }) {
  const toast = useToast()
  const queryClient = useQueryClient()
  const full = session.enrolled_count >= session.max_participants
  const closed = ['done', 'cancelled'].includes(session.status)

  const toggle = useMutation({
    mutationFn: () =>
      session.is_enrolled
        ? api.delete(`/training-sessions/${session.id}/enroll`)
        : api.post(`/training-sessions/${session.id}/enroll`),
    onSuccess: () => {
      toast.success(session.is_enrolled ? 'Inscription annulée.' : 'Inscription confirmée.')
      queryClient.invalidateQueries({ queryKey: ['trainings', trainingId, 'sessions'] })
      queryClient.invalidateQueries({ queryKey: ['trainings', 'mine'] })
    },
    onError: (err) => toast.error(err.message || 'Action impossible.'),
  })

  return (
    <li className="flex flex-wrap items-center gap-3 py-3">
      <div className="min-w-0 flex-1 space-y-1">
        <p className="flex items-center gap-2 font-medium">
          <CalendarClock size={16} aria-hidden="true" />
          {formatDateTime(session.start_at)} → {formatDateTime(session.end_at)}
        </p>
        <p className="flex flex-wrap items-center gap-x-4 text-sm text-slate-600 dark:text-slate-400">
          {session.location && (
            <span className="inline-flex items-center gap-1">
              <MapPin size={14} aria-hidden="true" /> {session.location}
            </span>
          )}
          {session.link && (
            <a
              href={session.link}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-brand-700 hover:underline dark:text-brand-300"
            >
              <Link2 size={14} aria-hidden="true" /> Visio
            </a>
          )}
          <span className="inline-flex items-center gap-1">
            <Users size={14} aria-hidden="true" /> {session.enrolled_count}/
            {session.max_participants}
          </span>
        </p>
      </div>
      {!session.is_public && <Badge>Sur invitation</Badge>}
      {session.status === 'cancelled' && <Badge tone="danger">Annulée</Badge>}
      {session.status === 'done' && <Badge>Terminée</Badge>}
      <Button
        size="sm"
        variant={session.is_enrolled ? 'secondary' : 'primary'}
        disabled={closed || (full && !session.is_enrolled)}
        loading={toggle.isPending}
        onClick={() => toggle.mutate()}
      >
        {session.is_enrolled ? 'Se désinscrire' : full ? 'Complet' : "S'inscrire"}
      </Button>
      {canManage && (
        <Button size="sm" variant="ghost" onClick={() => onManage(session)}>
          Gérer
        </Button>
      )}
    </li>
  )
}

/** Fiche d'une formation : description, documents, sessions et inscription. */
export default function TrainingPage() {
  const { trainingId } = useParams()
  const navigate = useNavigate()
  const { user } = useAuth()
  const toast = useToast()
  const queryClient = useQueryClient()
  const canManage = hasPermission(user, PERMISSIONS.MANAGE_TRAININGS)
  const training = useTraining(trainingId)
  const sessions = useTrainingSessions(trainingId)
  const mine = useMyEnrollments()
  const [editing, setEditing] = useState(false)
  const [addingSession, setAddingSession] = useState(false)
  const [managed, setManaged] = useState(null)

  const setActive = useMutation({
    mutationFn: (active) =>
      api.post(`/trainings/${trainingId}/${active ? 'reactivate' : 'deactivate'}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['trainings'] }),
    onError: () => toast.error('Action impossible.'),
  })
  const remove = useMutation({
    mutationFn: () => api.delete(`/trainings/${trainingId}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['trainings'] })
      navigate('/formations')
    },
    onError: () => toast.error('Suppression impossible.'),
  })

  if (training.isLoading) return <Spinner />
  if (training.isError) {
    return (
      <EmptyState
        title="Formation introuvable"
        action={<Link to="/formations">Retour au catalogue</Link>}
      />
    )
  }
  const t = training.data
  const interested = (mine.data ?? []).some((e) => e.training_id === t.id && e.interested)

  return (
    <>
      <Link
        to="/formations"
        className="mb-4 inline-flex items-center gap-1 text-sm text-brand-700 hover:underline dark:text-brand-300"
      >
        <ArrowLeft size={14} aria-hidden="true" /> Catalogue
      </Link>
      <PageHeader
        title={t.title}
        actions={
          <div className="flex items-center gap-2">
            <InterestButton trainingId={t.id} active={interested} />
            {canManage && (
              <>
                <Button variant="secondary" onClick={() => setEditing(true)}>
                  Modifier
                </Button>
                <Button variant="ghost" onClick={() => setActive.mutate(!t.is_active)}>
                  {t.is_active ? 'Désactiver' : 'Réactiver'}
                </Button>
                <Button variant="danger" loading={remove.isPending} onClick={() => remove.mutate()}>
                  Supprimer
                </Button>
              </>
            )}
          </div>
        }
      />
      <div className="mb-6 flex flex-wrap gap-2">
        <Badge tone="brand">{TRAINING_KINDS[t.kind]}</Badge>
        {t.category && <Badge>{t.category}</Badge>}
        {!t.is_active && <Badge tone="warning">Désactivée</Badge>}
      </div>

      <Card className="mb-8 space-y-4">
        {t.picture_path && (
          <img
            src={uploadUrl(t.picture_path)}
            alt=""
            className="max-h-64 w-full rounded-lg object-cover"
          />
        )}
        {t.description ? (
          <p className="whitespace-pre-wrap">{t.description}</p>
        ) : (
          <p className="text-slate-500">Pas de description.</p>
        )}
        {t.documents.length > 0 && (
          <ul className="space-y-1">
            {t.documents.map((path) => (
              <li key={path}>
                <a
                  href={uploadUrl(path)}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 text-sm text-brand-700 hover:underline dark:text-brand-300"
                >
                  <FileText size={14} aria-hidden="true" /> {path.split('/').pop()}
                </a>
              </li>
            ))}
          </ul>
        )}
      </Card>

      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-lg font-semibold">Sessions</h2>
        {canManage && (
          <Button size="sm" onClick={() => setAddingSession(true)}>
            <Plus size={14} aria-hidden="true" /> Session
          </Button>
        )}
      </div>
      {sessions.isLoading && <Spinner />}
      {sessions.data?.length === 0 && <EmptyState title="Aucune session programmée" />}
      <ul className="divide-y divide-slate-200 rounded-xl border border-slate-200 bg-white px-4 dark:divide-slate-800 dark:border-slate-800 dark:bg-slate-900">
        {sessions.data?.map((session) => (
          <SessionRow
            key={session.id}
            session={session}
            trainingId={t.id}
            canManage={canManage}
            onManage={setManaged}
          />
        ))}
      </ul>

      {editing && <TrainingFormModal training={t} onClose={() => setEditing(false)} />}
      {addingSession && (
        <SessionFormModal trainingId={t.id} onClose={() => setAddingSession(false)} />
      )}
      {managed && (
        <SessionAdminModal session={managed} trainingId={t.id} onClose={() => setManaged(null)} />
      )}
    </>
  )
}
