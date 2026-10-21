export const COMPANY_KINDS = {
  company: 'Entreprise',
  trainer: 'Formateur',
  partner: 'Partenaire',
}

export const fullName = (person) =>
  [person.first_name, person.last_name].filter(Boolean).join(' ') || person.email
