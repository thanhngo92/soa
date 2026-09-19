import api from '../lib/api'

export const initiatePaymentApi = (student_id) =>
  api.post('/payments/initiate', { student_id })

export const confirmPaymentApi = (payment_id, otp_code) =>
  api.post('/payments/confirm', { payment_id, otp_code })

export const getHistoryApi = () =>
  api.get('/payments/history')
