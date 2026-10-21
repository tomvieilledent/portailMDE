import React, { useState } from 'react'
import { X, ShieldCheck, Shield, Mail, User, Lock, Loader2, Save, Building2, Users, GraduationCap, TrendingUp } from 'lucide-react'
import { api } from '../../lib/api'

// Métadonnées des droits « staff » assignables (doivent rester alignées avec
// backend/models/user.py:STAFF_PERMISSIONS).
export const PERMISSION_META = {
  manage_companies: {
    label: 'Entreprises',
    desc: 'Créer, modifier et désactiver les entreprises hébergées et formateurs.',
    icon: Building2,
  },
  manage_users: {
    label: 'Comptes',
    desc: 'Créer, désactiver, réactiver et supprimer des comptes utilisateurs.',
    icon: Users,
  },
  manage_trainings: {
    label: 'Formations & agenda',
    desc: 'Gérer formations, ateliers, sessions et événements de l’agenda.',
    icon: GraduationCap,
  },
  manage_news: {
    label: 'Veille & accueil',
    desc: 'Publier la veille économique et éditer la page d’accueil publique.',
    icon: TrendingUp,
  },
}

export const ALL_PERMISSIONS = Object.keys(PERMISSION_META)

// Création d'un compte « plateforme » par un super admin :
//   - type 'staff'      : compte staff avec un sous-ensemble de droits.
//   - type 'superadmin' : super administrateur (tous les droits).
export default function StaffAccountModal({ onClose, onSuccess }) {
  const [type, setType] = useState('staff')
  const [form, setForm] = useState({
    first_name: '', last_name: '', email: '', password: '', confirm: '',
  })
  const [perms, setPerms] = useState(() => new Set())
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  const set = (field) => (e) => setForm((prev) => ({ ...prev, [field]: e.target.value }))
  const togglePerm = (key) => setPerms((prev) => {
    const next = new Set(prev)
    next.has(key) ? next.delete(key) : next.add(key)
    return next
  })

  const isStaff = type === 'staff'

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    if (form.password !== form.confirm) { setError('Les mots de passe ne correspondent pas'); return }
    if (isStaff && perms.size === 0) { setError('Sélectionnez au moins un droit'); return }
    setSubmitting(true)
    try {
      const payload = {
        email: form.email.trim(),
        password: form.password,
        first_name: form.first_name.trim() || null,
        last_name: form.last_name.trim() || null,
      }
      if (isStaff) {
        payload.is_staff = true
        payload.permissions = Array.from(perms)
      } else {
        payload.is_super_admin = true
      }
      const res = await api.createUser(payload)
      onSuccess?.(res?.user || res)
      onClose()
    } catch (err) {
      setError(err?.message || 'Échec de la création du compte')
      setSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4" onClick={onClose}>
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg overflow-hidden max-h-[92vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>

        <div className="bg-purple-600 px-6 py-5 flex items-start justify-between sticky top-0">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 bg-white/20 rounded-xl flex items-center justify-center">
              <ShieldCheck size={20} className="text-white" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white">Nouveau compte d'administration</h2>
              <p className="text-sm text-white/80">Super Admin ou membre du staff avec droits</p>
            </div>
          </div>
          <button onClick={onClose} className="text-white/70 hover:text-white transition-colors mt-0.5">
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="px-6 py-6 space-y-4">
          {/* Type de compte */}
          <div className="grid grid-cols-2 gap-3">
            <button type="button" onClick={() => setType('staff')}
              className={`flex items-start gap-2 p-3 rounded-xl border text-left transition-colors ${isStaff ? 'border-purple-400 bg-purple-50' : 'border-gray-200 hover:bg-gray-50'}`}>
              <Shield size={18} className={isStaff ? 'text-purple-600 mt-0.5' : 'text-gray-400 mt-0.5'} />
              <div>
                <p className="text-sm font-semibold text-gray-900">Staff</p>
                <p className="text-xs text-gray-500">Droits ciblés</p>
              </div>
            </button>
            <button type="button" onClick={() => setType('superadmin')}
              className={`flex items-start gap-2 p-3 rounded-xl border text-left transition-colors ${!isStaff ? 'border-purple-400 bg-purple-50' : 'border-gray-200 hover:bg-gray-50'}`}>
              <ShieldCheck size={18} className={!isStaff ? 'text-purple-600 mt-0.5' : 'text-gray-400 mt-0.5'} />
              <div>
                <p className="text-sm font-semibold text-gray-900">Super Admin</p>
                <p className="text-xs text-gray-500">Accès complet</p>
              </div>
            </button>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="flex items-center gap-1.5 text-sm font-medium text-gray-700 mb-1.5">
                <User size={13} className="text-gray-400" /> Prénom
              </label>
              <input type="text" placeholder="Prénom" value={form.first_name} onChange={set('first_name')}
                className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500" />
            </div>
            <div>
              <label className="flex items-center gap-1.5 text-sm font-medium text-gray-700 mb-1.5">
                <User size={13} className="text-gray-400" /> Nom
              </label>
              <input type="text" placeholder="Nom" value={form.last_name} onChange={set('last_name')}
                className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500" />
            </div>
          </div>

          <div>
            <label className="flex items-center gap-1.5 text-sm font-medium text-gray-700 mb-1.5">
              <Mail size={13} className="text-gray-400" /> Adresse email *
            </label>
            <input required type="email" placeholder="prenom.nom@mde.fr" value={form.email} onChange={set('email')}
              className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500" />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="flex items-center gap-1.5 text-sm font-medium text-gray-700 mb-1.5">
                <Lock size={13} className="text-gray-400" /> Mot de passe *
              </label>
              <input required type="password" minLength={8} placeholder="8 caractères min." value={form.password} onChange={set('password')}
                className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500" />
            </div>
            <div>
              <label className="flex items-center gap-1.5 text-sm font-medium text-gray-700 mb-1.5">
                <Lock size={13} className="text-gray-400" /> Confirmer *
              </label>
              <input required type="password" minLength={8} placeholder="Retapez" value={form.confirm} onChange={set('confirm')}
                className={`w-full px-3 py-2.5 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 ${form.confirm && form.confirm !== form.password ? 'border-red-300 bg-red-50' : 'border-gray-200'}`} />
            </div>
          </div>

          {/* Droits (staff uniquement) */}
          {isStaff ? (
            <div>
              <p className="text-sm font-medium text-gray-700 mb-2">Droits attribués *</p>
              <div className="space-y-2">
                {ALL_PERMISSIONS.map((key) => {
                  const meta = PERMISSION_META[key]
                  const Icon = meta.icon
                  const checked = perms.has(key)
                  return (
                    <label key={key}
                      className={`flex items-start gap-3 p-3 rounded-xl border cursor-pointer transition-colors ${checked ? 'border-purple-300 bg-purple-50/60' : 'border-gray-100 hover:bg-gray-50'}`}>
                      <input type="checkbox" checked={checked} onChange={() => togglePerm(key)}
                        className="mt-0.5 w-4 h-4 accent-purple-600 flex-shrink-0" />
                      <Icon size={16} className="text-purple-600 mt-0.5 flex-shrink-0" />
                      <div>
                        <p className="text-sm font-semibold text-gray-900">{meta.label}</p>
                        <p className="text-xs text-gray-500">{meta.desc}</p>
                      </div>
                    </label>
                  )
                })}
              </div>
            </div>
          ) : (
            <p className="text-xs text-gray-500 bg-purple-50 border border-purple-100 rounded-lg px-3 py-2">
              Un Super Admin dispose de tous les droits, y compris la création d'autres administrateurs.
            </p>
          )}

          {error && (
            <p className="text-sm text-red-500 bg-red-50 border border-red-200 rounded-lg px-3 py-2">{error}</p>
          )}

          <div className="flex gap-3 pt-1">
            <button type="button" onClick={onClose}
              className="flex-1 border border-gray-200 text-gray-600 hover:bg-gray-50 font-medium py-2.5 rounded-xl text-sm transition-colors">
              Annuler
            </button>
            <button type="submit" disabled={submitting}
              className="flex-1 bg-purple-600 hover:bg-purple-700 text-white font-medium py-2.5 rounded-xl text-sm transition-colors flex items-center justify-center gap-2 disabled:opacity-50">
              {submitting ? <Loader2 size={15} className="animate-spin" /> : <Save size={15} />}
              Créer le compte
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
