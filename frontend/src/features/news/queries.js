/** Requêtes des actualités. */

import { keepPreviousData, useQuery } from '@tanstack/react-query'

import { api } from '../../lib/api'

/** Nombre d'actualités par page. */
export const NEWS_PAGE = 20

/** Liste paginée des actualités. */
export const useNews = (params, options = {}) =>
  useQuery({
    queryKey: ['news', 'list', params],
    queryFn: () => api.get('/news', { limit: NEWS_PAGE, ...params }),
    placeholderData: keepPreviousData,
    ...options,
  })

/** Actualités mises en favori. */
export const useSavedNews = () =>
  useQuery({ queryKey: ['news', 'saved'], queryFn: () => api.get('/news/saved') })

/** Date de publication formatée. */
export const formatPublished = (iso) =>
  iso
    ? new Date(iso).toLocaleDateString('fr-FR', { day: 'numeric', month: 'long', year: 'numeric' })
    : ''
