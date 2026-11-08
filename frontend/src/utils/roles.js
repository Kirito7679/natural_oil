/**
 * Rollar va ularga ruxsat etilgan sahifalar.
 * investor — faqat ko'radi: bosh sahifa, mahsulotlar, ombor, qarzlar, hisobot.
 */
export const ROLE_LABELS = {
  admin: 'Директор',
  operator: 'Оператор',
  investor: 'Инвестор',
};

export const INVESTOR_PATHS = ['/', '/products', '/inventory', '/customer-debts', '/supplier-debts', '/reports'];
export const ADMIN_ONLY_PATHS = ['/users'];

export function canAccess(role, path) {
  if (role === 'investor') return INVESTOR_PATHS.includes(path);
  if (ADMIN_ONLY_PATHS.includes(path)) return role === 'admin';
  return true;
}
