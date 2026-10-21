/** Tests de l'annuaire des personnes et des entreprises. */

import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { AuthProvider } from '../../auth/AuthProvider'
import { ToastProvider } from '../../components/ui'
import { api } from '../../lib/api'
import { tokens } from '../../lib/tokens'
import CompaniesPage from './CompaniesPage'
import CompanyPage from './CompanyPage'
import PeoplePage from './PeoplePage'

vi.mock('../../lib/api', async (importOriginal) => {
  const actual = await importOriginal()
  return { ...actual, api: { get: vi.fn(), post: vi.fn() } }
})

const me = {
  id: 'me',
  email: 'me@x.fr',
  first_name: 'Moi',
  last_name: 'Même',
  role: 'member',
  permissions: [],
}
const ada = {
  id: 'p1',
  first_name: 'Ada',
  last_name: 'Lovelace',
  job_title: 'Ingénieure',
  email: 'ada@x.fr',
  phone: '0600000000',
  avatar_path: null,
  business_card_path: null,
  company: { id: 'c1', name: 'Acme', logo_path: null },
}
const acme = {
  id: 'c1',
  name: 'Acme',
  description: 'Fabrique tout',
  location: 'Rodez',
  website_url: 'https://acme.fr',
  logo_path: null,
  kind: 'partner',
  member_count: 2,
}

/** Affiche l'annuaire à l'adresse donnée. */
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
              <Route path="/annuaire" element={<PeoplePage />} />
              <Route path="/entreprises" element={<CompaniesPage />} />
              <Route path="/entreprises/:companyId" element={<CompanyPage />} />
              <Route path="/messagerie/:id" element={<p>messagerie ouverte</p>} />
            </Routes>
          </MemoryRouter>
        </AuthProvider>
      </ToastProvider>
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  vi.resetAllMocks()
  api.get.mockImplementation(async (path) => {
    if (path === '/users/me') return me
    if (path === '/directory/people') return { items: [ada], total: 1, limit: 24, offset: 0 }
    if (path === '/directory/companies') return { items: [acme], total: 1, limit: 24, offset: 0 }
    if (path === '/companies/c1') return acme
    if (path === '/companies/c1/members') return [{ ...ada, company: undefined }]
    throw new Error(`appel inattendu ${path}`)
  })
})

/** Recherche et fiche des personnes. */
describe('annuaire des personnes', () => {
  it('liste les personnes et ouvre la fiche', async () => {
    renderAt('/annuaire')
    await userEvent.click(await screen.findByText('Ada Lovelace'))
    const dialog = await screen.findByRole('dialog', { name: 'Ada Lovelace' })
    expect(dialog).toHaveTextContent('ada@x.fr')
    expect(screen.getByRole('link', { name: 'Acme' })).toHaveAttribute('href', '/entreprises/c1')
  })

  it('recherche avec un délai et renvoie le terme au backend', async () => {
    renderAt('/annuaire')
    await screen.findByText('Ada Lovelace')
    await userEvent.type(screen.getByLabelText('Rechercher'), 'ada')
    await waitFor(() =>
      expect(api.get).toHaveBeenCalledWith(
        '/directory/people',
        expect.objectContaining({ search: 'ada', offset: 0 }),
      ),
    )
  })

  it('démarre une conversation directe', async () => {
    api.post.mockResolvedValue({ id: 'conv1' })
    renderAt('/annuaire')
    await userEvent.click(await screen.findByText('Ada Lovelace'))
    await userEvent.click(await screen.findByRole('button', { name: /envoyer un message/i }))
    expect(api.post).toHaveBeenCalledWith('/conversations', { kind: 'direct', user_id: 'p1' })
    expect(await screen.findByText('messagerie ouverte')).toBeInTheDocument()
  })

  it('affiche un état vide', async () => {
    api.get.mockImplementation(async (path) =>
      path === '/users/me' ? me : { items: [], total: 0, limit: 24, offset: 0 },
    )
    renderAt('/annuaire')
    expect(await screen.findByText('Aucune personne trouvée')).toBeInTheDocument()
  })
})

/** Liste et fiche des entreprises. */
describe('annuaire des entreprises', () => {
  it('liste les entreprises avec leur type et filtre par type', async () => {
    renderAt('/entreprises')
    expect(await screen.findByText('Acme')).toBeInTheDocument()
    expect(screen.getByText('2 membres')).toBeInTheDocument()
    await userEvent.selectOptions(screen.getByLabelText('Type'), 'partner')
    await waitFor(() =>
      expect(api.get).toHaveBeenCalledWith(
        '/directory/companies',
        expect.objectContaining({ kind: 'partner' }),
      ),
    )
  })

  it("affiche la fiche d'une entreprise avec son équipe", async () => {
    renderAt('/entreprises/c1')
    expect(await screen.findByRole('heading', { name: 'Acme' })).toBeInTheDocument()
    expect(await screen.findByText('Ada Lovelace')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /acme\.fr/ })).toHaveAttribute(
      'rel',
      expect.stringContaining('noopener'),
    )
  })
})
