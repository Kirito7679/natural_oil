/**
 * Purchases (Prixod) page.
 * All UI labels in Uzbek.
 */
import { useState, useEffect } from 'react';
import { getPurchases, createPurchase, cancelPurchase } from '../api/purchases';
import { getProducts } from '../api/products';
import { getPartners } from '../api/partners';
import { formatDateTime, formatCurrency, formatNumber } from '../utils/formatters';
import { downloadExcel } from '../utils/excelDownload';
import Modal from '../components/Modal';

export default function Purchases() {
  const [purchases, setPurchases] = useState([]);
  const [products, setProducts] = useState([]);
  const [suppliers, setSuppliers] = useState([]);

  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const today = new Date().toISOString().split('T')[0];

  const emptyForm = {
    date: today,
    supplier_id: '',
    product_id: '',
    quantity_liters: '',
    calc_mode: 'price', // 'price' or 'total'
    purchase_price_per_liter: '',
    total_amount: '',
    paid_amount: '',
    payment_type: 'cash',
    note: ''
  };
  const [form, setForm] = useState(emptyForm);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [purchasesRes, productsRes, partnersRes] = await Promise.all([
        getPurchases(),
        getProducts(true),
        getPartners({ partner_type: 'supplier', active_only: true })
      ]);
      setPurchases(purchasesRes.data.items);
      setProducts(productsRes.data.items);
      // Both 'supplier' and 'both' are returned by backend
      setSuppliers(partnersRes.data.items.filter(p => p.is_active));
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, []);

  const openCreateModal = () => {
    setForm({ ...emptyForm, date: today });
    setError('');
    setModalOpen(true);
  };

  const updateField = (field, value) => {
    setForm(prev => {
      const next = { ...prev, [field]: value };

      // Auto-calculate live preview
      const qty = parseFloat(next.quantity_liters) || 0;

      if (next.calc_mode === 'price') {
        const price = parseFloat(next.purchase_price_per_liter) || 0;
        next._calculated_total = qty * price;
        next._calculated_price = price;
      } else {
        const total = parseFloat(next.total_amount) || 0;
        next._calculated_total = total;
        next._calculated_price = qty > 0 ? total / qty : 0;
      }

      const paid = parseFloat(next.paid_amount) || 0;
      next._calculated_debt = Math.max(0, next._calculated_total - paid);

      return next;
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!form.supplier_id || !form.product_id) {
      setError("Yetkazib beruvchi va mahsulotni tanlang");
      return;
    }

    setSaving(true);
    try {
      const payload = {
        date: form.date,
        supplier_id: parseInt(form.supplier_id),
        product_id: parseInt(form.product_id),
        quantity_liters: parseFloat(form.quantity_liters),
        note: form.note || null,
        payments: []
      };

      if (form.calc_mode === 'price') {
        payload.purchase_price_per_liter = parseFloat(form.purchase_price_per_liter);
      } else {
        payload.total_amount = parseFloat(form.total_amount);
      }

      const paidAmount = parseFloat(form.paid_amount) || 0;
      if (paidAmount > 0) {
        payload.payments.push({
          payment_type: form.payment_type,
          amount: paidAmount
        });
      }

      await createPurchase(payload);
      setModalOpen(false);
      fetchData();
    } catch (err) {
      setError(err.response?.data?.detail || "Xatolik yuz berdi");
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = async (id) => {
    if (!window.confirm("Haqiqatan ham bu prixodni bekor qilmoqchimisiz?")) return;

    try {
      await cancelPurchase(id);
      fetchData();
    } catch (err) {
      alert(err.response?.data?.detail || "Bekor qilishda xatolik");
    }
  };

  if (loading && purchases.length === 0) {
    return (
      <div className="page-loading">
        <div className="loading-spinner" />
      </div>
    );
  }

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Prixod (Xaridlar)</h1>
        <button
          className="btn btn-secondary"
          onClick={() => downloadExcel('purchases', {}, 'natural_oil_purchases.xlsx')}
        >
          ⬇ Excel
        </button>
        <button className="btn btn--primary" onClick={openCreateModal}>
          + Yangi prixod
        </button>
      </div>

      <div className="card">
        <div className="table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>Sana</th>
                <th>Yetkazib beruvchi</th>
                <th>Mahsulot</th>
                <th className="text-right">Miqdor (L)</th>
                <th className="text-right">Narx (UZS)</th>
                <th className="text-right">Jami summa</th>
                <th className="text-right">To'langan</th>
                <th className="text-right">Qarz</th>
                <th>Holat</th>
                <th>Amallar</th>
              </tr>
            </thead>
            <tbody>
              {purchases.length === 0 ? (
                <tr>
                  <td colSpan={10}>
                    <p className="empty-message">Prixodlar mavjud emas</p>
                  </td>
                </tr>
              ) : (
                purchases.map((p) => (
                  <tr key={p.id} className={p.status === 'cancelled' ? 'row-inactive' : ''}>
                    <td>{p.date}</td>
                    <td className="font-medium">{p.supplier.name}</td>
                    <td>{p.product.name}</td>
                    <td className="text-right">{formatNumber(p.quantity_liters)}</td>
                    <td className="text-right">{formatCurrency(p.purchase_price_per_liter)}</td>
                    <td className="text-right font-medium">{formatCurrency(p.total_amount)}</td>
                    <td className="text-right text-success">{formatCurrency(p.paid_amount)}</td>
                    <td className="text-right text-danger">{formatCurrency(p.debt_amount)}</td>
                    <td>
                      <span className={`badge badge--${p.status === 'active' ? 'active' : 'cancelled'}`}>
                        {p.status === 'active' ? 'Faol' : 'Bekor qilingan'}
                      </span>
                    </td>
                    <td>
                      {p.status === 'active' && (
                        <button
                          className="btn btn--sm btn--danger-outline"
                          onClick={() => handleCancel(p.id)}
                        >
                          Bekor qilish
                        </button>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Create Modal */}
      <Modal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        title="Yangi prixod"
        width={600}
      >
        <form onSubmit={handleSubmit}>
          {error && <div className="alert alert--error">{error}</div>}

          <div className="form-row">
            <div className="form-group">
              <label>Sana *</label>
              <input
                type="date"
                value={form.date}
                onChange={(e) => updateField('date', e.target.value)}
                required
              />
            </div>
            <div className="form-group">
              <label>Yetkazib beruvchi *</label>
              <select
                value={form.supplier_id}
                onChange={(e) => updateField('supplier_id', e.target.value)}
                required
              >
                <option value="">Tanlang...</option>
                {suppliers.map(s => (
                  <option key={s.id} value={s.id}>{s.name}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Mahsulot *</label>
              <select
                value={form.product_id}
                onChange={(e) => updateField('product_id', e.target.value)}
                required
              >
                <option value="">Tanlang...</option>
                {products.map(p => (
                  <option key={p.id} value={p.id}>{p.name}</option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label>Miqdor (Litr) *</label>
              <input
                type="number"
                min="0.01"
                step="0.01"
                value={form.quantity_liters}
                onChange={(e) => updateField('quantity_liters', e.target.value)}
                placeholder="0.00"
                required
              />
            </div>
          </div>

          <div className="calculation-box" style={{ background: 'var(--bg-input)', padding: '16px', borderRadius: '8px', marginBottom: '16px', border: '1px solid var(--border-color)' }}>
            <div className="form-group" style={{ marginBottom: '16px' }}>
              <label>Hisoblash usuli:</label>
              <div style={{ display: 'flex', gap: '16px' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontWeight: 'normal' }}>
                  <input
                    type="radio"
                    checked={form.calc_mode === 'price'}
                    onChange={() => updateField('calc_mode', 'price')}
                    style={{ width: 'auto' }}
                  />
                  1 litr narxini kiritish
                </label>
                <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontWeight: 'normal' }}>
                  <input
                    type="radio"
                    checked={form.calc_mode === 'total'}
                    onChange={() => updateField('calc_mode', 'total')}
                    style={{ width: 'auto' }}
                  />
                  Jami summani kiritish
                </label>
              </div>
            </div>

            {form.calc_mode === 'price' ? (
              <div className="form-group">
                <label>1 litr sotib olish narxi (UZS) *</label>
                <input
                  type="number"
                  min="0.01"
                  step="0.01"
                  value={form.purchase_price_per_liter}
                  onChange={(e) => updateField('purchase_price_per_liter', e.target.value)}
                  placeholder="0.00"
                  required
                />
                <div style={{ marginTop: '8px', fontSize: '13px', color: 'var(--text-secondary)' }}>
                  Jami summa: <strong style={{ color: 'var(--text-primary)' }}>{formatCurrency(form._calculated_total || 0)} UZS</strong>
                </div>
              </div>
            ) : (
              <div className="form-group">
                <label>Jami summa (UZS) *</label>
                <input
                  type="number"
                  min="0.01"
                  step="0.01"
                  value={form.total_amount}
                  onChange={(e) => updateField('total_amount', e.target.value)}
                  placeholder="0.00"
                  required
                />
                <div style={{ marginTop: '8px', fontSize: '13px', color: 'var(--text-secondary)' }}>
                  1 litr narxi: <strong style={{ color: 'var(--text-primary)' }}>{formatCurrency(form._calculated_price || 0)} UZS</strong>
                </div>
              </div>
            )}
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>To'langan summa (UZS)</label>
              <input
                type="number"
                min="0"
                step="0.01"
                value={form.paid_amount}
                onChange={(e) => updateField('paid_amount', e.target.value)}
                placeholder="0.00"
              />
              <div style={{ marginTop: '8px', fontSize: '13px', color: 'var(--text-secondary)' }}>
                Qarz: <strong className="text-danger">{formatCurrency(form._calculated_debt || 0)} UZS</strong>
              </div>
            </div>
            <div className="form-group">
              <label>To'lov turi</label>
              <select
                value={form.payment_type}
                onChange={(e) => updateField('payment_type', e.target.value)}
              >
                <option value="cash">Naqd (Cash)</option>
                <option value="bank_transfer">Perechisleniya (Bank)</option>
              </select>
            </div>
          </div>

          <div className="form-group">
            <label>Izoh</label>
            <input
              type="text"
              value={form.note}
              onChange={(e) => updateField('note', e.target.value)}
              placeholder="Qo'shimcha ma'lumot..."
            />
          </div>

          <div className="form-actions">
            <button
              type="button"
              className="btn btn--outline"
              onClick={() => setModalOpen(false)}
            >
              Bekor qilish
            </button>
            <button
              type="submit"
              className="btn btn--primary"
              disabled={saving}
            >
              {saving ? 'Saqlanmoqda...' : 'Saqlash'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}