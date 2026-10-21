/** Liens vers les pages légales (mentions légales, confidentialité). */

import { Link } from 'react-router-dom'

/** Liens de pied de page vers les informations légales. */
export default function LegalLinks({ className = '' }) {
  return (
    <nav aria-label="Informations légales" className={`flex justify-center gap-4 ${className}`}>
      <Link to="/mentions-legales" className="hover:underline">
        Mentions légales
      </Link>
      <Link to="/confidentialite" className="hover:underline">
        Politique de confidentialité
      </Link>
    </nav>
  )
}
