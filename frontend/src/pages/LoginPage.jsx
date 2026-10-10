import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { loginApi } from '@/services/authService'
import useAuth from '@/hooks/useAuth'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'
import { AlertCircle, Loader2 } from 'lucide-react'

export default function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ username: '', password: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const res = await loginApi(form.username, form.password)
      login(res.data.data.access_token)
      navigate('/')
    } catch (err) {
      setError(err.response?.data?.error?.message || 'Tài khoản hoặc mật khẩu không chính xác')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-muted/20">
      <Card className="w-full max-w-md shadow-sm border bg-card">
        <CardHeader className="space-y-1.5 text-center pb-6">
          <CardTitle className="text-2xl font-bold tracking-tight text-foreground">
            iBanking TDTU
          </CardTitle>
          <CardDescription className="text-sm text-muted-foreground">
            Đăng nhập tài khoản
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="username">Tên đăng nhập</Label>
              <Input
                id="username"
                type="text"
                placeholder="Tên đăng nhập"
                autoComplete="username"
                value={form.username}
                onChange={(e) => setForm({ ...form, username: e.target.value })}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Mật khẩu</Label>
              <Input
                id="password"
                type="password"
                placeholder="Mật khẩu"
                autoComplete="current-password"
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
                required
              />
            </div>

            {error && (
              <div className="flex items-center gap-2 p-3 text-sm text-destructive bg-destructive/10 rounded-lg border border-destructive/20">
                <AlertCircle className="h-4 w-4 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <Button type="submit" className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium h-11 text-base shadow-sm" disabled={loading}>
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Đang xử lý...
                </>
              ) : (
                'Đăng nhập'
              )}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
