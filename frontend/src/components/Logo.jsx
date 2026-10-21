import { cn } from '../lib/cn'

/** Logo de Rodez Agglomération, en version claire ou sombre selon le thème. */
export default function Logo({ className }) {
  return (
    <>
      <img
        src="/logo-rodez.png"
        alt="Rodez Agglomération"
        className={cn('h-10 w-auto dark:hidden', className)}
      />
      <img
        src="/logo-mode-sombre.png"
        alt="Rodez Agglomération"
        className={cn('hidden h-10 w-auto dark:block', className)}
      />
    </>
  )
}
