import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import App from '../App'
import { ThemeProvider } from '../components/ThemeProvider'
import { ToastProvider } from '../components/ui'
import { ApiError, api } from '../lib/api'
import { tokens } from '../lib/tokens'
import { AuthProvider } from './AuthProvider'
import { canManageCompany, hasPermission, isStaff } from './permissions'

vi.mock('../lib/api', async (importOriginal) => {
  const actual = await importOriginal()
  return {
    ...actual,
    api: { get: vi.fn(), post: vi.fn(), put: vi.fn(), patch: vi.fn(), delete: vi.fn() },
  }
})

const member = {
  id: '1',
  email: 'ada@x.fr',
  first_name: 'Ada',
  last_name: 'Lovelace',
  role: 'member',
  permissions: [],
  is_company_admin: false,
  company_id: null,
  avatar_path: null,
}

function renderApp(path) {
  return render(
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
}

beforeEach(() => {
  vi.resetAllMocks()
})

describe('permissions', () => {
  it('applique les droits par rôle', () => {
    const root = { role: 'super_admin', permissions: [] }
    const staff = { role: 'staff', permissions: ['manage_news'] }
    expect(hasPermission(root, 'manage_users')).toBe(true)
    expect(hasPermission(staff, 'manage_news')).toBe(true)
    expect(hasPermission(staff, 'manage_users')).toBe(false)
    expect(hasPermission(member, 'manage_news')).toBe(false)
    expect(isStaff(staff)).toBe(true)
    expect(isStaff(member)).toBe(false)
  })

  it("autorise l'admin d'entreprise sur sa propre entreprise", () => {
    const boss = { ...member, is_company_admin: true, company_id: 'c1' }
    expect(canManageCompany(boss, 'c1')).toBe(true)
    expect(canManageCompany(boss, 'c2')).toBe(false)
    expect(canManageCompany(member, 'c1')).toBe(false)
  })
})

describe('authentification', () => {
  it('redirige un visiteur vers la connexion', async () => {
    renderApp('/annuaire')
    expect(await screen.findByRole('heading', { name: 'Connexion' })).toBeInTheDocument()
  })

  it('connecte puis affiche la page demandée', async () => {
    api.post.mockResolvedValue({ access_token: 'A', refresh_token: 'R' })
    api.get.mockResolvedValue(member)
    renderApp('/connexion')
    await userEvent.type(screen.getByLabelText('Email'), 'ada@x.fr')
    await userEvent.type(screen.getByLabelText('Mot de passe'), 'password123')
    await userEvent.click(screen.getByRole('button', { name: 'Se connecter' }))
    expect(await screen.findByRole('heading', { name: 'Annuaire' })).toBeInTheDocument()
    expect(api.post).toHaveBeenCalledWith(
      '/auth/login',
      { email: 'ada@x.fr', password: 'password123' },
      { auth: false },
    )
    expect(tokens.access).toBe('A')
  })

  it('affiche une erreur si les identifiants sont faux', async () => {
    api.post.mockRejectedValue(new ApiError(401, 'UNAUTHORIZED', 'x'))
    renderApp('/connexion')
    await userEvent.type(screen.getByLabelText('Email'), 'a@x.fr')
    await userEvent.type(screen.getByLabelText('Mot de passe'), 'bad')
    await userEvent.click(screen.getByRole('button', { name: 'Se connecter' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Email ou mot de passe incorrect.')
  })

  it('restaure la session depuis le jeton et se déconnecte', async () => {
    tokens.set({ access_token: 'A', refresh_token: 'R' })
    api.get.mockResolvedValue(member)
    api.post.mockResolvedValue(null)
    renderApp('/annuaire')
    expect(await screen.findByText('Ada Lovelace')).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Se déconnecter' }))
    expect(await screen.findByRole('heading', { name: 'Connexion' })).toBeInTheDocument()
    expect(tokens.access).toBeNull()
  })

  it('vide la session si /users/me échoue', async () => {
    tokens.set({ access_token: 'A', refresh_token: 'R' })
    api.get.mockRejectedValue(new ApiError(401, 'UNAUTHORIZED', 'x'))
    renderApp('/annuaire')
    expect(await screen.findByRole('heading', { name: 'Connexion' })).toBeInTheDocument()
    expect(tokens.access).toBeNull()
  })

  it("cache l'administration aux simples membres", async () => {
    tokens.set({ access_token: 'A', refresh_token: 'R' })
    api.get.mockResolvedValue(member)
    renderApp('/administration')
    expect(await screen.findByRole('heading', { name: 'Annuaire' })).toBeInTheDocument()
    expect(screen.queryByRole('link', { name: 'Administration' })).not.toBeInTheDocument()
  })

  it("montre l'administration au staff", async () => {
    tokens.set({ access_token: 'A', refresh_token: 'R' })
    api.get.mockResolvedValue({ ...member, role: 'staff', permissions: ['manage_users'] })
    renderApp('/administration')
    expect(await screen.findByRole('heading', { name: 'Administration' })).toBeInTheDocument()
    expect(screen.getAllByRole('link', { name: 'Administration' }).length).toBeGreaterThan(0)
  })
})

describe('mot de passe oublié', () => {
  it('affiche toujours le même message', async () => {
    api.post.mockRejectedValue(new ApiError(500, 'X', 'x'))
    renderApp('/mot-de-passe-oublie')
    await userEvent.type(screen.getByLabelText('Email'), 'a@x.fr')
    await userEvent.click(screen.getByRole('button', { name: 'Envoyer le lien' }))
    expect(await screen.findByText(/Si un compte correspond/)).toBeInTheDocument()
  })

  it('réinitialise avec le jeton du lien', async () => {
    api.post.mockResolvedValue(null)
    renderApp('/reset-password?token=abc')
    await userEvent.type(screen.getByLabelText('Nouveau mot de passe'), 'brandnewpass1')
    await userEvent.type(screen.getByLabelText('Confirmation'), 'brandnewpass1')
    await userEvent.click(screen.getByRole('button', { name: 'Enregistrer' }))
    await waitFor(() =>
      expect(api.post).toHaveBeenCalledWith(
        '/auth/reset-password',
        { token: 'abc', new_password: 'brandnewpass1' },
        { auth: false },
      ),
    )
    expect(await screen.findByRole('heading', { name: 'Connexion' })).toBeInTheDocument()
  })

  it('refuse des mots de passe différents', async () => {
    renderApp('/reset-password?token=abc')
    await userEvent.type(screen.getByLabelText('Nouveau mot de passe'), 'brandnewpass1')
    await userEvent.type(screen.getByLabelText('Confirmation'), 'different123')
    await userEvent.click(screen.getByRole('button', { name: 'Enregistrer' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('ne correspondent pas')
    expect(api.post).not.toHaveBeenCalled()
  })

  it('signale un lien sans jeton', () => {
    renderApp('/reset-password')
    expect(screen.getByRole('heading', { name: 'Lien invalide' })).toBeInTheDocument()
  })
})
