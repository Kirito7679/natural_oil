/**
 * Login page — Uzbek labels.
 */
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Login() {
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(phone, password);
      navigate('/');
    } catch (err) {
      setError(
        err.response?.data?.detail || "Логин ёки парол нотўғри"
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-brand-panel">
        <div className="login-brand-drop" aria-hidden="true" />
        <div className="login-brand-text">
          <span className="login-brand-kicker">Natural Oil Products</span>
          <h2>Ёқилғи савдоси — битта тизимда.</h2>
          <p>Приход, омбор, сотув, қарзлар ва касса — барчаси реал вақтда.</p>
        </div>
      </div>
      <div className="login-card">
        <div className="login-header">
          <img className="login-logo-img" src="/brand/logo-full.png" alt="Natural Oil Products" />
          <p className="login-subtitle">ERP тизимига кириш</p>
        </div>
        <form onSubmit={handleSubmit} className="login-form">
          {error && <div className="alert alert--error">{error}</div>}
          <div className="form-group">
            <label htmlFor="phone">Логин (телефон ёки исм)</label>
            <input
              id="phone"
              type="text"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              placeholder="95 810 06 00"
              required
            />
          </div>
          <div className="form-group">
            <label htmlFor="password">Парол</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
            />
          </div>
          <button
            type="submit"
            className="btn btn--primary btn--full"
            disabled={loading}
          >
            {loading ? 'Кириш...' : 'Кириш'}
          </button>
        </form>
      </div>
    </div>
  );
}
