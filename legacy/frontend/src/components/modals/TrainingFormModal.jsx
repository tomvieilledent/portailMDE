import React, { useState } from 'react'
import { X, GraduationCap, Save, FileText, Tag, Link, Loader2, Paperclip, Upload, Trash2 } from 'lucide-react'

// Nom lisible d'une pièce jointe à partir de son chemin stocké
// (/uploads/trainings/documents/<uuid>__<nom-original>).
export function docName(path) {
  const base = (path || '').split('/').pop() || ''
  const parts = base.split('__')
  return parts.length > 1 ? parts.slice(1).join('__') : base
}

export default function TrainingFormModal({ training, onClose, onSave, categories = [] }) {
  const isEdit = !!training
  const [form, setForm] = useState({
    title: training?.title || '',
    category: training?.category || '',
    type: training?.type || 'formation',
    description: training?.description || '',
    url: training?.url || '',
  })
  // Pièces jointes : existantes (chemins) marquées pour suppression + nouveaux fichiers.
  const existingDocs = training?.documents || []
  const [removedDocs, setRemovedDocs] = useState([])
  const [docFiles, setDocFiles] = useState([])
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  const set = (field) => (e) => setForm((prev) => ({ ...prev, [field]: e.target.value }))

  const onPickFiles = (e) => {
    const picked = Array.from(e.target.files || [])
    if (picked.length) setDocFiles((prev) => [...prev, ...picked])
    e.target.value = ''
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setSubmitting(true)
    try {
      // Lien sans protocole → on préfixe https:// automatiquement.
      const url = form.url.trim()
        ? (/^https?:\/\//i.test(form.url.trim()) ? form.url.trim() : `https://${form.url.trim()}`)
        : ''
      await onSave({
        ...training, ...form, url, id: training?.id,
        documentFiles: docFiles, removedDocs,
      })
      onClose()
    } catch (err) {
      setError(err?.message || "Échec de l'enregistrement")
      setSubmitting(false)
    }
  }

  const visibleExisting = existingDocs.filter((d) => !removedDocs.includes(d))

  return (
    <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4" onClick={onClose}>
      <div
        className="bg-white rounded-2xl shadow-2xl w-full max-w-lg overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="bg-purple-500 px-6 py-5 flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 bg-white/20 rounded-xl flex items-center justify-center">
              <GraduationCap size={20} className="text-white" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white">
                {isEdit ? 'Modifier' : 'Créer'} {form.type === 'atelier' ? 'un atelier' : 'une formation'}
              </h2>
              <p className="text-sm text-white/80">
                {isEdit ? training.title : 'Nouvelle entrée dans le catalogue'}
              </p>
            </div>
          </div>
          <button onClick={onClose} className="text-white/70 hover:text-white transition-colors mt-0.5">
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="px-6 py-6 space-y-4 max-h-[75vh] overflow-y-auto">
          {/* Titre */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              <span className="flex items-center gap-1"><FileText size={13} /> Titre *</span>
            </label>
            <input
              required
              type="text"
              placeholder="Ex : Marketing Digital 2026"
              value={form.title}
              onChange={set('title')}
              className="w-full px-4 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-400"
            />
          </div>

          {/* Type : formation ou atelier */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">Type</label>
            <div className="grid grid-cols-2 gap-2">
              {[['formation', 'Formation'], ['atelier', 'Atelier']].map(([value, label]) => (
                <button
                  key={value}
                  type="button"
                  onClick={() => setForm((prev) => ({ ...prev, type: value }))}
                  className={`px-4 py-2.5 rounded-lg text-sm font-semibold border transition-colors ${
                    form.type === value
                      ? 'bg-purple-500 border-purple-500 text-white'
                      : 'bg-white border-gray-200 text-gray-600 hover:bg-gray-50'
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>

          {/* Lien */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              <span className="flex items-center gap-1"><Link size={13} /> Lien</span>
            </label>
            <input
              type="text"
              placeholder="www.exemple.com/formation"
              value={form.url}
              onChange={set('url')}
              className="w-full px-4 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-400"
            />
          </div>

          {/* Catégorie — saisie libre avec suggestions */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              <span className="flex items-center gap-1"><Tag size={13} /> Catégorie</span>
            </label>
            <input
              type="text"
              list="training-categories"
              placeholder="Ex : Marketing, Cybersécurité…"
              value={form.category}
              onChange={set('category')}
              className="w-full px-4 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-400"
            />
            <datalist id="training-categories">
              {categories.map((c) => <option key={c} value={c} />)}
            </datalist>
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">Description</label>
            <textarea
              rows={3}
              placeholder="Décrivez le contenu et les objectifs…"
              value={form.description}
              onChange={set('description')}
              className="w-full px-4 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-400 resize-none"
            />
          </div>

          {/* Pièces jointes */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              <span className="flex items-center gap-1"><Paperclip size={13} /> Pièces jointes</span>
            </label>
            <div className="space-y-1.5">
              {visibleExisting.map((path) => (
                <div key={path} className="flex items-center gap-2 bg-gray-50 border border-gray-100 rounded-lg px-3 py-2">
                  <FileText size={14} className="text-gray-400 flex-shrink-0" />
                  <span className="flex-1 text-sm text-gray-700 truncate">{docName(path)}</span>
                  <button type="button" onClick={() => setRemovedDocs((prev) => [...prev, path])}
                    className="text-gray-400 hover:text-red-500" title="Retirer">
                    <Trash2 size={15} />
                  </button>
                </div>
              ))}
              {docFiles.map((file, i) => (
                <div key={`${file.name}-${i}`} className="flex items-center gap-2 bg-purple-50 border border-purple-100 rounded-lg px-3 py-2">
                  <FileText size={14} className="text-purple-400 flex-shrink-0" />
                  <span className="flex-1 text-sm text-gray-700 truncate">{file.name}</span>
                  <button type="button" onClick={() => setDocFiles((prev) => prev.filter((_, idx) => idx !== i))}
                    className="text-gray-400 hover:text-red-500" title="Retirer">
                    <Trash2 size={15} />
                  </button>
                </div>
              ))}
            </div>
            <label className="mt-2 inline-flex items-center gap-1.5 text-sm font-medium text-purple-500 hover:text-purple-600 cursor-pointer">
              <Upload size={15} /> Ajouter un document
              <input type="file" multiple className="hidden"
                accept=".pdf,.doc,.docx,.ppt,.pptx,.xls,.xlsx,.odt,.odp,.ods,.txt,.csv,.jpg,.jpeg,.png,.webp"
                onChange={onPickFiles} />
            </label>
            <p className="text-xs text-gray-400 mt-1">Plaquettes, programmes… PDF, Office, images.</p>
          </div>

          <p className="text-xs text-gray-400 bg-gray-50 border border-gray-100 rounded-lg px-3 py-2">
            Les dates, la jauge d'inscrits et les invitations se définissent lors de la
            <span className="font-medium text-gray-500"> programmation d'une session</span> (réservée au super admin).
          </p>

          {error && (
            <p className="text-sm text-red-500 bg-red-50 border border-red-200 rounded-lg px-3 py-2">{error}</p>
          )}

          {/* Actions */}
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
              disabled={submitting}
              className="flex-1 bg-purple-500 hover:bg-purple-600 disabled:opacity-60 text-white font-semibold py-2.5 rounded-xl transition-colors flex items-center justify-center gap-2 text-sm"
            >
              {submitting ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />}
              {isEdit ? 'Enregistrer' : 'Créer'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
