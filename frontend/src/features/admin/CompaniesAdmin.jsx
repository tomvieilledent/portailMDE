/** Administration des entreprises. */

import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Plus, Search } from 'lucide-react'
import { useState } from 'react'

import {
  Badge,
  Button,
  Input,
  Modal,
  Pagination,
  Select,
  Spinner,
  Textarea,
  useToast,
} from '../../components/ui'
import { api } from '../../lib/api'
import { useDebounce } from '../../lib/useDebounce'
import { COMPANY_KINDS } from '../directory/labels'
import UserPicker from '../messaging/UserPicker'

const PAGE = 25

/** Création ou modification d'une entreprise. */
function CompanyFormModal({ company, onClose }) {
  const toast = useToast()
  const queryClient = useQueryClient()
  const [values, setValues] = useState({
    name: company?.name ?? '',
    description: company?.description ?? '',
    location: company?.location ?? '',
    website_url: company?.website_url ?? '',
    kind: company?.kind ?? 'company',
  })
  const [owner, setOwner] = useState([]) // propriétaire (création uniquement)
  const save = useMutation({
    mutationFn: () => {
      const body = {
        name: values.name.trim(),
        description: values.description.trim() || null,
        location: values.location.trim() || null,
        website_url: values.website_url.trim() || null,
        kind: values.kind,
      }
      return company
        ? api.patch(`/companies/${company.id}`, body)
        : api.post('/companies', { ...body, owner_id: owner[0] })
    },
    onSuccess: () => {
      toast.success(company ? 'Entreprise modifiée.' : 'Entreprise créée.')
      queryClient.invalidateQueries({ queryKey: ['admin', 'companies'] })
      onClose()
    },
    onError: () => toast.error('Enregistrement impossible.'),
  })
  const bind = (name) => ({
    value: values[name],
    onChange: (e) => setValues((v) => ({ ...v, [name]: e.target.value })),
  })

  return (
    <Modal open onClose={onClose} title={company ? "Modifier l'entreprise" : 'Nouvelle entreprise'}>
      <form
        onSubmit={(e) => {
          e.preventDefault()
          save.mutate()
        }}
        className="grid gap-4"
      >
        <Input label="Nom" required maxLength={200} {...bind('name')} />
        <Select label="Type" {...bind('kind')}>
          {Object.entries(COMPANY_KINDS).map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </Select>
        <Textarea label="Description" {...bind('description')} />
        <div className="grid gap-4 sm:grid-cols-2">
          <Input label="Localisation" {...bind('location')} />
          <Input label="Site web" type="url" placeholder="https://" {...bind('website_url')} />
        </div>
        {!company && (
          <fieldset className="space-y-2">
            <legend className="text-sm font-medium">Propriétaire de l'entreprise</legend>
            <p className="text-xs text-slate-500">
              Choisissez un compte existant : il devient administrateur de cette entreprise.
            </p>
            <UserPicker selected={owner} onChange={setOwner} single />
          </fieldset>
        )}
        <div className="flex justify-end gap-2">
          <Button variant="secondary" onClick={onClose}>
            Annuler
          </Button>
          <Button type="submit" loading={save.isPending} disabled={!company && owner.length === 0}>
            Enregistrer
          </Button>
        </div>
      </form>
    </Modal>
  )
}

/** Gestion des entreprises : création, modification, désactivation, suppression. */
export default function CompaniesAdmin() {
  const toast = useToast()
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const [offset, setOffset] = useState(0)
  const [form, setForm] = useState(null) // {company?}
  const debounced = useDebounce(search)
  const companies = useQuery({
    queryKey: ['admin', 'companies', { search: debounced, offset }],
    queryFn: () => api.get('/companies', { search: debounced, limit: PAGE, offset }),
    placeholderData: keepPreviousData,
  })
  const act = useMutation({
    mutationFn: ({ call }) => call(),
    onSuccess: (_, { success }) => {
      toast.success(success)
      queryClient.invalidateQueries({ queryKey: ['admin', 'companies'] })
    },
    onError: () => toast.error('Action impossible.'),
  })

  return (
    <>
      <div className="mb-4 flex flex-wrap items-end justify-between gap-4">
        <div className="relative w-full max-w-sm">
          <Search
            size={16}
            className="pointer-events-none absolute top-9 left-3 text-slate-400"
            aria-hidden="true"
          />
          <Input
            label="Rechercher une entreprise"
            type="search"
            className="pl-9"
            value={search}
            onChange={(e) => {
              setSearch(e.target.value)
              setOffset(0)
            }}
          />
        </div>
        <Button onClick={() => setForm({})}>
          <Plus size={16} aria-hidden="true" /> Nouvelle entreprise
        </Button>
      </div>
      {companies.isLoading && <Spinner />}
      {companies.isError && <p role="alert">Impossible de charger les entreprises.</p>}
      {companies.data && (
        <ul className="divide-y divide-slate-100 rounded-xl border border-slate-200 bg-white dark:divide-slate-800 dark:border-slate-800 dark:bg-slate-900">
          {companies.data.items.map((c) => (
            <li key={c.id} className="flex flex-wrap items-center gap-3 p-4">
              <div className="min-w-0 flex-1">
                <p className="font-medium">{c.name}</p>
                <p className="text-xs text-slate-500">{c.location}</p>
              </div>
              <Badge tone="brand">{COMPANY_KINDS[c.kind]}</Badge>
              {!c.is_active && <Badge tone="warning">Désactivée</Badge>}
              <Button size="sm" variant="secondary" onClick={() => setForm({ company: c })}>
                Modifier
              </Button>
              <Button
                size="sm"
                variant="ghost"
                onClick={() =>
                  act.mutate({
                    call: () =>
                      api.post(`/companies/${c.id}/${c.is_active ? 'deactivate' : 'reactivate'}`),
                    success: c.is_active ? 'Entreprise désactivée.' : 'Entreprise réactivée.',
                  })
                }
              >
                {c.is_active ? 'Désactiver' : 'Réactiver'}
              </Button>
              <Button
                size="sm"
                variant="ghost"
                className="text-red-600"
                aria-label={`Supprimer ${c.name}`}
                onClick={() =>
                  act.mutate({
                    call: () => api.delete(`/companies/${c.id}`),
                    success: 'Entreprise supprimée.',
                  })
                }
              >
                Supprimer
              </Button>
            </li>
          ))}
        </ul>
      )}
      {companies.data && (
        <Pagination
          total={companies.data.total}
          limit={PAGE}
          offset={offset}
          onChange={setOffset}
        />
      )}
      {form && <CompanyFormModal company={form.company} onClose={() => setForm(null)} />}
    </>
  )
}
