/** Annuaire des entreprises. */

import { Building2, Globe, MapPin, Search } from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router-dom'

import PageHeader from '../../components/layout/PageHeader'
import { Badge, Card, EmptyState, Input, Pagination, Select, Spinner } from '../../components/ui'
import { useDebounce } from '../../lib/useDebounce'
import { uploadUrl } from '../../lib/uploads'
import { COMPANY_KINDS } from './labels'
import { PAGE_SIZE, useCompanies } from './queries'

/** Logo de l'entreprise, ou ses initiales à défaut. */
export function CompanyLogo({ company, className = 'h-14 w-14' }) {
  return company.logo_path ? (
    <img
      src={uploadUrl(company.logo_path)}
      loading="lazy"
      decoding="async"
      alt=""
      className={`${className} shrink-0 rounded-lg object-contain`}
    />
  ) : (
    <span
      aria-hidden="true"
      className={`${className} bg-brand-100 text-brand-700 dark:bg-brand-900 dark:text-brand-200 inline-flex shrink-0 items-center justify-center rounded-lg`}
    >
      <Building2 />
    </span>
  )
}

/** Annuaire des entreprises, partenaires et formateurs. */
export default function CompaniesPage() {
  const [search, setSearch] = useState('')
  const [kind, setKind] = useState('')
  const [offset, setOffset] = useState(0)
  const debounced = useDebounce(search)
  const { data, isLoading, isError } = useCompanies({ search: debounced, kind, offset })

  return (
    <>
      <PageHeader
        title="Entreprises"
        description="Les entreprises hébergées, partenaires et formateurs."
      />
      <div className="mb-6 flex flex-wrap items-end gap-4">
        <div className="relative w-full max-w-md">
          <Search
            size={16}
            className="pointer-events-none absolute top-9 left-3 text-slate-400"
            aria-hidden="true"
          />
          <Input
            label="Rechercher"
            type="search"
            placeholder="Nom ou activité…"
            className="pl-9"
            value={search}
            onChange={(e) => {
              setSearch(e.target.value)
              setOffset(0)
            }}
          />
        </div>
        <Select
          label="Type"
          value={kind}
          onChange={(e) => {
            setKind(e.target.value)
            setOffset(0)
          }}
        >
          <option value="">Tous</option>
          {Object.entries(COMPANY_KINDS).map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </Select>
      </div>

      {isLoading && <Spinner />}
      {isError && <p role="alert">Impossible de charger les entreprises.</p>}
      {data && data.items.length === 0 && (
        <EmptyState icon={Building2} title="Aucune entreprise trouvée" />
      )}
      {data && data.items.length > 0 && (
        <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {data.items.map((company) => (
            <li key={company.id}>
              <Link to={`/entreprises/${company.id}`} className="block h-full">
                <Card className="hover:border-brand-400 flex h-full flex-col gap-3 transition hover:shadow-md">
                  <div className="flex items-center gap-3">
                    <CompanyLogo company={company} />
                    <div className="min-w-0">
                      <p className="truncate font-semibold">{company.name}</p>
                      <Badge tone="brand">{COMPANY_KINDS[company.kind]}</Badge>
                    </div>
                  </div>
                  {company.description && (
                    <p className="line-clamp-3 text-sm text-slate-600 dark:text-slate-400">
                      {company.description}
                    </p>
                  )}
                  <div className="mt-auto flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-500">
                    {company.location && (
                      <span className="inline-flex items-center gap-1">
                        <MapPin size={12} aria-hidden="true" /> {company.location}
                      </span>
                    )}
                    {company.website_url && (
                      <span className="inline-flex items-center gap-1">
                        <Globe size={12} aria-hidden="true" /> Site web
                      </span>
                    )}
                    <span>
                      {company.member_count} membre{company.member_count > 1 ? 's' : ''}
                    </span>
                  </div>
                </Card>
              </Link>
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
