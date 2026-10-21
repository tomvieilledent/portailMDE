import { Moon, Sun } from 'lucide-react'

import { useTheme } from '../components/ThemeProvider'

export default function HomePage() {
  const { theme, toggle } = useTheme()
  return (
    <main className="mx-auto flex min-h-screen max-w-3xl flex-col items-center justify-center gap-6 p-6 text-center">
      <h1 className="text-4xl font-bold text-brand-700 dark:text-brand-300">portailMDE</h1>
      <p className="text-slate-600 dark:text-slate-400">
        Le portail des entreprises de la pépinière : annuaire, messagerie, événements et formations.
      </p>
      <button
        type="button"
        onClick={toggle}
        className="inline-flex items-center gap-2 rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium hover:bg-slate-100 dark:border-slate-700 dark:hover:bg-slate-800"
      >
        {theme === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
        {theme === 'dark' ? 'Mode clair' : 'Mode sombre'}
      </button>
    </main>
  )
}
