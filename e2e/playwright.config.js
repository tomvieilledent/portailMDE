import { defineConfig, devices } from '@playwright/test'

// Les tests visent une pile complète déjà démarrée (docker compose up) et alimentée
// par `python -m app.cli seed-demo` (comptes *@demo.fr, mot de passe demo-password-1).
export default defineConfig({
  testDir: './tests',
  fullyParallel: false,
  workers: 1,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [['github'], ['html', { open: 'never' }]] : 'list',
  use: {
    baseURL: process.env.E2E_BASE_URL ?? 'http://localhost:5290',
    locale: 'fr-FR',
    trace: 'retain-on-failure',
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
})
