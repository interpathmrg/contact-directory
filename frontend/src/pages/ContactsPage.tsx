import React, { useCallback, useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import ConfirmDialog from '../components/common/ConfirmDialog';
import LoadingSpinner from '../components/common/LoadingSpinner';
import Pagination from '../components/common/Pagination';
import { useAuth } from '../hooks/useAuth';
import { contactService } from '../services/contactService';
import { Contact, ContactFilters, Society } from '../types';

type SortDir = 'asc' | 'desc';
type SortKey = 'apellido' | 'nombre' | 'empresa' | 'email' | 'sociedad_id';

export default function ContactsPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [filters, setFilters] = useState<ContactFilters>({ page: 1, page_size: 20, order_by: 'apellido', order_dir: 'asc' });
  const [search, setSearch] = useState('');
  const [deleteTarget, setDeleteTarget] = useState<Contact | null>(null);

  // Debounce search
  useEffect(() => {
    const timer = setTimeout(() => {
      setFilters(f => ({ ...f, search: search || undefined, page: 1 }));
    }, 400);
    return () => clearTimeout(timer);
  }, [search]);

  const { data, isLoading, isError } = useQuery(
    ['contacts', filters],
    () => contactService.list(filters),
    { keepPreviousData: true }
  );

  const { data: societies } = useQuery<Society[]>('societies', contactService.getSocieties);

  const deleteMutation = useMutation(
    (id: string) => contactService.delete(id),
    {
      onSuccess: () => {
        toast.success('Contacto eliminado');
        queryClient.invalidateQueries('contacts');
        setDeleteTarget(null);
      },
      onError: () => { toast.error('Error al eliminar el contacto'); },
    }
  );

  const handleSort = (col: SortKey) => {
    setFilters(f => ({
      ...f,
      order_by: col,
      order_dir: f.order_by === col && f.order_dir === 'asc' ? 'desc' : 'asc',
      page: 1,
    }));
  };

  const SortIcon = ({ col }: { col: string }) => {
    if (filters.order_by !== col) return <span className="text-gray-300 ml-1">↕</span>;
    return <span className="text-primary-600 ml-1">{filters.order_dir === 'asc' ? '↑' : '↓'}</span>;
  };

  const ColHeader = ({ col, label }: { col: SortKey; label: string }) => (
    <th
      className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 select-none"
      onClick={() => handleSort(col)}
    >
      {label}<SortIcon col={col} />
    </th>
  );

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Contactos</h1>
        {user?.is_admin && (
          <Link to="/contacts/new" className="btn-primary">
            + Nuevo Contacto
          </Link>
        )}
      </div>

      {/* Filtros */}
      <div className="card mb-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          <input
            type="text"
            placeholder="🔍 Búsqueda general..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="input-field lg:col-span-2"
          />
          <select
            value={filters.sociedad_id ?? ''}
            onChange={e => setFilters(f => ({ ...f, sociedad_id: e.target.value ? Number(e.target.value) : '', page: 1 }))}
            className="input-field"
          >
            <option value="">Todas las sociedades</option>
            {societies?.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
          </select>
          <input
            type="text"
            placeholder="Filtrar por empresa..."
            value={filters.empresa ?? ''}
            onChange={e => setFilters(f => ({ ...f, empresa: e.target.value, page: 1 }))}
            className="input-field"
          />
        </div>
        {(search || filters.sociedad_id || filters.empresa) && (
          <button
            onClick={() => { setSearch(''); setFilters({ page: 1, page_size: filters.page_size, order_by: 'apellido', order_dir: 'asc' }); }}
            className="mt-3 text-sm text-primary-600 hover:text-primary-700"
          >
            ✕ Limpiar filtros
          </button>
        )}
      </div>

      {/* Tabla */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        {isLoading ? (
          <div className="flex justify-center py-16"><LoadingSpinner /></div>
        ) : isError ? (
          <div className="text-center py-16 text-red-600">Error al cargar los contactos.</div>
        ) : !data?.items.length ? (
          <div className="text-center py-16 text-gray-500">No se encontraron contactos.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <ColHeader col="apellido" label="Apellido" />
                  <ColHeader col="nombre" label="Nombre" />
                  <ColHeader col="empresa" label="Empresa" />
                  <ColHeader col="sociedad_id" label="Sociedad" />
                  <ColHeader col="email" label="Email" />
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Teléfono</th>
                  {user?.is_admin && (
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Acciones</th>
                  )}
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-100">
                {data.items.map((c) => (
                  <tr key={c.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-4 py-3 font-medium text-gray-900 whitespace-nowrap">{c.apellido}</td>
                    <td className="px-4 py-3 text-gray-700 whitespace-nowrap">{c.nombre}</td>
                    <td className="px-4 py-3 text-gray-600 max-w-[200px] truncate">{c.empresa ?? '—'}</td>
                    <td className="px-4 py-3">
                      {c.society && (
                        <span className="inline-block bg-primary-100 text-primary-700 text-xs px-2 py-0.5 rounded-full">
                          {c.society.name}
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-gray-600 text-sm">
                      {c.email ? <a href={`mailto:${c.email}`} className="hover:text-primary-600">{c.email}</a> : '—'}
                    </td>
                    <td className="px-4 py-3 text-gray-600 text-sm">{c.telefono ?? c.celular ?? '—'}</td>
                    {user?.is_admin && (
                      <td className="px-4 py-3 text-right whitespace-nowrap">
                        <button
                          onClick={() => navigate(`/contacts/${c.id}/edit`)}
                          className="text-primary-600 hover:text-primary-800 text-sm mr-3 font-medium"
                        >
                          Editar
                        </button>
                        <button
                          onClick={() => setDeleteTarget(c)}
                          className="text-red-500 hover:text-red-700 text-sm font-medium"
                        >
                          Eliminar
                        </button>
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {data && data.total > 0 && (
          <Pagination
            currentPage={filters.page ?? 1}
            totalPages={data.pages}
            pageSize={filters.page_size ?? 20}
            total={data.total}
            onPageChange={(p) => setFilters(f => ({ ...f, page: p }))}
            onPageSizeChange={(s) => setFilters(f => ({ ...f, page_size: s, page: 1 }))}
          />
        )}
      </div>

      {/* Modal de confirmación */}
      <ConfirmDialog
        isOpen={!!deleteTarget}
        title="Eliminar contacto"
        message={`¿Eliminar a ${deleteTarget?.nombre} ${deleteTarget?.apellido}? Esta acción se puede revertir desde administración.`}
        confirmLabel="Eliminar"
        danger
        isLoading={deleteMutation.isLoading}
        onConfirm={() => deleteTarget && deleteMutation.mutate(deleteTarget.id)}
        onCancel={() => setDeleteTarget(null)}
      />
    </div>
  );
}
