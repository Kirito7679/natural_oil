/**
 * Users — Foydalanuvchilar (admin access management) + Tizimni tozalash.
 */
import { useState, useEffect } from 'react';
import client from '../api/client';
import { Lock, AlertTriangle } from 'lucide-react';

const formatDate = (d) => d ? new Date(d).toLocaleDateString('ru-RU') : '—';

export default function Users() {
    const [users, setUsers] = useState([]);
    const [me, setMe] = useState(null);
    const [loading, setLoading] = useState(true);

    // Create user modal
    const [showCreate, setShowCreate] = useState(false);
    const [createForm, setCreateForm] = useState({ name: '', phone: '', password: '', confirm_password: '', is_active: true });
    const [createError, setCreateError] = useState('');
    const [createLoading, setCreateLoading] = useState(false);

    // Reset password modal
    const [resetUser, setResetUser] = useState(null);
    const [resetForm, setResetForm] = useState({ new_password: '', confirm_password: '' });
    const [resetError, setResetError] = useState('');
    const [resetLoading, setResetLoading] = useState(false);

    // Change own password modal
    const [showOwn, setShowOwn] = useState(false);
    const [ownForm, setOwnForm] = useState({ current_password: '', new_password: '', confirm_password: '' });
    const [ownError, setOwnError] = useState('');
    const [ownLoading, setOwnLoading] = useState(false);

    // Clear data modal
    const [showClear, setShowClear] = useState(false);
    const [clearForm, setClearForm] = useState({ password: '', confirm_text: '' });
    const [clearError, setClearError] = useState('');
    const [clearLoading, setClearLoading] = useState(false);

    useEffect(() => {
        fetchMe();
        fetchUsers();
    }, []);

    async function fetchMe() {
        try {
            const res = await client.get(`/auth/me`);
            setMe(res.data);
        } catch { setMe(null); }
    }

    async function fetchUsers() {
        setLoading(true);
        try {
            const res = await client.get(`/users`);
            setUsers(res.data);
        } catch { setUsers([]); }
        finally { setLoading(false); }
    }

    async function submitCreate() {
        setCreateError('');
        if (!createForm.name.trim()) return setCreateError('Ism kiriting.');
        if (!createForm.phone.trim()) return setCreateError('Login kiriting.');
        if (createForm.password.length < 6) return setCreateError("Parol kamida 6 ta belgidan iborat bo'lishi kerak.");
        if (createForm.password !== createForm.confirm_password) return setCreateError('Parollar mos emas.');

        setCreateLoading(true);
        try {
            await client.post(`/users`, createForm);
            setShowCreate(false);
            setCreateForm({ name: '', phone: '', password: '', confirm_password: '', is_active: true });
            fetchUsers();
        } catch (e) {
            setCreateError(e.response?.data?.detail || 'Xato yuz berdi.');
        } finally { setCreateLoading(false); }
    }

    async function toggleActive(user) {
        try {
            await client.patch(`/users/${user.id}`,
                { is_active: !user.is_active }
            );
            fetchUsers();
        } catch (e) {
            alert(e.response?.data?.detail || 'Xato yuz berdi.');
        }
    }

    function openReset(user) {
        setResetUser(user);
        setResetForm({ new_password: '', confirm_password: '' });
        setResetError('');
    }

    async function submitReset() {
        setResetError('');
        if (resetForm.new_password.length < 6) return setResetError("Parol kamida 6 ta belgidan iborat bo'lishi kerak.");
        if (resetForm.new_password !== resetForm.confirm_password) return setResetError('Parollar mos emas.');

        setResetLoading(true);
        try {
            await client.post(`/users/${resetUser.id}/reset-password`, resetForm);
            setResetUser(null);
            alert("Parol almashtirildi.");
        } catch (e) {
            setResetError(e.response?.data?.detail || 'Xato yuz berdi.');
        } finally { setResetLoading(false); }
    }

    async function submitOwn() {
        setOwnError('');
        if (!ownForm.current_password) return setOwnError('Joriy parol kiriting.');
        if (ownForm.new_password.length < 6) return setOwnError("Yangi parol kamida 6 ta belgidan iborat bo'lishi kerak.");
        if (ownForm.new_password !== ownForm.confirm_password) return setOwnError('Parollar mos emas.');

        setOwnLoading(true);
        try {
            await client.post(`/users/me/change-password`, ownForm);
            setShowOwn(false);
            setOwnForm({ current_password: '', new_password: '', confirm_password: '' });
            alert("Parol o'zgartirildi.");
        } catch (e) {
            setOwnError(e.response?.data?.detail || 'Xato yuz berdi.');
        } finally { setOwnLoading(false); }
    }

    // Clear data submit
    async function submitClear() {
        setClearError('');
        if (!clearForm.password) return setClearError('Parolni kiriting.');
        if (clearForm.confirm_text.trim().toUpperCase() !== 'TOZALASH') {
            return setClearError("Tasdiqlash uchun 'TOZALASH' so'zini yozing.");
        }

        setClearLoading(true);
        try {
            await client.post(`/admin/clear-data`, clearForm);
            setShowClear(false);
            setClearForm({ password: '', confirm_text: '' });
            alert("Tizim muvaffaqiyatli tozalandi! Sahifa qayta yuklanadi.");
            window.location.reload();
        } catch (e) {
            setClearError(e.response?.data?.detail || 'Xato yuz berdi.');
        } finally {
            setClearLoading(false);
        }
    }

    const isAdmin = me?.role === 'admin';

    return (
        <div className="page">
            <div className="page-header">
                <h1 className="page-title">Foydalanuvchilar</h1>
                <div className="action-buttons">
                    <button className="btn btn-secondary" onClick={() => { setShowOwn(true); setOwnError(''); }}>
                        <Lock size={14} strokeWidth={2.4} /> Mening parolim
                    </button>
                    <button className="btn btn--primary" onClick={() => { setShowCreate(true); setCreateError(''); }}>
                        + Yangi foydalanuvchi
                    </button>
                </div>
            </div>

            <div className="card">
                {loading ? (
                    <p className="empty-message">Yuklanmoqda...</p>
                ) : users.length === 0 ? (
                    <p className="empty-message">Foydalanuvchilar yo'q</p>
                ) : (
                    <div className="table-wrapper">
                        <table className="data-table">
                            <thead>
                                <tr>
                                    <th>ID</th>
                                    <th>Ism</th>
                                    <th>Login</th>
                                    <th>Status</th>
                                    <th>Yaratilgan sana</th>
                                    <th>Amallar</th>
                                </tr>
                            </thead>
                            <tbody>
                                {users.map((u) => (
                                    <tr key={u.id}>
                                        <td>#{u.id}</td>
                                        <td>
                                            <strong>{u.name}</strong>
                                            {me && me.id === u.id && (
                                                <span style={{ marginLeft: 8, fontSize: '0.75rem', color: 'var(--accent)', fontWeight: 700 }}>(siz)</span>
                                            )}
                                        </td>
                                        <td>{u.phone}</td>
                                        <td>
                                            <span className={`badge badge--${u.is_active ? 'active' : 'cancelled'}`}>
                                                {u.is_active ? 'Faol' : 'Nofaol'}
                                            </span>
                                        </td>
                                        <td style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>{formatDate(u.created_at)}</td>
                                        <td>
                                            <div className="action-buttons">
                                                <button className="btn btn--outline btn--sm" onClick={() => openReset(u)}>
                                                    Parolni almashtirish
                                                </button>
                                                <button
                                                    className={`btn btn--sm ${u.is_active ? 'btn--danger-outline' : 'btn--success-outline'}`}
                                                    onClick={() => toggleActive(u)}
                                                >
                                                    {u.is_active ? 'Nofaol qilish' : 'Faollashtirish'}
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>

            {/* DANGER ZONE — Tizimni tozalash (faqat admin) */}
            {isAdmin && (
                <div className="card" style={{ borderColor: 'var(--danger-border)', background: 'var(--danger-soft)' }}>
                    <div style={{ display: 'flex', alignItems: 'flex-start', gap: 16, flexWrap: 'wrap' }}>
                        <div style={{
                            width: 44, height: 44, borderRadius: 12,
                            background: 'var(--danger-soft)', color: 'var(--danger)',
                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                            flexShrink: 0, border: '1px solid var(--danger-border)'
                        }}>
                            <AlertTriangle size={22} strokeWidth={2.2} />
                        </div>
                        <div style={{ flex: 1, minWidth: 240 }}>
                            <h3 style={{ margin: 0, fontSize: 16, fontWeight: 800, color: 'var(--danger)', marginBottom: 4 }}>
                                Xavfli zona — Tizimni tozalash
                            </h3>
                            <p style={{ margin: 0, fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                                Barcha tranzaksiyalar, hamkorlar, mahsulotlar va xarajatlar o'chiriladi.
                                Faqat foydalanuvchilar (login) saqlanadi. Bu amalni qaytarib bo'lmaydi!
                            </p>
                        </div>
                        <button
                            className="btn btn--danger"
                            onClick={() => { setShowClear(true); setClearError(''); setClearForm({ password: '', confirm_text: '' }); }}
                        >
                            <AlertTriangle size={14} strokeWidth={2.4} /> Ma'lumotlarni tozalash
                        </button>
                    </div>
                </div>
            )}

            {/* Create user modal */}
            {showCreate && (
                <div className="modal-overlay" onClick={() => setShowCreate(false)}>
                    <div className="modal" onClick={(e) => e.stopPropagation()}>
                        <div className="modal-header">
                            <h2>Yangi foydalanuvchi</h2>
                            <button className="modal-close" onClick={() => setShowCreate(false)}>×</button>
                        </div>
                        <div className="modal-body">
                            <div className="form-group">
                                <label>Ism</label>
                                <input type="text" className="form-control" value={createForm.name} onChange={(e) => setCreateForm({ ...createForm, name: e.target.value })} />
                            </div>
                            <div className="form-group">
                                <label>Login</label>
                                <input type="text" className="form-control" value={createForm.phone} onChange={(e) => setCreateForm({ ...createForm, phone: e.target.value })} />
                            </div>
                            <div className="form-group">
                                <label>Parol</label>
                                <input type="password" className="form-control" value={createForm.password} onChange={(e) => setCreateForm({ ...createForm, password: e.target.value })} />
                            </div>
                            <div className="form-group">
                                <label>Parolni tasdiqlash</label>
                                <input type="password" className="form-control" value={createForm.confirm_password} onChange={(e) => setCreateForm({ ...createForm, confirm_password: e.target.value })} />
                            </div>
                            <div className="form-group">
                                <label>Status</label>
                                <select className="form-control" value={createForm.is_active ? 'true' : 'false'} onChange={(e) => setCreateForm({ ...createForm, is_active: e.target.value === 'true' })}>
                                    <option value="true">Faol</option>
                                    <option value="false">Nofaol</option>
                                </select>
                            </div>
                            {createError && <div className="alert alert--error">{createError}</div>}
                        </div>
                        <div className="modal-footer">
                            <button className="btn btn--outline" onClick={() => setShowCreate(false)}>Bekor qilish</button>
                            <button className="btn btn--primary" onClick={submitCreate} disabled={createLoading}>
                                {createLoading ? 'Saqlanmoqda...' : 'Saqlash'}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Reset password modal */}
            {resetUser && (
                <div className="modal-overlay" onClick={() => setResetUser(null)}>
                    <div className="modal" style={{ maxWidth: 460 }} onClick={(e) => e.stopPropagation()}>
                        <div className="modal-header">
                            <h2>Parolni almashtirish — {resetUser.name}</h2>
                            <button className="modal-close" onClick={() => setResetUser(null)}>×</button>
                        </div>
                        <div className="modal-body">
                            <div className="form-group">
                                <label>Yangi parol</label>
                                <input type="password" className="form-control" value={resetForm.new_password} onChange={(e) => setResetForm({ ...resetForm, new_password: e.target.value })} />
                            </div>
                            <div className="form-group">
                                <label>Parolni tasdiqlash</label>
                                <input type="password" className="form-control" value={resetForm.confirm_password} onChange={(e) => setResetForm({ ...resetForm, confirm_password: e.target.value })} />
                            </div>
                            {resetError && <div className="alert alert--error">{resetError}</div>}
                        </div>
                        <div className="modal-footer">
                            <button className="btn btn--outline" onClick={() => setResetUser(null)}>Bekor qilish</button>
                            <button className="btn btn--primary" onClick={submitReset} disabled={resetLoading}>
                                {resetLoading ? 'Saqlanmoqda...' : 'Saqlash'}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Change own password modal */}
            {showOwn && (
                <div className="modal-overlay" onClick={() => setShowOwn(false)}>
                    <div className="modal" style={{ maxWidth: 460 }} onClick={(e) => e.stopPropagation()}>
                        <div className="modal-header">
                            <h2>Mening parolimni o'zgartirish</h2>
                            <button className="modal-close" onClick={() => setShowOwn(false)}>×</button>
                        </div>
                        <div className="modal-body">
                            <div className="form-group">
                                <label>Joriy parol</label>
                                <input type="password" className="form-control" value={ownForm.current_password} onChange={(e) => setOwnForm({ ...ownForm, current_password: e.target.value })} />
                            </div>
                            <div className="form-group">
                                <label>Yangi parol</label>
                                <input type="password" className="form-control" value={ownForm.new_password} onChange={(e) => setOwnForm({ ...ownForm, new_password: e.target.value })} />
                            </div>
                            <div className="form-group">
                                <label>Yangi parolni tasdiqlash</label>
                                <input type="password" className="form-control" value={ownForm.confirm_password} onChange={(e) => setOwnForm({ ...ownForm, confirm_password: e.target.value })} />
                            </div>
                            {ownError && <div className="alert alert--error">{ownError}</div>}
                        </div>
                        <div className="modal-footer">
                            <button className="btn btn--outline" onClick={() => setShowOwn(false)}>Bekor qilish</button>
                            <button className="btn btn--primary" onClick={submitOwn} disabled={ownLoading}>
                                {ownLoading ? 'Saqlanmoqda...' : "Saqlash"}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* CLEAR DATA MODAL — premium danger */}
            {showClear && (
                <div className="modal-overlay" onClick={() => !clearLoading && setShowClear(false)}>
                    <div className="modal modal--danger" style={{ maxWidth: 520 }} onClick={(e) => e.stopPropagation()}>
                        <div className="modal-header">
                            <h2 style={{ color: 'var(--danger)', display: 'flex', alignItems: 'center', gap: 10 }}>
                                <AlertTriangle size={22} strokeWidth={2.4} />
                                Tizimni tozalash
                            </h2>
                            <button className="modal-close" onClick={() => !clearLoading && setShowClear(false)}>×</button>
                        </div>
                        <div className="modal-body">
                            <div className="modal-danger-banner">
                                <strong>DIQQAT!</strong> Bu amal qaytarib bo'lmaydi. Barcha quyidagi ma'lumotlar o'chiriladi:
                                <ul style={{ marginTop: 8, marginBottom: 0, paddingLeft: 22, fontWeight: 500 }}>
                                    <li>Barcha sotuvlar va xaridlar</li>
                                    <li>Barcha qarzlar va to'lovlar</li>
                                    <li>Barcha xarajatlar va kategoriyalar</li>
                                    <li>Barcha hamkorlar (mijoz va yetkazib beruvchilar)</li>
                                    <li>Barcha mahsulotlar</li>
                                    <li>Ombor partiyalari va balanslar</li>
                                </ul>
                                <div style={{ marginTop: 10, fontWeight: 700 }}>
                                    Faqat foydalanuvchilar (login) saqlanadi.
                                </div>
                            </div>

                            <div className="form-group">
                                <label>Sizning parolingiz *</label>
                                <input
                                    type="password"
                                    className="form-control"
                                    value={clearForm.password}
                                    onChange={(e) => setClearForm({ ...clearForm, password: e.target.value })}
                                    placeholder="Admin parolini kiriting"
                                    autoComplete="current-password"
                                />
                            </div>

                            <div className="form-group">
                                <label>Tasdiqlash uchun "TOZALASH" so'zini yozing *</label>
                                <input
                                    type="text"
                                    className="form-control"
                                    value={clearForm.confirm_text}
                                    onChange={(e) => setClearForm({ ...clearForm, confirm_text: e.target.value })}
                                    placeholder="TOZALASH"
                                    style={{ textTransform: 'uppercase', letterSpacing: '0.1em', fontWeight: 700 }}
                                />
                            </div>

                            {clearError && <div className="alert alert--error">{clearError}</div>}
                        </div>
                        <div className="modal-footer">
                            <button className="btn btn--outline" onClick={() => setShowClear(false)} disabled={clearLoading}>
                                Bekor qilish
                            </button>
                            <button
                                className="btn btn--danger"
                                onClick={submitClear}
                                disabled={clearLoading || clearForm.confirm_text.trim().toUpperCase() !== 'TOZALASH' || !clearForm.password}
                            >
                                {clearLoading ? 'Tozalanmoqda...' : 'Tozalash'}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}