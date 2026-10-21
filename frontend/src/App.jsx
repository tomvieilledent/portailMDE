/** Routage de l'application : routes publiques (connexion, mot de passe) et pages protégées par rôle. */

import { lazy, Suspense } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'

import { useAuth } from './auth/AuthProvider'
import RequireAuth from './auth/RequireAuth'
import { isStaff } from './auth/permissions'
import AppLayout from './components/layout/AppLayout'
import UserMenu from './components/layout/UserMenu'
import { navItems } from './navigation'
import { useCompany } from './features/directory/queries'
import NotificationsBell from './features/notifications/NotificationsBell'
import PeoplePage from './features/directory/PeoplePage'
import HomePage from './pages/HomePage'
import NotFoundPage from './pages/NotFoundPage'
import RealtimeEffects from './realtime/RealtimeEffects'
import { RealtimeProvider } from './realtime/RealtimeProvider'
import ChangePasswordPage from './pages/auth/ChangePasswordPage'
import { LegalNoticePage, PrivacyPage } from './pages/LegalPages'
import ForgotPasswordPage from './pages/auth/ForgotPasswordPage'
import LoginPage from './pages/auth/LoginPage'
import ResetPasswordPage from './pages/auth/ResetPasswordPage'

const MyCompanyPage = lazy(() => import('./features/company/MyCompanyPage'))
const DashboardPage = lazy(() => import('./features/home/DashboardPage'))
const ProfilePage = lazy(() => import('./features/profile/ProfilePage'))
const CompaniesPage = lazy(() => import('./features/directory/CompaniesPage'))
const CompanyPage = lazy(() => import('./features/directory/CompanyPage'))
const AdminPage = lazy(() => import('./features/admin/AdminPage'))
const AgendaPage = lazy(() => import('./features/agenda/AgendaPage'))
const MessagingPage = lazy(() => import('./features/messaging/MessagingPage'))
const TrainingPage = lazy(() => import('./features/trainings/TrainingPage'))
const TrainingsPage = lazy(() => import('./features/trainings/TrainingsPage'))
const NewsPage = lazy(() => import('./features/news/NewsPage'))

/** Structure commune des pages connectées, avec menu filtré selon les droits de l'utilisateur. */
function Shell() {
  const { user } = useAuth()
  const company = useCompany(user.is_company_admin ? user.company_id : null)
  const items = navItems
    .filter(
      (item) =>
        (!item.staffOnly || isStaff(user)) &&
        (!item.needsCompany || user.company_id) &&
        (!item.companyAdminOnly || (user.is_company_admin && user.company_id)),
    )
    // L'entrée d'administration de l'entreprise affiche son logo, à défaut l'icône par défaut.
    .map((item) =>
      item.companyAdminOnly && company.data?.logo_path
        ? { ...item, logoPath: company.data.logo_path }
        : item,
    )
  return (
    <RealtimeProvider>
      <RealtimeEffects />
      <AppLayout
        items={items}
        actions={
          <>
            <NotificationsBell />
            <UserMenu />
          </>
        }
      />
    </RealtimeProvider>
  )
}

/** Déclaration des routes de l'application. */
export default function App() {
  const { user } = useAuth()
  return (
    <Suspense fallback={null}>
      <Routes>
        <Route path="/" element={user ? <Navigate to="/accueil" replace /> : <HomePage />} />
        <Route path="/mentions-legales" element={<LegalNoticePage />} />
        <Route path="/confidentialite" element={<PrivacyPage />} />
        <Route path="/connexion" element={<LoginPage />} />
        <Route path="/mot-de-passe-oublie" element={<ForgotPasswordPage />} />
        <Route path="/reset-password" element={<ResetPasswordPage />} />
        <Route element={<RequireAuth allowPending />}>
          <Route path="/changer-mot-de-passe" element={<ChangePasswordPage />} />
        </Route>
        <Route element={<RequireAuth />}>
          <Route element={<Shell />}>
            <Route path="/accueil" element={<DashboardPage />} />
            <Route path="/annuaire" element={<PeoplePage />} />
            <Route path="/messagerie" element={<MessagingPage />} />
            <Route path="/messagerie/:conversationId" element={<MessagingPage />} />
            <Route path="/agenda" element={<AgendaPage />} />
            <Route path="/formations" element={<TrainingsPage />} />
            <Route path="/formations/:trainingId" element={<TrainingPage />} />
            <Route path="/actualites" element={<NewsPage />} />
            <Route path="/profil" element={<ProfilePage />} />
            <Route path="/entreprises" element={<CompaniesPage />} />
            <Route path="/entreprises/:companyId" element={<CompanyPage />} />
          </Route>
        </Route>
        <Route element={<RequireAuth companyAdmin />}>
          <Route element={<Shell />}>
            <Route path="/mon-entreprise/administration" element={<MyCompanyPage manage />} />
          </Route>
        </Route>
        <Route element={<RequireAuth staffOnly />}>
          <Route element={<Shell />}>
            <Route path="/administration/*" element={<AdminPage />} />
          </Route>
        </Route>
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </Suspense>
  )
}
