import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { loginApi } from '@/services/authService'
import useAuth from '@/hooks/useAuth'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'
import { GraduationCap, AlertCircle, Loader2 } from 'lucide-react'

export default function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ username: 'sv.nguyen', password: 'Test@123' })
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
    <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center p-4 bg-muted/20">
      <Card className="w-full max-w-md shadow-lg border-muted">
        <CardHeader className="space-y-2 text-center pb-6">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-primary text-primary-foreground shadow-md">
            <GraduationCap className="h-6 w-6" />
          </div>
          <CardTitle className="text-2xl font-bold tracking-tight">Cổng iBanking TDTU</CardTitle>
          <CardDescription>Đăng nhập tài khoản ngân hàng để đóng học phí</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="username">Tên tài khoản</Label>
              <Input
                id="username"
                type="text"
                placeholder="sv.nguyen"
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
                placeholder="••••••••"
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

            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Đang đăng nhập...
                </>
              ) : (
                'Đăng nhập'
              )}
            </Button>
          </form>

          <div className="mt-6 pt-4 border-t text-xs text-muted-foreground space-y-1">
            <p className="font-semibold text-foreground">Tài khoản thử nghiệm:</p>
            <p className="font-mono">sv.nguyen / Test@123 (Số dư: 7.500.000 đ)</p>
            <p className="font-mono">sv.tran / Test@123 (Số dư: 2.300.000 đ)</p>
            <p className="font-mono">sv.le / Ibank@456 (Số dư: 12.000.000 đ)</p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
