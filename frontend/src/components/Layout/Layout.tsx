import { ReactNode } from 'react'
import { NavLink } from 'react-router-dom'

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
]

export default function Layout({ children }: LayoutProps) {
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

      <main className="flex-1 overflow-auto">
        <div className="p-6 max-w-7xl mx-auto">
          {children}
        </div>
      </main>
    </div>
  )
}
