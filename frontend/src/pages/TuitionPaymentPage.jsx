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
import { AlertCircle, Loader2 } from 'lucide-react'

const generateIdempotencyKey = (paymentId) =>
  typeof crypto !== 'undefined' && crypto.randomUUID
    ? crypto.randomUUID()
    : `pay-${paymentId}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`

const TERMINAL_OTP_CODES = new Set([
  'OTP_MAX_ATTEMPTS_EXCEEDED',
  'OTP_EXPIRED',
  'PAYMENT_NOT_PENDING',
  'INSUFFICIENT_BALANCE',
  'TUITION_ALREADY_PAID',
  'PAYMENT_FAILED',
])

const OTP_ERROR_TRANSLATIONS = {
  PAYMENT_NOT_PENDING: 'Phiên giao dịch này không còn ở trạng thái chờ xử lý.',
  OTP_MAX_ATTEMPTS_EXCEEDED: 'Bạn đã nhập sai mã OTP quá 3 lần. Giao dịch đã bị khóa.',
  OTP_EXPIRED: 'Mã OTP đã hết thời hạn hiệu lực (5 phút).',
  INSUFFICIENT_BALANCE: 'Số dư khả dụng không đủ (do vừa có giao dịch khác trừ tiền). Giao dịch này đã kết thúc.',
  TUITION_ALREADY_PAID: 'Khoản học phí này vừa được thanh toán bởi một giao dịch khác. Số tiền của bạn đã được hoàn trả đầy đủ.',
  PAYMENT_FAILED: 'Giao dịch không thành công (Khoản học phí đã được thanh toán bởi giao dịch khác). Số tiền đã được hoàn trả.',
}

// ============================================================================
// CỜ CẤU HÌNH KIỂM THỬ (TESTING FLAGS):
// - Đặt `true`: Chặn nút bấm ở Frontend nếu số dư không đủ (UI tự bảo vệ).
// - Đặt `false`: Cho phép bấm nút dù thiếu tiền để request gửi xuống Backend
//                kiểm tra và trả về mã lỗi 400 INSUFFICIENT_BALANCE.
// ============================================================================
const ENABLE_FRONTEND_BALANCE_GUARD = true

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
  const [payError, setPayError] = useState('')
  const [otpError, setOtpError] = useState('')
  const [searchLoading, setSearchLoading] = useState(false)
  const [payLoading, setPayLoading] = useState(false)
  const searchSeqRef = useRef(0)

  const executeSearch = async (studentId) => {
    const trimmedMssv = studentId.trim().toUpperCase()
    if (!isValidMssv(trimmedMssv)) return

    const seq = ++searchSeqRef.current
    setError('')
    setPayError('')
    setOtpError('')
    setOtpLocked(false)
    setSearchLoading(true)
    refreshProfile()

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
        const code = err.response?.data?.error?.code
        setError(
          code === 'STUDENT_NOT_FOUND'
            ? `Không tìm thấy thông tin học phí của mã sinh viên ${trimmedMssv}`
            : err.response?.data?.error?.message || 'Không tìm thấy thông tin sinh viên'
        )
      }
    } finally {
      if (seq === searchSeqRef.current) {
        setSearchLoading(false)
      }
    }
  }

  const handleSearch = (e) => {
    if (e) e.preventDefault()
    const trimmed = mssv.trim().toUpperCase()
    if (!trimmed) {
      setError('Vui lòng nhập mã số sinh viên')
      return
    }
    if (!isValidMssv(trimmed)) {
      setError('Mã số sinh viên cần từ 6 đến 10 ký tự chữ và số')
      return
    }
    executeSearch(trimmed)
  }

  useEffect(() => {
    const trimmed = mssv.trim().toUpperCase()
    if (!trimmed) {
      searchSeqRef.current += 1
      setTuition(null)
      setAgreedTerms(false)
      setError('')
      setSearchLoading(false)
    } else if (tuition && tuition.student_id !== trimmed) {
      setTuition(null)
      setAgreedTerms(false)
    }
  }, [mssv])

  const handleInitiate = async () => {
    if (!tuition || tuition.status === 'PAID') return
    setError('')
    setPayError('')
    setOtpError('')
    setOtpLocked(false)
    setPayLoading(true)
    refreshProfile()
    try {
      const res = await initiatePaymentApi(tuition.student_id)
      const newPaymentId = res.data.data.payment_id
      setPaymentId(newPaymentId)
      setIdempotencyKey(generateIdempotencyKey(newPaymentId))
      setShowOtp(true)
    } catch (err) {
      const code = err.response?.data?.error?.code
      const msgMap = {
        TUITION_ALREADY_PAID: 'Khoản học phí này đã được thanh toán.',
        INSUFFICIENT_BALANCE: 'Số dư khả dụng không đủ để thực hiện giao dịch.',
      }
      setPayError((code && msgMap[code]) || err.response?.data?.error?.message || 'Không thể khởi tạo giao dịch')
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
        refreshProfile()
        if (tuition?.student_id) {
          getTuitionApi(tuition.student_id)
            .then((r) => setTuition(r.data.data))
            .catch(() => {})
        }
      } else {
        setIdempotencyKey(generateIdempotencyKey(paymentId))
      }
      const rawMsg = err.response?.data?.error?.message
      const friendlyMsg = (errCode && OTP_ERROR_TRANSLATIONS[errCode]) || rawMsg || 'Xác nhận OTP thất bại'
      setOtpError(friendlyMsg)
    } finally {
      setPayLoading(false)
    }
  }

  const isBalanceSufficient = profile && tuition ? profile.balance >= tuition.amount : true
  const isPayable = tuition && tuition.status === 'UNPAID' && agreedTerms && (!ENABLE_FRONTEND_BALANCE_GUARD || isBalanceSufficient)

  return (
    <div className="container mx-auto max-w-5xl py-6 px-4 sm:px-6 space-y-5">
      <div>
        <h1 className="text-xl font-bold tracking-tight text-foreground">
          Thanh toán học phí
        </h1>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-start">
        {/* CỘT TRÁI (7 cột): Người nộp tiền & Thông tin học phí */}
        <div className="lg:col-span-7 space-y-5">
          {/* Nhóm 1: Người nộp tiền */}
          <Card className="shadow-xs border">
            <CardHeader className="pt-4 pb-2 px-4">
              <CardTitle className="text-sm font-semibold text-foreground">
                Người nộp tiền
              </CardTitle>
            </CardHeader>
            <CardContent className="p-4 pt-1">
              {profile ? (
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-sm">
                  <div>
                    <span className="text-xs text-muted-foreground block">Họ và tên</span>
                    <span className="font-semibold text-foreground">{profile.full_name}</span>
                  </div>
                  <div>
                    <span className="text-xs text-muted-foreground block">Số điện thoại</span>
                    <span className="text-foreground">{profile.phone || '---'}</span>
                  </div>
                  <div className="truncate">
                    <span className="text-xs text-muted-foreground block">Địa chỉ email</span>
                    <span className="text-foreground truncate block" title={profile.email}>{profile.email}</span>
                  </div>
                </div>
              ) : (
                <div className="py-2 text-center text-xs text-muted-foreground">Đang tải...</div>
              )}
            </CardContent>
          </Card>

          {/* Nhóm 2: Thông tin học phí */}
          <Card className="shadow-xs border">
            <CardHeader className="pt-4 pb-2 px-4">
              <CardTitle className="text-sm font-semibold text-foreground">
                Thông tin học phí
              </CardTitle>
            </CardHeader>

            <CardContent className="p-4 pt-1 space-y-3">
              <form onSubmit={handleSearch} className="flex gap-2">
                <Input
                  id="mssv"
                  type="text"
                  placeholder="Nhập mã số sinh viên"
                  value={mssv}
                  onChange={(e) => {
                    setMssv(e.target.value)
                    if (error) setError('')
                  }}
                  className="font-mono uppercase h-10 text-sm"
                />
                <Button type="submit" size="sm" className="h-10 px-4 font-medium" disabled={searchLoading || !mssv.trim()}>
                  {searchLoading ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin mr-1.5" />
                      <span>Đang tìm...</span>
                    </>
                  ) : (
                    'Tra cứu'
                  )}
                </Button>
              </form>

              {error && (
                <div className="flex items-center gap-2 p-2.5 text-xs text-red-800 dark:text-red-200 bg-red-50 dark:bg-red-950/40 rounded-lg border border-red-200 dark:border-red-900/50">
                  <AlertCircle className="h-3.5 w-3.5 shrink-0" />
                  <span>{error}</span>
                </div>
              )}

              {tuition ? (
                <div className={`pt-3 border-t space-y-3 transition-opacity duration-150 ${searchLoading ? 'opacity-60 pointer-events-none' : ''}`}>
                  <div className="flex items-center justify-between gap-2 text-sm">
                    <div>
                      <span className="text-xs text-muted-foreground block">Mã số sinh viên (MSSV)</span>
                      <span className="font-mono font-semibold text-foreground">{tuition.student_id}</span>
                    </div>
                    <Badge variant={tuition.status === 'PAID' ? 'success' : 'destructive'} className="text-xs">
                      {tuition.status === 'PAID' ? 'ĐÃ ĐÓNG' : 'CHƯA ĐÓNG'}
                    </Badge>
                  </div>

                  <div className="flex items-center justify-between text-sm">
                    <span className="text-xs text-muted-foreground">Họ và tên sinh viên</span>
                    <span className="font-bold text-base text-foreground">{tuition.student_name}</span>
                  </div>

                  <div className="flex items-baseline justify-between pt-1">
                    <span className="text-xs text-muted-foreground">Số tiền học phí cần thanh toán</span>
                    <span className="text-xl font-bold text-primary font-mono">{formatCurrency(tuition.amount)}</span>
                  </div>

                  {tuition.status === 'PAID' && tuition.paid_at && (
                    <p className="text-xs text-emerald-700 dark:text-emerald-400 font-medium">
                      Đã thanh toán: {formatDate(tuition.paid_at)}
                    </p>
                  )}
                </div>
              ) : !searchLoading && !error ? (
                <div className="py-4 text-center text-xs text-muted-foreground">
                  Nhập mã số sinh viên để tra cứu học phí
                </div>
              ) : null}
            </CardContent>
          </Card>
        </div>

        {/* CỘT PHẢI (5 cột): Nhóm 3 - Thông tin thanh toán */}
        <div className="lg:col-span-5 space-y-5 lg:sticky lg:top-20">
          <Card className="shadow-xs border">
            <CardHeader className="pt-4 pb-2 px-4">
              <CardTitle className="text-sm font-semibold text-foreground">
                Thông tin thanh toán
              </CardTitle>
            </CardHeader>

            <CardContent className="p-4 pt-1 space-y-3.5 text-sm">
              <div className="space-y-2 rounded-lg bg-muted/40 p-3 text-xs">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Số dư khả dụng của người nộp tiền</span>
                  <span className="font-mono font-bold text-primary text-sm">
                    {profile ? formatCurrency(profile.balance) : '---'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Số tiền cần thanh toán</span>
                  <span className="font-mono font-bold text-foreground text-sm">
                    {tuition ? formatCurrency(tuition.amount) : '---'}
                  </span>
                </div>
              </div>

              <label htmlFor="terms" className="flex items-start gap-2 text-xs text-muted-foreground cursor-pointer select-none">
                <input
                  type="checkbox"
                  id="terms"
                  checked={agreedTerms}
                  onChange={(e) => setAgreedTerms(e.target.checked)}
                  disabled={!tuition || tuition.status === 'PAID' || payLoading}
                  className="mt-0.5 h-3.5 w-3.5 rounded border-gray-300 text-primary focus:ring-primary cursor-pointer shrink-0"
                />
                <span>Tôi xác nhận thông tin sinh viên và đồng ý với các thỏa thuận và điều khoản của hệ thống.</span>
              </label>

              {tuition && tuition.status === 'PAID' && (
                <div className="p-2.5 rounded-lg bg-emerald-50 dark:bg-emerald-950/40 text-emerald-800 dark:text-emerald-200 text-xs border border-emerald-200 dark:border-emerald-900/50">
                  Khoản học phí này đã được thanh toán.
                </div>
              )}

              {tuition && tuition.status === 'UNPAID' && ENABLE_FRONTEND_BALANCE_GUARD && !isBalanceSufficient && (
                <div className="p-2.5 rounded-lg bg-red-50 dark:bg-red-950/40 text-red-800 dark:text-red-200 text-xs border border-red-200 dark:border-red-900/50">
                  Số dư khả dụng không đủ để thanh toán.
                </div>
              )}

              {payError && (
                <div className="flex items-center gap-2 p-2.5 text-xs text-red-800 dark:text-red-200 bg-red-50 dark:bg-red-950/40 rounded-lg border border-red-200 dark:border-red-900/50">
                  <AlertCircle className="h-3.5 w-3.5 shrink-0" />
                  <span>{payError}</span>
                </div>
              )}

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
                  'Xác nhận giao dịch'
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
