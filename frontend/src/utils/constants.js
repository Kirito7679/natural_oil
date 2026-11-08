/**
 * Application constants — payment types, labels, etc.
 *
 * IMPORTANT: Only 2 payment types: cash and bank_transfer. NO card.
 */

export const PAYMENT_TYPES = [
  { value: 'cash', label: 'Нақд' },
  { value: 'bank_transfer', label: 'Перечисления' },
];

export const PAYMENT_LABELS = {
  cash: 'Нақд',
  bank_transfer: 'Перечисления',
};

export const MOVEMENT_TYPE_LABELS = {
  initial_balance: "Бошланғич баланс",
  purchase_payment: "Приход тўлови",
  sale_payment: "Сотув тўлови",
  customer_debt_payment: "Мижоз қарзи тўлови",
  supplier_debt_payment: "Етказиб берувчи қарзи тўлови",
  expense: 'Харажат',
  balance_adjustment: 'Баланс тузатиш',
  cancellation: 'Бекор қилиш',
};

export const DIRECTION_LABELS = {
  income: 'Кирим',
  outgoing: 'Чиқим',
};

export const STATUS_LABELS = {
  active: 'Фаол',
  cancelled: 'Бекор қилинган',
  closed: 'Ёпилган',
  finished: 'Тугаган',
  deleted: "Ўчирилган",
};
