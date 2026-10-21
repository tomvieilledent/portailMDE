/** Page de l'agenda mensuel. */

import { ChevronLeft, ChevronRight, Download, Plus } from 'lucide-react'
import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import PageHeader from '../../components/layout/PageHeader'
import { Button, useToast } from '../../components/ui'
import { cn } from '../../lib/cn'
import { WEEKDAYS, buildMonthGrid, monthLabel, shortTime, toISODate } from '../../lib/calendar'
import { downloadFile } from '../../lib/download'
import EventDetailModal from './EventDetailModal'
import EventFormModal from './EventFormModal'
import InvitationsPanel from './InvitationsPanel'
import { useTrainings } from '../trainings/queries'
import { useEvents, useSessions } from './queries'

/** Couleurs des pastilles : événements, formations proposées, formations où l'on est inscrit. */
const CHIP = {
  event: 'bg-brand-100 text-brand-800 hover:bg-brand-200',
  session: 'bg-violet-100 text-violet-800 hover:bg-violet-200',
  enrolled: 'bg-orange-100 text-orange-800 ring-1 ring-orange-400 hover:bg-orange-200',
}

/** Agenda mensuel : événements publics et ceux auxquels on est invité. */
export default function AgendaPage() {
  const toast = useToast()
  const navigate = useNavigate()
  const today = toISODate(new Date())
  const [cursor, setCursor] = useState(() => {
    const now = new Date()
    return { year: now.getFullYear(), month: now.getMonth() }
  })
  const [detail, setDetail] = useState(null)
  const [form, setForm] = useState(null) // { event?, defaultDate }

  const weeks = useMemo(() => buildMonthGrid(cursor.year, cursor.month), [cursor])
  const start = weeks[0][0].iso
  const end = weeks[weeks.length - 1][6].iso
  const monthStart = toISODate(new Date(cursor.year, cursor.month, 1))
  const monthEnd = toISODate(new Date(cursor.year, cursor.month + 1, 0))
  const { data: events = [], isError } = useEvents(start, end)

  const sessionsQuery = useSessions(start, end)
  const trainings = useTrainings({})
  const titleById = useMemo(
    () => new Map((trainings.data?.items ?? []).map((t) => [t.id, t.title])),
    [trainings.data],
  )

  // Événements et sessions de formation fusionnés par jour, avec leur couleur.
  const byDay = useMemo(() => {
    const map = new Map()
    const add = (day, item) => map.set(day, [...(map.get(day) ?? []), item])
    events.forEach((e) =>
      add(e.event_date, {
        key: e.id,
        kind: 'event',
        title: e.title,
        time: shortTime(e.event_time),
        event: e,
      }),
    )
    const sessions = Array.isArray(sessionsQuery.data) ? sessionsQuery.data : []
    sessions
      .filter((s) => s.status !== 'cancelled')
      .forEach((s) => {
        const startDate = new Date(s.start_at)
        add(toISODate(startDate), {
          key: `session-${s.id}`,
          kind: s.is_enrolled ? 'enrolled' : 'session',
          title: titleById.get(s.training_id) ?? 'Formation',
          time: startDate.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' }),
          trainingId: s.training_id,
        })
      })
    return map
  }, [events, sessionsQuery.data, titleById])

  const move = (delta) =>
    setCursor(({ year, month }) => {
      const d = new Date(year, month + delta, 1)
      return { year: d.getFullYear(), month: d.getMonth() }
    })

  return (
    <>
      <PageHeader
        title="Agenda"
        actions={
          <div className="flex gap-2">
            <Button
              onClick={() =>
                downloadFile(
                  `/api/v1/events/export.pdf?start=${monthStart}&end=${monthEnd}`,
                  `agenda-${monthStart.slice(0, 7)}.pdf`,
                ).catch(() => toast.error('Export impossible.'))
              }
            >
              <Download size={16} aria-hidden="true" /> Affiche PDF du mois
            </Button>
            <Button
              variant="secondary"
              onClick={() =>
                downloadFile(
                  `/api/v1/events/export.ics?start=${start}&end=${end}`,
                  'agenda.ics',
                ).catch(() => toast.error('Export impossible.'))
              }
            >
              <Download size={16} aria-hidden="true" /> Calendrier (.ics)
            </Button>
            <Button onClick={() => setForm({ defaultDate: today })}>
              <Plus size={16} aria-hidden="true" /> Événement
            </Button>
          </div>
        }
      />
      <InvitationsPanel />

      <div className="mb-3 flex items-center justify-between">
        <Button variant="ghost" aria-label="Mois précédent" onClick={() => move(-1)}>
          <ChevronLeft size={18} />
        </Button>
        <h2 className="text-lg font-semibold capitalize" aria-live="polite">
          {monthLabel(cursor.year, cursor.month)}
        </h2>
        <Button variant="ghost" aria-label="Mois suivant" onClick={() => move(1)}>
          <ChevronRight size={18} />
        </Button>
      </div>
      <ul aria-label="Légende" className="mb-3 flex flex-wrap gap-2 text-xs">
        <li className={cn('rounded px-2 py-1', CHIP.event)}>Événements</li>
        <li className={cn('rounded px-2 py-1', CHIP.session)}>Formations proposées</li>
        <li className={cn('rounded px-2 py-1', CHIP.enrolled)}>Mes formations (inscrit·e)</li>
      </ul>
      {isError && <p role="alert">Impossible de charger l'agenda.</p>}

      <div
        role="table"
        aria-label="Calendrier"
        className="overflow-hidden rounded-xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900"
      >
        <div
          role="row"
          className="grid grid-cols-7 border-b border-slate-200 dark:border-slate-800"
        >
          {WEEKDAYS.map((day) => (
            <div
              key={day}
              role="columnheader"
              className="p-2 text-center text-xs font-semibold text-slate-500"
            >
              {day}
            </div>
          ))}
        </div>
        {weeks.map((week) => (
          <div key={week[0].iso} role="row" className="grid grid-cols-7">
            {week.map((day) => (
              <div
                key={day.iso}
                role="cell"
                className={cn(
                  'h-[4.5rem] overflow-hidden border-r border-b border-slate-100 p-1 dark:border-slate-800',
                  !day.inMonth && 'bg-slate-50 text-slate-500 dark:bg-slate-950/40',
                )}
              >
                <button
                  type="button"
                  aria-label={`Ajouter un événement le ${day.date.toLocaleDateString('fr-FR', {
                    weekday: 'long',
                    day: 'numeric',
                    month: 'long',
                    year: 'numeric',
                  })}`}
                  onClick={() => setForm({ defaultDate: day.iso })}
                  className={cn(
                    'mb-1 inline-flex h-6 w-6 items-center justify-center rounded-full text-xs hover:bg-slate-100 dark:hover:bg-slate-800',
                    day.iso === today && 'bg-brand-700 hover:bg-brand-800 font-bold text-white',
                  )}
                >
                  {day.date.getDate()}
                </button>
                <ul className="space-y-0.5">
                  {(byDay.get(day.iso) ?? []).slice(0, 2).map((item) => (
                    <li key={item.key}>
                      <button
                        type="button"
                        onClick={() =>
                          item.kind === 'event'
                            ? setDetail(item.event)
                            : navigate(`/formations/${item.trainingId}`)
                        }
                        className={cn(
                          'block w-full truncate rounded px-1 py-0.5 text-left text-xs',
                          CHIP[item.kind],
                        )}
                      >
                        {item.time && <span>{item.time} </span>}
                        {item.title}
                      </button>
                    </li>
                  ))}
                </ul>
                {(byDay.get(day.iso)?.length ?? 0) > 2 && (
                  <p className="px-1 text-[10px] text-slate-500">
                    +{byDay.get(day.iso).length - 2} autre(s)
                  </p>
                )}
              </div>
            ))}
          </div>
        ))}
      </div>

      {detail && (
        <EventDetailModal
          event={detail}
          onClose={() => setDetail(null)}
          onEdit={(event) => {
            setDetail(null)
            setForm({ event })
          }}
        />
      )}
      {form && (
        <EventFormModal
          event={form.event}
          defaultDate={form.defaultDate}
          onClose={() => setForm(null)}
        />
      )}
    </>
  )
}
