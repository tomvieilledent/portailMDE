/** Tests des actualités et de la cloche de notifications. */

import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { AuthProvider } from '../../auth/AuthProvider'
import RequireAuth from '../../auth/RequireAuth'
import { ToastProvider } from '../../components/ui'
import { api } from '../../lib/api'
import { tokens } from '../../lib/tokens'
import NotificationsBell from '../notifications/NotificationsBell'
import { notificationTarget } from '../notifications/target'
import NewsPage from './NewsPage'

vi.mock('../../lib/api', async (importOriginal) => {
  const actual = await importOriginal()
  return {
    ...actual,
    api: { get: vi.fn(), post: vi.fn(), put: vi.fn(), patch: vi.fn(), delete: vi.fn() },
  }
})

const member = { id: 'me', email: 'me@x.fr', role: 'member', permissions: [] }
const editor = { ...member, role: 'staff', permissions: ['manage_news'] }
const article = {
  id: 'a1',
  title: 'Nouvelle TVA',
  source: 'BOFiP',
  summary: 'Les taux changent',
  url: 'https://ex.fr/tva',
  category: 'fiscalité',
  published_at: '2026-10-01T10:00:00Z',
}

let saved
/** Affiche le composant avec les fournisseurs nécessaires. */
function setup(ui, user = member, extra = {}) {
  tokens.set({ access_token: 'A', refresh_token: 'R' })
  api.get.mockImplementation(async (url) => {
    if (url === '/users/me') return user
    if (url === '/news') return { items: [article], total: 1, limit: 20, offset: 0 }
    if (url === '/news/saved') return saved
    if (url === '/notifications/unread-count') return { count: extra.unread ?? 0 }
    if (url === '/notifications') return extra.notifications ?? []
    throw new Error(`appel inattendu ${url}`)
  })
  return render(
    <QueryClientProvider
      client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}
    >
      <ToastProvider>
        <AuthProvider>
          <MemoryRouter initialEntries={['/actualites']}>
            <Routes>
              <Route element={<RequireAuth />}>
                <Route path="/actualites" element={ui} />
                <Route path="/agenda" element={<p>page agenda</p>} />
                <Route path="/messagerie/:id" element={<p>page messagerie</p>} />
              </Route>
            </Routes>
          </MemoryRouter>
        </AuthProvider>
      </ToastProvider>
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  vi.resetAllMocks()
  saved = []
})

/** Liste, favoris et publication. */
describe('actualités', () => {
  it('affiche les articles avec lien externe sécurisé', async () => {
    setup(<NewsPage />)
    expect(await screen.findByText('Nouvelle TVA')).toBeInTheDocument()
    const link = screen.getByRole('link', { name: /Lire l'article/ })
    expect(link).toHaveAttribute('href', 'https://ex.fr/tva')
    expect(link).toHaveAttribute('rel', expect.stringContaining('noopener'))
  })

  it('enregistre un article en favori', async () => {
    api.put.mockResolvedValue({})
    setup(<NewsPage />)
    await userEvent.click(await screen.findByRole('button', { name: 'Enregistrer' }))
    await waitFor(() => expect(api.put).toHaveBeenCalledWith('/news/a1/save'))
  })

  it('retire un favori', async () => {
    saved = [{ ...article, id: 's1', article_id: 'a1' }]
    api.delete.mockResolvedValue(null)
    setup(<NewsPage />)
    await userEvent.click(await screen.findByRole('button', { name: 'Retirer des favoris' }))
    await waitFor(() => expect(api.delete).toHaveBeenCalledWith('/news/saved/s1'))
  })

  it("liste les favoris même si l'original a disparu", async () => {
    saved = [{ ...article, id: 's2', article_id: null, title: 'Ancien article' }]
    setup(<NewsPage />)
    await userEvent.click(await screen.findByRole('tab', { name: /Favoris/ }))
    expect(await screen.findByText('Ancien article')).toBeInTheDocument()
  })

  it('réserve publication, suppression et synchronisation au staff', async () => {
    setup(<NewsPage />)
    await screen.findByText('Nouvelle TVA')
    expect(screen.queryByRole('button', { name: /Synchroniser/ })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: "Supprimer l'article" })).not.toBeInTheDocument()
  })

  it('synchronise les flux (staff)', async () => {
    api.post.mockResolvedValue({ created: 3 })
    setup(<NewsPage />, editor)
    await userEvent.click(await screen.findByRole('button', { name: /Synchroniser/ }))
    await waitFor(() => expect(api.post).toHaveBeenCalledWith('/news/sync'))
    expect(await screen.findByText('3 nouvel(s) article(s).')).toBeInTheDocument()
  })

  it('publie un article (staff)', async () => {
    api.post.mockResolvedValue({})
    setup(<NewsPage />, editor)
    await userEvent.click(await screen.findByRole('button', { name: /Publier/ }))
    await userEvent.type(await screen.findByLabelText(/^Titre( \*)?( \(obligatoire\))?$/), 'Info')
    const dialog = screen.getByRole('dialog', { name: 'Publier un article' })
    await userEvent.click(within(dialog).getByRole('button', { name: 'Publier' }))
    await waitFor(() =>
      expect(api.post).toHaveBeenCalledWith(
        '/news',
        expect.objectContaining({ title: 'Info', url: null }),
      ),
    )
  })

  it('supprime un article (staff)', async () => {
    api.delete.mockResolvedValue(null)
    setup(<NewsPage />, editor)
    await userEvent.click(await screen.findByRole('button', { name: "Supprimer l'article" }))
    await waitFor(() => expect(api.delete).toHaveBeenCalledWith('/news/a1'))
  })
})

/** Compteur et liste des notifications. */
describe('cloche de notifications', () => {
  const notifications = [
    {
      id: 'n1',
      content: 'Ada vous invite : Afterwork',
      kind: 'invitation',
      data: {},
      is_read: false,
      created_at: '2026-10-21T10:00:00Z',
    },
    {
      id: 'n2',
      content: 'Vous avez été ajouté au groupe',
      kind: 'conversation',
      data: { conversation_id: 'c9' },
      is_read: true,
      created_at: '2026-10-20T10:00:00Z',
    },
  ]

  it('calcule la page cible', () => {
    expect(notificationTarget(notifications[0])).toBe('/agenda')
    expect(notificationTarget(notifications[1])).toBe('/messagerie/c9')
    expect(notificationTarget({ kind: 'announcement' })).toBeNull()
  })

  it('affiche le compteur de non lues', async () => {
    setup(<NotificationsBell />, member, { unread: 12 })
    expect(
      await screen.findByRole('button', { name: 'Notifications (12 non lues)' }),
    ).toHaveTextContent('9+')
  })

  it('ouvre la liste, marque comme lu et navigue', async () => {
    api.post.mockResolvedValue({})
    setup(<NotificationsBell />, member, { unread: 1, notifications })
    await userEvent.click(await screen.findByRole('button', { name: /Notifications/ }))
    await userEvent.click(await screen.findByText('Ada vous invite : Afterwork'))
    await waitFor(() => expect(api.post).toHaveBeenCalledWith('/notifications/n1/read'))
    expect(await screen.findByText('page agenda')).toBeInTheDocument()
  })

  it('marque tout comme lu', async () => {
    api.post.mockResolvedValue(null)
    setup(<NotificationsBell />, member, { unread: 1, notifications })
    await userEvent.click(await screen.findByRole('button', { name: /Notifications/ }))
    await userEvent.click(await screen.findByRole('button', { name: 'Tout marquer comme lu' }))
    await waitFor(() => expect(api.post).toHaveBeenCalledWith('/notifications/read-all'))
  })

  it('se ferme avec Échap', async () => {
    setup(<NotificationsBell />, member, { notifications })
    await userEvent.click(await screen.findByRole('button', { name: /Notifications/ }))
    expect(await screen.findByRole('dialog', { name: 'Notifications' })).toBeInTheDocument()
    await userEvent.keyboard('{Escape}')
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })
})
