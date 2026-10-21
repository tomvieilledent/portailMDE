import { ArrowLeft, Globe, MapPin } from 'lucide-react'
import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import PageHeader from '../../components/layout/PageHeader'
import { Badge, Card, EmptyState, Spinner } from '../../components/ui'
import { CompanyLogo } from './CompaniesPage'
import PersonCard from './PersonCard'
import PersonModal from './PersonModal'
import { COMPANY_KINDS } from './labels'
import { useCompany, useCompanyMembers } from './queries'

/** Fiche d'une entreprise et de ses membres. */
export default function CompanyPage() {
  const { companyId } = useParams()
  const company = useCompany(companyId)
  const members = useCompanyMembers(companyId)
  const [selected, setSelected] = useState(null)

  if (company.isLoading) return <Spinner />
  if (company.isError) {
    return (
      <EmptyState title="Entreprise introuvable" action={<Link to="/entreprises">Retour</Link>} />
    )
  }
  const c = company.data

  return (
    <>
      <Link
        to="/entreprises"
        className="text-brand-700 dark:text-brand-300 mb-4 inline-flex items-center gap-1 text-sm hover:underline"
      >
        <ArrowLeft size={14} aria-hidden="true" /> Toutes les entreprises
      </Link>
      <PageHeader title={c.name} actions={<Badge tone="brand">{COMPANY_KINDS[c.kind]}</Badge>} />
      <Card className="mb-8 flex flex-col gap-4 sm:flex-row">
        <CompanyLogo company={c} className="h-24 w-24" />
        <div className="space-y-2">
          {c.description && <p>{c.description}</p>}
          <div className="flex flex-wrap gap-x-6 gap-y-1 text-sm text-slate-600 dark:text-slate-400">
            {c.location && (
              <span className="inline-flex items-center gap-1">
                <MapPin size={14} aria-hidden="true" /> {c.location}
              </span>
            )}
            {c.website_url && (
              <a
                href={c.website_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-brand-700 dark:text-brand-300 inline-flex items-center gap-1 hover:underline"
              >
                <Globe size={14} aria-hidden="true" /> {c.website_url}
              </a>
            )}
          </div>
        </div>
      </Card>

      <h2 className="mb-4 text-lg font-semibold">Équipe</h2>
      {members.isLoading && <Spinner />}
      {members.data?.length === 0 && <EmptyState title="Aucun membre" />}
      <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {members.data?.map((member) => (
          <li key={member.id}>
            <PersonCard
              person={{ ...member, company: { id: c.id, name: c.name } }}
              onSelect={setSelected}
            />
          </li>
        ))}
      </ul>
      {selected && <PersonModal person={selected} onClose={() => setSelected(null)} />}
    </>
  )
}
