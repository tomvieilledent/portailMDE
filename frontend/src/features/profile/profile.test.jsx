/** Tests du profil et de la page « Mon entreprise ». */

import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { AuthProvider } from '../../auth/AuthProvider'
import RequireAuth from '../../auth/RequireAuth'
import { ToastProvider } from '../../components/ui'
import { ApiError, api } from '../../lib/api'
import { tokens } from '../../lib/tokens'
import MyCompanyPage from '../company/MyCompanyPage'
import ProfilePage from './ProfilePage'

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
  job_title: null,
  phone: null,
  role: 'member',
  permissions: [],
  is_company_admin: false,
  company_id: null,
  avatar_path: null,
  business_card_path: null,
}
const acme = {
  id: 'c1',
  name: 'Acme',
  description: 'Tout',
  location: null,
  website_url: null,
  logo_path: null,
  kind: 'company',
}
const colleague = {
  id: 'u2',
  email: 'c@x.fr',
  first_name: 'Cléo',
  last_name: 'Colle',
  is_active: true,
  is_company_admin: false,
}

/** Affiche la page à l'adresse donnée pour l'utilisateur donné. */
function renderAt(path, user = me) {
  tokens.set({ access_token: 'A', refresh_token: 'R' })
  api.get.mockImplementation(async (url) => {
    if (url === '/users/me') return user
    if (url === '/companies/me') return acme
    if (url === '/companies/c1/members') return [user, colleague]
    throw new Error(`appel inattendu ${url}`)
  })
  return render(
    <QueryClientProvider
      client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}
    >
      <ToastProvider>
        <AuthProvider>
          <MemoryRouter initialEntries={[path]}>
            <Routes>
              <Route element={<RequireAuth />}>
                <Route path="/profil" element={<ProfilePage />} />
                <Route path="/mon-entreprise" element={<MyCompanyPage />} />
              </Route>
            </Routes>
          </MemoryRouter>
        </AuthProvider>
      </ToastProvider>
    </QueryClientProvider>,
  )
}

beforeEach(() => vi.resetAllMocks())

/** Informations, images et mot de passe. */
describe('profil', () => {
  it('enregistre les informations modifiées', async () => {
    renderAt('/profil')
    api.patch.mockResolvedValue({ ...me, job_title: 'CTO' })
    await userEvent.type(await screen.findByLabelText('Fonction'), 'CTO')
    await userEvent.click(screen.getByRole('button', { name: 'Enregistrer' }))
    await waitFor(() =>
      expect(api.patch).toHaveBeenCalledWith('/users/me', {
        first_name: 'Moi',
        last_name: 'Même',
        job_title: 'CTO',
        phone: null,
      }),
    )
    expect(await screen.findByText('Profil mis à jour.')).toBeInTheDocument()
  })

  it('envoie la photo de profil', async () => {
    renderAt('/profil')
    api.put.mockResolvedValue({ ...me, avatar_path: 'avatars/a.png' })
    const file = new File(['x'], 'moi.png', { type: 'image/png' })
    await userEvent.upload(await screen.findByLabelText('Photo de profil'), file)
    await waitFor(() => expect(api.put).toHaveBeenCalled())
    const [path, form] = api.put.mock.calls[0]
    expect(path).toBe('/users/me/avatar')
    expect(form.get('file').name).toBe('moi.png')
  })

  it('change le mot de passe', async () => {
    renderAt('/profil')
    api.post.mockResolvedValue(null)
    await userEvent.type(
      await screen.findByLabelText(/^Mot de passe actuel( \*)?( \(obligatoire\))?$/),
      'password123',
    )
    await userEvent.type(
      screen.getByLabelText(/^Nouveau mot de passe( \*)?( \(obligatoire\))?$/),
      'brandnewpass1',
    )
    await userEvent.type(screen.getByLabelText('Confirmation'), 'brandnewpass1')
    await userEvent.click(screen.getByRole('button', { name: 'Changer le mot de passe' }))
    await waitFor(() =>
      expect(api.post).toHaveBeenCalledWith('/users/me/password', {
        current_password: 'password123',
        new_password: 'brandnewpass1',
      }),
    )
  })

  it('signale un mot de passe actuel incorrect', async () => {
    renderAt('/profil')
    api.post.mockRejectedValue(new ApiError(400, 'BAD_REQUEST', 'x'))
    await userEvent.type(
      await screen.findByLabelText(/^Mot de passe actuel( \*)?( \(obligatoire\))?$/),
      'wrong',
    )
    await userEvent.type(
      screen.getByLabelText(/^Nouveau mot de passe( \*)?( \(obligatoire\))?$/),
      'brandnewpass1',
    )
    await userEvent.type(screen.getByLabelText('Confirmation'), 'brandnewpass1')
    await userEvent.click(screen.getByRole('button', { name: 'Changer le mot de passe' }))
    expect(await screen.findByText('Mot de passe actuel incorrect.')).toBeInTheDocument()
  })
})

/** Fiche et équipe de l'entreprise. */
describe('mon entreprise', () => {
  it('invite à contacter la MDE sans entreprise', async () => {
    renderAt('/mon-entreprise')
    expect(await screen.findByText(/aucune entreprise/)).toBeInTheDocument()
  })

  it('est en lecture seule pour un simple membre', async () => {
    renderAt('/mon-entreprise', { ...me, company_id: 'c1' })
    expect(await screen.findByLabelText(/^Nom( \*)?( \(obligatoire\))?$/)).toBeDisabled()
    expect(
      screen.queryByRole('button', { name: 'Ajouter un collaborateur' }),
    ).not.toBeInTheDocument()
  })

  it("permet à l'admin de modifier et d'agir sur l'équipe", async () => {
    renderAt('/mon-entreprise', { ...me, company_id: 'c1', is_company_admin: true })
    api.patch.mockResolvedValue(acme)
    api.put.mockResolvedValue(null)
    api.post.mockResolvedValue(null)
    const name = await screen.findByLabelText(/^Nom( \*)?( \(obligatoire\))?$/)
    expect(name).toBeEnabled()
    await userEvent.type(screen.getByLabelText('Localisation'), 'Rodez')
    await userEvent.click(screen.getByRole('button', { name: 'Enregistrer' }))
    await waitFor(() =>
      expect(api.patch).toHaveBeenCalledWith(
        '/companies/c1',
        expect.objectContaining({ location: 'Rodez' }),
      ),
    )
    expect(await screen.findByText('Cléo Colle')).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Rendre admin' }))
    await waitFor(() =>
      expect(api.put).toHaveBeenCalledWith('/users/u2/company-admin', { is_company_admin: true }),
    )
    await userEvent.click(screen.getByRole('button', { name: 'Désactiver' }))
    await waitFor(() => expect(api.post).toHaveBeenCalledWith('/users/u2/deactivate'))
  })

  it('crée un collaborateur', async () => {
    renderAt('/mon-entreprise', { ...me, company_id: 'c1', is_company_admin: true })
    api.post.mockResolvedValue({})
    await userEvent.click(await screen.findByRole('button', { name: 'Ajouter un collaborateur' }))
    const dialog = await screen.findByRole('dialog')
    await userEvent.type(screen.getByLabelText(/^Email( \*)?( \(obligatoire\))?$/), 'new@x.fr')
    await userEvent.type(screen.getByLabelText('Mot de passe temporaire'), 'temporaire1')
    await userEvent.click(screen.getByRole('button', { name: 'Créer le compte' }))
    await waitFor(() =>
      expect(api.post).toHaveBeenCalledWith(
        '/users',
        expect.objectContaining({ email: 'new@x.fr', company_id: 'c1' }),
      ),
    )
    await waitFor(() => expect(dialog).not.toBeInTheDocument())
  })
})
