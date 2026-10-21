// Client API centralisé : ajoute le token JWT, parse le JSON, normalise les erreurs.
// Toutes les pages importent `api` plutôt que de réécrire `fetch` partout.

// Par défaut on passe par le proxy Vite (/api → backend :8000, voir vite.config.js)
// pour n'exposer QUE le port 3000 au navigateur (port forwarding, CORS).
// VITE_API_URL permet de forcer une URL absolue si besoin.
const BASE = import.meta.env.VITE_API_URL || '/api'

const TOKEN_KEY = 'access_token'
const REFRESH_KEY = 'refresh_token'

export function getToken() {
  return localStorage.getItem(TOKEN_KEY)
}

// Le backend renvoie les images uploadées en chemin relatif (/uploads/…).
// Sans préfixe, le navigateur les résout sur l'origine du front (:3000) → 404.
// On les rattache au backend ; les URLs absolues / blob / data sont laissées telles quelles.
export function mediaUrl(path) {
  if (!path) return path
  if (/^(https?:|blob:|data:)/.test(path)) return path
  return `${BASE}${path.startsWith('/') ? '' : '/'}${path}`
}

export function setTokens({ access_token, refresh_token }) {
  if (access_token) localStorage.setItem(TOKEN_KEY, access_token)
  if (refresh_token) localStorage.setItem(REFRESH_KEY, refresh_token)
}

export function clearTokens() {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(REFRESH_KEY)
}

// Erreur HTTP enrichie (status + message backend) pour pouvoir l'afficher proprement.
export class ApiError extends Error {
  constructor(message, status) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

async function request(path, { method = 'GET', body, auth = true, headers = {} } = {}) {
  // Les uploads (logo, photo…) passent par un FormData : on laisse alors le
  // navigateur poser le Content-Type (avec sa boundary) et on n'encode pas en JSON.
  const isForm = typeof FormData !== 'undefined' && body instanceof FormData
  const finalHeaders = { ...(isForm ? {} : { 'Content-Type': 'application/json' }), ...headers }
  const token = getToken()
  if (auth && token) finalHeaders.Authorization = `Bearer ${token}`

  let res
  try {
    res = await fetch(`${BASE}${path}`, {
      method,
      headers: finalHeaders,
      body: body !== undefined ? (isForm ? body : JSON.stringify(body)) : undefined,
    })
  } catch (networkErr) {
    throw new ApiError('Impossible de joindre le serveur. Est-il démarré ?', 0)
  }

  if (res.status === 204) return null

  let data = null
  try {
    data = await res.json()
  } catch (_) {
    /* réponse sans corps JSON */
  }

  if (!res.ok) {
    // Le backend renvoie {error: {code, message, details?}} ; on extrait le
    // message lisible plutôt que l'objet entier (sinon "[object Object]").
    const message =
      data?.error?.message ||
      (typeof data?.error === 'string' ? data.error : null) ||
      data?.message ||
      data?.msg ||
      `Erreur ${res.status}`
    // Session invalide/expirée sur un appel authentifié : on déconnecte
    // proprement pour que l'UI repasse à l'écran de connexion.
    if (res.status === 401 && auth) {
      clearTokens()
      if (typeof window !== 'undefined') window.dispatchEvent(new Event('auth:logout'))
    }
    throw new ApiError(message, res.status)
  }
  return data
}

export const api = {
  request,

  // --- Auth ---
  login: (email, password) =>
    request('/auth/login', { method: 'POST', body: { email, password }, auth: false }),
  register: (payload) =>
    request('/auth/register', { method: 'POST', body: payload, auth: false }),
  logout: () => request('/auth/logout', { method: 'POST' }),
  me: () => request('/users/me'),
  updateMe: (payload) => request('/users/me', { method: 'PATCH', body: payload }),
  forgotPassword: (email) =>
    request('/auth/forgot-password', { method: 'POST', body: { email }, auth: false }),
  resetPassword: (reset_token, password) =>
    request('/auth/reset-password', { method: 'POST', body: { reset_token, password }, auth: false }),

  // --- Contact (public) ---
  sendContact: (payload) =>
    request('/contact', { method: 'POST', body: payload, auth: false }),

  // --- Users ---
  getUsers: (params = '') => request(`/users${params}`),

  // --- Companies ---
  getCompanies: () => request('/companies'),
  createCompany: (payload) => request('/companies', { method: 'POST', body: payload }),
  updateCompany: (id, payload) => request(`/companies/${id}`, { method: 'PATCH', body: payload }),
  deactivateCompany: (id) => request(`/companies/${id}/deactivate`, { method: 'PATCH' }),
  reactivateCompany: (id) => request(`/companies/${id}/reactivate`, { method: 'PATCH' }),
  deleteCompany: (id) => request(`/companies/${id}`, { method: 'DELETE' }),

  // --- Users (admin) ---
  createUser: (payload) => request('/users', { method: 'POST', body: payload }),
  deactivateUser: (id) => request(`/users/${id}/deactivate`, { method: 'PATCH' }),
  reactivateUser: (id) => request(`/users/${id}/reactivate`, { method: 'PATCH' }),
  setUserRole: (id, is_super_admin) =>
    request(`/users/${id}/role`, { method: 'PATCH', body: { is_super_admin } }),
  setUserPermissions: (id, { is_staff, permissions }) =>
    request(`/users/${id}/permissions`, { method: 'PATCH', body: { is_staff, permissions } }),
  setUserCompanyRole: (id, is_company_admin) =>
    request(`/users/${id}/company-admin`, { method: 'PATCH', body: { is_company_admin } }),
  deleteUser: (id) => request(`/users/${id}`, { method: 'DELETE' }),
  resetUserPassword: (id, password) =>
    request(`/users/${id}/reset-password`, { method: 'POST', body: { password } }),

  // --- Trainings ---
  getTrainings: () => request('/trainings'),
  createTraining: (payload) => request('/trainings', { method: 'POST', body: payload }),
  updateTraining: (id, payload) => request(`/trainings/${id}`, { method: 'PATCH', body: payload }),
  removeTrainingDocument: (id, path) =>
    request(`/trainings/${id}/documents`, { method: 'DELETE', body: { path } }),
  expressInterest: (id) => request(`/trainings/${id}/interest`, { method: 'POST' }),
  removeInterest: (id) => request(`/trainings/${id}/interest`, { method: 'DELETE' }),

  // --- Training sessions (programmation) ---
  getSessions: () => request('/training-sessions'),
  createSession: (trainingId, payload) =>
    request(`/trainings/${trainingId}/sessions`, { method: 'POST', body: payload }),
  updateSession: (id, payload) =>
    request(`/training-sessions/${id}`, { method: 'PATCH', body: payload }),
  deleteSession: (id) => request(`/training-sessions/${id}`, { method: 'DELETE' }),
  enrollSession: (id) => request(`/training-sessions/${id}/enroll`, { method: 'POST' }),
  unenrollSession: (id) => request(`/training-sessions/${id}/enroll`, { method: 'DELETE' }),
  // Mes inscriptions (type: 'enrolled' | 'interested' | 'completed').
  getMyTrainings: (type) => request(`/me/trainings${type ? `?type=${type}` : ''}`),
  // Inscrits à une formation (admin / staff manage_trainings).
  getTrainingEnrollments: (trainingId, type) =>
    request(`/trainings/${trainingId}/enrollments${type ? `?type=${type}` : ''}`),

  // --- Events (agenda) ---
  getEvents: () => request('/events'),
  createEvent: (payload) => request('/events', { method: 'POST', body: payload }),
  updateEvent: (id, payload) => request(`/events/${id}`, { method: 'PATCH', body: payload }),
  deleteEvent: (id) => request(`/events/${id}`, { method: 'DELETE' }),

  // --- Monthly export (super-admin) ---
  getMonthlyExports: () => request('/exports/monthly'),
  generateMonthlyExport: (payload = {}) =>
    request('/exports/monthly', { method: 'POST', body: payload }),

  // --- News ---
  getNews: () => request('/news'),
  syncNews: () => request('/news/sync', { method: 'POST' }),
  getSavedNews: () => request('/news/saved'),
  saveNews: (payload) => request('/news/saved', { method: 'POST', body: payload }),
  unsaveNews: (savedId) => request(`/news/saved/${savedId}`, { method: 'DELETE' }),

  // --- Chat ---
  getConversations: () => request('/conversations'),
  createConversation: (payload) => request('/conversations', { method: 'POST', body: payload }),
  getConversation: (id) => request(`/conversations/${id}`),
  renameConversation: (id, title) => request(`/conversations/${id}`, { method: 'PATCH', body: { title } }),
  addParticipant: (id, participantId) =>
    request(`/conversations/${id}`, { method: 'PATCH', body: { participant_id: participantId, action: 'add' } }),
  removeParticipant: (id, participantId) =>
    request(`/conversations/${id}`, { method: 'PATCH', body: { participant_id: participantId, action: 'remove' } }),
  leaveConversation: (id) => request(`/conversations/${id}`, { method: 'DELETE' }),
  getConversationMessages: (id) => request(`/conversations/${id}/messages`),
  markConversationRead: (id) => request(`/conversations/${id}/read`, { method: 'POST' }),
  getDirectMessages: (otherUserId) => request(`/messages/direct/${otherUserId}`),
  markDirectRead: (otherUserId) => request(`/messages/direct/${otherUserId}`, { method: 'POST' }),
  getUnreadCount: () => request('/messages/unread'),
  uploadMessageAttachment: (formData) => request('/messages/attachment', { method: 'POST', body: formData }),

  // --- Site content (editable landing page) ---
  getLandingContent: () => request('/content/landing'),
  updateLandingContent: (content) => request('/content/landing', { method: 'PUT', body: { content } }),

  // --- Invitations (RSVP for events & trainings) ---
  createInvitations: (payload) => request('/invitations', { method: 'POST', body: payload }),
  getMyInvitations: () => request('/me/invitations'),
  markInvitationsRead: () => request('/me/invitations', { method: 'POST' }),
  respondInvitation: (id, status) => request(`/invitations/${id}`, { method: 'PATCH', body: { status } }),
  getTargetInvitations: (targetType, targetId) =>
    request(`/invitations?target_type=${targetType}&target_id=${targetId}`),
}

export default api
