import React, { useState, useEffect } from 'react'
import { ChevronLeft, ChevronRight, CalendarDays, Clock, Plus, Pencil, Trash2 } from 'lucide-react'
import EventFormModal from '../modals/EventFormModal'
import { api } from '../../lib/api'
import { useAuth, displayName } from '../../context/AuthContext'

const DAYS = ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim']
const MONTHS = ['Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin', 'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre']

function toKey(date) {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}

function formatDateLabel(dateStr) {
  const [y, m, d] = dateStr.split('-')
  return `${parseInt(d)} ${MONTHS[parseInt(m) - 1]} ${y}`
}

export default function DashboardPage() {
  const { user, isAdmin } = useAuth()
  const today = new Date()
  const todayKey = toKey(today)

  const [events, setEvents] = useState([])
  const [sessions, setSessions] = useState([])
  const [trainingTitles, setTrainingTitles] = useState({})
  const [users, setUsers] = useState([])
  const [error, setError] = useState('')
  const [viewDate, setViewDate] = useState(new Date(today.getFullYear(), today.getMonth(), 1))
  const [selectedDate, setSelectedDate] = useState(todayKey)
  const [createModal, setCreateModal] = useState(null) // null | string (date key)
  const [editModal, setEditModal] = useState(null)    // null | event object

  // Les événements sont partagés : tout le monde les voit, tout le monde peut
  // en créer ; seul le créateur (ou un super admin) peut modifier/supprimer.
  useEffect(() => {
    let cancelled = false
    Promise.all([
      api.getEvents(),
      api.getSessions().catch(() => ({ sessions: [] })),
      api.getTrainings().catch(() => ({ trainings: [] })),
      api.getUsers().catch(() => ({ users: [] })),
    ])
      .then(([evRes, sRes, tRes, uRes]) => {
        if (cancelled) return
        setEvents(evRes?.events || (Array.isArray(evRes) ? evRes : []))
        setSessions(sRes?.sessions || (Array.isArray(sRes) ? sRes : []))
        const tList = tRes?.trainings || tRes?.items || (Array.isArray(tRes) ? tRes : [])
        setTrainingTitles(Object.fromEntries(tList.map((t) => [t.id, t.title])))
        setUsers(uRes?.users || (Array.isArray(uRes) ? uRes : []))
      })
      .catch((err) => { if (!cancelled) setError(err.message) })
    return () => { cancelled = true }
  }, [])

  // Les sessions de formation programmées sont injectées dans l'agenda comme
  // des événements (non modifiables : ils se gèrent depuis l'onglet Formations).
  const sessionEvents = sessions
    .filter((s) => s.status !== 'cancelled' && s.status !== 'completed' && s.start_date)
    .map((s) => {
      const d = new Date(s.start_date)
      if (isNaN(d)) return null
      const time = `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
      return {
        id: `session-${s.id}`,
        title: trainingTitles[s.training_id] || 'Formation',
        date: toKey(d),
        time,
        color: 'bg-purple-500',
        creator: 'Formation',
        isSession: true,
      }
    })
    .filter(Boolean)

  const allEvents = [...events, ...sessionEvents]

  const canEdit = (ev) => !ev.isSession && (isAdmin || (user && ev.created_by === user.id))

  const year = viewDate.getFullYear()
  const month = viewDate.getMonth()

  const firstDayOffset = (new Date(year, month, 1).getDay() + 6) % 7
  const daysInMonth = new Date(year, month + 1, 0).getDate()

  const cells = []
  for (let i = 0; i < firstDayOffset; i++) cells.push(null)
  for (let d = 1; d <= daysInMonth; d++) cells.push(d)

  const eventsByDate = allEvents.reduce((acc, ev) => {
    acc[ev.date] = acc[ev.date] || []
    acc[ev.date].push(ev)
    return acc
  }, {})

  const selectedEvents = (eventsByDate[selectedDate] || [])
    .slice()
    .sort((a, b) => a.time.localeCompare(b.time))

  const upcoming = allEvents
    .filter((ev) => ev.date >= todayKey)
    .sort((a, b) => a.date.localeCompare(b.date) || a.time.localeCompare(b.time))
    .slice(0, 5)

  const handleDayClick = (key) => {
    setSelectedDate(key)
  }

  const handleSaveEvent = async (ev) => {
    const payload = {
      title: ev.title,
      date: ev.date,
      time: ev.time,
      color: ev.color,
      description: ev.description || '',
      creator: ev.creator || displayName(user),
      is_public: !!ev.is_public,
    }
    try {
      let saved
      if (ev.id && events.some((e) => e.id === ev.id)) {
        const res = await api.updateEvent(ev.id, payload)
        saved = res?.event || res
        setEvents((prev) => prev.map((e) => (e.id === ev.id ? saved : e)))
      } else {
        const res = await api.createEvent(payload)
        saved = res?.event || res
        setEvents((prev) => [...prev, saved])
      }
      // Envoi des invitations (sélection ou « tout le monde »).
      if (saved?.id && (ev.inviteAll || (ev.inviteeIds && ev.inviteeIds.length))) {
        await api.createInvitations({
          target_type: 'event', target_id: saved.id, target_title: saved.title,
          invitee_ids: ev.inviteeIds || [], all: !!ev.inviteAll,
        }).catch(() => { /* l'événement est créé, l'invitation est best-effort */ })
      }
      setSelectedDate(ev.date)
    } catch (err) {
      setError(err.message)
      throw err
    }
  }

  const handleDeleteEvent = async (id) => {
    try {
      await api.deleteEvent(id)
      setEvents((prev) => prev.filter((e) => e.id !== id))
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <>
      <div>
        <div className="mb-6">
          <h2 className="text-2xl font-bold text-gray-900">Accueil</h2>
          <p className="text-sm text-gray-500 mt-1">Votre agenda et prochains événements</p>
          {error && <p className="text-sm text-red-500 mt-2">{error}</p>}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
          {/* Calendrier */}
          <div className="lg:col-span-3 bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <div className="flex items-center justify-between mb-5">
              <button
                onClick={() => setViewDate(new Date(year, month - 1, 1))}
                className="p-1.5 rounded-lg hover:bg-gray-100 transition-colors"
              >
                <ChevronLeft size={18} className="text-gray-500" />
              </button>
              <h3 className="text-base font-bold text-gray-900">{MONTHS[month]} {year}</h3>
              <button
                onClick={() => setViewDate(new Date(year, month + 1, 1))}
                className="p-1.5 rounded-lg hover:bg-gray-100 transition-colors"
              >
                <ChevronRight size={18} className="text-gray-500" />
              </button>
            </div>

            <div className="grid grid-cols-7 mb-2">
              {DAYS.map((d) => (
                <div key={d} className="text-center text-xs font-semibold text-gray-400 py-1">{d}</div>
              ))}
            </div>

            <div className="grid grid-cols-7 gap-y-1">
              {cells.map((day, i) => {
                if (!day) return <div key={`e-${i}`} />
                const key = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`
                const hasEvents = !!eventsByDate[key]
                const isToday = key === todayKey
                const isSelected = key === selectedDate
                return (
                  <button
                    key={key}
                    onClick={() => handleDayClick(key)}
                    title="Voir les événements du jour"
                    className={`group relative mx-auto w-9 h-9 flex flex-col items-center justify-center rounded-full text-sm font-medium transition-colors
                      ${isSelected
                        ? 'bg-primary-light text-white'
                        : isToday
                        ? 'bg-primary-light/10 text-primary-light font-bold'
                        : 'hover:bg-gray-100 text-gray-700'
                      }`}
                  >
                    {day}
                    {hasEvents && !isSelected && (
                      <span className="absolute bottom-1 w-1 h-1 rounded-full bg-orange-400" />
                    )}
                  </button>
                )
              })}
            </div>
          </div>

          {/* Panneau événements */}
          <div className="lg:col-span-2 flex flex-col gap-4">
            {/* Événements du jour sélectionné */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5 flex-1">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <CalendarDays size={16} className="text-primary-light" />
                  <h3 className="text-sm font-bold text-gray-900">{formatDateLabel(selectedDate)}</h3>
                </div>
                <button
                  onClick={() => setCreateModal(selectedDate)}
                  title="Ajouter un événement"
                  className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-primary-light/10 hover:bg-primary-light/20 text-primary-light text-xs font-medium transition-colors"
                >
                  <Plus size={13} /> Ajouter
                </button>
              </div>
              {selectedEvents.length > 0 ? (
                <div className="space-y-2">
                  {selectedEvents.map((ev) => (
                    <div key={ev.id} className="group flex items-start gap-3 p-2 rounded-lg hover:bg-gray-50 transition-colors">
                      <div className={`w-2 h-2 rounded-full mt-1.5 flex-shrink-0 ${ev.color}`} />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900">{ev.title}</p>
                        <p className="flex items-center gap-1 text-xs text-gray-400 mt-0.5">
                          <Clock size={11} /> {ev.time}
                        </p>
                        {ev.description && (
                          <p className="text-xs text-gray-400 mt-0.5">{ev.description}</p>
                        )}
                      </div>
                      {canEdit(ev) && (
                        <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0">
                          <button
                            onClick={() => setEditModal(ev)}
                            title="Modifier"
                            className="p-1.5 rounded-lg hover:bg-blue-50 text-gray-400 hover:text-blue-500 transition-colors"
                          >
                            <Pencil size={13} />
                          </button>
                          <button
                            onClick={() => handleDeleteEvent(ev.id)}
                            title="Supprimer"
                            className="p-1.5 rounded-lg hover:bg-red-50 text-gray-400 hover:text-red-500 transition-colors"
                          >
                            <Trash2 size={13} />
                          </button>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-gray-400">Aucun événement ce jour</p>
              )}
            </div>

            {/* Prochains événements */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
              <h3 className="text-sm font-bold text-gray-900 mb-4">Prochains événements</h3>
              {upcoming.length > 0 ? (
                <div className="space-y-3">
                  {upcoming.map((ev) => (
                    <div key={ev.id} className="flex items-start gap-3">
                      <div className={`w-2 h-2 rounded-full mt-1.5 flex-shrink-0 ${ev.color}`} />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900 truncate flex items-center gap-1.5">
                          {ev.title}
                          {ev.isSession && (
                            <span className="px-1.5 py-0.5 rounded-full text-[10px] font-semibold bg-purple-100 text-purple-600">Formation</span>
                          )}
                        </p>
                        <p className="text-xs text-gray-400">{formatDateLabel(ev.date)} · {ev.time}</p>
                        {ev.creator && !ev.isSession && (
                          <p className="text-xs text-gray-400 mt-0.5">Par {ev.creator}</p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-gray-400">Aucun événement à venir</p>
              )}
            </div>
          </div>
        </div>
      </div>

      {createModal && (
        <EventFormModal
          date={createModal}
          users={users}
          currentUserId={user?.id}
          onClose={() => setCreateModal(null)}
          onSave={handleSaveEvent}
        />
      )}

      {editModal && (
        <EventFormModal
          event={editModal}
          date={editModal.date}
          users={users}
          currentUserId={user?.id}
          onClose={() => setEditModal(null)}
          onSave={(ev) => { handleSaveEvent(ev); setEditModal(null) }}
        />
      )}
    </>
  )
}
