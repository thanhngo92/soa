import api from '../lib/api'

export const loginApi = (username, password) =>
  api.post('/accounts/login', { username, password })

export const getMeApi = () =>
  api.get('/accounts/me')
