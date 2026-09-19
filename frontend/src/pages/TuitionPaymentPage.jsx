import { useState, useEffect } from 'react'
import { getTuitionApi } from '@/services/tuitionService'
import { initiatePaymentApi, confirmPaymentApi } from '@/services/paymentService'
import { getMeApi } from '@/services/authService'
import { formatCurrency } from '@/utils/formatters'
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
  CheckCircle2
} from 'lucide-react'

export default function TuitionPaymentPage() {
  const [profile, setProfile]   = useState(null)
  const [mssv, setMssv]         = useState('521H0002')
  const [tuition, setTuition]   = useState(null)
  const [paymentId, setPaymentId] = useState(null)
  const [receipt, setReceipt]   = useState(null)
  const [showOtp, setShowOtp]   = useState(false)
  const [error, setError]       = useState('')
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

  const handleSearch = async (e) => {
    e.preventDefault()
    setError('')
    setTuition(null)
    setSearchLoading(true)
    try {
      const res = await getTuitionApi(mssv.trim())
      setTuition(res.data.data)
    } catch (err) {
      setError(err.response?.data?.error?.message || 'Không tìm thấy thông tin sinh viên hoặc học phí')
    } finally {
      setSearchLoading(false)
    }
  }

  const handleInitiate = async () => {
    setError('')
    setPayLoading(true)
    try {
      const res = await initiatePaymentApi(tuition.student_id)
      setPaymentId(res.data.data.payment_id)
      setShowOtp(true)
    } catch (err) {
      setError(err.response?.data?.error?.message || 'Không thể khởi tạo giao dịch thanh toán')
    } finally {
      setPayLoading(false)
    }
  }

  const handleConfirm = async (otpCode) => {
    setPayLoading(true)
    setError('')
    try {
      const res = await confirmPaymentApi(paymentId, otpCode)
      setShowOtp(false)
      setReceipt(res.data.data)
      setTuition(null)
      fetchProfile() // Refresh balance after payment
    } catch (err) {
      setError(err.response?.data?.error?.message || 'Xác nhận OTP thất bại')
    } finally {
      setPayLoading(false)
    }
  }

  return (
    <div className="container mx-auto max-w-4xl py-8 px-4 sm:px-6 space-y-6">
      {/* Account Balance Card */}
      {profile && (
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-5 rounded-2xl bg-gradient-to-r from-primary/10 via-primary/5 to-transparent border">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-primary text-primary-foreground shadow">
              <Wallet className="h-6 w-6" />
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Tài khoản thanh toán</p>
              <h2 className="text-lg font-bold text-foreground">{profile.full_name} ({profile.username})</h2>
            </div>
          </div>
          <div className="sm:text-right">
            <p className="text-xs text-muted-foreground">Số dư khả dụng</p>
            <p className="text-2xl font-black text-primary">{formatCurrency(profile.balance)}</p>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-start">
        {/* Search Box */}
        <Card className="md:col-span-5 shadow-sm">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Search className="h-5 w-5 text-primary" />
              Tra cứu học phí
            </CardTitle>
            <CardDescription>Nhập Mã số sinh viên (MSSV) để kiểm tra nợ học phí</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSearch} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="mssv">Mã số sinh viên (MSSV)</Label>
                <Input
                  id="mssv"
                  type="text"
                  placeholder="VD: 521H0002"
                  value={mssv}
                  onChange={(e) => setMssv(e.target.value.toUpperCase())}
                  required
                  className="font-mono uppercase"
                />
              </div>

              {error && (
                <div className="flex items-start gap-2 p-3 text-sm text-destructive bg-destructive/10 rounded-lg border border-destructive/20">
                  <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
                  <span>{error}</span>
                </div>
              )}

              <Button type="submit" className="w-full gap-2" disabled={searchLoading}>
                {searchLoading ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Đang tra cứu...
                  </>
                ) : (
                  <>
                    <Search className="h-4 w-4" />
                    Tra cứu ngay
                  </>
                )}
              </Button>
            </form>

            <div className="mt-4 pt-3 border-t text-xs text-muted-foreground space-y-1">
              <p className="font-semibold text-foreground">MSSV mẫu nợ học phí:</p>
              <div className="flex flex-wrap gap-1.5 pt-1">
                {['521H0001', '521H0002', '521H0003', '522H0017', '522H0041', '523H0089'].map((id) => (
                  <button
                    key={id}
                    type="button"
                    onClick={() => setMssv(id)}
                    className="font-mono text-xs px-2 py-0.5 bg-muted rounded hover:bg-muted/80 border text-foreground"
                  >
                    {id}
                  </button>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Tuition Result Card */}
        <div className="md:col-span-7">
          {tuition ? (
            <Card className="shadow-md border-primary/20">
              <CardHeader className="pb-4">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <CardTitle className="text-xl font-bold flex items-center gap-2">
                      <GraduationCap className="h-5 w-5 text-primary" />
                      {tuition.student_name}
                    </CardTitle>
                    <CardDescription className="font-mono mt-1">MSSV: {tuition.student_id}</CardDescription>
                  </div>
                  <Badge variant={tuition.status === 'PAID' ? 'success' : 'destructive'}>
                    {tuition.status === 'PAID' ? 'ĐÃ ĐÓNG' : 'CHƯA ĐÓNG'}
                  </Badge>
                </div>
              </CardHeader>

              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-3 text-sm p-4 bg-muted/40 rounded-xl border">
                  <div>
                    <span className="text-xs text-muted-foreground block">Ngành học</span>
                    <span className="font-medium text-foreground">{tuition.major}</span>
                  </div>
                  <div>
                    <span className="text-xs text-muted-foreground block">Học kỳ</span>
                    <span className="font-medium text-foreground">{tuition.semester}</span>
                  </div>
                </div>

                <div className="p-4 rounded-xl border bg-primary/5 flex items-center justify-between">
                  <div>
                    <span className="text-xs text-muted-foreground block">Số tiền học phí</span>
                    <span className="text-2xl font-black text-primary">{formatCurrency(tuition.amount)}</span>
                  </div>
                  {tuition.status === 'PAID' && (
                    <div className="flex items-center gap-1.5 text-xs text-green-600 font-medium">
                      <CheckCircle2 className="h-4 w-4" />
                      Hoàn thành
                    </div>
                  )}
                </div>
              </CardContent>

              <CardFooter className="pt-0">
                {tuition.status === 'UNPAID' ? (
                  <Button
                    onClick={handleInitiate}
                    disabled={payLoading || (profile && profile.balance < tuition.amount)}
                    className="w-full gap-2"
                    size="lg"
                  >
                    {payLoading ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin" />
                        Đang xử lý...
                      </>
                    ) : (
                      <>
                        <CreditCard className="h-5 w-5" />
                        Thanh toán qua iBanking ({formatCurrency(tuition.amount)})
                      </>
                    )}
                  </Button>
                ) : (
                  <div className="w-full text-center text-sm text-green-600 font-medium py-2">
                    Khoản học phí này đã được gạch nợ thành công.
                  </div>
                )}
              </CardFooter>
            </Card>
          ) : (
            <Card className="border-dashed shadow-none text-center p-8 bg-muted/10">
              <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-muted text-muted-foreground mb-3">
                <UserCheck className="h-6 w-6" />
              </div>
              <h3 className="font-semibold text-foreground">Chưa có thông tin tra cứu</h3>
              <p className="text-sm text-muted-foreground mt-1 max-w-sm mx-auto">
                Nhập MSSV vào biểu mẫu bên trái và nhấn &quot;Tra cứu ngay&quot; để hiển thị chi tiết hóa đơn học phí.
              </p>
            </Card>
          )}
        </div>
      </div>

      {showOtp && (
        <OtpModal
          open={showOtp}
          onConfirm={handleConfirm}
          onCancel={() => setShowOtp(false)}
          loading={payLoading}
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
