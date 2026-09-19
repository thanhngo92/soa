import { useState, useEffect } from 'react'
import { getHistoryApi } from '@/services/paymentService'
import { formatCurrency, formatDate } from '@/utils/formatters'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { History, CreditCard, Calendar, CheckCircle2, Clock, XCircle, Loader2 } from 'lucide-react'

export default function HistoryPage() {
  const [records, setRecords] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError]     = useState('')

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
      case 'PENDING':
        return (
          <Badge variant="warning" className="gap-1">
            <Clock className="h-3 w-3" />
            ĐANG CHỜ
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

  return (
    <div className="container mx-auto max-w-4xl py-8 px-4 sm:px-6 space-y-6">
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10 text-primary">
          <History className="h-5 w-5" />
        </div>
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">Lịch sử giao dịch</h1>
          <p className="text-sm text-muted-foreground">Tất cả các giao dịch thanh toán học phí của tài khoản</p>
        </div>
      </div>

      {loading && (
        <div className="flex flex-col items-center justify-center py-16 text-muted-foreground gap-2">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <p className="text-sm">Đang tải lịch sử giao dịch...</p>
        </div>
      )}

      {error && (
        <div className="p-4 rounded-xl border border-destructive/20 bg-destructive/10 text-destructive text-sm">
          {error}
        </div>
      )}

      {!loading && !error && records.length === 0 && (
        <Card className="border-dashed text-center p-12 bg-muted/10">
          <CreditCard className="mx-auto h-12 w-12 text-muted-foreground mb-3" />
          <h3 className="font-semibold text-foreground">Chưa có giao dịch nào</h3>
          <p className="text-sm text-muted-foreground mt-1">
            Bạn chưa thực hiện thanh toán học phí nào từ tài khoản này.
          </p>
        </Card>
      )}

      {!loading && !error && records.length > 0 && (
        <div className="space-y-3">
          {records.map((r) => (
            <Card key={r.payment_id} className="hover:border-primary/40 transition-colors shadow-sm">
              <CardContent className="p-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-base text-foreground">{r.student_name}</span>
                    <span className="text-xs px-2 py-0.5 rounded bg-muted font-mono font-medium text-muted-foreground">
                      MSSV: {r.student_id}
                    </span>
                  </div>
                  <div className="flex items-center gap-4 text-xs text-muted-foreground">
                    <span className="flex items-center gap-1">
                      <Calendar className="h-3.5 w-3.5" />
                      {formatDate(r.created_at)}
                    </span>
                    <span className="font-mono">Mã GD: {r.payment_id.slice(-8).toUpperCase()}</span>
                  </div>
                </div>

                <div className="flex items-center sm:flex-col sm:items-end justify-between w-full sm:w-auto gap-1">
                  <span className="text-lg font-bold text-primary">
                    {formatCurrency(r.amount)}
                  </span>
                  <div>{getStatusBadge(r.status)}</div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
