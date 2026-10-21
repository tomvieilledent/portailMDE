/** Indicateur de chargement. */

import { cn } from '../../lib/cn'

/** Indicateur de chargement animé. */
export default function Spinner({ className }) {
  return (
    <span
      role="status"
      aria-label="Chargement"
      className={cn(
        'inline-block h-6 w-6 animate-spin rounded-full border-2 border-current border-t-transparent',
        className,
      )}
    />
  )
}
