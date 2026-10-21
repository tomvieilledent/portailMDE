/** Tests des utilitaires de calendrier. */

import { describe, expect, it } from 'vitest'

import { buildMonthGrid, shortTime, toISODate } from './calendar'

/** Grille mensuelle et formats de date. */
describe('calendrier', () => {
  it('commence la grille un lundi et couvre tout le mois', () => {
    const weeks = buildMonthGrid(2026, 9) // octobre 2026 : le 1er est un jeudi
    expect(weeks[0][0].iso).toBe('2026-09-28')
    expect(weeks[0][3]).toMatchObject({ iso: '2026-10-01', inMonth: true })
    const days = weeks.flat().filter((d) => d.inMonth)
    expect(days).toHaveLength(31)
    expect(weeks.every((w) => w.length === 7)).toBe(true)
  })

  it('retire la dernière semaine si elle est hors du mois', () => {
    expect(buildMonthGrid(2027, 1)).toHaveLength(4) // février 2027 : du lundi 1er au dimanche 28
    expect(buildMonthGrid(2026, 1)).toHaveLength(5) // février 2026 : commence un dimanche
  })

  it("n'est pas décalé par le fuseau horaire", () => {
    expect(toISODate(new Date(2026, 0, 1))).toBe('2026-01-01')
  })

  it('raccourcit les heures', () => {
    expect(shortTime('18:30:00')).toBe('18:30')
    expect(shortTime(null)).toBeNull()
  })
})
