/** Annuaire des personnes (trombinoscope). */

import { Search, Users } from 'lucide-react'
import { useState } from 'react'

import PageHeader from '../../components/layout/PageHeader'
import { EmptyState, Input, Pagination, Spinner } from '../../components/ui'
import { useDebounce } from '../../lib/useDebounce'
import PersonCard from './PersonCard'
import { PAGE_SIZE, usePeople } from './queries'

/** Trombinoscope : recherche par nom, fonction ou entreprise. */
export default function PeoplePage() {
  const [search, setSearch] = useState('')
  const [offset, setOffset] = useState(0)
  const debounced = useDebounce(search)
  const { data, isLoading, isError } = usePeople({ search: debounced, offset })

  return (
    <>
      <PageHeader
        title="Annuaire"
        description="Retrouvez les personnes de la Maison de l'Économie."
      />
      <div className="relative mb-6 max-w-md">
        <Search
          size={16}
          className="pointer-events-none absolute top-9 left-3 text-slate-400"
          aria-hidden="true"
        />
        <Input
          label="Rechercher"
          type="search"
          placeholder="Nom, fonction, entreprise…"
          className="pl-9"
          value={search}
          onChange={(e) => {
            setSearch(e.target.value)
            setOffset(0)
          }}
        />
      </div>

      {isLoading && <Spinner />}
      {isError && <p role="alert">Impossible de charger l'annuaire.</p>}
      {data && data.items.length === 0 && (
        <EmptyState icon={Users} title="Aucune personne trouvée" />
      )}
      {data && data.items.length > 0 && (
        <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {data.items.map((person) => (
            <li key={person.id}>
              <PersonCard person={person} />
            </li>
          ))}
        </ul>
      )}
      {data && (
        <Pagination total={data.total} limit={PAGE_SIZE} offset={offset} onChange={setOffset} />
      )}
    </>
  )
}
