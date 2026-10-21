/** Carte d'une personne de l'annuaire. */

import { Avatar, Card, uploadUrl } from '../../components/ui'
import { fullName } from './labels'

/** Carte du trombinoscope ; cliquable pour ouvrir la fiche. */
export default function PersonCard({ person, onSelect }) {
  return (
    <button type="button" onClick={() => onSelect(person)} className="text-left">
      <Card className="hover:border-brand-400 flex h-full items-center gap-4 transition hover:shadow-md">
        <Avatar
          src={uploadUrl(person.avatar_path)}
          firstName={person.first_name}
          lastName={person.last_name}
          size="lg"
        />
        <div className="min-w-0">
          <p className="truncate font-semibold">{fullName(person)}</p>
          {person.job_title && (
            <p className="truncate text-sm text-slate-600 dark:text-slate-400">
              {person.job_title}
            </p>
          )}
          {person.company && (
            <p className="text-brand-700 dark:text-brand-300 truncate text-sm">
              {person.company.name}
            </p>
          )}
        </div>
      </Card>
    </button>
  )
}
