import { useState } from 'react'
import { Link } from 'react-router-dom'

import { Button, Input } from '../../components/ui'
import { api } from '../../lib/api'
import AuthShell from './AuthShell'

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('')
  const [sent, setSent] = useState(false)
  const [loading, setLoading] = useState(false)

  async function onSubmit(event) {
    event.preventDefault()
    setLoading(true)
    try {
      await api.post('/auth/forgot-password', { email }, { auth: false })
    } catch {
      /* on ne révèle jamais si le compte existe : message identique en cas d'erreur */
    } finally {
      // Même message que le compte existe ou non (pas de fuite d'information).
      setSent(true)
      setLoading(false)
    }
  }

  return (
    <AuthShell title="Mot de passe oublié">
      {sent ? (
        <p role="status" className="text-sm">
          Si un compte correspond à cette adresse, un lien de réinitialisation vient d'être envoyé.
        </p>
      ) : (
        <form onSubmit={onSubmit} className="space-y-4">
          <Input
            label="Email"
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          <Button type="submit" loading={loading} className="w-full">
            Envoyer le lien
          </Button>
        </form>
      )}
      <Link
        to="/connexion"
        className="block text-center text-sm text-brand-700 hover:underline dark:text-brand-300"
      >
        Retour à la connexion
      </Link>
    </AuthShell>
  )
}
