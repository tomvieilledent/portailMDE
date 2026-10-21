/** Éléments d'agenda (événements et sessions de formation) fusionnés, avec leurs couleurs. */

import { useMemo } from 'react'

import { shortTime, toISODate } from '../../lib/calendar'
import { useTrainings } from '../trainings/queries'
import { useEvents, useSessions } from './queries'

/** Style par type : pastille (agenda), point (listes et calendrier d'accueil) et libellé de légende. */
export const KIND_STYLES = {
  event: {
    chip: 'bg-brand-100 text-brand-800 hover:bg-brand-200',
    dot: 'bg-brand-500',
    label: 'Événements',
  },
  session: {
    chip: 'bg-violet-100 text-violet-800 hover:bg-violet-200',
    dot: 'bg-violet-500',
    label: 'Formations proposées',
  },
  enrolled: {
    chip: 'bg-orange-100 text-orange-800 ring-1 ring-orange-400 hover:bg-orange-200',
    dot: 'bg-orange-500',
    label: 'Mes formations (inscrit·e)',
  },
}

/**
 * Événements et sessions de formation (hors annulées) entre `start` et `end` (AAAA-MM-JJ) :
 * `items` triés chronologiquement et `byDay` (Map jour → éléments).
 */
export function useAgendaItems(start, end) {
  const events = useEvents(start, end)
  const sessions = useSessions(start, end)
  const trainings = useTrainings({})
  const eventData = events.data
  const sessionData = sessions.data
  const trainingData = trainings.data

  const items = useMemo(() => {
    const titles = new Map((trainingData?.items ?? []).map((t) => [t.id, t.title]))
    const fromEvents = (Array.isArray(eventData) ? eventData : []).map((e) => ({
      key: e.id,
      kind: 'event',
      title: e.title,
      date: e.event_date,
      time: shortTime(e.event_time),
      event: e,
    }))
    const fromSessions = (Array.isArray(sessionData) ? sessionData : [])
      .filter((s) => s.status !== 'cancelled')
      .map((s) => {
        const startDate = new Date(s.start_at)
        return {
          key: `session-${s.id}`,
          kind: s.is_enrolled ? 'enrolled' : 'session',
          title: titles.get(s.training_id) ?? 'Formation',
          date: toISODate(startDate),
          time: startDate.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' }),
          trainingId: s.training_id,
        }
      })
    return [...fromEvents, ...fromSessions].sort((a, b) =>
      `${a.date}${a.time ?? ''}`.localeCompare(`${b.date}${b.time ?? ''}`),
    )
  }, [eventData, sessionData, trainingData])

  const byDay = useMemo(() => {
    const map = new Map()
    items.forEach((item) => map.set(item.date, [...(map.get(item.date) ?? []), item]))
    return map
  }, [items])

  return { items, byDay, isError: events.isError }
}
