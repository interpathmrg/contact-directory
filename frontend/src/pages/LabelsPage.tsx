import React, { useState } from 'react';
import { useQuery } from 'react-query';
import { toast } from 'react-toastify';
import api from '../services/api';
import { contactService } from '../services/contactService';
import LoadingSpinner from '../components/common/LoadingSpinner';
import { LabelContactItem, LabelRequest, Society } from '../types';

export default function LabelsPage() {
  const [req, setReq] = useState<LabelRequest>({ order_by: 'apellido' });
  const [preview, setPreview] = useState<LabelContactItem[] | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isLoadingPreview, setIsLoadingPreview] = useState(false);

  const { data: societies } = useQuery<Society[]>('societies', contactService.getSocieties);

  const handlePreview = async () => {
    setIsLoadingPreview(true);
    try {
      const { data } = await api.post('/labels/preview', req);
      setPreview(data.contacts);
      if (data.total === 0) toast.info('No se encontraron contactos con esos filtros');
    } catch {
      toast.error('Error al cargar la vista previa');
    } finally {
      setIsLoadingPreview(false);
    }
  };

  const handleDownloadPDF = async () => {
    setIsGenerating(true);
    try {
      const response = await api.post('/labels/pdf', req, { responseType: 'blob' });
      const url = URL.createObjectURL(response.data);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'etiquetas_invitacion.pdf';
      a.click();
      URL.revokeObjectURL(url);
      toast.success('PDF generado correctamente');
    } catch {
      toast.error('Error al generar el PDF');
    } finally {
      setIsGenerating(false);
    }
  };

  const ORDER_OPTIONS = [
    { value: 'apellido', label: 'Apellido' },
    { value: 'nombre', label: 'Nombre' },
    { value: 'empresa', label: 'Empresa' },
    { value: 'sociedad', label: 'Sociedad' },
  ];

  return (
    <div className="max-w-4xl">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Etiquetas de Invitación</h1>

      {/* Filtros */}
      <div className="card mb-6">
        <h2 className="text-sm font-semibold text-gray-700 uppercase tracking-wider mb-4">Filtros</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <div>
            <label className="label-field">Sociedad(es)</label>
            <div className="space-y-1">
              {societies?.map(s => (
                <label key={s.id} className="flex items-center gap-2 text-sm cursor-pointer">
                  <input
                    type="checkbox"
                    checked={req.sociedad_ids?.includes(s.id) ?? false}
                    onChange={e => {
                      const ids = req.sociedad_ids ?? [];
                      setReq(r => ({
                        ...r,
                        sociedad_ids: e.target.checked ? [...ids, s.id] : ids.filter(i => i !== s.id),
                      }));
                      setPreview(null);
                    }}
                    className="rounded text-primary-600"
                  />
                  {s.name}
                </label>
              ))}
            </div>
          </div>
          <div>
            <label className="label-field">Empresa</label>
            <input
              type="text"
              placeholder="Filtrar por empresa..."
              value={req.empresa ?? ''}
              onChange={e => { setReq(r => ({ ...r, empresa: e.target.value || undefined })); setPreview(null); }}
              className="input-field"
            />
            <label className="label-field mt-3">Nombre / Apellido</label>
            <input
              type="text"
              placeholder="Filtrar por nombre..."
              value={req.nombre ?? ''}
              onChange={e => { setReq(r => ({ ...r, nombre: e.target.value || undefined })); setPreview(null); }}
              className="input-field"
            />
          </div>
          <div>
            <label className="label-field">Ordenar por</label>
            <select
              value={req.order_by}
              onChange={e => { setReq(r => ({ ...r, order_by: e.target.value })); setPreview(null); }}
              className="input-field"
            >
              {ORDER_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
            </select>
          </div>
        </div>
        <div className="flex gap-3 mt-4">
          <button onClick={handlePreview} disabled={isLoadingPreview} className="btn-secondary">
            {isLoadingPreview ? <LoadingSpinner size="sm" /> : '👁 Vista previa'}
          </button>
          <button
            onClick={handleDownloadPDF}
            disabled={isGenerating || preview === null}
            className="btn-primary"
          >
            {isGenerating ? <LoadingSpinner size="sm" /> : '⬇ Descargar PDF'}
          </button>
        </div>
      </div>

      {/* Vista previa */}
      {preview !== null && (
        <div className="card">
          <h2 className="text-sm font-semibold text-gray-700 uppercase tracking-wider mb-4">
            Vista previa — {preview.length} etiqueta{preview.length !== 1 ? 's' : ''}
          </h2>
          {preview.length === 0 ? (
            <p className="text-gray-500 text-sm">Sin resultados con los filtros actuales.</p>
          ) : (
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3 max-h-96 overflow-y-auto">
              {preview.map(c => (
                <div key={c.id} className="border border-dashed border-gray-300 rounded p-3 text-xs">
                  <p className="font-bold text-gray-900">{c.nombre} {c.apellido}</p>
                  {c.empresa && <p className="text-gray-600 truncate">{c.empresa}</p>}
                  {c.sociedad && <p className="text-primary-600 italic">{c.sociedad}</p>}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
