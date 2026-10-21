/** Définition du menu principal. */

import {
  Briefcase,
  Building2,
  CalendarDays,
  GraduationCap,
  MessageSquare,
  Newspaper,
  Settings,
  Store,
  Users,
} from 'lucide-react'

/** Entrées du menu principal. `staffOnly` : réservé au staff et au super admin ; `needsCompany` : membres rattachés à une entreprise ; `companyAdminOnly` : administrateurs de leur entreprise. */
export const navItems = [
  { to: '/mon-entreprise', label: 'Mon entreprise', icon: Store, needsCompany: true },
  { to: '/annuaire', label: 'Annuaire', icon: Users },
  { to: '/entreprises', label: 'Entreprises', icon: Building2 },
  { to: '/messagerie', label: 'Messagerie', icon: MessageSquare },
  { to: '/agenda', label: 'Agenda', icon: CalendarDays },
  { to: '/formations', label: 'Formations', icon: GraduationCap },
  { to: '/actualites', label: 'Actualités', icon: Newspaper },
  {
    to: '/mon-entreprise/administration',
    label: "Administration de l'entreprise",
    icon: Settings,
    companyAdminOnly: true,
  },
  { to: '/administration', label: 'Administration', icon: Briefcase, staffOnly: true },
]
