/** Requêtes de l'annuaire (personnes et entreprises). */

import { keepPreviousData, useQuery } from '@tanstack/react-query'

import { api } from '../../lib/api'

/** Nombre d'éléments par page. */
export const PAGE_SIZE = 24

/** Liste paginée des personnes. */
export function usePeople(params) {
  return useQuery({
    queryKey: ['directory', 'people', params],
    queryFn: () => api.get('/directory/people', { limit: PAGE_SIZE, ...params }),
    placeholderData: keepPreviousData,
  })
}

/** Liste paginée des entreprises. */
export function useCompanies(params) {
  return useQuery({
    queryKey: ['directory', 'companies', params],
    queryFn: () => api.get('/directory/companies', { limit: PAGE_SIZE, ...params }),
    placeholderData: keepPreviousData,
  })
}

/** Fiche d'une entreprise. */
export function useCompany(id) {
  return useQuery({ queryKey: ['companies', id], queryFn: () => api.get(`/companies/${id}`) })
}

/** Membres d'une entreprise. */
export function useCompanyMembers(id) {
  return useQuery({
    queryKey: ['companies', id, 'members'],
    queryFn: () => api.get(`/companies/${id}/members`),
  })
}
