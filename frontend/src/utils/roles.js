/**
 * Rollar va ularga ruxsat etilgan sahifalar.
 * investor — faqat ko'radi: bosh sahifa, mahsulotlar, ombor, qarzlar, hisobot.
 */
export const ROLE_LABELS = {
  admin: 'Директор',
  dev: 'DEV',
  operator: 'Оператор',
  investor: 'Инвестор',
};

// Direktor — biznes egasi, dev — tizimga javob beradigan texnik ma'mur.
// Huquqlari bir xil (backend: app/utils/enums.py FULL_ACCESS_ROLES).
export const FULL_ACCESS_ROLES = ['admin', 'dev'];

export const INVESTOR_PATHS = ['/', '/products', '/inventory', '/customer-debts', '/supplier-debts', '/reports'];
export const ADMIN_ONLY_PATHS = ['/users'];

export function canAccess(role, path) {
  if (role === 'investor') return INVESTOR_PATHS.includes(path);
  if (ADMIN_ONLY_PATHS.includes(path)) return FULL_ACCESS_ROLES.includes(role);
  return true;
}
