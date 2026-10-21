import React, { useState, useEffect, useRef } from 'react'
import { MessageSquare, Moon, Sun, LogOut, LogIn } from 'lucide-react'
import NotificationsBell from './NotificationsBell'
import LoginModal from './modals/LoginModal'
import ProfileModal from './modals/ProfileModal'

function createImpulse(ctx, duration = 0.6, decay = 0.4) {
  const length = ctx.sampleRate * duration
  const impulse = ctx.createBuffer(2, length, ctx.sampleRate)
  for (let ch = 0; ch < 2; ch++) {
    const data = impulse.getChannelData(ch)
    for (let i = 0; i < length; i++) {
      data[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / length, decay)
    }
  }
  return impulse
}

async function playNotifSound() {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)()
    const res = await fetch('/notification.mp3')
    const buf = await ctx.decodeAudioData(await res.arrayBuffer())

    const source = ctx.createBufferSource()
    source.buffer = buf

    const masterGain = ctx.createGain()
    masterGain.gain.value = 0.28

    const convolver = ctx.createConvolver()
    convolver.buffer = createImpulse(ctx)

    const dryGain = ctx.createGain()
    dryGain.gain.value = 0.55
    const wetGain = ctx.createGain()
    wetGain.gain.value = 0.2

    source.connect(dryGain)
    source.connect(convolver)
    convolver.connect(wetGain)
    dryGain.connect(masterGain)
    wetGain.connect(masterGain)
    masterGain.connect(ctx.destination)

    source.start()
  } catch (_) {}
}

const ROLE_LABELS = { admin: 'Administrateur', patron: 'Patron', salarie: 'Salarié' }

export default function Header({ role = 'salarie', isLoggedIn = false, profile, onProfileSave, onDeactivateAccount, onLogin, onLogout, onOpenMessaging, unreadCount = 2, darkMode, onToggleDark }) {
  const [loginOpen, setLoginOpen] = useState(false)
  const [profileOpen, setProfileOpen] = useState(false)
  const [toast, setToast] = useState(null)
  const prevCount = useRef(unreadCount)

  const showToast = (msg) => {
    setToast(msg)
    setTimeout(() => setToast(null), 3000)
  }

  useEffect(() => {
    if (unreadCount > prevCount.current) playNotifSound()
    prevCount.current = unreadCount
  }, [unreadCount])

  return (
    <>
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
          {/* Logo */}
          <div className="flex items-center gap-5">
            <img src={darkMode ? "/logo%20mode%20sombre.png" : "/logo-rodez.png"} alt="Rodez Agglomération" className="h-14 w-auto" />
            <div className="w-px h-10 bg-gray-200" />
            <h1 className="text-xl font-bold text-gray-900">Maison de l'Économie</h1>
          </div>

          {/* Right side */}
          <div className="flex items-center gap-3">
            {/* Messagerie */}
            <button
              onClick={onOpenMessaging}
              className="relative p-2.5 hover:bg-gray-100 rounded-xl transition-colors text-gray-500 hover:text-gray-800"
              title="Messagerie interne"
            >
              <MessageSquare size={26} />
              {unreadCount > 0 && (
                <>
                  <span className="absolute top-1.5 right-1.5 w-4 h-4 bg-red-400 rounded-full animate-ping opacity-60" />
                  <span className="absolute top-1.5 right-1.5 w-4 h-4 bg-red-500 rounded-full flex items-center justify-center text-white text-xs font-bold leading-none">
                    {unreadCount}
                  </span>
                </>
              )}
            </button>

            {/* Notifications (invitations) */}
            {isLoggedIn && <NotificationsBell />}

            {isLoggedIn && profile ? (
              <>
                <button
                  onClick={() => setProfileOpen(true)}
                  className="flex items-center gap-3 hover:bg-gray-50 rounded-xl px-3 py-2 transition-colors"
                  title="Modifier mon profil"
                >
                  <div className="text-right">
                    <p className="text-base font-semibold text-gray-900 leading-snug">{profile.name}</p>
                    <p className="text-sm text-gray-500 leading-snug">{ROLE_LABELS[role] || role}</p>
                  </div>
                  {profile.photo ? (
                    <img src={profile.photo} alt="avatar" className="w-11 h-11 rounded-full object-cover border-2 border-gray-100 flex-shrink-0" />
                  ) : (
                    <div className="w-11 h-11 bg-primary-light rounded-full flex items-center justify-center text-white font-bold text-base flex-shrink-0">
                      {profile.name.split(' ').map((n) => n[0]).join('').slice(0, 2).toUpperCase()}
                    </div>
                  )}
                </button>
                <button
                  onClick={onLogout}
                  className="p-2.5 hover:bg-red-50 rounded-xl transition-colors text-gray-400 hover:text-red-500"
                  title="Se déconnecter"
                >
                  <LogOut size={20} />
                </button>
              </>
            ) : (
              <button
                onClick={() => setLoginOpen(true)}
                className="flex items-center gap-2 px-4 py-2 border-2 border-primary-light text-primary-light hover:bg-primary-light hover:text-white font-semibold rounded-xl transition-colors text-sm"
              >
                <LogIn size={16} />
                Connexion
              </button>
            )}

            {/* Dark mode toggle — à droite du login */}
            <button
              onClick={onToggleDark}
              className="p-2.5 hover:bg-gray-100 rounded-xl transition-colors text-gray-500 hover:text-gray-800"
              title={darkMode ? 'Passer en mode clair' : 'Passer en mode sombre'}
            >
              {darkMode ? <Sun size={22} /> : <Moon size={22} />}
            </button>
          </div>
        </div>
      </header>

      {loginOpen && (
        <LoginModal
          onClose={() => setLoginOpen(false)}
          onLoginSuccess={(role, name) => {
            setLoginOpen(false)
            onLogin?.(role, name)
            const label = role === 'admin' ? 'Super Admin' : role === 'patron' ? 'Patron' : 'Salarié'
            showToast(`✓ Connecté en tant que ${label}${name ? ` — ${name}` : ''}`)
          }}
        />
      )}

      {profileOpen && profile && (
        <ProfileModal
          profile={profile}
          onClose={() => setProfileOpen(false)}
          onSave={onProfileSave}
          onDeactivate={onDeactivateAccount}
        />
      )}

      {/* Toast */}
      {toast && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 bg-gray-900 text-white text-sm font-medium px-5 py-3 rounded-xl shadow-lg animate-fade-in">
          {toast}
        </div>
      )}
    </>
  )
}
