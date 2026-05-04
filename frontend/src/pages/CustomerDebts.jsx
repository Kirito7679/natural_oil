/**
 * CustomerDebts — mijozlar qarzdorligi sahifasi.
 */
import { useState, useEffect } from 'react';
import axios from 'axios';
import { downloadExcel } from '../utils/excelDownload';

const API = 'http://localhost:8000/api';

function getToken() {
    return localStorage.getItem('token');
}

function headers() {
    return { Authorization: `Bearer ${getToken()}` };
}

const formatMoney = (n) =>
    new Intl.NumberFormat('uz-UZ').format(Math.round(n)) + ' so\'m';

const formatDate = (d) => (d ? new Date(d).toLocaleDateString('ru-RU') : '—');

export default function CustomerDebts() {
    const [debts, setDebts] = useState([]);
    const [total, setTotal] = useState(0);
    const [loading, setLoading] = useState(true);
    const [statusFilter, setStatusFilter] = useState('active');
    const [payModal, setPayModal] = useState(null); // debt object
    const [payForm, setPayForm] = useState({ amount: '', payment_type: 'cash', date: new Date().toISOString().slice(0, 10), note: '' });
    const [payError, setPayError] = useState('');
    const [payLoading, setPayLoading] = useState(false);

    useEffect(() => {
        fetchDebts();
    }, [statusFilter]);

    async function fetchDebts() {
        setLoading(true);
        try {
            const params = { limit: 100 };
            if (statusFilter !== 'all') params.status = statusFilter;
            const res = await axios.get(`${API}/debts/customer`, { headers: headers(), params });
            setDebts(res.data.items);
            setTotal(res.data.total);
        } catch {
            setDebts([]);
        } finally {
            setLoading(false);
        }
    }

    function openPay(debt) {
        setPayModal(debt);
        setPayForm({
            amount: debt.remaining_amount.toFixed(0),
            payment_type: 'cash',
            date: new Date().toISOString().slice(0, 10),
            note: '',
        });
        setPayError('');
    }

    async function submitPay() {
        setPayLoading(true);
        setPayError('');
        try {
            await axios.post(
                `${API}/debts/customer/${payModal.id}/pay`,
                { ...payForm, amount: parseFloat(payForm.amount) },
                { headers: headers() }
            );
            setPayModal(null);
            fetchDebts();
        } catch (e) {
            setPayError(e.response?.data?.detail || 'Xato yuz berdi');
        } finally {
            setPayLoading(false);
        }
    }

    const totalRemaining = debts.reduce((s, d) => s + d.remaining_amount, 0);

    return (
        <div className="page">
            <div className="page-header">
                <h1 className="page-title">Mijozlar qarzdorligi</h1>
                <button
                    className="btn btn-secondary"
                    onClick={() => downloadExcel(
                        'customer-debts',
                        { status: statusFilter !== 'all' ? statusFilter : '' },
                        'natural_oil_customer_debts.xlsx'
                    )}
                >
                    ⬇ Excel
                </button>
            </div>

            {/* Summary */}
            <div style={{ display: 'flex', gap: '1rem', marginBottom: '1.5rem' }}>
                <div className="card" style={{ flex: 1, padding: '1rem' }}>
                    <div style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>Jami qarzlar</div>
                    <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--accent)' }}>{total} ta</div>
                </div>
                <div className="card" style={{ flex: 2, padding: '1rem' }}>
                    <div style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>Jami qolgan qarz</div>
                    <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--danger)' }}>{formatMoney(totalRemaining)}</div>
                </div>
            </div>

            {/* Filter */}
            <div className="card" style={{ marginBottom: '1rem', padding: '1rem', display: 'flex', gap: '0.5rem' }}>
                {['active', 'closed', 'all'].map((s) => (
                    <button
                        key={s}
                        onClick={() => setStatusFilter(s)}
                        className={`btn ${statusFilter === s ? 'btn-primary' : 'btn-secondary'}`}
                        style={{ fontSize: '0.85rem' }}
                    >
                        {s === 'active' ? 'Faol' : s === 'closed' ? 'Yopilgan' : 'Barchasi'}
                    </button>
                ))}
            </div>

            {/* Table */}
            <div className="card">
                {loading ? (
                    <p className="empty-message">Yuklanmoqda...</p>
                ) : debts.length === 0 ? (
                    <p className="empty-message">Qarzlar yo'q</p>
                ) : (
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>Mijoz</th>
                                <th>Sotuv #</th>
                                <th>Dastlabki</th>
                                <th>To'langan</th>
                                <th>Qolgan</th>
                                <th>Holat</th>
                                <th>Oxirgi to'lov</th>
                                <th>Amal</th>
                            </tr>
                        </thead>
                        <tbody>
                            {debts.map((d) => (
                                <tr key={d.id}>
                                    <td><strong>{d.customer?.name}</strong></td>
                                    <td>#{d.sale_id}</td>
                                    <td>{formatMoney(d.original_amount)}</td>
                                    <td style={{ color: 'var(--success)' }}>{formatMoney(d.paid_amount)}</td>
                                    <td style={{ color: 'var(--danger)', fontWeight: 600 }}>{formatMoney(d.remaining_amount)}</td>
                                    <td>
                                        <span style={{
                                            padding: '2px 8px',
                                            borderRadius: 4,
                                            fontSize: '0.8rem',
                                            background: d.status === 'active' ? 'var(--danger)' : 'var(--success)',
                                            color: '#fff',
                                        }}>
                                            {d.status === 'active' ? 'Faol' : 'Yopilgan'}
                                        </span>
                                    </td>
                                    <td>{formatDate(d.last_payment_date)}</td>
                                    <td>
                                        {d.status === 'active' && (
                                            <button className="btn btn-primary" style={{ fontSize: '0.8rem', padding: '4px 10px' }} onClick={() => openPay(d)}>
                                                To'lash
                                            </button>
                                        )}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </div>

            {/* Pay Modal */}
            {payModal && (
                <div className="modal-overlay" onClick={() => setPayModal(null)}>
                    <div className="modal" onClick={(e) => e.stopPropagation()}>
                        <div className="modal-header">
                            <h2>Qarz to'lash — {payModal.customer?.name}</h2>
                            <button className="modal-close" onClick={() => setPayModal(null)}>✕</button>
                        </div>
                        <div className="modal-body">
                            <p style={{ marginBottom: '1rem', color: 'var(--text-secondary)' }}>
                                Qolgan qarz: <strong style={{ color: 'var(--danger)' }}>{formatMoney(payModal.remaining_amount)}</strong>
                            </p>
                            <div className="form-group">
                                <label>Summa (so'm)</label>
                                <input
                                    type="number"
                                    className="form-control"
                                    value={payForm.amount}
                                    onChange={(e) => setPayForm({ ...payForm, amount: e.target.value })}
                                    max={payModal.remaining_amount}
                                />
                            </div>
                            <div className="form-group">
                                <label>To'lov turi</label>
                                <select className="form-control" value={payForm.payment_type} onChange={(e) => setPayForm({ ...payForm, payment_type: e.target.value })}>
                                    <option value="cash">Naqd</option>
                                    <option value="bank_transfer">Perechisleniya</option>
                                </select>
                            </div>
                            <div className="form-group">
                                <label>Sana</label>
                                <input type="date" className="form-control" value={payForm.date} onChange={(e) => setPayForm({ ...payForm, date: e.target.value })} />
                            </div>
                            <div className="form-group">
                                <label>Izoh (ixtiyoriy)</label>
                                <input type="text" className="form-control" value={payForm.note} onChange={(e) => setPayForm({ ...payForm, note: e.target.value })} />
                            </div>
                            {payError && <p style={{ color: 'var(--danger)', marginTop: '0.5rem' }}>{payError}</p>}
                        </div>
                        <div className="modal-footer">
                            <button className="btn btn-secondary" onClick={() => setPayModal(null)}>Bekor qilish</button>
                            <button className="btn btn-primary" onClick={submitPay} disabled={payLoading}>
                                {payLoading ? 'Saqlanmoqda...' : 'To\'lash'}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}