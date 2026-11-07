import { useState, useEffect } from 'react'
import { getHistoryApi } from '@/services/paymentService'
import { formatCurrency, formatDate } from '@/utils/formatters'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import ReceiptModal from '@/components/ReceiptModal'
import {
  History,
  CreditCard,
  Calendar,
  CheckCircle2,
  Clock,
  XCircle,
  Loader2,
  FileText,
  Filter
} from 'lucide-react'

const ERROR_LABELS = {
  INSUFFICIENT_BALANCE: 'Không đủ số dư khả dụng',
  TUITION_MARK_FAILED: 'Học phí đã được thanh toán bởi giao dịch khác (Đã hoàn tiền)',
  OTP_MAX_ATTEMPTS_EXCEEDED: 'Nhập sai mã OTP quá 3 lần',
  OTP_EXPIRED: 'Mã OTP hết thời hạn 5 phút',
  OTP_SEND_FAILED: 'Không gửi được email OTP',
  SUPERSEDED: 'Đã hủy do tạo phiên thanh toán mới',
}

export default function HistoryPage() {
  const [records, setRecords] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [selectedReceipt, setSelectedReceipt] = useState(null)
  const [filterStatus, setFilterStatus] = useState('ALL')

  useEffect(() => {
    getHistoryApi()
      .then((res) => setRecords(res.data.data))
      .catch((err) => setError(err.response?.data?.error?.message || 'Không thể tải lịch sử giao dịch'))
      .finally(() => setLoading(false))
  }, [])

  const getStatusBadge = (status) => {
    switch (status) {
      case 'SUCCESS':
        return (
          <Badge variant="success" className="gap-1">
            <CheckCircle2 className="h-3 w-3" />
            THÀNH CÔNG
          </Badge>
        )
      case 'PROCESSING':
        return (
          <Badge variant="warning" className="gap-1">
            <Loader2 className="h-3 w-3 animate-spin" />
            ĐANG XỬ LÝ
          </Badge>
        )
      case 'PENDING':
        return (
          <Badge variant="warning" className="gap-1">
            <Clock className="h-3 w-3" />
            ĐANG CHỜ OTP
          </Badge>
        )
      case 'FAILED':
      default:
        return (
          <Badge variant="destructive" className="gap-1">
            <XCircle className="h-3 w-3" />
            THẤT BẠI
          </Badge>
        )
    }
  }

  const filteredRecords = records.filter((r) => {
    if (filterStatus === 'ALL') return true
    if (filterStatus === 'SUCCESS') return r.status === 'SUCCESS'
    if (filterStatus === 'PENDING') return r.status === 'PENDING' || r.status === 'PROCESSING'
    if (filterStatus === 'FAILED') return r.status === 'FAILED'
    return true
  })

  return (
    <div className="container mx-auto max-w-5xl py-8 px-4 sm:px-6 space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2.5">
            <History className="h-6 w-6 text-primary shrink-0" />
            <span>Lịch sử giao dịch</span>
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Danh sách tất cả các giao dịch thanh toán học phí đã thực hiện
          </p>
        </div>

        {/* Bộ lọc trạng thái */}
        {!loading && records.length > 0 && (
          <div className="flex items-center gap-1.5 p-1 bg-muted/60 rounded-lg border text-xs">
            <span className="text-muted-foreground px-2 flex items-center gap-1">
              <Filter className="h-3 w-3" />
              Lọc:
            </span>
            {[
              { id: 'ALL', label: 'Tất cả' },
              { id: 'SUCCESS', label: 'Thành công' },
              { id: 'PENDING', label: 'Chờ xử lý' },
              { id: 'FAILED', label: 'Thất bại' },
            ].map((tab) => (
              <button
                key={tab.id}
                type="button"
                onClick={() => setFilterStatus(tab.id)}
                className={`px-3 py-1.5 rounded-md font-medium transition-colors ${
                  filterStatus === tab.id
                    ? 'bg-card text-foreground shadow-xs'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        )}
      </div>

      {loading && (
        <div className="flex flex-col items-center justify-center py-16 text-muted-foreground gap-2">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <p className="text-sm font-medium">Đang tải lịch sử giao dịch...</p>
        </div>
      )}

      {error && (
        <div className="p-4 rounded-xl border border-red-200 dark:border-red-900/50 bg-red-50 dark:bg-red-950/40 text-red-800 dark:text-red-200 text-sm" role="alert">
          {error}
        </div>
      )}

      {!loading && !error && records.length === 0 && (
        <Card className="border-dashed text-center p-12 bg-card">
          <CreditCard className="mx-auto h-8 w-8 text-muted-foreground/50 mb-2" />
          <h3 className="font-semibold text-foreground">Chưa có giao dịch</h3>
          <p className="text-sm text-muted-foreground mt-1">
            Tài khoản chưa có lịch sử phát sinh giao dịch nào.
          </p>
        </Card>
      )}

      {!loading && !error && records.length > 0 && filteredRecords.length === 0 && (
        <Card className="border-dashed text-center p-8 bg-card">
          <p className="text-sm text-muted-foreground">Không có giao dịch nào ở trạng thái đã chọn.</p>
        </Card>
      )}

      {!loading && !error && filteredRecords.length > 0 && (
        <div className="space-y-3">
          {filteredRecords.map((r) => (
            <Card key={r.payment_id} className="hover:border-primary/40 transition-colors shadow-sm border">
              <CardContent className="p-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                <div className="space-y-1.5 flex-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-bold text-base text-foreground">{r.student_name}</span>
                    <Badge variant="outline" className="font-mono text-xs">
                      MSSV: {r.student_id}
                    </Badge>
                    {r.semester && (
                      <Badge variant="secondary" className="text-xs">
                        {r.semester}
                      </Badge>
                    )}
                  </div>
                  <div className="flex items-center gap-4 text-xs text-muted-foreground flex-wrap">
                    <span className="flex items-center gap-1">
                      <Calendar className="h-3.5 w-3.5 text-muted-foreground/70" />
                      {formatDate(r.created_at)}
                    </span>
                    <span className="font-mono">Mã GD: #{r.payment_id}</span>
                  </div>
                  {r.status === 'FAILED' && r.error_code && (
                    <p className="text-xs text-destructive font-medium pt-0.5">
                      Nguyên nhân: {ERROR_LABELS[r.error_code] || r.error_code}
                    </p>
                  )}
                </div>

                <div className="flex items-center sm:flex-col sm:items-end justify-between w-full sm:w-auto gap-3">
                  <div className="sm:text-right">
                    <span className="text-lg font-bold text-primary tracking-tight font-mono block">
                      {formatCurrency(r.amount)}
                    </span>
                    <div className="mt-1">{getStatusBadge(r.status)}</div>
                  </div>

                  {/* Nút Xem lại biên lai cho giao dịch thành công */}
                  {r.status === 'SUCCESS' && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() =>
                        setSelectedReceipt({
                          payment_id: r.payment_id,
                          student_name: r.student_name,
                          student_id: r.student_id,
                          amount: r.amount,
                          semester: r.semester,
                          paid_at: r.updated_at || r.created_at,
                        })
                      }
                      className="h-8 text-xs gap-1.5 border-primary/30 text-primary hover:bg-primary/5 shrink-0"
                    >
                      <FileText className="h-3.5 w-3.5" />
                      <span>Xem biên lai</span>
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Modal hiển thị lại Biên lai */}
      <ReceiptModal
        open={!!selectedReceipt}
        data={selectedReceipt}
        onClose={() => setSelectedReceipt(null)}
      />
    </div>
  )
}
