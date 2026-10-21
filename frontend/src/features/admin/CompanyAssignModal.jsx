/** Modale de rattachement d'un compte à une entreprise et de son statut d'administrateur. */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'

import { Button, Modal, Select, useToast } from '../../components/ui'
import { api } from '../../lib/api'
import { fullName } from '../directory/labels'

/** Changement d'entreprise et statut d'administrateur d'entreprise (droit de gestion des entreprises). */
export default function CompanyAssignModal({ target, onClose }) {
  const toast = useToast()
  const queryClient = useQueryClient()
  const [companyId, setCompanyId] = useState(target.company_id ?? '')
  const [isAdmin, setIsAdmin] = useState(target.is_company_admin)
  const companies = useQuery({
    queryKey: ['admin', 'companies', 'all'],
    queryFn: () => api.get('/companies', { limit: 200 }),
  })

  const save = useMutation({
    mutationFn: async () => {
      const current = target.company_id ?? ''
      if (companyId !== current) {
        if (companyId) await api.put(`/companies/${companyId}/members/${target.id}`)
        else await api.delete(`/companies/${current}/members/${target.id}`)
      }
      // Le rattachement remet le statut à zéro : on le réapplique si besoin.
      if (companyId && (companyId !== current ? isAdmin : isAdmin !== target.is_company_admin)) {
        await api.put(`/users/${target.id}/company-admin`, { is_company_admin: isAdmin })
      }
    },
    onSuccess: () => {
      toast.success('Entreprise mise à jour.')
      queryClient.invalidateQueries({ queryKey: ['admin'] })
      queryClient.invalidateQueries({ queryKey: ['directory'] })
      queryClient.invalidateQueries({ queryKey: ['companies'] })
      onClose()
    },
    onError: (err) => toast.error(err.status === 403 ? err.message : 'Modification impossible.'),
  })

  return (
    <Modal open onClose={onClose} title={`Entreprise de ${fullName(target)}`}>
      <div className="grid gap-4">
        <Select
          label="Entreprise"
          value={companyId}
          onChange={(e) => {
            setCompanyId(e.target.value)
            setIsAdmin(false)
          }}
        >
          <option value="">Aucune</option>
          {companies.data?.items.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </Select>
        {companyId && (
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={isAdmin}
              onChange={(e) => setIsAdmin(e.target.checked)}
            />
            Administrateur de cette entreprise
          </label>
        )}
        <div className="flex justify-end gap-2">
          <Button variant="secondary" onClick={onClose}>
            Annuler
          </Button>
          <Button loading={save.isPending} onClick={() => save.mutate()}>
            Enregistrer
          </Button>
        </div>
      </div>
    </Modal>
  )
}
