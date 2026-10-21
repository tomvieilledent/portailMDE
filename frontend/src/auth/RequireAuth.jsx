import { Navigate, Outlet, useLocation } from 'react-router-dom'

import { Spinner } from '../components/ui'
import { useAuth } from './AuthProvider'
import { hasPermission, isStaff } from './permissions'

/**
 * Garde de route : redirige vers la connexion si non connecté.
 * `permission` restreint l'accès à un droit staff ; `staffOnly` à tout le staff.
 */
export default function RequireAuth({ permission, staffOnly = false }) {
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
  if ((permission && !hasPermission(user, permission)) || (staffOnly && !isStaff(user))) {
    return <Navigate to="/annuaire" replace />
  }
  return <Outlet />
}
