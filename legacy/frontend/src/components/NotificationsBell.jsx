import React, { useState, useEffect, useRef } from 'react'
import { Bell, Check, X, CalendarDays, GraduationCap } from 'lucide-react'
import { api } from '../lib/api'
import { getSocket } from '../lib/socket'

const TYPE_META = {
  event:    { label: 'Événement', Icon: CalendarDays },
  training: { label: 'Formation',  Icon: GraduationCap },
}

function fmtDate(iso) {
  if (!iso) return ''
  try { return new Date(iso).toLocaleDateString('fr-FR', { day: '2-digit', month: 'short' }) }
  catch { return '' }
}

// Cloche de notifications : invitations reçues (événements / formations) avec
// réponse RSVP (accepter / décliner), mise à jour en temps réel via Socket.IO.
export default function NotificationsBell() {
  const [open, setOpen] = useState(false)
  const [items, setItems] = useState([])
  const [pending, setPending] = useState(0)
  const [busyId, setBusyId] = useState(null)
  const panelRef = useRef(null)

  const load = () =>
    api.getMyInvitations()
      .then((res) => { setItems(res?.invitations || []); setPending(res?.pending || 0) })
      .catch(() => { /* silencieux */ })

  useEffect(() => { load() }, [])

  // Réception en direct d'une nouvelle invitation.
  useEffect(() => {
    const socket = getSocket()
    if (!socket) return
    const onInvitation = ({ invitation }) => {
      if (!invitation) return
      setItems((prev) => prev.some((i) => i.id === invitation.id) ? prev : [invitation, ...prev])
      if (invitation.status === 'pending') setPending((n) => n + 1)
    }
    socket.on('invitation', onInvitation)
    return () => socket.off('invitation', onInvitation)
  }, [])

  // Fermeture au clic extérieur.
  useEffect(() => {
    if (!open) return
    const onClick = (e) => { if (panelRef.current && !panelRef.current.contains(e.target)) setOpen(false) }
    document.addEventListener('mousedown', onClick)
    return () => document.removeEventListener('mousedown', onClick)
  }, [open])

  const toggle = () => {
    const next = !open
    setOpen(next)
    if (next) api.markInvitationsRead().catch(() => {})
  }

  const respond = async (id, status) => {
    setBusyId(id)
    try {
      const res = await api.respondInvitation(id, status)
      const updated = res?.invitation
      if (updated) {
        setItems((prev) => prev.map((i) => i.id === id ? updated : i))
        setPending((n) => Math.max(0, n - 1))
        // Répondre à une invitation de session (in)scrit l'utilisateur côté
        // backend : on prévient les vues montées (Formations) pour qu'elles
        // ré-hydratent leurs inscriptions sans attendre un remontage.
        if (updated.target_type === 'session') {
          window.dispatchEvent(new CustomEvent('enrollments:changed'))
        }
      }
    } catch { /* ignore */ }
    finally { setBusyId(null) }
  }

  return (
    <div className="relative" ref={panelRef}>
      <button onClick={toggle}
        className="relative p-2.5 hover:bg-gray-100 rounded-xl transition-colors text-gray-500 hover:text-gray-800"
        title="Notifications">
        <Bell size={26} />
        {pending > 0 && (
          <span className="absolute top-1.5 right-1.5 min-w-[16px] h-4 px-1 bg-red-500 rounded-full flex items-center justify-center text-white text-xs font-bold leading-none">
            {pending}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 mt-2 w-80 bg-white rounded-2xl shadow-xl border border-gray-100 z-50 overflow-hidden">
          <div className="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
            <p className="font-bold text-gray-900 text-sm">Notifications</p>
            {pending > 0 && <span className="text-xs text-primary-light font-semibold">{pending} en attente</span>}
          </div>
          <div className="max-h-96 overflow-y-auto">
            {items.length === 0 && (
              <p className="px-4 py-8 text-center text-sm text-gray-400">Aucune invitation</p>
            )}
            {items.map((inv) => {
              const meta = TYPE_META[inv.target_type] || TYPE_META.event
              const Icon = meta.Icon
              return (
                <div key={inv.id} className="px-4 py-3 border-b border-gray-50 last:border-0">
                  <div className="flex items-start gap-2.5">
                    <div className="w-8 h-8 rounded-lg bg-primary-light/10 flex items-center justify-center flex-shrink-0">
                      <Icon size={16} className="text-primary-light" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-gray-900">
                        Invitation · <span className="text-gray-400">{meta.label}</span>
                      </p>
                      <p className="text-sm font-semibold text-gray-900 truncate">{inv.target_title || 'Sans titre'}</p>
                      <p className="text-xs text-gray-400">{fmtDate(inv.created_at)}</p>

                      {inv.status === 'pending' ? (
                        <div className="flex gap-2 mt-2">
                          <button onClick={() => respond(inv.id, 'accepted')} disabled={busyId === inv.id}
                            className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-primary-light hover:bg-primary text-white text-xs font-semibold disabled:opacity-50">
                            <Check size={13} /> Accepter
                          </button>
                          <button onClick={() => respond(inv.id, 'declined')} disabled={busyId === inv.id}
                            className="flex items-center gap-1 px-2.5 py-1 rounded-lg border border-gray-200 text-gray-600 hover:bg-gray-50 text-xs font-semibold disabled:opacity-50">
                            <X size={13} /> Décliner
                          </button>
                        </div>
                      ) : (
                        <span className={`inline-block mt-1.5 px-2 py-0.5 rounded-full text-xs font-semibold ${
                          inv.status === 'accepted' ? 'bg-green-100 text-green-600' : 'bg-gray-100 text-gray-500'
                        }`}>
                          {inv.status === 'accepted' ? 'Accepté' : 'Décliné'}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
