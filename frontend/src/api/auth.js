/**
 * Auth API calls.
 */
import client from './client';

export const login = (phone, password) =>
  client.post('/auth/login', { phone, password });

export const getMe = () => client.get('/auth/me');
