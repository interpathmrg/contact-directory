export interface Society {
  id: number;
  name: string;
}

export interface Contact {
  id: string;
  nombre: string;
  apellido: string;
  empresa: string | null;
  cargo: string | null;
  puesto: string | null;
  direccion: string | null;
  telefono: string | null;
  celular: string | null;
  email: string | null;
  nombre_contacto_interno: string | null;
  email_contacto_interno: string | null;
  telefono_contacto_interno: string | null;
  nota: string | null;
  sociedad_id: number | null;
  society: Society | null;
  created_at: string;
  updated_at: string;
  updated_by: string | null;
  is_active: boolean;
}

export interface ContactFormData {
  nombre: string;
  apellido: string;
  empresa: string;
  cargo: string;
  puesto: string;
  direccion: string;
  telefono: string;
  celular: string;
  email: string;
  nombre_contacto_interno: string;
  email_contacto_interno: string;
  telefono_contacto_interno: string;
  nota: string;
  sociedad_id: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface ContactFilters {
  search?: string;
  sociedad_id?: number | '';
  empresa?: string;
  nombre?: string;
  page?: number;
  page_size?: number;
  order_by?: string;
  order_dir?: 'asc' | 'desc';
}

export interface User {
  email: string;
  name: string;
  role: string | null;
  permissions: Record<string, unknown>;
  is_admin: boolean;
}

export interface TokenPayload {
  sub: string;
  name: string;
  role: string | null;
  permissions: Record<string, unknown>;
  exp: number;
}

export interface UserRoleEntry {
  id: string;
  user_email: string;
  role: { id: number; name: string; description: string | null; permissions: Record<string, unknown> };
  assigned_by: string | null;
  assigned_at: string;
}

export interface LabelRequest {
  sociedad_ids?: number[];
  empresa?: string;
  nombre?: string;
  contact_ids?: string[];
  order_by: string;
}

export interface LabelContactItem {
  id: string;
  nombre: string;
  apellido: string;
  empresa: string | null;
  sociedad: string | null;
}

export interface ImportRowInput {
  nombre: string;
  apellido: string;
  empresa: string;
  cargo: string;
  puesto: string;
  direccion: string;
  telefono: string;
  celular: string;
  email: string;
  nombre_contacto_interno: string;
  email_contacto_interno: string;
  telefono_contacto_interno: string;
  nota: string;
  sociedad: string;
}

export interface ImportRowPreview {
  row_number: number;
  data: ImportRowInput;
  errors: string[];
  is_valid: boolean;
}

export interface ImportPreviewResponse {
  filename: string;
  total_rows: number;
  valid_rows: number;
  invalid_rows: number;
  rows: ImportRowPreview[];
}

export interface ImportConfirmResponse {
  total: number;
  created: number;
  skipped: number;
  errors: number;
  results: { row_number: number; email: string; nombre: string; apellido: string; status: string; message: string }[];
}
