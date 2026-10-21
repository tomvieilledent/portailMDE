import { Navigate, Route, Routes } from 'react-router-dom'

import { useAuth } from './auth/AuthProvider'
import RequireAuth from './auth/RequireAuth'
import { isStaff } from './auth/permissions'
import AppLayout from './components/layout/AppLayout'
import UserMenu from './components/layout/UserMenu'
import { navItems } from './navigation'
import MyCompanyPage from './features/company/MyCompanyPage'
import ProfilePage from './features/profile/ProfilePage'
import CompaniesPage from './features/directory/CompaniesPage'
import CompanyPage from './features/directory/CompanyPage'
import AgendaPage from './features/agenda/AgendaPage'
import MessagingPage from './features/messaging/MessagingPage'
import PeoplePage from './features/directory/PeoplePage'
import ComingSoonPage from './pages/ComingSoonPage'
import HomePage from './pages/HomePage'
import NotFoundPage from './pages/NotFoundPage'
import RealtimeEffects from './realtime/RealtimeEffects'
import { RealtimeProvider } from './realtime/RealtimeProvider'
import ForgotPasswordPage from './pages/auth/ForgotPasswordPage'
import LoginPage from './pages/auth/LoginPage'
import ResetPasswordPage from './pages/auth/ResetPasswordPage'

function Shell() {
  const { user } = useAuth()
  const items = navItems.filter(
    (item) => (!item.staffOnly || isStaff(user)) && (!item.needsCompany || user.company_id),
  )
  return (
    <RealtimeProvider>
      <RealtimeEffects />
      <AppLayout items={items} actions={<UserMenu />} />
    </RealtimeProvider>
  )
}

export default function App() {
  const { user } = useAuth()
  return (
    <Routes>
      <Route path="/" element={user ? <Navigate to="/annuaire" replace /> : <HomePage />} />
      <Route path="/connexion" element={<LoginPage />} />
      <Route path="/mot-de-passe-oublie" element={<ForgotPasswordPage />} />
      <Route path="/reset-password" element={<ResetPasswordPage />} />
      <Route element={<RequireAuth />}>
        <Route element={<Shell />}>
          <Route path="/annuaire" element={<PeoplePage />} />
          <Route path="/messagerie" element={<MessagingPage />} />
          <Route path="/messagerie/:conversationId" element={<MessagingPage />} />
          <Route path="/agenda" element={<AgendaPage />} />
          <Route path="/profil" element={<ProfilePage />} />
          <Route path="/mon-entreprise" element={<MyCompanyPage />} />
          <Route path="/entreprises" element={<CompaniesPage />} />
          <Route path="/entreprises/:companyId" element={<CompanyPage />} />
          {navItems
            .filter(
              (item) =>
                !item.staffOnly &&
                ![
                  '/annuaire',
                  '/entreprises',
                  '/mon-entreprise',
                  '/messagerie',
                  '/agenda',
                ].includes(item.to),
            )
            .map(({ to, label }) => (
              <Route key={to} path={to} element={<ComingSoonPage title={label} />} />
            ))}
        </Route>
      </Route>
      <Route element={<RequireAuth staffOnly />}>
        <Route element={<Shell />}>
          <Route path="/administration" element={<ComingSoonPage title="Administration" />} />
        </Route>
      </Route>
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  )
}
