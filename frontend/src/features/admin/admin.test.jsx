/** Tests de l'espace d'administration. */

import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import App from '../../App'
import { AuthProvider } from '../../auth/AuthProvider'
import { ThemeProvider } from '../../components/ThemeProvider'
import { ToastProvider } from '../../components/ui'
import { api } from '../../lib/api'
import { tokens } from '../../lib/tokens'

vi.mock('../../lib/api', async (importOriginal) => {
  const actual = await importOriginal()
  return {
    ...actual,
    api: { get: vi.fn(), post: vi.fn(), put: vi.fn(), patch: vi.fn(), delete: vi.fn() },
  }
})

const base = {
  id: 'me',
  email: 'me@x.fr',
  first_name: 'Moi',
  last_name: 'Admin',
  company_id: null,
  avatar_path: null,
}
const root = { ...base, role: 'super_admin', permissions: [] }
const userAdmin = { ...base, role: 'staff', permissions: ['manage_users'] }
const newsEditor = { ...base, role: 'staff', permissions: ['manage_news'] }
const ada = {
  id: 'u2',
  email: 'ada@x.fr',
  first_name: 'Ada',
  last_name: 'Lovelace',
  role: 'member',
  permissions: [],
  is_active: true,
  avatar_path: null,
}
const acme = {
  id: 'c1',
  name: 'Acme',
  kind: 'company',
  location: 'Rodez',
  is_active: true,
  description: null,
  website_url: null,
}

/** Affiche l'administration à l'adresse donnée, pour l'utilisateur donné. */
function renderAt(path, me) {
  tokens.set({ access_token: 'A', refresh_token: 'R' })
  api.get.mockImplementation(async (url) => {
    if (url === '/users/me') return me
    if (url === '/users')
      return { items: [ada, { ...base, ...me }], total: 2, limit: 25, offset: 0 }
    if (url === '/companies') return { items: [acme], total: 1, limit: 25, offset: 0 }
    if (url === '/directory/people') return { items: [ada], total: 1, limit: 20, offset: 0 }
    if (url === '/content/landing') return { key: 'landing', value: { slogan: 'Mon slogan' } }
    if (url === '/notifications/unread-count') return { count: 0 }
    throw new Error(`appel inattendu ${url}`)
  })
  return render(
    <QueryClientProvider
      client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}
    >
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
}

beforeEach(() => vi.resetAllMocks())

/** Accès à l'espace d'administration selon les droits. */
describe('administration', () => {
  it('redirige vers la première section autorisée', async () => {
    renderAt('/administration', userAdmin)
    expect(await screen.findByText('Ada Lovelace')).toBeInTheDocument()
    const nav = screen.getByRole('navigation', { name: 'Administration' })
    expect(within(nav).getAllByRole('link')).toHaveLength(1)
    expect(within(nav).getByRole('link', { name: 'Utilisateurs' })).toBeInTheDocument()
  })

  it('montre toutes les sections au super admin', async () => {
    renderAt('/administration', root)
    const nav = await screen.findByRole('navigation', { name: 'Administration' })
    expect(
      within(nav)
        .getAllByRole('link')
        .map((l) => l.textContent),
    ).toEqual(['Utilisateurs', 'Entreprises', 'Contenu'])
  })

  it("explique l'absence de droits", async () => {
    renderAt('/administration', { ...base, role: 'staff', permissions: ['manage_trainings'] })
    expect(await screen.findByText(/Aucun droit d'administration/)).toBeInTheDocument()
  })
})

/** Gestion des comptes. */
describe('utilisateurs', () => {
  it('désactive un compte', async () => {
    api.post.mockResolvedValue({})
    renderAt('/administration/utilisateurs', userAdmin)
    const row = (await screen.findByText('Ada Lovelace')).closest('tr')
    await userEvent.click(within(row).getByRole('button', { name: 'Désactiver' }))
    await waitFor(() => expect(api.post).toHaveBeenCalledWith('/users/u2/deactivate'))
  })

  it('supprime un compte mais pas le sien', async () => {
    api.delete.mockResolvedValue(null)
    renderAt('/administration/utilisateurs', userAdmin)
    await screen.findByText('Ada Lovelace')
    expect(screen.getAllByRole('button', { name: /^Supprimer/ })).toHaveLength(1)
    await userEvent.click(screen.getByRole('button', { name: 'Supprimer Ada Lovelace' }))
    await waitFor(() => expect(api.delete).toHaveBeenCalledWith('/users/u2'))
  })

  it("n'offre le changement de rôle qu'au super admin", async () => {
    renderAt('/administration/utilisateurs', userAdmin)
    await screen.findByText('Ada Lovelace')
    expect(screen.queryByRole('button', { name: 'Rôle' })).not.toBeInTheDocument()
  })

  it('attribue un rôle staff avec des droits', async () => {
    api.put.mockResolvedValue({})
    renderAt('/administration/utilisateurs', root)
    const row = (await screen.findByText('Ada Lovelace')).closest('tr')
    await userEvent.click(within(row).getByRole('button', { name: 'Rôle' }))
    const dialog = await screen.findByRole('dialog')
    await userEvent.selectOptions(within(dialog).getByLabelText('Rôle'), 'staff')
    await userEvent.click(within(dialog).getByLabelText('Gérer actualités et accueil'))
    await userEvent.click(within(dialog).getByRole('button', { name: 'Enregistrer' }))
    await waitFor(() =>
      expect(api.put).toHaveBeenCalledWith('/users/u2/role', {
        role: 'staff',
        permissions: ['manage_news'],
      }),
    )
  })

  it('crée un compte', async () => {
    api.post.mockResolvedValue({})
    renderAt('/administration/utilisateurs', userAdmin)
    await userEvent.click(await screen.findByRole('button', { name: /Nouveau compte/ }))
    const dialog = await screen.findByRole('dialog')
    await userEvent.type(within(dialog).getByLabelText('Email'), 'new@x.fr')
    await userEvent.type(within(dialog).getByLabelText('Mot de passe temporaire'), 'temporaire1')
    await userEvent.click(within(dialog).getByRole('button', { name: 'Créer le compte' }))
    await waitFor(() =>
      expect(api.post).toHaveBeenCalledWith(
        '/users',
        expect.objectContaining({
          email: 'new@x.fr',
          role: 'member',
          permissions: [],
          company_id: null,
        }),
      ),
    )
  })
})

/** Gestion des entreprises. */
describe('entreprises', () => {
  it('crée une entreprise', async () => {
    api.post.mockResolvedValue({})
    renderAt('/administration/entreprises', {
      ...base,
      role: 'staff',
      permissions: ['manage_companies'],
    })
    await userEvent.click(await screen.findByRole('button', { name: /Nouvelle entreprise/ }))
    await userEvent.type(await screen.findByLabelText('Nom'), 'Globex')
    const save = screen.getByRole('button', { name: 'Enregistrer' })
    expect(save).toBeDisabled() // le propriétaire est obligatoire
    const dialog = screen.getByRole('dialog')
    await userEvent.click(await within(dialog).findByRole('checkbox', { name: /Ada Lovelace/ }))
    await userEvent.click(save)
    await waitFor(() =>
      expect(api.post).toHaveBeenCalledWith(
        '/companies',
        expect.objectContaining({ name: 'Globex', kind: 'company', owner_id: 'u2' }),
      ),
    )
  })

  it('désactive et supprime une entreprise', async () => {
    api.post.mockResolvedValue({})
    api.delete.mockResolvedValue(null)
    renderAt('/administration/entreprises', {
      ...base,
      role: 'staff',
      permissions: ['manage_companies'],
    })
    await userEvent.click(await screen.findByRole('button', { name: 'Désactiver' }))
    await waitFor(() => expect(api.post).toHaveBeenCalledWith('/companies/c1/deactivate'))
    await userEvent.click(screen.getByRole('button', { name: 'Supprimer Acme' }))
    await waitFor(() => expect(api.delete).toHaveBeenCalledWith('/companies/c1'))
  })
})

/** Gestion du contenu éditorial. */
describe('contenu', () => {
  it("enregistre la page d'accueil", async () => {
    api.put.mockResolvedValue({})
    renderAt('/administration/contenu', newsEditor)
    const slogan = await screen.findByDisplayValue('Mon slogan')
    await userEvent.clear(slogan)
    await userEvent.type(slogan, 'Nouveau slogan')
    await userEvent.click(screen.getAllByRole('button', { name: 'Enregistrer' })[0])
    await waitFor(() => {
      const [path, body] = api.put.mock.calls[0]
      expect(path).toBe('/content/landing')
      expect(body.value.slogan).toBe('Nouveau slogan')
      expect(body.value.sections).toHaveLength(3)
    })
  })

  it('envoie une annonce', async () => {
    api.post.mockResolvedValue(null)
    renderAt('/administration/contenu', newsEditor)
    await userEvent.type(await screen.findByLabelText('Message'), 'Fermeture lundi')
    await userEvent.click(screen.getByRole('button', { name: "Envoyer l'annonce" }))
    await waitFor(() =>
      expect(api.post).toHaveBeenCalledWith('/notifications/broadcast', {
        content: 'Fermeture lundi',
      }),
    )
  })
})
