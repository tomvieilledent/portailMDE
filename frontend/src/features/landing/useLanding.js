import { useQuery } from '@tanstack/react-query'

import { api } from '../../lib/api'
import { defaultLanding } from './defaultContent'

/** Contenu éditable de la page d'accueil (public, avec repli sur le contenu par défaut). */
export function useLanding() {
  const query = useQuery({
    queryKey: ['content', 'landing'],
    queryFn: () => api.get('/content/landing'),
    select: (data) => data.value,
    retry: false,
  })
  return { content: { ...defaultLanding, ...(query.data ?? {}) }, isLoading: query.isLoading }
}
