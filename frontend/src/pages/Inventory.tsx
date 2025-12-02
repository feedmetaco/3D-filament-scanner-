import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { spoolsApi, productsApi } from '../services/api';
import type { Spool, Product } from '../services/api';

type SpoolWithProduct = Spool & { product?: Product };

export default function Inventory() {
  const [spools, setSpools] = useState<SpoolWithProduct[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>('all');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [spoolsRes, productsRes] = await Promise.all([
        spoolsApi.list(),
        productsApi.list(),
      ]);

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

  const filteredSpools = filter === 'all'
    ? spools
    : spools.filter(s => s.status === filter);

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

  // Helper to calculate total spools per product if needed, but user asked to replace diameter with spool count.
  // Since we are listing individual spools, maybe they mean "Spool #123" or similar?
  // Or maybe they want to group by product?
  // Based on "instead of 1.75mm it should say number of spool", I'll interpret this as showing the Spool ID or a sequential count.
  // Let's stick to showing the Spool ID for now as it's unique.

  if (loading) {
    return (
      <div className="max-w-md mx-auto px-4 py-6 flex items-center justify-center min-h-[50vh]">
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
    <div className="max-w-md mx-auto space-y-6 pb-6">
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
      <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-hide mask-fade-right">
        {[
          { label: 'ALL', value: 'all' },
          { label: 'IN STOCK', value: 'in_stock' },
          { label: 'USED UP', value: 'used_up' },
          { label: 'DONATED', value: 'donated' },
          { label: 'LOST', value: 'lost' },
        ].map(({ label, value }) => (
          <button
            key={value}
            onClick={() => setFilter(value)}
            className={`px-3 py-1.5 text-[10px] font-mono font-bold tracking-wider whitespace-nowrap transition-all uppercase border clip-corner ${
              filter === value
                ? 'bg-primary/20 text-primary border-primary'
                : 'bg-surface text-muted border-white/10 hover:text-white hover:border-white/30'
            }`}
          >
            {label}
          </button>
        ))}
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
            <Link
              key={spool.id}
              to={`/spools/${spool.id}/edit`}
              className="block bg-surface border border-white/5 hover:border-primary/50 hover:bg-white/5 transition-all group relative overflow-hidden clip-corner pl-1"
            >
               {/* Status Indicator Line */}
               <div className={`absolute left-0 top-0 bottom-0 w-[3px] ${
                  spool.status === 'in_stock' ? 'bg-tertiary' : 
                  spool.status === 'used_up' ? 'bg-muted' :
                  spool.status === 'donated' ? 'bg-primary' : 'bg-secondary'
               }`}></div>

              <div className="p-4 flex items-start justify-between gap-4">
                <div className="flex-1 space-y-2">
                  {/* Product Info */}
                  <div>
                    <div className="flex items-center gap-2">
                        <h3 className="font-bold text-base text-white group-hover:text-primary transition-colors uppercase tracking-wide">
                        {spool.product?.brand || 'Unknown'}
                        </h3>
                        <span className="text-[10px] font-mono text-black bg-primary px-1 rounded-sm font-bold">
                           {spool.product?.material || 'MAT'}
                        </span>
                    </div>
                    
                    <p className="text-xs text-muted font-mono mt-1 uppercase tracking-wider flex items-center gap-2">
                      <span className={`w-2 h-2 rounded-full`} style={{backgroundColor: 'white'}}></span>
                      {spool.product?.color_name || 'Color'} 
                      <span className="text-white/20">|</span>
                      <span className="text-white">ID: #{spool.id}</span>
                    </p>
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
                    {spool.storage_location && (
                      <span className="flex items-center gap-1 text-tertiary">
                        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                        </svg>
                        {spool.storage_location}
                      </span>
                    )}
                  </div>
                </div>

                {/* Status Badge */}
                <div className="flex flex-col items-end gap-1">
                   <div className={`px-2 py-0.5 border text-[10px] font-mono font-bold uppercase tracking-widest ${getStatusColor(spool.status)}`}>
                     {getStatusLabel(spool.status)}
                   </div>
                   {spool.price && (
                      <div className="text-xs font-mono text-white/70">
                         ${spool.price.toFixed(2)}
                      </div>
                   )}
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
