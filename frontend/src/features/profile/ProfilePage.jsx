import { useMutation } from '@tanstack/react-query'
import { useState } from 'react'

import { useAuth } from '../../auth/AuthProvider'
import PageHeader from '../../components/layout/PageHeader'
import { Avatar, Button, Card, ImageUpload, Input, uploadUrl, useToast } from '../../components/ui'
import { api } from '../../lib/api'

const toFormData = (file) => {
  const form = new FormData()
  form.append('file', file)
  return form
}

function InfoForm() {
  const { user, setUser } = useAuth()
  const toast = useToast()
  const [values, setValues] = useState({
    first_name: user.first_name ?? '',
    last_name: user.last_name ?? '',
    job_title: user.job_title ?? '',
    phone: user.phone ?? '',
  })
  const save = useMutation({
    mutationFn: () =>
      api.patch(
        '/users/me',
        Object.fromEntries(Object.entries(values).map(([k, v]) => [k, v.trim() || null])),
      ),
    onSuccess: (me) => {
      setUser(me)
      toast.success('Profil mis à jour.')
    },
    onError: () => toast.error('Mise à jour impossible.'),
  })
  const bind = (name) => ({
    value: values[name],
    onChange: (e) => setValues((v) => ({ ...v, [name]: e.target.value })),
  })

  return (
    <Card>
      <h2 className="mb-4 text-lg font-semibold">Informations</h2>
      <form
        onSubmit={(e) => {
          e.preventDefault()
          save.mutate()
        }}
        className="grid gap-4 sm:grid-cols-2"
      >
        <Input label="Prénom" autoComplete="given-name" {...bind('first_name')} />
        <Input label="Nom" autoComplete="family-name" {...bind('last_name')} />
        <Input label="Fonction" autoComplete="organization-title" {...bind('job_title')} />
        <Input label="Téléphone" type="tel" autoComplete="tel" {...bind('phone')} />
        <Input label="Email" value={user.email} disabled hint="L'email ne peut pas être modifié." />
        <div className="flex items-end sm:col-span-2">
          <Button type="submit" loading={save.isPending}>
            Enregistrer
          </Button>
        </div>
      </form>
    </Card>
  )
}

/** Envoi d'une image du profil ; la réponse (utilisateur à jour) remplace la session. */
function useImageUpload(path, success) {
  const { setUser } = useAuth()
  const toast = useToast()
  return useMutation({
    mutationFn: (file) => api.put(path, toFormData(file)),
    onSuccess: (me) => {
      setUser(me)
      toast.success(success)
    },
  })
}

function ImagesCard() {
  const { user } = useAuth()
  const avatar = useImageUpload('/users/me/avatar', 'Photo mise à jour.')
  const card = useImageUpload('/users/me/business-card', 'Carte de visite mise à jour.')

  return (
    <Card className="space-y-6">
      <h2 className="text-lg font-semibold">Photo et carte de visite</h2>
      <ImageUpload
        label="Photo de profil"
        loading={avatar.isPending}
        error={avatar.error?.message}
        onSelect={avatar.mutate}
        preview={
          <Avatar
            src={uploadUrl(user.avatar_path)}
            firstName={user.first_name}
            lastName={user.last_name}
            size="lg"
          />
        }
      />
      <ImageUpload
        label="Carte de visite"
        loading={card.isPending}
        error={card.error?.message}
        onSelect={card.mutate}
        preview={
          user.business_card_path ? (
            <img
              src={uploadUrl(user.business_card_path)}
              alt="Votre carte de visite"
              className="h-16 rounded border border-slate-200 dark:border-slate-700"
            />
          ) : null
        }
      />
    </Card>
  )
}

function PasswordForm() {
  const toast = useToast()
  const [current, setCurrent] = useState('')
  const [next, setNext] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState('')
  const change = useMutation({
    mutationFn: () =>
      api.post('/users/me/password', { current_password: current, new_password: next }),
    onSuccess: () => {
      toast.success('Mot de passe modifié.')
      setCurrent('')
      setNext('')
      setConfirm('')
    },
    onError: (err) =>
      setError(err.status === 400 ? 'Mot de passe actuel incorrect.' : 'Modification impossible.'),
  })

  function onSubmit(event) {
    event.preventDefault()
    if (next.length < 8)
      return setError('Le nouveau mot de passe doit contenir au moins 8 caractères.')
    if (next !== confirm) return setError('Les mots de passe ne correspondent pas.')
    setError('')
    change.mutate()
  }

  return (
    <Card>
      <h2 className="mb-4 text-lg font-semibold">Mot de passe</h2>
      <form onSubmit={onSubmit} className="grid max-w-md gap-4">
        <Input
          label="Mot de passe actuel"
          type="password"
          autoComplete="current-password"
          value={current}
          onChange={(e) => setCurrent(e.target.value)}
          required
        />
        <Input
          label="Nouveau mot de passe"
          type="password"
          autoComplete="new-password"
          value={next}
          onChange={(e) => setNext(e.target.value)}
          required
        />
        <Input
          label="Confirmation"
          type="password"
          autoComplete="new-password"
          value={confirm}
          onChange={(e) => setConfirm(e.target.value)}
          error={error}
          required
        />
        <div>
          <Button type="submit" loading={change.isPending}>
            Changer le mot de passe
          </Button>
        </div>
      </form>
    </Card>
  )
}

export default function ProfilePage() {
  return (
    <>
      <PageHeader
        title="Mon profil"
        description="Ces informations sont visibles dans l'annuaire."
      />
      <div className="space-y-6">
        <InfoForm />
        <ImagesCard />
        <PasswordForm />
      </div>
    </>
  )
}
