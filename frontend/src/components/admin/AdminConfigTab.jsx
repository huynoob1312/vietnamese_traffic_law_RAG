import React, { useState, useEffect } from 'react';
import { adminAPI } from '../../services/api';
import { Save, AlertTriangle, RefreshCw, CheckCircle2, AlertCircle } from 'lucide-react';

export default function AdminConfigTab() {
  const [config, setConfig] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [errors, setErrors] = useState({});
  const [toast, setToast] = useState(null); // { type: 'success' | 'error', message: string }

  const loadConfig = async () => {
    setLoading(true);
    setErrors({});
    try {
      const data = await adminAPI.getConfig();
      setConfig(data);
    } catch (err) {
      setToast({
        type: 'error',
        message: err.response?.data?.detail || 'Không thể tải tệp cấu hình hệ thống',
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadConfig();
  }, []);

  const handleChange = (section, field, value) => {
    setConfig((prev) => ({
      ...prev,
      [section]: {
        ...prev[section],
        [field]: value,
      },
    }));
    // Xóa lỗi của trường này khi người dùng sửa
    if (errors[`${section}.${field}`]) {
      setErrors((prev) => {
        const next = { ...prev };
        delete next[`${section}.${field}`];
        return next;
      });
    }
  };

  const validate = () => {
    const errs = {};

    // 1. Validate Retrieval
    const topK = Number(config.retrieval.top_k);
    if (!Number.isInteger(topK) || topK <= 0) {
      errs['retrieval.top_k'] = 'Top K bắt buộc là số nguyên dương (> 0)';
    }

    const topKRaw = Number(config.retrieval.top_k_raw);
    if (!Number.isInteger(topKRaw) || topKRaw <= 0) {
      errs['retrieval.top_k_raw'] = 'Top K raw bắt buộc là số nguyên dương (> 0)';
    } else if (topKRaw < topK) {
      errs['retrieval.top_k_raw'] = 'Top K raw phải lớn hơn hoặc bằng Top K';
    }

    // 2. Validate Chunking
    const threshDieu = Number(config.chunking.thresh_dieu);
    if (!Number.isInteger(threshDieu) || threshDieu <= 0) {
      errs['chunking.thresh_dieu'] = 'Ngưỡng điều phải là số nguyên dương (> 0)';
    }

    const threshKhoan = Number(config.chunking.thresh_khoan_default);
    if (!Number.isInteger(threshKhoan) || threshKhoan <= 0) {
      errs['chunking.thresh_khoan_default'] = 'Ngưỡng khoản phải là số nguyên dương (> 0)';
    }

    const minChunk = Number(config.chunking.min_chunk);
    if (!Number.isInteger(minChunk) || minChunk <= 0) {
      errs['chunking.min_chunk'] = 'Min chunk phải là số nguyên dương (> 0)';
    }

    const minChunkDiem = Number(config.chunking.min_chunk_diem);
    if (!Number.isInteger(minChunkDiem) || minChunkDiem <= 0) {
      errs['chunking.min_chunk_diem'] = 'Min chunk điểm phải là số nguyên dương (> 0)';
    }

    // 3. Validate LLM
    if (!config.llm_params.model || !config.llm_params.model.trim()) {
      errs['llm_params.model'] = 'Tên mô hình không được để trống';
    }

    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) {
      setToast({
        type: 'error',
        message: 'Dữ liệu không hợp lệ. Vui lòng kiểm tra các ô báo đỏ bên dưới.',
      });
      return;
    }

    setSaving(true);
    setToast(null);

    // Chuẩn hóa kiểu dữ liệu số
    const payload = {
      chunking: {
        thresh_dieu: parseInt(config.chunking.thresh_dieu, 10),
        thresh_khoan_default: parseInt(config.chunking.thresh_khoan_default, 10),
        min_chunk: parseInt(config.chunking.min_chunk, 10),
        min_chunk_diem: parseInt(config.chunking.min_chunk_diem, 10),
      },
      retrieval: {
        search_type: config.retrieval.search_type,
        top_k: parseInt(config.retrieval.top_k, 10),
        use_reranker: Boolean(config.retrieval.use_reranker),
        reranker_model: config.retrieval.reranker_model,
        top_k_raw: parseInt(config.retrieval.top_k_raw, 10),
      },
      llm_params: {
        provider: config.llm_params.provider,
        model: config.llm_params.model.trim(),
        temperature: parseFloat(config.llm_params.temperature || 0.1),
      },
      qdrant: config.qdrant,
      models: config.models,
    };

    try {
      const res = await adminAPI.updateConfig(payload);
      setToast({
        type: 'success',
        message: res.message || 'Cập nhật cấu hình và hot-reload thành công!',
      });
    } catch (err) {
      setToast({
        type: 'error',
        message: err.response?.data?.detail || 'Không thể lưu file cấu hình',
      });
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center p-12 text-stone space-y-3">
        <RefreshCw size={24} className="animate-spin text-charcoal" />
        <span className="text-xs">Đang nạp cấu hình hệ thống config.yaml...</span>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6 pb-4">
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

      {/* Block 1: Retrieval (Thời gian thực) */}
      <div className="bg-white border border-pebble rounded-card p-4 space-y-3 shadow-subtle">
        <div className="flex items-center justify-between border-b border-pebble pb-2">
          <div>
            <h3 className="text-xs font-semibold text-charcoal uppercase tracking-wider">
              1. Cơ chế Truy xuất (Retrieval)
            </h3>
            <p className="text-[11px] text-stone mt-0.5">
              Áp dụng ngay lập tức cho các lượt chat tiếp theo (Hot-reload)
            </p>
          </div>
          <span className="text-[10px] bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded-pill font-medium">
            Hot-Reload
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-1">
          <div>
            <label className="block text-xs font-medium text-charcoal mb-1">
              Phương thức tìm kiếm (search_type)
            </label>
            <select
              value={config.retrieval.search_type}
              onChange={(e) => handleChange('retrieval', 'search_type', e.target.value)}
              className="w-full h-8 px-2.5 bg-white border border-pebble rounded-input text-xs text-charcoal focus:outline-none focus:border-charcoal"
            >
              <option value="hybrid">Tìm kiếm lai Hybrid (BM25 + Dense Vector)</option>
              <option value="bm25">Từ khóa thuần BM25 (Keyword Search)</option>
              <option value="vector">Không gian Vector (Dense Vector Search)</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-charcoal mb-1">
              Số kết quả trích xuất cuối (top_k)
            </label>
            <input
              type="number"
              min="1"
              max="50"
              value={config.retrieval.top_k}
              onChange={(e) => handleChange('retrieval', 'top_k', e.target.value)}
              className={`w-full h-8 px-2.5 bg-white border rounded-input text-xs text-charcoal focus:outline-none ${
                errors['retrieval.top_k']
                  ? 'border-red-500 bg-red-50'
                  : 'border-pebble focus:border-charcoal'
              }`}
            />
            {errors['retrieval.top_k'] && (
              <span className="text-[10px] text-red-600 mt-1 block">
                {errors['retrieval.top_k']}
              </span>
            )}
          </div>

          <div>
            <label className="block text-xs font-medium text-charcoal mb-1">
              Số kết quả thô lấy ban đầu (top_k_raw)
            </label>
            <input
              type="number"
              min="1"
              value={config.retrieval.top_k_raw}
              onChange={(e) => handleChange('retrieval', 'top_k_raw', e.target.value)}
              className={`w-full h-8 px-2.5 bg-white border rounded-input text-xs text-charcoal focus:outline-none ${
                errors['retrieval.top_k_raw']
                  ? 'border-red-500 bg-red-50'
                  : 'border-pebble focus:border-charcoal'
              }`}
            />
            {errors['retrieval.top_k_raw'] && (
              <span className="text-[10px] text-red-600 mt-1 block">
                {errors['retrieval.top_k_raw']}
              </span>
            )}
          </div>

          <div className="flex items-center gap-3 pt-4">
            <label className="flex items-center gap-2 cursor-pointer select-none">
              <input
                type="checkbox"
                checked={config.retrieval.use_reranker}
                onChange={(e) => handleChange('retrieval', 'use_reranker', e.target.checked)}
                className="w-4 h-4 text-deep-teal rounded border-pebble focus:ring-deep-teal"
              />
              <span className="text-xs font-medium text-charcoal">
                Kích hoạt BAAI Reranker (use_reranker)
              </span>
            </label>
          </div>

          {config.retrieval.use_reranker && (
            <div className="md:col-span-2">
              <label className="block text-xs font-medium text-charcoal mb-1">
                Tên mô hình Reranker (reranker_model)
              </label>
              <input
                type="text"
                value={config.retrieval.reranker_model}
                onChange={(e) => handleChange('retrieval', 'reranker_model', e.target.value)}
                className="w-full h-8 px-2.5 bg-white border border-pebble rounded-input text-xs text-charcoal focus:outline-none focus:border-charcoal font-mono"
              />
            </div>
          )}
        </div>
      </div>

      {/* Block 2: LLM Configuration (Thời gian thực) */}
      <div className="bg-white border border-pebble rounded-card p-4 space-y-3 shadow-subtle">
        <div className="flex items-center justify-between border-b border-pebble pb-2">
          <div>
            <h3 className="text-xs font-semibold text-charcoal uppercase tracking-wider">
              2. Mô hình Ngôn ngữ Sinh câu trả lời (LLM)
            </h3>
            <p className="text-[11px] text-stone mt-0.5">
              Cấu hình nhà cung cấp và model sinh câu trả lời tự động
            </p>
          </div>
          <span className="text-[10px] bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded-pill font-medium">
            Hot-Reload
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-1">
          <div>
            <label className="block text-xs font-medium text-charcoal mb-1">
              Nhà cung cấp (provider)
            </label>
            <select
              value={config.llm_params.provider}
              onChange={(e) => handleChange('llm_params', 'provider', e.target.value)}
              className="w-full h-8 px-2.5 bg-white border border-pebble rounded-input text-xs text-charcoal focus:outline-none focus:border-charcoal"
            >
              <option value="gemini">Google Gemini (Cloud API)</option>
              <option value="ollama">Ollama (Mô hình Local On-Premise)</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-charcoal mb-1">
              Tên mô hình (model)
            </label>
            <input
              type="text"
              value={config.llm_params.model}
              onChange={(e) => handleChange('llm_params', 'model', e.target.value)}
              placeholder="VD: gemini-3.6-flash hoặc qwen2.5:3b"
              className={`w-full h-8 px-2.5 bg-white border rounded-input text-xs text-charcoal focus:outline-none font-mono ${
                errors['llm_params.model']
                  ? 'border-red-500 bg-red-50'
                  : 'border-pebble focus:border-charcoal'
              }`}
            />
            {errors['llm_params.model'] && (
              <span className="text-[10px] text-red-600 mt-1 block">
                {errors['llm_params.model']}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Block 3: Chunking & Storage (Yêu cầu Re-index) */}
      <div className="bg-white border border-pebble rounded-card p-4 space-y-3 shadow-subtle">
        <div className="flex items-center justify-between border-b border-pebble pb-2">
          <div>
            <h3 className="text-xs font-semibold text-charcoal uppercase tracking-wider">
              3. Phân mảnh (Chunking) & Cơ sở Dữ liệu Vector
            </h3>
            <p className="text-[11px] text-stone mt-0.5">
              Các thông số cấu trúc hóa văn bản quy phạm pháp luật
            </p>
          </div>
          <span className="text-[10px] bg-amber-100 text-amber-800 px-2 py-0.5 rounded-pill font-medium flex items-center gap-1">
            <AlertTriangle size={11} /> Cần Re-index
          </span>
        </div>

        <div className="p-2.5 bg-amber-50/70 border border-amber-200/80 rounded-input text-[11px] text-amber-900 flex items-start gap-2">
          <AlertTriangle size={15} className="text-amber-600 shrink-0 mt-0.5" />
          <p className="leading-relaxed">
            <strong>Lưu ý:</strong> Khi thay đổi các tham số phân đoạn (thresh_dieu, thresh_khoan) hoặc
            model embedding, bạn cần sang <strong>Tab 2 (Tri thức & Re-index)</strong> và bấm nút{' '}
            <strong>"Chạy Re-index dữ liệu"</strong> để nạp lại vector vào Qdrant.
          </p>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 pt-1">
          <div>
            <label className="block text-xs font-medium text-charcoal mb-1">
              Ngưỡng Điều (thresh_dieu)
            </label>
            <input
              type="number"
              min="1"
              value={config.chunking.thresh_dieu}
              onChange={(e) => handleChange('chunking', 'thresh_dieu', e.target.value)}
              className="w-full h-8 px-2.5 bg-white border border-pebble rounded-input text-xs text-charcoal focus:outline-none focus:border-charcoal"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-charcoal mb-1">
              Ngưỡng Khoản (thresh_khoan)
            </label>
            <input
              type="number"
              min="1"
              value={config.chunking.thresh_khoan_default}
              onChange={(e) => handleChange('chunking', 'thresh_khoan_default', e.target.value)}
              className="w-full h-8 px-2.5 bg-white border border-pebble rounded-input text-xs text-charcoal focus:outline-none focus:border-charcoal"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-charcoal mb-1">
              Min chunk (từ)
            </label>
            <input
              type="number"
              min="1"
              value={config.chunking.min_chunk}
              onChange={(e) => handleChange('chunking', 'min_chunk', e.target.value)}
              className="w-full h-8 px-2.5 bg-white border border-pebble rounded-input text-xs text-charcoal focus:outline-none focus:border-charcoal"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-charcoal mb-1">
              Min điểm (từ)
            </label>
            <input
              type="number"
              min="1"
              value={config.chunking.min_chunk_diem}
              onChange={(e) => handleChange('chunking', 'min_chunk_diem', e.target.value)}
              className="w-full h-8 px-2.5 bg-white border border-pebble rounded-input text-xs text-charcoal focus:outline-none focus:border-charcoal"
            />
          </div>

          <div className="col-span-2">
            <label className="block text-xs font-medium text-charcoal mb-1">
              Mô hình Embedding (embedding_model)
            </label>
            <input
              type="text"
              value={config.models?.embedding || ''}
              onChange={(e) => handleChange('models', 'embedding', e.target.value)}
              className="w-full h-8 px-2.5 bg-white border border-pebble rounded-input text-xs text-charcoal focus:outline-none focus:border-charcoal font-mono"
            />
          </div>

          <div className="col-span-2">
            <label className="block text-xs font-medium text-charcoal mb-1">
              Tên Collection Qdrant (collection_name)
            </label>
            <input
              type="text"
              value={config.qdrant?.collection_name || ''}
              onChange={(e) => handleChange('qdrant', 'collection_name', e.target.value)}
              className="w-full h-8 px-2.5 bg-white border border-pebble rounded-input text-xs text-charcoal focus:outline-none focus:border-charcoal font-mono"
            />
          </div>
        </div>
      </div>

      {/* Action Footer */}
      <div className="flex items-center justify-between pt-2">
        <button
          type="button"
          onClick={loadConfig}
          disabled={saving}
          className="px-4 py-2 rounded-pill border border-pebble text-xs text-stone hover:text-charcoal hover:bg-subtle-fill transition-colors"
        >
          Khôi phục giá trị cũ
        </button>

        <button
          type="submit"
          disabled={saving}
          className="px-5 py-2 rounded-pill bg-charcoal hover:bg-black text-white text-xs font-medium shadow-subtle flex items-center gap-1.5 transition-all active:scale-[0.99] disabled:opacity-50"
        >
          {saving ? (
            <>
              <RefreshCw size={14} className="animate-spin" />
              <span>Đang lưu và hot-reload...</span>
            </>
          ) : (
            <>
              <Save size={14} />
              <span>Lưu cấu hình hệ thống</span>
            </>
          )}
        </button>
      </div>
    </form>
  );
}
