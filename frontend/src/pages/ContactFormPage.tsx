import React, { useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { toast } from 'react-toastify';
import LoadingSpinner from '../components/common/LoadingSpinner';
import { contactService } from '../services/contactService';
import { ContactFormData, Society } from '../types';

export default function ContactFormPage() {
  const { id } = useParams<{ id: string }>();
  const isEdit = Boolean(id);
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const { register, handleSubmit, reset, formState: { errors, isDirty } } = useForm<ContactFormData>({
    defaultValues: {
      nombre: '', apellido: '', empresa: '', cargo: '', puesto: '',
      direccion: '', telefono: '', celular: '', email: '',
      nombre_contacto_interno: '', email_contacto_interno: '',
      telefono_contacto_interno: '', nota: '', sociedad_id: '',
    },
  });

  const { data: societies } = useQuery<Society[]>('societies', contactService.getSocieties);

  const { data: contact, isLoading: isLoadingContact } = useQuery(
    ['contact', id],
    () => contactService.getById(id!),
    {
      enabled: isEdit,
      onSuccess: (data) => reset({
        nombre: data.nombre ?? '',
        apellido: data.apellido ?? '',
        empresa: data.empresa ?? '',
        cargo: data.cargo ?? '',
        puesto: data.puesto ?? '',
        direccion: data.direccion ?? '',
        telefono: data.telefono ?? '',
        celular: data.celular ?? '',
        email: data.email ?? '',
        nombre_contacto_interno: data.nombre_contacto_interno ?? '',
        email_contacto_interno: data.email_contacto_interno ?? '',
        telefono_contacto_interno: data.telefono_contacto_interno ?? '',
        nota: data.nota ?? '',
        sociedad_id: data.sociedad_id ? String(data.sociedad_id) : '',
      }),
    }
  );

  const saveMutation = useMutation(
    (data: Partial<ContactFormData>) =>
      isEdit ? contactService.update(id!, data) : contactService.create(data),
    {
      onSuccess: () => {
        toast.success(isEdit ? 'Contacto actualizado' : 'Contacto creado');
        queryClient.invalidateQueries('contacts');
        navigate('/contacts');
      },
      onError: (err: any) => {
        const msg = err?.response?.data?.detail ?? 'Error al guardar el contacto';
        toast.error(typeof msg === 'string' ? msg : JSON.stringify(msg));
      },
    }
  );

  if (isEdit && isLoadingContact) return <div className="flex justify-center py-16"><LoadingSpinner /></div>;

  const Section = ({ title, children }: { title: string; children: React.ReactNode }) => (
    <div className="card mb-4">
      <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wider mb-4 pb-2 border-b">
        {title}
      </h3>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {children}
      </div>
    </div>
  );

  const Field = ({ name, label, required, type = 'text', fullWidth = false }: {
    name: keyof ContactFormData; label: string; required?: boolean; type?: string; fullWidth?: boolean;
  }) => (
    <div className={fullWidth ? 'sm:col-span-2' : ''}>
      <label className="label-field">
        {label}{required && <span className="text-red-500 ml-0.5">*</span>}
      </label>
      <input
        type={type}
        {...register(name, {
          required: required ? `${label} es obligatorio` : false,
          ...(type === 'email' ? { pattern: { value: /^[^\s@]+@[^\s@]+\.[^\s@]+$/, message: 'Email inválido' } } : {}),
        })}
        className={`input-field ${errors[name] ? 'border-red-400 focus:border-red-500 focus:ring-red-500' : ''}`}
      />
      {errors[name] && <p className="mt-1 text-xs text-red-600">{errors[name]?.message as string}</p>}
    </div>
  );

  return (
    <div className="max-w-3xl mx-auto">
      <div className="flex items-center gap-3 mb-6">
        <button onClick={() => navigate(-1)} className="text-gray-500 hover:text-gray-700">
          ← Volver
        </button>
        <h1 className="text-2xl font-bold text-gray-900">
          {isEdit ? 'Editar Contacto' : 'Nuevo Contacto'}
        </h1>
      </div>

      <form onSubmit={handleSubmit((data) => saveMutation.mutate(data))}>
        <Section title="Información Personal">
          <Field name="nombre" label="Nombre" required />
          <Field name="apellido" label="Apellido" required />
          <Field name="empresa" label="Empresa" />
          <Field name="cargo" label="Cargo" />
          <Field name="puesto" label="Puesto" fullWidth />
          <div>
            <label className="label-field">Sociedad</label>
            <select {...register('sociedad_id')} className="input-field">
              <option value="">— Sin sociedad —</option>
              {societies?.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
            </select>
          </div>
          <div />
        </Section>

        <Section title="Datos de Contacto">
          <Field name="email" label="Email" type="email" />
          <Field name="telefono" label="Teléfono" />
          <Field name="celular" label="Celular" />
          <Field name="direccion" label="Dirección" fullWidth />
        </Section>

        <Section title="Contacto Interno">
          <Field name="nombre_contacto_interno" label="Nombre Contacto Interno" fullWidth />
          <Field name="email_contacto_interno" label="Email Contacto Interno" type="email" />
          <Field name="telefono_contacto_interno" label="Teléfono Contacto Interno" />
        </Section>

        <div className="card mb-6">
          <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wider mb-4 pb-2 border-b">
            Nota
          </h3>
          <textarea
            {...register('nota')}
            rows={4}
            placeholder="Observaciones adicionales..."
            className="input-field resize-none"
          />
        </div>

        {/* Acciones */}
        <div className="flex items-center justify-end gap-3">
          <button type="button" onClick={() => navigate(-1)} className="btn-secondary">
            Cancelar
          </button>
          <button
            type="submit"
            disabled={saveMutation.isLoading || (isEdit && !isDirty)}
            className="btn-primary"
          >
            {saveMutation.isLoading ? <LoadingSpinner size="sm" /> : isEdit ? 'Guardar cambios' : 'Crear contacto'}
          </button>
        </div>
      </form>
    </div>
  );
}
