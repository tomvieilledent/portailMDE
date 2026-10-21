/** Libellés et utilitaires d'affichage de l'annuaire. */

/** Libellés des types d'entreprise. */
export const COMPANY_KINDS = {
  company: 'Entreprise',
  trainer: 'Formateur',
  partner: 'Partenaire',
}

/** Nom complet d'une personne. */
export const fullName = (person) =>
  [person.first_name, person.last_name].filter(Boolean).join(' ') || person.email
