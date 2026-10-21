/** Structure des pages connectées : menu latéral, tiroir mobile et en-tête. */

import { Menu, X } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { NavLink, Outlet, useLocation } from 'react-router-dom'

import LegalLinks from '../LegalLinks'
import { uploadUrl } from '../ui'
import Logo from '../Logo'
import { cn } from '../../lib/cn'
import { NAV_GROUPS, navItems } from '../../navigation'

/** Liste des liens du menu principal, regroupés par rubrique. */
function NavList({ items, onNavigate }) {
  const groups = Object.keys(NAV_GROUPS)
    .map((key) => ({ key, title: NAV_GROUPS[key], entries: items.filter((i) => i.group === key) }))
    .filter((g) => g.entries.length > 0)
  return (
    <nav aria-label="Navigation principale" className="flex flex-col gap-6">
      {groups.map(({ key, title, entries }) => (
        <div key={key} className="flex flex-col gap-0.5">
          {title && (
            <p className="mb-1 rounded-sm bg-black/30 px-3 py-1.5 text-sm font-bold text-white">
              {title}
            </p>
          )}
          {entries.map(({ to, label, logoPath }) => (
            <NavLink
              key={to}
              to={to}
              onClick={onNavigate}
              className={({ isActive }) =>
                cn(
                  'group relative flex items-center gap-3 rounded-sm px-3 py-2.5 text-[15px] font-medium transition',
                  isActive
                    ? 'bg-white/25 font-semibold text-white'
                    : 'text-white hover:bg-white/15',
                )
              }
            >
              {({ isActive }) => (
                <>
                  {isActive && (
                    <span
                      className="absolute top-1.5 bottom-1.5 left-0 w-[3px] rounded-full bg-[#7ec843]"
                      aria-hidden="true"
                    />
                  )}
                  {label}
                  {logoPath && (
                    <img
                      src={uploadUrl(logoPath)}
                      alt=""
                      className="ml-auto h-6 w-6 shrink-0 rounded-full object-cover"
                    />
                  )}
                </>
              )}
            </NavLink>
          ))}
        </div>
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
  const { pathname } = useLocation()
  const mainRef = useRef(null)
  const firstRender = useRef(true)
  const menuButton = useRef(null)
  const closeButton = useRef(null)
  const drawerRef = useRef(null)

  // Le shell est toujours en thème clair (cartes blanches sur verre) : on neutralise `dark`.
  useEffect(() => {
    const root = document.documentElement
    const wasDark = root.classList.contains('dark')
    root.classList.remove('dark')
    return () => root.classList.toggle('dark', wasDark)
  }, [])

  // Titre de l'onglet et focus du <h1> à chaque changement de route (WCAG 2.4.2).
  useEffect(() => {
    const main = mainRef.current
    const isFirst = firstRender.current
    firstRender.current = false
    let observer = null
    const apply = () => {
      const heading = main?.querySelector('h1')
      if (!heading?.textContent) return false
      document.title = `${heading.textContent} – portailMDE`
      if (!isFirst) {
        heading.tabIndex = -1
        heading.focus({ preventScroll: false })
      }
      return true
    }
    if (!apply()) {
      document.title = 'portailMDE'
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
    <div
      className="glass-app relative h-dvh overflow-hidden bg-[#1a3a2a] bg-cover bg-fixed bg-center text-white lg:grid lg:grid-cols-[17rem_1fr]"
      style={{ backgroundImage: 'url(/1920.webp)' }}
    >
      <div
        className="pointer-events-none fixed inset-0 bg-gradient-to-b from-black/30 via-black/20 to-black/45"
        aria-hidden="true"
      />
      <a
        href="#contenu"
        className="focus:bg-brand-700 sr-only focus:not-sr-only focus:fixed focus:top-2 focus:left-2 focus:z-[70] focus:rounded-lg focus:px-4 focus:py-2 focus:text-white"
      >
        Aller au contenu
      </a>
      <aside className="z-10 hidden h-full overflow-y-auto border-r border-white/15 bg-[#4a7a1a] p-5 lg:block">
        <div className="mb-8 flex justify-center rounded-md bg-white px-3 py-3">
          <Logo className="h-14" />
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
            className="absolute inset-y-0 left-0 w-72 overflow-y-auto bg-[#4a7a1a] p-5 shadow-xl"
          >
            <div className="mb-6 flex items-center justify-between px-3">
              <span className="rounded-md bg-white px-2 py-1.5">
                <Logo className="h-9" />
              </span>
              <button
                ref={closeButton}
                type="button"
                className="text-white/80 hover:text-white"
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

      <div className="relative z-10 flex h-full min-h-0 min-w-0 flex-col">
        <header className="sticky top-0 z-30 flex items-center gap-3 px-4 py-3 sm:px-6">
          <button
            ref={menuButton}
            type="button"
            className="rounded-md border border-white/25 bg-white/10 p-2 text-white backdrop-blur-xl hover:bg-white/20 lg:hidden"
            aria-label="Ouvrir le menu"
            onClick={() => setOpen(true)}
          >
            <Menu size={20} />
          </button>
          <div className="ml-auto flex items-center gap-2 rounded-md border border-white/25 bg-white/10 px-2 py-1 text-white backdrop-blur-xl">
            {actions}
          </div>
        </header>
        <main
          id="contenu"
          ref={mainRef}
          className="glass-panel mx-4 mb-2 min-h-0 flex-1 overflow-y-auto overscroll-contain rounded-md border border-white/30 bg-white/20 p-5 backdrop-blur-xl sm:mx-6 sm:p-8 xl:mx-auto xl:w-full xl:max-w-6xl"
        >
          <Outlet />
        </main>
        <footer className="shrink-0 py-3 text-xs text-white/70">
          <LegalLinks />
        </footer>
      </div>
    </div>
  )
}
