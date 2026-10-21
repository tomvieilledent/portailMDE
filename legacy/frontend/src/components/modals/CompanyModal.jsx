import React, { useState, useRef } from 'react'
import { X, Building2, MapPin, Save, Link, Mail, Loader2, ImagePlus, Users } from 'lucide-react'
import { mediaUrl } from '../../lib/api'

export default function CompanyModal({ company, defaultKind = 'company', userEmails = [], members = [], onClose, onSave }) {
  const isEdit = !!company
  const [form, setForm] = useState({
    name:        company?.name        || '',
    admin_email: company?.admin_email || '',
    location:    company?.location    || '',
    url:         company?.url         || company?.website_link || '',
    description: company?.description || '',
    kind:        company?.kind        || defaultKind,
  })
  const isTrainer = form.kind === 'trainer'
  const [logoFile, setLogoFile]   = useState(null)
  const [logoPreview, setLogoPreview] = useState(mediaUrl(company?.company_picture) || null)
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const fileRef = useRef(null)

  const set = (field) => (e) => setForm((prev) => ({ ...prev, [field]: e.target.value }))

  const handleLogo = (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    setLogoFile(file)
    setLogoPreview(URL.createObjectURL(file))
    e.target.value = ''
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setSubmitting(true)
    try {
      await onSave?.({ ...company, ...form, id: company?.id, logoFile })
      onClose()
    } catch (err) {
      setError(err.message || "Échec de l'enregistrement")
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4" onClick={onClose}>
      <div
        className="bg-white rounded-2xl shadow-2xl w-full max-w-lg overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="bg-primary-light px-6 py-5 flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 bg-white/20 rounded-xl flex items-center justify-center">
              <Building2 size={20} className="text-white" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white">
                {isEdit ? 'Modifier la fiche'
                        : (isTrainer ? 'Ajouter un formateur' : 'Ajouter une entreprise')}
              </h2>
              <p className="text-sm text-white/80">
                {isEdit ? company.name : 'Nouvelle entreprise dans la pépinière'}
              </p>
            </div>
          </div>
          <button onClick={onClose} className="text-white/70 hover:text-white transition-colors mt-0.5">
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="px-6 py-6 space-y-4 max-h-[75vh] overflow-y-auto">
          {error && (
            <div className="px-3 py-2.5 rounded-lg bg-red-50 border border-red-200 text-sm text-red-600">
              {error}
            </div>
          )}

          {/* Type de fiche : entreprise hébergée ou formateur */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">Type</label>
            <div className="grid grid-cols-2 gap-2">
              {[['company', 'Entreprise'], ['trainer', 'Formateur']].map(([value, label]) => (
                <button
                  key={value}
                  type="button"
                  onClick={() => setForm((prev) => ({ ...prev, kind: value }))}
                  className={`px-4 py-2.5 rounded-lg text-sm font-semibold border transition-colors ${
                    form.kind === value
                      ? 'bg-primary-light border-primary-light text-white'
                      : 'bg-white border-gray-200 text-gray-600 hover:bg-gray-50'
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>

          {/* Logo */}
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 rounded-2xl bg-orange-100 flex items-center justify-center overflow-hidden flex-shrink-0">
              {logoPreview ? (
                <img src={logoPreview} alt="logo" className="w-full h-full object-cover" />
              ) : (
                <Building2 size={28} className="text-orange-400" />
              )}
            </div>
            <div>
              <button type="button" onClick={() => fileRef.current?.click()}
                className="flex items-center gap-1.5 text-sm font-medium text-primary-light hover:text-primary transition-colors">
                <ImagePlus size={15} /> {logoPreview ? 'Changer le logo' : 'Ajouter un logo'}
              </button>
              <p className="text-xs text-gray-400 mt-0.5">PNG/JPG, carré de préférence.</p>
            </div>
            <input ref={fileRef} type="file" accept="image/*" className="hidden" onChange={handleLogo} />
          </div>

          {/* Nom */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">{isTrainer ? 'Nom du formateur *' : "Nom de l'entreprise *"}</label>
            <input required type="text" placeholder={isTrainer ? 'Ex : FormaPro / Jean Dupont' : 'Ex : Tech Innovators'}
              value={form.name} onChange={set('name')}
              className="w-full px-4 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-light" />
          </div>

          {/* Email de l'administrateur (requis par le backend) */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              <span className="flex items-center gap-1"><Mail size={13} /> Email de l'administrateur *</span>
            </label>
            <input required type="email" placeholder="admin@entreprise.fr" list="company-admin-emails"
              value={form.admin_email} onChange={set('admin_email')}
              className="w-full px-4 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-light" />
            <datalist id="company-admin-emails">
              {userEmails.map((email) => <option key={email} value={email} />)}
            </datalist>
            <p className="mt-1 text-xs text-gray-400">Doit correspondre à un utilisateur existant.</p>
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">Description</label>
            <textarea rows={3} placeholder="Activité, spécialité, points forts…"
              value={form.description} onChange={set('description')}
              className="w-full px-4 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-light resize-none" />
          </div>

          {/* Localisation */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              <span className="flex items-center gap-1"><MapPin size={13} /> Localisation</span>
            </label>
            <input type="text" placeholder="Ville"
              value={form.location} onChange={set('location')}
              className="w-full px-4 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-light" />
          </div>

          {/* Site web */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              <span className="flex items-center gap-1"><Link size={13} /> Site web</span>
            </label>
            <input type="text" placeholder="www.exemple.com"
              value={form.url} onChange={set('url')}
              className="w-full px-4 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-light" />
            <p className="mt-1 text-xs text-gray-400">Inutile de saisir « https:// », il est ajouté automatiquement.</p>
          </div>

          {isEdit && typeof company.employee_count === 'number' && (
            <p className="flex items-center gap-1.5 text-xs text-gray-400">
              <Users size={13} /> {company.employee_count} membre{company.employee_count > 1 ? 's' : ''} (calculé automatiquement)
            </p>
          )}

          {/* Membres de l'entreprise + rôles */}
          {members.length > 0 && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <span className="flex items-center gap-1"><Users size={13} /> Membres</span>
              </label>
              <div className="space-y-1.5 max-h-44 overflow-y-auto">
                {members.map((m, i) => (
                  <div key={m.id || i} className="flex items-center gap-2.5 bg-gray-50 border border-gray-100 rounded-lg px-3 py-2">
                    {m.photo && <img src={m.photo} alt={m.name} className="w-7 h-7 rounded-full object-cover flex-shrink-0" />}
                    <span className="text-sm text-gray-800 flex-1 truncate">{m.name}</span>
                    <span className={`px-2 py-0.5 rounded-full text-xs font-semibold flex-shrink-0 ${
                      /admin|responsable/i.test(m.role || '') ? 'bg-purple-100 text-purple-600' : 'bg-gray-200 text-gray-600'
                    }`}>{m.role || 'Membre'}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-3 pt-2">
            <button type="button" onClick={onClose} disabled={submitting}
              className="flex-1 border border-gray-200 text-gray-600 hover:bg-gray-50 font-semibold py-2.5 rounded-xl transition-colors text-sm disabled:opacity-60">
              Annuler
            </button>
            <button type="submit" disabled={submitting}
              className="flex-1 bg-primary-light hover:bg-primary text-white font-semibold py-2.5 rounded-xl transition-colors flex items-center justify-center gap-2 text-sm disabled:opacity-60 disabled:cursor-not-allowed">
              {submitting ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />}
              {submitting ? 'Enregistrement…' : isEdit ? 'Enregistrer' : 'Ajouter'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
