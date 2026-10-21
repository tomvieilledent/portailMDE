import { tokens } from './tokens'

const BASE = '/api/v1'

/** Erreur renvoyée par l'API (`{error: {code, message, details}}`). */
export class ApiError extends Error {
  constructor(status, code, message, details) {
    super(message)
    this.status = status
    this.code = code
    this.details = details
  }
}

let refreshing = null

/** Renouvelle la paire de jetons ; les appels simultanés partagent la même requête. */
async function refreshTokens() {
  if (!tokens.refresh) return false
  refreshing ??= fetch(`${BASE}/auth/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: tokens.refresh }),
  })
    .then(async (response) => {
      if (!response.ok) return false
      tokens.set(await response.json())
      return true
    })
    .catch(() => false)
    .finally(() => {
      refreshing = null
    })
  return refreshing
}

async function parseError(response) {
  const body = await response.json().catch(() => null)
  const error = body?.error ?? {}
  return new ApiError(
    response.status,
    error.code ?? 'UNKNOWN',
    error.message ?? response.statusText,
    error.details,
  )
}

/**
 * Appel JSON vers l'API. Ajoute le jeton, retente une fois après renouvellement sur 401
 * et émet `auth:logout` si la session ne peut plus être renouvelée.
 */
export async function request(
  path,
  { method = 'GET', body, params, auth = true, retry = true } = {},
) {
  const url = new URL(BASE + path, window.location.origin)
  Object.entries(params ?? {}).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') url.searchParams.set(key, value)
  })

  const headers = {}
  let payload
  if (body instanceof FormData) {
    payload = body
  } else if (body !== undefined) {
    headers['Content-Type'] = 'application/json'
    payload = JSON.stringify(body)
  }
  if (auth && tokens.access) headers.Authorization = `Bearer ${tokens.access}`

  const response = await fetch(url, { method, headers, body: payload })

  if (response.status === 401 && auth && retry && (await refreshTokens())) {
    return request(path, { method, body, params, auth, retry: false })
  }
  if (response.status === 401 && auth) {
    tokens.clear()
    window.dispatchEvent(new Event('auth:logout'))
  }
  if (!response.ok) throw await parseError(response)
  return response.status === 204 ? null : response.json()
}

export const api = {
  get: (path, params) => request(path, { params }),
  post: (path, body, options) => request(path, { method: 'POST', body, ...options }),
  put: (path, body) => request(path, { method: 'PUT', body }),
  patch: (path, body) => request(path, { method: 'PATCH', body }),
  delete: (path) => request(path, { method: 'DELETE' }),
}
