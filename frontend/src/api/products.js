/**
 * Products API calls.
 */
import client from './client';

export const getProducts = (activeOnly = false) =>
  client.get('/products', { params: { active_only: activeOnly } });

export const getProduct = (id) =>
  client.get(`/products/${id}`);

export const createProduct = (data) =>
  client.post('/products', data);

export const updateProduct = (id, data) =>
  client.put(`/products/${id}`, data);

export const toggleProduct = (id) =>
  client.patch(`/products/${id}/toggle`);
