import React, { useState, useEffect, useMemo } from 'react'
import { Search, ExternalLink, Bookmark, Newspaper, Tag, X, RefreshCw } from 'lucide-react'
import { api } from '../../lib/api'
import { useAuth } from '../../context/AuthContext'

const categoryColors = {
  'réglementation': 'bg-purple-100 text-purple-700',
  'vie-entreprises': 'bg-green-100 text-green-700',
  'opportunités': 'bg-orange-100 text-orange-700',
  'territoire': 'bg-blue-100 text-blue-700',
  'actualités': 'bg-indigo-100 text-indigo-700',
}

function formatDate(value) {
  if (!value) return ''
  return new Date(value).toLocaleDateString('fr-FR', { day: 'numeric', month: 'long', year: 'numeric' })
}

// Backend news : {id, title, source, summary, url, category, published_at}.
function mapNews(n) {
  return {
    id: n.id,
    title: n.title,
    source: n.source || '',
    date: formatDate(n.published_at || n.created_at),
    category: n.category || '',
    excerpt: n.summary || '',
    url: n.url || '',
  }
}

export default function News() {
  const { isAdmin } = useAuth()
  const [newsItems, setNewsItems] = useState([])
  const [saved, setSaved] = useState([])          // bookmarks persistés (backend)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [syncing, setSyncing] = useState(false)
  const [activeFilter, setActiveFilter] = useState('Tout')
  const [searchQuery, setSearchQuery] = useState('')

  const loadNews = async () => {
    const res = await api.getNews()
    const items = res?.items || res?.news || (Array.isArray(res) ? res : [])
    setNewsItems(items.map(mapNews))
  }

  const loadSaved = async () => {
    const res = await api.getSavedNews()
    setSaved(res?.items || [])
  }

  useEffect(() => {
    let cancelled = false
    Promise.all([loadNews(), loadSaved()])
      .catch((err) => { if (!cancelled) setError(err.message) })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [])

  // Synchronisation manuelle des flux RSS (super admin).
  const handleSync = async () => {
    setSyncing(true)
    setError('')
    try {
      await api.syncNews()
      await loadNews()
    } catch (err) {
      setError(err.message || 'Échec de la synchronisation')
    } finally {
      setSyncing(false)
    }
  }

  // news_id de l'article → entrée sauvegardée (pour le toggle dans le flux).
  const savedByNewsId = useMemo(() => {
    const m = new Map()
    saved.forEach((s) => { if (s.news_id) m.set(s.news_id, s) })
    return m
  }, [saved])

  const saveArticle = async (item) => {
    try {
      const res = await api.saveNews({ news_id: item.id })
      if (res?.saved) setSaved((prev) => [res.saved, ...prev])
    } catch (err) {
      setError(err.message || 'Échec de la sauvegarde')
    }
  }

  const unsaveArticle = async (savedId) => {
    try {
      await api.unsaveNews(savedId)
      setSaved((prev) => prev.filter((s) => s.id !== savedId))
    } catch (err) {
      setError(err.message || 'Échec du retrait')
    }
  }

  // Catégories réellement présentes (corrige l'ancien filtre figé qui ne matchait rien).
  const filters = useMemo(
    () => ['Tout', ...new Set(newsItems.map((n) => n.category).filter(Boolean))],
    [newsItems],
  )

  const filtered = newsItems.filter((item) => {
    const matchesFilter = activeFilter === 'Tout' || item.category === activeFilter
    const q = searchQuery.toLowerCase()
    const matchesSearch =
      item.title.toLowerCase().includes(q) ||
      item.source.toLowerCase().includes(q) ||
      item.excerpt.toLowerCase().includes(q)
    return matchesFilter && matchesSearch
  })

  const uniqueSources = [...new Set(newsItems.map((a) => a.source).filter(Boolean))].length

  return (
    <div>
      <div className="mb-6 flex items-start justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Veille Économique</h2>
          <p className="text-sm text-gray-500 mt-1">Actualités du mois — vos articles sauvegardés restent accessibles</p>
        </div>
        {isAdmin && (
          <button onClick={handleSync} disabled={syncing}
            className="flex items-center gap-2 btn-primary text-sm disabled:opacity-60">
            <RefreshCw size={16} className={syncing ? 'animate-spin' : ''} />
            {syncing ? 'Synchronisation…' : 'Synchroniser'}
          </button>
        )}
      </div>

      {loading && <p className="text-gray-400 py-6 text-center">Chargement des actualités…</p>}
      {error && <p className="text-red-500 py-6 text-center">{error}</p>}

      {/* Search */}
      <div className="relative mb-5">
        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
        <input
          type="text"
          placeholder="Rechercher des actus..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full pl-10 pr-4 py-3 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-light bg-white"
        />
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="bg-primary-light rounded-xl p-4 text-white flex items-center gap-3">
          <Newspaper size={28} className="opacity-80" />
          <div>
            <p className="text-2xl font-bold leading-none">{newsItems.length}</p>
            <p className="text-xs opacity-80 mt-1">Articles du mois</p>
          </div>
        </div>
        <div className="bg-amber-500 rounded-xl p-4 text-white flex items-center gap-3">
          <Bookmark size={28} className="opacity-80" fill="currentColor" />
          <div>
            <p className="text-2xl font-bold leading-none">{saved.length}</p>
            <p className="text-xs opacity-80 mt-1">Articles sauvegardés</p>
          </div>
        </div>
        <div className="bg-indigo-500 rounded-xl p-4 text-white flex items-center gap-3">
          <Tag size={28} className="opacity-80" />
          <div>
            <p className="text-2xl font-bold leading-none">{uniqueSources}</p>
            <p className="text-xs opacity-80 mt-1">Sources couvertes</p>
          </div>
        </div>
      </div>

      {/* Saved articles — persistent, restent visibles après la purge mensuelle */}
      {saved.length > 0 && (
        <div className="mb-6 bg-amber-50 border border-amber-200 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-3">
            <Bookmark size={16} className="text-amber-600" fill="currentColor" />
            <h3 className="text-sm font-semibold text-amber-800">
              Articles sauvegardés ({saved.length})
            </h3>
          </div>
          <div className="space-y-2">
            {saved.map((item) => (
              <div
                key={item.id}
                className="flex items-center justify-between gap-3 bg-white rounded-lg px-3 py-2 shadow-sm border border-amber-100"
              >
                <div className="min-w-0">
                  <p className="text-sm font-medium text-gray-800 truncate">{item.title}</p>
                  <p className="text-xs text-gray-400">
                    {[item.source, formatDate(item.saved_at)].filter(Boolean).join(' · ')}
                  </p>
                </div>
                <div className="flex items-center gap-1 flex-shrink-0">
                  {item.url && (
                    <a
                      href={item.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="p-1.5 rounded hover:bg-amber-100 text-amber-600 transition-colors"
                      title="Revoir l'article"
                    >
                      <ExternalLink size={14} />
                    </a>
                  )}
                  <button
                    onClick={() => unsaveArticle(item.id)}
                    className="p-1.5 rounded hover:bg-amber-100 text-amber-500 transition-colors"
                    title="Retirer"
                  >
                    <X size={14} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Filter tabs */}
      <div className="flex gap-2 mb-6 flex-wrap">
        {filters.map((f) => (
          <button
            key={f}
            onClick={() => setActiveFilter(f)}
            className={`px-4 py-1.5 rounded-full text-sm font-medium transition-colors ${
              activeFilter === f
                ? 'bg-primary-light text-white'
                : 'bg-white border border-gray-200 text-gray-600 hover:border-primary-light hover:text-primary-light'
            }`}
          >
            {f === 'Tout' ? f : f.charAt(0).toUpperCase() + f.slice(1)}
          </button>
        ))}
      </div>

      {/* News items */}
      <div className="space-y-4">
        {filtered.map((item) => {
          const savedEntry = savedByNewsId.get(item.id)
          return (
          <div
            key={item.id}
            className="bg-white rounded-xl shadow-sm border border-gray-100 p-5 hover:shadow-md transition-shadow"
          >
            <div className="flex items-start justify-between gap-3 mb-2">
              <div className="flex items-center gap-2 flex-wrap">
                {item.category && (
                  <span
                    className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                      categoryColors[item.category] || 'bg-gray-100 text-gray-700'
                    }`}
                  >
                    {item.category}
                  </span>
                )}
                <span className="text-xs text-gray-400">{[item.source, item.date].filter(Boolean).join(' · ')}</span>
              </div>
            </div>

            <h3 className="font-bold text-gray-900 mb-2">{item.title}</h3>
            <p className="text-sm text-gray-600 mb-4">{item.excerpt}</p>

            <div className="flex gap-3">
              <a
                href={item.url || '#'}
                target={item.url ? '_blank' : undefined}
                rel="noopener noreferrer"
                className={`flex items-center gap-1.5 px-4 py-2 bg-primary-light hover:bg-primary text-white text-sm font-medium rounded-lg transition-colors ${item.url ? '' : 'opacity-50 pointer-events-none'}`}
              >
                <ExternalLink size={14} />
                Lire l'article
              </a>
              <button
                onClick={() => (savedEntry ? unsaveArticle(savedEntry.id) : saveArticle(item))}
                className={`flex items-center gap-1.5 px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                  savedEntry
                    ? 'bg-amber-50 border border-amber-300 text-amber-600 hover:bg-amber-100'
                    : 'border border-gray-200 hover:border-gray-300 text-gray-600'
                }`}
              >
                <Bookmark size={14} fill={savedEntry ? 'currentColor' : 'none'} />
                {savedEntry ? 'Sauvegardé' : 'Sauvegarder'}
              </button>
            </div>
          </div>
          )
        })}

        {!loading && filtered.length === 0 && (
          <div className="text-center py-12">
            <p className="text-gray-400">Aucun article ne correspond à votre recherche</p>
          </div>
        )}
      </div>
    </div>
  )
}
