import { expect, test } from '@playwright/test'

import { login } from './helpers'

test("le super admin crée un compte puis l'utilise", async ({ browser, page }) => {
  const email = `nouveau.${Date.now()}@demo.fr`
  await login(page, 'admin@demo.fr')
  await page.getByRole('link', { name: 'Administration' }).first().click()
  await page.getByRole('button', { name: /Nouveau compte/ }).click()
  const dialog = page.getByRole('dialog', { name: 'Nouveau compte' })
  await dialog.getByLabel('Prénom').fill('Nina')
  await dialog.getByLabel('Email').fill(email)
  await dialog.getByLabel('Mot de passe temporaire').fill('temporaire-123')
  await dialog.getByRole('button', { name: 'Créer le compte' }).click()
  await expect(page.getByText(email)).toBeVisible()

  const context = await browser.newContext()
  const nina = await context.newPage()
  await nina.goto('/connexion')
  await nina.getByLabel('Email').fill(email)
  await nina.getByLabel('Mot de passe').fill('temporaire-123')
  await nina.getByRole('button', { name: 'Se connecter' }).click()
  await expect(nina).toHaveURL(/\/annuaire$/)
  await context.close()

  // désactivation : la connexion est ensuite refusée
  await page.getByRole('row', { name: new RegExp(email) }).getByRole('button', { name: 'Désactiver' }).click()
  await expect(page.getByRole('row', { name: new RegExp(email) })).toContainText('Désactivé')
})
