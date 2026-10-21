import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterEach } from 'vitest'

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
