import { useState, useEffect } from 'react'
import { getTuitionApi } from '@/services/tuitionService'
import { initiatePaymentApi, confirmPaymentApi } from '@/services/paymentService'
import { getMeApi } from '@/services/authService'
import { formatCurrency } from '@/utils/formatters'
import { isValidMssv } from '@/utils/validators'
import OtpModal from '@/components/OtpModal'
import ReceiptModal from '@/components/ReceiptModal'
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import {
  Search,
  Wallet,
  UserCheck,
  GraduationCap,
  CreditCard,
  AlertCircle,
  Loader2,
  CheckCircle2,
  Mail,
  Phone
} from 'lucide-react'

export default function TuitionPaymentPage() {
  const [profile, setProfile]   = useState(null)
  const [mssv, setMssv]         = useState('')
  const [tuition, setTuition]   = useState(null)
  const [paymentId, setPaymentId] = useState(null)
  const [idempotencyKey, setIdempotencyKey] = useState('')
  const [receipt, setReceipt]   = useState(null)
  const [showOtp, setShowOtp]   = useState(false)
  const [agreedTerms, setAgreedTerms] = useState(false)
  const [error, setError]       = useState('')
  const [otpError, setOtpError] = useState('')
  const [searchLoading, setSearchLoading] = useState(false)
  const [payLoading, setPayLoading]       = useState(false)

  const fetchProfile = async () => {
    try {
      const res = await getMeApi()
      setProfile(res.data.data)
    } catch {
      // Ignored
    }
  }

  useEffect(() => {
    fetchProfile()
  }, [])

  const executeSearch = async (studentId) => {
    const trimmedMssv = studentId.trim().toUpperCase()
    if (!isValidMssv(trimmedMssv)) {
      return
    }
    setError('')
    setOtpError('')
    setTuition(null)
    setAgreedTerms(false)
    setSearchLoading(true)
    try {
      const res = await getTuitionApi(trimmedMssv)
      setTuition(res.data.data)
    } catch (err) {
      setError(err.response?.data?.error?.message || 'Không tìm thấy thông tin sinh viên hoặc học phí')
    } finally {
      setSearchLoading(false)
    }
  }

  // Tự động tra cứu khi người dùng nhập đủ MSSV hợp lệ (Debounce 500ms)
  useEffect(() => {
    const trimmed = mssv.trim().toUpperCase()
    if (isValidMssv(trimmed)) {
      const timer = setTimeout(() => {
        executeSearch(trimmed)
      }, 500)
      return () => clearTimeout(timer)
    }
  }, [mssv])

  const handleSearch = (e) => {
    if (e) e.preventDefault()
    const trimmed = mssv.trim().toUpperCase()
    if (!isValidMssv(trimmed)) {
      setError('Mã sinh viên không hợp lệ (cần từ 6 đến 10 ký tự chữ và số)')
      return
    }
    executeSearch(trimmed)
  }

  const handleInitiate = async () => {
    setError('')
    setOtpError('')
    setPayLoading(true)
    try {
      const res = await initiatePaymentApi(tuition.student_id)
      setPaymentId(res.data.data.payment_id)
      const key = typeof crypto !== 'undefined' && crypto.randomUUID
        ? crypto.randomUUID()
        : `pay-${res.data.data.payment_id}-${Date.now()}`
      setIdempotencyKey(key)
      setShowOtp(true)
    } catch (err) {
      setError(err.response?.data?.error?.message || 'Không thể khởi tạo giao dịch thanh toán')
    } finally {
      setPayLoading(false)
    }
  }

  const handleConfirm = async (otpCode) => {
    setPayLoading(true)
    setOtpError('')
    try {
      const res = await confirmPaymentApi(paymentId, otpCode, idempotencyKey)
      setShowOtp(false)
      setReceipt(res.data.data)
      setTuition(null)
      fetchProfile() // Refresh balance after payment
    } catch (err) {
      setOtpError(err.response?.data?.error?.message || 'Xác nhận OTP thất bại')
    } finally {
      setPayLoading(false)
    }
  }

  return (
    <div className="container mx-auto max-w-4xl py-8 px-4 sm:px-6 space-y-6">
      {/* 1. Thẻ tài khoản thanh toán */}
      {profile && (
        <Card className="shadow-sm border">
          <CardContent className="p-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div className="flex items-center gap-3.5">
              <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-primary/10 text-primary shrink-0">
                <Wallet className="h-5 w-5" />
              </div>
              <div className="space-y-0.5">
                <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Tài khoản thanh toán</p>
                <div className="flex items-center gap-2 flex-wrap">
                  <h2 className="text-base font-bold text-foreground">{profile.full_name}</h2>
                  <Badge variant="secondary" className="font-mono text-xs">
                    {profile.username}
                  </Badge>
                </div>
                <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted-foreground pt-0.5">
                  {profile.email && (
                    <span className="flex items-center gap-1">
                      <Mail className="h-3.5 w-3.5 text-muted-foreground/70" />
                      <span>{profile.email}</span>
                    </span>
                  )}
                  {profile.email && profile.phone && <span className="text-border">•</span>}
                  {profile.phone && (
                    <span className="flex items-center gap-1">
                      <Phone className="h-3.5 w-3.5 text-muted-foreground/70" />
                      <span>{profile.phone}</span>
                    </span>
                  )}
                </div>
              </div>
            </div>
            <div className="sm:text-right w-full sm:w-auto pt-2 sm:pt-0 border-t sm:border-0 border-border/60">
              <p className="text-xs text-muted-foreground">Số dư khả dụng</p>
              <p className="text-2xl font-black text-primary tracking-tight">{formatCurrency(profile.balance)}</p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* 2. Khung tra cứu học phí */}
      <Card className="shadow-sm border">
        <CardHeader className="pb-3">
          <CardTitle className="text-lg font-bold text-foreground flex items-center gap-2">
            <Search className="h-5 w-5 text-primary" />
            <span>Tra cứu học phí</span>
          </CardTitle>
          <CardDescription>
            Nhập mã sinh viên để truy xuất thông tin học phí trực tiếp từ hệ thống
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <form onSubmit={handleSearch} className="flex flex-col sm:flex-row gap-3">
            <div className="relative flex-1">
              <Input
                id="mssv"
                type="text"
                placeholder="Nhập mã sinh viên..."
                value={mssv}
                onChange={(e) => setMssv(e.target.value.toUpperCase())}
                required
                className="font-mono uppercase placeholder:normal-case h-11"
              />
            </div>
            <Button type="submit" size="lg" className="sm:w-auto h-11 font-medium" disabled={searchLoading || !mssv.trim()}>
              {searchLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  <span>Đang tra cứu...</span>
                </>
              ) : (
                'Tra cứu'
              )}
            </Button>
          </form>

          {error && (
            <div className="flex items-start gap-2 p-3 text-sm text-red-800 dark:text-red-200 bg-red-50 dark:bg-red-950/40 rounded-lg border border-red-200 dark:border-red-900/50" role="alert">
              <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}
        </CardContent>
      </Card>

      {/* 3. Chi tiết hóa đơn học phí & Xác nhận thanh toán */}
      {tuition ? (
        <Card className="shadow-sm border">
          <CardHeader className="pb-4">
            <div className="flex items-start justify-between gap-3">
              <div>
                <CardTitle className="text-xl font-bold flex items-center gap-2">
                  <GraduationCap className="h-5 w-5 text-primary shrink-0" />
                  <span>{tuition.student_name}</span>
                </CardTitle>
                <CardDescription className="font-mono mt-1 text-xs">MSSV: {tuition.student_id}</CardDescription>
              </div>
              <Badge variant={tuition.status === 'PAID' ? 'success' : 'destructive'}>
                {tuition.status === 'PAID' ? 'ĐÃ ĐÓNG' : 'CHƯA ĐÓNG'}
              </Badge>
            </div>
          </CardHeader>

          <CardContent className="space-y-6">
            <dl className="space-y-3 divide-y divide-border/60 text-sm">
              <div className="flex items-center justify-between py-2">
                <dt className="text-muted-foreground">Ngành học</dt>
                <dd className="font-semibold text-foreground">{tuition.major}</dd>
              </div>
              <div className="flex items-center justify-between py-2">
                <dt className="text-muted-foreground">Học kỳ</dt>
                <dd className="font-semibold text-foreground">{tuition.semester}</dd>
              </div>
              <div className="flex items-baseline justify-between pt-3">
                <dt className="text-sm font-medium text-foreground">Số tiền học phí</dt>
                <dd className="text-2xl font-black text-primary tracking-tight">
                  {formatCurrency(tuition.amount)}
                </dd>
              </div>
            </dl>

            {/* c. Thông tin thanh toán & Thỏa thuận điều khoản */}
            {tuition.status === 'UNPAID' && (
              <div className="space-y-4 pt-2 border-t border-border">
                <div className="space-y-1">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
                    Thông tin thanh toán
                  </h4>
                  <p className="text-xs text-muted-foreground">
                    Hệ thống chỉ cho phép thanh toán toàn bộ khoản học phí, không thực hiện thanh toán một phần.
                  </p>
                </div>

                <div className="rounded-lg bg-muted/40 p-3.5 space-y-2.5 text-sm border">
                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground">Số dư khả dụng của người nộp tiền:</span>
                    <span className="font-bold text-foreground font-mono">
                      {profile ? formatCurrency(profile.balance) : '---'}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground">Số tiền cần thanh toán:</span>
                    <span className="font-bold text-primary font-mono text-base">
                      {formatCurrency(tuition.amount)}
                    </span>
                  </div>
                  {profile && (
                    <div className="flex items-center justify-between pt-1 border-t border-border/60 text-xs">
                      <span className="text-muted-foreground">Số dư dự kiến sau giao dịch:</span>
                      <span className={`font-semibold font-mono ${profile.balance >= tuition.amount ? 'text-emerald-700 dark:text-emerald-400' : 'text-destructive'}`}>
                        {profile.balance >= tuition.amount ? formatCurrency(profile.balance - tuition.amount) : 'Không đủ số dư'}
                      </span>
                    </div>
                  )}
                </div>

                <div className="space-y-3">
                  <label htmlFor="terms" className="flex items-start gap-2.5 text-xs text-muted-foreground leading-relaxed cursor-pointer select-none">
                    <input
                      type="checkbox"
                      id="terms"
                      checked={agreedTerms}
                      onChange={(e) => setAgreedTerms(e.target.checked)}
                      disabled={payLoading || (profile && profile.balance < tuition.amount)}
                      className="mt-0.5 h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary cursor-pointer shrink-0"
                    />
                    <span>
                      Tôi xác nhận thông tin sinh viên chính xác và đồng ý với các <strong>thỏa thuận và điều khoản của hệ thống</strong> để thực hiện trích nợ tài khoản thanh toán học phí.
                    </span>
                  </label>

                  {profile && profile.balance < tuition.amount && (
                    <div className="flex items-center gap-2 p-3 rounded-lg bg-red-50 dark:bg-red-950/40 text-red-800 dark:text-red-200 text-xs font-medium border border-red-200 dark:border-red-900/50" role="alert">
                      <AlertCircle className="h-4 w-4 shrink-0" />
                      <span>Số dư khả dụng không đủ để thực hiện giao dịch (Cần tối thiểu {formatCurrency(tuition.amount)}).</span>
                    </div>
                  )}
                </div>
              </div>
            )}
          </CardContent>

          <CardFooter className="pt-0">
            {tuition.status === 'UNPAID' ? (
              <Button
                onClick={handleInitiate}
                disabled={payLoading || !agreedTerms || !profile || (profile.balance < tuition.amount)}
                className="w-full gap-2 bg-blue-600 hover:bg-blue-700 text-white font-medium h-11 text-base shadow-sm"
                size="lg"
              >
                {payLoading ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <span>Đang xử lý...</span>
                  </>
                ) : (
                  <>
                    <CreditCard className="h-5 w-5" />
                    <span>Xác nhận giao dịch</span>
                  </>
                )}
              </Button>
            ) : (
              <div className="w-full flex items-center justify-center gap-2 text-sm font-semibold text-emerald-800 dark:text-emerald-300 py-2">
                <CheckCircle2 className="h-4 w-4 text-emerald-700 dark:text-emerald-400 shrink-0" />
                <span>Hóa đơn học phí đã được gạch nợ thành công</span>
              </div>
            )}
          </CardFooter>
        </Card>
      ) : (
        <Card className="border-dashed shadow-none text-center p-8 bg-card">
          <UserCheck className="mx-auto h-8 w-8 text-muted-foreground/50 mb-2" />
          <h3 className="font-semibold text-foreground">Chưa có dữ liệu</h3>
          <p className="text-sm text-muted-foreground mt-1 max-w-sm mx-auto">
            Nhập mã sinh viên để tra cứu hóa đơn học phí.
          </p>
        </Card>
      )}

      {showOtp && (
        <OtpModal
          open={showOtp}
          onConfirm={handleConfirm}
          onCancel={() => {
            setShowOtp(false)
            setOtpError('')
          }}
          loading={payLoading}
          error={otpError}
          onClearError={() => setOtpError('')}
        />
      )}

      {receipt && (
        <ReceiptModal
          open={!!receipt}
          data={receipt}
          onClose={() => setReceipt(null)}
        />
      )}
    </div>
  )
}
