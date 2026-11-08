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

const formatMoney = (n = 0) => new Intl.NumberFormat('uz-UZ').format(Math.round(n)) + ' сўм';

const MOVEMENT_LABELS = {
  initial_balance: "Бошланғич баланс",
  purchase_payment: "Харид тўлови",
  sale_payment: "Сотув тўлови",
  customer_debt_payment: "Мижоз қарз тўлови",
  supplier_debt_payment: "Етказувчи қарз тўлови",
  expense: 'Харажат',
  balance_adjustment: 'Баланс тузатиш',
  cancellation: 'Бекор қилиш',
};

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  const [showInitialBalanceModal, setShowInitialBalanceModal] = useState(false);
  const [showBalanceBreakdown, setShowBalanceBreakdown] = useState(false);
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
    if (!numAmount || numAmount <= 0) return setInitialError("Суммани тўғри киритинг.");
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
      setInitialError(e.response?.data?.detail || 'Хато юз берди.');
    } finally {
      setInitialLoading(false);
    }
  };

  if (loading) {
    return <div className="page"><p className="empty-message">Юкланмоқда...</p></div>;
  }
  if (!data) {
    return <div className="page"><p className="empty-message">Маълумот юкланмади</p></div>;
  }

  const { balances, today, debts, recent_movements } = data;
  const umumiyBalans = balances.cash + balances.bank_transfer + (data.inventory_value || 0) + debts.customer_total - debts.supplier_total;

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Бош саҳифа</h1>
        <button 
            className="write-action btn btn-primary"
            onClick={() => { setShowInitialBalanceModal(true); setInitialError(''); }}
        >
            + Ўзида бор пул қўшиш
        </button>
      </div>

      {/* Balance cards */}
      <div className="stat-grid">
        <StatCard
          label="Умумий баланс"
          value={formatMoney(umumiyBalans)}
          icon={Wallet}
          color={umumiyBalans >= 0 ? "success" : "danger"}
          valueColor={umumiyBalans >= 0 ? "green" : "red"}
          sub="Тафсилот учун босинг"
          variant="hero"
          onClick={() => setShowBalanceBreakdown(true)}
        />
        <StatCard
          label="Нақд"
          value={formatMoney(balances.cash)}
          icon={Banknote}
          color={balances.cash >= 0 ? "success" : "danger"}
          valueColor={balances.cash >= 0 ? "green" : "red"}
        />
        <StatCard
          label="Перечисления"
          value={formatMoney(balances.bank_transfer)}
          icon={CreditCard}
          color={balances.bank_transfer >= 0 ? "info" : "danger"}
          valueColor={balances.bank_transfer >= 0 ? "blue" : "red"}
        />
      </div>

      <div className="section-label">Бугун ва Омбордаги ҳолат</div>
      <div className="stat-grid">
        <StatCard
          label="Омбордаги ёқилғи қиймати"
          value={formatMoney(data.inventory_value || 0)}
          icon={ShoppingCart}
          color="info"
        />
        <StatCard
          label="Бугунги тушум (Кирим)"
          value={formatMoney(today.income_amount)}
          sub={`${today.sale_count} та сотув`}
          icon={TrendingUp}
          color="success"
          valueColor="green"
        />
        <StatCard
          label="Бугунги харажат"
          value={formatMoney(today.expense_amount)}
          sub={`${today.expense_count} та операция`}
          icon={Receipt}
          color="danger"
          valueColor="red"
        />
      </div>

      {/* Debts */}
      <div className="section-label">Қарзлар</div>
      <div className="stat-grid">
        <StatCard
          label="Мижозлар қарзи (жами)"
          value={formatMoney(debts.customer_total)}
          icon={Users}
          color="warning"
          valueColor="green"
        />
        <StatCard
          label="Бизнинг қарзлар (жами)"
          value={formatMoney(debts.supplier_total)}
          icon={AlertCircle}
          color="danger"
          valueColor="red"
        />
      </div>

      {/* Recent movements */}
      <div className="card">
        <h2 className="card-title">Сўнгги пул ҳаракатлари</h2>
        {recent_movements.length === 0 ? (
          <p className="empty-message">Ҳозирча пул ҳаракатлари йўқ</p>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Сана</th>
                  <th>Тур</th>
                  <th>Тўлов тури</th>
                  <th>Йўналиш</th>
                  <th style={{ textAlign: 'right' }}>Сумма</th>
                  <th>Изоҳ</th>
                </tr>
              </thead>
              <tbody>
                {recent_movements.map((m) => (
                  <tr key={m.id}>
                    <td style={{ fontSize: '13px' }}>{new Date(m.date).toLocaleDateString('ru-RU')}</td>
                    <td style={{ fontSize: '13px' }}>{MOVEMENT_LABELS[m.movement_type] || m.movement_type}</td>
                    <td>{m.payment_type === 'cash' ? 'Нақд' : 'Перечисления'}</td>
                    <td>
                      <span
                        className={`badge ${m.direction === 'income' ? 'badge--income' : 'badge--outgoing'}`}
                      >
                        {m.direction === 'income' ? 'Кирим' : 'Чиқим'}
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
                    <h2>Ўзида бор пул қўшиш (Бошланғич баланс)</h2>
                    <button className="modal-close" onClick={() => setShowInitialBalanceModal(false)}>✕</button>
                </div>
                <div className="modal-body">
                    <div className="form-group">
                        <label>Сана</label>
                        <input type="date" className="form-control" value={initialForm.date} onChange={(e) => setInitialForm({ ...initialForm, date: e.target.value })} />
                    </div>
                    <div className="form-group">
                        <label>Тўлов тури</label>
                        <select className="form-control" value={initialForm.payment_type} onChange={(e) => setInitialForm({ ...initialForm, payment_type: e.target.value })}>
                            <option value="cash">Нақд</option>
                            <option value="bank_transfer">Перечисления</option>
                        </select>
                    </div>
                    <div className="form-group">
                        <label>Сумма (сўм)</label>
                        <input 
                            type="text" 
                            className="form-control" 
                            value={initialForm.amount} 
                            onChange={(e) => setInitialForm({ ...initialForm, amount: formatMoneyInput(e.target.value) })} 
                            placeholder="Масалан: 10 000 000" 
                        />
                    </div>
                    <div className="form-group">
                        <label>Изоҳ (ихтиёрий)</label>
                        <input type="text" className="form-control" value={initialForm.note} onChange={(e) => setInitialForm({ ...initialForm, note: e.target.value })} />
                    </div>
                    {initialError && <p style={{ color: 'var(--danger)', marginTop: '0.5rem' }}>{initialError}</p>}
                </div>
                <div className="modal-footer">
                    <button className="btn btn-secondary" onClick={() => setShowInitialBalanceModal(false)}>Бекор қилиш</button>
                    <button className="btn btn-primary" onClick={submitInitialBalance} disabled={initialLoading}>
                        {initialLoading ? 'Сақланмоқда...' : 'Сақлаш'}
                    </button>
                </div>
            </div>
        </div>
      )}

      {showBalanceBreakdown && (
        <div className="modal-overlay" onClick={() => setShowBalanceBreakdown(false)}>
            <div className="modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '400px' }}>
                <div className="modal-header">
                    <h2>Умумий баланс формуласи</h2>
                    <button className="modal-close" onClick={() => setShowBalanceBreakdown(false)}>✕</button>
                </div>
                <div className="modal-body" style={{ lineHeight: '2' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span>Нақд:</span>
                        <span style={{ color: balances.cash >= 0 ? 'var(--success)' : 'var(--danger)' }}>{formatMoney(balances.cash)}</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span>Перечисления:</span>
                        <span style={{ color: balances.bank_transfer >= 0 ? 'var(--success)' : 'var(--danger)' }}>{formatMoney(balances.bank_transfer)}</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span>Омбор қиймати:</span>
                        <span style={{ color: 'var(--success)' }}>+ {formatMoney(data.inventory_value || 0)}</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span>Мижозлар қарздорлиги:</span>
                        <span style={{ color: 'var(--success)' }}>+ {formatMoney(debts.customer_total)}</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border)', paddingBottom: '0.5rem', marginBottom: '0.5rem' }}>
                        <span>Бизнинг қарзлар:</span>
                        <span style={{ color: 'var(--danger)' }}>- {formatMoney(debts.supplier_total)}</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontWeight: 'bold', fontSize: '1.1rem' }}>
                        <span>Умумий баланс:</span>
                        <span style={{ color: umumiyBalans >= 0 ? 'var(--success)' : 'var(--danger)' }}>{formatMoney(umumiyBalans)}</span>
                    </div>
                </div>
                <div className="modal-footer">
                    <button className="btn btn-secondary" onClick={() => setShowBalanceBreakdown(false)}>Ёпиш</button>
                </div>
            </div>
        </div>
      )}
    </div>
  );
}

/* ── Reusable StatCard ── */
function StatCard({ label, value, sub, icon: Icon, color = 'accent', valueColor, onClick, variant }) {
  const valueClass = valueColor ? `stat-card-value stat-card-value--${valueColor}` : 'stat-card-value';
  return (
    <div className={`stat-card${variant ? ` stat-card--${variant}` : ''}`} onClick={onClick} style={{ cursor: onClick ? 'pointer' : 'default' }}>
      <div className={`stat-card-icon stat-card-icon--${color}`}>
        <Icon size={22} strokeWidth={2.2} />
      </div>
      <div className="stat-card-label">{label}</div>
      <div className={valueClass}>{value}</div>
      {sub && <div className="stat-card-sub" style={{ marginTop: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>{sub}</div>}
    </div>
  );
}