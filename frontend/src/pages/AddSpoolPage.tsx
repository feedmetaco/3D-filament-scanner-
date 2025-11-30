import { FormEvent, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { createSpool, fetchProducts } from '../api'
import { Product, SpoolStatus } from '../types'

const statuses: { value: SpoolStatus; label: string }[] = [
  { value: 'in_stock', label: 'In stock' },
  { value: 'used_up', label: 'Used up' },
  { value: 'donated', label: 'Donated' },
  { value: 'lost', label: 'Lost' },
]

function AddSpoolPage() {
  const [products, setProducts] = useState<Product[]>([])
  const [productId, setProductId] = useState<number | ''>('')
  const [purchaseDate, setPurchaseDate] = useState('')
  const [vendor, setVendor] = useState('')
  const [price, setPrice] = useState('')
  const [storage, setStorage] = useState('')
  const [status, setStatus] = useState<SpoolStatus>('in_stock')
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    const loadProducts = async () => {
      try {
        const data = await fetchProducts()
        setProducts(data)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load products')
      }
    }

    loadProducts()
  }, [])

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setError(null)
    setMessage(null)

    if (!productId) {
      setError('Select a product before submitting')
      return
    }

    try {
      setSubmitting(true)
      const payload = {
        product_id: Number(productId),
        purchase_date: purchaseDate || null,
        vendor: vendor || null,
        price: price ? Number(price) : null,
        storage_location: storage || null,
        status,
      }
      await createSpool(payload)
      setMessage('Spool created successfully.')
      setPurchaseDate('')
      setVendor('')
      setPrice('')
      setStorage('')
      setStatus('in_stock')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create spool')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <p className="eyebrow">Add Spool</p>
          <h1>Manual entry</h1>
          <p className="muted">Create a spool linked to an existing product.</p>
        </div>
        <Link className="button" to="/spools">
          Back to spools
        </Link>
      </div>

      <div className="card">
        <form className="form" onSubmit={handleSubmit}>
          <label>
            <span>Product</span>
            <select value={productId} onChange={(e) => setProductId(Number(e.target.value))} required>
              <option value="">Select a product</option>
              {products.map((product) => (
                <option key={product.id} value={product.id}>
                  {product.brand} – {product.material} – {product.color_name}
                </option>
              ))}
            </select>
          </label>

          <label>
            <span>Purchase date</span>
            <input type="date" value={purchaseDate} onChange={(e) => setPurchaseDate(e.target.value)} />
          </label>

          <label>
            <span>Vendor</span>
            <input type="text" value={vendor} onChange={(e) => setVendor(e.target.value)} placeholder="Amazon, Bambu..." />
          </label>

          <label>
            <span>Price (per spool)</span>
            <input
              type="number"
              step="0.01"
              value={price}
              onChange={(e) => setPrice(e.target.value)}
              placeholder="e.g. 25.50"
            />
          </label>

          <label>
            <span>Storage location</span>
            <input
              type="text"
              value={storage}
              onChange={(e) => setStorage(e.target.value)}
              placeholder="Shelf A2, Drybox 1..."
            />
          </label>

          <label>
            <span>Status</span>
            <select value={status} onChange={(e) => setStatus(e.target.value as SpoolStatus)}>
              {statuses.map((entry) => (
                <option key={entry.value} value={entry.value}>
                  {entry.label}
                </option>
              ))}
            </select>
          </label>

          {message && <p className="success">{message}</p>}
          {error && <p className="error">{error}</p>}

          <button type="submit" className="button primary" disabled={submitting}>
            {submitting ? 'Saving...' : 'Create spool'}
          </button>
        </form>
      </div>
    </div>
  )
}

export default AddSpoolPage
