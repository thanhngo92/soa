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
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2.5">
          <History className="h-6 w-6 text-primary shrink-0" />
          <span>Lịch sử giao dịch</span>
        </h1>
        <p className="text-sm text-muted-foreground mt-1">Danh sách tất cả các giao dịch thanh toán học phí đã thực hiện</p>
      </div>

      {loading && (
        <div className="flex flex-col items-center justify-center py-16 text-muted-foreground gap-2">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <p className="text-sm font-medium">Đang tải lịch sử...</p>
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

      {!loading && !error && records.length > 0 && (
        <div className="space-y-3">
          {records.map((r) => (
            <Card key={r.payment_id} className="hover:border-primary/40 transition-colors shadow-sm border">
              <CardContent className="p-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                <div className="space-y-1.5">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-bold text-base text-foreground">{r.student_name}</span>
                    <Badge variant="outline" className="font-mono text-xs">
                      MSSV: {r.student_id}
                    </Badge>
                  </div>
                  <div className="flex items-center gap-4 text-xs text-muted-foreground flex-wrap">
                    <span className="flex items-center gap-1">
                      <Calendar className="h-3.5 w-3.5 text-muted-foreground/70" />
                      {formatDate(r.created_at)}
                    </span>
                    <span className="font-mono">Mã GD: #{r.payment_id}</span>
                  </div>
                </div>

                <div className="flex items-center sm:flex-col sm:items-end justify-between w-full sm:w-auto gap-2">
                  <span className="text-lg font-bold text-primary tracking-tight">
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
