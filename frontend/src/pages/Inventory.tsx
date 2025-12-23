import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { spoolsApi, productsApi } from '../services/api';
import type { Product, Spool, SpoolDetail } from '../services/api';

type SpoolWithProduct = SpoolDetail & { product?: Product };
type InventoryFilters = {
  brand: string;
  material: string;
  color: string;
  status: string;
  location: string;
};

export default function Inventory() {
  const [spools, setSpools] = useState<SpoolWithProduct[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [selectedSpool, setSelectedSpool] = useState<SpoolWithProduct | null>(null);
  const [statusUpdatingId, setStatusUpdatingId] = useState<number | null>(null);
  const [locationUpdatingId, setLocationUpdatingId] = useState<number | null>(null);
  const [editingLocationId, setEditingLocationId] = useState<number | null>(null);
  const [locationDraft, setLocationDraft] = useState<string>('');
  const [filters, setFilters] = useState<InventoryFilters>({
    brand: '',
    material: '',
    color: '',
    status: 'all',
    location: '',
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [spoolsRes, productsRes] = await Promise.all([
        spoolsApi.list(),
        productsApi.list(),
      ]);

      setProducts(productsRes.data);
      // Map products to spools
      const spoolsWithProducts = spoolsRes.data.map(spool => ({
        ...spool,
        product: productsRes.data.find(p => p.id === spool.product_id),
      }));

      setSpools(spoolsWithProducts);
    } catch (error) {
      console.error('Failed to load inventory:', error);
    } finally {
      setLoading(false);
    }
  };

  const attachProduct = (spool: SpoolDetail): SpoolWithProduct => ({
    ...spool,
    product: products.find(p => p.id === spool.product_id),
  });

  const applySpoolUpdate = (updatedSpool: SpoolDetail) => {
    const spoolWithProduct = attachProduct(updatedSpool);
    setSpools((prev) =>
      prev.some((spool) => spool.id === updatedSpool.id)
        ? prev.map((spool) =>
            spool.id === updatedSpool.id ? { ...spool, ...spoolWithProduct } : spool
          )
        : [...prev, spoolWithProduct]
    );
    setSelectedSpool((prev) =>
      prev && prev.id === updatedSpool.id ? { ...prev, ...spoolWithProduct } : prev
    );
    return spoolWithProduct;
  };

  const openSpoolDetail = async (spool: SpoolWithProduct) => {
    setSelectedSpool(spool);
    setDetailLoading(true);
    try {
      const { data } = await spoolsApi.get(spool.id);
      const spoolWithProduct = applySpoolUpdate(data);
      setSelectedSpool(spoolWithProduct);
    } catch (error) {
      console.error('Failed to load spool history', error);
    } finally {
      setDetailLoading(false);
    }
  };

  const handleStatusUpdate = async (spool: SpoolWithProduct, newStatus: Spool['status']) => {
    if (spool.status === newStatus) return;
    setStatusUpdatingId(spool.id);
    try {
      const { data } = await spoolsApi.update(spool.id, { status: newStatus });
      applySpoolUpdate(data);
    } catch (error) {
      console.error('Failed to update status:', error);
      alert('Could not update status. Please try again.');
    } finally {
      setStatusUpdatingId(null);
    }
  };

  const startLocationEdit = (spool: SpoolWithProduct) => {
    setEditingLocationId(spool.id);
    setLocationDraft(spool.storage_location || '');
  };

  const handleLocationSave = async (spool: SpoolWithProduct) => {
    setLocationUpdatingId(spool.id);
    try {
      const { data } = await spoolsApi.update(spool.id, {
        storage_location: locationDraft.trim() || null,
      });
      applySpoolUpdate(data);
      setEditingLocationId(null);
      setLocationDraft('');
    } catch (error) {
      console.error('Failed to update location:', error);
      alert('Could not update location. Please try again.');
    } finally {
      setLocationUpdatingId(null);
    }
  };

  const filteredSpools = useMemo(() => {
    return spools.filter((spool) => {
      const product = spool.product;
      if (filters.status !== 'all' && spool.status !== filters.status) return false;
      if (filters.brand && product?.brand !== filters.brand) return false;
      if (filters.material && product?.material !== filters.material) return false;
      if (filters.color && product?.color_name !== filters.color) return false;
      if (
        filters.location &&
        !(spool.storage_location || '').toLowerCase().includes(filters.location.toLowerCase())
      ) {
        return false;
      }
      return true;
    });
  }, [filters, spools]);

  const brandOptions = useMemo(
    () => Array.from(new Set(products.map((p) => p.brand))).sort(),
    [products]
  );
  const materialOptions = useMemo(
    () => Array.from(new Set(products.map((p) => p.material))).sort(),
    [products]
  );
  const colorOptions = useMemo(
    () => Array.from(new Set(products.map((p) => p.color_name))).sort(),
    [products]
  );
  const locationOptions = useMemo(
    () =>
      Array.from(new Set(spools.map((spool) => spool.storage_location).filter(Boolean))).sort(),
    [spools]
  );

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'in_stock':
        return 'text-tertiary bg-tertiary/5 border-tertiary/30';
      case 'used_up':
        return 'text-muted bg-surfaceHighlight border-white/5';
      case 'donated':
        return 'text-primary bg-primary/5 border-primary/30';
      case 'lost':
        return 'text-secondary bg-secondary/5 border-secondary/30';
      default:
        return 'text-muted bg-surfaceHighlight border-white/5';
    }
  };

  const getStatusLabel = (status: string) => {
    return status.toUpperCase().replace('_', ' ');
  };

  const clearFilters = () =>
    setFilters({
      brand: '',
      material: '',
      color: '',
      status: 'all',
      location: '',
    });

  const hasActiveFilters =
    filters.status !== 'all' || filters.brand || filters.material || filters.color || filters.location;

  const formatDate = (dateString?: string) => {
    if (!dateString) return '—';
    return new Date(dateString).toLocaleDateString();
  };

  if (loading) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-6 flex items-center justify-center min-h-[50vh]">
        <div className="text-center space-y-4">
          <div className="relative w-16 h-16 mx-auto">
             <div className="absolute inset-0 border-t-2 border-primary rounded-full animate-spin"></div>
             <div className="absolute inset-2 border-b-2 border-secondary rounded-full animate-spin duration-300"></div>
          </div>
          <p className="text-xs font-mono text-primary tracking-widest uppercase animate-pulse">Accessing Database...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6 pb-12 px-4">
      {/* Header */}
      <div className="flex items-end justify-between border-b border-white/10 pb-4">
        <div>
          <h2 className="text-xl font-bold text-white tracking-wider uppercase">Inventory</h2>
          <p className="text-xs text-muted font-mono mt-1">
             DATA_COUNT: <span className="text-primary">{filteredSpools.length}</span> UNITS
          </p>
        </div>
        <Link
          to="/spools/new"
          className="px-4 py-2 bg-primary/10 hover:bg-primary/20 border border-primary/50 hover:border-primary text-primary font-mono text-xs font-bold tracking-widest transition-all uppercase clip-corner"
        >
          + Register_Unit
        </Link>
      </div>

      {/* Filters */}
      <div className="space-y-3 bg-surface/50 border border-white/5 rounded-lg p-3">
        <div className="flex gap-2 overflow-x-auto pb-1 scrollbar-hide mask-fade-right">
          {[
            { label: 'ALL', value: 'all' },
            { label: 'IN STOCK', value: 'in_stock' },
            { label: 'USED UP', value: 'used_up' },
            { label: 'DONATED', value: 'donated' },
            { label: 'LOST', value: 'lost' },
          ].map(({ label, value }) => (
            <button
              key={value}
              onClick={() => setFilters((prev) => ({ ...prev, status: value }))}
              className={`px-3 py-1.5 text-[10px] font-mono font-bold tracking-wider whitespace-nowrap transition-all uppercase border clip-corner ${
                filters.status === value
                  ? 'bg-primary/20 text-primary border-primary'
                  : 'bg-surface text-muted border-white/10 hover:text-white hover:border-white/30'
              }`}
            >
              {label}
            </button>
          ))}
        </div>

        <div className="grid grid-cols-2 gap-2">
          <select
            value={filters.brand}
            onChange={(e) => setFilters((prev) => ({ ...prev, brand: e.target.value }))}
            className="w-full px-3 py-2 bg-black/30 border border-white/10 text-xs font-mono text-white/80 focus:border-primary outline-none clip-corner"
          >
            <option value="">Filter by brand</option>
            {brandOptions.map((brand) => (
              <option key={brand} value={brand}>
                {brand}
              </option>
            ))}
          </select>
          <select
            value={filters.material}
            onChange={(e) => setFilters((prev) => ({ ...prev, material: e.target.value }))}
            className="w-full px-3 py-2 bg-black/30 border border-white/10 text-xs font-mono text-white/80 focus:border-primary outline-none clip-corner"
          >
            <option value="">Filter by material</option>
            {materialOptions.map((material) => (
              <option key={material} value={material}>
                {material}
              </option>
            ))}
          </select>
          <select
            value={filters.color}
            onChange={(e) => setFilters((prev) => ({ ...prev, color: e.target.value }))}
            className="w-full px-3 py-2 bg-black/30 border border-white/10 text-xs font-mono text-white/80 focus:border-primary outline-none clip-corner"
          >
            <option value="">Filter by color</option>
            {colorOptions.map((color) => (
              <option key={color} value={color}>
                {color}
              </option>
            ))}
          </select>
          <div className="flex gap-2">
            <select
              value={filters.location}
              onChange={(e) => setFilters((prev) => ({ ...prev, location: e.target.value }))}
              className="w-full px-3 py-2 bg-black/30 border border-white/10 text-xs font-mono text-white/80 focus:border-primary outline-none clip-corner"
            >
              <option value="">Filter by location</option>
              {locationOptions.map((location) => (
                <option key={location} value={location as string}>
                  {location}
                </option>
              ))}
            </select>
          </div>
        </div>

        {hasActiveFilters && (
          <button
            onClick={clearFilters}
            className="text-[11px] font-mono text-muted hover:text-white transition-colors underline underline-offset-4"
          >
            Reset all filters
          </button>
        )}
      </div>

      {/* Spool List */}
      {filteredSpools.length === 0 ? (
        <div className="text-center py-12 space-y-4 border border-dashed border-white/10 rounded-lg bg-surface/30">
          <div className="w-16 h-16 mx-auto border border-white/10 flex items-center justify-center rounded-full bg-black/20">
            <svg className="w-8 h-8 text-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
            </svg>
          </div>
          <div>
             <p className="text-sm font-bold text-white uppercase tracking-wide">No Data Found</p>
             <p className="text-xs font-mono text-muted mt-1">Query returned 0 results.</p>
          </div>
          <Link
            to="/scanner"
            className="inline-block px-6 py-2 bg-primary/10 hover:bg-primary/20 text-primary font-mono text-xs font-bold tracking-widest uppercase transition-colors border border-primary/50 clip-corner"
          >
            Initiate Scan
          </Link>
        </div>
      ) : (
        <div className="space-y-3">
          {filteredSpools.map((spool) => (
            <div
              key={spool.id}
              onClick={() => openSpoolDetail(spool)}
              className="block bg-surface border border-white/5 hover:border-primary/50 hover:bg-white/5 transition-all group relative overflow-hidden clip-corner pl-1 cursor-pointer"
            >
              {/* Status Indicator Line */}
              <div
                className={`absolute left-0 top-0 bottom-0 w-[3px] ${
                  spool.status === 'in_stock'
                    ? 'bg-tertiary'
                    : spool.status === 'used_up'
                    ? 'bg-muted'
                    : spool.status === 'donated'
                    ? 'bg-primary'
                    : 'bg-secondary'
                }`}
              ></div>

              <div className="p-4 space-y-3">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 space-y-1.5">
                    {/* Product Info */}
                    <div className="flex items-center gap-2">
                      <h3 className="font-bold text-base text-white group-hover:text-primary transition-colors uppercase tracking-wide">
                        {spool.product?.brand || 'Unknown'}
                      </h3>
                      <span className="text-[10px] font-mono text-black bg-primary px-1 rounded-sm font-bold">
                        {spool.product?.material || 'MAT'}
                      </span>
                    </div>
                    <p className="text-xs text-muted font-mono uppercase tracking-wider flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-white/80"></span>
                      {spool.product?.color_name || 'Color'}
                      <span className="text-white/20">|</span>
                      <span className="text-white">ID: #{spool.id}</span>
                    </p>
                  </div>

                  {/* Status Badge + Edit */}
                  <div className="flex flex-col items-end gap-2">
                    <div
                      className={`px-2 py-0.5 border text-[10px] font-mono font-bold uppercase tracking-widest ${getStatusColor(
                        spool.status
                      )}`}
                    >
                      {getStatusLabel(spool.status)}
                    </div>
                    <Link
                      to={`/spools/${spool.id}/edit`}
                      onClick={(e) => e.stopPropagation()}
                      className="text-[11px] font-mono text-primary underline underline-offset-4 hover:text-white transition-colors"
                    >
                      Edit details
                    </Link>
                  </div>
                </div>

                {/* Meta */}
                <div className="flex flex-wrap gap-3 text-[10px] font-mono text-muted uppercase tracking-wider">
                  {spool.vendor && (
                    <span className="flex items-center gap-1">
                      <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
                      </svg>
                      {spool.vendor}
                    </span>
                  )}
                  {spool.price !== undefined && spool.price !== null && (
                    <span className="flex items-center gap-1 text-white">
                      <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8V5m0 11v3" />
                      </svg>
                      ${spool.price.toFixed(2)}
                    </span>
                  )}
                  {spool.purchase_date && (
                    <span className="flex items-center gap-1">
                      <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                      </svg>
                      {formatDate(spool.purchase_date)}
                    </span>
                  )}
                </div>

                <div className="flex items-center justify-between gap-3">
                  {editingLocationId === spool.id ? (
                    <div
                      className="flex items-center gap-2 flex-1"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <input
                        autoFocus
                        value={locationDraft}
                        onChange={(e) => setLocationDraft(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') {
                            e.preventDefault();
                            handleLocationSave(spool);
                          }
                          if (e.key === 'Escape') {
                            setEditingLocationId(null);
                            setLocationDraft('');
                          }
                        }}
                        className="flex-1 px-3 py-2 bg-black/30 border border-primary/30 text-xs text-white font-mono focus:border-primary outline-none clip-corner"
                        placeholder="Shelf, Drawer, etc."
                      />
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleLocationSave(spool);
                        }}
                        disabled={locationUpdatingId === spool.id}
                        className="px-3 py-2 bg-primary/20 text-primary border border-primary/60 text-[11px] font-mono clip-corner disabled:opacity-50"
                      >
                        Save
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setEditingLocationId(null);
                          setLocationDraft('');
                        }}
                        className="px-2 py-2 text-[11px] font-mono text-muted hover:text-white"
                      >
                        Cancel
                      </button>
                    </div>
                  ) : (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        startLocationEdit(spool);
                      }}
                      className="flex items-center gap-2 text-xs font-mono text-tertiary hover:text-white transition-colors"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                      </svg>
                      {spool.storage_location ? spool.storage_location : 'Add location'}
                    </button>
                  )}
                  <div className="flex flex-wrap gap-1 justify-end">
                    {['in_stock', 'used_up', 'donated', 'lost'].map((statusOption) => (
                      <button
                        key={statusOption}
                        onClick={(e) => {
                          e.stopPropagation();
                          handleStatusUpdate(spool, statusOption as Spool['status']);
                        }}
                        disabled={statusUpdatingId === spool.id}
                        className={`px-2 py-1 text-[10px] font-mono uppercase border clip-corner transition-all ${
                          spool.status === statusOption
                            ? 'bg-primary/20 border-primary text-primary'
                            : 'bg-black/40 border-white/10 text-muted hover:text-white hover:border-white/40'
                        }`}
                      >
                        {statusOption.replace('_', ' ')}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Spool Detail Drawer */}
      {selectedSpool && (
        <div
          className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-end justify-center px-4 py-6"
          onClick={() => setSelectedSpool(null)}
        >
          <div
            className="bg-surface border border-white/10 rounded-2xl shadow-xl w-full max-w-2xl overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-start justify-between gap-3 p-4 border-b border-white/5">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <h3 className="text-lg font-bold text-white tracking-wide uppercase">
                    {selectedSpool.product?.brand || 'Unknown'}
                  </h3>
                  <span className="text-[11px] font-mono bg-primary text-black px-2 py-1 rounded-sm">
                    {selectedSpool.product?.material || 'MAT'}
                  </span>
                </div>
                <p className="text-xs font-mono text-muted uppercase tracking-wider">
                  {selectedSpool.product?.color_name || 'Color'} • ID #{selectedSpool.id}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <div
                  className={`px-2 py-1 border text-[10px] font-mono font-bold uppercase tracking-widest ${getStatusColor(
                    selectedSpool.status
                  )}`}
                >
                  {getStatusLabel(selectedSpool.status)}
                </div>
                <button
                  onClick={() => setSelectedSpool(null)}
                  className="p-2 text-muted hover:text-white transition-colors"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>

            <div className="p-4 space-y-4">
              <div className="grid grid-cols-2 gap-3 text-xs font-mono">
                <div className="bg-black/30 border border-white/5 rounded-lg p-3 space-y-1">
                  <p className="text-muted">Vendor</p>
                  <p className="text-white">{selectedSpool.vendor || '—'}</p>
                </div>
                <div className="bg-black/30 border border-white/5 rounded-lg p-3 space-y-1">
                  <p className="text-muted">Purchase Date</p>
                  <p className="text-white">{formatDate(selectedSpool.purchase_date)}</p>
                </div>
                <div className="bg-black/30 border border-white/5 rounded-lg p-3 space-y-1">
                  <p className="text-muted">Price</p>
                  <p className="text-white">
                    {selectedSpool.price !== undefined && selectedSpool.price !== null
                      ? `$${selectedSpool.price.toFixed(2)}`
                      : '—'}
                  </p>
                </div>
                <div className="bg-black/30 border border-white/5 rounded-lg p-3 space-y-1">
                  <p className="text-muted">Location</p>
                  <p className="text-white">{selectedSpool.storage_location || '—'}</p>
                </div>
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <p className="text-sm font-semibold text-white">Status history</p>
                  <button
                    onClick={() => handleStatusUpdate(selectedSpool, 'used_up')}
                    disabled={selectedSpool.status === 'used_up' || statusUpdatingId === selectedSpool.id}
                    className="px-3 py-2 text-[11px] font-mono clip-corner border border-primary/60 text-primary hover:bg-primary/10 disabled:opacity-50"
                  >
                    {selectedSpool.status === 'used_up' ? 'Marked used' : 'Mark used up'}
                  </button>
                </div>

                <div className="bg-black/30 border border-white/5 rounded-lg p-3 max-h-64 overflow-y-auto space-y-3">
                  {detailLoading ? (
                    <div className="flex items-center gap-2 text-xs text-muted font-mono">
                      <div className="w-4 h-4 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                      Loading history...
                    </div>
                  ) : selectedSpool.change_logs && selectedSpool.change_logs.length > 0 ? (
                    selectedSpool.change_logs.map((log) => (
                      <div key={log.id} className="flex gap-3">
                        <div className="w-1 rounded-full bg-primary/40" />
                        <div className="space-y-1">
                          <p className="text-[11px] font-mono text-muted">
                            {new Date(log.created_at).toLocaleString()}
                          </p>
                          {log.from_status || log.to_status ? (
                            <p className="text-sm text-white">
                              {log.from_status ? getStatusLabel(log.from_status) : 'New'} →{' '}
                              {log.to_status ? getStatusLabel(log.to_status) : '—'}
                            </p>
                          ) : null}
                          {log.from_location !== log.to_location && (log.from_location || log.to_location) && (
                            <p className="text-xs text-muted">
                              Location: {log.from_location || '—'} → {log.to_location || '—'}
                            </p>
                          )}
                          {log.note && <p className="text-xs text-muted italic">{log.note}</p>}
                        </div>
                      </div>
                    ))
                  ) : (
                    <p className="text-xs text-muted font-mono">No history yet.</p>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
