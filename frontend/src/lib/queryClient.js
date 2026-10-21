/** Configuration du client de requêtes. */

import { QueryClient } from '@tanstack/react-query'

import { ApiError } from './api'

/** Client de requêtes partagé par l'application. */
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      // Inutile de réessayer une erreur 4xx : elle se reproduira à l'identique.
      retry: (count, error) => !(error instanceof ApiError && error.status < 500) && count < 2,
    },
  },
})
