/** Pages légales : mentions légales et politique de confidentialité. */

import { Link } from 'react-router-dom'

import { useDocumentTitle } from '../lib/useDocumentTitle'

/** Cadre commun des pages légales. */
function LegalShell({ title, children }) {
  useDocumentTitle(title)
  return (
    <main id="contenu" className="mx-auto max-w-3xl space-y-4 p-6">
      <Link to="/" className="text-brand-700 dark:text-brand-300 text-sm hover:underline">
        Retour à l'accueil
      </Link>
      <h1 className="text-2xl font-bold">{title}</h1>
      <div className="space-y-4 text-sm text-slate-700 dark:text-slate-300">{children}</div>
    </main>
  )
}

/** Mentions légales. */
export function LegalNoticePage() {
  return (
    <LegalShell title="Mentions légales">
      <p>
        Le site est édité par la Maison de l'Entreprise. Les coordonnées de l'éditeur, du directeur
        de la publication et de l'hébergeur sont à compléter par l'exploitant avant la mise en
        production.
      </p>
      <p>
        Les contenus du portail sont réservés à ses membres. Toute reproduction sans autorisation
        est interdite.
      </p>
    </LegalShell>
  )
}

/** Politique de confidentialité. */
export function PrivacyPage() {
  return (
    <LegalShell title="Politique de confidentialité">
      <section>
        <h2 className="font-semibold">Données collectées</h2>
        <p>
          Email, nom, prénom, fonction, téléphone, photo de profil, carte de visite, messages et
          notifications, uniquement pour faire fonctionner le portail et l'annuaire des membres.
        </p>
      </section>
      <section>
        <h2 className="font-semibold">Durées de conservation</h2>
        <p>
          Les données de profil sont conservées tant que le compte existe. À la suppression du
          compte, elles sont anonymisées et les fichiers associés effacés. Les notifications sont
          supprimées après 90 jours et les messages supprimés après 30 jours.
        </p>
      </section>
      <section>
        <h2 className="font-semibold">Vos droits</h2>
        <p>
          Depuis la page « Mon profil », vous pouvez exporter vos données (accès, portabilité), les
          rectifier et supprimer votre compte (effacement). Pour toute autre demande, contactez
          l'administrateur du portail.
        </p>
      </section>
    </LegalShell>
  )
}
