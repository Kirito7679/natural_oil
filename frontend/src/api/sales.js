import apiClient from './client';

export const getSales = () => apiClient.get('/sales');
export const getSale = (id) => apiClient.get(`/sales/${id}`);
export const createSale = (data) => apiClient.post('/sales', data);
export const cancelSale = (id) => apiClient.patch(`/sales/${id}/cancel`);
