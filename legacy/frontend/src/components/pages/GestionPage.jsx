import React, { useState, useEffect } from 'react'
import { Users, Building2, UserX, UserCheck, Trash2, AlertTriangle, ShieldCheck, Shield, X, Loader2, Home, Save, CheckCircle, UserPlus, KeyRound, FileDown, Download, Printer, RefreshCw, CalendarDays } from 'lucide-react'
import { api, mediaUrl } from '../../lib/api'
import { useAuth } from '../../context/AuthContext'
import StaffAccountModal, { PERMISSION_META, ALL_PERMISSIONS } from '../modals/StaffAccountModal'

// ── Rôle plateforme dérivé du backend ────────────────────────────────────────
// superAdmin = is_super_admin ; admin = administrateur d'une entreprise
// (Company.admin_id) ; user = ni l'un ni l'autre. Seul le rôle super admin est
// modifiable ici (le rôle « admin d'entreprise » se gère depuis la fiche
// entreprise via son email d'administrateur).
const getPlatformRole = (user) => {
  if (user.isSuperAdmin) return 'superAdmin'
  if (user.isStaff)      return 'staff'
  if (user.isAdmin)      return 'admin'
  return 'user'
}

const ROLE_META = {
  user:       { label: 'Utilisateur',  color: 'bg-gray-100 text-gray-600',              icon: <Users size={9} /> },
  admin:      { label: "Admin d'entreprise", color: 'bg-primary-light/10 text-primary-light', icon: <Shield size={9} /> },
  staff:      { label: 'Staff',        color: 'bg-indigo-100 text-indigo-600',          icon: <Shield size={9} /> },
  superAdmin: { label: 'Super Admin',  color: 'bg-purple-100 text-purple-600',          icon: <ShieldCheck size={9} /> },
}

function RoleBadge({ user }) {
  const meta = ROLE_META[getPlatformRole(user)]
  return (
    <span className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full text-xs font-semibold ${meta.color}`}>
      {meta.icon} {meta.label}
    </span>
  )
}

// ── Modal : basculer le rôle Super Admin ─────────────────────────────────────
function RoleModal({ target, isLastSuperAdmin, onClose, onConfirm }) {
  const currentlySuper = target.isSuperAdmin
  const [makeSuper, setMakeSuper] = useState(currentlySuper)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  // On ne peut pas rétrograder le dernier super admin actif.
  const demotingLast = currentlySuper && !makeSuper && isLastSuperAdmin
  const canConfirm = makeSuper !== currentlySuper && !demotingLast

  const confirm = async () => {
    setError('')
    setSubmitting(true)
    try {
      await onConfirm(makeSuper)
    } catch (err) {
      setError(err.message || 'Échec de la modification du rôle')
      setSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4" onClick={onClose}>
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-sm overflow-hidden" onClick={(e) => e.stopPropagation()}>

        <div className="bg-primary-light px-5 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 bg-white/20 rounded-xl flex items-center justify-center flex-shrink-0">
              <Shield size={18} className="text-white" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white">Modifier le rôle</h3>
              <p className="text-xs text-white/80">{target.name}</p>
            </div>
          </div>
          <button onClick={onClose} className="text-white/70 hover:text-white"><X size={18} /></button>
        </div>

        <div className="px-5 py-5 space-y-3">
          {error && (
            <div className="px-3 py-2.5 rounded-lg bg-red-50 border border-red-200 text-sm text-red-600">{error}</div>
          )}
          <div className="flex items-center gap-3 bg-gray-50 rounded-xl p-3">
            <img src={target.photo} alt={target.name} className="w-10 h-10 rounded-full object-cover border border-gray-100 flex-shrink-0" />
            <div>
              <p className="text-sm font-semibold text-gray-900">{target.name}</p>
              <p className="text-xs text-gray-500">{target.email}{target.company ? ` · ${target.company}` : ''}</p>
            </div>
          </div>

          {target.isAdmin && !target.isSuperAdmin && (
            <p className="text-xs text-gray-400 italic">
              Cet utilisateur est administrateur d'une entreprise — ce rôle se gère depuis la fiche entreprise.
            </p>
          )}

          <label className="flex items-start gap-3 p-3 rounded-xl border border-gray-100 cursor-pointer hover:bg-gray-50">
            <input type="checkbox" checked={makeSuper} onChange={(e) => setMakeSuper(e.target.checked)}
              className="mt-0.5 w-4 h-4 accent-purple-500 flex-shrink-0" />
            <div>
              <span className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full text-xs font-semibold ${ROLE_META.superAdmin.color}`}>
                {ROLE_META.superAdmin.icon} Super Admin
              </span>
              <p className="text-xs text-gray-500 mt-1">Accès complet — peut gérer tous les comptes et toutes les entreprises.</p>
            </div>
          </label>

          {demotingLast && (
            <p className="text-xs text-red-500 font-medium">
              Impossible : dernier Super Admin actif. Nommez un remplaçant d'abord.
            </p>
          )}

          <div className="flex gap-2 pt-1">
            <button onClick={onClose} disabled={submitting}
              className="flex-1 border border-gray-200 text-gray-600 hover:bg-gray-50 font-medium py-2.5 rounded-xl text-sm transition-colors disabled:opacity-60">
              Annuler
            </button>
            <button onClick={confirm} disabled={!canConfirm || submitting}
              className="flex-1 bg-primary-light hover:bg-primary disabled:opacity-40 disabled:cursor-not-allowed text-white font-semibold py-2.5 rounded-xl text-sm transition-colors flex items-center justify-center gap-1.5">
              {submitting ? <Loader2 size={14} className="animate-spin" /> : <Shield size={14} />} Confirmer
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

// ── Modal : gérer les droits « staff » d'un compte ───────────────────────────
function PermissionsModal({ target, onClose, onConfirm }) {
  const [isStaff, setIsStaff] = useState(target.isStaff)
  const [perms, setPerms] = useState(() => new Set(target.permissions || []))
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  const togglePerm = (key) => setPerms((prev) => {
    const next = new Set(prev)
    next.has(key) ? next.delete(key) : next.add(key)
    return next
  })

  const canConfirm = !isStaff || perms.size > 0

  const confirm = async () => {
    setError('')
    setSubmitting(true)
    try {
      await onConfirm(isStaff, isStaff ? Array.from(perms) : [])
    } catch (err) {
      setError(err.message || 'Échec de la modification des droits')
      setSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4" onClick={onClose}>
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md overflow-hidden max-h-[92vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
        <div className="bg-indigo-500 px-5 py-4 flex items-center justify-between sticky top-0">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 bg-white/20 rounded-xl flex items-center justify-center flex-shrink-0">
              <KeyRound size={18} className="text-white" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white">Droits du staff</h3>
              <p className="text-xs text-white/80">{target.name}</p>
            </div>
          </div>
          <button onClick={onClose} className="text-white/70 hover:text-white"><X size={18} /></button>
        </div>

        <div className="px-5 py-5 space-y-3">
          {error && (
            <div className="px-3 py-2.5 rounded-lg bg-red-50 border border-red-200 text-sm text-red-600">{error}</div>
          )}

          <label className="flex items-start gap-3 p-3 rounded-xl border border-gray-100 cursor-pointer hover:bg-gray-50">
            <input type="checkbox" checked={isStaff} onChange={(e) => setIsStaff(e.target.checked)}
              className="mt-0.5 w-4 h-4 accent-indigo-500 flex-shrink-0" />
            <div>
              <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-100 text-indigo-600">
                <Shield size={9} /> Membre du staff
              </span>
              <p className="text-xs text-gray-500 mt-1">Active un accès d'administration ciblé selon les droits ci-dessous.</p>
            </div>
          </label>

          {isStaff && (
            <div className="space-y-2">
              {ALL_PERMISSIONS.map((key) => {
                const meta = PERMISSION_META[key]
                const Icon = meta.icon
                const checked = perms.has(key)
                return (
                  <label key={key}
                    className={`flex items-start gap-3 p-3 rounded-xl border cursor-pointer transition-colors ${checked ? 'border-indigo-300 bg-indigo-50/60' : 'border-gray-100 hover:bg-gray-50'}`}>
                    <input type="checkbox" checked={checked} onChange={() => togglePerm(key)}
                      className="mt-0.5 w-4 h-4 accent-indigo-500 flex-shrink-0" />
                    <Icon size={16} className="text-indigo-600 mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="text-sm font-semibold text-gray-900">{meta.label}</p>
                      <p className="text-xs text-gray-500">{meta.desc}</p>
                    </div>
                  </label>
                )
              })}
            </div>
          )}

          <div className="flex gap-2 pt-1">
            <button onClick={onClose} disabled={submitting}
              className="flex-1 border border-gray-200 text-gray-600 hover:bg-gray-50 font-medium py-2.5 rounded-xl text-sm transition-colors disabled:opacity-60">
              Annuler
            </button>
            <button onClick={confirm} disabled={!canConfirm || submitting}
              className="flex-1 bg-indigo-500 hover:bg-indigo-600 disabled:opacity-40 disabled:cursor-not-allowed text-white font-semibold py-2.5 rounded-xl text-sm transition-colors flex items-center justify-center gap-1.5">
              {submitting ? <Loader2 size={14} className="animate-spin" /> : <KeyRound size={14} />} Enregistrer
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

// ── Modal : suppression définitive ───────────────────────────────────────────
function DeleteUserModal({ user, onClose, onConfirm }) {
  const [checked, setChecked] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  const confirm = async () => {
    setError('')
    setSubmitting(true)
    try {
      await onConfirm()
    } catch (err) {
      setError(err.message || 'Échec de la suppression')
      setSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4" onClick={onClose}>
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-sm overflow-hidden" onClick={(e) => e.stopPropagation()}>
        <div className="bg-red-500 px-5 py-4 flex items-center gap-3">
          <div className="w-9 h-9 bg-white/20 rounded-xl flex items-center justify-center flex-shrink-0">
            <Trash2 size={18} className="text-white" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white">Suppression définitive</h3>
            <p className="text-xs text-white/80">Cette action est irréversible</p>
          </div>
        </div>
        <div className="px-5 py-5 space-y-4">
          {error && (
            <div className="px-3 py-2.5 rounded-lg bg-red-50 border border-red-200 text-sm text-red-600">{error}</div>
          )}
          <div className="flex items-center gap-3 bg-gray-50 rounded-xl p-3">
            <img src={user.photo} alt={user.name} className="w-10 h-10 rounded-full object-cover border border-gray-200 flex-shrink-0" />
            <div>
              <p className="text-sm font-semibold text-gray-900">{user.name}</p>
              <p className="text-xs text-gray-500">{user.email}{user.company ? ` · ${user.company}` : ''}</p>
            </div>
          </div>
          <div className="flex items-start gap-2 bg-amber-50 border border-amber-200 rounded-xl p-3">
            <AlertTriangle size={15} className="text-amber-500 flex-shrink-0 mt-0.5" />
            <p className="text-xs text-amber-700 leading-relaxed">
              Le compte et toutes les données de <span className="font-semibold">{user.name}</span> seront supprimés définitivement.
            </p>
          </div>
          <label className="flex items-start gap-3 cursor-pointer">
            <input type="checkbox" checked={checked} onChange={(e) => setChecked(e.target.checked)}
              className="mt-0.5 w-4 h-4 accent-red-500 flex-shrink-0" />
            <span className="text-sm text-gray-700 leading-snug">
              Je confirme la suppression <span className="font-semibold text-red-600">définitive et irréversible</span> de ce compte
            </span>
          </label>
          <div className="flex gap-2">
            <button onClick={onClose} disabled={submitting}
              className="flex-1 border border-gray-200 text-gray-600 hover:bg-gray-50 font-medium py-2.5 rounded-xl text-sm transition-colors disabled:opacity-60">Annuler</button>
            <button onClick={confirm} disabled={!checked || submitting}
              className="flex-1 bg-red-500 hover:bg-red-600 disabled:opacity-40 disabled:cursor-not-allowed text-white font-semibold py-2.5 rounded-xl text-sm transition-colors flex items-center justify-center gap-1.5">
              {submitting ? <Loader2 size={14} className="animate-spin" /> : <Trash2 size={14} />} Supprimer
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

// ── Modal : réassigner l'admin d'entreprise avant désactivation ──────────────
function ReassignAdminModal({ target, onClose, onConfirm }) {
  const [members, setMembers] = useState([])
  const [selected, setSelected] = useState('')
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    let cancelled = false
    api.getUsers(`?company_id=${target.companyId || target.adminCompanyId}`)
      .then((res) => {
        if (cancelled) return
        const list = (res?.users || [])
          .filter((u) => u.is_active && u.id !== target.id)
          .map((u) => ({ id: u.id, email: u.email, name: [u.first_name, u.last_name].filter(Boolean).join(' ') || u.email }))
        setMembers(list)
        setSelected(list[0]?.email || '')
      })
      .catch((err) => { if (!cancelled) setError(err.message) })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [target])

  const confirm = async () => {
    setError('')
    setSubmitting(true)
    try { await onConfirm(selected) }
    catch (err) { setError(err.message || 'Échec de la réassignation'); setSubmitting(false) }
  }

  return (
    <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4" onClick={onClose}>
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-sm overflow-hidden" onClick={(e) => e.stopPropagation()}>
        <div className="bg-amber-500 px-5 py-4 flex items-center gap-3">
          <div className="w-9 h-9 bg-white/20 rounded-xl flex items-center justify-center flex-shrink-0">
            <Shield size={18} className="text-white" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white">Réassigner l'administration</h3>
            <p className="text-xs text-white/80">Avant de désactiver {target.name}</p>
          </div>
        </div>
        <div className="px-5 py-5 space-y-4">
          <p className="text-sm text-gray-600">
            <span className="font-semibold">{target.name}</span> administre une entreprise.
            Nommez un autre membre administrateur avant de le désactiver.
          </p>
          {error && (
            <div className="px-3 py-2.5 rounded-lg bg-red-50 border border-red-200 text-sm text-red-600">{error}</div>
          )}
          {loading ? (
            <p className="text-sm text-gray-400">Chargement des membres…</p>
          ) : members.length === 0 ? (
            <p className="text-sm text-amber-600 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2">
              Aucun autre membre actif dans cette entreprise. Ajoutez d'abord un membre.
            </p>
          ) : (
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1.5">Nouvel administrateur</label>
              <select value={selected} onChange={(e) => setSelected(e.target.value)}
                className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-amber-400 bg-white">
                {members.map((m) => <option key={m.id} value={m.email}>{m.name} — {m.email}</option>)}
              </select>
            </div>
          )}
          <div className="flex gap-2 pt-1">
            <button onClick={onClose} disabled={submitting}
              className="flex-1 border border-gray-200 text-gray-600 hover:bg-gray-50 font-medium py-2.5 rounded-xl text-sm transition-colors disabled:opacity-60">
              Annuler
            </button>
            <button onClick={confirm} disabled={!selected || submitting || members.length === 0}
              className="flex-1 bg-amber-500 hover:bg-amber-600 disabled:opacity-40 disabled:cursor-not-allowed text-white font-semibold py-2.5 rounded-xl text-sm transition-colors flex items-center justify-center gap-1.5">
              {submitting ? <Loader2 size={14} className="animate-spin" /> : <UserCheck size={14} />} Réassigner & désactiver
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

// ── Modal : suppression définitive d'une entreprise ──────────────────────────
function DeleteCompanyModal({ company, onClose, onConfirm }) {
  const [checked, setChecked] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  const confirm = async () => {
    setError('')
    setSubmitting(true)
    try { await onConfirm() }
    catch (err) { setError(err.message || 'Échec de la suppression'); setSubmitting(false) }
  }

  return (
    <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4" onClick={onClose}>
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-sm overflow-hidden" onClick={(e) => e.stopPropagation()}>
        <div className="bg-red-500 px-5 py-4 flex items-center gap-3">
          <div className="w-9 h-9 bg-white/20 rounded-xl flex items-center justify-center flex-shrink-0">
            <Trash2 size={18} className="text-white" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white">Supprimer l'entreprise</h3>
            <p className="text-xs text-white/80">Cette action est irréversible</p>
          </div>
        </div>
        <div className="px-5 py-5 space-y-4">
          {error && (
            <div className="px-3 py-2.5 rounded-lg bg-red-50 border border-red-200 text-sm text-red-600">{error}</div>
          )}
          <div className="flex items-start gap-2 bg-amber-50 border border-amber-200 rounded-xl p-3">
            <AlertTriangle size={15} className="text-amber-500 flex-shrink-0 mt-0.5" />
            <p className="text-xs text-amber-700 leading-relaxed">
              <span className="font-semibold">{company.name}</span> sera supprimée définitivement.
              Les comptes liés ne sont pas supprimés mais perdent leur rattachement.
            </p>
          </div>
          <label className="flex items-start gap-3 cursor-pointer">
            <input type="checkbox" checked={checked} onChange={(e) => setChecked(e.target.checked)}
              className="mt-0.5 w-4 h-4 accent-red-500 flex-shrink-0" />
            <span className="text-sm text-gray-700 leading-snug">
              Je confirme la suppression <span className="font-semibold text-red-600">définitive</span> de cette entreprise
            </span>
          </label>
          <div className="flex gap-2">
            <button onClick={onClose} disabled={submitting}
              className="flex-1 border border-gray-200 text-gray-600 hover:bg-gray-50 font-medium py-2.5 rounded-xl text-sm transition-colors disabled:opacity-60">Annuler</button>
            <button onClick={confirm} disabled={!checked || submitting}
              className="flex-1 bg-red-500 hover:bg-red-600 disabled:opacity-40 disabled:cursor-not-allowed text-white font-semibold py-2.5 rounded-xl text-sm transition-colors flex items-center justify-center gap-1.5">
              {submitting ? <Loader2 size={14} className="animate-spin" /> : <Trash2 size={14} />} Supprimer
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

// ── Mapping backend → UI ─────────────────────────────────────────────────────
function mapUser(u, adminCompanyByUserId, companyById) {
  const name = [u.first_name, u.last_name].filter(Boolean).join(' ') || u.email
  const adminCompany = adminCompanyByUserId[u.id] || null
  return {
    id: u.id,
    name,
    email: u.email,
    companyId: u.company_id || null,
    company: companyById[u.company_id] || '',
    photo: mediaUrl(u.profile_picture)
      || `https://ui-avatars.com/api/?name=${encodeURIComponent(name)}&background=4f8a8b&color=fff`,
    isSuperAdmin: !!u.is_super_admin,
    isStaff: !!u.is_staff,
    permissions: u.permissions || [],
    isAdmin: !!adminCompany,
    // Entreprise que l'utilisateur administre (pour la réassignation).
    adminCompanyId: adminCompany?.id || null,
    deactivated: !u.is_active,
  }
}

function mapCompany(c) {
  return { id: c.id, name: c.name, sector: c.description || '—', location: '—', employees: '', deactivated: !c.is_active }
}

// ── Main ──────────────────────────────────────────────────────────────────────
// ── Éditeur de la page d'accueil (super-admin) ───────────────────────────────
function Field({ label, value, onChange, textarea }) {
  const cls = 'w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-light'
  return (
    <div>
      <label className="block text-xs font-semibold text-gray-500 mb-1">{label}</label>
      {textarea ? (
        <textarea rows={3} value={value} onChange={(e) => onChange(e.target.value)} className={`${cls} resize-none`} />
      ) : (
        <input type="text" value={value} onChange={(e) => onChange(e.target.value)} className={cls} />
      )}
    </div>
  )
}

function LandingEditor() {
  const [content, setContent] = useState(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving]   = useState(false)
  const [saved, setSaved]     = useState(false)
  const [error, setError]     = useState('')

  useEffect(() => {
    let cancelled = false
    api.getLandingContent()
      .then((res) => { if (!cancelled) setContent(res?.content || null) })
      .catch((err) => { if (!cancelled) setError(err.message) })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [])

  const setField = (key, val) => setContent((prev) => ({ ...prev, [key]: val }))
  const setSection = (i, key, val) => setContent((prev) => ({
    ...prev,
    sections: prev.sections.map((s, idx) => idx === i ? { ...s, [key]: val } : s),
  }))

  const save = async () => {
    setSaving(true); setError(''); setSaved(false)
    try {
      const res = await api.updateLandingContent(content)
      setContent(res?.content || content)
      setSaved(true)
      setTimeout(() => setSaved(false), 3000)
    } catch (err) { setError(err.message) }
    finally { setSaving(false) }
  }

  if (loading) return <p className="text-gray-400 py-8 text-center">Chargement…</p>
  if (!content) return <p className="text-red-500 py-4">{error || 'Contenu indisponible'}</p>

  return (
    <div className="space-y-6 max-w-3xl">
      <p className="text-sm text-gray-500">
        Ces textes s'affichent sur la page d'accueil publique (avant connexion).
      </p>

      <div className="bg-white border border-gray-100 rounded-xl p-5 space-y-3 shadow-sm">
        <h3 className="text-sm font-bold text-gray-900">Accroche principale</h3>
        <Field label="Slogan" value={content.slogan || ''} onChange={(v) => setField('slogan', v)} />
        <Field label="Sous-titre" value={content.subtitle || ''} onChange={(v) => setField('subtitle', v)} textarea />
      </div>

      {(content.sections || []).map((s, i) => (
        <div key={i} className="bg-white border border-gray-100 rounded-xl p-5 space-y-3 shadow-sm">
          <h3 className="text-sm font-bold text-gray-900">Carte {i + 1}</h3>
          <div className="grid grid-cols-2 gap-3">
            <Field label="Titre" value={s.title || ''} onChange={(v) => setSection(i, 'title', v)} />
            <Field label="Durée" value={s.duration || ''} onChange={(v) => setSection(i, 'duration', v)} />
          </div>
          <Field label="Description" value={s.description || ''} onChange={(v) => setSection(i, 'description', v)} textarea />
          <Field label="Accroche (laisser vide pour masquer)" value={s.highlight || ''} onChange={(v) => setSection(i, 'highlight', v)} />
        </div>
      ))}

      {error && <p className="text-sm text-red-500">{error}</p>}

      <div className="flex items-center gap-3">
        <button onClick={save} disabled={saving}
          className="flex items-center gap-2 bg-primary-light hover:bg-primary disabled:opacity-50 text-white font-semibold px-5 py-2.5 rounded-xl transition-colors text-sm">
          {saving ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />}
          Enregistrer
        </button>
        {saved && (
          <span className="flex items-center gap-1.5 text-sm text-green-600 font-medium">
            <CheckCircle size={16} /> Enregistré
          </span>
        )}
      </div>
    </div>
  )
}

// ── Export mensuel de l'agenda (super-admin) ─────────────────────────────────
const EXPORT_MONTHS = ['Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
  'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre']

function nextMonth() {
  const now = new Date()
  const d = new Date(now.getFullYear(), now.getMonth() + 1, 1)
  return { year: d.getFullYear(), month: d.getMonth() + 1 }
}

function ExportPanel() {
  const [exports, setExports] = useState([])
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState('')
  const [error, setError] = useState('')
  const nxt = nextMonth()
  const [year, setYear] = useState(nxt.year)
  const [month, setMonth] = useState(nxt.month)

  const load = () =>
    api.getMonthlyExports()
      .then((res) => setExports(res.exports || []))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))

  useEffect(() => { load() }, [])

  // `tag` identifie le bouton en cours (pour le spinner) ; target = {year, month}.
  const handleGenerate = async (target, tag = 'custom') => {
    const y = Number(target?.year ?? year)
    const m = Number(target?.month ?? month)
    setGenerating(tag)
    setError('')
    try {
      await api.generateMonthlyExport({ year: y, month: m })
      setYear(y); setMonth(m)
      await load()
    } catch (err) {
      setError(err.message)
    } finally {
      setGenerating('')
    }
  }

  const years = [nxt.year - 1, nxt.year, nxt.year + 1]

  return (
    <div className="space-y-6">
      <p className="text-sm text-gray-500">
        Feuille imprimable : <strong>événements publics</strong>, <strong>formations</strong> et <strong>ateliers</strong> du mois.
        Une feuille du mois suivant est générée automatiquement le 25 de chaque mois.
      </p>

      {/* Génération à la demande */}
      <div className="bg-white border border-gray-100 rounded-xl p-4 shadow-sm flex flex-wrap items-end gap-3">
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">Mois</label>
          <select value={month} onChange={(e) => setMonth(e.target.value)}
            className="px-3 py-2 border border-gray-200 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-primary-light">
            {EXPORT_MONTHS.map((m, i) => <option key={m} value={i + 1}>{m}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">Année</label>
          <select value={year} onChange={(e) => setYear(e.target.value)}
            className="px-3 py-2 border border-gray-200 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-primary-light">
            {years.map((y) => <option key={y} value={y}>{y}</option>)}
          </select>
        </div>
        <button onClick={() => handleGenerate(null, 'custom')} disabled={!!generating}
          className="flex items-center gap-2 bg-primary-light hover:bg-primary text-white font-semibold px-4 py-2 rounded-lg text-sm transition-colors disabled:opacity-60">
          {generating === 'custom' ? <Loader2 size={15} className="animate-spin" /> : <RefreshCw size={15} />}
          Générer maintenant
        </button>
      </div>

      {error && <p className="text-red-500 text-sm">{error}</p>}

      {/* Feuilles disponibles */}
      {loading ? (
        <p className="text-gray-400 py-6 text-center">Chargement…</p>
      ) : exports.length === 0 ? (
        <p className="text-gray-400 py-6 text-center">Aucune feuille générée pour le moment.</p>
      ) : (
        <div className="space-y-2">
          {exports.map((exp) => (
            <div key={exp.filename}
              className="border border-gray-100 rounded-xl px-4 py-3 flex items-center gap-4 shadow-sm bg-white">
              <div className="w-10 h-10 rounded-lg bg-primary-light/10 flex items-center justify-center flex-shrink-0">
                <CalendarDays size={18} className="text-primary-light" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold text-gray-900">{exp.label}</p>
                <p className="text-xs text-gray-400">
                  Générée le {new Date(exp.generated_at).toLocaleString('fr-FR')}
                  {typeof exp.count === 'number' ? ` · ${exp.count} élément(s)` : ''}
                </p>
              </div>
              <a href={mediaUrl(exp.url)} target="_blank" rel="noreferrer"
                className="flex items-center gap-1.5 border border-gray-200 text-gray-700 hover:bg-gray-50 font-medium px-3 py-1.5 rounded-lg text-sm transition-colors">
                <Printer size={14} /> Ouvrir / Imprimer
              </a>
              <a href={mediaUrl(exp.url)} download={exp.filename}
                className="flex items-center gap-1.5 border border-gray-200 text-gray-700 hover:bg-gray-50 font-medium px-3 py-1.5 rounded-lg text-sm transition-colors">
                <Download size={14} /> Télécharger
              </a>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default function GestionPage() {
  const { user: currentUser, can } = useAuth()
  const isSuperAdmin = !!currentUser?.is_super_admin
  // Sous-onglets visibles selon les droits (un super admin voit tout).
  const visibleTabs = {
    users:     can('manage_users'),
    companies: can('manage_companies'),
    landing:   can('manage_news'),
    export:    isSuperAdmin,
  }
  const firstVisible = ['users', 'companies', 'landing', 'export'].find((t) => visibleTabs[t]) || 'users'

  const [subTab,    setSubTab]    = useState(firstVisible)
  const [users,     setUsers]     = useState([])
  const [companies, setCompanies] = useState([])
  const [loading,   setLoading]   = useState(true)
  const [error,     setError]     = useState('')
  const [busyId,    setBusyId]    = useState(null)

  const [deleteModal, setDeleteModal] = useState(null)
  const [roleModal,   setRoleModal]   = useState(null)
  const [permsModal,  setPermsModal]  = useState(null)
  const [createModal, setCreateModal] = useState(false)
  const [reassignModal, setReassignModal] = useState(null)
  const [deleteCompanyModal, setDeleteCompanyModal] = useState(null)

  const loadData = () =>
    Promise.all([api.getUsers(), api.getCompanies()])
      .then(([{ users: rawUsers }, { companies: rawCompanies }]) => {
        const adminCompanyByUserId = Object.fromEntries(
          (rawCompanies || []).filter((c) => c.admin_id).map((c) => [c.admin_id, c]))
        const companyById = Object.fromEntries((rawCompanies || []).map((c) => [c.id, c.name]))
        setUsers((rawUsers || []).map((u) => mapUser(u, adminCompanyByUserId, companyById)))
        setCompanies((rawCompanies || []).map(mapCompany))
      })

  useEffect(() => {
    let cancelled = false
    loadData()
      .catch((err) => { if (!cancelled) setError(err.message) })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [])

  const activeSuperAdmins = users.filter((u) => u.isSuperAdmin && !u.deactivated)

  const patchUser = (id, changes) =>
    setUsers((prev) => prev.map((u) => u.id === id ? { ...u, ...changes } : u))

  const handleDeactivate = async (user) => {
    // Un admin d'entreprise ne peut être désactivé qu'après réassignation de
    // l'administration de son entreprise à un autre membre.
    if (user.isAdmin && user.adminCompanyId) {
      setReassignModal(user)
      return
    }
    setBusyId(user.id)
    try { await api.deactivateUser(user.id); patchUser(user.id, { deactivated: true }) }
    catch (err) { setError(err.message) }
    finally { setBusyId(null) }
  }

  // Réassigne l'admin de l'entreprise puis désactive l'ancien admin.
  const handleReassignConfirm = async (newAdminEmail) => {
    const target = reassignModal
    await api.updateCompany(target.adminCompanyId, { admin_email: newAdminEmail })
    await api.deactivateUser(target.id)
    setReassignModal(null)
    await loadData()
  }

  const handleReactivate = async (user) => {
    setBusyId(user.id)
    try { await api.reactivateUser(user.id); patchUser(user.id, { deactivated: false }) }
    catch (err) { setError(err.message) }
    finally { setBusyId(null) }
  }

  const handleDeleteConfirm = async () => {
    const user = deleteModal
    await api.deleteUser(user.id)
    setUsers((prev) => prev.filter((u) => u.id !== user.id))
    setDeleteModal(null)
  }

  const handleRoleConfirm = async (makeSuper) => {
    const target = roleModal
    const { user } = await api.setUserRole(target.id, makeSuper)
    patchUser(target.id, { isSuperAdmin: !!user.is_super_admin })
    setRoleModal(null)
  }

  const handlePermsConfirm = async (isStaff, permissions) => {
    const target = permsModal
    const { user } = await api.setUserPermissions(target.id, { is_staff: isStaff, permissions })
    patchUser(target.id, { isStaff: !!user.is_staff, permissions: user.permissions || [] })
    setPermsModal(null)
  }

  const handleCreateSuccess = async () => {
    setCreateModal(false)
    await loadData()
  }

  const handleToggleCompany = async (company) => {
    setBusyId(company.id)
    try {
      if (company.deactivated) await api.reactivateCompany(company.id)
      else await api.deactivateCompany(company.id)
      setCompanies((prev) => prev.map((c) => c.id === company.id ? { ...c, deactivated: !c.deactivated } : c))
    } catch (err) { setError(err.message) }
    finally { setBusyId(null) }
  }

  const handleDeleteCompanyConfirm = async () => {
    const company = deleteCompanyModal
    await api.deleteCompany(company.id)
    setCompanies((prev) => prev.filter((c) => c.id !== company.id))
    setDeleteCompanyModal(null)
  }

  const activeUsers      = users.filter((u) => !u.deactivated)
  const deactivatedUsers = users.filter((u) => u.deactivated)

  return (
    <>
      <div>
        <div className="mb-6 flex items-start justify-between gap-4">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Gestion</h2>
            <p className="text-sm text-gray-500 mt-1">Administration des comptes et des entreprises</p>
          </div>
          {isSuperAdmin && (
            <button onClick={() => setCreateModal(true)}
              className="flex items-center gap-2 bg-purple-600 hover:bg-purple-700 text-white font-semibold px-4 py-2.5 rounded-xl text-sm transition-colors flex-shrink-0">
              <UserPlus size={16} /> Nouveau compte
            </button>
          )}
        </div>

        {loading && <p className="text-gray-400 py-8 text-center">Chargement…</p>}
        {error && <p className="text-red-500 py-4 text-center">{error}</p>}

        {/* Sub-tabs */}
        <div className="flex gap-1 mb-6 bg-gray-100 p-1 rounded-xl w-fit">
          {visibleTabs.users && (
            <button onClick={() => setSubTab('users')}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${subTab === 'users' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}>
              <Users size={15} /> Utilisateurs
              <span className={`px-1.5 py-0.5 rounded-full text-xs font-bold ${subTab === 'users' ? 'bg-primary-light/10 text-primary-light' : 'bg-gray-200 text-gray-500'}`}>
                {users.length}
              </span>
            </button>
          )}
          {visibleTabs.companies && (
            <button onClick={() => setSubTab('companies')}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${subTab === 'companies' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}>
              <Building2 size={15} /> Entreprises
              <span className={`px-1.5 py-0.5 rounded-full text-xs font-bold ${subTab === 'companies' ? 'bg-primary-light/10 text-primary-light' : 'bg-gray-200 text-gray-500'}`}>
                {companies.length}
              </span>
            </button>
          )}
          {visibleTabs.landing && (
            <button onClick={() => setSubTab('landing')}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${subTab === 'landing' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}>
              <Home size={15} /> Page d'accueil
            </button>
          )}
          {visibleTabs.export && (
            <button onClick={() => setSubTab('export')}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${subTab === 'export' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}>
              <FileDown size={15} /> Export agenda
            </button>
          )}
        </div>

        {/* ── Export agenda ── */}
        {subTab === 'export' && <ExportPanel />}

        {/* ── Page d'accueil ── */}
        {subTab === 'landing' && <LandingEditor />}

        {/* ── Utilisateurs ── */}
        {subTab === 'users' && (
          <div className="space-y-6">
            <div>
              <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
                Comptes actifs · {activeUsers.length}
              </h3>
              <div className="space-y-2">
                {activeUsers.map((user) => {
                  const busy = busyId === user.id
                  return (
                    <div key={user.id} className="border rounded-xl px-4 py-3 flex items-center gap-4 shadow-sm bg-white border-gray-100">
                      <img src={user.photo} alt={user.name} className="w-10 h-10 rounded-full object-cover border border-gray-100 flex-shrink-0" />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <p className="text-sm font-semibold text-gray-900">{user.name}</p>
                          <RoleBadge user={user} />
                          {user.isStaff && user.permissions.map((p) => PERMISSION_META[p] && (
                            <span key={p} className="px-1.5 py-0.5 rounded-full text-[10px] font-semibold bg-indigo-50 text-indigo-500">
                              {PERMISSION_META[p].label}
                            </span>
                          ))}
                        </div>
                        <p className="text-xs text-gray-400 truncate">{user.company || '—'}</p>
                      </div>
                      <p className="text-xs text-gray-400 hidden md:block shrink-0">{user.email}</p>

                      <div className="flex items-center gap-2 flex-shrink-0">
                        {isSuperAdmin && (
                          <button onClick={() => setRoleModal(user)}
                            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-primary-light/40 text-primary-light hover:bg-primary-light/5 text-xs font-medium transition-colors">
                            <Shield size={13} /> Rôle
                          </button>
                        )}
                        {isSuperAdmin && !user.isSuperAdmin && (
                          <button onClick={() => setPermsModal(user)}
                            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-indigo-200 text-indigo-600 hover:bg-indigo-50 text-xs font-medium transition-colors">
                            <KeyRound size={13} /> Droits
                          </button>
                        )}
                        {/* Un compte Super Admin ne peut être désactivé/supprimé
                            que par un autre Super Admin. */}
                        {(!user.isSuperAdmin || isSuperAdmin) && (
                          <button onClick={() => handleDeactivate(user)} disabled={busy}
                            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-amber-200 text-amber-600 hover:bg-amber-50 text-xs font-medium transition-colors disabled:opacity-50">
                            {busy ? <Loader2 size={13} className="animate-spin" /> : <UserX size={13} />} Désactiver
                          </button>
                        )}
                        {(!user.isSuperAdmin || isSuperAdmin) && (
                          <button onClick={() => setDeleteModal(user)}
                            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-red-200 text-red-500 hover:bg-red-50 text-xs font-medium transition-colors">
                            <Trash2 size={13} /> Supprimer
                          </button>
                        )}
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>

            {deactivatedUsers.length > 0 && (
              <div>
                <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-3">
                  Comptes désactivés · {deactivatedUsers.length}
                </h3>
                <div className="space-y-2">
                  {deactivatedUsers.map((user) => {
                    const busy = busyId === user.id
                    return (
                      <div key={user.id} className="bg-gray-50 border border-gray-200 rounded-xl px-4 py-3 flex items-center gap-4">
                        <img src={user.photo} alt={user.name} className="w-10 h-10 rounded-full object-cover border border-gray-200 grayscale opacity-60 flex-shrink-0" />
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-semibold text-gray-500">{user.name}</p>
                          <p className="text-xs text-gray-400 truncate">{user.company || '—'}</p>
                        </div>
                        <span className="text-xs font-semibold text-gray-400 bg-gray-200 px-2 py-0.5 rounded-full hidden md:block shrink-0">Désactivé</span>
                        <div className="flex items-center gap-2 flex-shrink-0">
                          <button onClick={() => handleReactivate(user)} disabled={busy}
                            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-green-200 text-green-600 hover:bg-green-50 text-xs font-medium transition-colors disabled:opacity-50">
                            {busy ? <Loader2 size={13} className="animate-spin" /> : <UserCheck size={13} />} Réactiver
                          </button>
                          {(!user.isSuperAdmin || isSuperAdmin) && (
                            <button onClick={() => setDeleteModal(user)}
                              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-red-200 text-red-500 hover:bg-red-50 text-xs font-medium transition-colors">
                              <Trash2 size={13} /> Supprimer
                            </button>
                          )}
                        </div>
                      </div>
                    )
                  })}
                </div>
              </div>
            )}
          </div>
        )}

        {/* ── Entreprises ── */}
        {subTab === 'companies' && (
          <div className="space-y-2">
            {companies.map((company) => {
              const busy = busyId === company.id
              return (
                <div key={company.id}
                  className={`border rounded-xl px-4 py-3 flex items-center gap-4 shadow-sm ${company.deactivated ? 'bg-gray-50 border-gray-200' : 'bg-white border-gray-100'}`}>
                  <div className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 ${company.deactivated ? 'bg-gray-200' : 'bg-primary-light/10'}`}>
                    <Building2 size={18} className={company.deactivated ? 'text-gray-400' : 'text-primary-light'} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <p className={`text-sm font-semibold ${company.deactivated ? 'text-gray-400' : 'text-gray-900'}`}>{company.name}</p>
                      {company.deactivated && (
                        <span className="text-xs font-semibold text-gray-400 bg-gray-200 px-2 py-0.5 rounded-full">Désactivée</span>
                      )}
                    </div>
                    <p className="text-xs text-gray-400">{company.sector}</p>
                  </div>
                  <div className="flex items-center gap-2 flex-shrink-0">
                    <button onClick={() => handleToggleCompany(company)} disabled={busy}
                      className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs font-medium transition-colors disabled:opacity-50 ${
                        company.deactivated
                          ? 'border-green-200 text-green-600 hover:bg-green-50'
                          : 'border-amber-200 text-amber-600 hover:bg-amber-50'
                      }`}>
                      {busy ? <Loader2 size={13} className="animate-spin" />
                        : company.deactivated ? <><UserCheck size={13} /> Réactiver</> : <><UserX size={13} /> Désactiver</>}
                    </button>
                    <button onClick={() => setDeleteCompanyModal(company)}
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-red-200 text-red-500 hover:bg-red-50 text-xs font-medium transition-colors">
                      <Trash2 size={13} /> Supprimer
                    </button>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>

      {deleteModal && (
        <DeleteUserModal
          user={deleteModal}
          onClose={() => setDeleteModal(null)}
          onConfirm={handleDeleteConfirm}
        />
      )}

      {roleModal && (
        <RoleModal
          target={roleModal}
          isLastSuperAdmin={roleModal.isSuperAdmin && activeSuperAdmins.length <= 1}
          onClose={() => setRoleModal(null)}
          onConfirm={handleRoleConfirm}
        />
      )}

      {reassignModal && (
        <ReassignAdminModal
          target={reassignModal}
          onClose={() => setReassignModal(null)}
          onConfirm={handleReassignConfirm}
        />
      )}

      {deleteCompanyModal && (
        <DeleteCompanyModal
          company={deleteCompanyModal}
          onClose={() => setDeleteCompanyModal(null)}
          onConfirm={handleDeleteCompanyConfirm}
        />
      )}

      {permsModal && (
        <PermissionsModal
          target={permsModal}
          onClose={() => setPermsModal(null)}
          onConfirm={handlePermsConfirm}
        />
      )}

      {createModal && (
        <StaffAccountModal
          onClose={() => setCreateModal(false)}
          onSuccess={handleCreateSuccess}
        />
      )}
    </>
  )
}
