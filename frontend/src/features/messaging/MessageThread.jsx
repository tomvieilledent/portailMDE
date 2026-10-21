/** Fil de discussion d'une conversation et saisie des messages. */

import { useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, Paperclip, Send, Settings, Trash2 } from 'lucide-react'
import { useEffect, useMemo, useRef, useState } from 'react'
import { Link } from 'react-router-dom'

import { Avatar, Button, Spinner, uploadUrl, useToast } from '../../components/ui'
import { cn } from '../../lib/cn'
import { api } from '../../lib/api'
import { downloadFile } from '../../lib/download'
import { useRealtime } from '../../realtime/useRealtime'
import GroupSettingsModal from './GroupSettingsModal'
import { conversationTitle, formatTime } from './helpers'
import { useMessages } from './queries'

/** Bulle d'un message, avec pièce jointe et suppression. */
function Bubble({ message, mine, onDelete }) {
  const toast = useToast()
  return (
    <li className={cn('flex gap-2', mine && 'flex-row-reverse')}>
      {!mine && (
        <Avatar
          src={uploadUrl(message.author?.avatar_path)}
          firstName={message.author?.first_name}
          lastName={message.author?.last_name}
          size="sm"
        />
      )}
      <div
        className={cn(
          'group max-w-[75%] rounded-2xl px-4 py-2 text-sm',
          mine
            ? 'bg-brand-700 text-white'
            : 'bg-white shadow-sm dark:bg-slate-800 dark:text-slate-100',
        )}
      >
        {!mine && message.author && (
          <p className="text-brand-700 dark:text-brand-300 mb-0.5 text-xs font-semibold">
            {message.author.first_name} {message.author.last_name}
          </p>
        )}
        {message.content && <p className="break-words whitespace-pre-wrap">{message.content}</p>}
        {message.file_url && (
          <a
            href={message.file_url}
            onClick={(event) => {
              // Le fichier exige l'en-tête Authorization : téléchargement via fetch.
              event.preventDefault()
              downloadFile(message.file_url, message.file_name).catch(() =>
                toast.error('Téléchargement impossible.'),
              )
            }}
            className="mt-1 inline-flex items-center gap-1 underline"
          >
            <Paperclip size={14} aria-hidden="true" /> {message.file_name}
          </a>
        )}
        <div className="mt-1 flex items-center justify-end gap-2 text-[11px] opacity-70">
          <time>{formatTime(message.created_at)}</time>
          {mine && (
            <button
              type="button"
              onClick={() => onDelete(message)}
              aria-label="Supprimer le message"
              className="opacity-0 transition group-hover:opacity-100 focus:opacity-100"
            >
              <Trash2 size={12} />
            </button>
          )}
        </div>
      </div>
    </li>
  )
}

/** Fil de discussion : historique paginé, envoi de messages et de fichiers. */
export default function MessageThread({ conversation, meId }) {
  const queryClient = useQueryClient()
  const toast = useToast()
  const [text, setText] = useState('')
  const [file, setFile] = useState(null)
  const [settings, setSettings] = useState(false)
  const bottomRef = useRef(null)
  const fileInput = useRef(null)
  const { data, hasNextPage, fetchNextPage, isFetchingNextPage, isLoading } = useMessages(
    conversation.id,
  )

  // Les pages arrivent du plus récent au plus ancien : on remet l'ordre chronologique.
  const messages = useMemo(() => (data ? data.pages.flat().reverse() : []), [data])
  const lastId = messages[messages.length - 1]?.id

  const markRead = useMutation({
    mutationFn: () => api.post(`/conversations/${conversation.id}/read`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['conversations'] }),
  })
  const { mutate: markAsRead } = markRead

  useEffect(() => {
    bottomRef.current?.scrollIntoView?.({ block: 'end' })
    if (lastId) markAsRead()
  }, [lastId, markAsRead])

  useRealtime('message.new', (event) => {
    if (event.conversation_id !== conversation.id) return
    queryClient.setQueryData(['messages', conversation.id], (old) => {
      if (!old || old.pages.flat().some((m) => m.id === event.message.id)) return old
      return { ...old, pages: [[event.message, ...old.pages[0]], ...old.pages.slice(1)] }
    })
  })
  useRealtime('message.deleted', (event) => {
    if (event.conversation_id !== conversation.id) return
    queryClient.setQueryData(
      ['messages', conversation.id],
      (old) =>
        old && {
          ...old,
          pages: old.pages.map((page) => page.filter((m) => m.id !== event.message_id)),
        },
    )
  })

  const send = useMutation({
    mutationFn: () => {
      const form = new FormData()
      form.append('content', text)
      if (file) form.append('file', file)
      return api.post(`/conversations/${conversation.id}/messages`, form)
    },
    onSuccess: (message) => {
      setText('')
      setFile(null)
      queryClient.setQueryData(['messages', conversation.id], (old) => {
        if (!old || old.pages.flat().some((m) => m.id === message.id)) return old
        return { ...old, pages: [[message, ...old.pages[0]], ...old.pages.slice(1)] }
      })
      queryClient.invalidateQueries({ queryKey: ['conversations'] })
    },
    onError: (err) => toast.error(err.message || 'Envoi impossible.'),
  })

  const remove = useMutation({
    mutationFn: (message) => api.delete(`/messages/${message.id}`),
    onSuccess: (_, message) => {
      queryClient.setQueryData(
        ['messages', conversation.id],
        (old) =>
          old && { ...old, pages: old.pages.map((p) => p.filter((m) => m.id !== message.id)) },
      )
      queryClient.invalidateQueries({ queryKey: ['conversations'] })
    },
    onError: () => toast.error('Suppression impossible.'),
  })

  function onSubmit(event) {
    event.preventDefault()
    if ((text.trim() || file) && !send.isPending) send.mutate()
  }

  return (
    <div className="flex h-full flex-col">
      <header className="flex items-center gap-3 border-b border-slate-200 p-4 dark:border-slate-800">
        <Link to="/messagerie" aria-label="Retour aux conversations" className="lg:hidden">
          <ArrowLeft size={20} />
        </Link>
        <h2 className="flex-1 truncate text-lg font-semibold">
          {conversationTitle(conversation, meId)}
        </h2>
        {conversation.kind === 'group' && (
          <button
            type="button"
            onClick={() => setSettings(true)}
            aria-label="Paramètres du groupe"
            className="rounded-lg p-2 hover:bg-slate-100 dark:hover:bg-slate-800"
          >
            <Settings size={18} />
          </button>
        )}
      </header>

      <div className="flex-1 overflow-y-auto bg-slate-100/60 p-4 dark:bg-slate-950/40">
        {isLoading && <Spinner />}
        {hasNextPage && (
          <div className="mb-4 text-center">
            <Button
              size="sm"
              variant="secondary"
              loading={isFetchingNextPage}
              onClick={() => fetchNextPage()}
            >
              Messages précédents
            </Button>
          </div>
        )}
        <ul className="space-y-3">
          {messages.map((message) => (
            <Bubble
              key={message.id}
              message={message}
              mine={message.author_id === meId}
              onDelete={remove.mutate}
            />
          ))}
        </ul>
        <div ref={bottomRef} />
      </div>

      <form
        onSubmit={onSubmit}
        className="flex items-end gap-2 border-t border-slate-200 p-3 dark:border-slate-800"
      >
        <input
          ref={fileInput}
          type="file"
          className="hidden"
          aria-label="Pièce jointe"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
        />
        <Button
          variant="ghost"
          aria-label="Joindre un fichier"
          onClick={() => fileInput.current?.click()}
        >
          <Paperclip size={18} />
        </Button>
        <div className="min-w-0 flex-1">
          {file && (
            <p className="mb-1 truncate text-xs text-slate-500">
              📎 {file.name}{' '}
              <button type="button" className="underline" onClick={() => setFile(null)}>
                retirer
              </button>
            </p>
          )}
          <textarea
            aria-label="Votre message"
            rows={1}
            value={text}
            maxLength={5000}
            placeholder="Écrire un message…"
            onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                onSubmit(e)
              }
            }}
            className="focus:ring-brand-500 block max-h-32 w-full resize-none rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm focus:ring-2 focus:outline-none dark:border-slate-700 dark:bg-slate-900"
          />
        </div>
        <Button type="submit" aria-label="Envoyer" loading={send.isPending}>
          <Send size={18} />
        </Button>
      </form>
      {settings && (
        <GroupSettingsModal
          conversation={conversation}
          meId={meId}
          onClose={() => setSettings(false)}
        />
      )}
    </div>
  )
}
