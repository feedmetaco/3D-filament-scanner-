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
  const [error, setError] = useState<string | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();

  const MAX_FILE_SIZE = 15 * 1024 * 1024; // 15 MB

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
    if (!file) return;

    setError(null);

    if (!file.type.startsWith('image/')) {
      setError('Please select an image file (JPEG, PNG, WebP, DNG, or TIFF)');
      return;
    }

    if (file.size > MAX_FILE_SIZE) {
      const sizeMB = (file.size / (1024 * 1024)).toFixed(1);
      setError(`File too large: ${sizeMB} MB. Maximum size is 15 MB.`);
      return;
    }

    const ext = file.name.split('.').pop()?.toLowerCase();
    const supportedExts = ['jpg', 'jpeg', 'png', 'webp', 'dng', 'tiff', 'tif', 'mpo'];
    if (!ext || !supportedExts.includes(ext)) {
      setError(`Unsupported file format: .${ext}. Supported formats: ${supportedExts.join(', ').toUpperCase()}`);
      return;
    }

    setImage(file);
    setPreview(URL.createObjectURL(file));
    setStep('preview');
  };

  const handleScan = async () => {
    if (!image) return;

    setLoading(true);
    setError(null);
    setUploadProgress(0);

    let progressInterval: NodeJS.Timeout | null = null;

    try {
      progressInterval = setInterval(() => {
        setUploadProgress(prev => Math.min(prev + 10, 90));
      }, 100);

      const { data } = await ocrApi.parseLabel(image);
      if (progressInterval) clearInterval(progressInterval);
      setUploadProgress(100);

      setParsed(data);

      if ((data as any).error) {
        const errorData = data as any;
        setError(errorData.error || errorData.message || 'OCR processing failed');
        setLoading(false);
        return;
      }

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
    } catch (error: any) {
      if (progressInterval) clearInterval(progressInterval);
      console.error('OCR failed:', error);
      
      let errorMessage = 'Failed to scan label. Please try again or enter manually.';
      if (error?.response?.data) {
        const errorData = error.response.data;
        if (errorData.detail) {
          if (typeof errorData.detail === 'string') {
            errorMessage = errorData.detail;
          } else if (errorData.detail.message) {
            errorMessage = errorData.detail.message;
            if (errorData.detail.suggestion) {
              errorMessage += ` ${errorData.detail.suggestion}`;
            }
          }
        }
      }
      
      setError(errorMessage);
    } finally {
      setLoading(false);
      setUploadProgress(0);
    }
  };

  const handleSave = async () => {
    try {
      const productData = {
        brand: formData.brand,
        material: formData.material,
        color_name: formData.color_name,
        diameter_mm: formData.diameter_mm,
        barcode: formData.barcode || undefined,
      };

      const { data: product } = await productsApi.create(productData);

      const spoolData = {
        product_id: product.id,
        vendor: formData.vendor || undefined,
        price: formData.price ? parseFloat(formData.price) : undefined,
        storage_location: formData.storage_location || undefined,
        status: 'in_stock' as const,
      };

      await spoolsApi.create(spoolData);
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
    setError(null);
    setUploadProgress(0);
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
      navigate('/inventory');
    } catch (error) {
      console.error('PDF import failed:', error);
      alert('Failed to import PDF invoice. Please try again or check the file format.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto space-y-6 pb-6">
      
      {/* Header Status */}
      <div className="flex items-center justify-between">
         <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${step === 'capture' ? 'bg-primary animate-pulse' : 'bg-muted'}`}></div>
            <div className={`h-[2px] w-8 ${step === 'preview' ? 'bg-primary animate-pulse' : 'bg-surfaceHighlight'}`}></div>
            <div className={`w-2 h-2 rounded-full ${step === 'preview' ? 'bg-primary animate-pulse' : step === 'capture' ? 'bg-muted' : 'bg-primary'}`}></div>
            <div className={`h-[2px] w-8 ${step === 'parsed' ? 'bg-primary animate-pulse' : 'bg-surfaceHighlight'}`}></div>
            <div className={`w-2 h-2 rounded-full ${step === 'parsed' ? 'bg-primary animate-pulse' : 'bg-muted'}`}></div>
         </div>
         <div className="text-xs font-mono text-primary tracking-widest uppercase">
            {step === 'capture' && 'INIT_SEQUENCE'}
            {step === 'preview' && 'IMG_ANALYSIS'}
            {step === 'parsed' && 'DATA_ENTRY'}
         </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-500/10 border border-red-500/50 clip-corner p-4 relative overflow-hidden">
          <div className="absolute inset-0 bg-red-500/5 animate-pulse"></div>
          <div className="flex items-start gap-3 relative z-10">
            <svg className="w-5 h-5 text-red-500 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div className="flex-1">
              <p className="text-sm font-mono text-red-400 uppercase tracking-wide">Error: {error}</p>
            </div>
            <button onClick={() => setError(null)} className="text-red-500 hover:text-red-400">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
      )}

      {/* Capture Step */}
      {step === 'capture' && (
        <div className="space-y-6">
          {/* Scanner UI */}
          <div className="relative group cursor-pointer" onClick={() => fileInputRef.current?.click()}>
             {/* Decorative Borders */}
             <div className="absolute -inset-0.5 bg-gradient-to-r from-primary to-blue-600 opacity-30 group-hover:opacity-70 transition duration-500 blur clip-corner-top-right"></div>
                
             <div className="relative bg-surface border border-white/10 clip-corner-top-right p-1">
                <div className="bg-black/40 aspect-[4/3] flex flex-col items-center justify-center relative overflow-hidden">
                    
                    {/* Grid Background */}
                    <div className="absolute inset-0 bg-grid opacity-[0.1]"></div>

                    {/* Scanner Reticle */}
                    <div className="absolute inset-8 border-2 border-white/20 rounded-lg flex flex-col items-center justify-center transition-all group-hover:border-primary/50 group-hover:inset-6">
                        <div className="absolute top-0 left-0 w-4 h-4 border-t-2 border-l-2 border-primary"></div>
                        <div className="absolute top-0 right-0 w-4 h-4 border-t-2 border-r-2 border-primary"></div>
                        <div className="absolute bottom-0 left-0 w-4 h-4 border-b-2 border-l-2 border-primary"></div>
                        <div className="absolute bottom-0 right-0 w-4 h-4 border-b-2 border-r-2 border-primary"></div>
                        
                        {/* Scanning Line Animation */}
                        <div className="w-full h-[2px] bg-primary/50 shadow-[0_0_10px_#00f0ff] absolute top-1/2 animate-pulse-glow"></div>
                    </div>

                    <div className="z-10 text-center space-y-4 mt-8">
                        <div className="w-12 h-12 mx-auto bg-primary/10 rounded-full flex items-center justify-center border border-primary/30 text-primary">
                           <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
                           </svg>
                        </div>
                        <p className="font-mono text-sm text-primary/80 tracking-widest uppercase">Tap to Capture</p>
                    </div>
                </div>
                
                {/* Tech Decoration */}
                <div className="absolute bottom-2 right-4 text-[10px] font-mono text-white/20 group-hover:text-primary/40 transition-colors">
                    CAM_01 // READY
                </div>
             </div>
             <input
               ref={fileInputRef}
               type="file"
               accept="image/jpeg,image/png,image/webp,image/dng,image/tiff,image/x-mpo"
               onChange={handleCapture}
               className="hidden"
             />
          </div>

          {/* Manual Entry Button */}
          <button
            onClick={() => navigate('/products/new')}
            className="w-full py-3 bg-surface border border-white/10 hover:border-primary/50 text-muted hover:text-white font-mono text-sm uppercase tracking-widest transition-all hover:bg-white/5 clip-corner"
          >
            Manual Override
          </button>

          {/* PDF Upload Section */}
          <div className="pt-6 border-t border-white/5">
            <div className="text-center mb-4">
               <span className="text-[10px] font-mono text-muted uppercase tracking-widest bg-bg px-2 relative z-10">Bulk Import Mode</span>
               <div className="h-px bg-white/10 -mt-2"></div>
            </div>

            <label className="block group cursor-pointer">
              <input
                type="file"
                accept="application/pdf"
                onChange={handlePdfUpload}
                className="hidden"
              />
              <div className="w-full py-3 bg-purple-900/10 hover:bg-purple-900/20 border border-purple-500/30 hover:border-purple-500 text-purple-400 font-mono text-sm uppercase tracking-widest transition-all clip-corner text-center flex items-center justify-center gap-2">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                </svg>
                Upload PDF Invoice
              </div>
            </label>
          </div>
        </div>
      )}

      {/* Preview Step */}
      {step === 'preview' && (
        <div className="space-y-4">
          <div className="relative bg-surface border border-primary/30 p-1 clip-corner-top-right">
            <div className="relative aspect-[4/3] bg-black/40 overflow-hidden">
               <img src={preview} alt="Label preview" className="w-full h-full object-contain relative z-10" />
               {/* Overlay Grid */}
               <div className="absolute inset-0 bg-grid opacity-[0.2] pointer-events-none z-20"></div>
            </div>

            <button
              onClick={handleReset}
              className="absolute top-3 right-3 z-30 p-2 bg-black/50 backdrop-blur border border-white/20 rounded-sm text-white/70 hover:text-white hover:border-white/50 transition-colors"
            >
               <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
               </svg>
            </button>
          </div>

          {/* Upload Progress */}
          {loading && uploadProgress > 0 && (
            <div className="space-y-2">
              <div className="w-full bg-surfaceHighlight h-1 overflow-hidden">
                <div
                  className="bg-primary h-full transition-all duration-300 shadow-[0_0_10px_#00f0ff]"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
              <div className="flex justify-between text-[10px] font-mono text-primary/70 uppercase">
                <span>Processing_Image_Data...</span>
                <span>{uploadProgress}%</span>
              </div>
            </div>
          )}

          <button
            onClick={handleScan}
            disabled={loading}
            className="w-full py-4 bg-primary/10 hover:bg-primary/20 border border-primary text-primary font-mono text-sm font-bold tracking-widest uppercase transition-all shadow-[0_0_15px_rgba(0,240,255,0.1)] hover:shadow-[0_0_25px_rgba(0,240,255,0.3)] disabled:opacity-50 disabled:cursor-not-allowed clip-corner"
          >
            {loading ? 'PROCESSING...' : 'INITIATE SCAN'}
          </button>
          
          {image && (
            <p className="text-[10px] font-mono text-muted text-center uppercase tracking-wide">
              Target: {image.name} ({(image.size / 1024).toFixed(1)} KB)
            </p>
          )}
        </div>
      )}

      {/* Parsed Step */}
      {step === 'parsed' && parsed && (
        <div className="space-y-6">
          {/* Preview Header */}
          <div className="flex gap-4 items-start bg-surface border border-white/10 p-3 clip-corner">
             <div className="w-20 h-20 bg-black relative overflow-hidden border border-white/10 flex-shrink-0">
                <img src={preview} alt="Scanned label" className="w-full h-full object-cover opacity-60" />
             </div>
             <div className="flex-1 min-w-0">
                <h3 className="text-sm font-bold text-primary uppercase tracking-widest mb-1">Scan Complete</h3>
                <p className="text-xs text-muted font-mono truncate">Verify extracted data before committing to database.</p>
             </div>
             <button onClick={handleReset} className="text-muted hover:text-white p-1">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
               </svg>
             </button>
          </div>

          {/* Debug Info */}
          {parsed.raw_text && (
            <details className="group">
               <summary className="text-[10px] font-mono text-muted uppercase tracking-widest cursor-pointer hover:text-white flex items-center gap-2">
                  <span className="border-b border-dashed border-muted group-hover:border-white">Raw_OCR_Data_Log</span>
               </summary>
               <div className="mt-2 p-3 bg-black/50 border border-white/5 text-[10px] font-mono text-muted whitespace-pre-wrap break-words">
                  {parsed.raw_text}
               </div>
            </details>
          )}

          {/* Form Fields */}
          <div className="space-y-6">
             {/* Product Section */}
             <div className="relative pl-4 border-l border-primary/30 space-y-4">
                <div className="absolute -left-[3px] top-0 w-[5px] h-[5px] bg-primary"></div>
                <h4 className="text-xs font-bold text-primary uppercase tracking-widest">Product Specs</h4>
                
                <div className="space-y-3">
                   <div className="space-y-1">
                      <label className="text-[10px] font-mono text-muted uppercase">Brand Identity</label>
                      <input
                        type="text"
                        value={formData.brand}
                        onChange={(e) => setFormData({ ...formData, brand: e.target.value })}
                        className="w-full bg-surfaceHighlight border border-white/10 text-white font-mono text-sm p-2 focus:border-primary focus:outline-none focus:shadow-[0_0_10px_rgba(0,240,255,0.2)] transition-all"
                        placeholder="UNKNOWN_BRAND"
                      />
                   </div>

                   <div className="grid grid-cols-2 gap-3">
                      <div className="space-y-1">
                         <label className="text-[10px] font-mono text-muted uppercase">Material</label>
                         <input
                           type="text"
                           value={formData.material}
                           onChange={(e) => setFormData({ ...formData, material: e.target.value })}
                           className="w-full bg-surfaceHighlight border border-white/10 text-white font-mono text-sm p-2 focus:border-primary focus:outline-none transition-all"
                         />
                      </div>
                      <div className="space-y-1">
                         <label className="text-[10px] font-mono text-muted uppercase">Diameter</label>
                         <select
                           value={formData.diameter_mm}
                           onChange={(e) => setFormData({ ...formData, diameter_mm: parseFloat(e.target.value) })}
                           className="w-full bg-surfaceHighlight border border-white/10 text-white font-mono text-sm p-2 focus:border-primary focus:outline-none transition-all appearance-none"
                         >
                           <option value="1.75">1.75mm</option>
                           <option value="2.85">2.85mm</option>
                           <option value="3.0">3.00mm</option>
                         </select>
                      </div>
                   </div>

                   <div className="space-y-1">
                      <label className="text-[10px] font-mono text-muted uppercase">Color Designation</label>
                      <input
                        type="text"
                        value={formData.color_name}
                        onChange={(e) => setFormData({ ...formData, color_name: e.target.value })}
                        className="w-full bg-surfaceHighlight border border-white/10 text-white font-mono text-sm p-2 focus:border-primary focus:outline-none transition-all"
                      />
                   </div>
                   
                   <div className="space-y-1">
                      <label className="text-[10px] font-mono text-muted uppercase">Barcode / ID</label>
                      <input
                        type="text"
                        value={formData.barcode}
                        onChange={(e) => setFormData({ ...formData, barcode: e.target.value })}
                        className="w-full bg-surfaceHighlight border border-white/10 text-white font-mono text-sm p-2 focus:border-primary focus:outline-none transition-all font-mono tracking-wider"
                        placeholder="NO_DATA"
                      />
                   </div>
                </div>
             </div>

             {/* Spool Section */}
             <div className="relative pl-4 border-l border-secondary/30 space-y-4">
                <div className="absolute -left-[3px] top-0 w-[5px] h-[5px] bg-secondary"></div>
                <h4 className="text-xs font-bold text-secondary uppercase tracking-widest">Inventory Meta</h4>

                <div className="space-y-3">
                   <div className="grid grid-cols-2 gap-3">
                      <div className="space-y-1">
                         <label className="text-[10px] font-mono text-muted uppercase">Vendor</label>
                         <input
                           type="text"
                           value={formData.vendor}
                           onChange={(e) => setFormData({ ...formData, vendor: e.target.value })}
                           className="w-full bg-surfaceHighlight border border-white/10 text-white font-mono text-sm p-2 focus:border-secondary focus:outline-none transition-all"
                         />
                      </div>
                      <div className="space-y-1">
                         <label className="text-[10px] font-mono text-muted uppercase">Unit Price</label>
                         <input
                           type="number"
                           step="0.01"
                           value={formData.price}
                           onChange={(e) => setFormData({ ...formData, price: e.target.value })}
                           className="w-full bg-surfaceHighlight border border-white/10 text-white font-mono text-sm p-2 focus:border-secondary focus:outline-none transition-all"
                         />
                      </div>
                   </div>
                   
                   <div className="space-y-1">
                      <label className="text-[10px] font-mono text-muted uppercase">Storage Node</label>
                      <input
                        type="text"
                        value={formData.storage_location}
                        onChange={(e) => setFormData({ ...formData, storage_location: e.target.value })}
                        className="w-full bg-surfaceHighlight border border-white/10 text-white font-mono text-sm p-2 focus:border-secondary focus:outline-none transition-all"
                        placeholder="UNASSIGNED"
                      />
                   </div>
                </div>
             </div>
          </div>

          {/* Actions */}
          <button
            onClick={handleSave}
            className="w-full py-4 bg-primary/10 hover:bg-primary/20 border border-primary text-primary font-mono text-sm font-bold tracking-widest uppercase transition-all shadow-[0_0_15px_rgba(0,240,255,0.1)] hover:shadow-[0_0_25px_rgba(0,240,255,0.3)] clip-corner"
          >
            Confirm & Commit
          </button>
        </div>
      )}
    </div>
  );
}
