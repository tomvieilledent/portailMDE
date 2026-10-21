/** Modale de création d'un compte utilisateur. */

import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'

import { Button, Input, Modal, useToast } from '../../components/ui'
import { api } from '../../lib/api'
import { PERMISSION_LABELS } from './labels'

/** Cases à cocher des droits du staff (réutilisées par la modale de rôle). */
export function PermissionCheckboxes({ value, onChange }) {
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

/**
 * Création d'un compte : identité, email et mot de passe temporaire. Le compte est un simple
 * membre sans entreprise ; il est rattaché à une entreprise lors de la création de celle-ci
 * (propriétaire) ou par l'administrateur de l'entreprise.
 */
export default function UserFormModal({ onClose }) {
  const toast = useToast()
  const queryClient = useQueryClient()
  const [values, setValues] = useState({
    email: '',
    password: '',
    first_name: '',
    last_name: '',
  })

  const create = useMutation({
    mutationFn: () =>
      api.post('/users', {
        email: values.email.trim(),
        password: values.password,
        first_name: values.first_name.trim() || null,
        last_name: values.last_name.trim() || null,
      }),
    onSuccess: () => {
      toast.success('Compte créé : le mot de passe temporaire a été envoyé par email.')
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
          hint="8 caractères minimum. Envoyé par email ; à changer à la première connexion."
          {...bind('password')}
        />
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
