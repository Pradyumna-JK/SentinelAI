import { useState } from 'react'
import { Outlet, useLocation } from 'react-router-dom'
import Navbar from '../components/Navbar'
import Sidebar from '../components/Sidebar'
import ToastContainer from '../components/Toast'
import { currentUser } from '../data/mockData'

const PAGE_TITLES = {
  '/dashboard': 'Dashboard',
  '/cctv': 'Camera Monitoring',
  '/alerts': 'Alert Center',
  '/compliance': 'Compliance Copilot',
  '/incidents': 'Incident Reports',
  '/analytics': 'Analytics',
  '/settings': 'Settings',
}

export default function MainLayout() {
  const [mobileNavOpen, setMobileNavOpen] = useState(false)
  const location = useLocation()
  const pageTitle = PAGE_TITLES[location.pathname] || ''

  return (
    <div className="flex min-h-screen bg-navy-900">
      {/* Desktop sidebar */}
      <aside className="hidden w-64 shrink-0 border-r border-border bg-navy-900 md:block">
        <div className="sticky top-0">
          <Sidebar />
        </div>
      </aside>

      {/* Mobile drawer */}
      {mobileNavOpen && (
        <div className="fixed inset-0 z-50 md:hidden">
          <div
            className="absolute inset-0 bg-navy-950/70"
            onClick={() => setMobileNavOpen(false)}
            aria-hidden="true"
          />
          <div className="absolute inset-y-0 left-0 w-64 border-r border-border bg-navy-900 shadow-panel">
            <div className="flex h-16 items-center justify-between border-b border-border px-4">
              <span className="text-sm font-semibold text-slate-100">Menu</span>
              <button
                onClick={() => setMobileNavOpen(false)}
                aria-label="Close navigation menu"
                className="focus-ring rounded-lg p-1.5 text-slate-400 hover:bg-navy-700 hover:text-slate-100"
              >
                ✕
              </button>
            </div>
            <Sidebar onNavigate={() => setMobileNavOpen(false)} />
          </div>
        </div>
      )}

      <div className="flex min-w-0 flex-1 flex-col">
        <Navbar user={currentUser} pageTitle={pageTitle} onMenuClick={() => setMobileNavOpen(true)} />
        <main className="flex-1 p-4 sm:p-6">
          <Outlet />
        </main>
      </div>

      <ToastContainer />
    </div>
  )
}
