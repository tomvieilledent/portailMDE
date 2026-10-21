/** Page de choix d'un nouveau mot de passe. */

import { useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'

import { Button, Input, useToast } from '../../components/ui'
import { api } from '../../lib/api'
import AuthShell from './AuthShell'

/** Formulaire de nouveau mot de passe à partir du lien reçu. */
export default function ResetPasswordPage() {
  const [params] = useSearchParams()
  const navigate = useNavigate()
  const toast = useToast()
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const token = params.get('token')

  async function onSubmit(event) {
    event.preventDefault()
    if (password.length < 8) return setError('Le mot de passe doit contenir au moins 8 caractères.')
    if (password !== confirm) return setError('Les mots de passe ne correspondent pas.')
    setError('')
    setLoading(true)
    try {
      await api.post('/auth/reset-password', { token, new_password: password }, { auth: false })
      toast.success('Mot de passe modifié. Vous pouvez vous connecter.')
      navigate('/connexion', { replace: true })
    } catch (err) {
      setError(
        err.status === 401
          ? 'Ce lien est invalide ou a expiré. Refaites une demande.'
          : 'Modification impossible.',
      )
    } finally {
      setLoading(false)
    }
  }

  if (!token) {
    return (
      <AuthShell title="Lien invalide">
        <Link to="/mot-de-passe-oublie" className="text-brand-700 text-sm hover:underline">
          Demander un nouveau lien
        </Link>
      </AuthShell>
    )
  }

  return (
    <AuthShell title="Nouveau mot de passe">
      <form onSubmit={onSubmit} className="space-y-4">
        <Input
          label="Nouveau mot de passe"
          type="password"
          autoComplete="new-password"
          required
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        <Input
          label="Confirmation"
          type="password"
          autoComplete="new-password"
          required
          value={confirm}
          onChange={(e) => setConfirm(e.target.value)}
          error={error}
        />
        <Button type="submit" loading={loading} className="w-full">
          Enregistrer
        </Button>
      </form>
    </AuthShell>
  )
}
