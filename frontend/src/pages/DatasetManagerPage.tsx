import React, { useState, useEffect } from 'react';
import {
  Database,
  Upload,
  FileText,
  CheckCircle2,
  AlertTriangle,
  Trash2,
  Download,
  Filter,
  Eye,
  RefreshCw,
  Info,
  ShieldCheck,
  Check
} from 'lucide-react';
import { api, Dataset, DatasetPreview } from '../api/client';
import { useAuth } from '../context/AuthContext';

export const DatasetManagerPage: React.FC = () => {
  const { application } = useAuth();
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [cleaning, setCleaning] = useState(false);
  const [selectedPreview, setSelectedPreview] = useState<DatasetPreview | null>(null);
  const [cleaningDatasetId, setCleaningDatasetId] = useState<number | null>(null);

  // Cleaning options
  const [dropDuplicates, setDropDuplicates] = useState(true);
  const [fillNumeric, setFillNumeric] = useState('median');
  const [fillCategorical, setFillCategorical] = useState('mode');

  useEffect(() => {
    loadDatasets();
  }, [application?.id]);

  const loadDatasets = async () => {
    try {
      setLoading(true);
      const data = await api.getDatasets(application?.id);
      setDatasets(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    try {
      setUploading(true);
      await api.uploadDataset(file, application?.id);
      await loadDatasets();
    } catch (err: any) {
      alert("Failed to upload dataset: " + (err.message || "Failed"));
    } finally {
      setUploading(false);
    }
  };

  const handlePreview = async (id: number) => {
    try {
      const prev = await api.getDatasetPreview(id);
      setSelectedPreview(prev);
    } catch (err) {
      alert("Failed to load preview");
    }
  };

  const handleClean = async () => {
    if (!cleaningDatasetId) return;
    try {
      setCleaning(true);
      await api.cleanDataset(cleaningDatasetId, {
        drop_duplicates: dropDuplicates,
        fill_missing_numeric: fillNumeric,
        fill_missing_categorical: fillCategorical
      });
      setCleaningDatasetId(null);
      await loadDatasets();
      alert("Dataset successfully cleaned and sanitized! Rejected records archived.");
    } catch (err: any) {
      alert("Cleaning failed: " + (err.message || "Failed"));
    } finally {
      setCleaning(false);
    }
  };

  const handleExportRejected = async (id: number) => {
    try {
      const res = await api.exportRejectedRecords(id);
      const blob = new Blob([JSON.stringify(res.records, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `rejected_records_dataset_${id}.json`;
      a.click();
    } catch (err) {
      alert("Failed to export rejected records");
    }
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Header & File Upload Dropzone */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2 mb-1">
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-50 text-indigo-700 border border-indigo-200">
                MODULE 6
              </span>
              <span className="text-xs text-slate-400 font-medium">Pandas Data Pipeline • SHA-256 Checksums</span>
            </div>
            <h1 className="text-xl font-bold text-slate-900">Enterprise Dataset Manager</h1>
            <p className="text-xs text-slate-500 mt-1 max-w-2xl leading-relaxed">
              Upload, validate schema, audit missingness and duplicates, execute automated data cleaning, and export quarantined rejected records.
            </p>
          </div>

          <label className="flex items-center justify-center space-x-2 px-4 py-2.5 bg-gradient-to-r from-teal-600 to-sky-700 hover:from-teal-700 hover:to-sky-800 text-white rounded-xl text-xs font-bold cursor-pointer transition shadow-md shadow-teal-900/20">
            <Upload className={`w-4 h-4 ${uploading ? 'animate-spin' : ''}`} />
            <span>{uploading ? 'Ingesting File...' : 'Upload CSV / JSON Dataset'}</span>
            <input
              type="file"
              accept=".csv,.json"
              onChange={handleFileUpload}
              disabled={uploading}
              className="hidden"
            />
          </label>
        </div>
      </div>

      {/* Datasets Table */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-sm font-bold text-slate-900">Ingested Datasets & Audit Log</h2>
            <p className="text-xs text-slate-500">Tracked schemas, file hashes, and quarantine status</p>
          </div>
          <span className="text-xs px-2.5 py-1 rounded-md bg-slate-100 text-slate-600 font-medium">
            {datasets.length} Total Datasets
          </span>
        </div>

        {loading ? (
          <div className="py-12 text-center text-slate-400 text-xs">
            Loading datasets...
          </div>
        ) : datasets.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-200 text-slate-500 uppercase text-[10px]">
                  <th className="py-2.5 font-bold">Filename / Source</th>
                  <th className="py-2.5 font-bold text-center">Records</th>
                  <th className="py-2.5 font-bold text-center">Columns</th>
                  <th className="py-2.5 font-bold">SHA-256 Checksum</th>
                  <th className="py-2.5 font-bold text-center">Status</th>
                  <th className="py-2.5 font-bold text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {datasets.map((d) => (
                  <tr key={d.id} className="hover:bg-slate-50/80">
                    <td className="py-3">
                      <div className="font-bold text-slate-900">{d.original_filename}</div>
                      <div className="text-[10px] text-slate-400">
                        Uploaded {new Date(d.created_at).toLocaleDateString()} • {(d.file_size_bytes / 1024).toFixed(1)} KB
                      </div>
                    </td>
                    <td className="py-3 text-center font-bold text-slate-800">{d.row_count}</td>
                    <td className="py-3 text-center text-slate-600">{d.column_count}</td>
                    <td className="py-3 font-mono text-[11px] text-slate-500">
                      {d.checksum.slice(0, 16)}...
                    </td>
                    <td className="py-3 text-center">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        d.status === 'Cleaned'
                          ? 'bg-emerald-100 text-emerald-800'
                          : 'bg-sky-100 text-sky-800'
                      }`}>
                        {d.status}
                      </span>
                    </td>
                    <td className="py-3 text-right space-x-1.5">
                      <button
                        onClick={() => handlePreview(d.id)}
                        className="px-2.5 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-medium transition inline-flex items-center space-x-1"
                      >
                        <Eye className="w-3 h-3" />
                        <span>Preview</span>
                      </button>
                      <button
                        onClick={() => setCleaningDatasetId(d.id)}
                        className="px-2.5 py-1 bg-teal-50 hover:bg-teal-100 text-teal-700 border border-teal-200 rounded-lg text-xs font-semibold transition inline-flex items-center space-x-1"
                      >
                        <Filter className="w-3 h-3" />
                        <span>Clean</span>
                      </button>
                      <button
                        onClick={() => handleExportRejected(d.id)}
                        className="px-2.5 py-1 bg-slate-50 hover:bg-slate-100 text-slate-600 border border-slate-200 rounded-lg text-xs font-medium transition inline-flex items-center space-x-1"
                        title="Export Rejected / Quarantined Records"
                      >
                        <Download className="w-3 h-3" />
                        <span>Rejected</span>
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-12 text-slate-400 text-xs">
            No datasets uploaded yet. Upload a CSV or JSON file to get started.
          </div>
        )}
      </div>

      {/* Dataset Preview Modal / Drawer */}
      {selectedPreview && (
        <div className="bg-white p-6 rounded-2xl border border-slate-300 shadow-xl space-y-4 animate-fadeIn">
          <div className="flex items-center justify-between pb-3 border-b border-slate-200">
            <div>
              <span className="text-[10px] font-bold text-teal-600 uppercase tracking-wider block">
                Schema & Ingestion Preview
              </span>
              <h2 className="text-sm font-bold text-slate-900">
                {selectedPreview.filename} ({selectedPreview.row_count} rows, {selectedPreview.column_count} columns)
              </h2>
            </div>
            <button
              onClick={() => setSelectedPreview(null)}
              className="text-slate-400 hover:text-slate-600 text-sm font-bold p-1"
            >
              ✕
            </button>
          </div>

          {/* Quick Hygiene stats */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
            <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
              <span className="text-slate-500 block text-[10px]">Duplicates Detected</span>
              <span className="text-lg font-bold text-slate-900">{selectedPreview.duplicate_count}</span>
            </div>
            <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
              <span className="text-slate-500 block text-[10px]">Total Missing Cells</span>
              <span className="text-lg font-bold text-slate-900">
                {Object.values(selectedPreview.missing_counts).reduce((a, b) => a + b, 0)}
              </span>
            </div>
            <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 sm:col-span-2">
              <span className="text-slate-500 block text-[10px]">Columns Schema</span>
              <span className="text-xs font-mono font-medium text-slate-700 truncate block">
                {selectedPreview.columns.join(', ')}
              </span>
            </div>
          </div>

          {/* Sample Head Data Table */}
          <div className="overflow-x-auto max-h-72 border border-slate-200 rounded-xl">
            <table className="w-full text-left text-[11px]">
              <thead className="bg-slate-100 text-slate-700 uppercase font-bold sticky top-0">
                <tr>
                  {selectedPreview.columns.map((col) => (
                    <th key={col} className="px-3 py-2 border-b border-slate-200 truncate">
                      {col} <span className="text-[9px] text-slate-400 font-normal">({selectedPreview.dtypes[col]})</span>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {selectedPreview.head.map((row, i) => (
                  <tr key={i} className="hover:bg-slate-50">
                    {selectedPreview.columns.map((col) => (
                      <td key={col} className="px-3 py-2 text-slate-700 truncate max-w-xs font-mono">
                        {row[col] !== null && row[col] !== undefined ? String(row[col]) : <span className="text-slate-300">null</span>}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Cleaning Config Modal */}
      {cleaningDatasetId && (
        <div className="bg-white p-6 rounded-2xl border border-teal-300 shadow-xl space-y-4 animate-fadeIn">
          <div className="flex items-center justify-between pb-3 border-b border-slate-200">
            <div>
              <span className="text-[10px] font-bold text-teal-600 uppercase tracking-wider block">
                Automated Cleaning Pipeline
              </span>
              <h2 className="text-sm font-bold text-slate-900">
                Configure Dataset Cleaning Rules
              </h2>
            </div>
            <button
              onClick={() => setCleaningDatasetId(null)}
              className="text-slate-400 hover:text-slate-600 text-sm font-bold p-1"
            >
              ✕
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
            <div className="p-4 bg-slate-50 rounded-xl border border-slate-200">
              <label className="font-bold text-slate-800 block mb-2">Deduplication</label>
              <label className="flex items-center space-x-2 cursor-pointer text-slate-700">
                <input
                  type="checkbox"
                  checked={dropDuplicates}
                  onChange={(e) => setDropDuplicates(e.target.checked)}
                  className="rounded text-teal-600"
                />
                <span>Drop duplicate rows</span>
              </label>
              <p className="text-[10px] text-slate-400 mt-2">Removes redundant identical records</p>
            </div>

            <div className="p-4 bg-slate-50 rounded-xl border border-slate-200">
              <label className="font-bold text-slate-800 block mb-2">Missing Numeric Strategy</label>
              <select
                value={fillNumeric}
                onChange={(e) => setFillNumeric(e.target.value)}
                className="w-full text-xs px-2.5 py-1.5 rounded-lg bg-white border border-slate-200 focus:outline-hidden"
              >
                <option value="median">Fill with Median (Robust)</option>
                <option value="mean">Fill with Mean</option>
                <option value="drop">Drop Rows with Missing Values</option>
              </select>
              <p className="text-[10px] text-slate-400 mt-2">Applied to integer and float fields</p>
            </div>

            <div className="p-4 bg-slate-50 rounded-xl border border-slate-200">
              <label className="font-bold text-slate-800 block mb-2">Missing Categorical Strategy</label>
              <select
                value={fillCategorical}
                onChange={(e) => setFillCategorical(e.target.value)}
                className="w-full text-xs px-2.5 py-1.5 rounded-lg bg-white border border-slate-200 focus:outline-hidden"
              >
                <option value="mode">Fill with Most Frequent (Mode)</option>
                <option value="unknown">Fill with 'Unknown' Token</option>
                <option value="drop">Drop Rows with Missing Values</option>
              </select>
              <p className="text-[10px] text-slate-400 mt-2">Applied to text and categorical fields</p>
            </div>
          </div>

          <div className="flex justify-end space-x-2 pt-2">
            <button
              onClick={() => setCleaningDatasetId(null)}
              className="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-xl"
            >
              Cancel
            </button>
            <button
              onClick={handleClean}
              disabled={cleaning}
              className="px-5 py-2 bg-gradient-to-r from-teal-600 to-sky-700 hover:from-teal-700 hover:to-sky-800 text-white rounded-xl text-xs font-bold transition flex items-center space-x-1.5"
            >
              <Filter className={`w-3.5 h-3.5 ${cleaning ? 'animate-spin' : ''}`} />
              <span>{cleaning ? 'Cleaning...' : 'Execute Data Cleaning Pipeline'}</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
