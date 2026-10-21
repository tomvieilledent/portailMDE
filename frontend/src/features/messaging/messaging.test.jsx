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
import MessagingPage from './MessagingPage'
import { conversationTitle, previewText } from './helpers'

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
  last_name: 'Même',
  role: 'member',
  permissions: [],
}
const ada = { id: 'ada', first_name: 'Ada', last_name: 'Lovelace', avatar_path: null }
const bob = { id: 'bob', first_name: 'Bob', last_name: 'Martin', avatar_path: null }
const msg = (id, content, author = ada) => ({
  id,
  conversation_id: 'c1',
  author_id: author.id,
  author,
  content,
  file_name: null,
  file_url: null,
  created_at: `2026-10-21T10:0${id}:00Z`,
})
const direct = {
  id: 'c1',
  kind: 'direct',
  title: null,
  creator_id: 'me',
  participants: [{ ...me, avatar_path: null }, ada],
  last_message: msg('2', 'Salut !'),
  unread_count: 2,
  created_at: '2026-10-20T10:00:00Z',
}
const group = {
  id: 'g1',
  kind: 'group',
  title: 'Équipe projet',
  creator_id: 'me',
  participants: [{ ...me, avatar_path: null }, ada, bob],
  last_message: null,
  unread_count: 0,
  created_at: '2026-10-20T09:00:00Z',
}

function renderAt(path) {
  tokens.set({ access_token: 'A', refresh_token: 'R' })
  return render(
    <QueryClientProvider
      client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}
    >
      <ToastProvider>
        <AuthProvider>
          <MemoryRouter initialEntries={[path]}>
            <Routes>
              <Route element={<RequireAuth />}>
                <Route path="/messagerie" element={<MessagingPage />} />
                <Route path="/messagerie/:conversationId" element={<MessagingPage />} />
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
  window.HTMLElement.prototype.scrollIntoView = vi.fn()
  api.get.mockImplementation(async (path) => {
    if (path === '/users/me') return me
    if (path === '/conversations') return [direct, group]
    if (path === '/conversations/c1/messages') return [msg('2', 'Salut !'), msg('1', 'Bonjour')]
    if (path === '/conversations/g1/messages') return []
    if (path === '/directory/people')
      return { items: [{ ...ada, email: 'a@x.fr', company: null }], total: 1 }
    throw new Error(`appel inattendu ${path}`)
  })
  api.post.mockResolvedValue(null)
})

describe('helpers', () => {
  it('nomme les conversations', () => {
    expect(conversationTitle(direct, 'me')).toBe('Ada Lovelace')
    expect(conversationTitle(group, 'me')).toBe('Équipe projet')
  })

  it('résume le dernier message', () => {
    expect(previewText(null)).toBe('Aucun message')
    expect(previewText({ content: '', file_name: 'a.pdf' })).toBe('📎 a.pdf')
  })
})

describe('messagerie', () => {
  it('liste les conversations avec les messages non lus', async () => {
    renderAt('/messagerie')
    const link = await screen.findByRole('link', { name: /Ada Lovelace/ })
    expect(within(link).getByText('Salut !')).toBeInTheDocument()
    expect(within(link).getByText('2')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /Équipe projet/ })).toBeInTheDocument()
    expect(screen.getByText('Sélectionnez une conversation')).toBeInTheDocument()
  })

  it('affiche le fil dans l’ordre chronologique et marque comme lu', async () => {
    renderAt('/messagerie/c1')
    await screen.findByText('Bonjour')
    const thread = within(screen.getByRole('region', { name: 'Discussion' }))
    const order = thread.getAllByRole('listitem').map((li) => li.textContent)
    expect(order[0]).toContain('Bonjour')
    expect(order[1]).toContain('Salut !')
    await waitFor(() => expect(api.post).toHaveBeenCalledWith('/conversations/c1/read'))
  })

  it('envoie un message avec Entrée', async () => {
    api.post.mockImplementation(async (path) =>
      path === '/conversations/c1/messages' ? msg('3', 'Coucou', me) : null,
    )
    renderAt('/messagerie/c1')
    await userEvent.type(await screen.findByLabelText('Votre message'), 'Coucou{Enter}')
    await waitFor(() => {
      const call = api.post.mock.calls.find(([p]) => p === '/conversations/c1/messages')
      expect(call[1].get('content')).toBe('Coucou')
    })
    expect(await screen.findAllByText('Coucou')).not.toHaveLength(0)
  })

  it('ne crée pas de message vide', async () => {
    renderAt('/messagerie/c1')
    await screen.findByLabelText('Votre message')
    await userEvent.click(screen.getByRole('button', { name: 'Envoyer' }))
    expect(api.post.mock.calls.some(([p]) => p === '/conversations/c1/messages')).toBe(false)
  })

  it('supprime un de ses messages', async () => {
    api.get.mockImplementation(async (path) => {
      if (path === '/users/me') return me
      if (path === '/conversations') return [direct]
      return [msg('1', 'à supprimer', me)]
    })
    api.delete.mockResolvedValue(null)
    renderAt('/messagerie/c1')
    await userEvent.click(await screen.findByRole('button', { name: 'Supprimer le message' }))
    await waitFor(() => expect(api.delete).toHaveBeenCalledWith('/messages/1'))
    await waitFor(() => expect(screen.queryByText('à supprimer')).not.toBeInTheDocument())
  })

  it('crée une conversation directe', async () => {
    api.post.mockResolvedValue({ id: 'c1' })
    renderAt('/messagerie')
    await userEvent.click(await screen.findByRole('button', { name: /Nouveau/ }))
    await userEvent.click(await screen.findByRole('checkbox', { name: /Ada Lovelace/ }))
    await userEvent.click(screen.getByRole('button', { name: 'Créer' }))
    await waitFor(() =>
      expect(api.post).toHaveBeenCalledWith('/conversations', { kind: 'direct', user_id: 'ada' }),
    )
  })

  it('crée un groupe nommé', async () => {
    api.post.mockResolvedValue({ id: 'g2' })
    renderAt('/messagerie')
    await userEvent.click(await screen.findByRole('button', { name: /Nouveau/ }))
    await userEvent.click(screen.getByLabelText('Groupe de discussion'))
    await userEvent.type(screen.getByLabelText('Nom du groupe'), 'Projet X')
    await userEvent.click(await screen.findByRole('checkbox', { name: /Ada Lovelace/ }))
    await userEvent.click(screen.getByRole('button', { name: 'Créer' }))
    await waitFor(() =>
      expect(api.post).toHaveBeenCalledWith('/conversations', {
        kind: 'group',
        title: 'Projet X',
        user_ids: ['ada'],
      }),
    )
  })

  it('permet au créateur de renommer et de quitter le groupe', async () => {
    api.patch.mockResolvedValue({})
    renderAt('/messagerie/g1')
    await userEvent.click(await screen.findByRole('button', { name: 'Paramètres du groupe' }))
    const dialog = await screen.findByRole('dialog')
    const name = within(dialog).getByLabelText('Nom du groupe')
    await userEvent.clear(name)
    await userEvent.type(name, 'Nouveau nom')
    await userEvent.click(within(dialog).getByRole('button', { name: 'Renommer' }))
    await waitFor(() =>
      expect(api.patch).toHaveBeenCalledWith('/conversations/g1', { title: 'Nouveau nom' }),
    )
    api.delete.mockResolvedValue(null)
    await userEvent.click(within(dialog).getByRole('button', { name: 'Retirer Bob Martin' }))
    await waitFor(() =>
      expect(api.delete).toHaveBeenCalledWith('/conversations/g1/participants/bob'),
    )
  })

  it('signale une conversation introuvable', async () => {
    renderAt('/messagerie/inconnue')
    expect(await screen.findByText('Conversation introuvable')).toBeInTheDocument()
  })
})
