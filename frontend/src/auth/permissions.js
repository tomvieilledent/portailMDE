/** Rôles et droits des utilisateurs (super admin, staff, membre) et fonctions de vérification. */

/** Droits du staff, miroir de `Permission` côté backend. */
export const PERMISSIONS = {
  MANAGE_COMPANIES: 'manage_companies',
  MANAGE_USERS: 'manage_users',
  MANAGE_TRAININGS: 'manage_trainings',
  MANAGE_NEWS: 'manage_news',
}

/** Vrai si l'utilisateur est super administrateur. */
export const isSuperAdmin = (user) => user?.role === 'super_admin'

/** Vrai si l'utilisateur fait partie du staff (super admin inclus). */
export const isStaff = (user) => user?.role === 'staff' || isSuperAdmin(user)

/** Le super admin a tous les droits ; le staff uniquement ceux qui lui sont attribués. */
export function hasPermission(user, permission) {
  if (!user) return false
  if (isSuperAdmin(user)) return true
  return user.role === 'staff' && user.permissions.includes(permission)
}

/** Peut gérer cette entreprise : gestionnaire d'entreprises ou administrateur de celle-ci. */
export function canManageCompany(user, companyId) {
  return (
    hasPermission(user, PERMISSIONS.MANAGE_COMPANIES) ||
    Boolean(user?.is_company_admin && companyId && user.company_id === companyId)
  )
}
