/** Page d'accueil des membres : calendrier du mois, événements du jour et à venir. */

import { CalendarDays, ChevronLeft, ChevronRight, Clock } from 'lucide-react'
import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'

import { useAuth } from '../../auth/AuthProvider'
import { cn } from '../../lib/cn'
import { WEEKDAYS, buildMonthGrid, formatLongDate, monthLabel, toISODate } from '../../lib/calendar'
import { KIND_STYLES, useAgendaItems } from '../agenda/useAgendaItems'

/** Raccourcis de recherche, centrés sous l'accueil. */
const SHORTCUTS = [
  { to: '/annuaire', label: "Trouver quelqu'un" },
  { to: '/entreprises', label: 'Trouver une entreprise' },
  { to: '/formations', label: 'Trouver une formation' },
]

/** Nombre de jours pris en compte pour « Prochains événements ». */
const UPCOMING_DAYS = 90

/** Ligne d'élément d'agenda : pastille de la couleur de son type, titre et heure. */
function EventRow({ event, withDate = false }) {
  return (
    <li className="flex items-start gap-3">
      <span
        className={`${KIND_STYLES[event.kind].dot} mt-1.5 h-2 w-2 shrink-0 rounded-full`}
        aria-hidden="true"
      />
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium">{event.title}</p>
        <p className="flex items-center gap-1 text-xs text-slate-500">
          <Clock size={11} aria-hidden="true" />
          {withDate && <span className="capitalize">{formatLongDate(event.date)}</span>}
          {withDate && event.time && ' · '}
          {event.time}
        </p>
      </div>
    </li>
  )
}

/** Accueil : agenda du mois en lecture, avec les prochains rendez-vous. */
export default function DashboardPage() {
  const { user } = useAuth()
  const today = toISODate(new Date())
  const [cursor, setCursor] = useState(() => {
    const now = new Date()
    return { year: now.getFullYear(), month: now.getMonth() }
  })
  const [selected, setSelected] = useState(today)

  const weeks = useMemo(() => buildMonthGrid(cursor.year, cursor.month), [cursor])
  const { byDay, isError } = useAgendaItems(weeks[0][0].iso, weeks[weeks.length - 1][6].iso)
  const upcomingEnd = useMemo(() => {
    const d = new Date()
    d.setDate(d.getDate() + UPCOMING_DAYS)
    return toISODate(d)
  }, [])
  const { items: ahead } = useAgendaItems(today, upcomingEnd)
  const upcoming = useMemo(() => ahead.slice(0, 5), [ahead])
  const selectedEvents = byDay.get(selected) ?? []

  const move = (delta) =>
    setCursor(({ year, month }) => {
      const d = new Date(year, month + delta, 1)
      return { year: d.getFullYear(), month: d.getMonth() }
    })

  return (
    <div className="flex min-h-0 flex-col gap-4 lg:h-full lg:overflow-hidden">
      <header className="flex flex-col items-center gap-4 text-center">
        <div className="flex flex-col items-center">
          <p className="text-xs font-semibold tracking-[0.2em] text-slate-500 uppercase">
            {new Date().toLocaleDateString('fr-FR', {
              weekday: 'long',
              day: 'numeric',
              month: 'long',
            })}
          </p>
          <h1 className="mt-2 text-4xl leading-tight tracking-tight sm:text-5xl">
            <span className="font-light">Bonjour</span>
            {user?.first_name && <span className="font-bold"> {user.first_name}</span>}
          </h1>
          <span className="mt-3 block h-1 w-12 bg-[#7ec843]" aria-hidden="true" />
        </div>
        <ul className="flex flex-wrap justify-center gap-3">
          {SHORTCUTS.map(({ to, label }) => (
            <li key={to}>
              <Link
                to={to}
                className="bg-brand-600 hover:bg-brand-700 block min-w-52 rounded-md px-5 py-2.5 text-center text-sm font-semibold text-white transition"
              >
                {label}
              </Link>
            </li>
          ))}
        </ul>
      </header>
      {isError && <p role="alert">Impossible de charger l'agenda.</p>}

      <div className="grid min-h-0 flex-1 grid-cols-1 gap-4 lg:grid-cols-5">
        <section
          aria-label="Calendrier"
          className="flex min-h-0 flex-col overflow-hidden rounded-xl border border-slate-200 bg-white p-4 lg:col-span-3"
        >
          <div className="mb-2 flex items-center justify-between">
            <button
              type="button"
              aria-label="Mois précédent"
              onClick={() => move(-1)}
              className="rounded-lg p-1 hover:bg-slate-100"
            >
              <ChevronLeft size={18} aria-hidden="true" />
            </button>
            <h2 className="text-base font-semibold capitalize" aria-live="polite">
              {monthLabel(cursor.year, cursor.month)}
            </h2>
            <button
              type="button"
              aria-label="Mois suivant"
              onClick={() => move(1)}
              className="rounded-lg p-1 hover:bg-slate-100"
            >
              <ChevronRight size={18} aria-hidden="true" />
            </button>
          </div>
          <div className="grid grid-cols-7">
            {WEEKDAYS.map((day) => (
              <div key={day} className="py-1 text-center text-xs font-semibold text-slate-500">
                {day}
              </div>
            ))}
          </div>
          <div className="grid min-h-0 flex-1 grid-cols-7 content-evenly gap-y-0.5">
            {weeks.flat().map((day) => {
              const isSelected = day.iso === selected
              return (
                <button
                  key={day.iso}
                  type="button"
                  aria-pressed={isSelected}
                  aria-label={formatLongDate(day.iso)}
                  onClick={() => setSelected(day.iso)}
                  className={cn(
                    'relative mx-auto flex h-8 w-8 items-center justify-center rounded-full text-sm font-medium transition-colors',
                    !day.inMonth && 'text-slate-400',
                    isSelected
                      ? 'bg-brand-600 text-white'
                      : day.iso === today
                        ? 'bg-brand-400/15 text-brand-700 font-bold'
                        : 'hover:bg-slate-100',
                  )}
                >
                  {day.date.getDate()}
                  {byDay.has(day.iso) && !isSelected && (
                    <span className="absolute bottom-0.5 flex gap-0.5" aria-hidden="true">
                      {[...new Set(byDay.get(day.iso).map((i) => i.kind))].map((kind) => (
                        <span
                          key={kind}
                          className={`h-1 w-1 rounded-full ${KIND_STYLES[kind].dot}`}
                        />
                      ))}
                    </span>
                  )}
                </button>
              )
            })}
          </div>
          <ul
            aria-label="Légende"
            className="mt-2 flex flex-wrap justify-center gap-x-4 gap-y-1 text-xs text-slate-500"
          >
            {Object.entries(KIND_STYLES).map(([kind, style]) => (
              <li key={kind} className="flex items-center gap-1.5">
                <span className={`${style.dot} h-2 w-2 rounded-full`} aria-hidden="true" />
                {style.label}
              </li>
            ))}
          </ul>
        </section>

        <div className="flex min-h-0 flex-col gap-4 lg:col-span-2">
          <section className="min-h-0 flex-1 overflow-hidden rounded-xl border border-slate-200 bg-white p-4">
            <h2 className="mb-3 flex items-center gap-2 text-sm font-bold capitalize">
              <CalendarDays size={16} className="text-brand-600" aria-hidden="true" />
              {formatLongDate(selected)}
            </h2>
            {selectedEvents.length > 0 ? (
              <ul className="space-y-2">
                {selectedEvents.slice(0, 3).map((event) => (
                  <EventRow key={event.id} event={event} />
                ))}
              </ul>
            ) : (
              <p className="text-sm text-slate-500">Aucun événement ce jour</p>
            )}
            {selectedEvents.length > 3 && (
              <Link to="/agenda" className="text-brand-700 mt-2 block text-xs hover:underline">
                +{selectedEvents.length - 3} autre(s) — voir l'agenda
              </Link>
            )}
          </section>

          <section className="min-h-0 flex-1 overflow-hidden rounded-xl border border-slate-200 bg-white p-4">
            <h2 className="mb-3 text-sm font-bold">Prochains événements</h2>
            {upcoming.length > 0 ? (
              <ul className="space-y-2">
                {upcoming.slice(0, 3).map((event) => (
                  <EventRow key={event.id} event={event} withDate />
                ))}
              </ul>
            ) : (
              <p className="text-sm text-slate-500">Aucun événement à venir</p>
            )}
            <Link to="/agenda" className="text-brand-700 mt-2 block text-xs hover:underline">
              Voir tout l'agenda
            </Link>
          </section>
        </div>
      </div>
    </div>
  )
}
