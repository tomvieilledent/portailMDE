import React, { useState } from 'react'
import { X, Mail, KeyRound, ArrowLeft, CheckCircle2, Send, Loader2 } from 'lucide-react'
import { api } from '../../lib/api'

export default function ForgotPasswordModal({ onClose, onBack }) {
  const [email, setEmail] = useState('')
  const [sent, setSent] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!email.trim() || loading) return
    setLoading(true)
    setError('')
    try {
      await api.forgotPassword(email.trim())
      setSent(true)
    } catch (err) {
      setError(err?.message || "Une erreur est survenue. Réessayez plus tard.")
    } finally {
      setLoading(false)
    }
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
              <KeyRound size={20} className="text-white" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white">Mot de passe oublié</h2>
              <p className="text-sm text-white/80">Récupération par email</p>
            </div>
          </div>
          <button onClick={onClose} className="text-white/70 hover:text-white transition-colors mt-0.5">
            <X size={20} />
          </button>
        </div>

        {!sent ? (
          <form onSubmit={handleSubmit} className="px-6 py-6 space-y-5">
            <p className="text-sm text-gray-600">
              Saisissez l'adresse email associée à votre compte. Nous vous enverrons un lien pour réinitialiser votre mot de passe.
            </p>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Adresse email</label>
              <div className="relative">
                <Mail size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                <input
                  type="email"
                  required
                  autoFocus
                  placeholder="votre.email@exemple.fr"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full pl-10 pr-4 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-light"
                />
              </div>
            </div>

            {error && (
              <p className="text-sm text-red-600 bg-red-50 border border-red-100 rounded-lg px-3 py-2">
                {error}
              </p>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-primary-light hover:bg-primary text-white font-semibold py-3 rounded-xl transition-colors flex items-center justify-center gap-2 disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {loading ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
              {loading ? 'Envoi…' : 'Envoyer le lien de récupération'}
            </button>

            <button
              type="button"
              onClick={onBack}
              className="w-full flex items-center justify-center gap-2 text-sm text-gray-500 hover:text-gray-800 transition-colors"
            >
              <ArrowLeft size={15} />
              Retour à la connexion
            </button>
          </form>
        ) : (
          <div className="px-6 py-8 flex flex-col items-center text-center space-y-4">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center">
              <CheckCircle2 size={36} className="text-primary" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-gray-900">Email envoyé !</h3>
              <p className="text-sm text-gray-500 mt-1">
                Un lien de récupération a été envoyé à
              </p>
              <p className="text-sm font-semibold text-gray-800 mt-0.5">{email}</p>
              <p className="text-xs text-gray-400 mt-3">
                Vérifiez vos spams si vous ne le recevez pas sous quelques minutes.
              </p>
            </div>
            <button
              onClick={onBack}
              className="w-full border-2 border-primary-light text-primary-light hover:bg-primary-light hover:text-white font-semibold py-2.5 rounded-xl transition-colors text-sm mt-2"
            >
              Retour à la connexion
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
