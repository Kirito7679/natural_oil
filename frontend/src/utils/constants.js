/**
 * Application constants — payment types, labels, etc.
 *
 * IMPORTANT: Only 2 payment types: cash and bank_transfer. NO card.
 */

export const PAYMENT_TYPES = [
  { value: 'cash', label: 'Naqd' },
  { value: 'bank_transfer', label: 'Perechisleniya' },
];

export const PAYMENT_LABELS = {
  cash: 'Naqd',
  bank_transfer: 'Perechisleniya',
};

export const MOVEMENT_TYPE_LABELS = {
  initial_balance: "Boshlang'ich balans",
  purchase_payment: "Prixod to'lovi",
  sale_payment: "Sotuv to'lovi",
  customer_debt_payment: "Mijoz qarzi to'lovi",
  supplier_debt_payment: "Yetkazib beruvchi qarzi to'lovi",
  expense: 'Xarajat',
  balance_adjustment: 'Balans tuzatish',
  cancellation: 'Bekor qilish',
};

export const DIRECTION_LABELS = {
  income: 'Kirim',
  outgoing: 'Chiqim',
};

export const STATUS_LABELS = {
  active: 'Faol',
  cancelled: 'Bekor qilingan',
  closed: 'Yopilgan',
  finished: 'Tugagan',
  deleted: "O'chirilgan",
};
