import React, { useState, useEffect } from "react";
import api from "../api";

export default function AdminModelsPage() {
  const [models, setModels] = useState([]);
  const [file, setFile] = useState(null);
  const [loadingUpload, setLoadingUpload] = useState(false);

  const loadModels = async () => {
    const res = await api.get("/risk/models");
    setModels(res.data);
  };

  useEffect(() => {
    loadModels().catch(() => {});
  }, []);

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) return;
    setLoadingUpload(true);

    try {
      const form = new FormData();
      form.append("file", file);

      await api.post("/risk/retrain", form, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      await loadModels();
      alert("Model retrained and set active");
    } catch (err) {
      alert(err?.response?.data?.detail || "Upload failed");
    } finally {
      setLoadingUpload(false);
    }
  };

  return (
    <div className="app-root">
      <div className="app-main">

        <h1>Model Management</h1>
        <p className="page-caption">
          Upload labelled credit card datasets to retrain delinquency models and track versions.
        </p>

        {/* Retrain Section */}
        <div className="card">
          <div className="card-header">Retrain model</div>
          <form onSubmit={handleUpload}>
            <label>
              <span>Training file (CSV/XLSX)</span>
              <input
                type="file"
                accept=".csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/vnd.ms-excel"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
              />
            </label>

            <button type="submit" disabled={loadingUpload}>
              {loadingUpload ? "Uploading..." : "Upload & Retrain"}
            </button>
          </form>
        </div>

        {/* Model Versions Table */}
        <div className="card">
          <div className="card-header">Model versions</div>

          {models.length === 0 ? (
            <p className="muted">No models retrained yet.</p>
          ) : (
            <div className="preview-table">
              <table>
                <thead>
                  <tr>
                    <th>Version</th>
                    <th>LogReg AUC</th>
                    <th>Tree AUC</th>
                    <th>NN AUC</th>
                    <th>Active</th>
                    <th>Created</th>
                  </tr>
                </thead>

                <tbody>
                  {models.map((m) => (
                    <tr key={m._id}>
                      <td>{m.version}</td>
                      <td>{m.logreg_auc.toFixed(3)}</td>
                      <td>{m.tree_auc.toFixed(3)}</td>
                      <td>{m.nn_auc.toFixed(3)}</td>
                      <td>{m.is_active ? "Yes" : "No"}</td>
                      <td>
                        {m.created_at
                          ? new Date(m.created_at).toLocaleString()
                          : "-"}
                      </td>
                    </tr>
                  ))}
                </tbody>

              </table>
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
