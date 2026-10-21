import React, { useState } from 'react'
import { X, GraduationCap, User, Mail, Building2, CheckCircle } from 'lucide-react'

export default function TrainingModal({ training, onClose }) {
  const [form, setForm] = useState({ name: '', email: '', company: '', message: '' })
  const [submitted, setSubmitted] = useState(false)

  const set = (field) => (e) => setForm((prev) => ({ ...prev, [field]: e.target.value }))

  const handleSubmit = (e) => {
    e.preventDefault()
    setSubmitted(true)
  }

  return (
    <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4" onClick={onClose}>
      <div
        className="bg-white rounded-2xl shadow-2xl w-full max-w-md overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="bg-primary-light px-6 py-5 flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 bg-white/20 rounded-xl flex items-center justify-center">
              <GraduationCap size={20} className="text-white" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white">S'inscrire à la formation</h2>
              <p className="text-sm text-white/80 truncate max-w-[220px]">{training?.title}</p>
            </div>
          </div>
          <button onClick={onClose} className="text-white/70 hover:text-white transition-colors mt-0.5">
            <X size={20} />
          </button>
        </div>

        {submitted ? (
          /* Confirmation */
          <div className="px-6 py-10 flex flex-col items-center text-center">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mb-4">
              <CheckCircle size={36} className="text-primary-light" />
            </div>
            <h3 className="text-lg font-bold text-gray-900 mb-2">Inscription confirmée !</h3>
            <p className="text-sm text-gray-500 mb-2">
              Vous êtes inscrit(e) à la formation
            </p>
            <p className="text-base font-semibold text-primary-light mb-6">{training?.title}</p>
            <p className="text-sm text-gray-500 mb-6">
              Un email de confirmation vous sera envoyé à <strong>{form.email}</strong>
            </p>
            <button
              onClick={onClose}
              className="px-8 py-2.5 bg-primary-light hover:bg-primary text-white font-semibold rounded-xl transition-colors"
            >
              Fermer
            </button>
          </div>
        ) : (
          /* Formulaire */
          <form onSubmit={handleSubmit} className="px-6 py-6 space-y-4">
            {/* Récap formation */}
            <div className="bg-gray-50 rounded-xl p-4 flex items-center gap-3 border border-gray-100">
              <div className="w-10 h-10 bg-primary-light rounded-xl flex items-center justify-center flex-shrink-0">
                <GraduationCap size={18} className="text-white" />
              </div>
              <div>
                <p className="font-semibold text-gray-900 text-sm">{training?.title}</p>
                <div className="flex gap-3 mt-0.5 text-xs text-gray-500">
                  {training?.duration && <span>⏱ {training.duration}</span>}
                  {training?.endDate && <span>📅 Jusqu'au {training.endDate}</span>}
                </div>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                <span className="flex items-center gap-1"><User size={13} /> Nom complet *</span>
              </label>
              <input
                required
                type="text"
                placeholder="Jean Dupont"
                value={form.name}
                onChange={set('name')}
                className="w-full px-4 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-light"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                <span className="flex items-center gap-1"><Mail size={13} /> Email *</span>
              </label>
              <input
                required
                type="email"
                placeholder="jean.dupont@exemple.fr"
                value={form.email}
                onChange={set('email')}
                className="w-full px-4 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-light"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                <span className="flex items-center gap-1"><Building2 size={13} /> Entreprise</span>
              </label>
              <input
                type="text"
                placeholder="Nom de votre entreprise"
                value={form.company}
                onChange={set('company')}
                className="w-full px-4 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-light"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Message (optionnel)</label>
              <textarea
                rows={3}
                placeholder="Questions ou commentaires sur cette formation…"
                value={form.message}
                onChange={set('message')}
                className="w-full px-4 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-light resize-none"
              />
            </div>

            <div className="flex gap-3 pt-1">
              <button
                type="button"
                onClick={onClose}
                className="flex-1 border border-gray-200 text-gray-600 hover:bg-gray-50 font-semibold py-2.5 rounded-xl transition-colors text-sm"
              >
                Annuler
              </button>
              <button
                type="submit"
                className="flex-1 bg-primary-light hover:bg-primary text-white font-semibold py-2.5 rounded-xl transition-colors flex items-center justify-center gap-2 text-sm"
              >
                <GraduationCap size={16} />
                Valider l'inscription
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  )
}
