/** Tests E2E de l'annuaire : personnes, entreprises et page « Mon entreprise ». */

import { expect, test } from '@playwright/test'

import { login } from './helpers'

/** Scénarios de l'annuaire, joués après connexion de Léa. */
test.describe('annuaire', () => {
  /** Connecte Léa avant chaque test. */
  test.beforeEach(async ({ page }) => {
    await login(page, 'lea@demo.fr')
  })

  /** Recherche une personne et ouvre sa fiche. */
  test('recherche une personne et ouvre sa fiche', async ({ page }) => {
    await page.getByLabel('Rechercher').fill('Karim')
    await expect(page.getByText('Karim Roux')).toBeVisible()
    await expect(page.getByText('Hugo Bernard')).toHaveCount(0)
    await page.getByRole('button', { name: 'Voir la fiche de Karim Roux' }).click()
    const dialog = page.getByRole('dialog', { name: 'Karim Roux' })
    await expect(dialog).toContainText('karim@demo.fr')
    await expect(dialog.getByRole('link', { name: 'AgriTech Aveyron' })).toBeVisible()
  })

  /** Filtre l'annuaire des entreprises et ouvre une fiche avec son équipe. */
  test('annuaire des entreprises et fiche avec équipe', async ({ page }) => {
    await page.getByRole('link', { name: 'Entreprises' }).first().click()
    await page.getByLabel('Type').selectOption('trainer')
    await expect(page.getByText('Formations Sud')).toBeVisible()
    await expect(page.getByText('Atelier Lumière')).toHaveCount(0)
    await page.getByLabel('Type').selectOption('')
    await page.getByText('Atelier Lumière').click()
    await expect(page.getByRole('heading', { name: 'Atelier Lumière' })).toBeVisible()
    await expect(page.getByRole('main').getByText('Léa Martin')).toBeVisible()
    await expect(page.getByText('Hugo Bernard')).toBeVisible()
  })

  /** La directrice peut modifier son entreprise, pas son collègue. */
  test('Mon entreprise : la directrice peut modifier, pas son collègue', async ({ page, browser }) => {
    await page.getByRole('link', { name: 'Mon entreprise' }).first().click()
    await expect(page.getByLabel('Nom')).toBeEnabled()
    await expect(page.getByRole('button', { name: 'Ajouter un collaborateur' })).toBeVisible()

    const context = await browser.newContext()
    const colleague = await context.newPage()
    await login(colleague, 'hugo@demo.fr')
    await colleague.getByRole('link', { name: 'Mon entreprise' }).first().click()
    await expect(colleague.getByLabel('Nom')).toBeDisabled()
    await context.close()
  })
})
