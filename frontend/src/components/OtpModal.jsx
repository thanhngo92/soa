import { useState, useEffect } from 'react'
import useCountdown from '@/hooks/useCountdown'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { ShieldCheck, Clock, Loader2 } from 'lucide-react'

export default function OtpModal({ open = true, onConfirm, onCancel, loading }) {
  const [otp, setOtp] = useState('')
  const countdown = useCountdown(300)

  useEffect(() => {
    countdown.start()
  }, [])

  return (
    <Dialog open={open} onOpenChange={(val) => !val && onCancel()}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader className="text-center sm:text-center items-center">
          <div className="mx-auto mb-2 flex h-12 w-12 items-center justify-center rounded-full bg-primary/10 text-primary">
            <ShieldCheck className="h-6 w-6" />
          </div>
          <DialogTitle className="text-xl">Xác thực mã OTP</DialogTitle>
          <DialogDescription className="text-center">
            Mã OTP gồm 6 chữ số đã được gửi qua email (Mailpit). Vui lòng nhập mã để hoàn tất thanh toán.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-2">
          <div className="flex items-center justify-center gap-1.5 text-sm font-medium text-amber-600 bg-amber-50 dark:bg-amber-950/30 p-2.5 rounded-lg border border-amber-200">
            <Clock className="h-4 w-4 shrink-0 animate-pulse" />
            <span>Thời gian còn lại: <strong className="font-mono text-base">{countdown.display}</strong></span>
          </div>

          <div className="space-y-2">
            <Input
              type="text"
              maxLength={6}
              autoFocus
              placeholder="000000"
              value={otp}
              onChange={(e) => setOtp(e.target.value.replace(/[^0-9]/g, ''))}
              className="text-center text-3xl font-mono tracking-[0.5em] h-14 font-bold border-2 focus-visible:ring-primary"
            />
            <p className="text-center text-xs text-muted-foreground">
              Xem email OTP tại: <a href="http://localhost:8025" target="_blank" rel="noreferrer" className="text-primary underline">Mailpit Web UI (cổng 8025)</a>
            </p>
          </div>

          <div className="flex gap-3 pt-2">
            <Button type="button" variant="outline" onClick={onCancel} className="flex-1" disabled={loading}>
              Hủy bỏ
            </Button>
            <Button
              type="button"
              onClick={() => onConfirm(otp)}
              disabled={otp.length !== 6 || loading || !countdown.isActive}
              className="flex-1"
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
