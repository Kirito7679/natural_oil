/**
 * Partners API calls.
 */
import client from './client';

export const getPartners = (params = {}) =>
  client.get('/partners', { params });

export const getPartner = (id) =>
  client.get(`/partners/${id}`);

export const createPartner = (data) =>
  client.post('/partners', data);

export const updatePartner = (id, data) =>
  client.put(`/partners/${id}`, data);

export const togglePartner = (id) =>
  client.patch(`/partners/${id}/toggle`);
