/** Notifications éphémères (toasts). */

import { CheckCircle2, Info, XCircle } from 'lucide-react'
import { createContext, useCallback, useContext, useMemo, useState } from 'react'

import { cn } from '../../lib/cn'

/** Contexte permettant d'afficher des notifications. */
const ToastContext = createContext(null)

const styles = {
  success: { icon: CheckCircle2, className: 'border-green-500 text-green-700 dark:text-green-300' },
  error: { icon: XCircle, className: 'border-red-500 text-red-700 dark:text-red-300' },
  info: { icon: Info, className: 'border-brand-500 text-brand-700 dark:text-brand-300' },
}

/** Notifications éphémères (« toasts ») annoncées aux lecteurs d'écran. */
export function ToastProvider({ children, duration = 8000 }) {
  const [toasts, setToasts] = useState([])

  const dismiss = useCallback((id) => setToasts((all) => all.filter((t) => t.id !== id)), [])

  const push = useCallback(
    (message, type = 'info') => {
      const id = crypto.randomUUID()
      setToasts((all) => [...all, { id, message, type }])
      setTimeout(() => dismiss(id), duration)
    },
    [dismiss, duration],
  )

  const api = useMemo(
    () => ({
      success: (message) => push(message, 'success'),
      error: (message) => push(message, 'error'),
      info: (message) => push(message, 'info'),
    }),
    [push],
  )

  return (
    <ToastContext.Provider value={api}>
      {children}
      <div
        role="status"
        aria-live="polite"
        className="pointer-events-none fixed inset-x-0 bottom-4 z-[60] flex flex-col items-center gap-2 px-4"
      >
        {toasts.map(({ id, message, type }) => {
          const { icon: Icon, className } = styles[type]
          return (
            <div
              key={id}
              role={type === 'error' ? 'alert' : undefined}
              className={cn(
                'pointer-events-auto flex max-w-md items-center gap-2 rounded-lg border-l-4 bg-white px-4 py-3 text-sm shadow-lg dark:bg-slate-800',
                className,
              )}
            >
              <Icon size={18} aria-hidden="true" />
              <span className="text-slate-800 dark:text-slate-100">{message}</span>
            </div>
          )
        })}
      </div>
    </ToastContext.Provider>
  )
}

/** Accès à la fonction d'affichage des notifications. */
// eslint-disable-next-line react-refresh/only-export-components
export function useToast() {
  const context = useContext(ToastContext)
  if (!context) throw new Error('useToast doit être utilisé dans un ToastProvider')
  return context
}
