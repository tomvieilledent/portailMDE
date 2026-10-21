/** Requêtes de l'agenda (événements et invitations). */

import { useQuery } from '@tanstack/react-query'

import { api } from '../../lib/api'

/** Événements visibles sur une période. */
export const useEvents = (start, end) =>
  useQuery({
    queryKey: ['events', start, end],
    queryFn: () => api.get('/events', { start, end }),
  })

/** Sessions de formation sur une période (avec l'inscription de l'utilisateur courant). */
export const useSessions = (start, end) =>
  useQuery({
    queryKey: ['training-sessions', start, end],
    queryFn: () =>
      api.get('/training-sessions', { start: `${start}T00:00:00`, end: `${end}T23:59:59` }),
  })

/** Invitations reçues par l'utilisateur. */
export const useMyInvitations = () =>
  useQuery({ queryKey: ['invitations'], queryFn: () => api.get('/invitations/me') })
