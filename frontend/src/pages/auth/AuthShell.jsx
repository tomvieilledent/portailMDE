/** Cadre commun des pages d'authentification. */

import { Link } from 'react-router-dom'

import LegalLinks from '../../components/LegalLinks'
import { useDocumentTitle } from '../../lib/useDocumentTitle'

/** Cadre commun des pages de connexion / mot de passe. */
export default function AuthShell({ title, subtitle, children }) {
  useDocumentTitle(title)
  return (
    <main
      className="relative flex min-h-screen items-center justify-center bg-[#1a3a2a] bg-cover bg-center p-4"
      style={{ backgroundImage: 'url(/1920.webp)' }}
    >
      <div className="absolute inset-0 bg-gradient-to-b from-black/60 via-black/50 to-black/75" />
      <div className="relative z-10 w-full max-w-xl space-y-6">
        <div className="space-y-5 rounded-md border border-white/30 bg-white/15 p-10 text-white shadow-xl backdrop-blur-xl [&_a]:text-white [&_label]:text-white [&_p]:text-white/80">
          <Link to="/" className="flex justify-center">
            <img src="/logo-rodez-sombre.png" alt="Rodez Agglomération" className="h-20 w-auto" />
          </Link>
          <div>
            <p className="mb-2 text-sm font-semibold text-[#7ec843]">Portail MDE</p>
            <h1 className="font-display text-3xl font-bold">{title}</h1>
            {subtitle && <p className="mt-1 text-sm">{subtitle}</p>}
          </div>
          {children}
        </div>
        <LegalLinks className="text-xs text-white/70" />
      </div>
    </main>
  )
}
