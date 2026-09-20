import React, { useState, useRef } from 'react';
import { UploadCloud, CheckCircle2, AlertCircle, Loader2, X } from 'lucide-react';
import { API_BASE } from '../../config/api';

export default function ContractUploadZone({ onUploadSuccess }) {
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState(null); // { type: 'success'|'error', message: string, data?: any }
  const fileInputRef = useRef(null);

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      processFiles(Array.from(e.dataTransfer.files));
    }
  };

  const handleFileSelect = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      processFiles(Array.from(e.target.files));
    }
  };

  const processFiles = async (filesList) => {
    const pdfFiles = filesList.filter(f => f.name.toLowerCase().endsWith('.pdf'));
    if (pdfFiles.length === 0) {
      setUploadStatus({
        type: 'error',
        message: 'Only PDF contract documents (.pdf) are supported.'
      });
      return;
    }

    setUploading(true);
    setUploadStatus(null);

    const formData = new FormData();
    if (pdfFiles.length === 1) {
      formData.append('file', pdfFiles[0]);
    } else {
      pdfFiles.forEach(f => formData.append('files', f));
    }

    try {
      const response = await fetch(`${API_BASE}/api/contracts/upload`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Upload failed with HTTP ${response.status}`);
      }

      const result = await response.json();
      if (result.documents) {
        setUploadStatus({
          type: 'success',
          message: `Successfully ingested ${result.total_ingested} contracts into the corpus. Live indices updated.`,
          data: result
        });
      } else {
        setUploadStatus({
          type: 'success',
          message: `Successfully ingested "${result.filename}" (${result.page_count} pages, ${result.obligations_extracted} obligations).`,
          data: result
        });
      }

      if (onUploadSuccess) {
        onUploadSuccess(result);
      }
    } catch (err) {
      setUploadStatus({
        type: 'error',
        message: err.message || 'Failed to upload and ingest contracts.'
      });
    } finally {
      setUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  return (
    <div style={{ width: '100%', maxWidth: '640px', margin: '0 auto 20px' }}>
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => !uploading && fileInputRef.current?.click()}
        style={{
          border: `1.5px dashed ${isDragging ? 'var(--accent-terracotta)' : 'var(--border-medium)'}`,
          borderRadius: '12px',
          padding: '16px 20px',
          background: isDragging ? 'var(--accent-terracotta-dim)' : 'var(--bg-surface)',
          cursor: uploading ? 'wait' : 'pointer',
          transition: 'all var(--transition-fast)',
          display: 'flex',
          alignItems: 'center',
          gap: '14px',
          boxShadow: 'var(--shadow-ambient)'
        }}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf"
          multiple
          style={{ display: 'none' }}
          onChange={handleFileSelect}
          disabled={uploading}
        />

        <div style={{
          width: '36px',
          height: '36px',
          borderRadius: '8px',
          background: 'var(--bg-surface-elevated)',
          border: '1px solid var(--border-medium)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0
        }}>
          {uploading ? (
            <Loader2
              size={18}
              color="var(--accent-terracotta)"
              className="animate-spin"
              style={{
                animation: 'spin 0.85s linear infinite',
                transformOrigin: 'center center',
                willChange: 'transform'
              }}
            />
          ) : (
            <UploadCloud size={18} color="var(--text-secondary)" />
          )}
        </div>

        <div style={{ flex: 1, textAlign: 'left' }}>
          <div style={{ fontSize: '0.84rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '2px' }}>
            {uploading ? 'Ingesting & Indexing PDF(s)...' : 'Drop contract PDF(s) to dynamically ingest'}
          </div>
          <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
            {uploading
              ? 'Extracting structural blocks, intelligence metadata & updating cross-contract graph...'
              : 'Click to select or drop single or multiple contract PDFs. Instantly queryable across the portfolio.'}
          </div>
        </div>

        <div style={{
          fontSize: '0.72rem',
          fontFamily: 'var(--font-mono)',
          padding: '3px 8px',
          borderRadius: '4px',
          background: 'var(--bg-surface-elevated)',
          border: '1px solid var(--border-medium)',
          color: 'var(--text-secondary)',
          flexShrink: 0
        }}>
          PDF · MULTI
        </div>
      </div>

      {uploadStatus && (
        <div style={{
          marginTop: '10px',
          padding: '8px 12px',
          borderRadius: '8px',
          background: uploadStatus.type === 'success' ? 'var(--signal-success-dim)' : 'rgba(239, 68, 68, 0.1)',
          border: `1px solid ${uploadStatus.type === 'success' ? 'var(--signal-success-border)' : 'rgba(239, 68, 68, 0.3)'}`,
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          fontSize: '0.78rem',
          color: uploadStatus.type === 'success' ? 'var(--signal-success)' : '#ef4444',
          animation: 'fadeIn 0.3s ease-out'
        }}>
          {uploadStatus.type === 'success' ? (
            <CheckCircle2 size={14} style={{ flexShrink: 0 }} />
          ) : (
            <AlertCircle size={14} style={{ flexShrink: 0 }} />
          )}
          <span style={{ flex: 1 }}>{uploadStatus.message}</span>
          <button
            onClick={(e) => {
              e.stopPropagation();
              setUploadStatus(null);
            }}
            style={{
              background: 'transparent',
              border: 'none',
              cursor: 'pointer',
              color: 'currentColor',
              padding: 0,
              display: 'flex',
              alignItems: 'center'
            }}
          >
            <X size={12} />
          </button>
        </div>
      )}
    </div>
  );
}
