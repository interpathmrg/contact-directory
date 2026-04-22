import api from './api';
import { User } from '../types';

export const authService = {
  async getLoginUrl(): Promise<{ auth_url: string; state: string }> {
    const { data } = await api.get('/auth/login');
    return data;
  },

  async getMe(): Promise<User> {
    const { data } = await api.get('/auth/me');
    return data;
  },

  async logout(): Promise<void> {
    await api.post('/auth/logout').catch(() => {});
    localStorage.removeItem('cd_access_token');
    localStorage.removeItem('cd_refresh_token');
    localStorage.removeItem('cd_expires_in');
  },
};
