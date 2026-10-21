import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'

import App from './App'
import { ThemeProvider } from './components/ThemeProvider'

const renderAt = (path) =>
  render(
    <ThemeProvider>
      <MemoryRouter initialEntries={[path]}>
        <App />
      </MemoryRouter>
    </ThemeProvider>,
  )

describe('App', () => {
  it("affiche l'accueil", () => {
    renderAt('/')
    expect(screen.getByRole('heading', { name: 'portailMDE' })).toBeInTheDocument()
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
