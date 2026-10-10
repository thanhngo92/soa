import api from '../lib/api'

export const initiatePaymentApi = (student_id) =>
  api.post('/payments/initiate', { student_id })

export const confirmPaymentApi = (payment_id, otp_code, idempotencyKey) => {
  const headers = idempotencyKey ? { 'Idempotency-Key': idempotencyKey } : {}
  return api.post('/payments/confirm', { payment_id, otp_code }, { headers })
}

export const getHistoryApi = () =>
  api.get('/payments/history')
