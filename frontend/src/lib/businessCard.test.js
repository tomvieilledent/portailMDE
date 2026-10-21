/** Tests de la génération de carte de visite (vCard). */

import { describe, expect, it } from 'vitest'

import { buildVCard, cardLines } from './businessCard'

const person = {
  first_name: 'Ada',
  last_name: 'Lovelace',
  job_title: 'Directrice, R&D',
  email: 'ada@x.fr',
  phone: '06 00 00 00 00',
  company: { name: 'Acme; Co' },
}

/** Contenu de la vCard et lignes de la carte. */
describe('carte de visite', () => {
  it('construit une vCard avec échappement des séparateurs', () => {
    const vcard = buildVCard(person)
    expect(vcard).toContain('BEGIN:VCARD')
    expect(vcard).toContain('FN:Ada Lovelace')
    expect(vcard).toContain('ORG:Acme\\; Co')
    expect(vcard).toContain('TITLE:Directrice\\, R&D')
    expect(vcard).toContain('EMAIL;TYPE=INTERNET:ada@x.fr')
    expect(vcard.endsWith('END:VCARD\r\n')).toBe(true)
  })

  it("se rabat sur l'email quand le nom est vide", () => {
    expect(cardLines({ email: 'a@x.fr' }).name).toBe('a@x.fr')
  })
})
