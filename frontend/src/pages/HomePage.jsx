/** Page d'accueil des visiteurs (photo plein écran, dispositifs et accès au portail). */

import { Key, Lightbulb, LogIn, Mail, Moon, Sun, TrendingUp } from 'lucide-react'
import { Link } from 'react-router-dom'

import LegalLinks from '../components/LegalLinks'
import { useTheme } from '../components/ThemeProvider'
import { useLanding } from '../features/landing/useLanding'
import { useDocumentTitle } from '../lib/useDocumentTitle'

// Les icônes sont associées aux cartes par position (seul le texte est éditable).
const icons = [
  { Icon: Lightbulb, color: 'text-brand-400' },
  { Icon: TrendingUp, color: 'text-green-300' },
  { Icon: Key, color: 'text-blue-300' },
]

/** Page d'accueil : contenu éditorial et accès rapides. */
export default function HomePage() {
  const { content } = useLanding()
  const { theme, toggle } = useTheme()
  useDocumentTitle('Accueil')

  return (
    <div
      className="relative flex min-h-screen flex-col overflow-hidden bg-cover bg-center"
      style={{ backgroundImage: 'url(/1920.webp)', backgroundColor: '#1a3a2a' }}
    >
      <div
        className="absolute inset-0 bg-gradient-to-b from-black/60 via-black/50 to-black/75"
        aria-hidden="true"
      />

      <header className="relative z-10 flex items-center justify-between gap-4 px-8 py-6">
        <div className="flex items-center gap-4">
          <img
            src="/logo-rodez.png"
            alt="Rodez Agglomération"
            className="h-14 w-auto rounded-lg bg-white px-2 py-1.5 shadow-md"
          />
        </div>
        <button
          type="button"
          onClick={toggle}
          aria-label={theme === 'dark' ? 'Passer en mode clair' : 'Passer en mode sombre'}
          className="rounded-lg p-2 text-white hover:bg-white/10"
        >
          {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
        </button>
      </header>

      <main className="relative z-10 flex flex-1 flex-col items-center justify-center px-6 py-8">
        <div className="mb-10 text-center">
          <h1 className="text-4xl leading-tight font-bold text-white drop-shadow-lg md:text-5xl">
            {content.slogan}
          </h1>
          {content.subtitle && (
            <p className="mx-auto mt-4 max-w-xl text-base leading-relaxed text-white/80">
              {content.subtitle}
            </p>
          )}
        </div>

        <section
          aria-label="Nos dispositifs"
          className="mb-4 grid w-full max-w-5xl grid-cols-1 gap-4 md:grid-cols-3"
        >
          {content.sections.map((section, index) => {
            const { Icon, color } = icons[index % icons.length]
            return (
              <div
                key={section.title}
                className="flex flex-col gap-3 rounded-2xl border border-white/30 bg-white/10 p-5 text-white backdrop-blur-sm"
              >
                <div className="flex items-center gap-2">
                  <Icon size={20} className={color} aria-hidden="true" />
                  <div>
                    <h2 className="text-base leading-tight font-bold">{section.title}</h2>
                    {section.duration && (
                      <p className="text-xs text-white/70">{section.duration}</p>
                    )}
                  </div>
                </div>
                <p className="flex-1 text-sm leading-relaxed text-white/90">
                  {section.description}
                </p>
                {section.highlight && (
                  <p className="text-brand-300 border-t border-white/10 pt-3 text-xs font-semibold">
                    {section.highlight}
                  </p>
                )}
              </div>
            )
          })}
        </section>
      </main>

      <div className="relative z-10 flex justify-center gap-4 pb-6">
        <Link
          to="/mentions-legales"
          className="flex items-center gap-2 rounded-full border-2 border-white/60 px-7 py-3.5 text-sm font-semibold text-white backdrop-blur-sm transition-colors hover:bg-white/10"
        >
          <Mail size={17} aria-hidden="true" />
          Contact
        </Link>
        <Link
          to="/connexion"
          className="bg-brand-600 hover:bg-brand-700 shadow-brand-400/30 flex items-center gap-2 rounded-full px-7 py-3.5 text-sm font-semibold text-white shadow-lg transition-colors"
        >
          <LogIn size={17} aria-hidden="true" />
          Se connecter
        </Link>
      </div>

      <footer className="relative z-10 pb-6 text-center text-sm text-white/70">
        <LegalLinks className="mb-2 text-white/80" />© {new Date().getFullYear()} Maison de
        l'Entreprise
      </footer>
    </div>
  )
}
