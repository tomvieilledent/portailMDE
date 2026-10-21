/** Structure des pages connectées : menu latéral, tiroir mobile et en-tête. */

import { Menu, Moon, Sun, X } from 'lucide-react'
import { useState } from 'react'
import { NavLink, Outlet } from 'react-router-dom'

import { cn } from '../../lib/cn'
import { navItems } from '../../navigation'
import { useTheme } from '../ThemeProvider'

/** Liste des liens du menu principal. */
function NavList({ items, onNavigate }) {
  return (
    <nav aria-label="Navigation principale" className="flex flex-col gap-1">
      {items.map(({ to, label, icon: Icon }) => (
        <NavLink
          key={to}
          to={to}
          onClick={onNavigate}
          className={({ isActive }) =>
            cn(
              'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition',
              isActive
                ? 'bg-brand-700 text-white'
                : 'text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800',
            )
          }
        >
          <Icon size={18} aria-hidden="true" />
          {label}
        </NavLink>
      ))}
    </nav>
  )
}

/**
 * Structure des pages connectées : barre latérale (bureau), tiroir (mobile) et en-tête.
 * `items` : entrées de menu déjà filtrées selon les droits ; `actions` : zone à droite de l'en-tête.
 */
export default function AppLayout({ items = navItems, actions = null }) {
  const [open, setOpen] = useState(false)
  const { theme, toggle } = useTheme()

  return (
    <div className="min-h-screen lg:grid lg:grid-cols-[16rem_1fr]">
      <aside className="hidden border-r border-slate-200 bg-white p-4 lg:block dark:border-slate-800 dark:bg-slate-900">
        <p className="text-brand-700 dark:text-brand-300 mb-6 px-3 text-xl font-bold">portailMDE</p>
        <NavList items={items} />
      </aside>

      {open && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <div
            className="absolute inset-0 bg-slate-900/50"
            onClick={() => setOpen(false)}
            aria-hidden="true"
          />
          <aside className="absolute inset-y-0 left-0 w-64 bg-white p-4 shadow-xl dark:bg-slate-900">
            <div className="mb-6 flex items-center justify-between px-3">
              <p className="text-brand-700 dark:text-brand-300 text-xl font-bold">portailMDE</p>
              <button type="button" aria-label="Fermer le menu" onClick={() => setOpen(false)}>
                <X size={20} />
              </button>
            </div>
            <NavList items={items} onNavigate={() => setOpen(false)} />
          </aside>
        </div>
      )}

      <div className="flex min-w-0 flex-col">
        <header className="sticky top-0 z-30 flex items-center gap-3 border-b border-slate-200 bg-white/80 px-4 py-3 backdrop-blur dark:border-slate-800 dark:bg-slate-900/80">
          <button
            type="button"
            className="rounded-lg p-2 hover:bg-slate-100 lg:hidden dark:hover:bg-slate-800"
            aria-label="Ouvrir le menu"
            onClick={() => setOpen(true)}
          >
            <Menu size={20} />
          </button>
          <div className="ml-auto flex items-center gap-2">
            {actions}
            <button
              type="button"
              onClick={toggle}
              aria-label={theme === 'dark' ? 'Passer en mode clair' : 'Passer en mode sombre'}
              className="rounded-lg p-2 hover:bg-slate-100 dark:hover:bg-slate-800"
            >
              {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
            </button>
          </div>
        </header>
        <main className="mx-auto w-full max-w-6xl flex-1 p-4 sm:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
