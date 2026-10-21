/** Tuile « carte de visite » d'une personne de l'annuaire, qui se retourne sur sa carte. */

import { Download, Mail, Phone, Undo2 } from 'lucide-react'
import { useState } from 'react'

import { Avatar, uploadUrl } from '../../components/ui'
import { cardLines, exportCardPng, exportCardVCard } from '../../lib/businessCard'
import { cn } from '../../lib/cn'
import { fullName } from './labels'

/** Face commune : même cadre, masquée quand elle est de dos. */
const FACE =
  'absolute inset-0 overflow-hidden rounded-xl border border-slate-200 bg-white [backface-visibility:hidden] dark:border-slate-700 dark:bg-slate-900'

/** Pastille ronde avec le logo de l'entreprise (initiale à défaut), en haut à droite du recto. */
function CompanyBadge({ company }) {
  const logo = uploadUrl(company.logo_path)
  return (
    <span
      aria-hidden="true"
      className="absolute top-3 right-3 flex h-10 w-10 items-center justify-center overflow-hidden rounded-full border border-slate-200 bg-white text-sm font-semibold text-slate-600 shadow-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-200"
    >
      {logo ? (
        <img
          src={logo}
          alt=""
          loading="lazy"
          decoding="async"
          className="h-full w-full object-cover"
        />
      ) : (
        company.name.slice(0, 1).toUpperCase()
      )}
    </span>
  )
}

/** Petit bouton d'action posé sur le verso de la tuile. */
function CardAction({ icon: Icon, children, ...props }) {
  return (
    <button
      type="button"
      className="text-brand-700 hover:bg-brand-50 dark:text-brand-300 flex items-center gap-1 rounded-md bg-white/90 px-2 py-1 text-xs font-medium shadow-sm dark:bg-slate-900/90 dark:hover:bg-slate-800"
      {...props}
    >
      <Icon size={13} aria-hidden="true" />
      {children}
    </button>
  )
}

/** Carte de visite basique générée depuis le profil (quand aucune carte n'est enregistrée). */
function GeneratedCard({ person }) {
  const { name, job, company, email, phone } = cardLines(person)
  return (
    <div className="flex h-full w-full border-l-[10px] border-[#3f6b16] bg-white p-4 pb-9 text-slate-900">
      <div className="min-w-0 space-y-0.5">
        <p className="truncate text-lg leading-tight font-bold">{name}</p>
        {job && <p className="truncate text-xs text-slate-600">{job}</p>}
        {company && <p className="truncate pt-1 text-sm font-semibold text-[#3f6b16]">{company}</p>}
        <p className="truncate pt-2 text-xs text-slate-700">{email}</p>
        {phone && <p className="text-xs text-slate-700">{phone}</p>}
      </div>
    </div>
  )
}

/**
 * Tuile au format carte de visite (85 × 55). Au clic, elle se retourne : carte enregistrée
 * dans le profil, ou à défaut carte générée exportable (PNG / vCard).
 */
export default function PersonCard({ person }) {
  const [flipped, setFlipped] = useState(false)
  const [seen, setSeen] = useState(false) // le verso n'est rendu qu'après le premier retournement
  const name = fullName(person)
  const cardUrl = uploadUrl(person.business_card_path)

  return (
    <div className="space-y-2">
      <div className="[perspective:1000px]">
        <div
          className={cn(
            'relative aspect-[85/55] w-full transition-transform duration-500 [transform-style:preserve-3d] motion-reduce:transition-none',
            flipped && '[transform:rotateY(180deg)]',
          )}
        >
          <div aria-hidden={flipped} className={cn(FACE, 'flex items-center gap-4 p-5')}>
            {!flipped && (
              <button
                type="button"
                onClick={() => {
                  setSeen(true)
                  setFlipped(true)
                }}
                aria-label={`${name} : voir la carte de visite`}
                className="focus-visible:ring-brand-500 absolute inset-0 rounded-2xl focus-visible:ring-2 focus-visible:outline-none"
              />
            )}
            {person.company && <CompanyBadge company={person.company} />}
            <span
              aria-hidden="true"
              className="absolute right-3 bottom-2 text-[11px] text-slate-500"
            >
              Carte de visite au dos
            </span>
            <Avatar
              src={uploadUrl(person.avatar_path)}
              firstName={person.first_name}
              lastName={person.last_name}
              size="lg"
            />
            <div className="min-w-0 space-y-0.5">
              <p className="font-display truncate text-lg font-semibold">{name}</p>
              {person.job_title && (
                <p className="truncate text-sm text-slate-600 dark:text-slate-400">
                  {person.job_title}
                </p>
              )}
              {person.company && (
                <p className="text-brand-700 dark:text-brand-300 truncate text-sm font-medium">
                  {person.company.name}
                </p>
              )}
              <p className="flex items-center gap-1.5 truncate pt-1 text-xs text-slate-500">
                <Mail size={13} aria-hidden="true" />
                <span className="truncate">{person.email}</span>
              </p>
              {person.phone && (
                <p className="flex items-center gap-1.5 text-xs text-slate-500">
                  <Phone size={13} aria-hidden="true" />
                  {person.phone}
                </p>
              )}
            </div>
          </div>

          <div
            aria-hidden={!flipped}
            className={cn(FACE, '[transform:rotateY(180deg)] bg-slate-50 dark:bg-slate-800')}
          >
            {seen && (
              <>
                {cardUrl ? (
                  <img
                    src={cardUrl}
                    alt={`Carte de visite de ${name}`}
                    loading="lazy"
                    decoding="async"
                    className="h-full w-full object-contain"
                  />
                ) : (
                  <GeneratedCard person={person} />
                )}
                {flipped && (
                  <div className="absolute right-2 bottom-2 left-2 flex flex-wrap justify-end gap-1.5">
                    {cardUrl ? (
                      <a
                        href={cardUrl}
                        download
                        aria-label={`Télécharger la carte de visite de ${name}`}
                        className="text-brand-700 hover:bg-brand-50 dark:text-brand-300 flex items-center gap-1 rounded-md bg-white/90 px-2 py-1 text-xs font-medium shadow-sm dark:bg-slate-900/90"
                      >
                        <Download size={13} aria-hidden="true" />
                        Télécharger
                      </a>
                    ) : (
                      <>
                        <CardAction
                          icon={Download}
                          aria-label={`Exporter la carte de ${name} (PNG)`}
                          onClick={() => exportCardPng(person)}
                        >
                          PNG
                        </CardAction>
                        <CardAction
                          icon={Download}
                          aria-label={`Exporter le contact ${name} (vCard)`}
                          onClick={() => exportCardVCard(person)}
                        >
                          vCard
                        </CardAction>
                      </>
                    )}
                    <CardAction
                      icon={Undo2}
                      aria-label={`Retour aux informations de ${name}`}
                      onClick={() => setFlipped(false)}
                    >
                      Retour
                    </CardAction>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
