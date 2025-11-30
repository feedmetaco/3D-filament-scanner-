export type SpoolStatus = 'in_stock' | 'used_up' | 'donated' | 'lost'

export interface Product {
  id: number
  brand: string
  line?: string | null
  material: string
  color_name: string
  diameter_mm: number
  notes?: string | null
  barcode?: string | null
  sku?: string | null
  created_at?: string
  updated_at?: string
}

export interface Spool {
  id: number
  product_id: number
  purchase_date?: string | null
  vendor?: string | null
  price?: number | null
  storage_location?: string | null
  photo_path?: string | null
  status: SpoolStatus
  order_id?: number | null
  created_at?: string
  updated_at?: string
}
