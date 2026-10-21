import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'

import { Button, Input, Modal, Textarea, useToast } from '../../components/ui'
import { api } from '../../lib/api'

/** Publication manuelle d'un article (réservé à `manage_news`). */
export default function ArticleForm({ onClose }) {
  const toast = useToast()
  const queryClient = useQueryClient()
  const [values, setValues] = useState({
    title: '',
    source: '',
    url: '',
    category: '',
    summary: '',
  })
  const create = useMutation({
    mutationFn: () =>
      api.post('/news', {
        title: values.title.trim(),
        source: values.source.trim() || null,
        url: values.url.trim() || null,
        category: values.category.trim() || null,
        summary: values.summary.trim() || null,
        published_at: new Date().toISOString(),
      }),
    onSuccess: () => {
      toast.success('Article publié.')
      queryClient.invalidateQueries({ queryKey: ['news'] })
      onClose()
    },
    onError: (err) =>
      toast.error(
        err.status === 409 ? 'Un article avec cette URL existe déjà.' : 'Publication impossible.',
      ),
  })
  const bind = (name) => ({
    value: values[name],
    onChange: (e) => setValues((v) => ({ ...v, [name]: e.target.value })),
  })

  return (
    <Modal open onClose={onClose} title="Publier un article">
      <form
        onSubmit={(e) => {
          e.preventDefault()
          create.mutate()
        }}
        className="grid gap-4"
      >
        <Input label="Titre" required maxLength={500} {...bind('title')} />
        <div className="grid gap-4 sm:grid-cols-2">
          <Input label="Source" {...bind('source')} />
          <Input label="Catégorie" {...bind('category')} />
        </div>
        <Input label="Lien" type="url" placeholder="https://" {...bind('url')} />
        <Textarea label="Résumé" {...bind('summary')} />
        <div className="flex justify-end gap-2">
          <Button variant="secondary" onClick={onClose}>
            Annuler
          </Button>
          <Button type="submit" loading={create.isPending}>
            Publier
          </Button>
        </div>
      </form>
    </Modal>
  )
}
