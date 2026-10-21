/** Requêtes de l'agenda (événements et invitations). */

import { useQuery } from '@tanstack/react-query'

import { api } from '../../lib/api'

/** Événements visibles sur une période. */
export const useEvents = (start, end) =>
  useQuery({
    queryKey: ['events', start, end],
    queryFn: () => api.get('/events', { start, end }),
  })

/** Invitations reçues par l'utilisateur. */
export const useMyInvitations = () =>
  useQuery({ queryKey: ['invitations'], queryFn: () => api.get('/invitations/me') })
