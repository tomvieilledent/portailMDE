import { keepPreviousData, useQuery } from '@tanstack/react-query'

import { api } from '../../lib/api'

export const PAGE_SIZE = 24

export function usePeople(params) {
  return useQuery({
    queryKey: ['directory', 'people', params],
    queryFn: () => api.get('/directory/people', { limit: PAGE_SIZE, ...params }),
    placeholderData: keepPreviousData,
  })
}

export function useCompanies(params) {
  return useQuery({
    queryKey: ['directory', 'companies', params],
    queryFn: () => api.get('/directory/companies', { limit: PAGE_SIZE, ...params }),
    placeholderData: keepPreviousData,
  })
}

export function useCompany(id) {
  return useQuery({ queryKey: ['companies', id], queryFn: () => api.get(`/companies/${id}`) })
}

export function useCompanyMembers(id) {
  return useQuery({
    queryKey: ['companies', id, 'members'],
    queryFn: () => api.get(`/companies/${id}/members`),
  })
}
