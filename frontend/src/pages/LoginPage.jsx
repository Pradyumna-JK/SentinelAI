import { useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import logo from '../assets/logo.svg'
import Button from '../components/Button'
import * as authService from '../services/authService'

export default function LoginPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const redirectTo = location.state?.from || '/dashboard'

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await authService.login(email, password)
      navigate(redirectTo, { replace: true })
    } catch (err) {
      setError(err.message || 'Invalid email or password')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-navy-900 px-4">
      <div className="w-full max-w-sm rounded-xl border border-border bg-navy-800 p-6 shadow-panel">
        <div className="mb-6 flex flex-col items-center gap-2 text-center">
          <img src={logo} alt="" className="h-10 w-10" />
          <h1 className="text-lg font-semibold text-slate-100">SentinelAI</h1>
          <p className="text-xs text-slate-500">Industrial Safety Intelligence Platform</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="email" className="mb-1 block text-xs font-medium text-slate-400">
              Email
            </label>
            <input
              id="email"
              type="email"
              required
              autoComplete="username"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="focus-ring w-full rounded-lg border border-border bg-navy-900 px-3 py-2 text-sm text-slate-100"
              placeholder="you@company.com"
            />
          </div>
          <div>
            <label htmlFor="password" className="mb-1 block text-xs font-medium text-slate-400">
              Password
            </label>
            <input
              id="password"
              type="password"
              required
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="focus-ring w-full rounded-lg border border-border bg-navy-900 px-3 py-2 text-sm text-slate-100"
              placeholder="••••••••"
            />
          </div>

          {error && (
            <p role="alert" className="rounded-lg border border-safety-red/30 bg-safety-red/10 px-3 py-2 text-xs text-safety-red">
              {error}
            </p>
          )}

          <Button type="submit" variant="primary" className="w-full" loading={loading} disabled={loading}>
            Sign in
          </Button>
        </form>
      </div>
    </div>
  )
}
