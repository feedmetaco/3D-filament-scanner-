import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { fetchProducts, fetchSpools } from '../api'
import { Product, Spool } from '../types'

const activeStatuses = new Set(['in_stock'])

const FieldSelect = ({
  label,
  value,
  options,
  onChange,
}: {
  label: string
  value: string
  options: string[]
  onChange: (value: string) => void
}) => {
  return (
    <label className="filter">
      <span>{label}</span>
      <select value={value} onChange={(e) => onChange(e.target.value)}>
        <option value="">All</option>
        {options.map((option) => (
          <option key={option} value={option}>
            {option}
          </option>
        ))}
      </select>
    </label>
  )
}

function InventoryPage() {
  const [products, setProducts] = useState<Product[]>([])
  const [spools, setSpools] = useState<Spool[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [brandFilter, setBrandFilter] = useState('')
  const [materialFilter, setMaterialFilter] = useState('')
  const [colorFilter, setColorFilter] = useState('')

  useEffect(() => {
    const load = async () => {
      try {
        setLoading(true)
        const [productData, spoolData] = await Promise.all([fetchProducts(), fetchSpools()])
        setProducts(productData)
        setSpools(spoolData)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load inventory')
      } finally {
        setLoading(false)
      }
    }

    load()
  }, [])

  const activeSpoolCounts = useMemo(() => {
    return spools.reduce<Record<number, number>>((acc, spool) => {
      if (activeStatuses.has(spool.status)) {
        acc[spool.product_id] = (acc[spool.product_id] ?? 0) + 1
      }
      return acc
    }, {})
  }, [spools])

  const filteredProducts = useMemo(() => {
    return products.filter((product) => {
      if (brandFilter && product.brand !== brandFilter) return false
      if (materialFilter && product.material !== materialFilter) return false
      if (colorFilter && product.color_name !== colorFilter) return false
      return true
    })
  }, [products, brandFilter, materialFilter, colorFilter])

  const brandOptions = useMemo(
    () => Array.from(new Set(products.map((p) => p.brand))).sort(),
    [products],
  )
  const materialOptions = useMemo(
    () => Array.from(new Set(products.map((p) => p.material))).sort(),
    [products],
  )
  const colorOptions = useMemo(
    () => Array.from(new Set(products.map((p) => p.color_name))).sort(),
    [products],
  )

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <p className="eyebrow">Phase 2 – Inventory</p>
          <h1>Products</h1>
          <p className="muted">Filter by brand, material, and color to see available spools.</p>
        </div>
      </div>

      <div className="card">
        <div className="filters">
          <FieldSelect label="Brand" value={brandFilter} options={brandOptions} onChange={setBrandFilter} />
          <FieldSelect
            label="Material"
            value={materialFilter}
            options={materialOptions}
            onChange={setMaterialFilter}
          />
          <FieldSelect label="Color" value={colorFilter} options={colorOptions} onChange={setColorFilter} />
        </div>

        {loading && <p>Loading inventory...</p>}
        {error && <p className="error">{error}</p>}

        {!loading && !error && (
          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th>Brand</th>
                  <th>Line</th>
                  <th>Material</th>
                  <th>Color</th>
                  <th>Diameter</th>
                  <th>Active Spools</th>
                </tr>
              </thead>
              <tbody>
                {filteredProducts.map((product) => (
                  <tr key={product.id}>
                    <td>{product.brand}</td>
                    <td>{product.line || '—'}</td>
                    <td>{product.material}</td>
                    <td>{product.color_name}</td>
                    <td>{product.diameter_mm} mm</td>
                    <td>
                      <Link to={`/products/${product.id}`} className="pill">
                        {activeSpoolCounts[product.id] ?? 0} in stock
                      </Link>
                    </td>
                  </tr>
                ))}
                {filteredProducts.length === 0 && (
                  <tr>
                    <td colSpan={6} className="muted">
                      No products match the selected filters.
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

export default InventoryPage
