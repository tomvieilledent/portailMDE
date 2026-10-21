import { keepPreviousData, useQuery } from '@tanstack/react-query'

import { api } from '../../lib/api'

export const NEWS_PAGE = 20

export const useNews = (params) =>
  useQuery({
    queryKey: ['news', 'list', params],
    queryFn: () => api.get('/news', { limit: NEWS_PAGE, ...params }),
    placeholderData: keepPreviousData,
  })

export const useSavedNews = () =>
  useQuery({ queryKey: ['news', 'saved'], queryFn: () => api.get('/news/saved') })

export const formatPublished = (iso) =>
  iso
    ? new Date(iso).toLocaleDateString('fr-FR', { day: 'numeric', month: 'long', year: 'numeric' })
    : ''
