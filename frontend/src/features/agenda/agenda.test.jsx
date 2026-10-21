import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { AuthProvider } from '../../auth/AuthProvider'
import RequireAuth from '../../auth/RequireAuth'
import { ToastProvider } from '../../components/ui'
import { api } from '../../lib/api'
import { tokens } from '../../lib/tokens'
import AgendaPage from './AgendaPage'

vi.mock('../../lib/api', async (importOriginal) => {
  const actual = await importOriginal()
  return {
    ...actual,
    api: { get: vi.fn(), post: vi.fn(), put: vi.fn(), patch: vi.fn(), delete: vi.fn() },
  }
})

const me = {
  id: 'me',
  email: 'me@x.fr',
  first_name: 'Moi',
  last_name: 'M',
  role: 'member',
  permissions: [],
}
const mine = {
  id: 'e1',
  title: 'Afterwork',
  description: 'Au bar',
  event_date: '2026-10-21',
  event_time: '18:30:00',
  is_public: true,
  created_by: 'me',
}
const others = {
  ...mine,
  id: 'e2',
  title: 'Réunion MDE',
  event_date: '2026-10-22',
  created_by: 'other',
}

function renderPage() {
  tokens.set({ access_token: 'A', refresh_token: 'R' })
  return render(
    <QueryClientProvider
      client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}
    >
      <ToastProvider>
        <AuthProvider>
          <MemoryRouter initialEntries={['/agenda']}>
            <Routes>
              <Route element={<RequireAuth />}>
                <Route path="/agenda" element={<AgendaPage />} />
              </Route>
            </Routes>
          </MemoryRouter>
        </AuthProvider>
      </ToastProvider>
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  vi.useFakeTimers({ toFake: ['Date'] })
  vi.setSystemTime(new Date(2026, 9, 21, 12))
  vi.resetAllMocks()
  api.get.mockImplementation(async (path) => {
    if (path === '/users/me') return me
    if (path === '/events') return [mine, others]
    if (path === '/invitations/me') return []
    if (path === '/events/e1/invitations')
      return [
        { id: 'i1', status: 'accepted' },
        { id: 'i2', status: 'pending' },
      ]
    if (path === '/directory/people') return { items: [], total: 0 }
    throw new Error(`appel inattendu ${path}`)
  })
})

afterEach(() => vi.useRealTimers())

describe('agenda', () => {
  it('affiche le mois courant avec ses événements', async () => {
    renderPage()
    expect(await screen.findByText('octobre 2026')).toBeInTheDocument()
    expect(await screen.findByRole('button', { name: /Afterwork/ })).toHaveTextContent('18:30')
    expect(screen.getByRole('button', { name: /Réunion MDE/ })).toBeInTheDocument()
    const [, params] = api.get.mock.calls.find(([p]) => p === '/events')
    expect(params).toEqual({ start: '2026-09-28', end: '2026-11-01' })
  })

  it('change de mois et recharge', async () => {
    renderPage()
    await screen.findByText('octobre 2026')
    await userEvent.click(screen.getByRole('button', { name: 'Mois suivant' }))
    expect(await screen.findByText('novembre 2026')).toBeInTheDocument()
    await waitFor(() =>
      expect(api.get).toHaveBeenCalledWith(
        '/events',
        expect.objectContaining({ start: '2026-10-26' }),
      ),
    )
  })

  it('propose la modification de ses propres événements seulement', async () => {
    renderPage()
    await userEvent.click(await screen.findByRole('button', { name: /Afterwork/ }))
    let dialog = await screen.findByRole('dialog', { name: 'Afterwork' })
    expect(within(dialog).getByRole('button', { name: 'Modifier' })).toBeInTheDocument()
    expect(await within(dialog).findByText('Accepté : 1')).toBeInTheDocument()
    await userEvent.keyboard('{Escape}')
    await userEvent.click(screen.getByRole('button', { name: /Réunion MDE/ }))
    dialog = await screen.findByRole('dialog', { name: 'Réunion MDE' })
    expect(within(dialog).queryByRole('button', { name: 'Modifier' })).not.toBeInTheDocument()
  })

  it('crée un événement à partir d’un jour', async () => {
    api.post.mockResolvedValue({})
    renderPage()
    await userEvent.click(
      await screen.findByRole('button', { name: 'Ajouter un événement le 2026-10-25' }),
    )
    await userEvent.type(await screen.findByLabelText('Titre'), 'Atelier')
    expect(screen.getByLabelText('Date')).toHaveValue('2026-10-25')
    await userEvent.click(screen.getByRole('button', { name: 'Enregistrer' }))
    await waitFor(() =>
      expect(api.post).toHaveBeenCalledWith('/events', {
        title: 'Atelier',
        description: null,
        event_date: '2026-10-25',
        event_time: null,
        is_public: false,
        invitee_ids: [],
      }),
    )
  })

  it('supprime un événement', async () => {
    api.delete.mockResolvedValue(null)
    renderPage()
    await userEvent.click(await screen.findByRole('button', { name: /Afterwork/ }))
    await userEvent.click(await screen.findByRole('button', { name: 'Supprimer' }))
    await waitFor(() => expect(api.delete).toHaveBeenCalledWith('/events/e1'))
  })

  it('répond à une invitation', async () => {
    api.get.mockImplementation(async (path) => {
      if (path === '/users/me') return me
      if (path === '/events') return []
      if (path === '/invitations/me')
        return [{ id: 'i9', status: 'pending', target_title: 'Séminaire', session_id: null }]
      throw new Error(path)
    })
    api.post.mockResolvedValue({})
    renderPage()
    await userEvent.click(await screen.findByRole('button', { name: 'Accepter Séminaire' }))
    await waitFor(() =>
      expect(api.post).toHaveBeenCalledWith('/invitations/i9/respond', { status: 'accepted' }),
    )
  })
})
