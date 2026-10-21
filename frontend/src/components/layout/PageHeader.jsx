/** En-tête de page réutilisable (titre, description, actions). */

/** Titre de page avec description et zone d'actions. */
export default function PageHeader({ title, description, actions }) {
  return (
    <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
      <div>
        <h1 className="text-2xl font-bold">{title}</h1>
        {description && (
          <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">{description}</p>
        )}
      </div>
      {actions}
    </div>
  )
}
