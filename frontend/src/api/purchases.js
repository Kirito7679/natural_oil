import apiClient from './client';

export const getPurchases = () => apiClient.get('/purchases');
export const getPurchase = (id) => apiClient.get(`/purchases/${id}`);
export const createPurchase = (data) => apiClient.post('/purchases', data);
export const cancelPurchase = (id) => apiClient.patch(`/purchases/${id}/cancel`);
