import { NavLink, Navigate, Route, Routes } from 'react-router-dom'

import { useAuth } from '../../auth/AuthProvider'
import { PERMISSIONS, hasPermission } from '../../auth/permissions'
import PageHeader from '../../components/layout/PageHeader'
import { cn } from '../../lib/cn'
import CompaniesAdmin from './CompaniesAdmin'
import ContentAdmin from './ContentAdmin'
import UsersAdmin from './UsersAdmin'

const SECTIONS = [
  {
    path: 'utilisateurs',
    label: 'Utilisateurs',
    permission: PERMISSIONS.MANAGE_USERS,
    element: <UsersAdmin />,
  },
  {
    path: 'entreprises',
    label: 'Entreprises',
    permission: PERMISSIONS.MANAGE_COMPANIES,
    element: <CompaniesAdmin />,
  },
  {
    path: 'contenu',
    label: 'Contenu',
    permission: PERMISSIONS.MANAGE_NEWS,
    element: <ContentAdmin />,
  },
]

/** Espace d'administration : une section par droit détenu. */
export default function AdminPage() {
  const { user } = useAuth()
  const allowed = SECTIONS.filter((s) => hasPermission(user, s.permission))

  return (
    <>
      <PageHeader title="Administration" />
      {allowed.length === 0 ? (
        <p className="text-slate-600 dark:text-slate-400">
          Aucun droit d'administration ne vous est attribué. Les formations et l'agenda se gèrent
          depuis leurs pages.
        </p>
      ) : (
        <>
          <nav
            aria-label="Administration"
            className="mb-6 flex gap-2 border-b border-slate-200 dark:border-slate-800"
          >
            {allowed.map(({ path, label }) => (
              <NavLink
                key={path}
                to={path}
                className={({ isActive }) =>
                  cn(
                    '-mb-px border-b-2 px-4 py-2 text-sm font-medium',
                    isActive
                      ? 'border-brand-700 text-brand-700 dark:border-brand-300 dark:text-brand-300'
                      : 'border-transparent text-slate-500 hover:text-slate-700',
                  )
                }
              >
                {label}
              </NavLink>
            ))}
          </nav>
          <Routes>
            {allowed.map(({ path, element }) => (
              <Route key={path} path={path} element={element} />
            ))}
            <Route path="*" element={<Navigate to={allowed[0].path} replace />} />
          </Routes>
        </>
      )}
    </>
  )
}
