/** Tests des composants d'interface réutilisables. */

import { act, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useState } from 'react'
import { describe, expect, it, vi } from 'vitest'

import {
  Avatar,
  Button,
  Input,
  Modal,
  Pagination,
  ToastProvider,
  uploadUrl,
  useToast,
} from './index'

/** Bouton : clic et état de chargement. */
describe('Button', () => {
  it('désactive pendant le chargement', () => {
    render(<Button loading>Envoyer</Button>)
    expect(screen.getByRole('button')).toBeDisabled()
    expect(screen.getByRole('status')).toBeInTheDocument()
  })
})

/** Champ de saisie : libellé et erreur. */
describe('Input', () => {
  it("relie le libellé et l'erreur au champ", () => {
    render(<Input label="Email" error="Email invalide" />)
    const input = screen.getByLabelText('Email')
    expect(input).toHaveAttribute('aria-invalid', 'true')
    expect(input).toHaveAccessibleDescription('Email invalide')
  })
})

/** Modale : ouverture, fermeture et focus. */
describe('Modal', () => {
  function Demo({ onClose }) {
    const [open, setOpen] = useState(true)
    return (
      <Modal
        open={open}
        title="Confirmer"
        onClose={() => {
          setOpen(false)
          onClose()
        }}
      >
        Contenu
      </Modal>
    )
  }

  it('se ferme avec Échap', async () => {
    const onClose = vi.fn()
    render(<Demo onClose={onClose} />)
    expect(screen.getByRole('dialog', { name: 'Confirmer' })).toBeInTheDocument()
    await userEvent.keyboard('{Escape}')
    expect(onClose).toHaveBeenCalled()
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('ne rend rien quand fermée', () => {
    render(<Modal open={false} title="x" onClose={() => {}} />)
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })
})

/** Notifications éphémères. */
describe('Toast', () => {
  it('affiche puis retire le message', () => {
    vi.useFakeTimers()
    function Trigger() {
      const toast = useToast()
      return <button onClick={() => toast.success('Enregistré')}>go</button>
    }
    render(
      <ToastProvider duration={1000}>
        <Trigger />
      </ToastProvider>,
    )
    act(() => screen.getByText('go').click())
    expect(screen.getByText('Enregistré')).toBeInTheDocument()
    act(() => vi.advanceTimersByTime(1100))
    expect(screen.queryByText('Enregistré')).not.toBeInTheDocument()
    vi.useRealTimers()
  })
})

/** Avatar : photo et initiales. */
describe('Avatar', () => {
  it('affiche les initiales sans photo', () => {
    render(<Avatar firstName="Ada" lastName="Lovelace" />)
    expect(screen.getByText('AL')).toBeInTheDocument()
  })

  it("construit l'URL d'un fichier", () => {
    expect(uploadUrl('avatars/a.png')).toBe('/uploads/avatars/a.png')
    expect(uploadUrl(null)).toBeNull()
  })
})

/** Pagination : navigation entre pages. */
describe('Pagination', () => {
  it('navigue entre les pages', async () => {
    const onChange = vi.fn()
    render(<Pagination total={120} limit={50} offset={50} onChange={onChange} />)
    expect(screen.getByText('Page 2 sur 3')).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: /suivant/i }))
    expect(onChange).toHaveBeenCalledWith(100)
    await userEvent.click(screen.getByRole('button', { name: /précédent/i }))
    expect(onChange).toHaveBeenCalledWith(0)
  })

  it("n'apparaît pas pour une seule page", () => {
    const { container } = render(
      <Pagination total={10} limit={50} offset={0} onChange={() => {}} />,
    )
    expect(container).toBeEmptyDOMElement()
  })
})
