export default function EmptyState({ icon: Icon, title, description, action }) {
  return (
    <div className="flex flex-col items-center gap-2 rounded-xl border border-dashed border-slate-300 p-10 text-center dark:border-slate-700">
      {Icon && <Icon size={32} className="text-slate-400" aria-hidden="true" />}
      <p className="font-medium">{title}</p>
      {description && <p className="text-sm text-slate-500 dark:text-slate-400">{description}</p>}
      {action}
    </div>
  )
}
