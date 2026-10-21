import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { ThemeProvider } from '../components/ThemeProvider'
import { api } from '../lib/api'
import HomePage from './HomePage'

vi.mock('../lib/api', () => ({ api: { get: vi.fn() } }))

function renderHome() {
  return render(
    <QueryClientProvider client={new QueryClient()}>
      <ThemeProvider>
        <MemoryRouter>
          <HomePage />
        </MemoryRouter>
      </ThemeProvider>
    </QueryClientProvider>,
  )
}

beforeEach(() => vi.resetAllMocks())

describe('HomePage', () => {
  it('affiche le contenu éditable renvoyé par le backend', async () => {
    api.get.mockResolvedValue({
      key: 'landing',
      value: {
        slogan: 'Ensemble plus loin',
        sections: [{ title: 'Coworking', duration: '1 mois', description: 'd', highlight: '' }],
      },
    })
    renderHome()
    expect(await screen.findByRole('heading', { name: 'Ensemble plus loin' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Coworking' })).toBeInTheDocument()
    expect(screen.getAllByRole('link', { name: /connecter|portail/i })[0]).toHaveAttribute(
      'href',
      '/connexion',
    )
  })

  it("se rabat sur le contenu par défaut si l'API échoue", async () => {
    api.get.mockRejectedValue(new Error('réseau'))
    renderHome()
    expect(screen.getByRole('heading', { name: "De l'idée à la création" })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Incubateur' })).toBeInTheDocument()
  })
})
