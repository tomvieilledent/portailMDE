/** Configuration commune des tests : matchers, nettoyage et simulation de `matchMedia`. */

import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterEach } from 'vitest'

/** Nettoie l'affichage et le stockage local après chaque test. */
afterEach(() => {
  cleanup()
  localStorage.clear()
})

// jsdom n'implémente pas matchMedia.
window.matchMedia ??= (query) => ({
  matches: false,
  media: query,
  addEventListener() {},
  removeEventListener() {},
})
