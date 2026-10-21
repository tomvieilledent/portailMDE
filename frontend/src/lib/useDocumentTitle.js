/** Titre d'onglet et focus du <h1> pour les pages hors AppLayout (WCAG 2.4.2). */

import { useEffect } from 'react'

let firstPage = true

/** Fixe le titre du document ; au changement de page (pas au premier chargement), place le focus sur le <h1>. */
export function useDocumentTitle(title) {
  useEffect(() => {
    document.title = title
    if (firstPage) {
      firstPage = false
      return
    }
    const heading = document.querySelector('h1')
    if (heading) {
      heading.tabIndex = -1
      heading.focus()
    }
  }, [title])
}
