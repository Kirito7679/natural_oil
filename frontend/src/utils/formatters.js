/**
 * Number and date formatting utilities.
 */

/**
 * Format number as UZS currency (e.g., 50,000,000)
 */
export function formatMoney(value) {
  if (value == null) return '0';
  return Number(value).toLocaleString('uz-UZ');
}

export const formatCurrency = formatMoney;
export const formatNumber = formatMoney;

/**
 * Format date string to DD.MM.YYYY
 */
export function formatDate(dateStr) {
  if (!dateStr) return '';
  const d = new Date(dateStr);
  return d.toLocaleDateString('ru-RU');
}

/**
 * Format datetime string to DD.MM.YYYY HH:mm
 */
export function formatDateTime(dateStr) {
  if (!dateStr) return '';
  const d = new Date(dateStr);
  return d.toLocaleString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}
