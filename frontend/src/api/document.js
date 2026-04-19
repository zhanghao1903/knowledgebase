import { get, del, upload, uploadPut } from './client.js'

export const listDocs = (kbId, params) => get(`/knowledge-bases/${kbId}/documents`, params)
export const getDoc = (id) => get(`/documents/${id}`)
export const getDocVersions = (id) => get(`/documents/${id}/versions`)
export const uploadDoc = (kbId, file) => upload(`/knowledge-bases/${kbId}/documents`, file)
export const reuploadDoc = (id, file) => uploadPut(`/documents/${id}/reupload`, file)
export const deleteDoc = (id) => del(`/documents/${id}`)
