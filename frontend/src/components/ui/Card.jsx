/** Conteneur de type carte. */

import { cn } from '../../lib/cn'

/** Carte : conteneur avec bordure et ombre. */
export default function Card({ className, children, ...props }) {
  return (
    <div
      className={cn(
        'rounded-xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900',
        className,
      )}
      {...props}
    >
      {children}
    </div>
  )
}
