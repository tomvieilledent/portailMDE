import React, { useState, useRef, useEffect } from 'react'
import { Search, Mail, Phone, MessageCircle, UserPlus, Building2, CreditCard, Download } from 'lucide-react'
import CreateAccountModal from '../modals/CreateAccountModal'
import { api, mediaUrl } from '../../lib/api'

// Backend user : {id, email, first_name, last_name, phone, profile_picture,
// business_card, is_super_admin, company_id}. Pas de « poste » ni de nom
// d'entreprise → on dérive le rôle d'affichage et on résout le nom via les
// entreprises chargées en parallèle.
function mapUser(u, companyById = {}) {
  const name = [u.first_name, u.last_name].filter(Boolean).join(' ') || u.email
  return {
    id: u.id,
    name,
    role: u.is_super_admin ? 'Administrateur' : 'Membre',
    jobTitle: u.job_title || '',
    company: companyById[u.company_id] || '',
    email: u.email,
    phone: u.phone || '—',
    photo: mediaUrl(u.profile_picture)
      || `https://ui-avatars.com/api/?name=${encodeURIComponent(name)}&background=4f8a8b&color=fff`,
    isAdmin: !!u.is_super_admin,
    business_card: mediaUrl(u.business_card) || null,
  }
}

const COMPANY_COLORS = {
  'Maison de l\'Économie': { bg: 'bg-primary-light', light: 'bg-primary-light/10', text: 'text-primary-light', hex: '#4f8a8b' },
  'Tech Innovators':       { bg: 'bg-orange-500',    light: 'bg-orange-50',        text: 'text-orange-600',    hex: '#f97316' },
  'Digital Solutions':     { bg: 'bg-blue-500',      light: 'bg-blue-50',          text: 'text-blue-600',      hex: '#3b82f6' },
  'Green Energy Co.':      { bg: 'bg-green-500',     light: 'bg-green-50',         text: 'text-green-600',     hex: '#22c55e' },
  'Creative Studio':       { bg: 'bg-purple-500',    light: 'bg-purple-50',        text: 'text-purple-600',    hex: '#a855f7' },
}

function getColor(company) {
  return COMPANY_COLORS[company] || { bg: 'bg-gray-500', light: 'bg-gray-50', text: 'text-gray-600', hex: '#6b7280' }
}

function FlipCard({ user, flipped, onFlip, onContact, businessCard, bio }) {
  const color = getColor(user.company)

  return (
    <div
      className={`flip-card cursor-pointer${flipped ? ' flipped' : ''}`}
      style={{ height: '330px' }}
      onClick={onFlip}
    >
      <div className="flip-card-inner">

        {/* ── FACE AVANT ── */}
        <div className="flip-card-front bg-white shadow-sm border border-gray-100 flex flex-col items-center text-center p-6 hover:shadow-md transition-shadow">
          <img
            src={user.photo}
            alt={user.name}
            className="w-20 h-20 rounded-full object-cover mb-3 border-2 border-gray-100 shadow-sm"
          />
          <h3 className="font-bold text-gray-900 text-base">{user.name}</h3>
          {user.jobTitle && <p className="text-sm font-medium text-gray-700 mt-0.5">{user.jobTitle}</p>}
          {!user.isAdmin && <p className="text-xs text-gray-400 mt-0.5">{user.role}</p>}
          {user.isAdmin && (
            <span className="mt-1 inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-primary-light/10 text-primary-light">
              ★ Admin MDE
            </span>
          )}
          <p className="text-xs font-semibold mt-1 mb-4 text-primary-light">{user.company}</p>

          <div className="w-full space-y-2 text-sm text-gray-600 border-t border-gray-100 pt-4 mb-3">
            <div className="flex items-center gap-2 justify-center">
              <Mail size={14} className="text-gray-400" />
              <span className="truncate text-xs">{user.email}</span>
            </div>
            <div className="flex items-center gap-2 justify-center">
              <Phone size={14} className="text-gray-400" />
              <span className="text-xs">{user.phone}</span>
            </div>
          </div>

          {bio && (
            <p className="text-xs text-gray-500 italic text-center leading-relaxed px-1 mb-2 border-t border-gray-100 pt-3 w-full line-clamp-3">
              {bio}
            </p>
          )}

          {businessCard && (
            <div className="mt-auto flex items-center justify-center gap-1.5 text-xs text-gray-400 pt-2">
              <CreditCard size={13} /> Carte de visite au dos
            </div>
          )}
        </div>

        {/* ── FACE ARRIÈRE — clic sur zone vide = flip retour ── */}
        <div className="flip-card-back shadow-md border border-gray-100 bg-white flex flex-col overflow-hidden">

          {businessCard ? (
            /* Image uploadée — centrée à bonnes proportions */
            <>
              {/* Barre du haut */}
              <div className="flex items-center justify-between px-4 py-2 border-b border-gray-100 flex-shrink-0">
                <span className="text-xs font-semibold text-gray-500">Carte de visite</span>
                <a
                  href={businessCard}
                  download="carte-de-visite.jpg"
                  onClick={(e) => e.stopPropagation()}
                  className="p-1 rounded-lg hover:bg-gray-100 text-gray-400 hover:text-primary-light transition-colors"
                  title="Télécharger la carte"
                >
                  <Download size={14} />
                </a>
              </div>

              {/* Image élargie */}
              <div className="flex-1 flex items-center justify-center px-3 py-2 bg-gray-50">
                <img
                  src={businessCard}
                  alt="Carte de visite"
                  className="w-full max-h-56 object-contain rounded-md shadow-md"
                />
              </div>

              {/* Hint retour */}
              <p className="text-center text-xs text-gray-300 py-1.5 flex-shrink-0">Cliquer pour retourner</p>
            </>
          ) : (
            /* Carte générée par défaut */
            <>
              <div className={`${color.bg} px-5 pt-4 pb-9 relative flex-shrink-0`}>
                <div className="flex items-center justify-between mb-1">
                  <p className="text-xs font-semibold text-white/80 uppercase tracking-wider">{user.company}</p>
                </div>
                <h3 className="text-lg font-bold text-white leading-tight">{user.name}</h3>
                <p className="text-sm text-white/80">{user.jobTitle || user.role}</p>
              </div>

              <div className="relative flex-1 bg-white px-5 pb-4">
                <img
                  src={user.photo}
                  alt={user.name}
                  className="w-14 h-14 rounded-full object-cover border-4 border-white shadow-md absolute -top-7 right-5"
                />
                <div className="pt-3 space-y-2 mt-1">
                  <a href={`mailto:${user.email}`} onClick={(e) => e.stopPropagation()}
                    className="flex items-center gap-2 text-gray-700 hover:text-primary-light transition-colors">
                    <div className={`w-6 h-6 ${color.light} rounded-md flex items-center justify-center flex-shrink-0`}>
                      <Mail size={11} className={color.text} />
                    </div>
                    <span className="truncate text-xs">{user.email}</span>
                  </a>
                  <a href={`tel:${user.phone}`} onClick={(e) => e.stopPropagation()}
                    className="flex items-center gap-2 text-gray-700 hover:text-primary-light transition-colors">
                    <div className={`w-6 h-6 ${color.light} rounded-md flex items-center justify-center flex-shrink-0`}>
                      <Phone size={11} className={color.text} />
                    </div>
                    <span className="text-xs">{user.phone}</span>
                  </a>
                  <div className="flex items-center gap-2 text-gray-500">
                    <div className={`w-6 h-6 ${color.light} rounded-md flex items-center justify-center flex-shrink-0`}>
                      <Building2 size={11} className={color.text} />
                    </div>
                    <span className="text-xs">{user.company}</span>
                  </div>
                </div>

                <div className="mt-3 flex gap-2">
                  <button
                    onClick={(e) => { e.stopPropagation(); onContact?.(user.name) }}
                    className={`flex-1 ${color.bg} hover:opacity-90 text-white text-xs font-semibold py-1.5 rounded-xl transition-opacity flex items-center justify-center gap-1.5`}
                  >
                    <MessageCircle size={13} /> Contacter
                  </button>
                </div>
              </div>
            </>
          )}
        </div>

      </div>
    </div>
  )
}

export default function Users({ onContact, role, canManage = false, profile }) {
  const [users, setUsers] = useState([])
  const [companies, setCompanies] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [flipped, setFlipped] = useState(new Set())
  const [createModal, setCreateModal] = useState(false)

  // Utilisateurs + entreprises (pour résoudre le nom d'entreprise par id et
  // alimenter le sélecteur d'entreprise à la création d'un admin).
  const loadData = () =>
    Promise.all([api.getUsers(), api.getCompanies().catch(() => ({ companies: [] }))])
      .then(([usersRes, compRes]) => {
        const list = usersRes?.users || (Array.isArray(usersRes) ? usersRes : [])
        const comps = compRes?.companies || []
        const companyById = Object.fromEntries(comps.map((c) => [c.id, c.name]))
        setCompanies(comps)
        setUsers(list.map((u) => mapUser(u, companyById)))
      })

  useEffect(() => {
    let cancelled = false
    loadData()
      .catch((err) => { if (!cancelled) setError(err.message) })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [])

  const toggleFlip = (id) => setFlipped((prev) => {
    const next = new Set(prev)
    next.has(id) ? next.delete(id) : next.add(id)
    return next
  })

  // Carte de visite effective : la carte fraîchement éditée du profil connecté
  // prime sur la valeur persistée renvoyée par l'API (user.business_card).
  const resolveCard = (user) => {
    if (profile?.id === user.id && profile?.businessCard) return profile.businessCard
    return user.business_card || null
  }

  // Création réelle : on recharge le répertoire après ajout d'un admin.
  const handleNewAccount = () => { loadData().catch((err) => setError(err.message)) }

  const filtered = users.filter(
    (u) =>
      u.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      u.company.toLowerCase().includes(searchQuery.toLowerCase())
  )

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Professionnels</h2>
          <p className="text-sm text-gray-500 mt-1">Répertoire des professionnels de la pépinière</p>
        </div>
        {(role === 'admin' || canManage) && (
          <button onClick={() => setCreateModal(true)} className="flex items-center gap-2 btn-primary text-sm">
            <UserPlus size={16} /> Créer un utilisateur
          </button>
        )}
      </div>

      <div className="relative mb-6">
        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
        <input
          type="text"
          placeholder="Rechercher par nom ou entreprise..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full pl-10 pr-4 py-3 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-light bg-white"
        />
      </div>

      {loading && <p className="text-gray-400 py-8 text-center">Chargement des professionnels…</p>}
      {error && <p className="text-red-500 py-8 text-center">{error}</p>}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filtered.map((user) => (
          <FlipCard
            key={user.id}
            user={user}
            flipped={flipped.has(user.id)}
            onFlip={() => toggleFlip(user.id)}
            onContact={onContact}
            businessCard={resolveCard(user)}
          />
        ))}
      </div>

      {filtered.length === 0 && (
        <div className="text-center py-12">
          <p className="text-gray-400">Aucun professionnel ne correspond à votre recherche</p>
        </div>
      )}

      {createModal && (
        <CreateAccountModal
          forRole="patron"
          companies={companies}
          onClose={() => setCreateModal(false)}
          onSuccess={handleNewAccount}
        />
      )}
    </div>
  )
}
