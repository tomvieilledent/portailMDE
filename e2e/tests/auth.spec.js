/** Tests E2E de l'authentification : accueil public, redirections, connexion et droits d'accès. */

import { expect, test } from '@playwright/test'

import { PASSWORD, login } from './helpers'

test.describe('authentification', () => {
  /** La page d'accueil publique mène à la page de connexion. */
  test("la page d'accueil publique propose la connexion", async ({ page }) => {
    await page.goto('/')
    await expect(page.getByRole('heading', { name: "De l'idée à la création" })).toBeVisible()
    await page.getByRole('link', { name: 'Se connecter' }).click()
    await expect(page).toHaveURL(/\/connexion$/)
  })

  /** Un visiteur non connecté est redirigé vers la connexion. */
  test('un visiteur est redirigé vers la connexion', async ({ page }) => {
    await page.goto('/agenda')
    await expect(page).toHaveURL(/\/connexion$/)
  })

  /** Un mauvais mot de passe affiche un message d'erreur. */
  test('mauvais mot de passe', async ({ page }) => {
    await page.goto('/connexion')
    await page.getByLabel('Email').fill('lea@demo.fr')
    await page.getByLabel('Mot de passe').fill(`${PASSWORD}-faux`)
    await page.getByRole('button', { name: 'Se connecter' }).click()
    await expect(page.getByRole('alert')).toHaveText('Email ou mot de passe incorrect.')
  })

  /** Connexion puis déconnexion, avec retour à la page de connexion. */
  test('connexion puis déconnexion', async ({ page }) => {
    await login(page, 'lea@demo.fr')
    await expect(page.getByRole('heading', { name: 'Annuaire' })).toBeVisible()
    await page.getByRole('button', { name: 'Se déconnecter' }).click()
    await expect(page).toHaveURL(/\/connexion$/)
    await page.goto('/annuaire')
    await expect(page).toHaveURL(/\/connexion$/)
  })

  /** L'administration est inaccessible aux membres hors staff. */
  test("l'administration est réservée au staff", async ({ page }) => {
    await login(page, 'lea@demo.fr')
    await expect(page.getByRole('link', { name: 'Administration' })).toHaveCount(0)
    await page.goto('/administration')
    await expect(page).toHaveURL(/\/annuaire$/)
  })
})
