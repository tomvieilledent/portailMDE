/** Tests du routage de l'application selon l'état de connexion. */

import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'

import App from './App'
import { AuthProvider } from './auth/AuthProvider'
import { ThemeProvider } from './components/ThemeProvider'
import { ToastProvider } from './components/ui'

/** Affiche l'application à l'adresse donnée. */
const renderAt = (path) =>
  render(
    <QueryClientProvider client={new QueryClient()}>
      <ThemeProvider>
        <ToastProvider>
          <AuthProvider>
            <MemoryRouter initialEntries={[path]}>
              <App />
            </MemoryRouter>
          </AuthProvider>
        </ToastProvider>
      </ThemeProvider>
    </QueryClientProvider>,
  )

/** Routage de l'application. */
describe('App', () => {
  it("affiche l'accueil public", () => {
    renderAt('/')
    expect(screen.getByRole('link', { name: 'Se connecter' })).toHaveAttribute('href', '/connexion')
  })

  it('affiche la page 404', () => {
    renderAt('/nimporte-quoi')
    expect(screen.getByText('Page introuvable')).toBeInTheDocument()
  })

  it('bascule le mode sombre et le mémorise', async () => {
    renderAt('/')
    await userEvent.click(screen.getByRole('button', { name: /mode/i }))
    const dark = document.documentElement.classList.contains('dark')
    expect(localStorage.getItem('theme')).toBe(dark ? 'dark' : 'light')
  })
})
