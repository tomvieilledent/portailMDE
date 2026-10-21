import { useEffect, useState } from 'react'

/** Valeur retardée : utile pour ne lancer la recherche qu'une fois la saisie terminée. */
export function useDebounce(value, delay = 300) {
  const [debounced, setDebounced] = useState(value)
  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay)
    return () => clearTimeout(timer)
  }, [value, delay])
  return debounced
}
