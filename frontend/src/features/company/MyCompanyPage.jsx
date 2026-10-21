/** Page « Mon entreprise » : fiche et équipe. */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'

import { useAuth } from '../../auth/AuthProvider'
import { canManageCompany } from '../../auth/permissions'
import PageHeader from '../../components/layout/PageHeader'
import {
  Avatar,
  Badge,
  Button,
  Card,
  EmptyState,
  ImageUpload,
  Input,
  Modal,
  Spinner,
  Textarea,
  uploadUrl,
  useToast,
} from '../../components/ui'
import { CompanyLogo } from '../directory/CompaniesPage'
import { fullName } from '../directory/labels'
import { api } from '../../lib/api'

/** Formulaire de la fiche de l'entreprise. */
function CompanyForm({ company, canEdit }) {
  const toast = useToast()
  const queryClient = useQueryClient()
  const [values, setValues] = useState({
    name: company.name,
    description: company.description ?? '',
    location: company.location ?? '',
    website_url: company.website_url ?? '',
  })
  const refresh = () => queryClient.invalidateQueries({ queryKey: ['companies'] })
  const save = useMutation({
    mutationFn: () =>
      api.patch(`/companies/${company.id}`, {
        name: values.name.trim(),
        description: values.description.trim() || null,
        location: values.location.trim() || null,
        website_url: values.website_url.trim() || null,
      }),
    onSuccess: () => {
      toast.success('Entreprise mise à jour.')
      refresh()
    },
    onError: () => toast.error('Mise à jour impossible.'),
  })
  const logo = useMutation({
    mutationFn: (file) => {
      const form = new FormData()
      form.append('file', file)
      return api.put(`/companies/${company.id}/logo`, form)
    },
    onSuccess: () => {
      toast.success('Logo mis à jour.')
      refresh()
    },
  })
  const bind = (name) => ({
    value: values[name],
    disabled: !canEdit,
    onChange: (e) => setValues((v) => ({ ...v, [name]: e.target.value })),
  })

  return (
    <Card className="mb-8">
      <form
        onSubmit={(e) => {
          e.preventDefault()
          save.mutate()
        }}
        className="grid gap-4"
      >
        {canEdit && (
          <ImageUpload
            label="Logo"
            loading={logo.isPending}
            error={logo.error?.message}
            onSelect={logo.mutate}
            preview={<CompanyLogo company={company} />}
          />
        )}
        <Input label="Nom" required {...bind('name')} />
        <Textarea label="Description" {...bind('description')} />
        <div className="grid gap-4 sm:grid-cols-2">
          <Input label="Localisation" {...bind('location')} />
          <Input label="Site web" type="url" placeholder="https://" {...bind('website_url')} />
        </div>
        {canEdit && (
          <div>
            <Button type="submit" loading={save.isPending}>
              Enregistrer
            </Button>
          </div>
        )}
      </form>
    </Card>
  )
}

/** Modale d'ajout d'un membre à l'entreprise. */
function AddMemberModal({ company, onClose }) {
  const toast = useToast()
  const queryClient = useQueryClient()
  const [values, setValues] = useState({ email: '', password: '', first_name: '', last_name: '' })
  const create = useMutation({
    mutationFn: () =>
      api.post('/users', {
        ...values,
        first_name: values.first_name || null,
        last_name: values.last_name || null,
        company_id: company.id,
      }),
    onSuccess: () => {
      toast.success('Compte créé : un email de bienvenue a été envoyé.')
      queryClient.invalidateQueries({ queryKey: ['companies', company.id, 'members'] })
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
    <Modal open onClose={onClose} title="Ajouter un collaborateur">
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
          type="text"
          minLength={8}
          required
          hint="8 caractères minimum. Communiquez-le à la personne."
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

/** Liste des membres de l'entreprise et leur gestion. */
function MembersCard({ company, canEdit }) {
  const { user } = useAuth()
  const toast = useToast()
  const queryClient = useQueryClient()
  const [adding, setAdding] = useState(false)
  const members = useQuery({
    queryKey: ['companies', company.id, 'members'],
    queryFn: () => api.get(`/companies/${company.id}/members`),
  })
  const act = useMutation({
    mutationFn: ({ call, success }) => call().then(() => success),
    onSuccess: (message) => {
      toast.success(message)
      queryClient.invalidateQueries({ queryKey: ['companies', company.id, 'members'] })
    },
    onError: () => toast.error('Action impossible.'),
  })

  return (
    <>
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-lg font-semibold">Équipe</h2>
        {canEdit && <Button onClick={() => setAdding(true)}>Ajouter un collaborateur</Button>}
      </div>
      {members.isLoading && <Spinner />}
      {members.data?.length === 0 && <EmptyState title="Aucun membre" />}
      <ul className="divide-y divide-slate-200 rounded-xl border border-slate-200 bg-white dark:divide-slate-800 dark:border-slate-800 dark:bg-slate-900">
        {members.data?.map((member) => (
          <li key={member.id} className="flex flex-wrap items-center gap-3 p-4">
            <Avatar
              src={uploadUrl(member.avatar_path)}
              firstName={member.first_name}
              lastName={member.last_name}
            />
            <div className="min-w-0 flex-1">
              <p className="truncate font-medium">{fullName(member)}</p>
              <p className="truncate text-sm text-slate-500">{member.email}</p>
            </div>
            {member.is_company_admin && <Badge tone="brand">Administrateur</Badge>}
            {!member.is_active && <Badge tone="warning">Désactivé</Badge>}
            {canEdit && member.id !== user.id && (
              <div className="flex gap-2">
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() =>
                    act.mutate({
                      call: () =>
                        api.put(`/users/${member.id}/company-admin`, {
                          is_company_admin: !member.is_company_admin,
                        }),
                      success: 'Droits mis à jour.',
                    })
                  }
                >
                  {member.is_company_admin ? 'Retirer admin' : 'Rendre admin'}
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() =>
                    act.mutate({
                      call: () =>
                        api.post(
                          `/users/${member.id}/${member.is_active ? 'deactivate' : 'reactivate'}`,
                        ),
                      success: member.is_active ? 'Compte désactivé.' : 'Compte réactivé.',
                    })
                  }
                >
                  {member.is_active ? 'Désactiver' : 'Réactiver'}
                </Button>
              </div>
            )}
          </li>
        ))}
      </ul>
      {adding && <AddMemberModal company={company} onClose={() => setAdding(false)} />}
    </>
  )
}

/**
 * « Mon entreprise » : fiche et équipe en lecture seule ; avec `manage` (onglet d'administration
 * de l'entreprise), l'administrateur modifie la fiche et gère l'équipe.
 */
export default function MyCompanyPage({ manage = false }) {
  const { user } = useAuth()
  const company = useQuery({
    queryKey: ['companies', 'me'],
    queryFn: () => api.get('/companies/me'),
    enabled: Boolean(user.company_id),
  })

  if (!user.company_id) {
    return (
      <EmptyState
        title="Vous n'êtes rattaché à aucune entreprise"
        description="Contactez l'équipe de la Maison de l'Entreprise."
      />
    )
  }
  if (company.isLoading) return <Spinner />
  if (company.isError) return <p role="alert">Impossible de charger votre entreprise.</p>

  const canEdit = manage && canManageCompany(user, company.data.id)
  return (
    <>
      <PageHeader
        title={company.data.name}
        description={canEdit ? 'Gérez la fiche et l’équipe de votre entreprise.' : undefined}
      />
      <CompanyForm
        key={company.data.updated_at ?? company.data.id}
        company={company.data}
        canEdit={canEdit}
      />
      <MembersCard company={company.data} canEdit={canEdit} />
    </>
  )
}
