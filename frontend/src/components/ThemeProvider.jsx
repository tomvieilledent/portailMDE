/** Fournisseur du thème clair ou sombre. */

import { createContext, useContext, useEffect, useMemo, useState } from 'react'

/** Contexte portant le thème courant. */
const ThemeContext = createContext(null)

/** Thème initial : préférence mémorisée, sinon préférence du système. */
function initialTheme() {
  try {
    const saved = localStorage.getItem('theme')
    if (saved) return saved
  } catch {
    /* stockage indisponible */
  }
  return matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

/** Gère le mode sombre (classe `dark` sur <html>, préférence mémorisée). */
export function ThemeProvider({ children }) {
  const [theme, setTheme] = useState(initialTheme)

  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark')
    try {
      localStorage.setItem('theme', theme)
    } catch {
      /* stockage indisponible */
    }
  }, [theme])

  const value = useMemo(
    () => ({ theme, toggle: () => setTheme((t) => (t === 'dark' ? 'light' : 'dark')) }),
    [theme],
  )
  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
}

/** Accès au thème courant et à sa bascule. */
// eslint-disable-next-line react-refresh/only-export-components
export function useTheme() {
  const context = useContext(ThemeContext)
  if (!context) throw new Error('useTheme doit être utilisé dans un ThemeProvider')
  return context
}
