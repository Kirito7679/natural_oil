/**
 * Balance API calls.
 */
import client from './client';

export const getBalance = () => client.get('/balance');

export const setInitialBalance = (cashAmount, bankTransferAmount) =>
  client.post('/balance/initial', {
    cash_amount: cashAmount,
    bank_transfer_amount: bankTransferAmount,
  });

export const adjustBalance = (paymentType, amount, note = '') =>
  client.post('/balance/adjust', {
    payment_type: paymentType,
    amount,
    note,
  });

export const getMoneyMovements = (skip = 0, limit = 50) =>
  client.get('/balance/movements', { params: { skip, limit } });
