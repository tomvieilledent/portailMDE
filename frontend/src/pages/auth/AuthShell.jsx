/** Cadre commun des pages d'authentification. */

import { Link } from 'react-router-dom'

import LegalLinks from '../../components/LegalLinks'
import { Card } from '../../components/ui'
import { useDocumentTitle } from '../../lib/useDocumentTitle'
import Logo from '../../components/Logo'

/** Cadre commun des pages de connexion / mot de passe. */
export default function AuthShell({ title, subtitle, children }) {
  useDocumentTitle(title)
  return (
    <main className="flex min-h-screen items-center justify-center p-4">
      <div className="w-full max-w-md space-y-6">
        <Link
          to="/"
          className="text-brand-700 dark:text-brand-300 flex flex-col items-center gap-2 text-center text-2xl font-bold"
        >
          <Logo className="h-14" />
          portailMDE
        </Link>
        <Card className="space-y-5">
          <div>
            <h1 className="text-xl font-semibold">{title}</h1>
            {subtitle && (
              <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">{subtitle}</p>
            )}
          </div>
          {children}
        </Card>
        <LegalLinks className="text-xs text-slate-500" />
      </div>
    </main>
  )
}
