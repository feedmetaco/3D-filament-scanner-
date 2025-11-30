import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { fetchProducts, fetchSpools } from '../api'
import { Product, Spool, SpoolStatus } from '../types'

const statusLabels: Record<SpoolStatus, string> = {
  in_stock: 'In stock',
  used_up: 'Used up',
  donated: 'Donated',
  lost: 'Lost',
}

function SpoolListPage() {
  const [spools, setSpools] = useState<Spool[]>([])
  const [products, setProducts] = useState<Product[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [statusFilter, setStatusFilter] = useState('')
  const [search, setSearch] = useState('')

  useEffect(() => {
    const load = async () => {
      try {
        setLoading(true)
        const [spoolData, productData] = await Promise.all([fetchSpools(), fetchProducts()])
        setSpools(spoolData)
        setProducts(productData)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load spools')
      } finally {
        setLoading(false)
      }
    }

    load()
  }, [])

  const productMap = useMemo(
    () => Object.fromEntries(products.map((product) => [product.id, product])),
    [products],
  )

  const filteredSpools = useMemo(() => {
    return spools.filter((spool) => {
      if (statusFilter && spool.status !== statusFilter) return false
      if (!search.trim()) return true

      const product = productMap[spool.product_id]
      const haystack = [
        product?.brand,
        product?.material,
        product?.color_name,
        spool.vendor,
        spool.storage_location,
      ]
        .filter(Boolean)
        .join(' ')
        .toLowerCase()

      return haystack.includes(search.toLowerCase())
    })
  }, [spools, statusFilter, search, productMap])

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <p className="eyebrow">Phase 2 – Inventory</p>
          <h1>Spools</h1>
          <p className="muted">Search by product info or vendor, and filter by status.</p>
        </div>
        <Link className="button" to="/add-spool">
          + Add spool
        </Link>
      </div>

      <div className="card">
        <div className="filters">
          <label className="filter">
            <span>Status</span>
            <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
              <option value="">All</option>
              {Object.entries(statusLabels).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </label>
          <label className="filter">
            <span>Search</span>
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Brand, material, vendor, storage"
            />
          </label>
        </div>

        {loading && <p>Loading spools...</p>}
        {error && <p className="error">{error}</p>}

        {!loading && !error && (
          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th>Brand / Line</th>
                  <th>Material</th>
                  <th>Color</th>
                  <th>Status</th>
                  <th>Vendor</th>
                  <th>Storage</th>
                </tr>
              </thead>
              <tbody>
                {filteredSpools.map((spool) => {
                  const product = productMap[spool.product_id]
                  return (
                    <tr key={spool.id}>
                      <td>
                        {product ? (
                          <Link to={`/products/${product.id}`} className="pill">
                            {product.brand} {product.line ? `• ${product.line}` : ''}
                          </Link>
                        ) : (
                          'Unknown product'
                        )}
                      </td>
                      <td>{product?.material ?? '—'}</td>
                      <td>{product?.color_name ?? '—'}</td>
                      <td>
                        <span className={`status ${spool.status}`}>{statusLabels[spool.status]}</span>
                      </td>
                      <td>{spool.vendor || '—'}</td>
                      <td>{spool.storage_location || '—'}</td>
                    </tr>
                  )
                })}
                {filteredSpools.length === 0 && (
                  <tr>
                    <td colSpan={6} className="muted">
                      No spools found. Try adjusting filters or add a new spool.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

export default SpoolListPage
