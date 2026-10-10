import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { formatCurrency, formatDate } from '@/utils/formatters'

export default function ReceiptModal({ open = true, data, onClose }) {
  if (!data) return null

  return (
    <Dialog open={open} onOpenChange={(val) => !val && onClose()}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader className="text-center sm:text-center items-center pb-2">
          <DialogTitle className="text-2xl font-bold text-emerald-800 dark:text-emerald-300 text-center">
            Thanh toán thành công
          </DialogTitle>
          <DialogDescription className="sr-only">
            Chi tiết biên lai thanh toán học phí
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-2">
          <div className="rounded-xl border bg-muted/30 p-4 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs text-muted-foreground uppercase tracking-wider font-semibold">Trạng thái</span>
              <Badge variant="success">THÀNH CÔNG</Badge>
            </div>

            <hr className="border-t border-border" />

            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Mã giao dịch</span>
              <span className="font-mono font-medium">{data.payment_id}</span>
            </div>

            {data.student_name && (
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Sinh viên</span>
                <span className="font-semibold text-foreground">{data.student_name}</span>
              </div>
            )}

            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Mã sinh viên</span>
              <span className="font-mono font-bold text-foreground">{data.student_id}</span>
            </div>

            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Thời gian</span>
              <span>{formatDate(data.paid_at)}</span>
            </div>

            <hr className="border-t border-border" />

            <div className="flex items-center justify-between">
              <span className="font-semibold text-foreground">Số tiền</span>
              <span className="text-xl font-bold text-primary">{formatCurrency(data.amount)}</span>
            </div>
          </div>

          <div className="pt-2">
            <Button onClick={onClose} className="w-full" size="lg">
              Đóng
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
