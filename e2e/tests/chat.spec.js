/** Tests E2E de la messagerie : discussion en temps réel entre deux utilisateurs. */

import { expect, test } from '@playwright/test'

import { login } from './helpers'

/** Zone de discussion de la page. */
const thread = (page) => page.getByRole('region', { name: 'Discussion' })

/** Deux utilisateurs échangent des messages reçus en direct, sans rechargement. */
test('deux utilisateurs discutent en temps réel', async ({ browser }) => {
  const leaCtx = await browser.newContext()
  const hugoCtx = await browser.newContext()
  const lea = await leaCtx.newPage()
  const hugo = await hugoCtx.newPage()
  await login(lea, 'lea@demo.fr')
  await login(hugo, 'hugo@demo.fr')

  // Léa ouvre une conversation directe depuis la fiche de Hugo
  await lea.getByLabel('Rechercher').fill('Hugo')
  await lea.getByText('Hugo Bernard').click()
  await lea.getByRole('button', { name: /Envoyer un message/ }).click()
  await expect(lea).toHaveURL(/\/messagerie\/.+/)

  // Hugo ouvre la messagerie : la conversation apparaît puis les messages arrivent en direct
  await hugo.getByRole('link', { name: 'Messagerie' }).first().click()
  const message = `Bonjour Hugo ${Date.now()}`
  await lea.getByLabel('Votre message').fill(message)
  await lea.getByLabel('Votre message').press('Enter')
  await expect(thread(lea).getByText(message)).toBeVisible()

  await hugo.getByRole('link', { name: /Léa Martin/ }).click()
  await expect(thread(hugo).getByText(message)).toBeVisible()

  // Réponse de Hugo reçue sans rechargement par Léa
  const reply = `Salut Léa ${Date.now()}`
  await hugo.getByLabel('Votre message').fill(reply)
  await hugo.getByLabel('Votre message').press('Enter')
  await expect(thread(lea).getByText(reply)).toBeVisible()

  await leaCtx.close()
  await hugoCtx.close()
})
