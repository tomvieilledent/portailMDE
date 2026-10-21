/** Requêtes des formations et de leurs sessions. */

import { keepPreviousData, useQuery } from '@tanstack/react-query'

import { api } from '../../lib/api'

/** Libellés des types de formation. */
export const TRAINING_KINDS = { formation: 'Formation', atelier: 'Atelier' }

/** Liste paginée des formations. */
export const useTrainings = (params) =>
  useQuery({
    queryKey: ['trainings', 'list', params],
    queryFn: () => api.get('/trainings', { limit: 200, ...params }),
    placeholderData: keepPreviousData,
  })

/** Détail d'une formation. */
export const useTraining = (id) =>
  useQuery({ queryKey: ['trainings', id], queryFn: () => api.get(`/trainings/${id}`) })

/** Inscriptions / favoris de l'utilisateur courant. */
export const useMyEnrollments = () =>
  useQuery({ queryKey: ['trainings', 'mine'], queryFn: () => api.get('/trainings/mine') })

/** Sessions d'une formation. */
export const useTrainingSessions = (id) =>
  useQuery({
    queryKey: ['trainings', id, 'sessions'],
    queryFn: () => api.get(`/trainings/${id}/sessions`),
  })

/** Personnes qui attendent la programmation d'une formation (gestionnaires). */
export const useInterested = (id, enabled) =>
  useQuery({
    queryKey: ['trainings', id, 'interested'],
    queryFn: () => api.get(`/trainings/${id}/interested`),
    enabled,
  })

/** Date et heure formatées. */
export const formatDateTime = (iso) =>
  new Date(iso).toLocaleString('fr-FR', {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  })
