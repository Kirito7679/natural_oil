/**
 * Dashboard — premium light dizayn, lucide iconlar.
 */
import { useState, useEffect } from 'react';
import client from '../api/client';
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

import { formatMoneyInput, parseMoneyInput } from '../utils/formatters';

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

  const [showInitialBalanceModal, setShowInitialBalanceModal] = useState(false);
  const [initialForm, setInitialForm] = useState({ date: new Date().toISOString().slice(0, 10), payment_type: 'cash', amount: '', note: '' });
  const [initialLoading, setInitialLoading] = useState(false);
  const [initialError, setInitialError] = useState('');

  const fetchDashboard = () => {
    client.get(`/reports/dashboard`)
      .then((res) => setData(res.data))
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchDashboard();
  }, []);

  const submitInitialBalance = async () => {
    const numAmount = parseMoneyInput(initialForm.amount);
    if (!numAmount || numAmount <= 0) return setInitialError("Summani to'g'ri kiriting.");
    setInitialLoading(true);
    setInitialError('');
    try {
      await client.post('/balance/add-initial', {
        ...initialForm,
        amount: numAmount
      });
      setShowInitialBalanceModal(false);
      setInitialForm({ date: new Date().toISOString().slice(0, 10), payment_type: 'cash', amount: '', note: '' });
      fetchDashboard();
    } catch (e) {
      setInitialError(e.response?.data?.detail || 'Xato yuz berdi.');
    } finally {
      setInitialLoading(false);
    }
  };

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
        <button 
            className="btn btn-primary"
            onClick={() => { setShowInitialBalanceModal(true); setInitialError(''); }}
        >
            + O'zida bor pul qo'shish
        </button>
      </div>

      {/* Balance cards */}
      <div className="stat-grid">
        <StatCard
          label="Umumiy balans"
          value={formatMoney(balances.total)}
          icon={Wallet}
          color={balances.total >= 0 ? "accent" : "danger"}
          valueColor={balances.total >= 0 ? "gold" : "red"}
        />
        <StatCard
          label="Naqd"
          value={formatMoney(balances.cash)}
          icon={Banknote}
          color={balances.cash >= 0 ? "success" : "danger"}
          valueColor={balances.cash >= 0 ? "green" : "red"}
        />
        <StatCard
          label="Perechisleniya"
          value={formatMoney(balances.bank_transfer)}
          icon={CreditCard}
          color={balances.bank_transfer >= 0 ? "info" : "danger"}
          valueColor={balances.bank_transfer >= 0 ? "blue" : "red"}
        />
      </div>

      <div className="section-label">Bugun va Ombordagi holat</div>
      <div className="stat-grid">
        <StatCard
          label="Ombordagi yoqilg'i qiymati"
          value={formatMoney(data.inventory_value || 0)}
          icon={ShoppingCart}
          color="info"
        />
        <StatCard
          label="Bugungi tushum (Kirim)"
          value={formatMoney(today.income_amount)}
          sub={`${today.sale_count} ta sotuv`}
          icon={TrendingUp}
          color="success"
          valueColor="green"
        />
        <StatCard
          label="Bugungi xarajat"
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

      {showInitialBalanceModal && (
        <div className="modal-overlay" onClick={() => setShowInitialBalanceModal(false)}>
            <div className="modal" onClick={(e) => e.stopPropagation()}>
                <div className="modal-header">
                    <h2>O'zida bor pul qo'shish (Boshlang'ich balans)</h2>
                    <button className="modal-close" onClick={() => setShowInitialBalanceModal(false)}>✕</button>
                </div>
                <div className="modal-body">
                    <div className="form-group">
                        <label>Sana</label>
                        <input type="date" className="form-control" value={initialForm.date} onChange={(e) => setInitialForm({ ...initialForm, date: e.target.value })} />
                    </div>
                    <div className="form-group">
                        <label>To'lov turi</label>
                        <select className="form-control" value={initialForm.payment_type} onChange={(e) => setInitialForm({ ...initialForm, payment_type: e.target.value })}>
                            <option value="cash">Naqd</option>
                            <option value="bank_transfer">Perechisleniya</option>
                        </select>
                    </div>
                    <div className="form-group">
                        <label>Summa (so'm)</label>
                        <input 
                            type="text" 
                            className="form-control" 
                            value={initialForm.amount} 
                            onChange={(e) => setInitialForm({ ...initialForm, amount: formatMoneyInput(e.target.value) })} 
                            placeholder="Masalan: 10 000 000" 
                        />
                    </div>
                    <div className="form-group">
                        <label>Izoh (ixtiyoriy)</label>
                        <input type="text" className="form-control" value={initialForm.note} onChange={(e) => setInitialForm({ ...initialForm, note: e.target.value })} />
                    </div>
                    {initialError && <p style={{ color: 'var(--danger)', marginTop: '0.5rem' }}>{initialError}</p>}
                </div>
                <div className="modal-footer">
                    <button className="btn btn-secondary" onClick={() => setShowInitialBalanceModal(false)}>Bekor qilish</button>
                    <button className="btn btn-primary" onClick={submitInitialBalance} disabled={initialLoading}>
                        {initialLoading ? 'Saqlanmoqda...' : 'Saqlash'}
                    </button>
                </div>
            </div>
        </div>
      )}
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