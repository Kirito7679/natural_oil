/**
 * Expenses — Xarajatlar sahifasi.
 */
import { useState, useEffect } from 'react';
import client from '../api/client';
import { downloadExcel } from '../utils/excelDownload';

const formatMoney = (n) => new Intl.NumberFormat('uz-UZ').format(Math.round(n)) + ' so\'m';
const formatDate = (d) => d ? new Date(d).toLocaleDateString('ru-RU') : '—';
const today = () => new Date().toISOString().slice(0, 10);

export default function Expenses() {
    const [expenses, setExpenses] = useState([]);
    const [categories, setCategories] = useState([]);
    const [loading, setLoading] = useState(true);
    const [statusFilter, setStatusFilter] = useState('active');

    // Add expense modal
    const [showModal, setShowModal] = useState(false);
    const [form, setForm] = useState({ date: today(), category_id: '', amount: '', payment_type: 'cash', note: '' });
    const [formError, setFormError] = useState('');
    const [formLoading, setFormLoading] = useState(false);

    // Category modal
    const [showCatModal, setShowCatModal] = useState(false);
    const [catName, setCatName] = useState('');
    const [catError, setCatError] = useState('');
    const [catLoading, setCatLoading] = useState(false);

    useEffect(() => {
        fetchCategories();
        fetchExpenses();
    }, [statusFilter]);

    async function fetchCategories() {
        try {
            const res = await client.get(`/expenses/categories`);
            setCategories(res.data);
        } catch { setCategories([]); }
    }

    async function fetchExpenses() {
        setLoading(true);
        try {
            const params = { limit: 100 };
            if (statusFilter !== 'all') params.status = statusFilter;
            const res = await client.get(`/expenses`, { params });
            setExpenses(res.data.items);
        } catch { setExpenses([]); }
        finally { setLoading(false); }
    }

    async function submitExpense() {
        if (!form.category_id) return setFormError('Kategoriya tanlang.');
        if (!form.amount || parseFloat(form.amount) <= 0) return setFormError('Summa 0 dan katta bo\'lishi kerak.');
        setFormLoading(true);
        setFormError('');
        try {
            await client.post(`/expenses`, { ...form, amount: parseFloat(form.amount), category_id: parseInt(form.category_id) });
            setShowModal(false);
            setForm({ date: today(), category_id: '', amount: '', payment_type: 'cash', note: '' });
            fetchExpenses();
        } catch (e) {
            setFormError(e.response?.data?.detail || 'Xato yuz berdi.');
        } finally { setFormLoading(false); }
    }

    async function cancelExpense(id) {
        if (!window.confirm('Xarajatni bekor qilasizmi?')) return;
        try {
            await client.patch(`/expenses/${id}/cancel`, {});
            fetchExpenses();
        } catch (e) {
            alert(e.response?.data?.detail || 'Xato yuz berdi.');
        }
    }

    async function submitCategory() {
        if (!catName.trim()) return setCatError('Nom kiriting.');
        setCatLoading(true);
        setCatError('');
        try {
            await client.post(`/expenses/categories`, { name: catName.trim() });
            setCatName('');
            setShowCatModal(false);
            fetchCategories();
        } catch (e) {
            setCatError(e.response?.data?.detail || 'Xato yuz berdi.');
        } finally { setCatLoading(false); }
    }

    // Summary stats
    const activeExpenses = expenses.filter(e => e.status === 'active');
    const todayStr = today();
    const todayTotal = activeExpenses.filter(e => e.date === todayStr).reduce((s, e) => s + e.amount, 0);
    const monthTotal = activeExpenses.reduce((s, e) => s + e.amount, 0);
    const cashTotal = activeExpenses.filter(e => e.payment_type === 'cash').reduce((s, e) => s + e.amount, 0);
    const bankTotal = activeExpenses.filter(e => e.payment_type === 'bank_transfer').reduce((s, e) => s + e.amount, 0);

    return (
        <div className="page">
            <div className="page-header">
                <h1 className="page-title">Xarajatlar</h1>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                    <button
                        className="btn btn-secondary"
                        onClick={() => downloadExcel(
                            'expenses',
                            { status: statusFilter !== 'all' ? statusFilter : '' },
                            'natural_oil_expenses.xlsx'
                        )}
                    >
                        ⬇ Excel
                    </button>
                    <button className="btn btn-secondary" onClick={() => { setShowCatModal(true); setCatError(''); setCatName(''); }}>
                        + Kategoriya
                    </button>
                    <button className="btn btn-primary" onClick={() => { setShowModal(true); setFormError(''); }}>
                        + Xarajat qo'shish
                    </button>
                </div>
            </div>

            {/* Summary cards */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem', marginBottom: '1.5rem' }}>
                {[
                    { label: 'Bugungi xarajat', value: todayTotal, color: 'var(--accent)' },
                    { label: 'Jami xarajat', value: monthTotal, color: 'var(--danger)' },
                    { label: 'Naqd xarajat', value: cashTotal, color: 'var(--text-secondary)' },
                    { label: 'Perechisleniya', value: bankTotal, color: 'var(--text-secondary)' },
                ].map((c) => (
                    <div key={c.label} className="card" style={{ padding: '1rem' }}>
                        <div style={{ color: 'var(--text-secondary)', fontSize: '0.82rem', marginBottom: '0.4rem' }}>{c.label}</div>
                        <div style={{ fontSize: '1.3rem', fontWeight: 700, color: c.color }}>{formatMoney(c.value)}</div>
                    </div>
                ))}
            </div>

            {/* Filter */}
            <div className="card" style={{ marginBottom: '1rem', padding: '0.75rem 1rem', display: 'flex', gap: '0.5rem' }}>
                {['active', 'cancelled', 'all'].map((s) => (
                    <button key={s} onClick={() => setStatusFilter(s)} className={`btn ${statusFilter === s ? 'btn-primary' : 'btn-secondary'}`} style={{ fontSize: '0.85rem' }}>
                        {s === 'active' ? 'Faol' : s === 'cancelled' ? 'Bekor qilingan' : 'Barchasi'}
                    </button>
                ))}
            </div>

            {/* Table */}
            <div className="card">
                {loading ? (
                    <p className="empty-message">Yuklanmoqda...</p>
                ) : expenses.length === 0 ? (
                    <p className="empty-message">Xarajatlar yo'q</p>
                ) : (
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>Sana</th>
                                <th>Kategoriya</th>
                                <th>Summa</th>
                                <th>To'lov turi</th>
                                <th>Izoh</th>
                                <th>Holat</th>
                                <th>Amal</th>
                            </tr>
                        </thead>
                        <tbody>
                            {expenses.map((e) => (
                                <tr key={e.id}>
                                    <td>{formatDate(e.date)}</td>
                                    <td>{e.category?.name}</td>
                                    <td style={{ fontWeight: 600, color: 'var(--danger)' }}>{formatMoney(e.amount)}</td>
                                    <td>{e.payment_type === 'cash' ? 'Naqd' : 'Perechisleniya'}</td>
                                    <td style={{ color: 'var(--text-secondary)' }}>{e.note || '—'}</td>
                                    <td>
                                        <span style={{
                                            padding: '2px 8px', borderRadius: 4, fontSize: '0.8rem',
                                            background: e.status === 'active' ? 'var(--success)' : 'var(--text-secondary)',
                                            color: '#fff',
                                        }}>
                                            {e.status === 'active' ? 'Faol' : 'Bekor'}
                                        </span>
                                    </td>
                                    <td>
                                        {e.status === 'active' && (
                                            <button className="btn btn-secondary" style={{ fontSize: '0.8rem', padding: '3px 10px' }} onClick={() => cancelExpense(e.id)}>
                                                Bekor
                                            </button>
                                        )}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </div>

            {/* Add Expense Modal */}
            {showModal && (
                <div className="modal-overlay" onClick={() => setShowModal(false)}>
                    <div className="modal" onClick={(e) => e.stopPropagation()}>
                        <div className="modal-header">
                            <h2>Xarajat qo'shish</h2>
                            <button className="modal-close" onClick={() => setShowModal(false)}>✕</button>
                        </div>
                        <div className="modal-body">
                            <div className="form-group">
                                <label>Sana</label>
                                <input type="date" className="form-control" value={form.date} onChange={(e) => setForm({ ...form, date: e.target.value })} />
                            </div>
                            <div className="form-group">
                                <label>Kategoriya</label>
                                <select className="form-control" value={form.category_id} onChange={(e) => setForm({ ...form, category_id: e.target.value })}>
                                    <option value="">— Tanlang —</option>
                                    {categories.filter(c => c.is_active).map((c) => (
                                        <option key={c.id} value={c.id}>{c.name}</option>
                                    ))}
                                </select>
                            </div>
                            <div className="form-group">
                                <label>Summa (so'm)</label>
                                <input type="number" className="form-control" value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })} placeholder="0" />
                            </div>
                            <div className="form-group">
                                <label>To'lov turi</label>
                                <select className="form-control" value={form.payment_type} onChange={(e) => setForm({ ...form, payment_type: e.target.value })}>
                                    <option value="cash">Naqd</option>
                                    <option value="bank_transfer">Perechisleniya</option>
                                </select>
                            </div>
                            <div className="form-group">
                                <label>Izoh (ixtiyoriy)</label>
                                <input type="text" className="form-control" value={form.note} onChange={(e) => setForm({ ...form, note: e.target.value })} />
                            </div>
                            {formError && <p style={{ color: 'var(--danger)', marginTop: '0.5rem' }}>{formError}</p>}
                        </div>
                        <div className="modal-footer">
                            <button className="btn btn-secondary" onClick={() => setShowModal(false)}>Bekor qilish</button>
                            <button className="btn btn-primary" onClick={submitExpense} disabled={formLoading}>
                                {formLoading ? 'Saqlanmoqda...' : 'Saqlash'}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Add Category Modal */}
            {showCatModal && (
                <div className="modal-overlay" onClick={() => setShowCatModal(false)}>
                    <div className="modal" style={{ maxWidth: 400 }} onClick={(e) => e.stopPropagation()}>
                        <div className="modal-header">
                            <h2>Kategoriya qo'shish</h2>
                            <button className="modal-close" onClick={() => setShowCatModal(false)}>✕</button>
                        </div>
                        <div className="modal-body">
                            <div className="form-group">
                                <label>Kategoriya nomi</label>
                                <input type="text" className="form-control" value={catName} onChange={(e) => setCatName(e.target.value)} placeholder="Masalan: Arenda" />
                            </div>
                            {catError && <p style={{ color: 'var(--danger)' }}>{catError}</p>}

                            {/* Existing categories */}
                            <div style={{ marginTop: '1rem' }}>
                                <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '0.5rem' }}>Mavjud kategoriyalar:</p>
                                {categories.map((c) => (
                                    <div key={c.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '4px 0', borderBottom: '1px solid var(--border)' }}>
                                        <span style={{ color: c.is_active ? 'var(--text-primary)' : 'var(--text-secondary)' }}>{c.name}</span>
                                        <span style={{ fontSize: '0.75rem', color: c.is_active ? 'var(--success)' : 'var(--danger)' }}>
                                            {c.is_active ? 'Faol' : 'Nofaol'}
                                        </span>
                                    </div>
                                ))}
                            </div>
                        </div>
                        <div className="modal-footer">
                            <button className="btn btn-secondary" onClick={() => setShowCatModal(false)}>Yopish</button>
                            <button className="btn btn-primary" onClick={submitCategory} disabled={catLoading}>
                                {catLoading ? 'Saqlanmoqda...' : 'Saqlash'}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}