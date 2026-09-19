import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { formatCurrency, formatDate } from '@/utils/formatters'
import { CheckCircle2, Receipt } from 'lucide-react'

export default function ReceiptModal({ open = true, data, onClose }) {
  if (!data) return null

  return (
    <Dialog open={open} onOpenChange={(val) => !val && onClose()}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader className="text-center sm:text-center items-center pb-2">
          <div className="mx-auto mb-2 flex h-14 w-14 items-center justify-center rounded-full bg-green-100 text-green-600 dark:bg-green-900/30">
            <CheckCircle2 className="h-8 w-8" />
          </div>
          <DialogTitle className="text-2xl font-bold text-green-700 dark:text-green-400">
            Giao dịch thành công!
          </DialogTitle>
          <p className="text-sm text-muted-foreground">
            Học phí đã được thanh toán và gạch nợ thành công
          </p>
        </DialogHeader>

        <div className="space-y-4 py-2">
          <div className="rounded-xl border bg-muted/30 p-4 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs text-muted-foreground uppercase tracking-wider font-semibold">Trạng thái</span>
              <Badge variant="success">THÀNH CÔNG</Badge>
            </div>

            <Separator />

            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Mã giao dịch</span>
              <span className="font-mono font-medium">{data.payment_id}</span>
            </div>

            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Mã sinh viên (MSSV)</span>
              <span className="font-mono font-bold text-foreground">{data.student_id}</span>
            </div>

            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Thời gian hoàn tất</span>
              <span>{formatDate(data.paid_at)}</span>
            </div>

            <Separator />

            <div className="flex items-center justify-between">
              <span className="font-semibold text-foreground">Số tiền thanh toán</span>
              <span className="text-xl font-bold text-primary">{formatCurrency(data.amount)}</span>
            </div>
          </div>

          <div className="pt-2">
            <Button onClick={onClose} className="w-full gap-2" size="lg">
              <Receipt className="h-4 w-4" />
              Xác nhận & Đóng
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
