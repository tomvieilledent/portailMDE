/** Pagination des listes. */

import { ChevronLeft, ChevronRight } from 'lucide-react'

import Button from './Button'

/** Pagination précédent / suivant pour les réponses `{items, total, limit, offset}`. */
export default function Pagination({ total, limit, offset, onChange }) {
  if (total <= limit) return null
  const page = Math.floor(offset / limit) + 1
  const pages = Math.ceil(total / limit)
  return (
    <nav aria-label="Pagination" className="flex items-center justify-between gap-4 pt-4">
      <Button
        variant="secondary"
        size="sm"
        disabled={offset === 0}
        onClick={() => onChange(Math.max(0, offset - limit))}
      >
        <ChevronLeft size={16} aria-hidden="true" /> Précédent
      </Button>
      <span className="text-sm text-slate-600 dark:text-slate-400">
        Page {page} sur {pages}
      </span>
      <Button
        variant="secondary"
        size="sm"
        disabled={offset + limit >= total}
        onClick={() => onChange(offset + limit)}
      >
        Suivant <ChevronRight size={16} aria-hidden="true" />
      </Button>
    </nav>
  )
}
