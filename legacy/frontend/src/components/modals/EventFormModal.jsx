import React, { useState } from 'react'
import { X, CalendarDays, Clock, Tag, AlignLeft, Pencil, User, Globe, Lock } from 'lucide-react'
import InviteePicker from '../InviteePicker'
import InvitationResponses from '../InvitationResponses'

const MONTHS = ['Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin', 'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre']

const COLOR_OPTIONS = [
  { label: 'Bleu',   value: 'bg-blue-500',   ring: 'ring-blue-400',   dot: 'bg-blue-500'   },
  { label: 'Violet', value: 'bg-purple-500',  ring: 'ring-purple-400', dot: 'bg-purple-500' },
  { label: 'Orange', value: 'bg-orange-400',  ring: 'ring-orange-300', dot: 'bg-orange-400' },
  { label: 'Vert',   value: 'bg-green-500',   ring: 'ring-green-400',  dot: 'bg-green-500'  },
  { label: 'Rouge',  value: 'bg-red-500',     ring: 'ring-red-400',    dot: 'bg-red-500'    },
]

function formatHeader(dateStr) {
  const [y, m, d] = dateStr.split('-')
  return `${parseInt(d)} ${MONTHS[parseInt(m) - 1]} ${y}`
}

export default function EventFormModal({ date, event, onClose, onSave, users = [], currentUserId = null }) {
  const isEdit = !!event
  const now = new Date()
  const defaultTime = `${String(now.getHours()).padStart(2, '0')}:00`

  const [form, setForm] = useState({
    title:       event?.title       || '',
    date:        event?.date        || date,
    time:        event?.time        || defaultTime,
    description: event?.description || '',
    color:       event?.color       || 'bg-blue-500',
    creator:     event?.creator     || '',
  })
  const [errors, setErrors] = useState({})
  const [isPublic, setIsPublic] = useState(!!event?.is_public)
  const [inviteAll, setInviteAll] = useState(false)
  const [invitees, setInvitees] = useState([])

  const set = (field) => (e) => setForm((prev) => ({ ...prev, [field]: e.target.value }))

  const validate = () => {
    const e = {}
    if (!form.title.trim()) e.title = 'Le titre est requis'
    if (!form.date) e.date = 'La date est requise'
    if (!form.time) e.time = "L'heure est requise"
    return e
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    const e2 = validate()
    if (Object.keys(e2).length) { setErrors(e2); return }
    onSave({
      ...(event || {}), ...form, title: form.title.trim(), id: event?.id ?? Date.now(),
      is_public: isPublic,
      inviteAll: isPublic ? false : inviteAll,
      inviteeIds: isPublic ? [] : invitees,
    })
    onClose()
  }

  return (
    <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4" onClick={onClose}>
      <div
        className="bg-white rounded-2xl shadow-2xl w-full max-w-md overflow-y-auto max-h-[92vh]"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="bg-primary-light px-6 py-5 flex items-start justify-between sticky top-0 z-10">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 bg-white/20 rounded-xl flex items-center justify-center">
              {isEdit ? <Pencil size={18} className="text-white" /> : <CalendarDays size={20} className="text-white" />}
            </div>
            <div>
              <h2 className="text-lg font-bold text-white">{isEdit ? 'Modifier l\'événement' : 'Nouvel événement'}</h2>
              <p className="text-sm text-white/80">{formatHeader(form.date)}</p>
            </div>
          </div>
          <button onClick={onClose} className="text-white/70 hover:text-white transition-colors mt-0.5">
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="px-6 py-6 space-y-5">
          {/* Titre */}
          <div>
            <label className="flex items-center gap-1.5 text-sm font-medium text-gray-700 mb-1.5">
              <Tag size={14} className="text-gray-400" /> Titre
            </label>
            <input
              autoFocus
              type="text"
              placeholder="Nom de l'événement"
              value={form.title}
              onChange={set('title')}
              className={`w-full px-3 py-2.5 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-light ${
                errors.title ? 'border-red-300 bg-red-50' : 'border-gray-200'
              }`}
            />
            {errors.title && <p className="mt-1 text-xs text-red-500">{errors.title}</p>}
          </div>

          {/* Créateur */}
          <div>
            <label className="flex items-center gap-1.5 text-sm font-medium text-gray-700 mb-1.5">
              <User size={14} className="text-gray-400" /> Créateur <span className="text-gray-400 font-normal">(optionnel)</span>
            </label>
            <input
              type="text"
              placeholder="Nom du créateur"
              value={form.creator}
              onChange={set('creator')}
              className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-light"
            />
          </div>

          {/* Date + Heure */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="flex items-center gap-1.5 text-sm font-medium text-gray-700 mb-1.5">
                <CalendarDays size={14} className="text-gray-400" /> Date
              </label>
              <input
                type="date"
                value={form.date}
                onChange={set('date')}
                className={`w-full px-3 py-2.5 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-light ${
                  errors.date ? 'border-red-300 bg-red-50' : 'border-gray-200'
                }`}
              />
              {errors.date && <p className="mt-1 text-xs text-red-500">{errors.date}</p>}
            </div>
            <div>
              <label className="flex items-center gap-1.5 text-sm font-medium text-gray-700 mb-1.5">
                <Clock size={14} className="text-gray-400" /> Heure
              </label>
              <input
                type="time"
                value={form.time}
                onChange={set('time')}
                className={`w-full px-3 py-2.5 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-light ${
                  errors.time ? 'border-red-300 bg-red-50' : 'border-gray-200'
                }`}
              />
              {errors.time && <p className="mt-1 text-xs text-red-500">{errors.time}</p>}
            </div>
          </div>

          {/* Description */}
          <div>
            <label className="flex items-center gap-1.5 text-sm font-medium text-gray-700 mb-1.5">
              <AlignLeft size={14} className="text-gray-400" /> Description <span className="text-gray-400 font-normal">(optionnel)</span>
            </label>
            <textarea
              rows={2}
              placeholder="Détails, lieu, notes…"
              value={form.description}
              onChange={set('description')}
              className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-light resize-none"
            />
          </div>

          {/* Couleur */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Couleur</label>
            <div className="flex gap-2">
              {COLOR_OPTIONS.map((c) => (
                <button
                  key={c.value}
                  type="button"
                  onClick={() => setForm((prev) => ({ ...prev, color: c.value }))}
                  title={c.label}
                  className={`w-7 h-7 rounded-full ${c.dot} transition-all ${
                    form.color === c.value ? `ring-2 ring-offset-2 ${c.ring} scale-110` : 'hover:scale-105'
                  }`}
                />
              ))}
            </div>
          </div>

          {/* Visibilité : public (tout le monde) ou privé (sur invitation) */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Visibilité</label>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button" onClick={() => setIsPublic(true)}
                className={`flex items-center justify-center gap-2 py-2.5 rounded-lg text-sm font-medium border transition-colors ${
                  isPublic ? 'bg-primary-light text-white border-primary-light' : 'bg-white text-gray-600 border-gray-200 hover:bg-gray-50'
                }`}
              >
                <Globe size={15} /> Public
              </button>
              <button
                type="button" onClick={() => setIsPublic(false)}
                className={`flex items-center justify-center gap-2 py-2.5 rounded-lg text-sm font-medium border transition-colors ${
                  !isPublic ? 'bg-primary-light text-white border-primary-light' : 'bg-white text-gray-600 border-gray-200 hover:bg-gray-50'
                }`}
              >
                <Lock size={15} /> Privé
              </button>
            </div>
            <p className="mt-1.5 text-xs text-gray-400">
              {isPublic
                ? 'Visible par tous et inclus dans la feuille mensuelle.'
                : 'Visible uniquement par les personnes invitées.'}
            </p>
          </div>

          {/* Invitations (uniquement pour un événement privé) */}
          {!isPublic && users.length > 0 && (
            <InviteePicker
              users={users} excludeId={currentUserId}
              selected={invitees} onChange={setInvitees}
              all={inviteAll} onToggleAll={setInviteAll}
            />
          )}
          {isEdit && (
            <InvitationResponses targetType="event" targetId={event.id} users={users} />
          )}

          {/* Actions */}
          <div className="flex gap-3 pt-1">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 border border-gray-200 text-gray-600 hover:bg-gray-50 font-medium py-2.5 rounded-xl text-sm transition-colors"
            >
              Annuler
            </button>
            <button
              type="submit"
              className="flex-1 bg-primary-light hover:bg-primary text-white font-medium py-2.5 rounded-xl text-sm transition-colors"
            >
              {isEdit ? 'Enregistrer' : "Créer l'événement"}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
