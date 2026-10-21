/** Page de garde : tout l'essentiel tient sur un écran (ordinateur), sans défilement. */

import { Link } from 'react-router-dom'

import LegalLinks from '../components/LegalLinks'
import Logo from '../components/Logo'
import { useLanding } from '../features/landing/useLanding'
import { useDocumentTitle } from '../lib/useDocumentTitle'

/** Numéro de contact affiché sur la page de garde (factice, à remplacer). */
const CONTACT_PHONE = '00 00 00 00 00'

/**
 * Page de garde. Sur ordinateur : deux colonnes (message et accès à gauche, dispositifs à droite)
 * qui remplissent exactement la hauteur de la fenêtre ; sur petit écran, la page défile.
 */
export default function HomePage() {
  const { content } = useLanding()
  useDocumentTitle('Accueil')

  return (
    <div
      className="relative flex min-h-dvh flex-col bg-[#1a3a2a] bg-cover bg-center text-white lg:h-dvh lg:overflow-hidden"
      style={{ backgroundImage: 'url(/1920.webp)' }}
    >
      <div className="absolute inset-0 bg-gradient-to-r from-black/65 via-black/50 to-black/75" />

      <header className="relative z-10 mx-auto flex w-full max-w-7xl shrink-0 items-center justify-between px-6 py-4">
        <div className="flex items-center gap-4">
          <Logo className="h-11" onDark />
          <span className="hidden h-8 w-px bg-white/25 sm:block" />
          <p className="hidden text-sm leading-snug font-medium text-white/80 sm:block">
            Maison de l'Économie
            <br />
            Rodez Agglomération
          </p>
        </div>
        <Link
          to="/connexion"
          className="bg-[#7ec843] px-6 py-2.5 text-sm font-bold text-white transition hover:bg-[#5da020]"
        >
          Se connecter
        </Link>
      </header>

      <main className="relative z-10 mx-auto flex min-h-0 w-full max-w-7xl flex-1 flex-col justify-center px-6 py-4">
        <div>
          <p className="mb-4 text-sm font-semibold text-[#7ec843]">
            Maison de l'Économie · Rodez Agglomération
          </p>
          <h1 className="font-display text-5xl leading-[1.02] font-bold tracking-tight xl:text-6xl">
            {content.slogan}
          </h1>
          <span className="mt-5 block h-1 w-20 bg-[#7ec843]" aria-hidden="true" />
          {/* Sous-titre et contact dans un même bloc translucide */}
          <div className="mt-5 max-w-xl border border-white/20 bg-black/35 backdrop-blur-md">
            {content.subtitle && (
              <p className="px-5 py-4 text-lg leading-relaxed font-semibold text-white">
                {content.subtitle}
              </p>
            )}
            <a
              href={`tel:${CONTACT_PHONE.replaceAll(' ', '')}`}
              aria-label={`Pour plus de renseignements, appelez le ${CONTACT_PHONE}`}
              className="block border-t border-l-4 border-white/20 border-l-[#7ec843] px-5 py-3 transition hover:bg-black/30"
            >
              <span className="block text-base text-white/85">
                Pour plus de renseignements, appelez le
              </span>
              <strong className="block text-3xl font-bold tracking-wide text-[#7ec843]">
                {CONTACT_PHONE}
              </strong>
            </a>
          </div>
        </div>
      </main>

      <section
        aria-label="Nos dispositifs"
        className="relative z-10 mx-auto grid w-full max-w-7xl shrink-0 gap-3 px-6 pb-3 md:grid-cols-3"
      >
        {content.sections.map((section, index) => (
          <article
            key={section.title}
            className="border-l-4 border-[#7ec843] bg-black/40 px-5 py-4 backdrop-blur-md"
          >
            <p className="text-sm font-semibold text-[#7ec843]">
              {String(index + 1).padStart(2, '0')}
              {section.duration && <span className="text-white/60"> — {section.duration}</span>}
            </p>
            <h2 className="font-display text-xl font-semibold">{section.title}</h2>
            <p className="mt-1 line-clamp-3 text-sm leading-relaxed text-white/80 [@media(min-height:820px)]:line-clamp-6">
              {section.description}
            </p>
            {section.highlight && (
              <p className="mt-2 line-clamp-1 text-sm font-medium text-white [@media(max-height:780px)]:hidden">
                {section.highlight}
              </p>
            )}
          </article>
        ))}
      </section>

      <footer className="relative z-10 shrink-0 py-3 text-center text-xs text-white/60">
        <LegalLinks className="mb-1" />© {new Date().getFullYear()} Maison de l'Entreprise
      </footer>
    </div>
  )
}
