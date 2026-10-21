/** Administration du contenu éditorial (page d'accueil, annonces). */

import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'

import { Button, Card, Input, Textarea, useToast } from '../../components/ui'
import { api } from '../../lib/api'
import { useLanding } from '../landing/useLanding'

/** Éditeur du contenu de la page d'accueil. */
function LandingEditor() {
  const { content } = useLanding()
  const toast = useToast()
  const queryClient = useQueryClient()
  const [draft, setDraft] = useState(content)
  const save = useMutation({
    mutationFn: () => api.put('/content/landing', { value: draft }),
    onSuccess: () => {
      toast.success("Page d'accueil mise à jour.")
      queryClient.invalidateQueries({ queryKey: ['content', 'landing'] })
    },
    onError: () => toast.error('Enregistrement impossible.'),
  })
  const setSection = (index, field, value) =>
    setDraft((d) => ({
      ...d,
      sections: d.sections.map((s, i) => (i === index ? { ...s, [field]: value } : s)),
    }))

  return (
    <Card>
      <h2 className="mb-4 text-lg font-semibold">Page d'accueil</h2>
      <form
        onSubmit={(e) => {
          e.preventDefault()
          save.mutate()
        }}
        className="grid gap-4"
      >
        <Input
          label="Slogan"
          value={draft.slogan}
          onChange={(e) => setDraft({ ...draft, slogan: e.target.value })}
        />
        <Textarea
          label="Sous-titre"
          rows={2}
          value={draft.subtitle}
          onChange={(e) => setDraft({ ...draft, subtitle: e.target.value })}
        />
        {draft.sections.map((section, index) => (
          <fieldset
            key={index}
            className="grid gap-3 rounded-lg border border-slate-200 p-4 dark:border-slate-700"
          >
            <legend className="px-2 text-sm font-semibold">Carte {index + 1}</legend>
            <Input
              label="Titre"
              value={section.title}
              onChange={(e) => setSection(index, 'title', e.target.value)}
            />
            <Input
              label="Durée"
              value={section.duration}
              onChange={(e) => setSection(index, 'duration', e.target.value)}
            />
            <Textarea
              label="Description"
              rows={3}
              value={section.description}
              onChange={(e) => setSection(index, 'description', e.target.value)}
            />
            <Input
              label="Mise en avant"
              value={section.highlight}
              onChange={(e) => setSection(index, 'highlight', e.target.value)}
            />
          </fieldset>
        ))}
        <div>
          <Button type="submit" loading={save.isPending}>
            Enregistrer
          </Button>
        </div>
      </form>
    </Card>
  )
}

/** Édition de l'annonce affichée aux membres. */
function Announcement() {
  const toast = useToast()
  const [content, setContent] = useState('')
  const send = useMutation({
    mutationFn: () => api.post('/notifications/broadcast', { content: content.trim() }),
    onSuccess: () => {
      toast.success('Annonce envoyée à tous les membres.')
      setContent('')
    },
    onError: () => toast.error('Envoi impossible.'),
  })
  return (
    <Card>
      <h2 className="mb-4 text-lg font-semibold">Annonce à tous les membres</h2>
      <form
        onSubmit={(e) => {
          e.preventDefault()
          send.mutate()
        }}
        className="grid gap-4"
      >
        <Textarea
          label="Message"
          rows={3}
          maxLength={1000}
          value={content}
          onChange={(e) => setContent(e.target.value)}
          hint="Apparaît dans la cloche de notifications de chaque membre."
        />
        <div>
          <Button type="submit" loading={send.isPending} disabled={!content.trim()}>
            Envoyer l'annonce
          </Button>
        </div>
      </form>
    </Card>
  )
}

/** Contenu éditorial : page d'accueil et annonces. */
export default function ContentAdmin() {
  const { isLoading } = useLanding()
  // `key` : l'éditeur est initialisé avec le contenu chargé (ou le contenu par défaut en repli).
  return (
    <div className="space-y-6">
      <LandingEditor key={String(isLoading)} />
      <Announcement />
    </div>
  )
}
