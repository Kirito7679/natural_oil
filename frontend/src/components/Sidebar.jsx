/**
 * Sidebar — premium navigation with sections and lucide icons.
 */
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Package,
  Users as UsersIcon,
  Download,
  Upload,
  Warehouse,
  Wallet,
  Banknote,
  Receipt,
  TrendingUp,
  UserCog,
  LogOut,
  X,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { canAccess, ROLE_LABELS } from '../utils/roles';

const SECTIONS = [
  {
    label: 'Асосий',
    items: [
      { to: '/', label: 'Бош саҳифа', icon: LayoutDashboard },
      { to: '/products', label: 'Маҳсулотлар', icon: Package },
      { to: '/partners', label: 'Ҳамкорлар', icon: UsersIcon },
    ],
  },
  {
    label: 'Операциялар',
    items: [
      { to: '/purchases', label: 'Приход', icon: Download },
      { to: '/sales', label: 'Сотув', icon: Upload },
      { to: '/inventory', label: 'Омбор', icon: Warehouse },
    ],
  },
  {
    label: 'Молия',
    items: [
      { to: '/customer-debts', label: 'Қарздорлар', icon: Wallet },
      { to: '/supplier-debts', label: 'Бизнинг қарзлар', icon: Banknote },
      { to: '/expenses', label: 'Харажатлар', icon: Receipt },
    ],
  },
  {
    label: 'Тизим',
    items: [
      { to: '/reports', label: 'Ҳисобот', icon: TrendingUp },
      { to: '/users', label: 'Фойдаланувчилар', icon: UserCog },
    ],
  },
];

export default function Sidebar({ onClose }) {
  const { user, logout } = useAuth();

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="sidebar-logo-icon">
          <img src="/brand/logo-mark.png" alt="NOP" />
        </div>
        <button className="sidebar-close" onClick={onClose} aria-label="Ёпиш"><X size={20} /></button>
        <div className="sidebar-brand">
          <span className="sidebar-logo">Natural Oil</span>
          <span className="sidebar-subtitle">{user?.role === 'investor' ? 'Инвестор панели' : 'Products · ERP'}</span>
        </div>
      </div>

      <nav className="sidebar-nav">
        {SECTIONS.map((section) => ({ ...section, items: section.items.filter((i) => canAccess(user?.role, i.to)) }))
          .filter((section) => section.items.length > 0)
          .map((section) => (
          <div key={section.label}>
            <div className="sidebar-section-label">{section.label}</div>
            {section.items.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.to === '/'}
                  className={({ isActive }) =>
                    `sidebar-link ${isActive ? 'sidebar-link--active' : ''}`
                  }
                >
                  <span className="sidebar-link-icon">
                    <Icon size={17} strokeWidth={2.2} />
                  </span>
                  <span>{item.label}</span>
                </NavLink>
              );
            })}
          </div>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div className="sidebar-user">
          <span className="sidebar-user-avatar">{(user?.name || 'A').charAt(0).toUpperCase()}</span>
          <div className="sidebar-user-info">
          <span className="sidebar-user-name">{user?.name || 'Admin'}</span>
          <span className="sidebar-user-role">
            {ROLE_LABELS[user?.role] || user?.role}
          </span>
          </div>
        </div>
        <button className="sidebar-logout" onClick={logout}>
          <LogOut size={14} strokeWidth={2.4} />
          <span>Чиқиш</span>
        </button>
      </div>
    </aside>
  );
}