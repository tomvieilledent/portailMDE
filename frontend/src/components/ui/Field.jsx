import { forwardRef, useId } from 'react'

import { cn } from '../../lib/cn'

const control =
  'block w-full rounded-lg border bg-white px-3 py-2 text-sm text-slate-900 shadow-sm placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-brand-500 disabled:cursor-not-allowed disabled:opacity-60 dark:bg-slate-900 dark:text-slate-100'

/** Champ de formulaire (libellé, aide, message d'erreur reliés au contrôle pour l'accessibilité). */
function FieldShell({ label, error, hint, id, children }) {
  return (
    <div className="space-y-1">
      {label && (
        <label
          htmlFor={id}
          className="block text-sm font-medium text-slate-700 dark:text-slate-300"
        >
          {label}
        </label>
      )}
      {children}
      {hint && !error && <p className="text-xs text-slate-500 dark:text-slate-400">{hint}</p>}
      {error && (
        <p id={`${id}-error`} role="alert" className="text-xs text-red-600 dark:text-red-400">
          {error}
        </p>
      )}
    </div>
  )
}

function controlProps(id, error) {
  return {
    id,
    'aria-invalid': error ? true : undefined,
    'aria-describedby': error ? `${id}-error` : undefined,
  }
}

const borderClass = (error) => (error ? 'border-red-500' : 'border-slate-300 dark:border-slate-700')

export const Input = forwardRef(function Input({ label, error, hint, className, ...props }, ref) {
  const id = useId()
  return (
    <FieldShell label={label} error={error} hint={hint} id={id}>
      <input
        ref={ref}
        className={cn(control, borderClass(error), className)}
        {...controlProps(id, error)}
        {...props}
      />
    </FieldShell>
  )
})

export const Textarea = forwardRef(function Textarea(
  { label, error, hint, className, rows = 4, ...props },
  ref,
) {
  const id = useId()
  return (
    <FieldShell label={label} error={error} hint={hint} id={id}>
      <textarea
        ref={ref}
        rows={rows}
        className={cn(control, borderClass(error), className)}
        {...controlProps(id, error)}
        {...props}
      />
    </FieldShell>
  )
})

export const Select = forwardRef(function Select(
  { label, error, hint, className, children, ...props },
  ref,
) {
  const id = useId()
  return (
    <FieldShell label={label} error={error} hint={hint} id={id}>
      <select
        ref={ref}
        className={cn(control, borderClass(error), className)}
        {...controlProps(id, error)}
        {...props}
      >
        {children}
      </select>
    </FieldShell>
  )
})
