# Reliability Plan: OCR & PDF Uploads

## Goal
Ensure label photos, PDF invoices, and screenshots work reliably **before** migration. No debugging after deployment.

---

## Current Issues to Address

### 1. **File Upload Validation**
- ✅ Basic content-type checking exists
- ❌ No file size limits
- ❌ No format validation (file extensions vs content)
- ❌ No image dimension checks
- ❌ No PDF page count limits

### 2. **Error Handling**
- ✅ Basic error handling exists
- ❌ No retry mechanisms
- ❌ No detailed error logging
- ❌ No user-friendly error messages

### 3. **Testing**
- ❌ No automated tests for OCR
- ❌ No test images included
- ❌ No validation scripts

### 4. **Monitoring**
- ❌ No health checks for OCR service
- ❌ No performance metrics
- ❌ No failure tracking

---

## Reliability Improvements Plan

### Phase 1: Enhanced Validation (30 min)

#### 1.1 File Size Limits
```python
# Add to backend/main.py
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_PDF_SIZE = 20 * 1024 * 1024     # 20 MB
```

#### 1.2 Format Validation
- Check file extension matches content-type
- Validate image formats (JPEG, PNG, WebP)
- Validate PDF structure (not just MIME type)
- Check image dimensions (min/max)

#### 1.3 Content Validation
- Verify image is actually readable (not corrupted)
- Verify PDF has extractable text
- Check PDF page count (prevent huge files)

### Phase 2: Better Error Handling (20 min)

#### 2.1 Detailed Error Messages
```python
{
  "error": "Image too large",
  "details": "File size: 15MB, Maximum: 10MB",
  "suggestion": "Please compress image or use smaller file"
}
```

#### 2.2 Retry Logic
- Automatic retry for transient OCR failures
- Exponential backoff
- Max 3 retries

#### 2.3 Error Logging
- Log all failures with context
- Include file metadata (size, type, dimensions)
- Track success/failure rates

### Phase 3: Health Checks & Monitoring (20 min)

#### 3.1 OCR Health Endpoint
```python
GET /api/v1/health/ocr
# Returns: Tesseract version, available, test result
```

#### 3.2 Performance Metrics
- Track OCR processing time
- Track success rates
- Track confidence scores

### Phase 4: Test Utilities (30 min)

#### 4.1 Test Script
```bash
python scripts/test_ocr.py <image_path>
# Tests OCR with sample images
# Reports success/failure
```

#### 4.2 Sample Test Images
- Include sample label images (Sunlu, eSUN, Bambu)
- Include sample PDF invoices
- Include edge cases (blurry, low contrast, etc.)

#### 4.3 Validation Script
```bash
python scripts/validate_deployment.py
# Checks:
# - Tesseract installed
# - Dependencies available
# - Can process test images
# - Can parse test PDFs
```

### Phase 5: Frontend Improvements (20 min)

#### 5.1 File Size Warnings
- Show file size before upload
- Warn if file is too large
- Suggest compression

#### 5.2 Upload Progress
- Show upload progress bar
- Show processing status
- Display OCR confidence score

#### 5.3 Error Display
- Show detailed error messages
- Suggest solutions
- Allow retry without re-upload

---

## Implementation Checklist

### Backend Changes
- [ ] Add file size validation
- [ ] Add format validation (extension + content)
- [ ] Add image dimension checks
- [ ] Add PDF structure validation
- [ ] Improve error messages with details
- [ ] Add retry logic for OCR
- [ ] Add health check endpoint
- [ ] Add performance logging
- [ ] Create test utilities
- [ ] Add sample test files

### Frontend Changes
- [ ] Add file size display
- [ ] Add upload progress indicator
- [ ] Improve error display
- [ ] Add retry button
- [ ] Show OCR confidence score

### Testing
- [ ] Create test script for OCR
- [ ] Create test script for PDF parsing
- [ ] Add sample test images
- [ ] Add sample test PDFs
- [ ] Create validation script
- [ ] Test with real labels
- [ ] Test with real invoices

### Documentation
- [ ] Document file size limits
- [ ] Document supported formats
- [ ] Document error codes
- [ ] Create troubleshooting guide

---

## Test Scenarios

### Label Photo Tests
1. ✅ Clear, well-lit label (Sunlu)
2. ✅ Clear, well-lit label (eSUN)
3. ✅ Clear, well-lit label (Bambu)
4. ⚠️ Blurry image
5. ⚠️ Low contrast image
6. ⚠️ Angled photo
7. ⚠️ Glare/reflection
8. ❌ Corrupted image
9. ❌ Wrong format (GIF, BMP)
10. ❌ File too large (>10MB)

### PDF Invoice Tests
1. ✅ Bambu Lab invoice (PDF)
2. ✅ Amazon invoice (PDF) - when implemented
3. ⚠️ Scanned PDF (image-based)
4. ⚠️ Multi-page PDF
5. ❌ Corrupted PDF
6. ❌ Non-PDF file (renamed image)
7. ❌ File too large (>20MB)
8. ❌ Password-protected PDF

### Screenshot Tests
1. ✅ Screenshot of order confirmation
2. ✅ Screenshot of invoice
3. ⚠️ Low resolution screenshot
4. ⚠️ Compressed screenshot

---

## Success Criteria

### OCR Reliability
- ✅ 90%+ success rate on clear labels
- ✅ 70%+ success rate on poor quality images
- ✅ Clear error messages for failures
- ✅ Confidence scores > 50% for successful scans

### PDF Parsing Reliability
- ✅ 95%+ success rate on Bambu invoices
- ✅ Clear error messages for unsupported formats
- ✅ Handles multi-page invoices

### User Experience
- ✅ File size warnings before upload
- ✅ Progress indicators during processing
- ✅ Clear error messages with suggestions
- ✅ Easy retry without re-upload

---

## Deployment Validation

Before going live, run:
```bash
# 1. Validate deployment
python scripts/validate_deployment.py

# 2. Test OCR with samples
python scripts/test_ocr.py tests/samples/label_sunlu.jpg
python scripts/test_ocr.py tests/samples/label_esun.jpg
python scripts/test_ocr.py tests/samples/label_bambu.jpg

# 3. Test PDF parsing
python scripts/test_pdf.py tests/samples/invoice_bambu.pdf

# 4. Health check
curl https://your-backend.render.com/api/v1/health/ocr
```

All tests must pass before deployment!

---

## Timeline

- **Phase 1-2:** 50 minutes (validation + error handling)
- **Phase 3:** 20 minutes (health checks)
- **Phase 4:** 30 minutes (test utilities)
- **Phase 5:** 20 minutes (frontend)
- **Testing:** 30 minutes (manual testing)
- **Total:** ~2.5 hours

---

## Next Steps

1. Implement all validation improvements
2. Create test utilities and sample files
3. Test thoroughly with real examples
4. Deploy to staging/test environment
5. Validate everything works
6. Then migrate to Split Architecture

This ensures reliability **before** migration, not after!

