import { Link } from 'react-router-dom'

export default function NotFoundPage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-4 p-6">
      <h1 className="text-3xl font-bold">Page introuvable</h1>
      <Link to="/" className="text-brand-600 hover:underline dark:text-brand-300">
        Retour à l'accueil
      </Link>
    </main>
  )
}
