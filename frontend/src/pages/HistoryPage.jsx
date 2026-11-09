import { useState, useEffect } from 'react'
import { getHistoryApi } from '@/services/paymentService'
import { formatCurrency, formatDate } from '@/utils/formatters'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Loader2 } from 'lucide-react'

export default function HistoryPage() {
  const [records, setRecords] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    getHistoryApi()
      .then((res) => setRecords(res.data.data || []))
      .catch(() => setError('Không thể tải lịch sử giao dịch'))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="container mx-auto max-w-5xl py-6 px-4 sm:px-6 space-y-4">
      <h1 className="text-xl font-bold tracking-tight text-foreground">
        Lịch sử giao dịch
      </h1>

      {loading && (
        <div className="flex items-center justify-center py-12 text-muted-foreground gap-2">
          <Loader2 className="h-5 w-5 animate-spin text-primary" />
          <span className="text-xs">Đang tải lịch sử giao dịch...</span>
        </div>
      )}

      {error && (
        <div className="p-3 rounded-lg border border-red-200 bg-red-50 text-red-800 text-xs" role="alert">
          {error}
        </div>
      )}

      {!loading && !error && records.length === 0 && (
        <div className="py-12 text-center text-xs text-muted-foreground border border-dashed rounded-lg bg-card">
          Chưa có giao dịch nào được ghi nhận.
        </div>
      )}

      {!loading && !error && records.length > 0 && (
        <Card>
          <CardContent className="p-4 sm:p-6 overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs sm:text-sm">
              <thead>
                <tr className="border-b text-xs font-semibold text-muted-foreground">
                  <th className="py-3 px-4">Mã GD</th>
                  <th className="py-3 px-4">Họ và tên sinh viên</th>
                  <th className="py-3 px-4">MSSV</th>
                  <th className="py-3 px-4 text-right">Số tiền</th>
                  <th className="py-3 px-4">Thời gian</th>
                  <th className="py-3 px-4">Trạng thái</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {records.map((r) => (
                  <tr key={r.payment_id} className="hover:bg-muted/20 transition-colors">
                    <td className="py-3 px-4 font-mono text-xs text-muted-foreground">
                      #{r.payment_id}
                    </td>
                    <td className="py-3 px-4 font-medium text-foreground">
                      {r.student_name}
                    </td>
                    <td className="py-3 px-4 font-mono text-xs">
                      {r.student_id}
                    </td>
                    <td className="py-3 px-4 text-right font-mono font-semibold text-foreground">
                      {formatCurrency(r.amount)}
                    </td>
                    <td className="py-3 px-4 text-xs text-muted-foreground whitespace-nowrap">
                      {formatDate(r.completed_at || r.created_at)}
                    </td>
                    <td className="py-3 px-4">
                      {r.status === 'SUCCESS' ? (
                        <Badge variant="success">Thành công</Badge>
                      ) : (
                        <div className="flex flex-col gap-1 items-start">
                          <Badge variant="destructive">Thất bại</Badge>
                          <span className="text-[11px] text-amber-600 font-semibold whitespace-nowrap">
                            Đã hoàn tiền (Saga)
                          </span>
                        </div>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
