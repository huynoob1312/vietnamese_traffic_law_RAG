import React, { useState, useEffect, useRef } from 'react';
import { adminAPI } from '../../services/api';
import { Upload, Trash2, FileText, RefreshCw, CheckCircle2, AlertCircle, Database, Play } from 'lucide-react';

export default function AdminIngestionTab() {
  const [documents, setDocuments] = useState([]);
  const [loadingDocs, setLoadingDocs] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [ingestStatus, setIngestStatus] = useState({ status: 'idle', message: 'Hệ thống sẵn sàng' });
  const [triggeringIngest, setTriggeringIngest] = useState(false);
  const [toast, setToast] = useState(null);
  const pollTimerRef = useRef(null);
  const fileInputRef = useRef(null);

  const loadDocuments = async () => {
    try {
      const data = await adminAPI.getDocuments();
      setDocuments(data);
    } catch (err) {
      console.error('Lỗi khi tải danh sách tài liệu:', err);
    } finally {
      setLoadingDocs(false);
    }
  };

  const checkIngestStatus = async () => {
    try {
      const statusData = await adminAPI.getIngestStatus();
      setIngestStatus(statusData);
      if (statusData.status === 'running') {
        // Tiếp tục poll sau 2.5 giây nếu đang chạy
        pollTimerRef.current = setTimeout(checkIngestStatus, 2500);
      }
    } catch (err) {
      console.error('Lỗi kiểm tra trạng thái ingestion:', err);
    }
  };

  useEffect(() => {
    loadDocuments();
    checkIngestStatus();
    return () => {
      if (pollTimerRef.current) clearTimeout(pollTimerRef.current);
    };
  }, []);

  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const ext = file.name.split('.').pop().toLowerCase();
    if (!['docx', 'pdf'].includes(ext)) {
      setToast({
        type: 'error',
        message: 'Hệ thống chỉ hỗ trợ định dạng tệp .docx hoặc .pdf',
      });
      return;
    }

    setUploading(true);
    setToast(null);
    try {
      await adminAPI.uploadDocument(file);
      setToast({
        type: 'success',
        message: `Đã tải lên tệp "${file.name}" thành công!`,
      });
      await loadDocuments();
    } catch (err) {
      setToast({
        type: 'error',
        message: err.response?.data?.detail || 'Lỗi khi tải lên tài liệu',
      });
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleDeleteDocument = async (filename) => {
    if (!window.confirm(`Bạn có chắc chắn muốn xóa văn bản "${filename}" khỏi kho dữ liệu?`)) {
      return;
    }

    try {
      await adminAPI.deleteDocument(filename);
      setToast({
        type: 'success',
        message: `Đã xóa văn bản "${filename}"`,
      });
      await loadDocuments();
    } catch (err) {
      setToast({
        type: 'error',
        message: err.response?.data?.detail || 'Không thể xóa tài liệu',
      });
    }
  };

  const handleTriggerIngest = async () => {
    setTriggeringIngest(true);
    setToast(null);
    try {
      const res = await adminAPI.triggerIngest();
      setToast({
        type: 'success',
        message: res.message || 'Đã kích hoạt quy trình Re-index ngầm.',
      });
      checkIngestStatus();
    } catch (err) {
      setToast({
        type: 'error',
        message: err.response?.data?.detail || 'Không thể kích hoạt Ingestion',
      });
    } finally {
      setTriggeringIngest(false);
    }
  };

  const isRunning = ingestStatus.status === 'running';

  return (
    <div className="space-y-6 pb-4">
      {/* Toast Alert */}
      {toast && (
        <div
          className={`p-3 rounded-card text-xs flex items-center justify-between border ${
            toast.type === 'success'
              ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
              : 'bg-red-50 border-red-200 text-red-800'
          }`}
        >
          <div className="flex items-center gap-2">
            {toast.type === 'success' ? <CheckCircle2 size={16} /> : <AlertCircle size={16} />}
            <span>{toast.message}</span>
          </div>
          <button
            type="button"
            onClick={() => setToast(null)}
            className="text-xs underline hover:opacity-75"
          >
            Đóng
          </button>
        </div>
      )}

      {/* Re-index Action Card */}
      <div className="bg-white border border-pebble rounded-card p-4 space-y-3 shadow-subtle">
        <div className="flex items-center justify-between border-b border-pebble pb-2">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-pill bg-deep-teal/10 text-deep-teal flex items-center justify-center">
              <Database size={15} />
            </div>
            <div>
              <h3 className="text-xs font-semibold text-charcoal uppercase tracking-wider">
                Đồng bộ & Re-index Cơ sở Dữ liệu Vector Qdrant
              </h3>
              <p className="text-[11px] text-stone mt-0.5">
                Chạy toàn bộ luồng Ingestion (Load văn bản $\rightarrow$ Chunking theo Điều/Khoản $\rightarrow$ Đẩy Vector vào Qdrant)
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={handleTriggerIngest}
            disabled={isRunning || triggeringIngest}
            className={`px-4 py-2 rounded-pill text-xs font-medium flex items-center gap-1.5 transition-all shadow-subtle ${
              isRunning
                ? 'bg-amber-100 text-amber-800 cursor-not-allowed'
                : 'bg-deep-teal hover:bg-deep-teal/90 text-white active:scale-[0.99]'
            }`}
          >
            {isRunning ? (
              <>
                <RefreshCw size={13} className="animate-spin" />
                <span>Đang xử lý Ingestion...</span>
              </>
            ) : (
              <>
                <Play size={13} />
                <span>Chạy Re-index dữ liệu</span>
              </>
            )}
          </button>
        </div>

        {/* Ingest Status Box */}
        <div
          className={`p-3 rounded-card border text-xs flex flex-col md:flex-row md:items-center justify-between gap-2 ${
            isRunning
              ? 'bg-amber-50/70 border-amber-200 text-amber-900'
              : ingestStatus.status === 'completed'
              ? 'bg-emerald-50/70 border-emerald-200 text-emerald-900'
              : ingestStatus.status === 'failed'
              ? 'bg-red-50/70 border-red-200 text-red-900'
              : 'bg-aged-paper border-pebble text-charcoal'
          }`}
        >
          <div className="flex items-center gap-2">
            <span
              className={`w-2 h-2 rounded-full ${
                isRunning
                  ? 'bg-amber-500 animate-ping'
                  : ingestStatus.status === 'completed'
                  ? 'bg-emerald-500'
                  : ingestStatus.status === 'failed'
                  ? 'bg-red-500'
                  : 'bg-stone'
              }`}
            />
            <span className="font-medium capitalize">
              Trạng thái: {ingestStatus.status === 'idle' ? 'Sẵn sàng' : ingestStatus.status}
            </span>
            <span className="text-stone">|</span>
            <span className="truncate">{ingestStatus.message}</span>
          </div>

          <div className="flex items-center gap-3 text-[11px] text-stone shrink-0">
            {ingestStatus.elapsed_seconds !== null && ingestStatus.elapsed_seconds !== undefined && (
              <span>Thời gian: {ingestStatus.elapsed_seconds}s</span>
            )}
            {ingestStatus.total_chunks && (
              <span className="font-medium text-charcoal">
                Chunks tạo: {ingestStatus.total_chunks}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Upload Zone Card */}
      <div className="bg-white border border-pebble rounded-card p-4 space-y-3 shadow-subtle">
        <div className="flex items-center justify-between border-b border-pebble pb-2">
          <div>
            <h3 className="text-xs font-semibold text-charcoal uppercase tracking-wider">
              Tải lên Văn bản Luật Mới
            </h3>
            <p className="text-[11px] text-stone mt-0.5">
              Hỗ trợ tệp văn bản quy phạm pháp luật định dạng .docx hoặc .pdf (tối đa 25MB)
            </p>
          </div>
        </div>

        <div className="border-2 border-dashed border-pebble hover:border-charcoal rounded-card p-6 flex flex-col items-center justify-center text-center transition-colors bg-aged-paper/40">
          <Upload size={28} className="text-stone mb-2" />
          <p className="text-xs font-medium text-charcoal mb-1">
            Chọn tệp văn bản luật từ máy tính để tải lên
          </p>
          <p className="text-[11px] text-stone mb-3">
            File tải lên sẽ tự động được lưu vào thư mục <code>data/</code> của hệ thống
          </p>

          <input
            type="file"
            ref={fileInputRef}
            accept=".docx,.pdf"
            onChange={handleFileUpload}
            disabled={uploading}
            className="hidden"
            id="admin-doc-upload"
          />

          <label
            htmlFor="admin-doc-upload"
            className={`px-4 py-2 rounded-pill bg-white hover:bg-subtle-fill border border-pebble text-xs font-medium text-charcoal cursor-pointer shadow-subtle transition-all active:scale-[0.99] flex items-center gap-1.5 ${
              uploading ? 'opacity-50 cursor-not-allowed' : ''
            }`}
          >
            {uploading ? (
              <>
                <RefreshCw size={13} className="animate-spin" />
                <span>Đang tải tệp lên...</span>
              </>
            ) : (
              <>
                <Upload size={13} />
                <span>Chọn tệp văn bản (.docx, .pdf)</span>
              </>
            )}
          </label>
        </div>
      </div>

      {/* Documents List Card */}
      <div className="bg-white border border-pebble rounded-card p-4 space-y-3 shadow-subtle">
        <div className="flex items-center justify-between border-b border-pebble pb-2">
          <div>
            <h3 className="text-xs font-semibold text-charcoal uppercase tracking-wider">
              Kho Tài liệu Tri thức Hiện có ({documents.length})
            </h3>
            <p className="text-[11px] text-stone mt-0.5">
              Danh sách các văn bản đang nằm trong thư mục nguồn data/
            </p>
          </div>
          <button
            type="button"
            onClick={loadDocuments}
            className="p-1 text-stone hover:text-charcoal rounded-pill hover:bg-subtle-fill transition-colors"
            title="Làm mới danh sách"
          >
            <RefreshCw size={14} />
          </button>
        </div>

        {loadingDocs ? (
          <div className="py-8 text-center text-xs text-stone">Đang tải danh sách tài liệu...</div>
        ) : documents.length === 0 ? (
          <div className="py-8 text-center text-xs text-stone italic">
            Chưa có tài liệu nào trong thư mục data/
          </div>
        ) : (
          <div className="divide-y divide-pebble/60 max-h-[280px] overflow-y-auto">
            {documents.map((doc) => (
              <div
                key={doc.filename}
                className="py-2.5 px-1 flex items-center justify-between hover:bg-subtle-fill/40 rounded transition-colors"
              >
                <div className="flex items-center gap-2.5 min-w-0 pr-3">
                  <div className="w-7 h-7 rounded bg-aged-paper border border-pebble flex items-center justify-center shrink-0 text-stone">
                    <FileText size={15} />
                  </div>
                  <div className="flex flex-col min-w-0">
                    <span className="text-xs font-medium text-charcoal truncate" title={doc.filename}>
                      {doc.filename}
                    </span>
                    <span className="text-[10px] text-stone">
                      {doc.size_readable} • Cập nhật: {doc.updated_at}
                    </span>
                  </div>
                </div>

                <button
                  type="button"
                  onClick={() => handleDeleteDocument(doc.filename)}
                  className="p-1.5 text-stone hover:text-red-600 rounded-full hover:bg-red-50 transition-colors shrink-0"
                  title="Xóa tài liệu"
                >
                  <Trash2 size={14} />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
