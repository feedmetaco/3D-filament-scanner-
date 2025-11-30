import { Product, Spool, SpoolStatus } from './types'

const defaultBaseUrl = 'http://localhost:8000/api/v1'
const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? defaultBaseUrl

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })

  if (!response.ok) {
    const message = await response.text()
    throw new Error(message || `Request failed with status ${response.status}`)
  }

  return response.json() as Promise<T>
}

export async function fetchProducts(): Promise<Product[]> {
  return fetchJson<Product[]>('/products')
}

export async function fetchProduct(id: number): Promise<Product> {
  return fetchJson<Product>(`/products/${id}`)
}

export async function fetchSpools(): Promise<Spool[]> {
  return fetchJson<Spool[]>('/spools')
}

export async function createSpool(payload: {
  product_id: number
  purchase_date?: string | null
  vendor?: string | null
  price?: number | null
  storage_location?: string | null
  photo_path?: string | null
  status?: SpoolStatus
}): Promise<Spool> {
  return fetchJson<Spool>('/spools', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}
