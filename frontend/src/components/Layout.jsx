/**
 * Main layout with sidebar and content area.
 */
import { useEffect, useState } from 'react';
import { Outlet, Navigate, useLocation } from 'react-router-dom';
import { Menu } from 'lucide-react';
import { canAccess } from '../utils/roles';
import { useAuth } from '../context/AuthContext';
import Sidebar from './Sidebar';

export default function Layout() {
  const { user, loading } = useAuth();
  const location = useLocation();
  const [menuOpen, setMenuOpen] = useState(false);

  // Sahifa almashganda mobil menyu yopiladi
  useEffect(() => { setMenuOpen(false); }, [location.pathname]);

  if (loading) {
    return (
      <div className="loading-screen">
        <div className="loading-spinner" />
        <p>Юкланмоқда...</p>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (!canAccess(user.role, location.pathname)) {
    return <Navigate to="/" replace />;
  }

  return (
    <div className={`app-layout role-${user.role} ${menuOpen ? 'menu-open' : ''}`}>
      <header className="mobile-topbar">
        <button className="mobile-menu-btn" onClick={() => setMenuOpen(true)} aria-label="Менюни очиш">
          <Menu size={22} strokeWidth={2.4} />
        </button>
        <div className="mobile-brand">
          <span className="mobile-brand-icon"><img src="/brand/logo-mark.png" alt="" /></span>
          <span>Natural Oil</span>
        </div>
        <span className="mobile-role">{user.role === 'investor' ? 'Инвестор' : ''}</span>
      </header>
      <div className="sidebar-backdrop" onClick={() => setMenuOpen(false)} />
      <Sidebar onClose={() => setMenuOpen(false)} />
      <main className="app-content">
        <Outlet />
      </main>
    </div>
  );
}
