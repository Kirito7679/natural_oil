/**
 * SupplierDebts — yetkazib beruvchilarga qarzlar sahifasi.
 */
import { useState, useEffect } from 'react';
import { Eye } from 'lucide-react';
import client from '../api/client';
import { downloadExcel } from '../utils/excelDownload';
import { parseMoneyInput, formatMoneyInput } from '../utils/formatters';
const formatMoney = (n) => new Intl.NumberFormat('uz-UZ').format(Math.round(n)) + ' so\'m';
const formatDate = (d) => (d ? new Date(d).toLocaleDateString('ru-RU') : '—');

export default function SupplierDebts() {
    const [debts, setDebts] = useState([]);
    const [total, setTotal] = useState(0);
    const [loading, setLoading] = useState(true);
    const [statusFilter, setStatusFilter] = useState('active');
    const [payModal, setPayModal] = useState(null);
    const [payForm, setPayForm] = useState({ amount: '', payment_type: 'cash', date: new Date().toISOString().slice(0, 10), note: '' });
    const [payError, setPayError] = useState('');
    const [payLoading, setPayLoading] = useState(false);

    const [partners, setPartners] = useState([]);
    const [manualModal, setManualModal] = useState(false);
    const [manualForm, setManualForm] = useState({
        partner_id: '', partner_name: '', partner_phone: '',
        product_name: '', quantity_liters: '', price_per_liter: '',
        total_amount: '', date: new Date().toISOString().slice(0, 10), note: ''
    });
    const [manualError, setManualError] = useState('');
    const [manualLoading, setManualLoading] = useState(false);

    const [detailModal, setDetailModal] = useState(null);
    const [detailLoading, setDetailLoading] = useState(false);

    async function openDetail(debt) {
        setDetailLoading(true);
        setDetailModal({ ...debt, payments: [] });
        try {
            const res = await client.get(`/debts/supplier/${debt.id}/detail`);
            setDetailModal(res.data);
        } catch (e) {
            console.error(e);
        } finally {
            setDetailLoading(false);
        }
    }

    useEffect(() => { 
        fetchDebts(); 
        fetchPartners();
    }, [statusFilter]);

    async function fetchPartners() {
        try {
            const res = await client.get('/partners', { params: { partner_type: 'supplier', active_only: true } });
            setPartners(res.data.items || []);
        } catch (e) {
            console.error(e);
        }
    }

    async function fetchDebts() {
        setLoading(true);
        try {
            const params = { limit: 100 };
            if (statusFilter !== 'all') params.status = statusFilter;
            const res = await client.get(`/debts/supplier`, { params });
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
        setPayForm({ amount: debt.remaining_amount.toFixed(0), payment_type: 'cash', date: new Date().toISOString().slice(0, 10), note: '' });
        setPayError('');
    }

    async function submitPay() {
        setPayLoading(true);
        setPayError('');
        try {
            await client.post(
                `/debts/supplier/${payModal.id}/pay`,
                { ...payForm, amount: parseMoneyInput(payForm.amount) }
            );
            setPayModal(null);
            fetchDebts();
        } catch (e) {
            setPayError(e.response?.data?.detail || 'Xato yuz berdi');
        } finally {
            setPayLoading(false);
        }
    }

    async function submitManualDebt() {
        setManualLoading(true);
        setManualError('');

        // Frontend validation
        const partnerId = manualForm.partner_id ? parseInt(manualForm.partner_id) : null;
        if (!partnerId && !manualForm.partner_name?.trim()) {
            setManualError('Yetkazib beruvchi tanlanmagan yoki nomi kiritilmagan');
            setManualLoading(false);
            return;
        }
        const totalAmount = parseMoneyInput(manualForm.total_amount);
        if (!totalAmount || totalAmount <= 0) {
            setManualError('Jami qarz summasi 0 dan katta bo\'lishi kerak');
            setManualLoading(false);
            return;
        }

        try {
            const payload = {
                partner_id: partnerId,
                partner_name: partnerId ? null : manualForm.partner_name.trim(),
                partner_phone: partnerId ? null : (manualForm.partner_phone?.trim() || null),
                product_name: manualForm.product_name || null,
                quantity_liters: manualForm.quantity_liters ? parseMoneyInput(manualForm.quantity_liters) : null,
                price_per_liter: manualForm.price_per_liter ? parseMoneyInput(manualForm.price_per_liter) : null,
                total_amount: totalAmount,
                date: manualForm.date,
                note: manualForm.note || null
            };
            console.log('[SupplierDebts] Manual debt payload:', JSON.stringify(payload));
            await client.post('/debts/supplier/manual', payload);
            setManualModal(false);
            setManualForm({
                partner_id: '', partner_name: '', partner_phone: '',
                product_name: '', quantity_liters: '', price_per_liter: '',
                total_amount: '', date: new Date().toISOString().slice(0, 10), note: ''
            });
            fetchDebts();
            fetchPartners();
        } catch (e) {
            setManualError(e.response?.data?.detail || 'Saqlashda xatolik yuz berdi');
        } finally {
            setManualLoading(false);
        }
    }

    useEffect(() => {
        if (manualForm.quantity_liters && manualForm.price_per_liter) {
            const qty = parseMoneyInput(manualForm.quantity_liters) || 0;
            const prc = parseMoneyInput(manualForm.price_per_liter) || 0;
            if (qty > 0 && prc > 0) {
                setManualForm(prev => ({ ...prev, total_amount: formatMoneyInput((qty * prc).toFixed(0)) }));
            }
        }
    }, [manualForm.quantity_liters, manualForm.price_per_liter]);

    const totalRemaining = debts.reduce((s, d) => s + d.remaining_amount, 0);

    return (
        <div className="page">
            <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <h1 className="page-title">Bizning qarzlar (yetkazib beruvchilar)</h1>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                    <button
                        className="btn btn-secondary"
                        onClick={() => downloadExcel(
                            'supplier-debts',
                            { status: statusFilter !== 'all' ? statusFilter : '' },
                            'natural_oil_supplier_debts.xlsx'
                        )}
                    >
                        ⬇ Excel
                    </button>
                    <button
                        className="btn btn-primary"
                        onClick={() => {
                            setManualModal(true);
                            setManualError('');
                        }}
                    >
                        + O'zida bor qarzni qo'shish
                    </button>
                </div>
            </div>

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

            <div className="card" style={{ marginBottom: '1rem', padding: '1rem', display: 'flex', gap: '0.5rem' }}>
                {['active', 'closed', 'all'].map((s) => (
                    <button key={s} onClick={() => setStatusFilter(s)} className={`btn ${statusFilter === s ? 'btn-primary' : 'btn-secondary'}`} style={{ fontSize: '0.85rem' }}>
                        {s === 'active' ? 'Faol' : s === 'closed' ? 'Yopilgan' : 'Barchasi'}
                    </button>
                ))}
            </div>

            <div className="card">
                {loading ? (
                    <p className="empty-message">Yuklanmoqda...</p>
                ) : debts.length === 0 ? (
                    <p className="empty-message">Qarzlar yo'q</p>
                ) : (
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>Yetkazib beruvchi</th>
                                <th>Xarid # / Qarz turi</th>
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
                                    <td><strong>{d.supplier?.name}</strong></td>
                                    <td>
                                        {d.is_manual ? (
                                            <span style={{ fontSize: '0.8rem', padding: '2px 6px', background: '#e0e7ff', color: '#3730a3', borderRadius: 4 }}>
                                                Eski qarz
                                            </span>
                                        ) : (
                                            `#${d.purchase_id}`
                                        )}
                                    </td>
                                    <td>{formatMoney(d.original_amount)}</td>
                                    <td style={{ color: 'var(--success)' }}>{formatMoney(d.paid_amount)}</td>
                                    <td style={{ color: 'var(--danger)', fontWeight: 600 }}>{formatMoney(d.remaining_amount)}</td>
                                    <td>
                                        <span style={{ padding: '2px 8px', borderRadius: 4, fontSize: '0.8rem', background: d.status === 'active' ? 'var(--danger)' : 'var(--success)', color: '#fff' }}>
                                            {d.status === 'active' ? 'Faol' : 'Yopilgan'}
                                        </span>
                                    </td>
                                    <td>{formatDate(d.last_payment_date)}</td>
                                    <td style={{ display: 'flex', gap: '0.35rem', alignItems: 'center' }}>
                                        {d.status === 'active' && (
                                            <button className="btn btn-primary" style={{ fontSize: '0.8rem', padding: '4px 10px' }} onClick={() => openPay(d)}>To'lash</button>
                                        )}
                                        <button
                                            className="row-action-btn"
                                            onClick={() => openDetail(d)}
                                            title="Tafsilot"
                                        >
                                            <Eye size={15} strokeWidth={2.2} />
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </div>

            {/* Manual Debt Modal */}
            {manualModal && (
                <div className="modal-overlay" onClick={() => setManualModal(false)}>
                    <div className="modal" onClick={(e) => e.stopPropagation()}>
                        <div className="modal-header">
                            <h2>O'zida bor qarzni qo'shish (Yetkazib beruvchi)</h2>
                            <button className="modal-close" onClick={() => setManualModal(false)}>✕</button>
                        </div>
                        <div className="modal-body">
                            <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '1rem' }}>
                                Bu qarz faqat eski qarzni ro'yxatga olish uchun. Ombor, xarid, xarajat yoki balansga ta'sir qilmaydi.
                            </p>
                            
                            <div className="form-group">
                                <label>Yetkazib beruvchini tanlash (yoki yangi kiriting)</label>
                                <select 
                                    className="form-control" 
                                    value={manualForm.partner_id} 
                                    onChange={(e) => setManualForm({ ...manualForm, partner_id: e.target.value })}
                                >
                                    <option value="">-- Yangi yetkazib beruvchi kiritish --</option>
                                    {partners.map(p => (
                                        <option key={p.id} value={p.id}>{p.name} ({p.phone || 'Tel raqamsiz'})</option>
                                    ))}
                                </select>
                            </div>

                            {!manualForm.partner_id && (
                                <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem' }}>
                                    <div style={{ flex: 1 }}>
                                        <label>Yetkazib beruvchi nomi</label>
                                        <input type="text" className="form-control" value={manualForm.partner_name} onChange={(e) => setManualForm({...manualForm, partner_name: e.target.value})} />
                                    </div>
                                    <div style={{ flex: 1 }}>
                                        <label>Telefon</label>
                                        <input type="text" className="form-control" value={manualForm.partner_phone} onChange={(e) => setManualForm({...manualForm, partner_phone: e.target.value})} />
                                    </div>
                                </div>
                            )}

                            <div className="form-group">
                                <label>Yoqilg'i nomi (ixtiyoriy)</label>
                                <input type="text" className="form-control" value={manualForm.product_name} onChange={(e) => setManualForm({...manualForm, product_name: e.target.value})} />
                            </div>

                            <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem' }}>
                                <div style={{ flex: 1 }}>
                                    <label>Hajmi (litr)</label>
                                    <input type="text" className="form-control" value={manualForm.quantity_liters} onChange={(e) => setManualForm({...manualForm, quantity_liters: formatMoneyInput(e.target.value)})} />
                                </div>
                                <div style={{ flex: 1 }}>
                                    <label>Litr narxi</label>
                                    <input type="text" className="form-control" value={manualForm.price_per_liter} onChange={(e) => setManualForm({...manualForm, price_per_liter: formatMoneyInput(e.target.value)})} />
                                </div>
                            </div>

                            <div className="form-group">
                                <label>Jami qarz summasi *</label>
                                <input type="text" className="form-control" required value={manualForm.total_amount} onChange={(e) => setManualForm({...manualForm, total_amount: formatMoneyInput(e.target.value)})} />
                            </div>

                            <div className="form-group">
                                <label>Sana</label>
                                <input type="date" className="form-control" value={manualForm.date} onChange={(e) => setManualForm({...manualForm, date: e.target.value})} />
                            </div>

                            <div className="form-group">
                                <label>Izoh</label>
                                <input type="text" className="form-control" value={manualForm.note} onChange={(e) => setManualForm({...manualForm, note: e.target.value})} />
                            </div>

                            {manualError && <p style={{ color: 'var(--danger)', marginTop: '0.5rem' }}>{manualError}</p>}
                        </div>
                        <div className="modal-footer">
                            <button className="btn btn-secondary" onClick={() => setManualModal(false)}>Bekor qilish</button>
                            <button className="btn btn-primary" onClick={submitManualDebt} disabled={manualLoading}>
                                {manualLoading ? 'Saqlanmoqda...' : 'Saqlash'}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {payModal && (
                <div className="modal-overlay" onClick={() => setPayModal(null)}>
                    <div className="modal" onClick={(e) => e.stopPropagation()}>
                        <div className="modal-header">
                            <h2>Qarz to'lash — {payModal.supplier?.name}</h2>
                            <button className="modal-close" onClick={() => setPayModal(null)}>✕</button>
                        </div>
                        <div className="modal-body">
                            <p style={{ marginBottom: '1rem', color: 'var(--text-secondary)' }}>
                                Qolgan qarz: <strong style={{ color: 'var(--danger)' }}>{formatMoney(payModal.remaining_amount)}</strong>
                            </p>
                            <div className="form-group">
                                <label>Summa (so'm)</label>
                                <input type="text" className="form-control" value={payForm.amount} onChange={(e) => setPayForm({ ...payForm, amount: formatMoneyInput(e.target.value) })} />
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
                            <button className="btn btn-primary" onClick={submitPay} disabled={payLoading}>{payLoading ? 'Saqlanmoqda...' : 'To\'lash'}</button>
                        </div>
                    </div>
                </div>
            )}

            {/* Debt Detail Modal */}
            {detailModal && (
                <div className="modal-overlay" onClick={() => setDetailModal(null)}>
                    <div className="modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '560px' }}>
                        <div className="modal-header">
                            <h2>Bizning qarz tafsilotlari</h2>
                            <button className="modal-close" onClick={() => setDetailModal(null)}>✕</button>
                        </div>
                        <div className="modal-body">
                            <div style={{ marginBottom: '1.25rem' }}>
                                <div style={{ fontWeight: 700, fontSize: '0.82rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.5rem' }}>Asosiy ma'lumotlar</div>
                                <SDetailRow label="Qarz turi" value={
                                    detailModal.is_manual ? '🏷 Eski qarz (qo\'lda kiritilgan)'
                                    : detailModal.purchase_id ? `📦 Prixoddan qarz — #${detailModal.purchase_id}`
                                    : 'Qarz'
                                } />
                                <SDetailRow label="Yetkazib beruvchi" value={detailModal.supplier?.name || '—'} bold />
                                <SDetailRow label="Telefon" value={detailModal.supplier?.phone || '—'} />
                                {(detailModal.manual_product_name || detailModal.purchase?.product?.name) && (
                                    <SDetailRow label="Mahsulot" value={detailModal.manual_product_name || detailModal.purchase?.product?.name} />
                                )}
                                {(detailModal.manual_quantity_liters || detailModal.purchase?.quantity_liters) && (
                                    <SDetailRow label="Miqdor" value={`${Number(detailModal.manual_quantity_liters || detailModal.purchase?.quantity_liters).toLocaleString('uz-UZ')} L`} />
                                )}
                                {(detailModal.manual_price_per_liter || detailModal.purchase?.purchase_price_per_liter) && (
                                    <SDetailRow label="Litr narxi" value={formatMoney(detailModal.manual_price_per_liter || detailModal.purchase?.purchase_price_per_liter)} />
                                )}
                                <SDetailRow label="Sana" value={formatDate(detailModal.manual_date || detailModal.purchase?.date || detailModal.created_at)} />
                                {detailModal.manual_note && <SDetailRow label="Izoh" value={detailModal.manual_note} />}
                            </div>

                            <div style={{ marginBottom: '1.25rem' }}>
                                <div style={{ fontWeight: 700, fontSize: '0.82rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.5rem' }}>Moliyaviy holat</div>
                                <SDetailRow label="Dastlabki qarz" value={formatMoney(detailModal.original_amount)} />
                                <SDetailRow label="To'langan" value={formatMoney(detailModal.paid_amount)} valueColor="var(--success)" />
                                <SDetailRow label="Qolgan qarz" value={formatMoney(detailModal.remaining_amount)} valueColor="var(--danger)" bold />
                                <SDetailRow label="Holat" value={
                                    detailModal.status === 'closed' ? '✅ Yopilgan'
                                    : detailModal.paid_amount > 0 ? '🕐 Qisman to\'langan'
                                    : '🔴 Faol'
                                } />
                            </div>

                            <div>
                                <div style={{ fontWeight: 700, fontSize: '0.82rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.5rem' }}>To'lovlar tarixi</div>
                                {detailLoading ? (
                                    <p style={{ color: 'var(--text-secondary)', fontSize: '0.88rem' }}>Yuklanmoqda...</p>
                                ) : !detailModal.payments || detailModal.payments.length === 0 ? (
                                    <p style={{ color: 'var(--text-secondary)', fontSize: '0.88rem', fontStyle: 'italic' }}>To'lovlar hali mavjud emas</p>
                                ) : (
                                    <table className="data-table" style={{ fontSize: '0.85rem' }}>
                                        <thead><tr>
                                            <th>Sana</th>
                                            <th>To'lov turi</th>
                                            <th className="text-right">Summa</th>
                                            <th>Izoh</th>
                                        </tr></thead>
                                        <tbody>
                                            {detailModal.payments.map(p => (
                                                <tr key={p.id}>
                                                    <td>{formatDate(p.date)}</td>
                                                    <td>{p.payment_type === 'cash' ? 'Naqd' : 'Perechisleniya'}</td>
                                                    <td className="text-right" style={{ color: 'var(--success)', fontWeight: 600 }}>{formatMoney(p.amount)}</td>
                                                    <td style={{ color: 'var(--text-secondary)' }}>{p.note || '—'}</td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                )}
                            </div>
                        </div>
                        <div className="modal-footer">
                            <button className="btn btn-secondary" onClick={() => setDetailModal(null)}>Yopish</button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

function SDetailRow({ label, value, valueColor, bold }) {
    return (
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', padding: '5px 0', borderBottom: '1px solid var(--border)' }}>
            <span style={{ color: 'var(--text-secondary)', fontSize: '0.88rem', flexShrink: 0, marginRight: '1rem' }}>{label}</span>
            <span style={{ fontWeight: bold ? 700 : 500, fontSize: '0.88rem', color: valueColor || 'inherit', textAlign: 'right' }}>{value}</span>
        </div>
    );
}