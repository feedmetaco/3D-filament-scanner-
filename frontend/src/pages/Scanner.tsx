import { useState, useRef } from 'react';
import type { ChangeEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { ocrApi, productsApi, spoolsApi, invoiceApi } from '../services/api';
import type { ParsedLabel } from '../services/api';

export default function Scanner() {
  const [image, setImage] = useState<File | null>(null);
  const [preview, setPreview] = useState<string>('');
  const [parsed, setParsed] = useState<ParsedLabel | null>(null);
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState<'capture' | 'preview' | 'parsed'>('capture');
  const fileInputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();

  // Form state for parsed data
  const [formData, setFormData] = useState({
    brand: '',
    material: '',
    color_name: '',
    diameter_mm: 1.75,
    barcode: '',
    vendor: '',
    price: '',
    storage_location: '',
  });

  const handleCapture = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setImage(file);
      setPreview(URL.createObjectURL(file));
      setStep('preview');
    }
  };

  const handleScan = async () => {
    if (!image) return;

    setLoading(true);
    try {
      const { data } = await ocrApi.parseLabel(image);
      setParsed(data);

      // Populate form with parsed data
      setFormData({
        brand: data.brand || '',
        material: data.material || '',
        color_name: data.color_name || '',
        diameter_mm: data.diameter_mm || 1.75,
        barcode: data.barcode || '',
        vendor: '',
        price: '',
        storage_location: '',
      });

      setStep('parsed');
    } catch (error) {
      console.error('OCR failed:', error);
      alert('Failed to scan label. Please try again or enter manually.');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      // Create Product
      const productData = {
        brand: formData.brand,
        material: formData.material,
        color_name: formData.color_name,
        diameter_mm: formData.diameter_mm,
        barcode: formData.barcode || undefined,
      };

      const { data: product } = await productsApi.create(productData);

      // Create Spool linked to Product
      const spoolData = {
        product_id: product.id,
        vendor: formData.vendor || undefined,
        price: formData.price ? parseFloat(formData.price) : undefined,
        storage_location: formData.storage_location || undefined,
        status: 'in_stock' as const,
      };

      await spoolsApi.create(spoolData);

      // Navigate to inventory
      navigate('/inventory');
    } catch (error) {
      console.error('Save failed:', error);
      alert('Failed to save. Please try again.');
    }
  };

  const handleReset = () => {
    setImage(null);
    setPreview('');
    setParsed(null);
    setStep('capture');
    setFormData({
      brand: '',
      material: '',
      color_name: '',
      diameter_mm: 1.75,
      barcode: '',
      vendor: '',
      price: '',
      storage_location: '',
    });
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handlePdfUpload = async (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setLoading(true);
    try {
      const result = await invoiceApi.importInvoice(file);

      alert(
        `Invoice imported successfully!\n\n` +
        `Order: ${result.order_number}\n` +
        `Vendor: ${result.vendor}\n` +
        `Products created: ${result.products_created}\n` +
        `Spools created: ${result.spools_created}`
      );

      // Navigate to inventory
      navigate('/inventory');
    } catch (error) {
      console.error('PDF import failed:', error);
      alert('Failed to import PDF invoice. Please try again or check the file format.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto px-4 py-6 space-y-6">
      {/* Header */}
      <div className="space-y-2">
        <h2 className="text-2xl font-mono tracking-tight">
          Label Scanner
        </h2>
        <p className="text-sm text-zinc-500 font-mono">
          STEP {step === 'capture' ? '1' : step === 'preview' ? '2' : '3'}/3 ·{' '}
          {step === 'capture' && 'CAPTURE IMAGE'}
          {step === 'preview' && 'SCAN LABEL'}
          {step === 'parsed' && 'VERIFY & SAVE'}
        </p>
      </div>

      {/* Capture Step */}
      {step === 'capture' && (
        <div className="space-y-4">
          <div className="relative aspect-[4/3] bg-zinc-900 border-2 border-dashed border-zinc-700 rounded-lg overflow-hidden flex items-center justify-center">
            <div className="text-center space-y-3 p-6">
              <div className="w-16 h-16 mx-auto border-2 border-cyan-500/30 rounded-lg flex items-center justify-center">
                <svg className="w-8 h-8 text-cyan-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
              </div>
              <p className="text-sm font-mono text-zinc-400">
                TAP TO CAPTURE
              </p>
            </div>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              capture="environment"
              onChange={handleCapture}
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
            />
          </div>

          <button
            onClick={() => navigate('/products/new')}
            className="w-full py-3 bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 text-zinc-300 font-mono text-sm transition-colors"
          >
            OR ENTER MANUALLY
          </button>

          {/* PDF Invoice Upload */}
          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-zinc-800"></div>
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-background px-2 text-zinc-600 font-mono">Or bulk import</span>
            </div>
          </div>

          <label className="w-full block">
            <input
              type="file"
              accept="application/pdf"
              onChange={handlePdfUpload}
              className="hidden"
            />
            <div className="w-full py-3 bg-purple-900/30 hover:bg-purple-900/50 border border-purple-700/50 text-purple-300 font-mono text-sm transition-colors cursor-pointer text-center flex items-center justify-center gap-2">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
              </svg>
              UPLOAD PDF INVOICE
            </div>
          </label>
        </div>
      )}

      {/* Preview Step */}
      {step === 'preview' && (
        <div className="space-y-4">
          <div className="relative aspect-[4/3] bg-zinc-900 rounded-lg overflow-hidden border border-zinc-800">
            <img src={preview} alt="Label preview" className="w-full h-full object-contain" />
            <div className="absolute top-2 right-2 flex gap-2">
              <button
                onClick={handleReset}
                className="p-2 bg-zinc-900/90 backdrop-blur-sm border border-zinc-700 rounded text-zinc-400 hover:text-zinc-100 transition-colors"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>

          <button
            onClick={handleScan}
            disabled={loading}
            className="w-full py-4 bg-cyan-600 hover:bg-cyan-500 disabled:bg-cyan-900 disabled:text-cyan-700 text-white font-mono text-sm font-bold tracking-wide transition-all transform active:scale-[0.98] disabled:cursor-not-allowed disabled:transform-none"
          >
            {loading ? (
              <span className="flex items-center justify-center gap-2">
                <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                PROCESSING...
              </span>
            ) : (
              'SCAN LABEL'
            )}
          </button>
        </div>
      )}

      {/* Parsed Step */}
      {step === 'parsed' && parsed && (
        <div className="space-y-6">
          {/* Preview thumbnail */}
          <div className="relative h-32 bg-zinc-900 rounded overflow-hidden border border-zinc-800">
            <img src={preview} alt="Scanned label" className="w-full h-full object-cover opacity-60" />
            <div className="absolute inset-0 bg-gradient-to-t from-zinc-900 to-transparent"></div>
            <button
              onClick={handleReset}
              className="absolute top-2 right-2 p-1.5 bg-zinc-900/90 backdrop-blur-sm border border-zinc-700 rounded text-zinc-400 hover:text-zinc-100 transition-colors"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            </button>
          </div>

          {/* Form */}
          <div className="space-y-4 bg-zinc-900/50 border border-zinc-800 rounded-lg p-4">
            <p className="text-xs font-mono text-zinc-500 uppercase tracking-wide">Product Details</p>

            <div className="space-y-3">
              <div>
                <label className="block text-xs font-mono text-zinc-400 mb-1.5">BRAND</label>
                <input
                  type="text"
                  value={formData.brand}
                  onChange={(e) => setFormData({ ...formData, brand: e.target.value })}
                  className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 text-zinc-100 font-mono text-sm focus:outline-none focus:border-cyan-500 transition-colors"
                  placeholder="Enter brand name"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-mono text-zinc-400 mb-1.5">MATERIAL</label>
                  <input
                    type="text"
                    value={formData.material}
                    onChange={(e) => setFormData({ ...formData, material: e.target.value })}
                    className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 text-zinc-100 font-mono text-sm focus:outline-none focus:border-cyan-500 transition-colors"
                    placeholder="PLA"
                  />
                </div>

                <div>
                  <label className="block text-xs font-mono text-zinc-400 mb-1.5">DIAMETER</label>
                  <select
                    value={formData.diameter_mm}
                    onChange={(e) => setFormData({ ...formData, diameter_mm: parseFloat(e.target.value) })}
                    className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 text-zinc-100 font-mono text-sm focus:outline-none focus:border-cyan-500 transition-colors"
                  >
                    <option value="1.75">1.75mm</option>
                    <option value="2.85">2.85mm</option>
                    <option value="3.0">3.00mm</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-mono text-zinc-400 mb-1.5">COLOR</label>
                <input
                  type="text"
                  value={formData.color_name}
                  onChange={(e) => setFormData({ ...formData, color_name: e.target.value })}
                  className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 text-zinc-100 font-mono text-sm focus:outline-none focus:border-cyan-500 transition-colors"
                  placeholder="Color name"
                />
              </div>

              <div>
                <label className="block text-xs font-mono text-zinc-400 mb-1.5">BARCODE (Optional)</label>
                <input
                  type="text"
                  value={formData.barcode}
                  onChange={(e) => setFormData({ ...formData, barcode: e.target.value })}
                  className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 text-zinc-100 font-mono text-sm focus:outline-none focus:border-cyan-500 transition-colors"
                  placeholder="Barcode if detected"
                />
              </div>
            </div>
          </div>

          {/* Spool Details */}
          <div className="space-y-4 bg-zinc-900/50 border border-zinc-800 rounded-lg p-4">
            <p className="text-xs font-mono text-zinc-500 uppercase tracking-wide">Spool Details</p>

            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-mono text-zinc-400 mb-1.5">VENDOR</label>
                  <input
                    type="text"
                    value={formData.vendor}
                    onChange={(e) => setFormData({ ...formData, vendor: e.target.value })}
                    className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 text-zinc-100 font-mono text-sm focus:outline-none focus:border-cyan-500 transition-colors"
                    placeholder="Amazon"
                  />
                </div>

                <div>
                  <label className="block text-xs font-mono text-zinc-400 mb-1.5">PRICE</label>
                  <input
                    type="number"
                    step="0.01"
                    value={formData.price}
                    onChange={(e) => setFormData({ ...formData, price: e.target.value })}
                    className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 text-zinc-100 font-mono text-sm focus:outline-none focus:border-cyan-500 transition-colors"
                    placeholder="0.00"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-mono text-zinc-400 mb-1.5">STORAGE</label>
                <input
                  type="text"
                  value={formData.storage_location}
                  onChange={(e) => setFormData({ ...formData, storage_location: e.target.value })}
                  className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 text-zinc-100 font-mono text-sm focus:outline-none focus:border-cyan-500 transition-colors"
                  placeholder="Shelf location"
                />
              </div>
            </div>
          </div>

          {/* Actions */}
          <button
            onClick={handleSave}
            className="w-full py-4 bg-green-600 hover:bg-green-500 text-white font-mono text-sm font-bold tracking-wide transition-all transform active:scale-[0.98]"
          >
            SAVE TO INVENTORY
          </button>
        </div>
      )}
    </div>
  );
}
