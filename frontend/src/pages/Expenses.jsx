/**
 * Expenses — Xarajatlar sahifasi.
 */
import { useState, useEffect } from 'react';
import client from '../api/client';
import { downloadExcel } from '../utils/excelDownload';

const formatMoney = (n) => new Intl.NumberFormat('uz-UZ').format(Math.round(n)) + ' сўм';
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
    const [editingId, setEditingId] = useState(null);
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
        if (!form.category_id) return setFormError('Категория танланг.');
        if (!form.amount || parseFloat(form.amount) <= 0) return setFormError('Сумма 0 дан катта бўлиши керак.');
        setFormLoading(true);
        setFormError('');
        try {
            const payload = { ...form, amount: parseFloat(form.amount), category_id: parseInt(form.category_id) };
            if (editingId) {
                await client.put(`/expenses/${editingId}`, payload);
            } else {
                await client.post(`/expenses`, payload);
            }
            setShowModal(false);
            setEditingId(null);
            setForm({ date: today(), category_id: '', amount: '', payment_type: 'cash', note: '' });
            fetchExpenses();
        } catch (e) {
            setFormError(e.response?.data?.detail || 'Хато юз берди.');
        } finally { setFormLoading(false); }
    }

    // Tuzatish: eski xarajat bekor qilinib, yangisi yoziladi (bitta tranzaksiyada).
    function openEdit(e) {
        setForm({
            date: e.date,
            category_id: String(e.category_id ?? e.category?.id ?? ''),
            amount: String(e.amount ?? ''),
            payment_type: e.payment_type || 'cash',
            note: e.note || ''
        });
        setEditingId(e.id);
        setFormError('');
        setShowModal(true);
    }

    async function cancelExpense(id) {
        if (!window.confirm('Харажатни бекор қиласизми?')) return;
        try {
            await client.patch(`/expenses/${id}/cancel`, {});
            fetchExpenses();
        } catch (e) {
            alert(e.response?.data?.detail || 'Хато юз берди.');
        }
    }

    async function submitCategory() {
        if (!catName.trim()) return setCatError('Ном киритинг.');
        setCatLoading(true);
        setCatError('');
        try {
            await client.post(`/expenses/categories`, { name: catName.trim() });
            setCatName('');
            setShowCatModal(false);
            fetchCategories();
        } catch (e) {
            setCatError(e.response?.data?.detail || 'Хато юз берди.');
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
                <h1 className="page-title">Харажатлар</h1>
                <div className="action-buttons">
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
                        + Категория
                    </button>
                    <button className="btn btn-primary" onClick={() => { setEditingId(null); setForm({ date: today(), category_id: '', amount: '', payment_type: 'cash', note: '' }); setShowModal(true); setFormError(''); }}>
                        + Харажат қўшиш
                    </button>
                </div>
            </div>

            {/* Summary cards */}
            <div className="kpi-grid">
                {[
                    { label: 'Бугунги харажат', value: todayTotal, color: 'var(--accent)' },
                    { label: 'Жами харажат', value: monthTotal, color: 'var(--danger)' },
                    { label: 'Нақд харажат', value: cashTotal, color: 'var(--text-secondary)' },
                    { label: 'Перечисления', value: bankTotal, color: 'var(--text-secondary)' },
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
                        {s === 'active' ? 'Фаол' : s === 'cancelled' ? 'Бекор қилинган' : 'Барчаси'}
                    </button>
                ))}
            </div>

            {/* Table */}
            <div className="card">
                {loading ? (
                    <p className="empty-message">Юкланмоқда...</p>
                ) : expenses.length === 0 ? (
                    <p className="empty-message">Харажатлар йўқ</p>
                ) : (
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>Сана</th>
                                <th>Категория</th>
                                <th>Сумма</th>
                                <th>Тўлов тури</th>
                                <th>Изоҳ</th>
                                <th>Ҳолат</th>
                                <th>Амал</th>
                            </tr>
                        </thead>
                        <tbody>
                            {expenses.map((e) => (
                                <tr key={e.id}>
                                    <td>{formatDate(e.date)}</td>
                                    <td>{e.category?.name}</td>
                                    <td style={{ fontWeight: 600, color: 'var(--danger)' }}>{formatMoney(e.amount)}</td>
                                    <td>{e.payment_type === 'cash' ? 'Нақд' : 'Перечисления'}</td>
                                    <td style={{ color: 'var(--text-secondary)' }}>{e.note || '—'}</td>
                                    <td>
                                        <span style={{
                                            padding: '2px 8px', borderRadius: 4, fontSize: '0.8rem',
                                            background: e.status === 'active' ? 'var(--success)' : 'var(--text-secondary)',
                                            color: '#fff',
                                        }}>
                                            {e.status === 'active' ? 'Фаол' : 'Бекор'}
                                        </span>
                                    </td>
                                    <td>
                                        {e.status === 'active' && (
                                            <>
                                                <button className="btn btn-secondary" style={{ fontSize: '0.8rem', padding: '3px 10px', marginRight: '0.35rem' }} onClick={() => openEdit(e)}>
                                                    Тўғрилаш
                                                </button>
                                                <button className="btn btn-secondary" style={{ fontSize: '0.8rem', padding: '3px 10px' }} onClick={() => cancelExpense(e.id)}>
                                                    Бекор
                                                </button>
                                            </>
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
                            <h2>Харажат қўшиш</h2>
                            <button className="modal-close" onClick={() => setShowModal(false)}>✕</button>
                        </div>
                        <div className="modal-body">
                            <div className="form-group">
                                <label>Сана</label>
                                <input type="date" className="form-control" value={form.date} onChange={(e) => setForm({ ...form, date: e.target.value })} />
                            </div>
                            <div className="form-group">
                                <label>Категория</label>
                                <select className="form-control" value={form.category_id} onChange={(e) => setForm({ ...form, category_id: e.target.value })}>
                                    <option value="">— Танланг —</option>
                                    {categories.filter(c => c.is_active).map((c) => (
                                        <option key={c.id} value={c.id}>{c.name}</option>
                                    ))}
                                </select>
                            </div>
                            <div className="form-group">
                                <label>Сумма (сўм)</label>
                                <input type="number" className="form-control" value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })} placeholder="0" />
                            </div>
                            <div className="form-group">
                                <label>Тўлов тури</label>
                                <select className="form-control" value={form.payment_type} onChange={(e) => setForm({ ...form, payment_type: e.target.value })}>
                                    <option value="cash">Нақд</option>
                                    <option value="bank_transfer">Перечисления</option>
                                </select>
                            </div>
                            <div className="form-group">
                                <label>Изоҳ (ихтиёрий)</label>
                                <input type="text" className="form-control" value={form.note} onChange={(e) => setForm({ ...form, note: e.target.value })} />
                            </div>
                            {formError && <p style={{ color: 'var(--danger)', marginTop: '0.5rem' }}>{formError}</p>}
                        </div>
                        <div className="modal-footer">
                            <button className="btn btn-secondary" onClick={() => setShowModal(false)}>Бекор қилиш</button>
                            <button className="btn btn-primary" onClick={submitExpense} disabled={formLoading}>
                                {formLoading ? 'Сақланмоқда...' : 'Сақлаш'}
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
                            <h2>Категория қўшиш</h2>
                            <button className="modal-close" onClick={() => setShowCatModal(false)}>✕</button>
                        </div>
                        <div className="modal-body">
                            <div className="form-group">
                                <label>Категория номи</label>
                                <input type="text" className="form-control" value={catName} onChange={(e) => setCatName(e.target.value)} placeholder="Масалан: Аренда" />
                            </div>
                            {catError && <p style={{ color: 'var(--danger)' }}>{catError}</p>}

                            {/* Existing categories */}
                            <div style={{ marginTop: '1rem' }}>
                                <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '0.5rem' }}>Мавжуд категориялар:</p>
                                {categories.map((c) => (
                                    <div key={c.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '4px 0', borderBottom: '1px solid var(--border)' }}>
                                        <span style={{ color: c.is_active ? 'var(--text-primary)' : 'var(--text-secondary)' }}>{c.name}</span>
                                        <span style={{ fontSize: '0.75rem', color: c.is_active ? 'var(--success)' : 'var(--danger)' }}>
                                            {c.is_active ? 'Фаол' : 'Нофаол'}
                                        </span>
                                    </div>
                                ))}
                            </div>
                        </div>
                        <div className="modal-footer">
                            <button className="btn btn-secondary" onClick={() => setShowCatModal(false)}>Ёпиш</button>
                            <button className="btn btn-primary" onClick={submitCategory} disabled={catLoading}>
                                {catLoading ? 'Сақланмоқда...' : 'Сақлаш'}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}