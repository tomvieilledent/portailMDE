/** Page de garde : présentation des dispositifs et accès à la connexion. */

import { Link } from 'react-router-dom'

import LegalLinks from '../components/LegalLinks'
import Logo from '../components/Logo'
import { useLanding } from '../features/landing/useLanding'
import { useDocumentTitle } from '../lib/useDocumentTitle'

/** Page de garde : photo plein cadre, titre en grand et dispositifs numérotés. */
export default function HomePage() {
  const { content } = useLanding()
  useDocumentTitle('Accueil')

  return (
    <div
      className="relative flex min-h-screen flex-col overflow-hidden bg-[#1a3a2a] bg-cover bg-center text-white"
      style={{ backgroundImage: 'url(/1920.webp)' }}
    >
      <div className="absolute inset-0 bg-gradient-to-r from-black/60 via-black/50 to-black/75" />
      <div className="absolute inset-x-0 bottom-0 h-1/2 bg-gradient-to-t from-black/60 to-transparent" />

      <header className="relative z-10 mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-6">
        <div className="flex items-center gap-4">
          <Logo className="h-12" onDark />
          <span className="hidden h-8 w-px bg-white/25 sm:block" />
          <p className="hidden text-sm leading-snug font-medium text-white/80 sm:block">
            Maison de l'Économie
            <br />
            Rodez Agglomération
          </p>
        </div>
        <Link
          to="/connexion"
          className="border border-white/50 px-5 py-2 text-sm font-semibold transition hover:bg-[#5da020] hover:text-[#4a7a1a]"
        >
          Se connecter
        </Link>
      </header>

      <main className="relative z-10 mx-auto flex w-full max-w-6xl flex-1 flex-col justify-center px-6 py-16">
        <p className="mb-6 text-sm font-semibold text-[#7ec843]">
          Maison de l'Économie · Rodez Agglomération
        </p>
        <h1 className="font-display max-w-3xl text-5xl leading-[1.02] font-bold tracking-tight sm:text-7xl">
          {content.slogan}
        </h1>
        <span className="mt-6 block h-1 w-20 bg-[#7ec843]" aria-hidden="true" />
        {content.subtitle && (
          <p className="mt-6 max-w-xl text-lg leading-relaxed text-white/75">{content.subtitle}</p>
        )}
        <Link
          to="/connexion"
          className="mt-10 inline-flex w-fit items-center gap-3 bg-[#7ec843] px-7 py-3.5 font-semibold text-white transition hover:bg-[#5da020]"
        >
          Accéder au portail
          <span aria-hidden="true">→</span>
        </Link>
      </main>

      <section
        aria-label="Nos dispositifs"
        className="relative z-10 mx-auto grid w-full max-w-6xl gap-px px-6 pb-10 md:grid-cols-3"
      >
        {content.sections.map((section, index) => (
          <article
            key={section.title}
            className="flex flex-col gap-3 border-t border-white/25 bg-white/5 p-6 backdrop-blur-md"
          >
            <p className="text-sm font-semibold text-[#7ec843]">
              {String(index + 1).padStart(2, '0')}
              {section.duration && <span className="text-white/50"> — {section.duration}</span>}
            </p>
            <h2 className="font-display text-2xl font-semibold">{section.title}</h2>
            <p className="text-sm leading-relaxed text-white/70">{section.description}</p>
            {section.highlight && (
              <p className="mt-auto pt-2 text-sm font-medium text-white">{section.highlight}</p>
            )}
          </article>
        ))}
      </section>

      <footer className="relative z-10 pb-6 text-center text-xs text-white/50">
        <LegalLinks className="mb-2" />© {new Date().getFullYear()} Maison de l'Entreprise
      </footer>
    </div>
  )
}
