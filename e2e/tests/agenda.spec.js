/** Tests E2E de l'agenda : création, visibilité et suppression d'un événement public. */

import { expect, test } from '@playwright/test'

import { login } from './helpers'

/** Un événement public créé par un membre est visible d'un autre, et supprimable par son créateur. */
test('crée un événement public visible par un autre membre', async ({ browser }) => {
  const title = `Petit-déjeuner ${Date.now()}`
  const leaCtx = await browser.newContext()
  const lea = await leaCtx.newPage()
  await login(lea, 'lea@demo.fr')
  await lea.getByRole('link', { name: 'Agenda' }).first().click()
  await lea.getByRole('button', { name: /Événement/ }).click()
  const dialog = lea.getByRole('dialog', { name: 'Nouvel événement' })
  await dialog.getByLabel('Titre').fill(title)
  await dialog.getByLabel(/Visible par tous/).check()
  await dialog.getByRole('button', { name: 'Enregistrer' }).click()
  await expect(lea.getByRole('button', { name: new RegExp(title) })).toBeVisible()

  const sofiaCtx = await browser.newContext()
  const sofia = await sofiaCtx.newPage()
  await login(sofia, 'sofia@demo.fr')
  await sofia.getByRole('link', { name: 'Agenda' }).first().click()
  await expect(sofia.getByRole('button', { name: new RegExp(title) })).toBeVisible()

  // Le créateur peut supprimer son événement
  await lea.getByRole('button', { name: new RegExp(title) }).click()
  await lea.getByRole('button', { name: 'Supprimer' }).click()
  await expect(lea.getByRole('button', { name: new RegExp(title) })).toHaveCount(0)

  await leaCtx.close()
  await sofiaCtx.close()
})
