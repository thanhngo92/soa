import { Link, useNavigate, useLocation } from 'react-router-dom'
import useAuth from '@/hooks/useAuth'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { GraduationCap, History, LogOut } from 'lucide-react'

export default function Navbar() {
  const { isAuthenticated, user, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  if (!isAuthenticated) return null

  return (
    <header className="sticky top-0 z-40 w-full border-b bg-card/95 backdrop-blur supports-[backdrop-filter]:bg-card/75">
      <div className="container mx-auto flex h-16 max-w-4xl items-center justify-between px-4 sm:px-6">
        <div className="flex items-center gap-6">
          <Link to="/" className="flex items-center gap-2.5 font-bold text-primary tracking-tight text-lg">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary text-primary-foreground shadow-sm">
              <GraduationCap className="h-5 w-5" />
            </div>
            <span>iBanking TDTU</span>
          </Link>
          <nav className="flex items-center gap-1.5 text-sm font-medium">
            <Button
              asChild
              variant={location.pathname === '/' ? 'secondary' : 'ghost'}
              size="sm"
            >
              <Link to="/" className="flex items-center gap-1.5">
                <GraduationCap className="h-4 w-4" />
                <span>Thanh toán</span>
              </Link>
            </Button>
            <Button
              asChild
              variant={location.pathname === '/history' ? 'secondary' : 'ghost'}
              size="sm"
            >
              <Link to="/history" className="flex items-center gap-1.5">
                <History className="h-4 w-4" />
                <span>Lịch sử</span>
              </Link>
            </Button>
          </nav>
        </div>

        <div className="flex items-center gap-3">
          {user?.username && (
            <Badge variant="outline" className="hidden sm:inline-flex font-mono text-xs font-normal text-muted-foreground">
              {user.username}
            </Badge>
          )}
          <Button variant="ghost" size="sm" onClick={handleLogout} className="gap-1.5 text-muted-foreground hover:text-destructive">
            <LogOut className="h-4 w-4" />
            <span>Đăng xuất</span>
          </Button>
        </div>
      </div>
    </header>
  )
}
