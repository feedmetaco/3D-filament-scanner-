import { useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { fetchProduct, fetchSpools } from '../api'
import { Product, Spool } from '../types'

function ProductDetailPage() {
  const { id } = useParams<{ id: string }>()
  const productId = Number(id)

  const [product, setProduct] = useState<Product | null>(null)
  const [spools, setSpools] = useState<Spool[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!productId) return

    const load = async () => {
      try {
        setLoading(true)
        const [productData, spoolData] = await Promise.all([
          fetchProduct(productId),
          fetchSpools(),
        ])
        setProduct(productData)
        setSpools(spoolData.filter((spool) => spool.product_id === productId))
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load product')
      } finally {
        setLoading(false)
      }
    }

    load()
  }, [productId])

  const activeSpools = useMemo(
    () => spools.filter((spool) => spool.status === 'in_stock').length,
    [spools],
  )

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <p className="eyebrow">Product</p>
          <h1>{product ? `${product.brand} ${product.color_name}` : 'Loading...'}</h1>
          {product && (
            <p className="muted">
              {product.material} {product.line ? `• ${product.line}` : ''} • {product.diameter_mm} mm
            </p>
          )}
        </div>
        <Link className="button" to="/spools">
          Back to spools
        </Link>
      </div>

      <div className="card">
        {loading && <p>Loading product...</p>}
        {error && <p className="error">{error}</p>}

        {!loading && !error && product && (
          <div className="product-grid">
            <div>
              <h3>Details</h3>
              <ul className="detail-list">
                <li>
                  <span>Brand</span>
                  <strong>{product.brand}</strong>
                </li>
                <li>
                  <span>Line</span>
                  <strong>{product.line || '—'}</strong>
                </li>
                <li>
                  <span>Material</span>
                  <strong>{product.material}</strong>
                </li>
                <li>
                  <span>Color</span>
                  <strong>{product.color_name}</strong>
                </li>
                <li>
                  <span>Diameter</span>
                  <strong>{product.diameter_mm} mm</strong>
                </li>
                <li>
                  <span>Notes</span>
                  <strong>{product.notes || '—'}</strong>
                </li>
              </ul>
            </div>

            <div>
              <h3>Spools</h3>
              <p className="muted">{activeSpools} active in-stock spools</p>
              <div className="table-wrapper">
                <table>
                  <thead>
                    <tr>
                      <th>Status</th>
                      <th>Vendor</th>
                      <th>Purchase Date</th>
                      <th>Storage</th>
                    </tr>
                  </thead>
                  <tbody>
                    {spools.map((spool) => (
                      <tr key={spool.id}>
                        <td>{spool.status.replace('_', ' ')}</td>
                        <td>{spool.vendor || '—'}</td>
                        <td>{spool.purchase_date || '—'}</td>
                        <td>{spool.storage_location || '—'}</td>
                      </tr>
                    ))}
                    {spools.length === 0 && (
                      <tr>
                        <td colSpan={4} className="muted">
                          No spools for this product yet.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default ProductDetailPage
