// Stockage des jetons JWT. localStorage peut être indisponible (navigation privée) : tout est protégé.
const ACCESS = 'access_token'
const REFRESH = 'refresh_token'

function read(key) {
  try {
    return localStorage.getItem(key)
  } catch {
    return null
  }
}

export const tokens = {
  get access() {
    return read(ACCESS)
  },
  get refresh() {
    return read(REFRESH)
  },
  set({ access_token, refresh_token }) {
    try {
      localStorage.setItem(ACCESS, access_token)
      localStorage.setItem(REFRESH, refresh_token)
    } catch {
      /* stockage indisponible */
    }
  },
  clear() {
    try {
      localStorage.removeItem(ACCESS)
      localStorage.removeItem(REFRESH)
    } catch {
      /* stockage indisponible */
    }
  },
}
