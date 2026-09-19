import api from '../lib/api'

export const getTuitionApi = (mssv) =>
  api.get(`/tuitions/students/${mssv}`)
