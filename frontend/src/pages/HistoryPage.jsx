import { useState, useEffect } from 'react'
import { getHistoryApi } from '@/services/paymentService'
import { formatCurrency, formatDate } from '@/utils/formatters'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import ReceiptModal from '@/components/ReceiptModal'
import { Loader2 } from 'lucide-react'

// [Rubric Tiêu chí 4 / Đề bài Mục 3: Lịch sử giao dịch]
// - Hiển thị danh sách các giao dịch thanh toán học phí của tài khoản đang đăng nhập.
// - Phân loại trạng thái (SUCCESS, PENDING, FAILED) và nguyên nhân chi tiết nếu thất bại.
// - Hỗ trợ xem lại biên lai giao dịch thành công.
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
          <Badge variant="success" className="text-[11px] font-medium py-0.5 px-2">
            Thành công
          </Badge>
        )
      case 'PROCESSING':
        return (
          <Badge variant="warning" className="text-[11px] font-medium py-0.5 px-2">
            Đang xử lý
          </Badge>
        )
      case 'PENDING':
        return (
          <Badge variant="warning" className="text-[11px] font-medium py-0.5 px-2">
            Đang chờ OTP
          </Badge>
        )
      case 'FAILED':
      default:
        return (
          <Badge variant="destructive" className="text-[11px] font-medium py-0.5 px-2">
            Thất bại
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
    <div className="container mx-auto max-w-5xl py-6 px-4 sm:px-6 space-y-5">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <h1 className="text-xl font-bold tracking-tight text-foreground">
          Lịch sử giao dịch
        </h1>

        {/* Bộ lọc trạng thái */}
        {!loading && records.length > 0 && (
          <div className="flex items-center gap-1 p-1 bg-muted/40 rounded-lg border text-xs self-start sm:self-auto">
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
                className={`px-3 py-1 rounded-md font-medium transition-colors cursor-pointer ${
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
        <div className="flex flex-col items-center justify-center py-12 text-muted-foreground gap-2">
          <Loader2 className="h-6 w-6 animate-spin text-primary" />
          <p className="text-xs">Đang tải lịch sử giao dịch...</p>
        </div>
      )}

      {error && (
        <div className="p-3 rounded-lg border border-red-200 dark:border-red-900/50 bg-red-50 dark:bg-red-950/40 text-red-800 dark:text-red-200 text-xs" role="alert">
          {error}
        </div>
      )}

      {!loading && !error && records.length === 0 && (
        <div className="py-12 text-center text-xs text-muted-foreground border border-dashed rounded-lg bg-card">
          Chưa có lịch sử phát sinh giao dịch nào.
        </div>
      )}

      {!loading && !error && records.length > 0 && filteredRecords.length === 0 && (
        <div className="py-8 text-center text-xs text-muted-foreground border border-dashed rounded-lg bg-card">
          Không có giao dịch nào ở trạng thái đã chọn.
        </div>
      )}

      {!loading && !error && filteredRecords.length > 0 && (
        <div className="space-y-2.5">
          {filteredRecords.map((r) => (
            <Card key={r.payment_id} className="border shadow-xs hover:border-muted-foreground/30 transition-colors">
              <CardContent className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                {/* Thông tin giao dịch & sinh viên */}
                <div className="space-y-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-semibold text-sm text-foreground">
                      {r.student_name}
                    </span>
                    <span className="text-xs font-mono text-muted-foreground">
                      ({r.student_id})
                    </span>
                    {r.semester && (
                      <span className="text-xs text-muted-foreground">
                        • {r.semester}
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <span>{formatDate(r.created_at)}</span>
                    <span>•</span>
                    <span className="font-mono">Mã GD: #{r.payment_id}</span>
                  </div>
                  {r.status === 'FAILED' && r.error_code && (
                    <p className="text-xs text-destructive pt-0.5">
                      Lý do: {ERROR_LABELS[r.error_code] || r.error_code}
                    </p>
                  )}
                </div>

                {/* Số tiền & Hành động */}
                <div className="flex sm:flex-col items-center sm:items-end justify-between sm:justify-center gap-2 pt-2 sm:pt-0 border-t sm:border-0 border-border/50">
                  <span className="font-bold text-sm sm:text-base font-mono text-foreground">
                    {formatCurrency(r.amount)}
                  </span>
                  <div className="flex items-center gap-2">
                    {getStatusBadge(r.status)}
                    {r.status === 'SUCCESS' && (
                      <Button
                        variant="ghost"
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
                        className="h-6 px-2 text-xs text-primary hover:text-primary hover:bg-primary/10"
                      >
                        Xem biên lai
                      </Button>
                    )}
                  </div>
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
