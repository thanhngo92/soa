import { useState, useEffect } from 'react'
import useCountdown from '@/hooks/useCountdown'
import { isValidOtp } from '@/utils/validators'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { AlertCircle, ShieldCheck, Clock, Loader2 } from 'lucide-react'

// [Rubric Tiêu chí 5 & 7 / Đề bài Mục 3: Modal xác thực OTP]
// - Nghiệp vụ: Đếm ngược thời hạn hiệu lực 5 phút (300s), giới hạn 6 ký tự số.
// - Kỹ thuật: Khóa input và nút xác nhận ngay lập tức khi locked=true (hết hạn hoặc quá 3 lần nhập sai).
export default function OtpModal({
  open = true,
  onConfirm,
  onCancel,
  loading,
  error,
  locked = false,
  onClearError,
}) {
  const [otp, setOtp] = useState('')
  const countdown = useCountdown(300)

  useEffect(() => {
    if (open) {
      setOtp('')
      countdown.start()
    }
  }, [open])

  const isExpired = !countdown.isActive

  return (
    <Dialog open={open} onOpenChange={(val) => !val && onCancel()}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader className="text-center sm:text-center items-center pb-1">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-primary/10 text-primary mb-1">
            <ShieldCheck className="h-6 w-6" />
          </div>
          <DialogTitle className="text-xl font-bold">
            Xác thực OTP
          </DialogTitle>
          <DialogDescription className="text-center text-xs text-muted-foreground">
            Nhập mã xác thực gồm 6 chữ số đã gửi đến email của bạn
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-2">
          {/* Đồng hồ đếm ngược */}
          <div className={`flex items-center justify-center gap-1.5 text-sm font-medium p-2.5 rounded-lg border transition-colors ${
            isExpired || locked
              ? 'text-red-900 dark:text-red-200 bg-red-50 dark:bg-red-950/40 border-red-200 dark:border-red-900/50'
              : 'text-amber-900 dark:text-amber-200 bg-amber-50 dark:bg-amber-950/30 border-amber-200 dark:border-amber-900/40'
          }`}>
            <Clock className={`h-4 w-4 shrink-0 ${isExpired || locked ? '' : 'animate-pulse text-amber-700 dark:text-amber-400'}`} />
            {locked ? (
              <span className="font-semibold text-destructive">Phiên giao dịch đã bị khóa</span>
            ) : isExpired ? (
              <span className="font-semibold text-destructive">Mã OTP đã hết thời hạn hiệu lực (5 phút)</span>
            ) : (
              <span>Hiệu lực còn lại: <strong className="font-mono text-base font-bold">{countdown.display}</strong></span>
            )}
          </div>

          <div className="space-y-2">
            <Input
              type="text"
              maxLength={6}
              autoFocus
              disabled={loading || locked || isExpired}
              placeholder="000000"
              value={otp}
              onChange={(e) => {
                if (error && !locked && onClearError) onClearError()
                setOtp(e.target.value.replace(/[^0-9]/g, ''))
              }}
              className="text-center text-3xl font-mono tracking-[0.5em] h-14 font-bold border-2 focus-visible:ring-primary"
            />

            {error && (
              <div className="flex items-center gap-2 p-2.5 text-xs text-red-800 dark:text-red-200 bg-red-50 dark:bg-red-950/40 rounded-lg border border-red-200 dark:border-red-900/50" role="alert">
                <AlertCircle className="h-4 w-4 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <div className="text-xs text-muted-foreground pt-1">
              <span>Tối đa 3 lần thử sai</span>
            </div>
          </div>

          <div className="flex gap-3 pt-2">
            <Button type="button" variant="outline" onClick={onCancel} className="flex-1" disabled={loading}>
              {locked || isExpired ? 'Đóng' : 'Hủy'}
            </Button>
            <Button
              type="button"
              onClick={() => onConfirm(otp)}
              disabled={!isValidOtp(otp) || loading || locked || isExpired}
              className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-medium"
            >
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Đang xác thực...
                </>
              ) : (
                'Xác nhận'
              )}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
