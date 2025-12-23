import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'https://3d-filament-scanner-production.up.railway.app';

export interface Product {
  id: number;
  brand: string;
  line?: string;
  material: string;
  color_name: string;
  diameter_mm: number;
  barcode?: string;
  sku?: string;
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface Spool {
  id: number;
  product_id: number;
  order_id?: number;
  purchase_date?: string;
  vendor?: string;
  price?: number;
  storage_location?: string;
  photo_path?: string;
  status: 'in_stock' | 'used_up' | 'donated' | 'lost';
  created_at: string;
  updated_at: string;
}

export interface SpoolChangeLog {
  id: number;
  spool_id: number;
  from_status?: Spool['status'] | null;
  to_status?: Spool['status'] | null;
  from_location?: string | null;
  to_location?: string | null;
  note?: string | null;
  created_at: string;
}

export type SpoolDetail = Spool & { change_logs?: SpoolChangeLog[] };

export interface ParsedLabel {
  brand: string | null;
  material: string | null;
  color_name: string | null;
  diameter_mm: number | null;
  barcode: string | null;
  raw_text: string;
}

export interface InvoiceImportResult {
  success: boolean;
  products_created: number;
  spools_created: number;
  order_number: string;
  order_date: string;
  vendor: string;
  items: Array<{
    product_id: number;
    brand: string;
    material: string;
    color_name: string;
    quantity: number;
    price?: number;
  }>;
}

const api = axios.create({
  baseURL: `${API_BASE}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const productsApi = {
  list: (params?: { brand?: string; material?: string; color_name?: string }) =>
    api.get<Product[]>('/products', { params }),
  get: (id: number) => api.get<Product>(`/products/${id}`),
  create: (data: Omit<Product, 'id' | 'created_at' | 'updated_at'>) =>
    api.post<Product>('/products', data),
  update: (id: number, data: Partial<Product>) =>
    api.put<Product>(`/products/${id}`, data),
  delete: (id: number) => api.delete(`/products/${id}`),
};

export const spoolsApi = {
  list: (params?: {
    status?: string;
    brand?: string;
    material?: string;
    color_name?: string;
    storage_location?: string;
  }) => api.get<Spool[]>('/spools', { params }),
  get: (id: number) => api.get<SpoolDetail>(`/spools/${id}`),
  create: (data: Omit<Spool, 'id' | 'created_at' | 'updated_at'>) =>
    api.post<Spool>('/spools', data),
  update: (id: number, data: Partial<Spool>) =>
    api.put<SpoolDetail>(`/spools/${id}`, data),
  delete: (id: number) => api.delete(`/spools/${id}`),
};

export const ocrApi = {
  parseLabel: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post<ParsedLabel>('/ocr/parse-label', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
};

export const invoiceApi = {
  parseInvoice: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/invoice/parse', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  importInvoice: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post<InvoiceImportResult>('/invoice/import', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }).then(response => response.data);
  },
};
