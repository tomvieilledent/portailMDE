/** Requêtes de la messagerie. */

import { useInfiniteQuery, useQuery } from '@tanstack/react-query'

import { api } from '../../lib/api'

/** Nombre de messages par page. */
export const MESSAGES_PAGE = 30

/** Conversations de l'utilisateur. */
export const useConversations = () =>
  useQuery({ queryKey: ['conversations'], queryFn: () => api.get('/conversations') })

/** Messages d'une conversation, paginés vers le passé (curseur `before`). */
export function useMessages(conversationId) {
  return useInfiniteQuery({
    queryKey: ['messages', conversationId],
    queryFn: ({ pageParam }) =>
      api.get(`/conversations/${conversationId}/messages`, {
        limit: MESSAGES_PAGE,
        before: pageParam,
      }),
    initialPageParam: undefined,
    getNextPageParam: (lastPage) =>
      lastPage.length === MESSAGES_PAGE ? lastPage[lastPage.length - 1].created_at : undefined,
    enabled: Boolean(conversationId),
  })
}
