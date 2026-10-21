/** Sélecteur de personnes de la messagerie. */

import { useQuery } from '@tanstack/react-query'
import { Check } from 'lucide-react'

import { Avatar, Button, Input, Select, Spinner, uploadUrl } from '../../components/ui'
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
  const [companyId, setCompanyId] = useState('')
  const debounced = useDebounce(search)
  const { data, isLoading } = useQuery({
    queryKey: ['directory', 'picker', debounced, companyId],
    queryFn: () =>
      api.get('/directory/people', {
        search: debounced,
        limit: single ? 20 : 200,
        ...(companyId ? { company_id: companyId } : {}),
      }),
  })
  // Tri par entreprise (sélection multiple uniquement)
  const companies = useQuery({
    queryKey: ['directory', 'picker', 'companies'],
    queryFn: () => api.get('/directory/companies', { limit: 200 }),
    enabled: !single,
  })

  const toggle = (id) => {
    if (single) return onChange(selected.includes(id) ? [] : [id])
    onChange(selected.includes(id) ? selected.filter((s) => s !== id) : [...selected, id])
  }
  const people = data?.items.filter((p) => !exclude.includes(p.id)) ?? []
  const allChecked = people.length > 0 && people.every((p) => selected.includes(p.id))
  // Coche (ou décoche) toutes les personnes actuellement listées : recherche et entreprise comprises.
  const toggleAll = () =>
    onChange(
      allChecked
        ? selected.filter((id) => !people.some((p) => p.id === id))
        : [...new Set([...selected, ...people.map((p) => p.id)])],
    )

  return (
    <div className="space-y-2">
      <Input
        label="Rechercher une personne"
        type="search"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
      />
      {!single && (
        <div className="flex flex-wrap items-end gap-3">
          <div className="min-w-0 flex-1">
            <Select
              label="Filtrer par entreprise"
              value={companyId}
              onChange={(e) => setCompanyId(e.target.value)}
            >
              <option value="">Toutes les entreprises</option>
              {companies.data?.items.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </Select>
          </div>
          <Button
            variant="secondary"
            disabled={people.length === 0}
            onClick={toggleAll}
            aria-pressed={allChecked}
          >
            {allChecked ? 'Tout désélectionner' : 'Tout sélectionner'}
          </Button>
        </div>
      )}
      {!single && (
        <p className="text-xs text-slate-500" aria-live="polite">
          {selected.length} personne{selected.length > 1 ? 's' : ''} sélectionnée
          {selected.length > 1 ? 's' : ''}
        </p>
      )}
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
