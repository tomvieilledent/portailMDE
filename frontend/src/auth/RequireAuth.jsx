/** Garde de route réservant l'accès aux utilisateurs connectés et autorisés. */

import { Navigate, Outlet, useLocation } from 'react-router-dom'

import { Spinner } from '../components/ui'
import { useAuth } from './AuthProvider'
import { hasPermission, isStaff } from './permissions'

/**
 * Garde de route : redirige vers la connexion si non connecté.
 * `permission` restreint l'accès à un droit staff ; `staffOnly` à tout le staff ;
 * `allowPending` laisse passer un utilisateur qui doit encore changer son mot de passe.
 */
export default function RequireAuth({ permission, staffOnly = false, allowPending = false }) {
  const { user, loading } = useAuth()
  const location = useLocation()

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Spinner />
      </div>
    )
  }
  if (!user) return <Navigate to="/connexion" replace state={{ from: location }} />
  // Mot de passe temporaire : changement obligatoire avant tout accès au portail.
  if (user.must_change_password && !allowPending) {
    return <Navigate to="/changer-mot-de-passe" replace />
  }
  if ((permission && !hasPermission(user, permission)) || (staffOnly && !isStaff(user))) {
    return <Navigate to="/annuaire" replace />
  }
  return <Outlet />
}
