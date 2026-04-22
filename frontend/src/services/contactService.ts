import api from './api';
import { Contact, ContactFilters, ContactFormData, PaginatedResponse, Society } from '../types';

export const contactService = {
  async list(filters: ContactFilters = {}): Promise<PaginatedResponse<Contact>> {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([k, v]) => {
      if (v !== undefined && v !== '' && v !== null) params.set(k, String(v));
    });
    const { data } = await api.get(`/contacts?${params.toString()}`);
    return data;
  },

  async getById(id: string): Promise<Contact> {
    const { data } = await api.get(`/contacts/${id}`);
    return data;
  },

  async create(payload: Partial<ContactFormData>): Promise<Contact> {
    const { data } = await api.post('/contacts', normalisePayload(payload));
    return data;
  },

  async update(id: string, payload: Partial<ContactFormData>): Promise<Contact> {
    const { data } = await api.put(`/contacts/${id}`, normalisePayload(payload));
    return data;
  },

  async delete(id: string): Promise<void> {
    await api.delete(`/contacts/${id}`);
  },

  async getSocieties(): Promise<Society[]> {
    const { data } = await api.get('/contacts/societies/all');
    return data;
  },
};

function normalisePayload(form: Partial<ContactFormData>): Record<string, unknown> {
  const out: Record<string, unknown> = {};
  Object.entries(form).forEach(([k, v]) => {
    if (k === 'sociedad_id') {
      out[k] = v === '' || v === undefined ? null : Number(v);
    } else {
      out[k] = v === '' ? null : v;
    }
  });
  return out;
}
