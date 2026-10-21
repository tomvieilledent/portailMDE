import React, { useState, useEffect } from 'react'
import { Check, X, Clock } from 'lucide-react'
import { api } from '../lib/api'

const nameOf = (u) => u
  ? ([u.first_name, u.last_name].filter(Boolean).join(' ') || u.email || 'Utilisateur')
  : 'Utilisateur'

// Vue organisateur : qui a répondu à l'invitation pour cet événement/formation.
export default function InvitationResponses({ targetType, targetId, users = [] }) {
  const [invs, setInvs] = useState(null)
  const usersById = Object.fromEntries(users.map((u) => [u.id, u]))

  useEffect(() => {
    let cancelled = false
    if (!targetId) return
    api.getTargetInvitations(targetType, targetId)
      .then((res) => { if (!cancelled) setInvs(res?.invitations || []) })
      .catch(() => { if (!cancelled) setInvs([]) })
    return () => { cancelled = true }
  }, [targetType, targetId])

  if (invs === null) return null
  if (invs.length === 0) return null

  const counts = {
    accepted: invs.filter((i) => i.status === 'accepted').length,
    declined: invs.filter((i) => i.status === 'declined').length,
    pending:  invs.filter((i) => i.status === 'pending').length,
  }

  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-2">Réponses aux invitations</label>
      <div className="flex gap-2 mb-2">
        <span className="flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-green-100 text-green-600"><Check size={12} /> {counts.accepted}</span>
        <span className="flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-gray-100 text-gray-500"><X size={12} /> {counts.declined}</span>
        <span className="flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-amber-100 text-amber-600"><Clock size={12} /> {counts.pending}</span>
      </div>
      <div className="max-h-32 overflow-y-auto border border-gray-100 rounded-lg divide-y divide-gray-50">
        {invs.map((i) => (
          <div key={i.id} className="flex items-center gap-2 px-3 py-1.5">
            <span className="flex-1 text-sm text-gray-700 truncate">{nameOf(usersById[i.invitee_id])}</span>
            <span className={`text-xs font-semibold ${
              i.status === 'accepted' ? 'text-green-600' : i.status === 'declined' ? 'text-gray-400' : 'text-amber-600'
            }`}>
              {i.status === 'accepted' ? 'Accepté' : i.status === 'declined' ? 'Décliné' : 'En attente'}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
