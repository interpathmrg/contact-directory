import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { toast } from 'react-toastify';
import api from '../services/api';
import LoadingSpinner from '../components/common/LoadingSpinner';
import ConfirmDialog from '../components/common/ConfirmDialog';
import { UserRoleEntry } from '../types';

export default function AdminPage() {
  const queryClient = useQueryClient();
  const [newEmail, setNewEmail] = useState('');
  const [newRole, setNewRole] = useState('VIEWER');
  const [revokeTarget, setRevokeTarget] = useState<UserRoleEntry | null>(null);

  const { data: users, isLoading } = useQuery<UserRoleEntry[]>(
    'admin-users',
    async () => { const { data } = await api.get('/admin/users'); return data; }
  );

  const assignMutation = useMutation(
    () => api.post('/admin/users', { user_email: newEmail, role_name: newRole }),
    {
      onSuccess: () => {
        toast.success(`Acceso asignado a ${newEmail}`);
        setNewEmail('');
        queryClient.invalidateQueries('admin-users');
      },
      onError: (err: any) => { toast.error(err?.response?.data?.detail ?? 'Error al asignar acceso'); },
    }
  );

  const changeRoleMutation = useMutation(
    ({ id, role }: { id: string; role: string }) =>
      api.put(`/admin/users/${id}/role`, { role_name: role }),
    {
      onSuccess: () => { toast.success('Rol actualizado'); queryClient.invalidateQueries('admin-users'); },
      onError: (err: any) => { toast.error(err?.response?.data?.detail ?? 'Error'); },
    }
  );

  const revokeMutation = useMutation(
    (id: string) => api.delete(`/admin/users/${id}`),
    {
      onSuccess: () => {
        toast.success('Acceso revocado');
        setRevokeTarget(null);
        queryClient.invalidateQueries('admin-users');
      },
      onError: (err: any) => { toast.error(err?.response?.data?.detail ?? 'Error'); },
    }
  );

  return (
    <div className="max-w-3xl">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Administración de Accesos</h1>

      {/* Asignar nuevo acceso */}
      <div className="card mb-6">
        <h2 className="font-semibold text-gray-700 mb-4">Dar acceso a un usuario</h2>
        <div className="flex gap-3">
          <input
            type="email"
            placeholder="email@corporativo.com"
            value={newEmail}
            onChange={e => setNewEmail(e.target.value)}
            className="input-field flex-1"
          />
          <select value={newRole} onChange={e => setNewRole(e.target.value)} className="input-field w-32">
            <option value="VIEWER">VIEWER</option>
            <option value="ADMIN">ADMIN</option>
          </select>
          <button
            onClick={() => assignMutation.mutate()}
            disabled={!newEmail || assignMutation.isLoading}
            className="btn-primary whitespace-nowrap"
          >
            {assignMutation.isLoading ? <LoadingSpinner size="sm" /> : '+ Asignar'}
          </button>
        </div>
      </div>

      {/* Lista de usuarios */}
      <div className="card">
        <h2 className="font-semibold text-gray-700 mb-4">Usuarios con acceso</h2>
        {isLoading ? (
          <div className="flex justify-center py-8"><LoadingSpinner /></div>
        ) : !users?.length ? (
          <p className="text-gray-500 text-sm">No hay usuarios registrados.</p>
        ) : (
          <table className="min-w-full divide-y divide-gray-200 text-sm">
            <thead>
              <tr>
                <th className="text-left py-2 text-xs font-medium text-gray-500 uppercase">Email</th>
                <th className="text-left py-2 text-xs font-medium text-gray-500 uppercase">Rol</th>
                <th className="text-left py-2 text-xs font-medium text-gray-500 uppercase">Asignado por</th>
                <th className="py-2" />
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {users.map(u => (
                <tr key={u.id} className="hover:bg-gray-50">
                  <td className="py-3 font-medium text-gray-900">{u.user_email}</td>
                  <td className="py-3">
                    <select
                      defaultValue={u.role.name}
                      onChange={e => changeRoleMutation.mutate({ id: u.id, role: e.target.value })}
                      className="text-xs border border-gray-300 rounded px-2 py-1"
                    >
                      <option value="VIEWER">VIEWER</option>
                      <option value="ADMIN">ADMIN</option>
                    </select>
                  </td>
                  <td className="py-3 text-gray-500 text-xs">{u.assigned_by ?? '—'}</td>
                  <td className="py-3 text-right">
                    <button
                      onClick={() => setRevokeTarget(u)}
                      className="text-red-500 hover:text-red-700 text-xs font-medium"
                    >
                      Revocar
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <ConfirmDialog
        isOpen={!!revokeTarget}
        title="Revocar acceso"
        message={`¿Revocar el acceso de ${revokeTarget?.user_email}?`}
        confirmLabel="Revocar"
        danger
        isLoading={revokeMutation.isLoading}
        onConfirm={() => revokeTarget && revokeMutation.mutate(revokeTarget.id)}
        onCancel={() => setRevokeTarget(null)}
      />
    </div>
  );
}
