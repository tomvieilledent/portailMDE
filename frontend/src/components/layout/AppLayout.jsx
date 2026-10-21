/** Structure des pages connectées : menu latéral, tiroir mobile et en-tête. */

import { Menu, Moon, Sun, X } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { NavLink, Outlet, useLocation } from 'react-router-dom'

import LegalLinks from '../LegalLinks'
import { cn } from '../../lib/cn'
import { navItems } from '../../navigation'
import { useTheme } from '../ThemeProvider'
import Logo from '../Logo'

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
  const { pathname } = useLocation()
  const mainRef = useRef(null)
  const firstRender = useRef(true)
  const menuButton = useRef(null)
  const closeButton = useRef(null)
  const drawerRef = useRef(null)

  // Titre de l'onglet et focus du <h1> à chaque changement de route (WCAG 2.4.2).
  useEffect(() => {
    const main = mainRef.current
    const isFirst = firstRender.current
    firstRender.current = false
    let observer = null
    const apply = () => {
      const heading = main?.querySelector('h1')
      if (!heading?.textContent) return false
      document.title = `${heading.textContent} – Maison de l'Économie`
      if (!isFirst) {
        heading.tabIndex = -1
        heading.focus({ preventScroll: false })
      }
      return true
    }
    if (!apply()) {
      document.title = "Maison de l'Économie"
      // Titre dépendant de données chargées : on attend l'apparition du <h1>.
      if (main) {
        observer = new MutationObserver(() => {
          if (apply()) observer.disconnect()
        })
        observer.observe(main, { childList: true, subtree: true, characterData: true })
      }
    }
    return () => observer?.disconnect()
  }, [pathname])

  // Tiroir mobile : focus à l'ouverture, Échap pour fermer, focus restauré à la fermeture.
  useEffect(() => {
    if (!open) return undefined
    const trigger = menuButton.current
    closeButton.current?.focus()
    const onKey = (event) => {
      if (event.key === 'Escape') {
        setOpen(false)
        return
      }
      if (event.key !== 'Tab') return
      const focusable = drawerRef.current?.querySelectorAll('a[href], button:not([disabled])')
      if (!focusable?.length) return
      const first = focusable[0]
      const last = focusable[focusable.length - 1]
      const active = document.activeElement
      if (!drawerRef.current.contains(active)) {
        event.preventDefault()
        first.focus()
      } else if (event.shiftKey && active === first) {
        event.preventDefault()
        last.focus()
      } else if (!event.shiftKey && active === last) {
        event.preventDefault()
        first.focus()
      }
    }
    document.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('keydown', onKey)
      trigger?.focus()
    }
  }, [open])

  return (
    <div className="min-h-screen lg:grid lg:grid-cols-[16rem_1fr]">
      <a
        href="#contenu"
        className="focus:bg-brand-700 sr-only focus:not-sr-only focus:fixed focus:top-2 focus:left-2 focus:z-[70] focus:rounded-lg focus:px-4 focus:py-2 focus:text-white"
      >
        Aller au contenu
      </a>
      <aside className="hidden border-r border-slate-200 bg-white p-4 lg:block dark:border-slate-800 dark:bg-slate-900">
        <div className="mb-6 space-y-2 px-3">
          <Logo />
          <p className="text-brand-700 dark:text-brand-300 text-xl font-bold">
            Maison de l'Économie
          </p>
        </div>
        <NavList items={items} />
      </aside>

      {open && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <div
            className="absolute inset-0 bg-slate-900/50"
            onClick={() => setOpen(false)}
            aria-hidden="true"
          />
          <aside
            ref={drawerRef}
            role="dialog"
            aria-modal="true"
            aria-label="Menu"
            className="absolute inset-y-0 left-0 w-64 bg-white p-4 shadow-xl dark:bg-slate-900"
          >
            <div className="mb-6 flex items-center justify-between px-3">
              <div className="space-y-2">
                <Logo />
                <p className="text-brand-700 dark:text-brand-300 text-xl font-bold">
                  Maison de l'Économie
                </p>
              </div>
              <button
                ref={closeButton}
                type="button"
                aria-label="Fermer le menu"
                onClick={() => setOpen(false)}
              >
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
            ref={menuButton}
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
        <main id="contenu" ref={mainRef} className="mx-auto w-full max-w-6xl flex-1 p-4 sm:p-6">
          <Outlet />
        </main>
        <footer className="border-t border-slate-200 py-4 text-xs text-slate-500 dark:border-slate-800">
          <LegalLinks />
        </footer>
      </div>
    </div>
  )
}
