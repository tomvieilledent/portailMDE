/** En-tête de page réutilisable (rubrique, titre, description, actions). */

import { useLocation } from 'react-router-dom'

import { NAV_GROUPS, navItems } from '../../navigation'

/** Rubrique du menu correspondant à l'adresse courante (affichée au-dessus du titre). */
function useSection() {
  const { pathname } = useLocation()
  const item = navItems
    .filter((i) => pathname === i.to || pathname.startsWith(`${i.to}/`))
    .sort((a, b) => b.to.length - a.to.length)[0]
  return (item && NAV_GROUPS[item.group]) || 'Portail MDE'
}

/** Titre en deux graisses : tous les mots en léger, le dernier en gras. */
function StyledTitle({ title }) {
  const words = String(title).split(' ')
  if (words.length === 1) return <span className="font-bold">{title}</span>
  return (
    <>
      <span className="font-light">{words.slice(0, -1).join(' ')} </span>
      <span className="font-bold">{words[words.length - 1]}</span>
    </>
  )
}

/** Titre de page avec rubrique, description et zone d'actions. */
export default function PageHeader({ title, description, actions }) {
  const section = useSection()
  return (
    <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
      <div>
        <p className="text-xs font-semibold tracking-[0.2em] text-slate-500 uppercase">{section}</p>
        <h1 className="mt-1 text-3xl leading-tight tracking-tight sm:text-4xl">
          <StyledTitle title={title} />
        </h1>
        <span className="mt-2 block h-1 w-12 bg-[#7ec843]" aria-hidden="true" />
        {description && (
          <p className="mt-3 max-w-xl text-sm text-slate-600 dark:text-slate-400">{description}</p>
        )}
      </div>
      {actions}
    </div>
  )
}
