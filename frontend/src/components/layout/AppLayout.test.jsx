import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it } from 'vitest'

import { ThemeProvider } from '../ThemeProvider'
import AppLayout from './AppLayout'

describe('AppLayout', () => {
  it('affiche le menu et ouvre le tiroir mobile', async () => {
    render(
      <ThemeProvider>
        <MemoryRouter initialEntries={['/annuaire']}>
          <Routes>
            <Route element={<AppLayout />}>
              <Route path="/annuaire" element={<p>contenu</p>} />
            </Route>
          </Routes>
        </MemoryRouter>
      </ThemeProvider>,
    )
    expect(screen.getByText('contenu')).toBeInTheDocument()
    expect(screen.getAllByRole('link', { name: 'Messagerie' })).toHaveLength(1)
    await userEvent.click(screen.getByRole('button', { name: 'Ouvrir le menu' }))
    expect(screen.getAllByRole('link', { name: 'Messagerie' })).toHaveLength(2)
    await userEvent.click(screen.getByRole('button', { name: 'Fermer le menu' }))
    expect(screen.getAllByRole('link', { name: 'Messagerie' })).toHaveLength(1)
  })
})
