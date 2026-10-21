/** Logo Rodez Agglomération, en version claire ou sombre selon le thème. */

import { cn } from '../lib/cn'

/** Logo de l'application ; `className` fixe la hauteur. */
export default function Logo({ className = 'h-10', onDark = false }) {
  if (onDark) {
    return (
      <img
        src="/logo-rodez-sombre.png"
        alt="Rodez Agglomération"
        className={cn(className, 'w-auto')}
      />
    )
  }
  return (
    <>
      <img
        src="/logo-rodez.png"
        alt="Rodez Agglomération"
        className={cn(className, 'w-auto dark:hidden')}
      />
      <img
        src="/logo-rodez-sombre.png"
        alt="Rodez Agglomération"
        className={cn(className, 'hidden w-auto dark:block')}
      />
    </>
  )
}
