import { useQuery } from '@tanstack/react-query'

import { api } from '../../lib/api'

export const useEvents = (start, end) =>
  useQuery({
    queryKey: ['events', start, end],
    queryFn: () => api.get('/events', { start, end }),
  })

export const useMyInvitations = () =>
  useQuery({ queryKey: ['invitations'], queryFn: () => api.get('/invitations/me') })
