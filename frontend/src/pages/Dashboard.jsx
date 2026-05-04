/**
 * Dashboard — premium light dizayn, lucide iconlar.
 */
import { useState, useEffect } from 'react';
import axios from 'axios';
import {
  Wallet,
  Banknote,
  CreditCard,
  TrendingUp,
  ShoppingCart,
  Download,
  Receipt,
  Users,
  AlertCircle,
} from 'lucide-react';

const API = 'http://localhost:8000/api';
function headers() { return { Authorization: `Bearer ${localStorage.getItem('token')}` }; }
const formatMoney = (n = 0) => new Intl.NumberFormat('uz-UZ').format(Math.round(n)) + ' so\'m';

const MOVEMENT_LABELS = {
  initial_balance: "Boshlang'ich balans",
  purchase_payment: "Xarid to'lovi",
  sale_payment: "Sotuv to'lovi",
  customer_debt_payment: "Mijoz qarz to'lovi",
  supplier_debt_payment: "Yetkazuvchi qarz to'lovi",
  expense: 'Xarajat',
  balance_adjustment: 'Balans tuzatish',
  cancellation: 'Bekor qilish',
};

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios.get(`${API}/reports/dashboard`, { headers: headers() })
      .then((res) => setData(res.data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="page"><p className="empty-message">Yuklanmoqda...</p></div>;
  }
  if (!data) {
    return <div className="page"><p className="empty-message">Ma'lumot yuklanmadi</p></div>;
  }

  const { balances, today, debts, recent_movements } = data;

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Bosh sahifa</h1>
      </div>

      {/* Balance cards */}
      <div className="stat-grid">
        <StatCard
          label="Umumiy balans"
          value={formatMoney(balances.total)}
          icon={Wallet}
          color="accent"
          valueColor="gold"
        />
        <StatCard
          label="Naqd"
          value={formatMoney(balances.cash)}
          icon={Banknote}
          color="success"
        />
        <StatCard
          label="Perechisleniya"
          value={formatMoney(balances.bank_transfer)}
          icon={CreditCard}
          color="info"
        />
      </div>

      {/* Today */}
      <div className="section-label">Bugun</div>
      <div className="stat-grid">
        <StatCard
          label="Sotuv"
          value={formatMoney(today.sale_amount)}
          sub={`${today.sale_count} ta operatsiya`}
          icon={ShoppingCart}
          color="success"
          valueColor="green"
        />
        <StatCard
          label="Yalpi foyda"
          value={formatMoney(today.profit)}
          sub="bugungi"
          icon={TrendingUp}
          color="accent"
          valueColor="gold"
        />
        <StatCard
          label="Xarid"
          value={formatMoney(today.purchase_amount)}
          sub={`${today.purchase_count} ta operatsiya`}
          icon={Download}
          color="info"
        />
        <StatCard
          label="Xarajat"
          value={formatMoney(today.expense_amount)}
          sub={`${today.expense_count} ta operatsiya`}
          icon={Receipt}
          color="danger"
          valueColor="red"
        />
      </div>

      {/* Debts */}
      <div className="section-label">Qarzlar</div>
      <div className="stat-grid">
        <StatCard
          label="Mijozlar qarzi (jami)"
          value={formatMoney(debts.customer_total)}
          icon={Users}
          color="warning"
          valueColor="red"
        />
        <StatCard
          label="Bizning qarzlar (jami)"
          value={formatMoney(debts.supplier_total)}
          icon={AlertCircle}
          color="danger"
          valueColor="red"
        />
      </div>

      {/* Recent movements */}
      <div className="card">
        <h2 className="card-title">So'nggi pul harakatlari</h2>
        {recent_movements.length === 0 ? (
          <p className="empty-message">Hozircha pul harakatlari yo'q</p>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Sana</th>
                  <th>Tur</th>
                  <th>To'lov turi</th>
                  <th>Yo'nalish</th>
                  <th style={{ textAlign: 'right' }}>Summa</th>
                  <th>Izoh</th>
                </tr>
              </thead>
              <tbody>
                {recent_movements.map((m) => (
                  <tr key={m.id}>
                    <td style={{ fontSize: '13px' }}>{new Date(m.date).toLocaleDateString('ru-RU')}</td>
                    <td style={{ fontSize: '13px' }}>{MOVEMENT_LABELS[m.movement_type] || m.movement_type}</td>
                    <td>{m.payment_type === 'cash' ? 'Naqd' : 'Perechisleniya'}</td>
                    <td>
                      <span
                        className={`badge ${m.direction === 'income' ? 'badge--income' : 'badge--outgoing'}`}
                      >
                        {m.direction === 'income' ? 'Kirim' : 'Chiqim'}
                      </span>
                    </td>
                    <td style={{ textAlign: 'right', fontWeight: 700 }}>{formatMoney(m.amount)}</td>
                    <td style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>{m.note || '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

/* ── Reusable StatCard ── */
function StatCard({ label, value, sub, icon: Icon, color = 'accent', valueColor }) {
  const valueClass = valueColor ? `stat-card-value stat-card-value--${valueColor}` : 'stat-card-value';
  return (
    <div className="stat-card">
      <div className={`stat-card-icon stat-card-icon--${color}`}>
        <Icon size={22} strokeWidth={2.2} />
      </div>
      <div className="stat-card-label">{label}</div>
      <div className={valueClass}>{value}</div>
      {sub && <div className="stat-card-sub">{sub}</div>}
    </div>
  );
}