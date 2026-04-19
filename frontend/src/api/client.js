const BASE = '/api/v1'

async function request(path, options = {}) {
  const url = `${BASE}${path}`
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  })
  if (res.status === 204) return null
  const data = await res.json()
  if (!res.ok) {
    const msg = data?.error?.message || `HTTP ${res.status}`
    throw new Error(msg)
  }
  return data
}

export function get(path, params) {
  const qs = params ? '?' + new URLSearchParams(params).toString() : ''
  return request(`${path}${qs}`)
}

export function post(path, body) {
  return request(path, { method: 'POST', body: JSON.stringify(body) })
}

export function patch(path, body) {
  return request(path, { method: 'PATCH', body: JSON.stringify(body) })
}

export function del(path) {
  return request(path, { method: 'DELETE' })
}

export async function upload(path, file) {
  const form = new FormData()
  form.append('file', file)
  const res = await fetch(`${BASE}${path}`, { method: 'POST', body: form })
  const data = await res.json()
  if (!res.ok) throw new Error(data?.error?.message || `HTTP ${res.status}`)
  return data
}

export async function uploadPut(path, file) {
  const form = new FormData()
  form.append('file', file)
  const res = await fetch(`${BASE}${path}`, { method: 'PUT', body: form })
  const data = await res.json()
  if (!res.ok) throw new Error(data?.error?.message || `HTTP ${res.status}`)
  return data
}
