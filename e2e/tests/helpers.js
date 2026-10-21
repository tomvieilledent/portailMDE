export const PASSWORD = 'demo-password-1'

/** Se connecte via l'interface et attend l'arrivée sur l'annuaire. */
export async function login(page, email) {
  await page.goto('/connexion')
  await page.getByLabel('Email').fill(email)
  await page.getByLabel('Mot de passe').fill(PASSWORD)
  await page.getByRole('button', { name: 'Se connecter' }).click()
  await page.waitForURL('**/annuaire')
}
