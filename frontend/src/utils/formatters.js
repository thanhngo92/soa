export const formatCurrency = (amount) =>
  new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(amount)

export const formatDate = (isoString) =>
  new Date(isoString).toLocaleString('vi-VN', { timeZone: 'Asia/Ho_Chi_Minh' })
