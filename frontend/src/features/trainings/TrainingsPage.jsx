/** Page du catalogue des formations. */

import { GraduationCap, Plus, Search } from 'lucide-react'
import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'

import { useAuth } from '../../auth/AuthProvider'
import { PERMISSIONS, hasPermission } from '../../auth/permissions'
import PageHeader from '../../components/layout/PageHeader'
import { Badge, Button, Card, EmptyState, Input, Select, Spinner } from '../../components/ui'
import { cn } from '../../lib/cn'
import { uploadUrl } from '../../lib/uploads'
import InterestButton from './InterestButton'
import TrainingFormModal from './TrainingFormModal'
import { TRAINING_KINDS, useMyEnrollments, useTrainings } from './queries'

const TABS = [
  { id: 'catalogue', label: 'Catalogue' },
  { id: 'mine', label: 'Mes formations' },
]

/** Catalogue des formations et ateliers, et suivi de ses inscriptions / favoris. */
export default function TrainingsPage() {
  const { user } = useAuth()
  const canManage = hasPermission(user, PERMISSIONS.MANAGE_TRAININGS)
  const [tab, setTab] = useState('catalogue')
  const [search, setSearch] = useState('')
  const [kind, setKind] = useState('')
  const [creating, setCreating] = useState(false)
  const trainings = useTrainings({})
  const mine = useMyEnrollments()

  const interested = useMemo(
    () => new Set((mine.data ?? []).filter((e) => e.interested).map((e) => e.training_id)),
    [mine.data],
  )
  const myIds = useMemo(() => new Set((mine.data ?? []).map((e) => e.training_id)), [mine.data])
  const enrolledByTraining = useMemo(
    () => new Map((mine.data ?? []).map((e) => [e.training_id, e])),
    [mine.data],
  )

  const visible = (trainings.data?.items ?? []).filter(
    (t) =>
      (tab === 'catalogue' || myIds.has(t.id)) &&
      (!kind || t.kind === kind) &&
      (!search || `${t.title} ${t.description ?? ''}`.toLowerCase().includes(search.toLowerCase())),
  )

  return (
    <>
      <PageHeader
        title="Formations"
        description="Formations et ateliers proposés aux entreprises."
        actions={
          canManage && (
            <Button onClick={() => setCreating(true)}>
              <Plus size={16} aria-hidden="true" /> Nouvelle formation
            </Button>
          )
        }
      />
      <div
        role="tablist"
        className="mb-6 flex gap-2 border-b border-slate-200 dark:border-slate-800"
      >
        {TABS.map(({ id, label }) => (
          <button
            key={id}
            role="tab"
            type="button"
            aria-selected={tab === id}
            onClick={() => setTab(id)}
            className={cn(
              '-mb-px border-b-2 px-4 py-2 text-sm font-medium',
              tab === id
                ? 'border-brand-700 text-brand-700 dark:border-brand-300 dark:text-brand-300'
                : 'border-transparent text-slate-500 hover:text-slate-700',
            )}
          >
            {label}
          </button>
        ))}
      </div>

      <div className="mb-6 flex flex-wrap items-end gap-4">
        <div className="relative w-full max-w-md">
          <Search
            size={16}
            className="pointer-events-none absolute top-9 left-3 text-slate-400"
            aria-hidden="true"
          />
          <Input
            label="Rechercher"
            type="search"
            className="pl-9"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <Select label="Type" value={kind} onChange={(e) => setKind(e.target.value)}>
          <option value="">Tous</option>
          {Object.entries(TRAINING_KINDS).map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </Select>
      </div>

      {trainings.isLoading && <Spinner />}
      {trainings.isError && <p role="alert">Impossible de charger les formations.</p>}
      {trainings.data && visible.length === 0 && (
        <EmptyState
          icon={GraduationCap}
          title={tab === 'mine' ? 'Aucune inscription ni favori' : 'Aucune formation trouvée'}
        />
      )}
      <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {visible.map((training) => {
          const enrollment = enrolledByTraining.get(training.id)
          return (
            <li key={training.id}>
              <Link to={`/formations/${training.id}`} className="block h-full">
                <Card className="hover:border-brand-400 flex h-full flex-col gap-3 overflow-hidden p-0 transition hover:shadow-md">
                  {training.picture_path ? (
                    <img
                      src={uploadUrl(training.picture_path)}
                      alt=""
                      className="h-36 w-full object-cover"
                    />
                  ) : (
                    <div className="bg-brand-50 text-brand-400 dark:bg-brand-900/30 flex h-36 items-center justify-center">
                      <GraduationCap size={40} aria-hidden="true" />
                    </div>
                  )}
                  <div className="flex flex-1 flex-col gap-2 p-4 pt-0">
                    <div className="flex items-start justify-between gap-2">
                      <h2 className="font-semibold">{training.title}</h2>
                      <InterestButton
                        trainingId={training.id}
                        active={interested.has(training.id)}
                      />
                    </div>
                    <div className="flex flex-wrap gap-2">
                      <Badge tone="brand">{TRAINING_KINDS[training.kind]}</Badge>
                      {training.category && <Badge>{training.category}</Badge>}
                      {!training.is_active && <Badge tone="warning">Désactivée</Badge>}
                      {enrollment?.completed_at && <Badge tone="success">Terminée</Badge>}
                      {enrollment?.enrolled_at && !enrollment.completed_at && (
                        <Badge tone="success">Inscrit</Badge>
                      )}
                    </div>
                    {training.description && (
                      <p className="line-clamp-3 text-sm text-slate-600 dark:text-slate-400">
                        {training.description}
                      </p>
                    )}
                  </div>
                </Card>
              </Link>
            </li>
          )
        })}
      </ul>
      {creating && <TrainingFormModal onClose={() => setCreating(false)} />}
    </>
  )
}
