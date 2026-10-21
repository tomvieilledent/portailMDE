/** Tests du catalogue et des fiches de formation. */

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
import TrainingPage from './TrainingPage'
import TrainingsPage from './TrainingsPage'

vi.mock('../../lib/api', async (importOriginal) => {
  const actual = await importOriginal()
  return {
    ...actual,
    api: { get: vi.fn(), post: vi.fn(), put: vi.fn(), patch: vi.fn(), delete: vi.fn() },
  }
})

const member = { id: 'me', email: 'me@x.fr', role: 'member', permissions: [] }
const manager = { ...member, role: 'staff', permissions: ['manage_trainings'] }
const excel = {
  id: 't1',
  title: 'Excel avancé',
  description: 'Tableaux croisés',
  picture_path: null,
  category: 'Bureautique',
  kind: 'formation',
  documents: ['trainings/support.pdf'],
  link: null,
  is_active: true,
  upcoming_sessions: 0,
  interested_count: 0,
}
const atelier = {
  ...excel,
  id: 't2',
  title: 'Atelier pitch',
  description: null,
  kind: 'atelier',
  category: null,
  documents: [],
}
const session = {
  id: 's1',
  training_id: 't1',
  start_at: '2026-11-10T09:00:00Z',
  end_at: '2026-11-10T17:00:00Z',
  max_participants: 2,
  location: 'Salle 3',
  link: null,
  status: 'upcoming',
  is_public: true,
  enrolled_count: 1,
  is_enrolled: false,
}

let mineData
let trainingOne = excel
/** Affiche la page avec l'utilisateur et les sessions donnés. */
function setup(path, user = member, sessions = [session]) {
  tokens.set({ access_token: 'A', refresh_token: 'R' })
  api.get.mockImplementation(async (url) => {
    if (url === '/users/me') return user
    if (url === '/trainings') return { items: [excel, atelier], total: 2 }
    if (url === '/trainings/mine') return mineData
    if (url === '/trainings/t1') return trainingOne
    if (url === '/trainings/t1/sessions') return sessions
    if (url === '/training-sessions/s1/enrollments') return []
    if (url === '/trainings/t1/interested') {
      return [{ id: 'e1', user: { first_name: 'Ada', last_name: 'Lovelace' } }]
    }
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
                <Route path="/formations" element={<TrainingsPage />} />
                <Route path="/formations/:trainingId" element={<TrainingPage />} />
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
  mineData = []
  trainingOne = excel
})

/** Liste, filtres et favoris. */
describe('catalogue', () => {
  it('liste et filtre les formations', async () => {
    setup('/formations')
    expect(await screen.findByText('Excel avancé')).toBeInTheDocument()
    expect(screen.getByText('Atelier pitch')).toBeInTheDocument()
    await userEvent.selectOptions(
      screen.getByLabelText(/^Type( \*)?( \(obligatoire\))?$/),
      'atelier',
    )
    expect(screen.queryByText('Excel avancé')).not.toBeInTheDocument()
    await userEvent.selectOptions(screen.getByLabelText(/^Type( \*)?( \(obligatoire\))?$/), '')
    await userEvent.type(screen.getByLabelText(/^Rechercher( \*)?( \(obligatoire\))?$/), 'croisés')
    expect(screen.queryByText('Atelier pitch')).not.toBeInTheDocument()
    expect(screen.getByText('Excel avancé')).toBeInTheDocument()
  })

  it('affiche « Mes formations » (inscrites ou favorites)', async () => {
    mineData = [
      {
        id: 'e1',
        training_id: 't1',
        interested: true,
        enrolled_at: '2026-10-01T00:00:00Z',
        completed_at: null,
      },
    ]
    setup('/formations')
    await screen.findByText('Excel avancé')
    expect(await screen.findByText('Inscrit')).toBeInTheDocument()
    await userEvent.click(screen.getByRole('tab', { name: 'Mes formations' }))
    expect(screen.getByText('Excel avancé')).toBeInTheDocument()
    expect(screen.queryByText('Atelier pitch')).not.toBeInTheDocument()
  })

  it('ajoute une formation aux favoris', async () => {
    api.put.mockResolvedValue(null)
    setup('/formations')
    const buttons = await screen.findAllByRole('button', { name: "Cette formation m'intéresse" })
    await userEvent.click(buttons[0])
    await waitFor(() => expect(api.put).toHaveBeenCalledWith('/trainings/t1/interest'))
  })

  it('réserve la création au staff', async () => {
    setup('/formations')
    await screen.findByText('Excel avancé')
    expect(screen.queryByRole('button', { name: /Nouvelle formation/ })).not.toBeInTheDocument()
  })

  it('crée une formation', async () => {
    api.post.mockResolvedValue({})
    setup('/formations', manager)
    await userEvent.click(await screen.findByRole('button', { name: /Nouvelle formation/ }))
    await userEvent.type(await screen.findByLabelText(/^Titre( \*)?( \(obligatoire\))?$/), 'Compta')
    await userEvent.click(screen.getByRole('button', { name: 'Enregistrer' }))
    await waitFor(() =>
      expect(api.post).toHaveBeenCalledWith('/trainings', {
        title: 'Compta',
        description: null,
        category: null,
        kind: 'formation',
        link: null,
      }),
    )
  })
})

/** Détail, sessions et inscription. */
describe('fiche formation', () => {
  it('affiche description, documents et sessions', async () => {
    setup('/formations/t1')
    expect(await screen.findByRole('heading', { name: 'Excel avancé' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /support\.pdf/ })).toHaveAttribute(
      'href',
      '/uploads/trainings/support.pdf',
    )
    expect(screen.getByText('Salle 3')).toBeInTheDocument()
    expect(screen.getByText('1/2')).toBeInTheDocument()
  })

  it("s'inscrit à une session", async () => {
    api.post.mockResolvedValue({})
    setup('/formations/t1')
    await userEvent.click(await screen.findByRole('button', { name: "S'inscrire" }))
    await waitFor(() => expect(api.post).toHaveBeenCalledWith('/training-sessions/s1/enroll'))
  })

  it('se désinscrit', async () => {
    api.delete.mockResolvedValue(null)
    setup('/formations/t1', member, [{ ...session, is_enrolled: true }])
    await userEvent.click(await screen.findByRole('button', { name: 'Se désinscrire' }))
    await waitFor(() => expect(api.delete).toHaveBeenCalledWith('/training-sessions/s1/enroll'))
  })

  it('bloque une session complète', async () => {
    setup('/formations/t1', member, [{ ...session, enrolled_count: 2 }])
    expect(await screen.findByRole('button', { name: 'Complet' })).toBeDisabled()
  })

  it('bloque une session annulée', async () => {
    setup('/formations/t1', member, [{ ...session, status: 'cancelled' }])
    expect(await screen.findByRole('button', { name: "S'inscrire" })).toBeDisabled()
    expect(screen.getByText('Annulée')).toBeInTheDocument()
  })

  it('programme une session (staff)', async () => {
    api.post.mockResolvedValue({})
    setup('/formations/t1', manager, [])
    await userEvent.click(await screen.findByRole('button', { name: /Session/ }))
    const dialog = await screen.findByRole('dialog', { name: 'Nouvelle session' })
    await userEvent.type(
      within(dialog).getByLabelText(/^Début( \*)?( \(obligatoire\))?$/),
      '2026-11-10T09:00',
    )
    await userEvent.type(
      within(dialog).getByLabelText(/^Fin( \*)?( \(obligatoire\))?$/),
      '2026-11-10T17:00',
    )
    await userEvent.click(within(dialog).getByRole('button', { name: 'Créer' }))
    await waitFor(() => {
      const [path, body] = api.post.mock.calls.at(-1)
      expect(path).toBe('/trainings/t1/sessions')
      expect(body).toMatchObject({ max_participants: 10, is_public: true })
      expect(body.start_at).toMatch(/^2026-11-10T/)
    })
  })

  it("n'affiche pas la gestion aux membres", async () => {
    setup('/formations/t1')
    await screen.findByRole('heading', { name: 'Excel avancé' })
    expect(screen.queryByRole('button', { name: 'Gérer' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Supprimer' })).not.toBeInTheDocument()
  })

  it('signale une formation introuvable', async () => {
    tokens.set({ access_token: 'A', refresh_token: 'R' })
    setup('/formations/t9')
    api.get.mockImplementation(async (url) => {
      if (url === '/users/me') return member
      if (url === '/trainings/mine') return []
      throw new Error('introuvable')
    })
    expect(await screen.findByText('Formation introuvable')).toBeInTheDocument()
  })
})

/** Demandes de formations non programmées. */
describe('demandes de formation', () => {
  it('le staff voit les personnes en attente et peut planifier', async () => {
    trainingOne = { ...excel, interested_count: 1 }
    setup('/formations/t1', manager, [])
    expect(await screen.findByText(/1 personne attend cette formation/)).toBeInTheDocument()
    expect(await screen.findByText('Ada Lovelace')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Planifier une session' })).toBeInTheDocument()
  })

  it("un membre peut dire que la formation l'intéresse, pas voir les demandes", async () => {
    setup('/formations/t1', member, [])
    expect(
      await screen.findByRole('button', { name: "Cette formation m'intéresse" }),
    ).toBeInTheDocument()
    expect(screen.queryByText(/attend cette formation/)).not.toBeInTheDocument()
  })
})
