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
  Flame,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const SECTIONS = [
  {
    label: 'Asosiy',
    items: [
      { to: '/', label: 'Bosh sahifa', icon: LayoutDashboard },
      { to: '/products', label: 'Mahsulotlar', icon: Package },
      { to: '/partners', label: 'Hamkorlar', icon: UsersIcon },
    ],
  },
  {
    label: 'Operatsiyalar',
    items: [
      { to: '/purchases', label: 'Prixod', icon: Download },
      { to: '/sales', label: 'Sotuv', icon: Upload },
      { to: '/inventory', label: 'Ombor', icon: Warehouse },
    ],
  },
  {
    label: 'Moliya',
    items: [
      { to: '/customer-debts', label: 'Qarzdorlar', icon: Wallet },
      { to: '/supplier-debts', label: 'Bizning qarzlar', icon: Banknote },
      { to: '/expenses', label: 'Xarajatlar', icon: Receipt },
    ],
  },
  {
    label: 'Tizim',
    items: [
      { to: '/reports', label: 'Hisobot', icon: TrendingUp },
      { to: '/users', label: 'Foydalanuvchilar', icon: UserCog },
    ],
  },
];

export default function Sidebar() {
  const { user, logout } = useAuth();

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="sidebar-logo-icon">
          <Flame size={20} strokeWidth={2.4} />
        </div>
        <div className="sidebar-brand">
          <span className="sidebar-logo">Natural Oil</span>
          <span className="sidebar-subtitle">ERP Tizimi</span>
        </div>
      </div>

      <nav className="sidebar-nav">
        {SECTIONS.map((section) => (
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
          <span className="sidebar-user-name">{user?.name || 'Admin'}</span>
          <span className="sidebar-user-role">
            {user?.role === 'admin' ? 'Administrator' : 'Operator'}
          </span>
        </div>
        <button className="sidebar-logout" onClick={logout}>
          <LogOut size={14} strokeWidth={2.4} />
          <span>Chiqish</span>
        </button>
      </div>
    </aside>
  );
}