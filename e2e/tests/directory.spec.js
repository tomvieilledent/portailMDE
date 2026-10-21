import { expect, test } from '@playwright/test'

import { login } from './helpers'

test.describe('annuaire', () => {
  test.beforeEach(async ({ page }) => {
    await login(page, 'lea@demo.fr')
  })

  test('recherche une personne et ouvre sa fiche', async ({ page }) => {
    await page.getByLabel('Rechercher').fill('Karim')
    await expect(page.getByText('Karim Roux')).toBeVisible()
    await expect(page.getByText('Hugo Bernard')).toHaveCount(0)
    await page.getByText('Karim Roux').click()
    const dialog = page.getByRole('dialog', { name: 'Karim Roux' })
    await expect(dialog).toContainText('karim@demo.fr')
    await expect(dialog.getByRole('link', { name: 'AgriTech Aveyron' })).toBeVisible()
  })

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
