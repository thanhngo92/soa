import { useState, useEffect, useRef } from 'react'
import { getTuitionApi } from '@/services/tuitionService'
import { initiatePaymentApi, confirmPaymentApi } from '@/services/paymentService'
import useAuth from '@/hooks/useAuth'
import { formatCurrency, formatDate } from '@/utils/formatters'
import { isValidMssv } from '@/utils/validators'
import OtpModal from '@/components/OtpModal'
import ReceiptModal from '@/components/ReceiptModal'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  Search,
  Wallet,
  GraduationCap,
  CreditCard,
  AlertCircle,
  Loader2,
  CheckCircle2,
  Mail,
  Phone,
  User,
  ShieldCheck
} from 'lucide-react'

const generateIdempotencyKey = (paymentId) =>
  typeof crypto !== 'undefined' && crypto.randomUUID
    ? crypto.randomUUID()
    : `pay-${paymentId}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`

const TERMINAL_OTP_CODES = new Set([
  'OTP_MAX_ATTEMPTS_EXCEEDED',
  'OTP_EXPIRED',
  'PAYMENT_NOT_PENDING',
])

const SAMPLE_STUDENTS = ['521H0001', '521H0002', '522H0041', '523H0089']

export default function TuitionPaymentPage() {
  const { user: authUser, refreshProfile } = useAuth()
  const profile = (authUser && authUser.balance !== undefined) ? authUser : null

  const [mssv, setMssv] = useState('')
  const [tuition, setTuition] = useState(null)
  const [paymentId, setPaymentId] = useState(null)
  const [idempotencyKey, setIdempotencyKey] = useState('')
  const [receipt, setReceipt] = useState(null)
  const [showOtp, setShowOtp] = useState(false)
  const [otpLocked, setOtpLocked] = useState(false)
  const [agreedTerms, setAgreedTerms] = useState(false)
  const [error, setError] = useState('')
  const [otpError, setOtpError] = useState('')
  const [searchLoading, setSearchLoading] = useState(false)
  const [payLoading, setPayLoading] = useState(false)
  const searchSeqRef = useRef(0)

  // Tra cứu học phí tự động & Chống Race Condition
  const executeSearch = async (studentId) => {
    const trimmedMssv = studentId.trim().toUpperCase()
    if (!isValidMssv(trimmedMssv)) return

    const seq = ++searchSeqRef.current
    setError('')
    setOtpError('')
    setOtpLocked(false)
    setSearchLoading(true)

    try {
      const res = await getTuitionApi(trimmedMssv)
      if (seq === searchSeqRef.current) {
        setTuition(res.data.data)
        setAgreedTerms(false)
      }
    } catch (err) {
      if (seq === searchSeqRef.current) {
        setTuition(null)
        setAgreedTerms(false)
        setError(err.response?.data?.error?.message || 'Không tìm thấy thông tin sinh viên')
      }
    } finally {
      if (seq === searchSeqRef.current) {
        setSearchLoading(false)
      }
    }
  }

  useEffect(() => {
    const trimmed = mssv.trim().toUpperCase()
    if (!isValidMssv(trimmed)) {
      if (!trimmed) {
        setTuition(null)
        setError('')
      }
      return
    }
    if (tuition && tuition.student_id === trimmed) return

    const timer = setTimeout(() => {
      executeSearch(trimmed)
    }, 400)
    return () => clearTimeout(timer)
  }, [mssv, tuition?.student_id])

  const handleSearch = (e) => {
    if (e) e.preventDefault()
    const trimmed = mssv.trim().toUpperCase()
    if (!isValidMssv(trimmed)) {
      setError('Mã sinh viên cần từ 6 đến 10 ký tự')
      return
    }
    executeSearch(trimmed)
  }

  const handleSelectSample = (sampleMssv) => {
    if (mssv === sampleMssv && tuition && tuition.student_id === sampleMssv) return
    setMssv(sampleMssv)
    executeSearch(sampleMssv)
  }

  const handleInitiate = async () => {
    if (!tuition || tuition.status === 'PAID') return
    setError('')
    setOtpError('')
    setOtpLocked(false)
    setPayLoading(true)
    try {
      const res = await initiatePaymentApi(tuition.student_id)
      const newPaymentId = res.data.data.payment_id
      setPaymentId(newPaymentId)
      setIdempotencyKey(generateIdempotencyKey(newPaymentId))
      setShowOtp(true)
    } catch (err) {
      setError(err.response?.data?.error?.message || 'Không thể khởi tạo giao dịch')
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
      setOtpLocked(false)
      setReceipt(res.data.data)
      setTuition(null)
      refreshProfile()
    } catch (err) {
      const errCode = err.response?.data?.error?.code
      if (TERMINAL_OTP_CODES.has(errCode)) {
        setOtpLocked(true)
      } else {
        setIdempotencyKey(generateIdempotencyKey(paymentId))
      }
      setOtpError(err.response?.data?.error?.message || 'Xác nhận OTP thất bại')
    } finally {
      setPayLoading(false)
    }
  }

  const isBalanceSufficient = profile && tuition ? profile.balance >= tuition.amount : true
  const isPayable = tuition && tuition.status === 'UNPAID' && isBalanceSufficient && agreedTerms

  return (
    <div className="container mx-auto max-w-5xl py-6 px-4 sm:px-6 space-y-6">
      {/* Tiêu đề ngắn gọn, thoáng mắt */}
      <div>
        <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
          <GraduationCap className="h-6 w-6 text-primary shrink-0" />
          <span>Thanh toán học phí</span>
        </h1>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-start">
        {/* CỘT TRÁI (7 cột): Thông tin người nộp (Nhóm a) & Thông tin học phí (Nhóm b) */}
        <div className="lg:col-span-7 space-y-5">
          {/* Nhóm a. Thông tin người nộp tiền */}
          <Card className="shadow-xs border">
            <CardHeader className="py-3 px-4 border-b bg-muted/20">
              <CardTitle className="text-sm font-semibold text-foreground flex items-center gap-1.5">
                <User className="h-4 w-4 text-primary shrink-0" />
                <span>a. Người nộp tiền</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="p-4">
              {profile ? (
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <span className="text-xs text-muted-foreground block">Họ và tên</span>
                    <span className="font-semibold text-foreground">{profile.full_name}</span>
                  </div>
                  <div>
                    <span className="text-xs text-muted-foreground block">Số điện thoại</span>
                    <span className="text-foreground">{profile.phone || '---'}</span>
                  </div>
                  <div className="truncate">
                    <span className="text-xs text-muted-foreground block">Email</span>
                    <span className="text-foreground truncate block">{profile.email}</span>
                  </div>
                  <div>
                    <span className="text-xs text-muted-foreground block">Số dư khả dụng</span>
                    <span className="font-bold text-primary font-mono">{formatCurrency(profile.balance)}</span>
                  </div>
                </div>
              ) : (
                <div className="py-2 text-center text-xs text-muted-foreground">Đang tải...</div>
              )}
            </CardContent>
          </Card>

          {/* Nhóm b. Thông tin học phí */}
          <Card className="shadow-xs border">
            <CardHeader className="py-3 px-4 border-b bg-muted/20">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm font-semibold text-foreground flex items-center gap-1.5">
                  <Search className="h-4 w-4 text-primary shrink-0" />
                  <span>b. Thông tin học phí</span>
                </CardTitle>
                {searchLoading && (
                  <span className="flex items-center gap-1 text-xs text-muted-foreground">
                    <Loader2 className="h-3 w-3 animate-spin" />
                    <span>Đang tìm...</span>
                  </span>
                )}
              </div>
            </CardHeader>

            <CardContent className="p-4 space-y-3">
              {/* Form tra cứu MSSV */}
              <form onSubmit={handleSearch} className="flex gap-2">
                <Input
                  id="mssv"
                  type="text"
                  placeholder="Nhập mã sinh viên (VD: 521H0001)..."
                  value={mssv}
                  onChange={(e) => {
                    setMssv(e.target.value.toUpperCase())
                    if (error) setError('')
                  }}
                  className="font-mono uppercase h-10 text-sm"
                />
                <Button type="submit" size="sm" className="h-10 px-4 font-medium" disabled={searchLoading || !mssv.trim()}>
                  Tra cứu
                </Button>
              </form>

              {/* Gợi ý MSSV mẫu gọn nhẹ */}
              <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                <span>Mẫu:</span>
                {SAMPLE_STUDENTS.map((s) => (
                  <button
                    key={s}
                    type="button"
                    onClick={() => handleSelectSample(s)}
                    className={`px-2 py-0.5 rounded border font-mono text-[11px] transition-colors cursor-pointer ${
                      mssv === s
                        ? 'border-primary bg-primary text-primary-foreground font-semibold'
                        : 'border-border bg-muted/40 hover:bg-muted text-foreground'
                    }`}
                  >
                    {s}
                  </button>
                ))}
              </div>

              {/* Thông báo lỗi */}
              {error && (
                <div className="flex items-center gap-2 p-2.5 text-xs text-red-800 dark:text-red-200 bg-red-50 dark:bg-red-950/40 rounded-lg border border-red-200 dark:border-red-900/50">
                  <AlertCircle className="h-3.5 w-3.5 shrink-0" />
                  <span>{error}</span>
                </div>
              )}

              {/* Kết quả học phí sinh viên */}
              {tuition ? (
                <div className={`rounded-lg border bg-card p-4 space-y-3 transition-opacity duration-150 ${searchLoading ? 'opacity-60 pointer-events-none' : ''}`}>
                  <div className="flex items-center justify-between gap-2 pb-2.5 border-b">
                    <div>
                      <span className="font-bold text-base text-foreground block">{tuition.student_name}</span>
                      <span className="font-mono text-xs text-muted-foreground">MSSV: {tuition.student_id}</span>
                    </div>
                    <Badge variant={tuition.status === 'PAID' ? 'success' : 'destructive'} className="text-xs">
                      {tuition.status === 'PAID' ? 'ĐÃ ĐÓNG' : 'CHƯA ĐÓNG'}
                    </Badge>
                  </div>

                  <div className="grid grid-cols-2 gap-2 text-xs text-muted-foreground">
                    <div>Ngành: <span className="font-medium text-foreground">{tuition.major}</span></div>
                    <div>Học kỳ: <span className="font-medium text-foreground">{tuition.semester}</span></div>
                  </div>

                  <div className="flex items-baseline justify-between pt-1">
                    <span className="text-xs text-muted-foreground">Học phí cần đóng:</span>
                    <span className="text-xl font-bold text-primary font-mono">{formatCurrency(tuition.amount)}</span>
                  </div>

                  {tuition.status === 'PAID' && tuition.paid_at && (
                    <p className="text-xs text-emerald-700 dark:text-emerald-400 font-medium">
                      ✓ Đã thanh toán: {formatDate(tuition.paid_at)}
                    </p>
                  )}
                </div>
              ) : !searchLoading && !error ? (
                <div className="py-6 text-center text-xs text-muted-foreground border border-dashed rounded-lg">
                  Nhập mã số sinh viên để hiển thị học phí
                </div>
              ) : null}
            </CardContent>
          </Card>
        </div>

        {/* CỘT PHẢI (5 cột): Nhóm c. Thông tin thanh toán */}
        <div className="lg:col-span-5 space-y-5 lg:sticky lg:top-20">
          <Card className="shadow-xs border">
            <CardHeader className="py-3 px-4 border-b bg-muted/20">
              <CardTitle className="text-sm font-semibold text-foreground flex items-center gap-1.5">
                <CreditCard className="h-4 w-4 text-primary shrink-0" />
                <span>c. Thông tin thanh toán</span>
              </CardTitle>
            </CardHeader>

            <CardContent className="p-4 space-y-3.5 text-sm">
              <div className="space-y-2 rounded-lg bg-muted/30 p-3 border text-xs">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Số tiền thanh toán</span>
                  <span className="font-mono font-bold text-foreground text-sm">
                    {tuition ? formatCurrency(tuition.amount) : '---'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Số dư khả dụng</span>
                  <span className="font-mono text-foreground">
                    {profile ? formatCurrency(profile.balance) : '---'}
                  </span>
                </div>
                {tuition && profile && (
                  <div className="flex justify-between pt-1.5 border-t">
                    <span className="text-muted-foreground">Số dư còn lại</span>
                    <span className={`font-mono font-semibold ${isBalanceSufficient ? 'text-emerald-700 dark:text-emerald-400' : 'text-destructive'}`}>
                      {isBalanceSufficient ? formatCurrency(profile.balance - tuition.amount) : 'Không đủ số dư'}
                    </span>
                  </div>
                )}
              </div>

              {/* Phương thức xác thực */}
              <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                <ShieldCheck className="h-3.5 w-3.5 text-primary shrink-0" />
                <span>Xác thực bằng mã OTP qua Email</span>
              </div>

              {/* Điều khoản */}
              <label htmlFor="terms" className="flex items-start gap-2 text-xs text-muted-foreground cursor-pointer select-none">
                <input
                  type="checkbox"
                  id="terms"
                  checked={agreedTerms}
                  onChange={(e) => setAgreedTerms(e.target.checked)}
                  disabled={!tuition || tuition.status === 'PAID' || !isBalanceSufficient || payLoading}
                  className="mt-0.5 h-3.5 w-3.5 rounded border-gray-300 text-primary focus:ring-primary cursor-pointer shrink-0"
                />
                <span>Tôi xác nhận thông tin sinh viên và đồng ý với điều khoản thanh toán.</span>
              </label>

              {/* Cảnh báo trạng thái */}
              {tuition && tuition.status === 'PAID' && (
                <div className="p-2.5 rounded-lg bg-emerald-50 dark:bg-emerald-950/40 text-emerald-800 dark:text-emerald-200 text-xs border border-emerald-200 dark:border-emerald-900/50">
                  Khoản học phí này đã được thanh toán.
                </div>
              )}

              {tuition && tuition.status === 'UNPAID' && !isBalanceSufficient && (
                <div className="p-2.5 rounded-lg bg-red-50 dark:bg-red-950/40 text-red-800 dark:text-red-200 text-xs border border-red-200 dark:border-red-900/50">
                  Số dư khả dụng không đủ để thanh toán.
                </div>
              )}

              {/* Nút hành động */}
              <Button
                onClick={handleInitiate}
                disabled={!isPayable || payLoading}
                className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium h-10 text-sm shadow-xs mt-1"
                size="default"
              >
                {payLoading ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin mr-1.5" />
                    <span>Đang xử lý...</span>
                  </>
                ) : (
                  'Thanh toán học phí'
                )}
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Modal OTP */}
      <OtpModal
        open={showOtp}
        onConfirm={handleConfirm}
        onResend={handleInitiate}
        onCancel={() => {
          setShowOtp(false)
          setOtpError('')
          setOtpLocked(false)
        }}
        loading={payLoading}
        error={otpError}
        locked={otpLocked}
        onClearError={() => setOtpError('')}
      />

      {/* Modal Biên lai */}
      <ReceiptModal
        open={!!receipt}
        data={receipt}
        onClose={() => setReceipt(null)}
      />
    </div>
  )
}
