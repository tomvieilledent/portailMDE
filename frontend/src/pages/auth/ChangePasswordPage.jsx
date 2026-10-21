/** Page de changement obligatoire du mot de passe temporaire. */

import { useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'

import { useAuth } from '../../auth/AuthProvider'
import { Button, Input, useToast } from '../../components/ui'
import { api } from '../../lib/api'
import { tokens } from '../../lib/tokens'
import AuthShell from './AuthShell'

/** Formulaire demandant à l'utilisateur de remplacer son mot de passe temporaire. */
export default function ChangePasswordPage() {
  const { user, setUser, logout } = useAuth()
  const navigate = useNavigate()
  const toast = useToast()
  const [current, setCurrent] = useState('')
  const [next, setNext] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  if (!user?.must_change_password) return <Navigate to="/accueil" replace />

  async function onSubmit(event) {
    event.preventDefault()
    if (next.length < 8)
      return setError('Le nouveau mot de passe doit contenir au moins 8 caractères.')
    if (next !== confirm) return setError('Les mots de passe ne correspondent pas.')
    setError('')
    setLoading(true)
    try {
      // Les anciens jetons sont révoqués : l'API renvoie une nouvelle paire.
      const pair = await api.post('/users/me/password', {
        current_password: current,
        new_password: next,
      })
      if (pair?.access_token) tokens.set(pair)
      setUser({ ...user, must_change_password: false })
      toast.success('Mot de passe modifié.')
      navigate('/accueil', { replace: true })
    } catch (err) {
      setError(
        err.status === 400 ? 'Mot de passe temporaire incorrect.' : 'Modification impossible.',
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthShell
      title="Choisissez votre mot de passe"
      subtitle="Votre mot de passe est temporaire : remplacez-le pour accéder au portail."
    >
      <form onSubmit={onSubmit} className="space-y-4">
        <Input
          label="Mot de passe temporaire"
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
          hint="8 caractères minimum."
          required
        />
        <Input
          label="Confirmation"
          type="password"
          autoComplete="new-password"
          value={confirm}
          onChange={(e) => setConfirm(e.target.value)}
          required
        />
        {error && (
          <p role="alert" className="text-sm text-red-600">
            {error}
          </p>
        )}
        <Button type="submit" loading={loading} className="w-full">
          Enregistrer
        </Button>
        <Button variant="ghost" className="w-full" onClick={logout}>
          Se déconnecter
        </Button>
      </form>
    </AuthShell>
  )
}
