import { ArrowRight, Building2, Moon, Rocket, Sprout, Sun } from 'lucide-react'
import { Link } from 'react-router-dom'

import { useTheme } from '../components/ThemeProvider'
import { Card } from '../components/ui'
import { useLanding } from '../features/landing/useLanding'

// Les icônes sont associées aux cartes par position (seul le texte est éditable).
const icons = [Rocket, Sprout, Building2]

export default function HomePage() {
  const { content } = useLanding()
  const { theme, toggle } = useTheme()

  return (
    <div className="min-h-screen">
      <header className="mx-auto flex max-w-6xl items-center justify-between p-4">
        <span className="text-brand-700 dark:text-brand-300 text-xl font-bold">portailMDE</span>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={toggle}
            aria-label={theme === 'dark' ? 'Passer en mode clair' : 'Passer en mode sombre'}
            className="rounded-lg p-2 hover:bg-slate-100 dark:hover:bg-slate-800"
          >
            {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
          </button>
          <Link
            to="/connexion"
            className="bg-brand-700 hover:bg-brand-800 rounded-lg px-4 py-2 text-sm font-medium text-white"
          >
            Se connecter
          </Link>
        </div>
      </header>

      <main>
        <section className="from-brand-50 dark:from-brand-900/30 bg-gradient-to-b to-transparent px-4 py-16 text-center sm:py-24">
          <div className="mx-auto max-w-3xl space-y-6">
            <h1 className="text-brand-800 dark:text-brand-200 text-4xl font-bold tracking-tight sm:text-5xl">
              {content.slogan}
            </h1>
            <p className="text-lg text-slate-600 dark:text-slate-400">{content.subtitle}</p>
            <Link
              to="/connexion"
              className="bg-brand-700 hover:bg-brand-800 inline-flex items-center gap-2 rounded-lg px-6 py-3 font-medium text-white"
            >
              Accéder au portail <ArrowRight size={18} aria-hidden="true" />
            </Link>
          </div>
        </section>

        <section aria-label="Nos dispositifs" className="mx-auto max-w-6xl px-4 pb-20">
          <div className="grid gap-6 md:grid-cols-3">
            {content.sections.map((section, index) => {
              const Icon = icons[index % icons.length]
              return (
                <Card key={section.title} className="flex flex-col gap-3">
                  <Icon
                    className="text-brand-600 dark:text-brand-300"
                    size={28}
                    aria-hidden="true"
                  />
                  <h2 className="text-xl font-semibold">{section.title}</h2>
                  <p className="text-brand-700 dark:text-brand-300 text-sm font-medium">
                    {section.duration}
                  </p>
                  <p className="text-sm text-slate-600 dark:text-slate-400">
                    {section.description}
                  </p>
                  {section.highlight && (
                    <p className="mt-auto border-t border-slate-200 pt-3 text-sm italic dark:border-slate-800">
                      {section.highlight}
                    </p>
                  )}
                </Card>
              )
            })}
          </div>
        </section>
      </main>

      <footer className="border-t border-slate-200 py-6 text-center text-sm text-slate-500 dark:border-slate-800">
        © {new Date().getFullYear()} Maison de l'Entreprise
      </footer>
    </div>
  )
}
