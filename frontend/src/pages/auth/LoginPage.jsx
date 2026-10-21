/** Page de connexion. */

import { useState } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'

import { useAuth } from '../../auth/AuthProvider'
import { Button, Input } from '../../components/ui'
import AuthShell from './AuthShell'

/** Formulaire de connexion. */
export default function LoginPage() {
  const { login, user } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const destination = location.state?.from?.pathname ?? '/accueil'
  if (user) return <Navigate to={destination} replace />

  async function onSubmit(event) {
    event.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(email, password)
      navigate(destination, { replace: true })
    } catch (err) {
      setError(err.status === 401 ? 'Email ou mot de passe incorrect.' : 'Connexion impossible.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthShell
      title="Connexion"
      subtitle="Votre compte est créé par l'équipe de la Maison de l'Entreprise."
    >
      <form onSubmit={onSubmit} className="space-y-4" noValidate>
        <Input
          label="Email"
          type="email"
          autoComplete="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
        <Input
          label="Mot de passe"
          type="password"
          autoComplete="current-password"
          required
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          error={error}
        />
        <Button type="submit" loading={loading} className="w-full">
          Se connecter
        </Button>
      </form>
      <Link
        to="/mot-de-passe-oublie"
        className="text-brand-700 dark:text-brand-300 block text-center text-sm hover:underline"
      >
        Mot de passe oublié ?
      </Link>
      <p className="text-center text-xs text-slate-500">
        En vous connectant, vous acceptez le traitement de vos données décrit dans notre{' '}
        <Link to="/confidentialite" className="underline">
          politique de confidentialité
        </Link>
        .
      </p>
    </AuthShell>
  )
}
