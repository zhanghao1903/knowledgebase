import { get, post, patch, del } from './client.js'

export const listKBs = (params) => get('/knowledge-bases', params)
export const getKB = (id) => get(`/knowledge-bases/${id}`)
export const createKB = (data) => post('/knowledge-bases', data)
export const updateKB = (id, data) => patch(`/knowledge-bases/${id}`, data)
export const deleteKB = (id) => del(`/knowledge-bases/${id}`)
