/**
 * Purchases (Prixod) page.
 * All UI labels in Uzbek.
 */
import { useState, useEffect } from 'react';
import client from '../api/client';
import { getPurchases, createPurchase, cancelPurchase } from '../api/purchases';
import { getProducts } from '../api/products';
import { getPartners } from '../api/partners';
import PartnerPicker from '../components/PartnerPicker';
import { formatDateTime, formatCurrency, formatNumber, formatMoneyInput, parseMoneyInput } from '../utils/formatters';
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

  const [initialStockOpen, setInitialStockOpen] = useState(false);
  const [initialForm, setInitialForm] = useState({ product_id: '', quantity_liters: '', purchase_price_per_liter: '', note: '' });
  const [initialLoading, setInitialLoading] = useState(false);
  const [initialError, setInitialError] = useState('');

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
      const qty = parseMoneyInput(next.quantity_liters) || 0;

      if (next.calc_mode === 'price') {
        const price = parseMoneyInput(next.purchase_price_per_liter) || 0;
        next._calculated_total = qty * price;
        next._calculated_price = price;
      } else {
        const total = parseMoneyInput(next.total_amount) || 0;
        next._calculated_total = total;
        next._calculated_price = qty > 0 ? total / qty : 0;
      }

      const paid = parseMoneyInput(next.paid_amount) || 0;
      next._calculated_debt = Math.max(0, next._calculated_total - paid);

      return next;
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!form.supplier_id || !form.product_id) {
      setError("Етказиб берувчи ва маҳсулотни танланг");
      return;
    }

    setSaving(true);
    try {
      const payload = {
        date: form.date,
        supplier_id: parseInt(form.supplier_id),
        product_id: parseInt(form.product_id),
        quantity_liters: parseMoneyInput(form.quantity_liters),
        note: form.note || null,
        payments: []
      };

      if (form.calc_mode === 'price') {
        payload.purchase_price_per_liter = parseMoneyInput(form.purchase_price_per_liter);
      } else {
        payload.total_amount = parseMoneyInput(form.total_amount);
      }

      const paidAmount = parseMoneyInput(form.paid_amount) || 0;
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
      setError(err.response?.data?.detail || "Хатолик юз берди");
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = async (id) => {
    if (!window.confirm("Ҳақиқатан ҳам бу приходни бекор қилмоқчимисиз?")) return;

    try {
      await cancelPurchase(id);
      fetchData();
    } catch (err) {
      alert(err.response?.data?.detail || "Бекор қилишда хатолик");
    }
  };

  const handleInitialStockSubmit = async (e) => {
    e.preventDefault();
    if (!initialForm.product_id) return setInitialError("Маҳсулот танланг");
    
    const qty = parseMoneyInput(initialForm.quantity_liters);
    const price = parseMoneyInput(initialForm.purchase_price_per_liter);
    
    if (!qty || qty <= 0) return setInitialError("Миқдорни тўғри киритинг");
    if (!price || price <= 0) return setInitialError("Нархни тўғри киритинг");

    setInitialLoading(true);
    setInitialError('');
    try {
      await client.post('/purchases/initial-stock', {
        date: today,
        product_id: parseInt(initialForm.product_id),
        quantity_liters: qty,
        purchase_price_per_liter: price,
        note: initialForm.note || null
      });
      setInitialStockOpen(false);
      setInitialForm({ product_id: '', quantity_liters: '', purchase_price_per_liter: '', note: '' });
      fetchData();
    } catch (err) {
      setInitialError(err.response?.data?.detail || "Хатолик юз берди");
    } finally {
      setInitialLoading(false);
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
        <h1 className="page-title">Приход (Харидлар)</h1>
        <button
          className="btn btn-secondary"
          onClick={() => downloadExcel('purchases', {}, 'natural_oil_purchases.xlsx')}
        >
          ⬇ Excel
        </button>
        <button className="btn btn-secondary" onClick={() => setInitialStockOpen(true)}>
          + Ўзида бор қолдиқ
        </button>
        <button className="btn btn--primary" onClick={openCreateModal}>
          + Янги приход
        </button>
      </div>

      <div className="card">
        <div className="table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>Сана</th>
                <th>Етказиб берувчи</th>
                <th>Маҳсулот</th>
                <th className="text-right">Миқдор (Л)</th>
                <th className="text-right">Нарх (UZS)</th>
                <th className="text-right">Жами сумма</th>
                <th className="text-right">Тўланган</th>
                <th className="text-right">Қарз</th>
                <th>Ҳолат</th>
                <th>Амаллар</th>
              </tr>
            </thead>
            <tbody>
              {purchases.length === 0 ? (
                <tr>
                  <td colSpan={10}>
                    <p className="empty-message">Приходлар мавжуд эмас</p>
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
                        {p.status === 'active' ? 'Фаол' : 'Бекор қилинган'}
                      </span>
                    </td>
                    <td>
                      {p.status === 'active' && (
                        <button
                          className="btn btn--sm btn--danger-outline"
                          onClick={() => handleCancel(p.id)}
                        >
                          Бекор қилиш
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
        title="Янги приход"
        width={600}
      >
        <form onSubmit={handleSubmit}>
          {error && <div className="alert alert--error">{error}</div>}

          <div className="form-row">
            <div className="form-group">
              <label>Сана *</label>
              <input
                type="date"
                value={form.date}
                onChange={(e) => updateField('date', e.target.value)}
                required
              />
            </div>
            <PartnerPicker
              type="supplier"
              label="Етказиб берувчи"
              partners={suppliers}
              onPartnersChange={setSuppliers}
              value={form.supplier_id}
              onChange={(v) => updateField('supplier_id', v)}
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Маҳсулот *</label>
              <select
                value={form.product_id}
                onChange={(e) => updateField('product_id', e.target.value)}
                required
              >
                <option value="">Танланг...</option>
                {products.map(p => (
                  <option key={p.id} value={p.id}>{p.name}</option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label>Миқдор (Литр) *</label>
              <input
                type="text"
                value={form.quantity_liters}
                onChange={(e) => updateField('quantity_liters', formatMoneyInput(e.target.value))}
                placeholder="0.00"
                required
              />
            </div>
          </div>

          <div className="calculation-box" style={{ background: 'var(--bg-input)', padding: '16px', borderRadius: '8px', marginBottom: '16px', border: '1px solid var(--border-color)' }}>
            <div className="form-group" style={{ marginBottom: '16px' }}>
              <label>Ҳисоблаш усули:</label>
              <div style={{ display: 'flex', gap: '16px' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontWeight: 'normal' }}>
                  <input
                    type="radio"
                    checked={form.calc_mode === 'price'}
                    onChange={() => updateField('calc_mode', 'price')}
                    style={{ width: 'auto' }}
                  />
                  1 литр нархини киритиш
                </label>
                <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontWeight: 'normal' }}>
                  <input
                    type="radio"
                    checked={form.calc_mode === 'total'}
                    onChange={() => updateField('calc_mode', 'total')}
                    style={{ width: 'auto' }}
                  />
                  Жами суммани киритиш
                </label>
              </div>
            </div>

            {form.calc_mode === 'price' ? (
              <div className="form-group">
                <label>1 литр сотиб олиш нархи (UZS) *</label>
                <input
                  type="text"
                  value={form.purchase_price_per_liter}
                  onChange={(e) => updateField('purchase_price_per_liter', formatMoneyInput(e.target.value))}
                  placeholder="Масалан: 9 000"
                  required
                />
                <div style={{ marginTop: '8px', fontSize: '13px', color: 'var(--text-secondary)' }}>
                  Жами сумма: <strong style={{ color: 'var(--text-primary)' }}>{formatCurrency(form._calculated_total || 0)} UZS</strong>
                </div>
              </div>
            ) : (
              <div className="form-group">
                <label>Жами сумма (UZS) *</label>
                <input
                  type="text"
                  value={form.total_amount}
                  onChange={(e) => updateField('total_amount', formatMoneyInput(e.target.value))}
                  placeholder="Масалан: 10 000 000"
                  required
                />
                <div style={{ marginTop: '8px', fontSize: '13px', color: 'var(--text-secondary)' }}>
                  1 литр нархи: <strong style={{ color: 'var(--text-primary)' }}>{formatCurrency(form._calculated_price || 0)} UZS</strong>
                </div>
              </div>
            )}
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Тўланган сумма (UZS)</label>
              <input
                type="text"
                value={form.paid_amount}
                onChange={(e) => updateField('paid_amount', formatMoneyInput(e.target.value))}
                placeholder="Масалан: 5 000 000"
              />
              <div style={{ marginTop: '8px', fontSize: '13px', color: 'var(--text-secondary)' }}>
                Қарз: <strong className="text-danger">{formatCurrency(form._calculated_debt || 0)} UZS</strong>
              </div>
            </div>
            <div className="form-group">
              <label>Тўлов тури</label>
              <select
                value={form.payment_type}
                onChange={(e) => updateField('payment_type', e.target.value)}
              >
                <option value="cash">Нақд</option>
                <option value="bank_transfer">Перечисления (Банк)</option>
              </select>
            </div>
          </div>

          <div className="form-group">
            <label>Изоҳ</label>
            <input
              type="text"
              value={form.note}
              onChange={(e) => updateField('note', e.target.value)}
              placeholder="Қўшимча маълумот..."
            />
          </div>

          <div className="form-actions">
            <button
              type="button"
              className="btn btn--outline"
              onClick={() => setModalOpen(false)}
            >
              Бекор қилиш
            </button>
            <button
              type="submit"
              className="btn btn--primary"
              disabled={saving}
            >
              {saving ? 'Сақланмоқда...' : 'Сақлаш'}
            </button>
          </div>
        </form>
      </Modal>

      {/* Initial Stock Modal */}
      <Modal
        isOpen={initialStockOpen}
        onClose={() => setInitialStockOpen(false)}
        title="Ўзида бор қолдиқ қўшиш"
        width={500}
      >
        <form onSubmit={handleInitialStockSubmit}>
          {initialError && <div className="alert alert--error">{initialError}</div>}
          <div className="form-group">
            <label>Маҳсулот *</label>
            <select
              value={initialForm.product_id}
              onChange={(e) => setInitialForm({ ...initialForm, product_id: e.target.value })}
              required
            >
              <option value="">Танланг...</option>
              {products.map(p => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label>Миқдор (Литр) *</label>
            <input
              type="text"
              value={initialForm.quantity_liters}
              onChange={(e) => setInitialForm({ ...initialForm, quantity_liters: formatMoneyInput(e.target.value) })}
              placeholder="Масалан: 1 000"
              required
            />
          </div>
          <div className="form-group">
            <label>1 литр таннархи (UZS) *</label>
            <input
              type="text"
              value={initialForm.purchase_price_per_liter}
              onChange={(e) => setInitialForm({ ...initialForm, purchase_price_per_liter: formatMoneyInput(e.target.value) })}
              placeholder="Масалан: 9 000"
              required
            />
          </div>
          <div className="form-group">
            <label>Изоҳ (ихтиёрий)</label>
            <input
              type="text"
              value={initialForm.note}
              onChange={(e) => setInitialForm({ ...initialForm, note: e.target.value })}
              placeholder="Қўшимча маълумот..."
            />
          </div>
          <div className="form-actions">
            <button
              type="button"
              className="btn btn--outline"
              onClick={() => setInitialStockOpen(false)}
            >
              Бекор қилиш
            </button>
            <button
              type="submit"
              className="btn btn--primary"
              disabled={initialLoading}
            >
              {initialLoading ? 'Сақланмоқда...' : 'Сақлаш'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}