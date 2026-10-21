/** Modale de changement de rôle et de droits d'un compte. */

import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'

import { Button, Modal, Select, useToast } from '../../components/ui'
import { api } from '../../lib/api'
import { fullName } from '../directory/labels'
import { ROLES } from './labels'
import { PermissionCheckboxes } from './UserFormModal'

/** Changement de rôle et de droits d'un compte (super admin uniquement). */
export default function RoleModal({ target, onClose }) {
  const toast = useToast()
  const queryClient = useQueryClient()
  const [role, setRole] = useState(target.role)
  const [permissions, setPermissions] = useState(target.permissions)

  const save = useMutation({
    mutationFn: () =>
      api.put(`/users/${target.id}/role`, {
        role,
        permissions: role === 'staff' ? permissions : [],
      }),
    onSuccess: () => {
      toast.success('Rôle mis à jour.')
      queryClient.invalidateQueries({ queryKey: ['admin', 'users'] })
      onClose()
    },
    onError: (err) => toast.error(err.status === 403 ? err.message : 'Modification impossible.'),
  })

  return (
    <Modal open onClose={onClose} title={`Rôle de ${fullName(target)}`}>
      <div className="grid gap-4">
        <Select label="Rôle" value={role} onChange={(e) => setRole(e.target.value)}>
          {Object.entries(ROLES).map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </Select>
        {role === 'staff' && <PermissionCheckboxes value={permissions} onChange={setPermissions} />}
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
