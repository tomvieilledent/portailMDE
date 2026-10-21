import { useContext, useEffect, useRef } from 'react'

import { RealtimeContext } from './context'

/** Appelle `handler(event)` à chaque événement temps réel du type donné. */
export function useRealtime(type, handler) {
  const { subscribe } = useContext(RealtimeContext)
  const saved = useRef(handler)
  useEffect(() => {
    saved.current = handler
  })
  useEffect(() => subscribe(type, (event) => saved.current(event)), [subscribe, type])
}
