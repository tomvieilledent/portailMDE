/** Sélecteur d'image avec aperçu. */

import { useId } from 'react'

import Spinner from './Spinner'

/** Sélecteur d'image avec aperçu ; `onSelect(file)` est appelé dès qu'un fichier est choisi. */
export default function ImageUpload({ label, preview, onSelect, loading = false, error }) {
  const id = useId()
  return (
    <div className="space-y-2">
      <label htmlFor={id} className="block text-sm font-medium text-slate-700 dark:text-slate-300">
        {label}
      </label>
      <div className="flex flex-wrap items-center gap-3 sm:flex-nowrap sm:gap-4">
        {preview}
        <input
          id={id}
          type="file"
          accept="image/png,image/jpeg,image/gif,image/webp"
          disabled={loading}
          onChange={(event) => {
            const file = event.target.files?.[0]
            if (file) onSelect(file)
            event.target.value = ''
          }}
          className="file:bg-brand-50 file:text-brand-700 hover:file:bg-brand-100 dark:file:bg-brand-900 dark:file:text-brand-200 block w-full min-w-0 flex-1 truncate text-xs text-slate-600 file:mr-3 file:rounded-lg file:border-0 file:px-3 file:py-2 file:text-sm file:font-medium sm:text-sm dark:text-slate-300"
        />
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
