import React, { useRef, useState } from 'react';
import { toast } from 'react-toastify';
import api from '../services/api';
import LoadingSpinner from '../components/common/LoadingSpinner';
import { ImportConfirmResponse, ImportPreviewResponse, ImportRowInput } from '../types';

type Tab = 'import' | 'export';

export default function ImportPage() {
  const [tab, setTab] = useState<Tab>('import');
  const [preview, setPreview] = useState<ImportPreviewResponse | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isImporting, setIsImporting] = useState(false);
  const [result, setResult] = useState<ImportConfirmResponse | null>(null);
  const [exportFormat, setExportFormat] = useState<'xlsx' | 'csv'>('xlsx');
  const [isExporting, setIsExporting] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setIsUploading(true);
    setPreview(null);
    setResult(null);
    try {
      const form = new FormData();
      form.append('file', file);
      const { data } = await api.post<ImportPreviewResponse>('/import/preview', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setPreview(data);
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? 'Error al procesar el archivo');
    } finally {
      setIsUploading(false);
      if (fileRef.current) fileRef.current.value = '';
    }
  };

  const handleConfirm = async () => {
    if (!preview) return;
    const validRows: ImportRowInput[] = preview.rows.filter(r => r.is_valid).map(r => r.data);
    if (!validRows.length) { toast.warning('No hay filas válidas para importar'); return; }
    setIsImporting(true);
    try {
      const { data } = await api.post<ImportConfirmResponse>('/import/confirm', { rows: validRows });
      setResult(data);
      setPreview(null);
      toast.success(`Importación completada: ${data.created} creados, ${data.skipped} omitidos`);
    } catch {
      toast.error('Error durante la importación');
    } finally {
      setIsImporting(false);
    }
  };

  const handleExport = async () => {
    setIsExporting(true);
    try {
      const response = await api.get(`/export/download?format=${exportFormat}`, { responseType: 'blob' });
      const url = URL.createObjectURL(response.data);
      const a = document.createElement('a');
      a.href = url;
      a.download = `contactos_${new Date().toISOString().slice(0, 10)}.${exportFormat}`;
      a.click();
      URL.revokeObjectURL(url);
      toast.success('Exportación descargada');
    } catch {
      toast.error('Error al exportar');
    } finally {
      setIsExporting(false);
    }
  };

  const downloadTemplate = async () => {
    try {
      const response = await api.get('/import/template', { responseType: 'blob' });
      const url = URL.createObjectURL(response.data);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'plantilla_contactos.xlsx';
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      toast.error('Error al descargar la plantilla');
    }
  };

  return (
    <div className="max-w-4xl">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Importación / Exportación</h1>

      {/* Tabs */}
      <div className="flex border-b mb-6">
        {(['import', 'export'] as Tab[]).map(t => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-6 py-3 text-sm font-medium transition-colors border-b-2 -mb-px ${
              tab === t ? 'border-primary-600 text-primary-600' : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            {t === 'import' ? '⬆ Importar' : '⬇ Exportar'}
          </button>
        ))}
      </div>

      {tab === 'import' && (
        <div className="space-y-4">
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-semibold text-gray-700">Subir archivo Excel o CSV</h2>
              <button onClick={downloadTemplate} className="btn-secondary text-xs">
                📥 Descargar plantilla
              </button>
            </div>
            <input ref={fileRef} type="file" accept=".xlsx,.csv" onChange={handleFileUpload} className="input-field" />
            {isUploading && <div className="flex items-center gap-2 mt-3 text-sm text-gray-500"><LoadingSpinner size="sm" /> Analizando archivo...</div>}
          </div>

          {preview && (
            <div className="card">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h2 className="font-semibold text-gray-700">Vista previa: {preview.filename}</h2>
                  <p className="text-sm text-gray-500 mt-1">
                    <span className="text-green-600 font-medium">{preview.valid_rows} válidas</span>
                    {preview.invalid_rows > 0 && <span className="text-red-600 font-medium ml-3">{preview.invalid_rows} con errores</span>}
                    <span className="ml-3 text-gray-400">/ {preview.total_rows} total</span>
                  </p>
                </div>
                <button onClick={handleConfirm} disabled={isImporting || preview.valid_rows === 0} className="btn-primary">
                  {isImporting ? <LoadingSpinner size="sm" /> : `Importar ${preview.valid_rows} contactos`}
                </button>
              </div>
              <div className="overflow-x-auto max-h-96 overflow-y-auto">
                <table className="min-w-full text-xs divide-y divide-gray-200">
                  <thead className="bg-gray-50 sticky top-0">
                    <tr>
                      <th className="px-3 py-2 text-left">Fila</th>
                      <th className="px-3 py-2 text-left">Nombre</th>
                      <th className="px-3 py-2 text-left">Apellido</th>
                      <th className="px-3 py-2 text-left">Email</th>
                      <th className="px-3 py-2 text-left">Empresa</th>
                      <th className="px-3 py-2 text-left">Sociedad</th>
                      <th className="px-3 py-2 text-left">Estado</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {preview.rows.map(row => (
                      <tr key={row.row_number} className={row.is_valid ? '' : 'bg-red-50'}>
                        <td className="px-3 py-2 text-gray-500">{row.row_number}</td>
                        <td className="px-3 py-2">{row.data.nombre}</td>
                        <td className="px-3 py-2">{row.data.apellido}</td>
                        <td className="px-3 py-2 text-gray-600">{row.data.email}</td>
                        <td className="px-3 py-2 text-gray-600">{row.data.empresa}</td>
                        <td className="px-3 py-2 text-gray-600">{row.data.sociedad}</td>
                        <td className="px-3 py-2">
                          {row.is_valid
                            ? <span className="text-green-600">✓</span>
                            : <span className="text-red-600" title={row.errors.join('; ')}>✗ {row.errors[0]}</span>
                          }
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {result && (
            <div className="card border-green-200 bg-green-50">
              <h2 className="font-semibold text-green-800 mb-2">Importación completada</h2>
              <div className="grid grid-cols-3 gap-4 text-center">
                <div><p className="text-2xl font-bold text-green-700">{result.created}</p><p className="text-xs text-gray-600">Creados</p></div>
                <div><p className="text-2xl font-bold text-yellow-600">{result.skipped}</p><p className="text-xs text-gray-600">Omitidos</p></div>
                <div><p className="text-2xl font-bold text-red-600">{result.errors}</p><p className="text-xs text-gray-600">Errores</p></div>
              </div>
            </div>
          )}
        </div>
      )}

      {tab === 'export' && (
        <div className="card">
          <h2 className="font-semibold text-gray-700 mb-4">Exportar todos los contactos activos</h2>
          <div className="flex items-center gap-4">
            <div>
              <label className="label-field">Formato</label>
              <select value={exportFormat} onChange={e => setExportFormat(e.target.value as 'xlsx' | 'csv')} className="input-field">
                <option value="xlsx">Excel (.xlsx)</option>
                <option value="csv">CSV (.csv)</option>
              </select>
            </div>
            <div className="pt-5">
              <button onClick={handleExport} disabled={isExporting} className="btn-primary">
                {isExporting ? <LoadingSpinner size="sm" /> : '⬇ Descargar'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
