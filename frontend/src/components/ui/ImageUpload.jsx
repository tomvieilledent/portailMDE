/** Sélecteur d'image avec aperçu. */

import { useId, useState } from 'react'

import Spinner from './Spinner'

/** Sélecteur d'image avec aperçu ; `onSelect(file)` est appelé dès qu'un fichier est choisi. */
export default function ImageUpload({ label, preview, onSelect, loading = false, error }) {
  const id = useId()
  const [name, setName] = useState('')
  return (
    <div className="space-y-2">
      <label htmlFor={id} className="block text-sm font-medium text-slate-700 dark:text-slate-300">
        {label}
      </label>
      <div className="flex flex-wrap items-center gap-3">
        {preview}
        {/* Champ natif masqué : son texte (« Aucun fichier choisi ») était tronqué sur mobile. */}
        <input
          id={id}
          type="file"
          accept="image/png,image/jpeg,image/gif,image/webp"
          disabled={loading}
          onChange={(event) => {
            const file = event.target.files?.[0]
            if (file) {
              setName(file.name)
              onSelect(file)
            }
            event.target.value = ''
          }}
          className="peer sr-only"
        />
        <label
          htmlFor={id}
          className="bg-brand-50 text-brand-700 hover:bg-brand-100 dark:bg-brand-900 dark:text-brand-200 peer-focus-visible:ring-brand-500 inline-flex cursor-pointer items-center rounded-lg px-3 py-2 text-sm font-medium peer-focus-visible:ring-2 peer-disabled:cursor-not-allowed peer-disabled:opacity-60"
        >
          Choisir une image
        </label>
        <span className="min-w-0 text-xs break-all text-slate-500">
          {name || 'Aucune image choisie'}
        </span>
        {loading && <Spinner className="h-5 w-5" />}
      </div>
      {error && (
        <p role="alert" className="text-xs text-red-600 dark:text-red-400">
          {error}
        </p>
      )}
    </div>
  )
}
