export const formatCurrency = (amount) =>
  new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(amount)

export const formatDate = (isoString) => {
  if (!isoString) return '---'
  const str = String(isoString).trim()
  const hasTz = /Z$|[+-]\d{2}:\d{2}$/.test(str)
  const normalized = hasTz ? str : `${str.replace(' ', 'T')}Z`
  return new Date(normalized).toLocaleString('vi-VN', { timeZone: 'Asia/Ho_Chi_Minh' })
}
