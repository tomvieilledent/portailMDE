import React, { useState, useRef } from 'react'
import { X, Camera, User, Mail, Phone, Upload, Trash2, Save, Shield, CreditCard, Briefcase, Lock, Loader2 } from 'lucide-react'

const ROLE_LABELS = { admin: 'Super Administrateur', patron: 'Patron', salarie: 'Salarié' }
const ROLE_COLORS = { admin: 'bg-primary-light/10 text-primary-light', patron: 'bg-purple-100 text-purple-600', salarie: 'bg-gray-100 text-gray-600' }

export default function ProfileModal({ profile, onClose, onSave, onDeactivate }) {
  const [form, setForm] = useState({
    firstName:    profile.firstName    || '',
    lastName:     profile.lastName     || '',
    jobTitle:     profile.jobTitle     || '',
    email:        profile.email        || '',
    phone:        profile.phone        || '',
    photo:        profile.photo        || null,
    businessCard: profile.businessCard || null,
    password:     '',
    confirm:      '',
  })
  // Fichiers réels à téléverser (null = inchangé).
  const [photoFile, setPhotoFile] = useState(null)
  const [cardFile, setCardFile]   = useState(null)
  const [dragOver, setDragOver] = useState(false)
  const [deactivateConfirm, setDeactivateConfirm] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [deactivating, setDeactivating] = useState(false)
  const [error, setError] = useState('')

  const photoRef = useRef()
  const cardRef  = useRef()

  const set = (field) => (e) => setForm((prev) => ({ ...prev, [field]: e.target.value }))

  const handlePhotoChange = (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    setPhotoFile(file)
    setForm((prev) => ({ ...prev, photo: URL.createObjectURL(file) }))
  }

  const handleCardChange = (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    setCardFile(file)
    setForm((prev) => ({ ...prev, businessCard: URL.createObjectURL(file) }))
    e.target.value = ''
  }

  const handleCardDrop = (e) => {
    e.preventDefault()
    setDragOver(false)
    const file = e.dataTransfer.files?.[0]
    if (!file || !file.type.startsWith('image/')) return
    setCardFile(file)
    setForm((prev) => ({ ...prev, businessCard: URL.createObjectURL(file) }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    // Validation du changement de mot de passe (optionnel).
    if (form.password || form.confirm) {
      if (form.password.length < 8) { setError('Le mot de passe doit faire au moins 8 caractères'); return }
      if (form.password !== form.confirm) { setError('Les mots de passe ne correspondent pas'); return }
    }
    setSubmitting(true)
    try {
      // Le backend stocke first_name / last_name / job_title / phone /
      // profile_picture / business_card (+ password en self-service).
      const fd = new FormData()
      fd.append('first_name', form.firstName.trim())
      fd.append('last_name', form.lastName.trim())
      fd.append('job_title', form.jobTitle.trim())
      fd.append('phone', form.phone || '')
      if (form.password) fd.append('password', form.password)
      if (photoFile) fd.append('profile_picture_file', photoFile)
      if (cardFile) fd.append('business_card_file', cardFile)
      await onSave?.(fd)
      onClose()
    } catch (err) {
      setError(err.message || "Échec de l'enregistrement")
    } finally {
      setSubmitting(false)
    }
  }

  const handleDeactivate = async () => {
    setError('')
    setDeactivating(true)
    try {
      await onDeactivate?.()
    } catch (err) {
      setError(err.message || 'Échec de la désactivation')
      setDeactivating(false)
    }
  }

  const fullName = [form.firstName, form.lastName].filter(Boolean).join(' ')
  const initials = fullName
    ? fullName.split(' ').map((n) => n[0]).join('').slice(0, 2).toUpperCase()
    : '?'

  return (
    <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4" onClick={onClose}>
      <div
        className="bg-white rounded-2xl shadow-2xl w-full max-w-lg overflow-hidden max-h-[90vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="bg-primary-light px-6 py-5 flex items-start justify-between flex-shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 bg-white/20 rounded-xl flex items-center justify-center">
              <User size={20} className="text-white" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white">Mon profil</h2>
              <p className="text-sm text-white/80">Modifier vos informations personnelles</p>
            </div>
          </div>
          <button onClick={onClose} className="text-white/70 hover:text-white transition-colors mt-0.5">
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="overflow-y-auto flex-1">
          <div className="px-6 py-6 space-y-5">

            {/* Avatar + rôle */}
            <div className="flex items-center gap-4">
              <div className="relative flex-shrink-0">
                {form.photo ? (
                  <img src={form.photo} alt="avatar" className="w-20 h-20 rounded-full object-cover border-4 border-white shadow-md" />
                ) : (
                  <div className="w-20 h-20 rounded-full bg-primary-light flex items-center justify-center text-white font-bold text-xl border-4 border-white shadow-md">
                    {initials}
                  </div>
                )}
                <button
                  type="button"
                  onClick={() => photoRef.current.click()}
                  className="absolute bottom-0 right-0 w-7 h-7 bg-white border-2 border-gray-200 rounded-full flex items-center justify-center shadow hover:bg-gray-50 transition-colors"
                  title="Changer la photo"
                >
                  <Camera size={13} className="text-gray-600" />
                </button>
                <input ref={photoRef} type="file" accept="image/*" className="hidden" onChange={handlePhotoChange} />
              </div>
              <div>
                <p className="font-bold text-gray-900 text-base">{fullName || 'Votre nom'}</p>
                <span className={`inline-flex items-center gap-1 mt-1 px-2.5 py-0.5 rounded-full text-xs font-semibold ${ROLE_COLORS[profile.role] || 'bg-gray-100 text-gray-600'}`}>
                  <Shield size={10} /> {ROLE_LABELS[profile.role] || profile.role}
                </span>
              </div>
            </div>

            {/* Prénom + Nom */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="flex items-center gap-1.5 text-sm font-medium text-gray-700 mb-1.5">
                  <User size={13} className="text-gray-400" /> Prénom
                </label>
                <input type="text" placeholder="Prénom" value={form.firstName} onChange={set('firstName')}
                  className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-light" />
              </div>
              <div>
                <label className="flex items-center gap-1.5 text-sm font-medium text-gray-700 mb-1.5">
                  <User size={13} className="text-gray-400" /> Nom
                </label>
                <input type="text" placeholder="Nom" value={form.lastName} onChange={set('lastName')}
                  className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-light" />
              </div>
            </div>

            {/* Poste / rôle dans l'entreprise */}
            <div>
              <label className="flex items-center gap-1.5 text-sm font-medium text-gray-700 mb-1.5">
                <Briefcase size={13} className="text-gray-400" /> Poste dans l'entreprise <span className="text-gray-400 font-normal">(optionnel)</span>
              </label>
              <input type="text" placeholder="ex : Gérant, Directrice Commerciale…" value={form.jobTitle} onChange={set('jobTitle')}
                className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-light" />
            </div>

            {/* Email (non modifiable : sert d'identifiant de connexion) */}
            <div>
              <label className="flex items-center gap-1.5 text-sm font-medium text-gray-700 mb-1.5">
                <Mail size={13} className="text-gray-400" /> Email
              </label>
              <input type="email" value={form.email} disabled readOnly
                className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm bg-gray-50 text-gray-500 cursor-not-allowed" />
              <p className="mt-1 text-xs text-gray-400">L'email de connexion ne peut pas être modifié ici.</p>
            </div>

            {/* Téléphone */}
            <div>
              <label className="flex items-center gap-1.5 text-sm font-medium text-gray-700 mb-1.5">
                <Phone size={13} className="text-gray-400" /> Téléphone
              </label>
              <input type="tel" placeholder="+33 6 00 00 00 00" value={form.phone} onChange={set('phone')}
                className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-light" />
            </div>

            {/* Carte de visite */}
            <div>
              <label className="flex items-center gap-1.5 text-sm font-medium text-gray-700 mb-2">
                <CreditCard size={13} className="text-gray-400" /> Carte de visite <span className="text-gray-400 font-normal">(optionnel)</span>
              </label>

              {form.businessCard ? (
                <div className="relative border border-gray-200 rounded-xl overflow-hidden bg-gray-50">
                  <img
                    src={form.businessCard}
                    alt="Carte de visite"
                    className="w-full max-h-40 object-contain py-3"
                  />
                  <div className="absolute top-2 right-2 flex gap-1.5">
                    <button
                      type="button"
                      onClick={() => cardRef.current.click()}
                      className="flex items-center gap-1 bg-white/90 hover:bg-white text-gray-600 text-xs font-medium px-2.5 py-1.5 rounded-lg shadow-sm border border-gray-200 transition-colors"
                    >
                      <Upload size={11} /> Remplacer
                    </button>
                    <button
                      type="button"
                      onClick={() => setForm((prev) => ({ ...prev, businessCard: null }))}
                      className="bg-white/90 hover:bg-red-50 text-gray-400 hover:text-red-500 p-1.5 rounded-lg shadow-sm border border-gray-200 transition-colors"
                    >
                      <Trash2 size={13} />
                    </button>
                  </div>
                  <p className="text-xs text-gray-400 text-center pb-2">Visible sur votre fiche du Trombinoscope</p>
                </div>
              ) : (
                <div
                  onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
                  onDragLeave={() => setDragOver(false)}
                  onDrop={handleCardDrop}
                  onClick={() => cardRef.current.click()}
                  className={`border-2 border-dashed rounded-xl px-4 py-5 text-center cursor-pointer transition-colors ${
                    dragOver ? 'border-primary-light bg-primary-light/5' : 'border-gray-200 hover:border-primary-light hover:bg-gray-50'
                  }`}
                >
                  <CreditCard size={20} className="mx-auto mb-1.5 text-gray-300" />
                  <p className="text-sm text-gray-500">Glissez votre carte ici ou <span className="text-primary-light font-medium">parcourir</span></p>
                  <p className="text-xs text-gray-400 mt-0.5">Image de votre carte de visite (JPG, PNG…)</p>
                </div>
              )}
              <input ref={cardRef} type="file" accept="image/*" className="hidden" onChange={handleCardChange} />
            </div>

            {/* Changement de mot de passe */}
            <div className="border-t border-gray-100 pt-5">
              <p className="flex items-center gap-1.5 text-sm font-medium text-gray-700 mb-3">
                <Lock size={13} className="text-gray-400" /> Changer le mot de passe <span className="text-gray-400 font-normal">(optionnel)</span>
              </p>
              <div className="grid grid-cols-2 gap-3">
                <input type="password" placeholder="Nouveau mot de passe" autoComplete="new-password"
                  value={form.password} onChange={set('password')}
                  className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-light" />
                <input type="password" placeholder="Confirmer" autoComplete="new-password"
                  value={form.confirm} onChange={set('confirm')}
                  className={`w-full px-3 py-2.5 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-light ${
                    form.confirm && form.confirm !== form.password ? 'border-red-300 bg-red-50' : 'border-gray-200'
                  }`} />
              </div>
              {form.confirm && form.confirm !== form.password && (
                <p className="mt-1 text-xs text-red-500">Les mots de passe ne correspondent pas</p>
              )}
            </div>
          </div>

          {/* Zone de danger */}
          <div className="mx-6 mb-4 border border-red-200 rounded-xl p-4 bg-red-50">
            <p className="text-xs font-semibold text-red-700 mb-2 uppercase tracking-wide">Zone de danger</p>
            {!deactivateConfirm ? (
              <div className="flex items-center justify-between gap-3">
                <p className="text-xs text-red-600 leading-snug">
                  Désactiver votre compte suspendra votre accès à la plateforme.
                </p>
                <button
                  type="button"
                  onClick={() => setDeactivateConfirm(true)}
                  className="flex-shrink-0 text-xs font-semibold text-red-600 border border-red-300 hover:bg-red-100 px-3 py-1.5 rounded-lg transition-colors"
                >
                  Désactiver
                </button>
              </div>
            ) : (
              <div className="space-y-3">
                <p className="text-xs text-red-700 font-medium">
                  Confirmez-vous la désactivation de votre compte ?
                </p>
                <div className="bg-white border border-red-100 rounded-lg p-3 text-xs text-gray-600 leading-relaxed">
                  Pour une <span className="font-semibold">suppression définitive</span> de votre compte et de vos données, contactez le super administrateur :{' '}
                  <a href="mailto:admin@admin.com" className="text-primary-light font-semibold hover:underline">
                    admin@admin.com
                  </a>
                </div>
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => setDeactivateConfirm(false)}
                    className="flex-1 text-xs border border-gray-200 text-gray-600 hover:bg-gray-50 py-2 rounded-lg transition-colors"
                  >
                    Annuler
                  </button>
                  <button
                    type="button"
                    onClick={handleDeactivate}
                    disabled={deactivating}
                    className="flex-1 text-xs bg-red-500 hover:bg-red-600 disabled:opacity-60 text-white font-semibold py-2 rounded-lg transition-colors flex items-center justify-center gap-1.5"
                  >
                    {deactivating && <Loader2 size={12} className="animate-spin" />}
                    {deactivating ? 'Désactivation…' : 'Confirmer la désactivation'}
                  </button>
                </div>
              </div>
            )}
          </div>

          {error && (
            <div className="mx-6 mb-3 px-3 py-2.5 rounded-lg bg-red-50 border border-red-200 text-sm text-red-600">
              {error}
            </div>
          )}

          {/* Actions */}
          <div className="px-6 pb-6 flex gap-3">
            <button type="button" onClick={onClose} disabled={submitting}
              className="flex-1 border border-gray-200 text-gray-600 hover:bg-gray-50 font-medium py-2.5 rounded-xl text-sm transition-colors disabled:opacity-60">
              Annuler
            </button>
            <button type="submit" disabled={submitting}
              className="flex-1 bg-primary-light hover:bg-primary text-white font-medium py-2.5 rounded-xl text-sm transition-colors flex items-center justify-center gap-2 disabled:opacity-60">
              {submitting ? <Loader2 size={15} className="animate-spin" /> : <Save size={15} />}
              {submitting ? 'Enregistrement…' : 'Enregistrer'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
