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

export default function OtpModal({ open = true, onConfirm, onCancel, loading, error, onClearError }) {
  const [otp, setOtp] = useState('')
  const countdown = useCountdown(300)

  useEffect(() => {
    if (open) {
      setOtp('')
      countdown.start()
    }
  }, [open, countdown.start])

  return (
    <Dialog open={open} onOpenChange={(val) => !val && onCancel()}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader className="text-center sm:text-center items-center">
          <DialogTitle className="text-xl flex items-center justify-center gap-2">
            <ShieldCheck className="h-5 w-5 text-primary shrink-0" />
            <span>Xác thực OTP</span>
          </DialogTitle>
          <DialogDescription className="text-center">
            Nhập mã OTP để xác nhận giao dịch.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-2">
          <div className="flex items-center justify-center gap-1.5 text-sm font-medium text-amber-900 dark:text-amber-200 bg-amber-50 dark:bg-amber-950/30 p-2.5 rounded-lg border border-amber-200 dark:border-amber-900/40">
            <Clock className="h-4 w-4 shrink-0 animate-pulse text-amber-700 dark:text-amber-400" />
            <span>Hiệu lực: <strong className="font-mono text-base">{countdown.display}</strong></span>
          </div>

          <div className="space-y-2">
            <Input
              type="text"
              maxLength={6}
              autoFocus
              placeholder="000000"
              value={otp}
              onChange={(e) => {
                if (error && onClearError) onClearError()
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
            <p className="text-center text-xs text-muted-foreground">
              Mã xác thực gồm 6 chữ số đã được gửi đến email đăng ký của quý khách.
            </p>
          </div>

          <div className="flex gap-3 pt-2">
            <Button type="button" variant="outline" onClick={onCancel} className="flex-1" disabled={loading}>
              Hủy
            </Button>
            <Button
              type="button"
              onClick={() => onConfirm(otp)}
              disabled={!isValidOtp(otp) || loading || !countdown.isActive}
              className="flex-1"
            >
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Đang xử lý...
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
