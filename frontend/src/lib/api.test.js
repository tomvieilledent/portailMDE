/** Tests du client HTTP de l'API. */

import { beforeEach, describe, expect, it, vi } from 'vitest'

import { ApiError, api } from './api'
import { tokens } from './tokens'

/** Fabrique une réponse JSON. */
const json = (body, status = 200) => Promise.resolve(new Response(JSON.stringify(body), { status }))

beforeEach(() => {
  vi.restoreAllMocks()
})

/** Jetons, renouvellement et erreurs. */
describe('api client', () => {
  it('ajoute le jeton et les paramètres de requête', async () => {
    tokens.set({ access_token: 'A', refresh_token: 'R' })
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockImplementation(() => json({ ok: true }))
    await api.get('/users', { search: 'ada', empty: '' })
    const [url, options] = fetchMock.mock.calls[0]
    expect(url.pathname + url.search).toBe('/api/v1/users?search=ada')
    expect(options.headers.Authorization).toBe('Bearer A')
  })

  it("transforme les erreurs de l'API en ApiError", async () => {
    vi.spyOn(globalThis, 'fetch').mockImplementation(() =>
      json({ error: { code: 'NOT_FOUND', message: 'introuvable' } }, 404),
    )
    await expect(api.get('/x')).rejects.toMatchObject({
      status: 404,
      code: 'NOT_FOUND',
      message: 'introuvable',
    })
    await expect(api.get('/x')).rejects.toBeInstanceOf(ApiError)
  })

  it('renouvelle le jeton sur 401 puis rejoue la requête', async () => {
    tokens.set({ access_token: 'old', refresh_token: 'R' })
    const fetchMock = vi
      .spyOn(globalThis, 'fetch')
      .mockImplementationOnce(() => json({ error: { code: 'UNAUTHORIZED', message: 'x' } }, 401))
      .mockImplementationOnce(() => json({ access_token: 'new', refresh_token: 'R2' }))
      .mockImplementationOnce(() => json({ hello: 'world' }))
    expect(await api.get('/me')).toEqual({ hello: 'world' })
    expect(fetchMock).toHaveBeenCalledTimes(3)
    expect(tokens.access).toBe('new')
  })

  it('déconnecte si le renouvellement échoue', async () => {
    tokens.set({ access_token: 'old', refresh_token: 'R' })
    const onLogout = vi.fn()
    window.addEventListener('auth:logout', onLogout)
    vi.spyOn(globalThis, 'fetch').mockImplementation(() =>
      json({ error: { code: 'UNAUTHORIZED', message: 'x' } }, 401),
    )
    await expect(api.get('/me')).rejects.toMatchObject({ status: 401 })
    expect(onLogout).toHaveBeenCalled()
    expect(tokens.access).toBeNull()
    window.removeEventListener('auth:logout', onLogout)
  })

  it('retourne null sur 204', async () => {
    vi.spyOn(globalThis, 'fetch').mockImplementation(() =>
      Promise.resolve(new Response(null, { status: 204 })),
    )
    expect(await api.delete('/x')).toBeNull()
  })
})
