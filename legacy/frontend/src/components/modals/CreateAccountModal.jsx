import React, { useState } from 'react'
import { X, UserPlus, Mail, User, Building2, Lock, Loader2, Save } from 'lucide-react'
import { api } from '../../lib/api'

// Création directe d'un compte (pas d'email d'activation pour l'instant).
//  - forRole="patron"  : un super admin crée l'admin d'une entreprise
//    (sélection de l'entreprise + is_company_admin).
//  - forRole="salarie" : un admin d'entreprise crée un salarié de SON
//    entreprise (company_id imposé, pas de sélection).
export default function CreateAccountModal({ forRole, companies = [], companyId = null, onClose, onSuccess }) {
  const isCreatingPatron = forRole === 'patron'
  const activeCompanies = companies.filter((c) => c.is_active !== false)

  const [form, setForm] = useState({
    first_name: '',
    last_name: '',
    email: '',
    password: '',
    confirm: '',
    company_id: isCreatingPatron ? '' : (companyId || ''),
  })
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  const set = (field) => (e) => setForm((prev) => ({ ...prev, [field]: e.target.value }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    if (form.password !== form.confirm) { setError('Les mots de passe ne correspondent pas'); return }
    setSubmitting(true)
    try {
      const payload = {
        email: form.email.trim(),
        password: form.password,
        first_name: form.first_name.trim() || null,
        last_name: form.last_name.trim() || null,
        company_id: form.company_id || null,
      }
      if (isCreatingPatron && form.company_id) payload.is_company_admin = true
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
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md overflow-hidden" onClick={(e) => e.stopPropagation()}>

        {/* Header */}
        <div className={`px-6 py-5 flex items-start justify-between ${isCreatingPatron ? 'bg-primary-light' : 'bg-purple-500'}`}>
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 bg-white/20 rounded-xl flex items-center justify-center">
              <UserPlus size={20} className="text-white" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white">
                {isCreatingPatron ? "Créer un utilisateur" : 'Créer un compte salarié'}
              </h2>
              <p className="text-sm text-white/80">
                {isCreatingPatron ? "Entreprise facultative" : 'Compte actif immédiatement'}
              </p>
            </div>
          </div>
          <button onClick={onClose} className="text-white/70 hover:text-white transition-colors mt-0.5">
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="px-6 py-6 space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="flex items-center gap-1.5 text-sm font-medium text-gray-700 mb-1.5">
                <User size={13} className="text-gray-400" /> Prénom
              </label>
              <input type="text" placeholder="Prénom" value={form.first_name} onChange={set('first_name')}
                className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-light" />
            </div>
            <div>
              <label className="flex items-center gap-1.5 text-sm font-medium text-gray-700 mb-1.5">
                <User size={13} className="text-gray-400" /> Nom
              </label>
              <input type="text" placeholder="Nom" value={form.last_name} onChange={set('last_name')}
                className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-light" />
            </div>
          </div>

          <div>
            <label className="flex items-center gap-1.5 text-sm font-medium text-gray-700 mb-1.5">
              <Mail size={13} className="text-gray-400" /> Adresse email *
            </label>
            <input required type="email" placeholder="prenom.nom@entreprise.fr"
              value={form.email} onChange={set('email')}
              className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-light" />
          </div>

          <div>
            <label className="flex items-center gap-1.5 text-sm font-medium text-gray-700 mb-1.5">
              <Lock size={13} className="text-gray-400" /> Mot de passe *
            </label>
            <input required type="password" minLength={8} placeholder="8 caractères minimum"
              value={form.password} onChange={set('password')}
              className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-light" />
          </div>

          <div>
            <label className="flex items-center gap-1.5 text-sm font-medium text-gray-700 mb-1.5">
              <Lock size={13} className="text-gray-400" /> Confirmer le mot de passe *
            </label>
            <input required type="password" minLength={8} placeholder="Retapez le mot de passe"
              value={form.confirm} onChange={set('confirm')}
              className={`w-full px-3 py-2.5 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-light ${
                form.confirm && form.confirm !== form.password ? 'border-red-300 bg-red-50' : 'border-gray-200'
              }`} />
            {form.confirm && form.confirm !== form.password && (
              <p className="mt-1 text-xs text-red-500">Les mots de passe ne correspondent pas</p>
            )}
          </div>

          {/* Entreprise : sélection (patron) ou imposée (salarié) */}
          {isCreatingPatron && (
            <div>
              <label className="flex items-center gap-1.5 text-sm font-medium text-gray-700 mb-1.5">
                <Building2 size={13} className="text-gray-400" /> Entreprise
              </label>
              <select value={form.company_id} onChange={set('company_id')}
                className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-light bg-white">
                <option value="">Aucune entreprise</option>
                {activeCompanies.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
              <p className="mt-1 text-xs text-gray-400">
                Si une entreprise est choisie, l'utilisateur en devient l'administrateur.
              </p>
            </div>
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
              className={`flex-1 text-white font-medium py-2.5 rounded-xl text-sm transition-colors flex items-center justify-center gap-2 disabled:opacity-50 ${isCreatingPatron ? 'bg-primary-light hover:bg-primary' : 'bg-purple-500 hover:bg-purple-600'}`}>
              {submitting ? <Loader2 size={15} className="animate-spin" /> : <Save size={15} />}
              Créer le compte
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
