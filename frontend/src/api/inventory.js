import apiClient from './client';

export const getInventoryBatches = (status = 'active') => 
  apiClient.get('/inventory/batches', { params: { status } });
  
export const getInventorySummary = () => 
  apiClient.get('/inventory/summary');
