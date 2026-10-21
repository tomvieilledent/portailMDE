import React from 'react'
import { LayoutDashboard, Building2, Users, GraduationCap, TrendingUp, Settings, Store } from 'lucide-react'

const ICONS = {
  dashboard: LayoutDashboard,
  companies: Building2,
  users: Users,
  trainings: GraduationCap,
  news: TrendingUp,
  gestion: Settings,
  monentreprise: Store,
}

const ICON_COLORS = {
  dashboard: 'text-primary',
  companies: 'text-orange-400',
  users: 'text-blue-500',
  trainings: 'text-purple-500',
  news: 'text-amber-500',
  gestion: 'text-gray-500',
  monentreprise: 'text-teal-500',
}

export default function TabNavigation({ tabs, activeTab, setActiveTab }) {
  return (
    <nav className="bg-white border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-6 flex items-center justify-center gap-3 py-4">
        {tabs.map((tab) => {
          const Icon = ICONS[tab.id]
          const isActive = activeTab === tab.id
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-3 px-7 py-3.5 rounded-xl font-semibold text-lg transition-colors whitespace-nowrap ${
                isActive
                  ? 'bg-primary-light text-white shadow-sm'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
              }`}
            >
              {Icon && (
                <Icon
                  size={22}
                  className={isActive ? ICON_COLORS[tab.id] : ''}
                />
              )}
              {tab.label}
            </button>
          )
        })}
      </div>
    </nav>
  )
}
