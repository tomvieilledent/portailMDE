import React, { useState, useRef, useEffect, useMemo } from 'react'
import { X, Search, Send, ArrowLeft, Users, Plus, Settings, UserPlus, LogOut, Check, Paperclip, FileText, Image as ImageIcon, Loader2 } from 'lucide-react'
import { api, mediaUrl } from '../lib/api'
import { connectSocket, getSocket } from '../lib/socket'
import { useAuth, displayName, initialsOf } from '../context/AuthContext'

const AVATAR_COLORS = ['bg-green-600', 'bg-blue-600', 'bg-purple-600', 'bg-orange-500', 'bg-teal-600', 'bg-pink-600']
const colorFor = (id) => AVATAR_COLORS[(String(id).charCodeAt(0) || 0) % AVATAR_COLORS.length]

const fmtTime = (iso) => {
  if (!iso) return ''
  try {
    return new Date(iso).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
  } catch { return '' }
}

// Nom affiché pour un groupe : le titre s'il existe, sinon la liste des membres.
const groupName = (conv, usersById, myId) => {
  if (conv.title) return conv.title
  const others = (conv.participant_ids || []).filter((id) => id !== myId)
  const names = others.map((id) => usersById[id] ? displayName(usersById[id]) : '?')
  return names.join(', ') || 'Groupe'
}

export default function Messagerie({ onClose, initialContact = null, onNewMessage }) {
  const { user } = useAuth()
  const myId = user?.id

  const [users, setUsers] = useState([])              // autres utilisateurs (contacts)
  const [conversations, setConversations] = useState([]) // groupes (conversations)
  const [selected, setSelected] = useState(null)      // { type:'dm'|'group', id }
  const [messages, setMessages] = useState([])
  const [onlineIds, setOnlineIds] = useState(new Set())
  const [unreadByUser, setUnreadByUser] = useState({})   // dm: senderId -> nb
  const [unreadByConv, setUnreadByConv] = useState({})   // group: convId -> nb
  const [searchQuery, setSearchQuery] = useState('')
  const [newMessage, setNewMessage] = useState('')
  const [loading, setLoading] = useState(true)
  const [showCreate, setShowCreate] = useState(false)
  const [showManage, setShowManage] = useState(false)
  const [pendingAttachment, setPendingAttachment] = useState(null) // {file_url, file_name}
  const [uploading, setUploading] = useState(false)
  const [uploadError, setUploadError] = useState('')
  const fileInputRef = useRef(null)
  const scrollRef = useRef(null)
  // Mirror `selected` in a ref so the socket handler can read the active
  // conversation without putting side effects inside a setState updater
  // (StrictMode invokes updaters twice, which would double-count notifications).
  const selectedRef = useRef(selected)
  useEffect(() => { selectedRef.current = selected }, [selected])

  const usersById = useMemo(() => {
    const map = {}
    users.forEach((u) => { map[u.id] = u })
    if (user) map[user.id] = user
    return map
  }, [users, user])

  // ── Chargement initial : contacts + groupes + non-lus ───────────────────────
  const reloadConversations = () =>
    api.getConversations().then(({ conversations: convs }) => {
      setConversations(convs || [])
      const byConv = {}
      ;(convs || []).forEach((c) => { if (c.unread) byConv[c.id] = c.unread })
      setUnreadByConv(byConv)
      return convs || []
    }).catch(() => [])

  useEffect(() => {
    let cancelled = false
    Promise.all([
      api.getUsers(),
      api.getUnreadCount().catch(() => ({ by_sender: {} })),
      reloadConversations(),
    ])
      .then(([{ users: all }, unread]) => {
        if (cancelled) return
        setUsers((all || []).filter((u) => u.id !== myId))
        setUnreadByUser(unread?.by_sender || {})
      })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [myId])

  // ── Connexion socket + écoute des évènements ────────────────────────────────
  useEffect(() => {
    const socket = connectSocket()
    if (!socket) return

    const onNew = ({ message }) => {
      if (!message) return
      const sel = selectedRef.current
      if (message.conversation_id) {
        // Message de groupe
        const active = sel?.type === 'group' && sel.id === message.conversation_id
        if (active) {
          setMessages((prev) => prev.some((m) => m.id === message.id) ? prev : [...prev, message])
        } else if (message.author_id !== myId) {
          setUnreadByConv((prev) => ({ ...prev, [message.conversation_id]: (prev[message.conversation_id] || 0) + 1 }))
          onNewMessage?.()
        }
        return
      }
      // Message direct (DM)
      const otherId = message.author_id === myId ? message.recipient_id : message.author_id
      const active = sel?.type === 'dm' && sel.id === otherId
      if (active) {
        setMessages((prev) => prev.some((m) => m.id === message.id) ? prev : [...prev, message])
      } else if (message.author_id !== myId) {
        setUnreadByUser((prev) => ({ ...prev, [message.author_id]: (prev[message.author_id] || 0) + 1 }))
        onNewMessage?.()
      }
    }
    const onPresence = ({ user_id, online }) => {
      setOnlineIds((prev) => {
        const next = new Set(prev)
        online ? next.add(user_id) : next.delete(user_id)
        return next
      })
    }
    const onOnlineList = ({ user_ids }) => setOnlineIds(new Set(user_ids || []))

    // Un groupe vient d'être créé ou je viens d'y être ajouté : on l'insère
    // dans la liste en direct (dédup par id, le créateur l'ayant déjà ajouté).
    const onConvAdded = ({ conversation }) => {
      if (!conversation) return
      setConversations((prev) =>
        prev.some((c) => c.id === conversation.id) ? prev : [conversation, ...prev])
      if (conversation.unread) {
        setUnreadByConv((prev) => ({ ...prev, [conversation.id]: conversation.unread }))
      }
    }
    // J'ai été retiré (ou j'ai quitté) : on retire le groupe et on ferme le fil
    // s'il était ouvert.
    const onConvRemoved = ({ conversation_id }) => {
      setConversations((prev) => prev.filter((c) => c.id !== conversation_id))
      setUnreadByConv((prev) => {
        if (!prev[conversation_id]) return prev
        const next = { ...prev }; delete next[conversation_id]; return next
      })
      setSelected((sel) => (sel?.type === 'group' && sel.id === conversation_id) ? null : sel)
    }
    // Métadonnée de groupe modifiée (renommage) : on met à jour la liste.
    const onConvUpdated = ({ conversation }) => {
      if (!conversation) return
      setConversations((prev) => prev.map((c) =>
        c.id === conversation.id ? { ...c, ...conversation } : c))
    }

    socket.on('new_message', onNew)
    socket.on('presence', onPresence)
    socket.on('online_users', onOnlineList)
    socket.on('conversation_added', onConvAdded)
    socket.on('conversation_removed', onConvRemoved)
    socket.on('conversation_updated', onConvUpdated)
    const askOnline = () => socket.emit('who_is_online')
    socket.connected ? askOnline() : socket.on('connect', askOnline)

    return () => {
      socket.off('new_message', onNew)
      socket.off('presence', onPresence)
      socket.off('online_users', onOnlineList)
      socket.off('conversation_added', onConvAdded)
      socket.off('conversation_removed', onConvRemoved)
      socket.off('conversation_updated', onConvUpdated)
      socket.off('connect', askOnline)
    }
  }, [myId, onNewMessage])

  // ── Présélection depuis "Contacter" (par nom) ───────────────────────────────
  useEffect(() => {
    if (!initialContact || !users.length || selected) return
    const needle = initialContact.toLowerCase()
    const match = users.find((u) => displayName(u).toLowerCase().includes(needle) || (u.email || '').toLowerCase().includes(needle))
    if (match) selectDm(match.id)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialContact, users])

  // ── Auto-scroll en bas à chaque nouveau message ─────────────────────────────
  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages])

  const selectDm = async (userId) => {
    setSelected({ type: 'dm', id: userId })
    setMessages([])
    setUnreadByUser((prev) => {
      if (!prev[userId]) return prev
      const next = { ...prev }; delete next[userId]; return next
    })
    api.markDirectRead(userId).catch(() => {})
    try {
      const { messages: history } = await api.getDirectMessages(userId)
      setMessages(history || [])
    } catch { /* historique indisponible */ }
  }

  const selectGroup = async (convId) => {
    setSelected({ type: 'group', id: convId })
    setMessages([])
    setUnreadByConv((prev) => {
      if (!prev[convId]) return prev
      const next = { ...prev }; delete next[convId]; return next
    })
    const socket = getSocket()
    socket?.emit('join_conversation', { conversation_id: convId })
    api.markConversationRead(convId).catch(() => {})
    try {
      const { messages: history } = await api.getConversationMessages(convId)
      setMessages(history || [])
    } catch { /* historique indisponible */ }
  }

  const handleFileSelect = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    e.target.value = ''
    setUploadError('')
    setUploading(true)
    try {
      const formData = new FormData()
      formData.append('file', file)
      const res = await api.uploadMessageAttachment(formData)
      setPendingAttachment({ file_url: res.file_url, file_name: res.file_name })
    } catch (err) {
      setUploadError(err.message || 'Échec de l\'upload')
    } finally {
      setUploading(false)
    }
  }

  const sendMessage = () => {
    const content = newMessage.trim()
    if (!content && !pendingAttachment || !selected) return
    const socket = getSocket()
    if (!socket) return
    const payload = {
      content: content || pendingAttachment.file_name,
      ...(pendingAttachment || {}),
    }
    if (selected.type === 'group') {
      socket.emit('send_message', { conversation_id: selected.id, ...payload })
    } else {
      socket.emit('send_message', { recipient_id: selected.id, ...payload })
    }
    setNewMessage('')
    setPendingAttachment(null)
    setUploadError('')
  }

  const handleGroupCreated = (conv) => {
    // Dédup par id : le backend pousse aussi `conversation_added` au créateur,
    // qui peut arriver avant ou après la réponse REST. Sans ce garde-fou, une
    // course fait apparaître le groupe en double dans la liste.
    setConversations((prev) => prev.some((c) => c.id === conv.id) ? prev : [conv, ...prev])
    getSocket()?.emit('join_conversation', { conversation_id: conv.id })
    setShowCreate(false)
    selectGroup(conv.id)
  }

  const filteredUsers = useMemo(
    () => users.filter((u) => displayName(u).toLowerCase().includes(searchQuery.toLowerCase())),
    [users, searchQuery]
  )
  const filteredGroups = useMemo(
    () => conversations.filter((c) => groupName(c, usersById, myId).toLowerCase().includes(searchQuery.toLowerCase())),
    [conversations, usersById, myId, searchQuery]
  )

  const activeUser = selected?.type === 'dm' ? usersById[selected.id] : null
  const activeGroup = selected?.type === 'group' ? conversations.find((c) => c.id === selected.id) : null

  return (
    <div className="fixed inset-0 z-50 bg-white flex flex-col">
      {/* Top bar */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 bg-white shadow-sm">
        <div className="flex items-center gap-3">
          <button onClick={onClose} className="p-2 hover:bg-gray-100 rounded-xl transition-colors text-gray-500 hover:text-gray-900" title="Retour">
            <ArrowLeft size={22} />
          </button>
          <div className="w-8 h-8 bg-primary-light rounded-full flex items-center justify-center">
            <svg viewBox="0 0 24 24" width="16" height="16" fill="white">
              <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z" />
            </svg>
          </div>
          <h1 className="text-xl font-bold text-gray-900">Messagerie interne</h1>
        </div>
        <button onClick={onClose} className="p-2 hover:bg-gray-100 rounded-lg text-gray-500 hover:text-gray-900 transition-colors">
          <X size={22} />
        </button>
      </div>

      {/* Main content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left panel — conversations */}
        <div className={`w-full md:w-80 lg:w-96 border-r border-gray-200 flex flex-col flex-shrink-0 ${selected ? 'hidden md:flex' : 'flex'}`}>
          <div className="p-4 border-b border-gray-100 space-y-3">
            <div className="relative">
              <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                placeholder="Rechercher..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-4 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-light bg-gray-50"
              />
            </div>
            <button
              onClick={() => setShowCreate(true)}
              className="w-full flex items-center justify-center gap-2 py-2 text-sm font-semibold text-white bg-primary-light hover:bg-primary rounded-lg transition-colors"
            >
              <Plus size={16} /> Nouveau groupe
            </button>
          </div>

          <div className="flex-1 overflow-y-auto">
            {loading && <p className="text-center text-gray-400 text-sm py-6">Chargement…</p>}

            {/* Groupes */}
            {!loading && filteredGroups.length > 0 && (
              <p className="px-4 pt-3 pb-1 text-xs font-bold text-gray-400 uppercase tracking-wide">Groupes</p>
            )}
            {filteredGroups.map((c) => {
              const unread = unreadByConv[c.id] || 0
              const active = selected?.type === 'group' && selected.id === c.id
              return (
                <button
                  key={c.id}
                  onClick={() => selectGroup(c.id)}
                  className={`w-full flex items-center gap-3 px-4 py-4 hover:bg-gray-50 transition-colors border-b border-gray-50 text-left ${active ? 'bg-green-50 border-l-4 border-l-primary-light' : unread ? 'bg-primary-light/5' : ''}`}
                >
                  <div className="w-11 h-11 rounded-full flex items-center justify-center text-white bg-primary flex-shrink-0">
                    <Users size={20} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <span className={`text-sm truncate block ${unread ? 'font-bold text-gray-900' : 'font-semibold text-gray-900'}`}>{groupName(c, usersById, myId)}</span>
                    <p className={`text-xs truncate ${unread ? 'text-primary-light font-medium' : 'text-gray-500'}`}>
                      {unread ? `${unread} nouveau${unread > 1 ? 'x' : ''} message${unread > 1 ? 's' : ''}` : `${(c.participant_ids || []).length} membres`}
                    </p>
                  </div>
                  {unread > 0 && (
                    <span className="ml-2 flex-shrink-0 min-w-[20px] h-5 px-1.5 bg-primary-light rounded-full flex items-center justify-center text-white text-xs font-bold">{unread}</span>
                  )}
                </button>
              )
            })}

            {/* Contacts (DM) */}
            {!loading && filteredUsers.length > 0 && (
              <p className="px-4 pt-3 pb-1 text-xs font-bold text-gray-400 uppercase tracking-wide">Contacts</p>
            )}
            {!loading && filteredGroups.length === 0 && filteredUsers.length === 0 && (
              <p className="text-center text-gray-400 text-sm py-6">Aucun résultat</p>
            )}
            {filteredUsers.map((u) => {
              const online = onlineIds.has(u.id)
              const unread = unreadByUser[u.id] || 0
              const active = selected?.type === 'dm' && selected.id === u.id
              return (
                <button
                  key={u.id}
                  onClick={() => selectDm(u.id)}
                  className={`w-full flex items-center gap-3 px-4 py-4 hover:bg-gray-50 transition-colors border-b border-gray-50 text-left ${active ? 'bg-green-50 border-l-4 border-l-primary-light' : unread ? 'bg-primary-light/5' : ''}`}
                >
                  <div className="relative flex-shrink-0">
                    {u.profile_picture ? (
                      <img src={mediaUrl(u.profile_picture)} alt={displayName(u)} className="w-11 h-11 rounded-full object-cover" />
                    ) : (
                      <div className={`w-11 h-11 rounded-full flex items-center justify-center text-white font-bold text-sm ${colorFor(u.id)}`}>
                        {initialsOf(u)}
                      </div>
                    )}
                    {online && <span className="absolute bottom-0 right-0 w-3 h-3 bg-green-400 border-2 border-white rounded-full" />}
                  </div>
                  <div className="flex-1 min-w-0">
                    <span className={`text-sm truncate block ${unread ? 'font-bold text-gray-900' : 'font-semibold text-gray-900'}`}>{displayName(u)}</span>
                    <p className={`text-xs truncate ${unread ? 'text-primary-light font-medium' : 'text-gray-500'}`}>
                      {unread ? `${unread} nouveau${unread > 1 ? 'x' : ''} message${unread > 1 ? 's' : ''}` : (online ? 'En ligne' : (u.email || ''))}
                    </p>
                  </div>
                  {unread > 0 && (
                    <span className="ml-2 flex-shrink-0 min-w-[20px] h-5 px-1.5 bg-primary-light rounded-full flex items-center justify-center text-white text-xs font-bold">{unread}</span>
                  )}
                </button>
              )
            })}
          </div>
        </div>

        {/* Right panel — thread */}
        <div className={`flex-1 flex flex-col ${selected ? 'flex' : 'hidden md:flex'}`}>
          {selected && (activeUser || activeGroup) ? (
            <>
              {/* Header du fil */}
              <div className="flex items-center gap-3 px-6 py-4 border-b border-gray-200 bg-white">
                <button onClick={() => setSelected(null)} className="p-1 hover:bg-gray-100 rounded-lg md:hidden">
                  <ArrowLeft size={20} />
                </button>
                {activeGroup ? (
                  <>
                    <div className="w-10 h-10 rounded-full flex items-center justify-center text-white bg-primary">
                      <Users size={20} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-semibold text-gray-900 truncate">{groupName(activeGroup, usersById, myId)}</p>
                      <p className="text-xs text-gray-500 truncate">
                        {(activeGroup.participant_ids || []).map((id) => id === myId ? 'Vous' : (usersById[id] ? displayName(usersById[id]) : '?')).join(', ')}
                      </p>
                    </div>
                    <button onClick={() => setShowManage(true)} className="p-2 hover:bg-gray-100 rounded-lg text-gray-500 hover:text-gray-900" title="Gérer le groupe">
                      <Settings size={20} />
                    </button>
                  </>
                ) : (
                  <>
                    {activeUser.profile_picture ? (
                      <img src={mediaUrl(activeUser.profile_picture)} alt={displayName(activeUser)} className="w-10 h-10 rounded-full object-cover" />
                    ) : (
                      <div className={`w-10 h-10 rounded-full flex items-center justify-center text-white font-bold text-sm ${colorFor(activeUser.id)}`}>
                        {initialsOf(activeUser)}
                      </div>
                    )}
                    <div>
                      <p className="font-semibold text-gray-900">{displayName(activeUser)}</p>
                      <p className="text-xs text-gray-500">
                        {onlineIds.has(activeUser.id) ? <span className="text-green-500">● En ligne</span> : 'Hors ligne'}
                      </p>
                    </div>
                  </>
                )}
              </div>

              {/* Fil de messages */}
              <div ref={scrollRef} className="flex-1 overflow-y-auto px-6 py-4 space-y-3 bg-gray-50">
                {messages.length === 0 && (
                  <p className="text-center text-gray-400 text-sm mt-8">Aucun message. Démarrez la conversation !</p>
                )}
                {messages.map((msg) => {
                  const mine = msg.author_id === myId
                  const sender = usersById[msg.author_id]
                  return (
                    <div key={msg.id} className={`flex ${mine ? 'justify-end' : 'justify-start'}`}>
                      {!mine && (
                        sender?.profile_picture ? (
                          <img src={mediaUrl(sender.profile_picture)} alt="" className="w-8 h-8 rounded-full object-cover mr-2 flex-shrink-0 self-end" />
                        ) : (
                          <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white font-bold text-xs mr-2 flex-shrink-0 self-end ${colorFor(msg.author_id)}`}>
                            {sender ? initialsOf(sender) : '?'}
                          </div>
                        )
                      )}
                      <div className={`max-w-xs lg:max-w-md xl:max-w-lg rounded-2xl text-sm overflow-hidden ${mine ? 'bg-primary-light text-white rounded-br-sm' : 'bg-white text-gray-900 shadow-sm rounded-bl-sm'}`}>
                        {!mine && activeGroup && (
                          <p className="px-4 pt-2 text-xs font-bold text-primary">{sender ? displayName(sender) : 'Inconnu'}</p>
                        )}
                        {msg.file_url && (() => {
                          const isImage = /\.(jpg|jpeg|png|gif|webp)$/i.test(msg.file_name || msg.file_url)
                          const fullUrl = msg.file_url.startsWith('http') ? msg.file_url : `${window.location.origin.replace(':3000', ':8000')}${msg.file_url}`
                          return isImage ? (
                            <a href={fullUrl} target="_blank" rel="noreferrer" className="block px-2 pt-2">
                              <img src={fullUrl} alt={msg.file_name || 'image'} className="rounded-xl max-h-48 object-cover" />
                            </a>
                          ) : (
                            <a href={fullUrl} target="_blank" rel="noreferrer" download={msg.file_name}
                              className={`flex items-center gap-2 mx-3 mt-2 px-3 py-2 rounded-lg text-xs font-medium ${mine ? 'bg-white/20 hover:bg-white/30 text-white' : 'bg-gray-100 hover:bg-gray-200 text-gray-700'} transition-colors`}
                            >
                              <FileText size={14} className="flex-shrink-0" />
                              <span className="truncate max-w-[180px]">{msg.file_name || 'Fichier joint'}</span>
                            </a>
                          )
                        })()}
                        {/* Affiche le texte : toujours sans fichier, ou comme légende si différent du nom du fichier */}
                        {(!msg.file_url || (msg.content && msg.content !== msg.file_name)) && (
                          <p className={`px-4 pb-1 ${msg.file_url ? 'pt-1.5' : 'pt-2.5'}`}>{msg.content}</p>
                        )}
                        <p className={`text-xs px-4 pb-2.5 ${mine ? 'text-green-100' : 'text-gray-400'}`}>{fmtTime(msg.created_at)}</p>
                      </div>
                    </div>
                  )
                })}
              </div>

              {/* Zone de saisie */}
              <div className="px-6 py-3 border-t border-gray-200 bg-white">
                {/* Chip fichier en attente */}
                {pendingAttachment && (
                  <div className="flex items-center gap-2 mb-2 px-3 py-1.5 bg-primary-light/10 rounded-lg max-w-xs">
                    <FileText size={14} className="text-primary-light flex-shrink-0" />
                    <span className="text-xs text-primary-light truncate flex-1">{pendingAttachment.file_name}</span>
                    <button onClick={() => setPendingAttachment(null)} className="text-primary-light hover:text-red-500 flex-shrink-0">
                      <X size={13} />
                    </button>
                  </div>
                )}
                {uploadError && <p className="text-xs text-red-500 mb-1">{uploadError}</p>}
                <div className="flex items-center gap-2">
                  {/* Input fichier caché */}
                  <input ref={fileInputRef} type="file" className="hidden" onChange={handleFileSelect}
                    accept=".jpg,.jpeg,.png,.gif,.webp,.pdf,.doc,.docx,.ppt,.pptx,.xls,.xlsx,.odt,.odp,.ods,.txt,.csv,.zip"
                  />
                  <button
                    onClick={() => fileInputRef.current?.click()}
                    disabled={uploading}
                    title="Joindre un fichier"
                    className="w-9 h-9 flex-shrink-0 flex items-center justify-center rounded-full hover:bg-gray-100 text-gray-400 hover:text-primary-light transition-colors disabled:opacity-40"
                  >
                    {uploading ? <Loader2 size={18} className="animate-spin" /> : <Paperclip size={18} />}
                  </button>
                  <input
                    type="text"
                    placeholder="Écrire un message..."
                    value={newMessage}
                    onChange={(e) => setNewMessage(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
                    className="flex-1 px-4 py-2.5 border border-gray-200 rounded-full text-sm focus:outline-none focus:ring-2 focus:ring-primary-light bg-gray-50"
                  />
                  <button
                    onClick={sendMessage}
                    disabled={!newMessage.trim() && !pendingAttachment}
                    className="w-10 h-10 flex-shrink-0 bg-primary-light hover:bg-primary disabled:opacity-40 rounded-full flex items-center justify-center text-white transition-colors"
                  >
                    <Send size={16} />
                  </button>
                </div>
              </div>
            </>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center text-gray-400">
              <svg viewBox="0 0 24 24" width="64" height="64" fill="currentColor" className="mb-4 opacity-30">
                <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z" />
              </svg>
              <p className="text-lg font-medium">Sélectionnez une conversation</p>
              <p className="text-sm mt-1">Choisissez un contact ou un groupe pour échanger</p>
            </div>
          )}
        </div>
      </div>

      {showCreate && (
        <GroupCreateModal users={users} onClose={() => setShowCreate(false)} onCreated={handleGroupCreated} />
      )}
      {showManage && activeGroup && (
        <GroupManageModal
          conversation={activeGroup}
          users={users}
          usersById={usersById}
          myId={myId}
          onClose={() => setShowManage(false)}
          onChanged={(updated) => {
            setConversations((prev) => prev.map((c) => c.id === updated.id ? { ...c, ...updated } : c))
          }}
          onLeft={(convId) => {
            setConversations((prev) => prev.filter((c) => c.id !== convId))
            setShowManage(false)
            setSelected(null)
          }}
        />
      )}
    </div>
  )
}

// ── Modal : créer un groupe ───────────────────────────────────────────────────
function GroupCreateModal({ users, onClose, onCreated }) {
  const [title, setTitle] = useState('')
  const [selectedIds, setSelectedIds] = useState(new Set())
  const [query, setQuery] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const toggle = (id) => setSelectedIds((prev) => {
    const next = new Set(prev)
    next.has(id) ? next.delete(id) : next.add(id)
    return next
  })

  const filtered = users.filter((u) => displayName(u).toLowerCase().includes(query.toLowerCase()))

  const submit = async () => {
    if (!title.trim()) { setError('Donnez un nom au groupe.'); return }
    if (selectedIds.size === 0) { setError('Sélectionnez au moins un membre.'); return }
    setSaving(true); setError('')
    try {
      const { conversation } = await api.createConversation({
        title: title.trim(),
        participant_ids: [...selectedIds],
      })
      onCreated(conversation)
    } catch (e) {
      setError(e?.message || 'Échec de la création du groupe.')
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 z-[60] bg-black/40 flex items-center justify-center p-4" onClick={onClose}>
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md flex flex-col max-h-[85vh]" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100">
          <h2 className="text-lg font-bold text-gray-900">Nouveau groupe</h2>
          <button onClick={onClose} className="p-1.5 hover:bg-gray-100 rounded-lg text-gray-500"><X size={20} /></button>
        </div>
        <div className="px-5 py-4 space-y-3 overflow-y-auto">
          <input
            type="text"
            placeholder="Nom du groupe"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="w-full px-4 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-light"
          />
          <div className="relative">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="Rechercher un membre..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="w-full pl-9 pr-4 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-light bg-gray-50"
            />
          </div>
          <p className="text-xs text-gray-500">{selectedIds.size} membre{selectedIds.size > 1 ? 's' : ''} sélectionné{selectedIds.size > 1 ? 's' : ''}</p>
          <div className="max-h-60 overflow-y-auto -mx-1">
            {filtered.map((u) => {
              const checked = selectedIds.has(u.id)
              return (
                <button key={u.id} onClick={() => toggle(u.id)} className="w-full flex items-center gap-3 px-1 py-2 hover:bg-gray-50 rounded-lg text-left">
                  {u.profile_picture ? (
                    <img src={mediaUrl(u.profile_picture)} alt="" className="w-9 h-9 rounded-full object-cover" />
                  ) : (
                    <div className={`w-9 h-9 rounded-full flex items-center justify-center text-white font-bold text-xs ${colorFor(u.id)}`}>{initialsOf(u)}</div>
                  )}
                  <span className="flex-1 text-sm text-gray-900 truncate">{displayName(u)}</span>
                  <span className={`w-5 h-5 rounded border flex items-center justify-center ${checked ? 'bg-primary-light border-primary-light' : 'border-gray-300'}`}>
                    {checked && <Check size={14} className="text-white" />}
                  </span>
                </button>
              )
            })}
          </div>
          {error && <p className="text-sm text-red-500">{error}</p>}
        </div>
        <div className="px-5 py-4 border-t border-gray-100 flex justify-end gap-2">
          <button onClick={onClose} className="px-4 py-2 text-sm font-medium text-gray-600 hover:bg-gray-100 rounded-lg">Annuler</button>
          <button onClick={submit} disabled={saving} className="px-4 py-2 text-sm font-semibold text-white bg-primary-light hover:bg-primary disabled:opacity-50 rounded-lg">
            {saving ? 'Création…' : 'Créer'}
          </button>
        </div>
      </div>
    </div>
  )
}

// ── Modal : gérer un groupe (renommer / membres / quitter) ────────────────────
function GroupManageModal({ conversation, users, usersById, myId, onClose, onChanged, onLeft }) {
  const [title, setTitle] = useState(conversation.title || '')
  const [members, setMembers] = useState(conversation.participant_ids || [])
  const [query, setQuery] = useState('')
  const [busy, setBusy] = useState(false)
  // Only the group creator may rename it or add/remove members. Guests get a
  // read-only view whose sole action is leaving the conversation.
  const isCreator = conversation.creator_id === myId

  const rename = async () => {
    setBusy(true)
    try {
      const { conversation: updated } = await api.renameConversation(conversation.id, title.trim())
      onChanged(updated)
    } catch { /* ignore */ }
    setBusy(false)
  }

  const addMember = async (uid) => {
    setBusy(true)
    try {
      const { conversation: updated } = await api.addParticipant(conversation.id, uid)
      setMembers(updated.participant_ids || [])
      onChanged(updated)
    } catch { /* ignore */ }
    setBusy(false)
  }

  const removeMember = async (uid) => {
    setBusy(true)
    try {
      const { conversation: updated } = await api.removeParticipant(conversation.id, uid)
      setMembers(updated.participant_ids || [])
      onChanged(updated)
    } catch { /* ignore */ }
    setBusy(false)
  }

  const leave = async () => {
    setBusy(true)
    try {
      await api.removeParticipant(conversation.id, myId)
      onLeft(conversation.id)
    } catch { setBusy(false) }
  }

  const candidates = users.filter((u) => !members.includes(u.id) && displayName(u).toLowerCase().includes(query.toLowerCase()))

  return (
    <div className="fixed inset-0 z-[60] bg-black/40 flex items-center justify-center p-4" onClick={onClose}>
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md flex flex-col max-h-[85vh]" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100">
          <h2 className="text-lg font-bold text-gray-900">{isCreator ? 'Gérer le groupe' : 'Infos du groupe'}</h2>
          <button onClick={onClose} className="p-1.5 hover:bg-gray-100 rounded-lg text-gray-500"><X size={20} /></button>
        </div>
        <div className="px-5 py-4 space-y-4 overflow-y-auto">
          {isCreator ? (
            <div>
              <label className="text-xs font-bold text-gray-400 uppercase">Nom du groupe</label>
              <div className="flex gap-2 mt-1">
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="flex-1 px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-light"
                />
                <button onClick={rename} disabled={busy} className="px-3 py-2 text-sm font-semibold text-white bg-primary-light hover:bg-primary disabled:opacity-50 rounded-lg">OK</button>
              </div>
            </div>
          ) : (
            <p className="text-xs text-gray-400">Seul le créateur du groupe peut le renommer ou gérer ses membres.</p>
          )}

          <div>
            <label className="text-xs font-bold text-gray-400 uppercase">Membres ({members.length})</label>
            <div className="mt-1 space-y-1">
              {members.map((id) => {
                const u = usersById[id]
                return (
                  <div key={id} className="flex items-center gap-3 py-1.5">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white font-bold text-xs ${colorFor(id)}`}>{u ? initialsOf(u) : '?'}</div>
                    <span className="flex-1 text-sm text-gray-900 truncate">{id === myId ? 'Vous' : (u ? displayName(u) : '?')}</span>
                    {isCreator && id !== myId && (
                      <button onClick={() => removeMember(id)} disabled={busy} className="p-1 text-gray-400 hover:text-red-500" title="Retirer"><X size={16} /></button>
                    )}
                  </div>
                )
              })}
            </div>
          </div>

          {isCreator && (
            <div>
              <label className="text-xs font-bold text-gray-400 uppercase">Ajouter un membre</label>
              <div className="relative mt-1">
                <UserPlus size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                <input
                  type="text"
                  placeholder="Rechercher..."
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  className="w-full pl-9 pr-4 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-light bg-gray-50"
                />
              </div>
              {query && (
                <div className="mt-1 max-h-40 overflow-y-auto">
                  {candidates.map((u) => (
                    <button key={u.id} onClick={() => addMember(u.id)} disabled={busy} className="w-full flex items-center gap-3 py-2 px-1 hover:bg-gray-50 rounded-lg text-left">
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white font-bold text-xs ${colorFor(u.id)}`}>{initialsOf(u)}</div>
                      <span className="flex-1 text-sm text-gray-900 truncate">{displayName(u)}</span>
                      <Plus size={16} className="text-primary-light" />
                    </button>
                  ))}
                  {candidates.length === 0 && <p className="text-xs text-gray-400 py-2">Aucun contact</p>}
                </div>
              )}
            </div>
          )}
        </div>
        <div className="px-5 py-4 border-t border-gray-100 flex justify-between">
          <button onClick={leave} disabled={busy} className="flex items-center gap-2 px-4 py-2 text-sm font-semibold text-red-500 hover:bg-red-50 rounded-lg">
            <LogOut size={16} /> Quitter
          </button>
          <button onClick={onClose} className="px-4 py-2 text-sm font-medium text-gray-600 hover:bg-gray-100 rounded-lg">Fermer</button>
        </div>
      </div>
    </div>
  )
}
