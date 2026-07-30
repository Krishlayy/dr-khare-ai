import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import {
  CheckCircle2,
  FileUp,
  History,
  Loader2,
  Upload,
  XCircle,
} from "lucide-react";
import "./Admin.css";

const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";

const PIPELINE_STAGES = [
  { key: "uploading", label: "Uploading..." },
  { key: "extracting_text", label: "Extracting text..." },
  { key: "creating_chunks", label: "Creating chunks..." },
  { key: "generating_embeddings", label: "Generating embeddings..." },
  { key: "indexing_knowledge", label: "Indexing knowledge..." },
  { key: "completed", label: "Completed" },
];

function Toast({ toast, onDismiss }) {
  useEffect(() => {
    const timer = setTimeout(() => onDismiss(toast.id), 4000);
    return () => clearTimeout(timer);
  }, [toast.id, onDismiss]);

  return (
    <div className={`toast toast-${toast.type}`}>
      {toast.type === "success" ? (
        <CheckCircle2 size={20} />
      ) : (
        <XCircle size={20} />
      )}
      <span>{toast.message}</span>
    </div>
  );
}

function Admin() {
  const navigate = useNavigate();
  const fileInputRef = useRef(null);

  const [history, setHistory] = useState([]);
  const [dashboard, setDashboard] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [currentStage, setCurrentStage] = useState("");
  const [toasts, setToasts] = useState([]);

  const getAuthHeaders = () => {
    const token = localStorage.getItem("admin_token");
    return { Authorization: `Bearer ${token}` };
  };

  const showToast = useCallback((type, message) => {
    setToasts((prev) => [
      ...prev,
      { id: Date.now() + Math.random(), type, message },
    ]);
  }, []);

  const dismissToast = useCallback((id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const fetchHistory = useCallback(async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/upload/history`, {
        headers: getAuthHeaders(),
      });
      setHistory(response.data);
    } catch {
      /* history load failed silently */
    }
  }, []);

  const fetchDashboard = useCallback(async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/admin/dashboard`, {
        headers: getAuthHeaders(),
      });
      setDashboard(response.data);
    } catch {
      /* dashboard load failed silently */
    }
  }, []);

  const deleteDocument = useCallback(async (docId, filename) => {
    if (!window.confirm(`Delete "${filename}" from the knowledge base?`)) return;
    try {
      await axios.delete(`${API_BASE}/api/docs/${docId}`, {
        headers: getAuthHeaders(),
      });
      showToast("success", `Deleted "${filename}"`);
      await fetchHistory();
      await fetchDashboard();
    } catch {
      showToast("error", `Failed to delete "${filename}"`);
    }
  }, [fetchHistory, fetchDashboard, showToast]);

  useEffect(() => {
    const token = localStorage.getItem("admin_token");
    if (!token) {
      navigate("/login");
      return;
    }
    
    const interceptor = axios.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          localStorage.removeItem("admin_token");
          navigate("/login");
        }
        return Promise.reject(error);
      }
    );

    (async () => {
      await fetchHistory();
      await fetchDashboard();
    })();
    
    return () => axios.interceptors.response.eject(interceptor);
  }, [navigate, fetchHistory, fetchDashboard]);

  const pollProcessingStatus = async (documentId) => {
    const maxAttempts = 120;
    for (let attempt = 0; attempt < maxAttempts; attempt += 1) {
      const response = await axios.get(
        `${API_BASE}/api/upload/status/${documentId}`,
        { headers: getAuthHeaders() }
      );

      const { status, stage_label, progress } = response.data;
      setCurrentStage(stage_label);
      setUploadProgress(Math.max(35, progress));

      if (status === "completed") {
        setUploadProgress(100);
        setCurrentStage("Completed");
        return true;
      }

      if (status === "failed") {
        throw new Error(response.data.error_message || "Processing failed");
      }

      await new Promise((resolve) => setTimeout(resolve, 800));
    }

    throw new Error("Processing timed out");
  };

  const handleFileChange = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    setIsUploading(true);
    setUploadProgress(0);
    setCurrentStage("Uploading...");

    try {
      const uploadResponse = await axios.post(
        `${API_BASE}/api/upload`,
        formData,
        {
          headers: {
            ...getAuthHeaders(),
            "Content-Type": "multipart/form-data",
          },
          onUploadProgress: (event) => {
            if (!event.total) return;
            const percent = Math.round((event.loaded / event.total) * 35);
            setUploadProgress(percent);
          },
        }
      );

      const { document_id } = uploadResponse.data;
      await pollProcessingStatus(document_id);

      showToast("success", "Document indexed successfully");
      await fetchHistory();
      await fetchDashboard();
    } catch {
      showToast("error", "Failed to process document");
    } finally {
      setIsUploading(false);
      setUploadProgress(0);
      setCurrentStage("");
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  };

  const formatDate = (value) => {
    if (!value) return "—";
    return new Date(value).toLocaleString();
  };

  const getStageIndex = (currentStageLabel) => {
    // currentStageLabel may be a label string (from poll) or a key (during upload init)
    // Try matching by label first, then by key
    const byLabel = PIPELINE_STAGES.findIndex((s) => s.label === currentStageLabel);
    if (byLabel !== -1) return byLabel;
    const byKey = PIPELINE_STAGES.findIndex((s) => s.key === currentStageLabel);
    return byKey;
  };

  const activeStageIndex = getStageIndex(currentStage);

  const statusClass = (status) => {
    if (status === "completed") return "status-completed";
    if (status === "failed") return "status-failed";
    if (status === "processing") return "status-processing";
    return "status-pending";
  };

  return (
    <div className="admin-page">
      <div className="toast-container">
        {toasts.map((toast) => (
          <Toast key={toast.id} toast={toast} onDismiss={dismissToast} />
        ))}
      </div>

      <div className="admin-shell">
        <header className="admin-header">
          <div>
            <h1>Unified Control Panel</h1>
            <p>Dr. Khare Systems Management — Document Ingestion</p>
          </div>
          <button
            type="button"
            className="admin-logout"
            onClick={() => {
              localStorage.removeItem("admin_token");
              navigate("/login");
            }}
          >
            Secure Logout
          </button>
        </header>

        {dashboard && (
          <div className="stats-grid">
            {[
              { label: "Documents Indexed", value: dashboard.documents_indexed },
              { label: "Chunks Indexed", value: dashboard.chunks_indexed },
              { label: "Storage Used", value: `${dashboard.storage_used_mb} MB` },
              { label: "Queries Today", value: dashboard.queries_today },
              { label: "Avg Response", value: `${dashboard.average_response_time_ms}ms` },
              { label: "KB Health", value: dashboard.knowledge_base_health },
            ].map((stat) => (
              <div key={stat.label} className="stat-card">
                <span className="stat-value">{stat.value}</span>
                <span className="stat-label">{stat.label}</span>
              </div>
            ))}
          </div>
        )}

        <div className="admin-grid">
          <section className="admin-card">
            <h2>Knowledge Base Upload</h2>
            <p className="admin-card-desc">
              Upload PDF, DOCX, or TXT files. Documents are extracted, chunked,
              embedded, and indexed into ChromaDB automatically.
            </p>

            <div
              className={`upload-zone ${isUploading ? "active disabled" : ""}`}
            >
              <div className="upload-icon-wrap">
                {isUploading ? (
                  <Loader2 size={28} className="spin-icon" />
                ) : (
                  <FileUp size={28} />
                )}
              </div>
              <p className="upload-title">PDF / DOCX / TXT Upload</p>
              <p className="upload-subtitle">
                Files stored in storage/uploads/
              </p>

              <input
                type="file"
                ref={fileInputRef}
                accept=".pdf,.docx,.txt"
                onChange={handleFileChange}
                style={{ display: "none" }}
                disabled={isUploading}
              />

              <button
                type="button"
                className="upload-btn"
                disabled={isUploading}
                onClick={() => fileInputRef.current?.click()}
              >
                {isUploading ? (
                  <>
                    <Loader2 size={18} className="spin-icon" />
                    Processing...
                  </>
                ) : (
                  <>
                    <Upload size={18} />
                    Browse Files
                  </>
                )}
              </button>
            </div>

            {isUploading && (
              <div className="progress-panel">
                <div className="progress-label-row">
                  <span className="progress-stage">
                    <span className="spinner" />
                    {currentStage || "Uploading..."}
                  </span>
                  <span className="progress-percent">{uploadProgress}%</span>
                </div>
                <div className="progress-track">
                  <div
                    className="progress-fill"
                    style={{ width: `${uploadProgress}%` }}
                  />
                </div>
                <div className="stage-steps">
                  {PIPELINE_STAGES.map((stage, index) => {
                    let pillClass = "stage-pill";
                    if (index < activeStageIndex) pillClass += " done";
                    if (index === activeStageIndex) pillClass += " active";
                    return (
                      <span key={stage.key} className={pillClass}>
                        {stage.label}
                      </span>
                    );
                  })}
                </div>
              </div>
            )}
          </section>

          <section className="admin-card">
            <h2>Pipeline Overview</h2>
            <p className="admin-card-desc">
              Production ingestion flow for Dr. Khare&apos;s knowledge base.
            </p>
            <div className="stage-steps" style={{ marginTop: 0 }}>
              {[
                "Upload",
                "Extract Text",
                "Clean Text",
                "Chunk Text",
                "Generate Embeddings",
                "Store in ChromaDB",
                "Save Metadata",
              ].map((step, i) => (
                <span key={step} className="stage-pill done">
                  {i + 1}. {step}
                </span>
              ))}
            </div>
          </section>

          <section className="admin-card history-card">
            <h2>
              <History
                size={20}
                style={{ display: "inline", verticalAlign: "middle", marginRight: 8 }}
              />
              Upload History
            </h2>
            <p className="admin-card-desc">
              Track filename, upload date, processing status, and chunk count.
            </p>

            {history.length === 0 ? (
              <div className="empty-history">No documents uploaded yet.</div>
            ) : (
              <div className="history-table-wrap">
                <table className="history-table">
                  <thead>
                    <tr>
                      <th>Filename</th>
                      <th>Upload Date</th>
                      <th>Status</th>
                      <th>Chunks</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {history.map((doc) => (
                      <tr key={doc.id}>
                        <td>{doc.filename}</td>
                        <td>{formatDate(doc.upload_date)}</td>
                        <td>
                          <span className={`status-badge ${statusClass(doc.status)}`}>
                            {doc.status}
                          </span>
                        </td>
                        <td>{doc.chunks_count}</td>
                        <td>
                          <button
                            type="button"
                            className="delete-btn"
                            onClick={() => deleteDocument(doc.id, doc.filename)}
                            title={`Delete ${doc.filename}`}
                          >
                            ✕
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        </div>
      </div>
    </div>
  );
}

export default Admin;
