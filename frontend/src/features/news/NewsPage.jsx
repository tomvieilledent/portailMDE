/** Page de la veille économique (actualités). */

import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Bookmark, ExternalLink, Newspaper, Plus, RefreshCw, Search, Trash2 } from 'lucide-react'
import { useMemo, useState } from 'react'

import { useAuth } from '../../auth/AuthProvider'
import { PERMISSIONS, hasPermission } from '../../auth/permissions'
import PageHeader from '../../components/layout/PageHeader'
import {
  Badge,
  Button,
  Card,
  EmptyState,
  Input,
  Modal,
  Pagination,
  Spinner,
  useToast,
} from '../../components/ui'
import { api } from '../../lib/api'
import { cn } from '../../lib/cn'
import { safeHref } from '../../lib/safeUrl'
import { useDebounce } from '../../lib/useDebounce'
import ArticleForm from './ArticleForm'
import { NEWS_PAGE, formatPublished, useNews, useSavedNews } from './queries'

/** Carte d'une actualité : favori et suppression. */
function ArticleCard({ article, saved, onToggleSave, onDelete }) {
  const [reading, setReading] = useState(false)
  const href = safeHref(article.url)

  return (
    <Card className="flex h-64 flex-col gap-2 overflow-hidden">
      <div className="flex items-start justify-between gap-3">
        <h2 className="line-clamp-2 font-semibold">{article.title}</h2>
        <div className="flex shrink-0 gap-1">
          <button
            type="button"
            aria-pressed={saved}
            aria-label={saved ? 'Retirer des favoris' : 'Enregistrer'}
            onClick={onToggleSave}
            className="rounded-full p-1.5 hover:bg-slate-100 dark:hover:bg-slate-800"
          >
            <Bookmark
              size={18}
              className={cn(saved ? 'fill-brand-600 text-brand-600' : 'text-slate-500')}
              aria-hidden="true"
            />
          </button>
          {onDelete && (
            <button
              type="button"
              aria-label="Supprimer l'article"
              onClick={onDelete}
              className="rounded-full p-1.5 text-slate-500 hover:bg-slate-100 hover:text-red-600 dark:hover:bg-slate-800"
            >
              <Trash2 size={18} aria-hidden="true" />
            </button>
          )}
        </div>
      </div>
      <div className="flex flex-wrap items-center gap-2 text-xs text-slate-500">
        {article.category && <Badge tone="brand">{article.category}</Badge>}
        {article.source && <span>{article.source}</span>}
        {article.published_at && <time>{formatPublished(article.published_at)}</time>}
      </div>
      <p className="line-clamp-4 min-h-0 flex-1 overflow-hidden text-sm text-slate-600 dark:text-slate-400">
        {article.summary}
      </p>
      <div className="mt-auto shrink-0">
        {href ? (
          <a
            href={href}
            target="_blank"
            rel="noopener noreferrer"
            className="bg-brand-600 hover:bg-brand-700 inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-semibold text-white"
          >
            Lire l'article <ExternalLink size={14} aria-hidden="true" />
          </a>
        ) : (
          <Button size="sm" onClick={() => setReading(true)}>
            Lire l'article
          </Button>
        )}
      </div>
      {reading && (
        <Modal open onClose={() => setReading(false)} title={article.title}>
          <p className="mb-3 text-xs text-slate-500">
            {[article.source, article.published_at && formatPublished(article.published_at)]
              .filter(Boolean)
              .join(' · ')}
          </p>
          <p className="text-sm whitespace-pre-line">{article.summary}</p>
        </Modal>
      )}
    </Card>
  )
}

/** Veille économique : articles des flux RSS et publications du staff, avec favoris. */
export default function NewsPage() {
  const { user } = useAuth()
  const toast = useToast()
  const queryClient = useQueryClient()
  const canManage = hasPermission(user, PERMISSIONS.MANAGE_NEWS)
  const [tab, setTab] = useState('all')
  const [search, setSearch] = useState('')
  const [offset, setOffset] = useState(0)
  const [publishing, setPublishing] = useState(false)
  const debounced = useDebounce(search)
  // Base vide : le serveur lance seul la synchronisation, on réinterroge quelques fois.
  const news = useNews(
    { search: debounced, offset },
    {
      refetchInterval: (query) =>
        query.state.data?.total === 0 && query.state.dataUpdateCount < 12 ? 5000 : false,
    },
  )
  // « Nouvelles infos du jour » : articles des dernières 24 h.
  const since = useMemo(() => new Date(Date.now() - 24 * 3600 * 1000).toISOString(), [])
  const today = useNews({ since, limit: 4 })
  const syncing = news.data?.total === 0 && !debounced && offset === 0
  const saved = useSavedNews()
  const savedByArticle = new Map(
    (saved.data ?? []).filter((s) => s.article_id).map((s) => [s.article_id, s]),
  )
  const refresh = () => queryClient.invalidateQueries({ queryKey: ['news'] })

  const toggleSave = useMutation({
    mutationFn: (article) => {
      const existing = savedByArticle.get(article.id)
      return existing
        ? api.delete(`/news/saved/${existing.id}`)
        : api.put(`/news/${article.id}/save`)
    },
    onSuccess: refresh,
    onError: () => toast.error('Action impossible.'),
  })
  const unsave = useMutation({
    mutationFn: (item) => api.delete(`/news/saved/${item.id}`),
    onSuccess: refresh,
    onError: () => toast.error('Action impossible.'),
  })
  const remove = useMutation({
    mutationFn: (article) => api.delete(`/news/${article.id}`),
    onSuccess: () => {
      toast.success('Article supprimé.')
      refresh()
    },
    onError: () => toast.error('Suppression impossible.'),
  })
  const sync = useMutation({
    mutationFn: () => api.post('/news/sync'),
    onSuccess: ({ created }) => {
      toast.success(created ? `${created} nouvel(s) article(s).` : 'Déjà à jour.')
      refresh()
    },
    onError: () => toast.error('Synchronisation impossible.'),
  })

  return (
    <>
      <PageHeader
        title="Actualités"
        description="La veille économique et réglementaire pour les entreprises."
        actions={
          canManage && (
            <div className="flex gap-2">
              <Button variant="secondary" loading={sync.isPending} onClick={() => sync.mutate()}>
                <RefreshCw size={16} aria-hidden="true" /> Synchroniser
              </Button>
              <Button onClick={() => setPublishing(true)}>
                <Plus size={16} aria-hidden="true" /> Publier
              </Button>
            </div>
          )
        }
      />
      <div
        role="tablist"
        className="mb-6 flex gap-2 border-b border-slate-200 dark:border-slate-800"
      >
        {[
          ['all', 'Toutes'],
          ['saved', `Favoris${saved.data?.length ? ` (${saved.data.length})` : ''}`],
        ].map(([id, label]) => (
          <button
            key={id}
            role="tab"
            type="button"
            aria-selected={tab === id}
            onClick={() => setTab(id)}
            className={cn(
              '-mb-px border-b-2 px-4 py-2 text-sm font-medium',
              tab === id
                ? 'border-brand-700 text-brand-700 dark:border-brand-300 dark:text-brand-300'
                : 'border-transparent text-slate-500 hover:text-slate-700',
            )}
          >
            {label}
          </button>
        ))}
      </div>

      {tab === 'all' && (
        <>
          {today.data?.items.length > 0 && (
            <section aria-labelledby="news-today" className="mb-10">
              <p className="text-xs font-semibold tracking-[0.2em] text-slate-500 uppercase">
                À la une
              </p>
              <h2 id="news-today" className="mb-4 text-2xl tracking-tight">
                <span className="font-light">Nouvelles infos </span>
                <span className="font-bold">du jour</span>
              </h2>
              <ul className="grid gap-4 md:grid-cols-2">
                {today.data.items.map((article) => (
                  <li key={article.id}>
                    <ArticleCard
                      article={article}
                      saved={savedByArticle.has(article.id)}
                      onToggleSave={() => toggleSave.mutate(article)}
                      onDelete={canManage ? () => remove.mutate(article) : undefined}
                    />
                  </li>
                ))}
              </ul>
            </section>
          )}
          <div className="relative mb-6 max-w-md">
            <Search
              size={16}
              className="pointer-events-none absolute top-9 left-3 text-slate-400"
              aria-hidden="true"
            />
            <Input
              label="Rechercher"
              type="search"
              className="pl-9"
              value={search}
              onChange={(e) => {
                setSearch(e.target.value)
                setOffset(0)
              }}
            />
          </div>
          {news.isLoading && <Spinner />}
          {news.isError && <p role="alert">Impossible de charger les actualités.</p>}
          {syncing && (
            <div className="mb-4 flex items-center gap-3 text-sm text-slate-600">
              <Spinner /> Synchronisation des actualités en cours…
            </div>
          )}
          {news.data?.items.length === 0 && !syncing && (
            <EmptyState icon={Newspaper} title="Aucun article" />
          )}
          <ul className="grid gap-4 md:grid-cols-2">
            {news.data?.items.map((article) => (
              <li key={article.id}>
                <ArticleCard
                  article={article}
                  saved={savedByArticle.has(article.id)}
                  onToggleSave={() => toggleSave.mutate(article)}
                  onDelete={canManage ? () => remove.mutate(article) : undefined}
                />
              </li>
            ))}
          </ul>
          {news.data && (
            <Pagination
              total={news.data.total}
              limit={NEWS_PAGE}
              offset={offset}
              onChange={setOffset}
            />
          )}
        </>
      )}

      {tab === 'saved' && (
        <>
          {saved.data?.length === 0 && (
            <EmptyState
              icon={Bookmark}
              title="Aucun favori"
              description="Enregistrez des articles pour les retrouver ici."
            />
          )}
          <ul className="grid gap-4 md:grid-cols-2">
            {saved.data?.map((item) => (
              <li key={item.id}>
                <ArticleCard article={item} saved onToggleSave={() => unsave.mutate(item)} />
              </li>
            ))}
          </ul>
        </>
      )}
      {publishing && <ArticleForm onClose={() => setPublishing(false)} />}
    </>
  )
}
