/** Tests E2E des formations : inscription à une session et droits de gestion du staff. */

import { expect, test } from '@playwright/test'

import { login } from './helpers'

/** Un membre s'inscrit puis se désinscrit d'une session. */
test('un membre s’inscrit puis se désinscrit d’une session', async ({ page }) => {
  await login(page, 'karim@demo.fr')
  await page.getByRole('link', { name: 'Formations' }).first().click()
  await page.getByText('Réussir son pitch').click()
  await expect(page.getByRole('heading', { name: 'Réussir son pitch' })).toBeVisible()
  await expect(page.getByText('Salle des Cèdres')).toBeVisible()

  await page.getByRole('button', { name: "S'inscrire" }).click()
  await expect(page.getByRole('button', { name: 'Se désinscrire' })).toBeVisible()
  await expect(page.getByText('1/12')).toBeVisible()

  await page.getByRole('button', { name: 'Se désinscrire' }).click()
  await expect(page.getByRole('button', { name: "S'inscrire" })).toBeVisible()
})

/** Le staff voit les boutons de gestion des formations. */
test('le staff voit les boutons de gestion', async ({ page }) => {
  await login(page, 'staff@demo.fr')
  await page.goto('/formations')
  await expect(page.getByRole('button', { name: /Nouvelle formation/ })).toBeVisible()
})
