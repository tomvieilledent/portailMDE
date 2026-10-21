import {
  Briefcase,
  Building2,
  CalendarDays,
  GraduationCap,
  MessageSquare,
  Newspaper,
  Users,
} from 'lucide-react'

/** Entrées du menu principal. `staffOnly` : réservé au staff et au super admin. */
export const navItems = [
  { to: '/annuaire', label: 'Annuaire', icon: Users },
  { to: '/entreprises', label: 'Entreprises', icon: Building2 },
  { to: '/messagerie', label: 'Messagerie', icon: MessageSquare },
  { to: '/agenda', label: 'Agenda', icon: CalendarDays },
  { to: '/formations', label: 'Formations', icon: GraduationCap },
  { to: '/actualites', label: 'Actualités', icon: Newspaper },
  { to: '/administration', label: 'Administration', icon: Briefcase, staffOnly: true },
]
