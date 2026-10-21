/** Modale de création d'un compte utilisateur. */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'

import { useAuth } from '../../auth/AuthProvider'
import { isSuperAdmin } from '../../auth/permissions'
import { Button, Input, Modal, Select, useToast } from '../../components/ui'
import { api } from '../../lib/api'
import { PERMISSION_LABELS, ROLES } from './labels'

/** Cases à cocher des droits du staff. */
function PermissionCheckboxes({ value, onChange }) {
  return (
    <fieldset className="space-y-1">
      <legend className="mb-1 text-sm font-medium">Droits du staff</legend>
      {Object.entries(PERMISSION_LABELS).map(([key, label]) => (
        <label key={key} className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={value.includes(key)}
            onChange={(e) =>
              onChange(e.target.checked ? [...value, key] : value.filter((k) => k !== key))
            }
          />
          {label}
        </label>
      ))}
    </fieldset>
  )
}

/** Création d'un compte (le staff choisit l'entreprise ; seul le super admin attribue un rôle). */
export default function UserFormModal({ onClose }) {
  const { user } = useAuth()
  const toast = useToast()
  const queryClient = useQueryClient()
  const superAdmin = isSuperAdmin(user)
  const [values, setValues] = useState({
    email: '',
    password: '',
    first_name: '',
    last_name: '',
    company_id: '',
    role: 'member',
    is_company_admin: false,
    permissions: [],
  })
  const companies = useQuery({
    queryKey: ['companies', 'options'],
    queryFn: () => api.get('/companies', { limit: 200 }),
  })

  const create = useMutation({
    mutationFn: () =>
      api.post('/users', {
        email: values.email.trim(),
        password: values.password,
        first_name: values.first_name.trim() || null,
        last_name: values.last_name.trim() || null,
        company_id: values.company_id || null,
        role: values.role,
        is_company_admin: values.is_company_admin,
        permissions: values.role === 'staff' ? values.permissions : [],
      }),
    onSuccess: () => {
      toast.success('Compte créé : un email de bienvenue a été envoyé.')
      queryClient.invalidateQueries({ queryKey: ['admin', 'users'] })
      onClose()
    },
    onError: (err) =>
      toast.error(err.status === 409 ? 'Cet email est déjà utilisé.' : 'Création impossible.'),
  })
  const bind = (name) => ({
    value: values[name],
    onChange: (e) => setValues((v) => ({ ...v, [name]: e.target.value })),
  })

  return (
    <Modal open onClose={onClose} title="Nouveau compte">
      <form
        onSubmit={(e) => {
          e.preventDefault()
          create.mutate()
        }}
        className="grid gap-4"
      >
        <div className="grid gap-4 sm:grid-cols-2">
          <Input label="Prénom" {...bind('first_name')} />
          <Input label="Nom" {...bind('last_name')} />
        </div>
        <Input label="Email" type="email" required {...bind('email')} />
        <Input
          label="Mot de passe temporaire"
          required
          minLength={8}
          hint="8 caractères minimum, à communiquer à la personne."
          {...bind('password')}
        />
        <Select label="Entreprise" {...bind('company_id')}>
          <option value="">Aucune</option>
          {companies.data?.items.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </Select>
        {values.company_id && (
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={values.is_company_admin}
              onChange={(e) => setValues((v) => ({ ...v, is_company_admin: e.target.checked }))}
            />
            Administrateur de son entreprise
          </label>
        )}
        {superAdmin && (
          <Select label="Rôle" {...bind('role')}>
            {Object.entries(ROLES).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </Select>
        )}
        {values.role === 'staff' && (
          <PermissionCheckboxes
            value={values.permissions}
            onChange={(permissions) => setValues((v) => ({ ...v, permissions }))}
          />
        )}
        <div className="flex justify-end gap-2">
          <Button variant="secondary" onClick={onClose}>
            Annuler
          </Button>
          <Button type="submit" loading={create.isPending}>
            Créer le compte
          </Button>
        </div>
      </form>
    </Modal>
  )
}

export { PermissionCheckboxes }
