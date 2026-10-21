import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Plus, Search } from 'lucide-react'
import { useState } from 'react'

import { useAuth } from '../../auth/AuthProvider'
import { isSuperAdmin } from '../../auth/permissions'
import {
  Avatar,
  Badge,
  Button,
  Input,
  Pagination,
  Spinner,
  uploadUrl,
  useToast,
} from '../../components/ui'
import { api } from '../../lib/api'
import { useDebounce } from '../../lib/useDebounce'
import { fullName } from '../directory/labels'
import RoleModal from './RoleModal'
import UserFormModal from './UserFormModal'
import { ROLES } from './labels'

const PAGE = 25

/** Gestion des comptes : création, activation, suppression, rôles. */
export default function UsersAdmin() {
  const { user: me } = useAuth()
  const toast = useToast()
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const [offset, setOffset] = useState(0)
  const [creating, setCreating] = useState(false)
  const [roleTarget, setRoleTarget] = useState(null)
  const debounced = useDebounce(search)
  const users = useQuery({
    queryKey: ['admin', 'users', { search: debounced, offset }],
    queryFn: () => api.get('/users', { search: debounced, limit: PAGE, offset }),
    placeholderData: keepPreviousData,
  })
  const refresh = () => queryClient.invalidateQueries({ queryKey: ['admin', 'users'] })
  const act = useMutation({
    mutationFn: ({ call }) => call(),
    onSuccess: (_, { success }) => {
      toast.success(success)
      refresh()
    },
    onError: (err) => toast.error(err.status === 403 ? err.message : 'Action impossible.'),
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
            label="Rechercher un compte"
            type="search"
            className="pl-9"
            value={search}
            onChange={(e) => {
              setSearch(e.target.value)
              setOffset(0)
            }}
          />
        </div>
        <Button onClick={() => setCreating(true)}>
          <Plus size={16} aria-hidden="true" /> Nouveau compte
        </Button>
      </div>

      {users.isLoading && <Spinner />}
      {users.isError && <p role="alert">Impossible de charger les comptes.</p>}
      {users.data && (
        <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-slate-200 text-xs text-slate-500 uppercase dark:border-slate-800">
              <tr>
                <th className="p-3">Compte</th>
                <th className="p-3">Rôle</th>
                <th className="p-3">Statut</th>
                <th className="p-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {users.data.items.map((u) => (
                <tr key={u.id}>
                  <td className="p-3">
                    <div className="flex items-center gap-3">
                      <Avatar
                        src={uploadUrl(u.avatar_path)}
                        firstName={u.first_name}
                        lastName={u.last_name}
                        size="sm"
                      />
                      <div>
                        <p className="font-medium">{fullName(u)}</p>
                        <p className="text-xs text-slate-500">{u.email}</p>
                      </div>
                    </div>
                  </td>
                  <td className="p-3">
                    <Badge tone={u.role === 'member' ? 'neutral' : 'brand'}>{ROLES[u.role]}</Badge>
                  </td>
                  <td className="p-3">
                    {u.is_active ? (
                      <Badge tone="success">Actif</Badge>
                    ) : (
                      <Badge tone="warning">Désactivé</Badge>
                    )}
                  </td>
                  <td className="p-3">
                    <div className="flex justify-end gap-1">
                      {isSuperAdmin(me) && (
                        <Button size="sm" variant="ghost" onClick={() => setRoleTarget(u)}>
                          Rôle
                        </Button>
                      )}
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() =>
                          act.mutate({
                            call: () =>
                              api.post(
                                `/users/${u.id}/${u.is_active ? 'deactivate' : 'reactivate'}`,
                              ),
                            success: u.is_active ? 'Compte désactivé.' : 'Compte réactivé.',
                          })
                        }
                      >
                        {u.is_active ? 'Désactiver' : 'Réactiver'}
                      </Button>
                      {u.id !== me.id && (
                        <Button
                          size="sm"
                          variant="ghost"
                          className="text-red-600"
                          aria-label={`Supprimer ${fullName(u)}`}
                          onClick={() =>
                            act.mutate({
                              call: () => api.delete(`/users/${u.id}`),
                              success: 'Compte supprimé.',
                            })
                          }
                        >
                          Supprimer
                        </Button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {users.data && (
        <Pagination total={users.data.total} limit={PAGE} offset={offset} onChange={setOffset} />
      )}
      {creating && <UserFormModal onClose={() => setCreating(false)} />}
      {roleTarget && <RoleModal target={roleTarget} onClose={() => setRoleTarget(null)} />}
    </>
  )
}
