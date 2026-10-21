import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Bell } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { useToast } from '../../components/ui'
import { api } from '../../lib/api'
import { cn } from '../../lib/cn'
import { useRealtime } from '../../realtime/useRealtime'
import { notificationTarget } from './target'

/** Cloche de l'en-tête : compteur de non lues, liste déroulante, mises à jour en temps réel. */
export default function NotificationsBell() {
  const navigate = useNavigate()
  const toast = useToast()
  const queryClient = useQueryClient()
  const [open, setOpen] = useState(false)
  const root = useRef(null)

  const count = useQuery({
    queryKey: ['notifications', 'count'],
    queryFn: () => api.get('/notifications/unread-count'),
    refetchInterval: 120_000,
  })
  const list = useQuery({
    queryKey: ['notifications', 'list'],
    queryFn: () => api.get('/notifications', { limit: 15 }),
    enabled: open,
  })
  const refresh = () => queryClient.invalidateQueries({ queryKey: ['notifications'] })

  useRealtime('notification.new', (event) => {
    refresh()
    toast.info(event.notification.content)
  })

  const markRead = useMutation({
    mutationFn: (id) => api.post(`/notifications/${id}/read`),
    onSuccess: refresh,
  })
  const readAll = useMutation({
    mutationFn: () => api.post('/notifications/read-all'),
    onSuccess: refresh,
  })

  useEffect(() => {
    if (!open) return undefined
    const close = (event) => {
      if (
        event.key === 'Escape' ||
        (event.type === 'mousedown' && !root.current?.contains(event.target))
      ) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', close)
    document.addEventListener('keydown', close)
    return () => {
      document.removeEventListener('mousedown', close)
      document.removeEventListener('keydown', close)
    }
  }, [open])

  const unread = count.data?.count ?? 0

  function onSelect(notification) {
    if (!notification.is_read) markRead.mutate(notification.id)
    setOpen(false)
    const target = notificationTarget(notification)
    if (target) navigate(target)
  }

  return (
    <div ref={root} className="relative">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-label={unread ? `Notifications (${unread} non lues)` : 'Notifications'}
        aria-expanded={open}
        className="relative rounded-lg p-2 hover:bg-slate-100 dark:hover:bg-slate-800"
      >
        <Bell size={18} />
        {unread > 0 && (
          <span className="absolute right-0.5 top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-red-600 px-1 text-[10px] font-bold text-white">
            {unread > 9 ? '9+' : unread}
          </span>
        )}
      </button>
      {open && (
        <div
          role="dialog"
          aria-label="Notifications"
          className="absolute right-0 z-50 mt-2 w-80 max-w-[90vw] rounded-xl border border-slate-200 bg-white shadow-xl dark:border-slate-700 dark:bg-slate-900"
        >
          <div className="flex items-center justify-between border-b border-slate-200 px-4 py-3 dark:border-slate-800">
            <h2 className="text-sm font-semibold">Notifications</h2>
            {unread > 0 && (
              <button
                type="button"
                onClick={() => readAll.mutate()}
                className="text-xs text-brand-700 hover:underline dark:text-brand-300"
              >
                Tout marquer comme lu
              </button>
            )}
          </div>
          <ul className="max-h-96 overflow-y-auto">
            {list.data?.length === 0 && (
              <li className="p-4 text-center text-sm text-slate-500">Aucune notification</li>
            )}
            {list.data?.map((notification) => (
              <li key={notification.id}>
                <button
                  type="button"
                  onClick={() => onSelect(notification)}
                  className={cn(
                    'block w-full border-b border-slate-100 px-4 py-3 text-left text-sm hover:bg-slate-50 dark:border-slate-800 dark:hover:bg-slate-800',
                    !notification.is_read && 'bg-brand-50/60 font-medium dark:bg-brand-900/20',
                  )}
                >
                  {notification.content}
                  <time className="mt-1 block text-xs font-normal text-slate-400">
                    {new Date(notification.created_at).toLocaleString('fr-FR', {
                      day: 'numeric',
                      month: 'short',
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </time>
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
