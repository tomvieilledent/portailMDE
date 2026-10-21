import React, { useState } from 'react'
import { X, CalendarClock, Calendar, Users, MapPin, Link as LinkIcon, Save, GraduationCap, Loader2, Globe, Lock } from 'lucide-react'
import InviteePicker from '../InviteePicker'

// Programmation d'une session de formation (réservée au super admin) : c'est
// ici que l'on choisit une formation existante, ses dates, sa jauge et les
// personnes à inviter (RSVP interne).
export default function SessionFormModal({ trainings = [], users = [], currentUserId = null, onClose, onSave }) {
  // Le catalogue mélange formations et ateliers : on les sépare pour les
  // présenter dans deux groupes distincts du menu déroulant.
  const formations = trainings.filter((t) => (t.type || 'formation') !== 'atelier')
  const ateliers = trainings.filter((t) => t.type === 'atelier')

  const [form, setForm] = useState({
    training_id: trainings[0]?.id || '',
    start_date: '',
    end_date: '',
    max_participants: 15,
    location: '',
    link: '',
  })
  const [isPublic, setIsPublic] = useState(false)
  const [inviteAll, setInviteAll] = useState(false)
  const [invitees, setInvitees] = useState([])
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  const set = (field) => (e) => setForm((prev) => ({ ...prev, [field]: e.target.value }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    if (!form.training_id) { setError('Choisissez une formation'); return }
    if (!form.start_date || !form.end_date) { setError('Renseignez les dates de début et de fin'); return }
    if (new Date(form.end_date) < new Date(form.start_date)) {
      setError('La date de fin doit être postérieure au début'); return
    }
    setSubmitting(true)
    try {
      // datetime-local n'a pas de secondes : le backend attend un format ISO
      // avec secondes → on complète avec ':00'.
      await onSave(form.training_id, {
        start_date: `${form.start_date}:00`,
        end_date: `${form.end_date}:00`,
        max_participants: Number(form.max_participants),
        location: form.location.trim() || null,
        link: form.link.trim() || null,
        is_public: isPublic,
      }, { inviteAll: isPublic ? false : inviteAll,
           inviteeIds: isPublic ? [] : invitees })
      onClose()
    } catch (err) {
      setError(err?.message || 'Échec de la programmation')
      setSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4" onClick={onClose}>
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg overflow-hidden" onClick={(e) => e.stopPropagation()}>
        <div className="bg-purple-500 px-6 py-5 flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 bg-white/20 rounded-xl flex items-center justify-center">
              <CalendarClock size={20} className="text-white" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white">Programmer une formation / un atelier</h2>
              <p className="text-sm text-white/80">Dates et jauge d'inscrits</p>
            </div>
          </div>
          <button onClick={onClose} className="text-white/70 hover:text-white transition-colors mt-0.5">
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="px-6 py-6 space-y-4 max-h-[75vh] overflow-y-auto">
          {/* Formation / Atelier — regroupés par type pour les distinguer */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              <span className="flex items-center gap-1"><GraduationCap size={13} /> Formation / Atelier *</span>
            </label>
            {trainings.length === 0 ? (
              <p className="text-sm text-gray-400 bg-gray-50 border border-gray-100 rounded-lg px-3 py-2">
                Aucune formation ou atelier au catalogue. Créez-en d'abord un.
              </p>
            ) : (
              <select
                value={form.training_id}
                onChange={set('training_id')}
                className="w-full px-4 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-400 bg-white"
              >
                {formations.length > 0 && (
                  <optgroup label="Formations">
                    {formations.map((t) => <option key={t.id} value={t.id}>{t.title}</option>)}
                  </optgroup>
                )}
                {ateliers.length > 0 && (
                  <optgroup label="Ateliers">
                    {ateliers.map((t) => <option key={t.id} value={t.id}>{t.title}</option>)}
                  </optgroup>
                )}
              </select>
            )}
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                <span className="flex items-center gap-1"><Calendar size={13} /> Début *</span>
              </label>
              <input type="datetime-local" required value={form.start_date} onChange={set('start_date')}
                className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-400" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                <span className="flex items-center gap-1"><Calendar size={13} /> Fin *</span>
              </label>
              <input type="datetime-local" required value={form.end_date} onChange={set('end_date')}
                className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-400" />
            </div>
          </div>

          {/* Jauge */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              <span className="flex items-center gap-1"><Users size={13} /> Jauge (places) *</span>
            </label>
            <input type="number" min={1} required value={form.max_participants} onChange={set('max_participants')}
              className="w-full px-4 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-400" />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              <span className="flex items-center gap-1"><MapPin size={13} /> Lieu</span>
            </label>
            <input type="text" placeholder="Ex : Salle B, MDE Rodez" value={form.location} onChange={set('location')}
              className="w-full px-4 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-400" />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              <span className="flex items-center gap-1"><LinkIcon size={13} /> Lien (visio)</span>
            </label>
            <input type="url" placeholder="https://…" value={form.link} onChange={set('link')}
              className="w-full px-4 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-400" />
          </div>

          {/* Visibilité : publique (tout le monde) ou privée (sur invitation) */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Visibilité</label>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button" onClick={() => setIsPublic(true)}
                className={`flex items-center justify-center gap-2 py-2.5 rounded-lg text-sm font-medium border transition-colors ${
                  isPublic ? 'bg-purple-500 text-white border-purple-500' : 'bg-white text-gray-600 border-gray-200 hover:bg-gray-50'
                }`}
              >
                <Globe size={15} /> Publique
              </button>
              <button
                type="button" onClick={() => setIsPublic(false)}
                className={`flex items-center justify-center gap-2 py-2.5 rounded-lg text-sm font-medium border transition-colors ${
                  !isPublic ? 'bg-purple-500 text-white border-purple-500' : 'bg-white text-gray-600 border-gray-200 hover:bg-gray-50'
                }`}
              >
                <Lock size={15} /> Privée
              </button>
            </div>
            <p className="mt-1.5 text-xs text-gray-400">
              {isPublic
                ? 'Visible par tous et incluse dans la feuille mensuelle.'
                : 'Visible uniquement par les personnes invitées.'}
            </p>
          </div>

          {/* Invitations (RSVP interne) — uniquement pour une session privée */}
          {!isPublic && users.length > 0 && (
            <InviteePicker
              users={users} excludeId={currentUserId}
              selected={invitees} onChange={setInvitees}
              all={inviteAll} onToggleAll={setInviteAll}
            />
          )}

          {error && (
            <p className="text-sm text-red-500 bg-red-50 border border-red-200 rounded-lg px-3 py-2">{error}</p>
          )}

          <div className="flex gap-3 pt-1">
            <button type="button" onClick={onClose}
              className="flex-1 border border-gray-200 text-gray-600 hover:bg-gray-50 font-semibold py-2.5 rounded-xl transition-colors text-sm">
              Annuler
            </button>
            <button type="submit" disabled={submitting || trainings.length === 0}
              className="flex-1 bg-purple-500 hover:bg-purple-600 disabled:opacity-50 text-white font-semibold py-2.5 rounded-xl transition-colors flex items-center justify-center gap-2 text-sm">
              {submitting ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />}
              Programmer
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
