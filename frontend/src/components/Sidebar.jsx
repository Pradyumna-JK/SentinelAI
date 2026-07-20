import { NavLink } from 'react-router-dom'

const NAV_ITEMS = [
  { to: '/dashboard', label: 'Dashboard', icon: DashboardIcon },
  { to: '/cctv', label: 'Camera Monitoring', icon: CameraIcon },
  { to: '/alerts', label: 'Alerts', icon: AlertIcon },
  { to: '/compliance', label: 'Compliance Copilot', icon: ComplianceIcon },
  { to: '/incidents', label: 'Incident Reports', icon: IncidentIcon },
  { to: '/analytics', label: 'Analytics', icon: AnalyticsIcon },
  { to: '/settings', label: 'Settings', icon: SettingsIcon },
]

export default function Sidebar({ onNavigate }) {
  return (
    <nav aria-label="Primary" className="flex h-full flex-col gap-1 p-3">
      {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
        <NavLink
          key={to}
          to={to}
          onClick={onNavigate}
          className={({ isActive }) =>
            `focus-ring flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
              isActive
                ? 'bg-safety-orange/12 text-safety-orange'
                : 'text-slate-400 hover:bg-navy-700 hover:text-slate-100'
            }`
          }
          end
        >
          {({ isActive }) => (
            <>
              <Icon active={isActive} />
              <span>{label}</span>
            </>
          )}
        </NavLink>
      ))}
    </nav>
  )
}

function iconBase(active) {
  return `h-5 w-5 shrink-0 ${active ? 'text-safety-orange' : 'text-slate-500'}`
}

function DashboardIcon({ active }) {
  return (
    <svg className={iconBase(active)} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.6} d="M3 13h4v7H3v-7zM10 4h4v16h-4V4zM17 9h4v11h-4V9z" />
    </svg>
  )
}
function CameraIcon({ active }) {
  return (
    <svg className={iconBase(active)} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.6} d="M15 10l4.55-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.45.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
    </svg>
  )
}
function AlertIcon({ active }) {
  return (
    <svg className={iconBase(active)} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.6} d="M12 9v3.75m0 3.75h.007M10.29 3.86L1.82 18a1.5 1.5 0 001.29 2.25h17.78a1.5 1.5 0 001.29-2.25L13.71 3.86a1.5 1.5 0 00-2.42 0z" />
    </svg>
  )
}
function ComplianceIcon({ active }) {
  return (
    <svg className={iconBase(active)} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.6} d="M8 12h8m-8 4h5M7 4h10a2 2 0 012 2v13.5a.5.5 0 01-.79.41L15 17.5l-3.21 2.41a.5.5 0 01-.58 0L8 17.5l-3.21 2.41A.5.5 0 014 19.5V6a2 2 0 012-2z" />
    </svg>
  )
}
function IncidentIcon({ active }) {
  return (
    <svg className={iconBase(active)} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.6} d="M9 12h6m-6 4h6m-7 5h8a2 2 0 002-2V7.828a2 2 0 00-.586-1.414l-3.828-3.828A2 2 0 0012.172 2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
    </svg>
  )
}
function AnalyticsIcon({ active }) {
  return (
    <svg className={iconBase(active)} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.6} d="M3 3v18h18M7 15l3.5-4.5 3 3L18 8" />
    </svg>
  )
}
function SettingsIcon({ active }) {
  return (
    <svg className={iconBase(active)} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.6} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.99.608 2.296.087 2.572-1.065z" />
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.6} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
    </svg>
  )
}
