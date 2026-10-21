import React, { useState } from 'react'
import { X, Lock, KeyRound, CheckCircle2, Send, Loader2, Eye, EyeOff } from 'lucide-react'
import { api } from '../../lib/api'

export default function ResetPasswordModal({ token, onDone }) {
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [show, setShow] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [done, setDone] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (loading) return
    if (password.length < 8) {
      setError('Le mot de passe doit contenir au moins 8 caractères.')
      return
    }
    if (password !== confirm) {
      setError('Les deux mots de passe ne correspondent pas.')
      return
    }
    setLoading(true)
    setError('')
    try {
      await api.resetPassword(token, password)
      setDone(true)
    } catch (err) {
      setError(err?.message || 'Lien invalide ou expiré. Refaites une demande.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 z-[60] bg-black/50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md overflow-hidden" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="bg-primary-light px-6 py-5 flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 bg-white/20 rounded-xl flex items-center justify-center">
              <KeyRound size={20} className="text-white" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white">Nouveau mot de passe</h2>
              <p className="text-sm text-white/80">Définissez votre nouveau mot de passe</p>
            </div>
          </div>
          <button onClick={onDone} className="text-white/70 hover:text-white transition-colors mt-0.5">
            <X size={20} />
          </button>
        </div>

        {!done ? (
          <form onSubmit={handleSubmit} className="px-6 py-6 space-y-5">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Nouveau mot de passe</label>
              <div className="relative">
                <Lock size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                <input
                  type={show ? 'text' : 'password'}
                  required autoFocus placeholder="Au moins 8 caractères"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full pl-10 pr-10 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-light"
                />
                <button
                  type="button" onClick={() => setShow((s) => !s)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  {show ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Confirmer le mot de passe</label>
              <div className="relative">
                <Lock size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                <input
                  type={show ? 'text' : 'password'}
                  required placeholder="Retapez le mot de passe"
                  value={confirm}
                  onChange={(e) => setConfirm(e.target.value)}
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
              {loading ? 'Enregistrement…' : 'Réinitialiser mon mot de passe'}
            </button>
          </form>
        ) : (
          <div className="px-6 py-8 flex flex-col items-center text-center space-y-4">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center">
              <CheckCircle2 size={36} className="text-primary" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-gray-900">Mot de passe mis à jour !</h3>
              <p className="text-sm text-gray-500 mt-1">
                Vous pouvez désormais vous connecter avec votre nouveau mot de passe.
              </p>
            </div>
            <button
              onClick={onDone}
              className="w-full bg-primary-light hover:bg-primary text-white font-semibold py-2.5 rounded-xl transition-colors text-sm mt-2"
            >
              Retour à la connexion
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
