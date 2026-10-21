/** Définition du menu principal, organisé en rubriques. */

/** Rubriques du menu, dans l'ordre d'affichage. */
export const NAV_GROUPS = {
  main: null,
  community: 'Communauté',
  life: 'Vie de la Maison',
  manage: 'Gestion',
}

/**
 * Entrées du menu principal. `group` : rubrique (cf. `NAV_GROUPS`) ; `staffOnly` : réservé au
 * staff et au super admin ; `needsCompany` : membres rattachés à une entreprise ;
 * `companyAdminOnly` : administrateurs de leur entreprise.
 */
export const navItems = [
  { to: '/accueil', label: 'Accueil', group: 'main' },
  { to: '/annuaire', label: 'Annuaire', group: 'community' },
  { to: '/entreprises', label: 'Entreprises', group: 'community' },
  { to: '/messagerie', label: 'Messagerie', group: 'community' },
  { to: '/actualites', label: 'Actualités', group: 'life' },
  { to: '/agenda', label: 'Agenda', group: 'life' },
  { to: '/formations', label: 'Formations', group: 'life' },
  {
    to: '/mon-entreprise/administration',
    label: 'Administrer mon entreprise',
    group: 'manage',
    companyAdminOnly: true,
  },
  {
    to: '/administration',
    label: 'Administration',
    group: 'manage',
    staffOnly: true,
  },
]
