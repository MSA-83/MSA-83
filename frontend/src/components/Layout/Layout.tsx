import { useState, ReactNode } from 'react'
import { NavLink } from 'react-router-dom'
import NotificationsPanel from '../NotificationsPanel'
import { useNotificationsContext } from '../../contexts/NotificationsContext'

interface LayoutProps {
  children: ReactNode
}

const navItems = [
  { path: '/', label: 'Dashboard', icon: '📊' },
  { path: '/chat', label: 'Chat', icon: '💬' },
  { path: '/chat/ws', label: 'Live Chat', icon: '⚡' },
  { path: '/memory', label: 'Memory', icon: '🧠' },
  { path: '/agents', label: 'Agents', icon: '🤖' },
  { path: '/billing', label: 'Billing', icon: '💳' },
  { path: '/admin', label: 'Admin', icon: '🔧' },
  { path: '/settings', label: 'Settings', icon: '⚙️' },
  { path: '/settings/webhooks', label: 'Webhooks', icon: '🔗' },
]

export default function Layout({ children }: LayoutProps) {
  const [showNotifications, setShowNotifications] = useState(false)
  const { unreadCount } = useNotificationsContext()

  return (
    <div className="flex h-screen bg-titanium-950">
      <aside className="w-64 bg-titanium-900 border-r border-titanium-800 flex flex-col">
        <div className="p-6 border-b border-titanium-800">
          <h1 className="text-xl font-bold text-accent-400">Titanium</h1>
          <p className="text-xs text-titanium-400 mt-1">Enterprise AI Platform</p>
        </div>

        <nav className="flex-1 p-4 overflow-y-auto">
          <ul className="space-y-1">
            {navItems.map((item) => (
              <li key={item.path}>
                <NavLink
                  to={item.path}
                  className={({ isActive }) =>
                    `flex items-center gap-3 px-4 py-2.5 rounded-lg transition-colors text-sm ${
                      isActive
                        ? 'bg-accent-500/10 text-accent-400 border border-accent-500/20'
                        : 'text-titanium-400 hover:bg-titanium-800 hover:text-titanium-200'
                    }`
                  }
                >
                  <span className="text-base">{item.icon}</span>
                  <span className="font-medium">{item.label}</span>
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>

        <div className="p-4 border-t border-titanium-800">
          <div className="flex items-center gap-3 px-4 py-2">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
            <span className="text-sm text-titanium-400">System Online</span>
          </div>
          <NavLink
            to="/login"
            className="flex items-center gap-3 px-4 py-2 mt-1 text-sm text-titanium-500 hover:text-titanium-300 transition-colors"
          >
            <span>🔑</span>
            <span>Auth</span>
          </NavLink>
        </div>
      </aside>

      <div className="flex-1 flex flex-col overflow-hidden">
        <header className="flex items-center justify-end p-4 border-b border-titanium-800 bg-titanium-900/50">
          <div className="relative">
            <button
              onClick={() => setShowNotifications(!showNotifications)}
              className="relative p-2 text-titanium-400 hover:text-titanium-200 transition-colors rounded-lg hover:bg-titanium-800"
              aria-label="Notifications"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
              </svg>
              {unreadCount > 0 && (
                <span className="absolute -top-1 -right-1 w-4 h-4 bg-accent-500 text-white text-xs rounded-full flex items-center justify-center">
                  {unreadCount > 9 ? '9+' : unreadCount}
                </span>
              )}
            </button>

            <NotificationsPanel
              isOpen={showNotifications}
              onClose={() => setShowNotifications(false)}
            />
          </div>
        </header>

        <main className="flex-1 overflow-auto">
          <div className="p-6 max-w-7xl mx-auto">
            {children}
          </div>
        </main>
      </div>
    </div>
  )
}
