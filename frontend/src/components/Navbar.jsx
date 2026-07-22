import logo from '../assets/logo.svg'

const ROLE_LABEL = {
  admin: 'Platform Administrator',
  safety_manager: 'Safety Manager',
  site_operator: 'Site Operator',
  compliance_officer: 'Compliance Officer',
  viewer: 'Viewer',
}

export default function Navbar({ user, pageTitle, onMenuClick, onLogout }) {
  const displayUser = user || { full_name: 'Signed in user', role: 'Viewer' }
  return (
    <header className="sticky top-0 z-40 flex h-16 items-center justify-between gap-3 border-b border-border bg-navy-900/95 px-4 backdrop-blur">
      <div className="flex items-center gap-3">
        <button
          onClick={onMenuClick}
          aria-label="Open navigation menu"
          className="focus-ring rounded-lg p-2 text-slate-400 hover:bg-navy-700 hover:text-slate-100 md:hidden"
        >
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>
        <div className="flex items-center gap-2.5">
          <img src={logo} alt="" className="h-8 w-8" />
          <div className="hidden sm:block">
            <p className="text-sm font-semibold leading-tight text-slate-100">SentinelAI</p>
            <p className="text-[11px] leading-tight text-slate-500">Industrial Safety Intelligence</p>
          </div>
        </div>
        {pageTitle && (
          <>
            <span className="hidden h-5 w-px bg-border sm:block" />
            <h1 className="hidden text-sm font-medium text-slate-300 sm:block">{pageTitle}</h1>
          </>
        )}
      </div>

      <div className="flex items-center gap-3">
        <span className="hidden items-center gap-1.5 rounded-full border border-safety-green/30 bg-safety-green/10 px-2.5 py-1 text-xs text-safety-green sm:flex">
          <span className="h-1.5 w-1.5 rounded-full bg-safety-green" />
          All systems normal
        </span>
        <div className="flex items-center gap-2.5 rounded-lg border border-border bg-navy-800 px-2.5 py-1.5">
          <div className="flex h-7 w-7 items-center justify-center rounded-full bg-safety-orange/15 text-xs font-semibold text-safety-orange">
            {displayUser.full_name
              .split(' ')
              .map((n) => n[0])
              .join('')
              .slice(0, 2)}
          </div>
          <div className="hidden text-left leading-tight sm:block">
            <p className="text-xs font-medium text-slate-100">{displayUser.full_name}</p>
            <p className="text-[11px] text-slate-500">{ROLE_LABEL[displayUser.role] || displayUser.role}</p>
          </div>
        </div>
        {onLogout && (
          <button
            onClick={onLogout}
            aria-label="Sign out"
            className="focus-ring rounded-lg p-2 text-slate-400 hover:bg-navy-700 hover:text-slate-100"
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.8}
                d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V6a3 3 0 013-3h4a3 3 0 013 3v1"
              />
            </svg>
          </button>
        )}
      </div>
    </header>
  )
}
