import { get } from './client.js'

export const getTask = (id) => get(`/tasks/${id}`)
export const listTasks = (params) => get('/tasks', params)
