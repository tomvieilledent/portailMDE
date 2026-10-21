/** Boîte de dialogue modale accessible. */

import { X } from 'lucide-react'
import { useEffect, useId, useRef } from 'react'

import { cn } from '../../lib/cn'

/** Boîte de dialogue modale : Échap ou clic sur le fond pour fermer, focus restauré à la fermeture. */
export default function Modal({ open, onClose, title, children, footer, className }) {
  const titleId = useId()
  const panelRef = useRef(null)

  useEffect(() => {
    if (!open) return undefined
    const previous = document.activeElement
    panelRef.current?.focus()
    const onKey = (event) => event.key === 'Escape' && onClose()
    document.addEventListener('keydown', onKey)
    document.body.style.overflow = 'hidden'
    return () => {
      document.removeEventListener('keydown', onKey)
      document.body.style.overflow = ''
      previous?.focus?.()
    }
  }, [open, onClose])

  if (!open) return null
  return (
    <div
      className="fixed inset-0 z-50 flex items-end justify-center bg-slate-900/50 p-0 sm:items-center sm:p-4"
      onMouseDown={(event) => event.target === event.currentTarget && onClose()}
    >
      <div
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        tabIndex={-1}
        className={cn(
          'max-h-[90vh] w-full overflow-y-auto rounded-t-2xl bg-white p-6 shadow-xl focus:outline-none sm:max-w-lg sm:rounded-2xl dark:bg-slate-900',
          className,
        )}
      >
        <div className="mb-4 flex items-start justify-between gap-4">
          <h2 id={titleId} className="text-lg font-semibold">
            {title}
          </h2>
          <button
            type="button"
            onClick={onClose}
            aria-label="Fermer"
            className="rounded-lg p-1 text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800"
          >
            <X size={18} />
          </button>
        </div>
        {children}
        {footer && <div className="mt-6 flex justify-end gap-2">{footer}</div>}
      </div>
    </div>
  )
}
