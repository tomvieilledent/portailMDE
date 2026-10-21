/** Sélecteur de personnes de la messagerie. */

import { useQuery } from '@tanstack/react-query'
import { Check } from 'lucide-react'

import { Avatar, Input, Spinner, uploadUrl } from '../../components/ui'
import { api } from '../../lib/api'
import { useDebounce } from '../../lib/useDebounce'
import { fullName } from '../directory/labels'
import { useState } from 'react'

/**
 * Sélecteur de personnes avec recherche (annuaire). `selected` : ids choisis,
 * `exclude` : ids masqués (déjà membres, soi-même), `single` : un seul choix possible.
 */
export default function UserPicker({ selected, onChange, exclude = [], single = false }) {
  const [search, setSearch] = useState('')
  const debounced = useDebounce(search)
  const { data, isLoading } = useQuery({
    queryKey: ['directory', 'picker', debounced],
    queryFn: () => api.get('/directory/people', { search: debounced, limit: 20 }),
  })

  const toggle = (id) => {
    if (single) return onChange(selected.includes(id) ? [] : [id])
    onChange(selected.includes(id) ? selected.filter((s) => s !== id) : [...selected, id])
  }
  const people = data?.items.filter((p) => !exclude.includes(p.id)) ?? []

  return (
    <div className="space-y-2">
      <Input
        label="Rechercher une personne"
        type="search"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
      />
      {isLoading && <Spinner className="h-5 w-5" />}
      <ul className="max-h-56 divide-y divide-slate-100 overflow-y-auto rounded-lg border border-slate-200 dark:divide-slate-800 dark:border-slate-700">
        {people.map((person) => {
          const checked = selected.includes(person.id)
          return (
            <li key={person.id}>
              <button
                type="button"
                role="checkbox"
                aria-checked={checked}
                onClick={() => toggle(person.id)}
                className="flex w-full items-center gap-3 px-3 py-2 text-left hover:bg-slate-50 dark:hover:bg-slate-800"
              >
                <Avatar
                  src={uploadUrl(person.avatar_path)}
                  firstName={person.first_name}
                  lastName={person.last_name}
                  size="sm"
                />
                <span className="flex-1 truncate text-sm">
                  {fullName(person)}
                  {person.company && (
                    <span className="text-slate-500"> · {person.company.name}</span>
                  )}
                </span>
                {checked && <Check size={16} className="text-brand-600" aria-hidden="true" />}
              </button>
            </li>
          )
        })}
        {!isLoading && people.length === 0 && (
          <li className="p-3 text-sm text-slate-500">Aucun résultat</li>
        )}
      </ul>
    </div>
  )
}
