/** Bouton de l'interface avec variantes et état de chargement. */

import { forwardRef } from 'react'

import { cn } from '../../lib/cn'
import Spinner from './Spinner'

const variants = {
  primary: 'bg-brand-700 text-white hover:bg-brand-800 focus-visible:ring-brand-500',
  secondary:
    'border border-slate-300 bg-white text-slate-700 hover:bg-slate-50 focus-visible:ring-brand-500 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800',
  danger: 'bg-red-600 text-white hover:bg-red-700 focus-visible:ring-red-500',
  ghost:
    'text-slate-600 hover:bg-slate-100 focus-visible:ring-brand-500 dark:text-slate-300 dark:hover:bg-slate-800',
}

const sizes = {
  sm: 'px-3 py-1.5 text-sm',
  md: 'px-4 py-2 text-sm',
  lg: 'px-5 py-2.5 text-base',
}

/** Bouton accessible ; `loading` désactive le bouton et affiche un indicateur. */
const Button = forwardRef(function Button(
  { variant = 'primary', size = 'md', loading = false, className, children, disabled, ...props },
  ref,
) {
  return (
    <button
      ref={ref}
      type="button"
      disabled={disabled || loading}
      className={cn(
        'inline-flex items-center justify-center gap-2 rounded-lg font-medium transition focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:outline-none disabled:cursor-not-allowed disabled:opacity-60 dark:focus-visible:ring-offset-slate-950',
        variants[variant],
        sizes[size],
        className,
      )}
      {...props}
    >
      {loading && <Spinner className="h-4 w-4" />}
      {children}
    </button>
  )
})

export default Button
