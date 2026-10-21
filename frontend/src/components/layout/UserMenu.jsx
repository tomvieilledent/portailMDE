import { LogOut } from 'lucide-react'

import { useAuth } from '../../auth/AuthProvider'
import { Avatar, uploadUrl } from '../ui'

/** Identité de l'utilisateur connecté et bouton de déconnexion (zone d'actions de l'en-tête). */
export default function UserMenu() {
  const { user, logout } = useAuth()
  return (
    <div className="flex items-center gap-2">
      <Avatar
        src={uploadUrl(user.avatar_path)}
        firstName={user.first_name}
        lastName={user.last_name}
        size="sm"
      />
      <span className="hidden text-sm font-medium sm:inline">
        {[user.first_name, user.last_name].filter(Boolean).join(' ') || user.email}
      </span>
      <button
        type="button"
        onClick={logout}
        aria-label="Se déconnecter"
        className="rounded-lg p-2 hover:bg-slate-100 dark:hover:bg-slate-800"
      >
        <LogOut size={18} />
      </button>
    </div>
  )
}
