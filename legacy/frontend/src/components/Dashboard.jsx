import React, { useState, useEffect, useMemo, useRef, useCallback } from 'react'
import { useAuth, displayName } from '../context/AuthContext'
import { connectSocket } from '../lib/socket'
import { api, mediaUrl } from '../lib/api'
import Header from './Header'
import TabNavigation from './TabNavigation'
import Companies from './pages/Companies'
import Users from './pages/Users'
import Trainings from './pages/Trainings'
import News from './pages/News'
import DashboardPage from './pages/DashboardPage'
import MonOnglet from './pages/MonOnglet'
import MonEntreprise from './pages/MonEntreprise'
import Messagerie from './Messagerie'
import LandingPage from './pages/LandingPage'
import GestionPage from './pages/GestionPage'
import ResetPasswordModal from './modals/ResetPasswordModal'

// Ordre des onglets identique pour tous les rôles ; seul le dernier onglet
// (spécifique au rôle) diffère : Gestion pour l'admin, Mon entreprise pour le
// patron, rien de plus pour le salarié.
const COMMON_TABS = [
  { id: 'dashboard',  label: 'Accueil' },
  { id: 'companies',  label: 'Entreprises' },
  { id: 'users',      label: 'Trombinoscope' },
  { id: 'trainings',  label: 'Formations / Ateliers' },
  { id: 'news',       label: 'Veille économique' },
]

const ADMIN_TABS = [...COMMON_TABS, { id: 'gestion', label: 'Gestion' }]
const PATRON_TABS = [...COMMON_TABS, { id: 'monentreprise', label: 'Mon entreprise' }]
const SALARIE_TABS = COMMON_TABS

// Droits de gestion ouvrant l'onglet « Gestion » à un membre du staff.
const STAFF_PERMS = ['manage_companies', 'manage_users', 'manage_trainings', 'manage_news']

function getTabsForRole(role, can = () => false, companyName = null) {
  const administersCompany = !!companyName
  // L'onglet « Mon entreprise » porte le nom de l'entreprise administrée.
  const companyLabel = companyName || 'Mon entreprise'
  let tabs
  if (role === 'admin')  tabs = ADMIN_TABS
  else if (role === 'patron') tabs = PATRON_TABS
  // Un membre du staff disposant d'au moins un droit de gestion accède aussi
  // à l'onglet « Gestion » (les sous-onglets y sont filtrés par droit).
  else if (STAFF_PERMS.some((p) => can(p))) tabs = ADMIN_TABS
  else tabs = SALARIE_TABS
  // Renomme l'onglet « Mon entreprise » présent dans PATRON_TABS.
  tabs = tabs.map((t) => (t.id === 'monentreprise' ? { ...t, label: companyLabel } : t))
  // Cumul des rôles : un utilisateur qui administre une entreprise (y compris
  // un super admin) voit aussi cet onglet, en plus de ses autres onglets.
  if (administersCompany && !tabs.some((t) => t.id === 'monentreprise')) {
    const companyTab = { id: 'monentreprise', label: companyLabel }
    // « Gestion » reste le dernier onglet : on insère l'entreprise juste avant.
    const gestionIdx = tabs.findIndex((t) => t.id === 'gestion')
    if (gestionIdx === -1) {
      tabs = [...tabs, companyTab]
    } else {
      tabs = [...tabs.slice(0, gestionIdx), companyTab, ...tabs.slice(gestionIdx)]
    }
  }
  return tabs
}

// Construit l'objet `profile` attendu par le Header / les pages à partir de
// l'utilisateur authentifié. Les champs cosmétiques absents du backend
// (company, bio) sont laissés vides en attendant leur câblage.
function profileFromUser(user, role) {
  if (!user) return null
  return {
    id: user.id,
    name: displayName(user),
    firstName: user.first_name || '',
    lastName: user.last_name || '',
    jobTitle: user.job_title || '',
    email: user.email,
    phone: user.phone || '',
    company: '',
    isSuperAdmin: !!user.is_super_admin,
    photo: mediaUrl(user.profile_picture) || null,
    businessCard: mediaUrl(user.business_card) || null,
    role,
  }
}

export default function DashboardContainer() {
  const { user, role, can, companyAdminId, companyAdminName, isAuthenticated, loading, logout, updateProfile } = useAuth()
  const [profileOverride, setProfileOverride] = useState(null)
  const [activeTab, setActiveTab] = useState('dashboard')
  // Jeton de réinitialisation de mot de passe passé dans l'URL (lien email).
  const [resetToken, setResetToken] = useState(() => {
    if (typeof window === 'undefined') return null
    return new URLSearchParams(window.location.search).get('reset_token')
  })
  const clearResetToken = useCallback(() => {
    setResetToken(null)
    if (typeof window !== 'undefined') {
      const url = new URL(window.location.href)
      url.searchParams.delete('reset_token')
      window.history.replaceState({}, '', url.pathname + url.search)
    }
  }, [])
  const [messagingOpen, setMessagingOpen] = useState(false)
  const [messagingContact, setMessagingContact] = useState(null)
  const [darkMode, setDarkMode] = useState(
    () => localStorage.getItem('darkMode') === 'true'
  )
  const [unreadCount, setUnreadCount] = useState(0)

  // Profil effectif = données backend + modifications locales non encore
  // persistées (l'édition de profil sera câblée à une étape ultérieure).
  const profile = useMemo(() => {
    const base = profileFromUser(user, role)
    return base ? { ...base, ...(profileOverride || {}) } : null
  }, [user, role, profileOverride])

  useEffect(() => {
    document.documentElement.classList.toggle('dark', darkMode)
    localStorage.setItem('darkMode', String(darkMode))
  }, [darkMode])

  // Réinitialise l'onglet et les surcharges de profil à chaque (dé)connexion.
  useEffect(() => {
    setActiveTab('dashboard')
    setProfileOverride(null)
  }, [user?.id])

  // Notification globale de réception : le composant Messagerie n'est monté que
  // lorsque le panneau est ouvert, donc on écoute aussi `new_message` ici
  // (toujours monté) pour incrémenter le badge + jouer le son même panneau
  // fermé. On ignore quand le panneau est ouvert (Messagerie gère alors ses
  // propres badges par contact). Un ref évite de se réabonner à chaque toggle.
  const messagingOpenRef = useRef(messagingOpen)
  useEffect(() => { messagingOpenRef.current = messagingOpen }, [messagingOpen])

  useEffect(() => {
    const myId = user?.id
    if (!myId) return
    const socket = connectSocket()
    if (!socket) return
    const onNew = ({ message }) => {
      if (!message || message.author_id === myId) return
      // DM qui m'est adressé OU message de groupe (room rejointe à la
      // connexion). On ne notifie que lorsque le panneau est fermé.
      const forMe = message.conversation_id ? true : message.recipient_id === myId
      if (!forMe) return
      if (!messagingOpenRef.current) {
        setUnreadCount((n) => n + 1)
        setMsgToast(message.content ? `📨 ${message.content}` : '📨 Nouveau message reçu')
      }
    }
    socket.on('new_message', onNew)
    return () => { socket.off('new_message', onNew) }
  }, [user?.id])

  // Toast de réception (auto-disparition au bout de 5 s).
  const [msgToast, setMsgToast] = useState(null)
  useEffect(() => {
    if (!msgToast) return
    const t = setTimeout(() => setMsgToast(null), 5000)
    return () => clearTimeout(t)
  }, [msgToast])

  // Stable identity so Messagerie's socket effect doesn't re-subscribe (and
  // briefly drop its listeners) on every Dashboard re-render.
  const handleIncomingMessage = useCallback(() => setUnreadCount((n) => n + 1), [])

  const handleLogout = () => { logout() }

  // Sauvegarde du profil (persistée via PATCH /users/me) + désactivation de
  // son propre compte (puis déconnexion).
  const handleProfileSave = async (formData) => { await updateProfile(formData) }
  const handleDeactivateAccount = async () => {
    if (user?.id) await api.deactivateUser(user.id)
    logout()
  }

  const handleContact = (contactName) => {
    setMessagingContact(contactName)
    setMessagingOpen(true)
  }

  const handleCloseMessaging = () => {
    setMessagingOpen(false)
    setMessagingContact(null)
  }

  const renderPage = () => {
    switch (activeTab) {
      case 'dashboard':     return <DashboardPage />
      case 'companies':     return <Companies isAdmin={role === 'admin' || can('manage_companies')} />
      case 'monentreprise': return <MonEntreprise />
      case 'users':         return <Users onContact={handleContact} role={role} canManage={role === 'admin' || can('manage_users')} profile={profile} />
      case 'trainings':     return <Trainings isAdmin={role === 'admin' || can('manage_trainings')} profile={profile} />
      case 'news':          return <News />
      case 'gestion':       return <GestionPage />
      case 'mononglet':     return <MonOnglet />
      default:              return <DashboardPage />
    }
  }

  // Lien de réinitialisation ouvert depuis l'email : on affiche le formulaire
  // par-dessus la landing, quel que soit l'état d'authentification.
  if (resetToken) {
    return (
      <div className="min-h-screen bg-gray-50">
        <LandingPage onLoginSuccess={() => {}} />
        <ResetPasswordModal token={resetToken} onDone={clearResetToken} />
      </div>
    )
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="w-8 h-8 border-2 border-primary-light border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  if (!isAuthenticated) {
    // La connexion est gérée par le contexte ; on ferme simplement la landing.
    return <LandingPage onLoginSuccess={() => {}} />
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header
        role={role}
        isLoggedIn={isAuthenticated}
        profile={profile}
        onProfileSave={handleProfileSave}
        onDeactivateAccount={handleDeactivateAccount}
        onLogout={handleLogout}
        onOpenMessaging={() => { setMessagingContact(null); setMessagingOpen(true); setUnreadCount(0); setMsgToast(null) }}
        unreadCount={unreadCount}
        darkMode={darkMode}
        onToggleDark={() => setDarkMode((d) => !d)}
      />
      <TabNavigation tabs={getTabsForRole(role, can, companyAdminName)} activeTab={activeTab} setActiveTab={setActiveTab} />
      <main className="max-w-7xl mx-auto px-4 py-8">
        {renderPage()}
      </main>
      {messagingOpen && (
        <Messagerie
          onClose={handleCloseMessaging}
          initialContact={messagingContact}
          onNewMessage={handleIncomingMessage}
        />
      )}

      {/* Notification de réception (panneau fermé) — cliquable pour ouvrir le chat */}
      {msgToast && !messagingOpen && (
        <button
          onClick={() => { setMessagingContact(null); setMessagingOpen(true); setUnreadCount(0); setMsgToast(null) }}
          className="fixed bottom-6 right-6 z-50 max-w-xs flex items-center gap-3 bg-gray-900 text-white text-sm font-medium pl-4 pr-5 py-3 rounded-xl shadow-lg hover:bg-gray-800 transition-colors animate-fade-in text-left"
        >
          <span className="truncate">{msgToast}</span>
        </button>
      )}
    </div>
  )
}
