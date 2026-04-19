import { post } from './client.js'

export const queryKB = (kbId, question, topK = 5) =>
  post(`/knowledge-bases/${kbId}/query`, { question, top_k: topK })
