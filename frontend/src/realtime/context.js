/** Contexte de la connexion temps réel. */

import { createContext } from 'react'

/** Par défaut (hors provider, ex. tests) : aucun événement n'est jamais reçu. */
export const RealtimeContext = createContext({ subscribe: () => () => {} })
