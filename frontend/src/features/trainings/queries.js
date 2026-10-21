import { keepPreviousData, useQuery } from '@tanstack/react-query'

import { api } from '../../lib/api'

export const TRAINING_KINDS = { formation: 'Formation', atelier: 'Atelier' }

export const useTrainings = (params) =>
  useQuery({
    queryKey: ['trainings', 'list', params],
    queryFn: () => api.get('/trainings', { limit: 200, ...params }),
    placeholderData: keepPreviousData,
  })

export const useTraining = (id) =>
  useQuery({ queryKey: ['trainings', id], queryFn: () => api.get(`/trainings/${id}`) })

/** Inscriptions / favoris de l'utilisateur courant. */
export const useMyEnrollments = () =>
  useQuery({ queryKey: ['trainings', 'mine'], queryFn: () => api.get('/trainings/mine') })

export const useTrainingSessions = (id) =>
  useQuery({
    queryKey: ['trainings', id, 'sessions'],
    queryFn: () => api.get(`/trainings/${id}/sessions`),
  })

export const formatDateTime = (iso) =>
  new Date(iso).toLocaleString('fr-FR', {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  })
