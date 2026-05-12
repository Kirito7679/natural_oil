/**
 * Sales (Sotuv) page.
 * All UI labels in Uzbek.
 */
import { useState, useEffect, useMemo } from 'react';
import { Eye } from 'lucide-react';
import { getSales, createSale, cancelSale } from '../api/sales';
import { getProducts } from '../api/products';
import { getPartners } from '../api/partners';
import { getInventoryBatches } from '../api/inventory';
import { formatDateTime, formatCurrency, formatNumber, formatMoneyInput, parseMoneyInput } from '../utils/formatters';
import { downloadExcel } from '../utils/excelDownload';
import Modal from '../components/Modal';

export default function Sales() {
  const [sales, setSales] = useState([]);
  const [products, setProducts] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [inventoryBatches, setInventoryBatches] = useState([]);

  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  // Detail modal
  const [detailSale, setDetailSale] = useState(null);

  const today = new Date().toISOString().split('T')[0];

  const emptyForm = {
    date: today,
    customer_id: '',
    product_id: '',
    inventory_batch_id: '',
    quantity_liters: '',
    purchase_price_per_liter: '',
    sale_price_per_liter: '',
    paid_amount: '',
    payment_type: 'cash',
    note: ''
  };
  const [form, setForm] = useState(emptyForm);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [salesRes, productsRes, partnersRes, batchesRes] = await Promise.all([
        getSales(),
        getProducts(true),
        getPartners({ partner_type: 'customer', active_only: true }),
        getInventoryBatches('active')
      ]);
      setSales(salesRes.data.items);
      setProducts(productsRes.data.items);
      setCustomers(partnersRes.data.items.filter(p => p.is_active));
      setInventoryBatches(batchesRes.data.items);
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

      if (field === 'inventory_batch_id' && value) {
        const selectedBatch = inventoryBatches.find(b => b.id.toString() === value.toString());
        if (selectedBatch) {
          next.purchase_price_per_liter = selectedBatch.purchase_price_per_liter;
        }
      }

      if (field === 'product_id') {
        next.inventory_batch_id = '';
        next.purchase_price_per_liter = '';
      }

      return next;
    });
  };

  const availableBatches = useMemo(() => {
    if (!form.product_id) return [];
    return inventoryBatches.filter(b => b.product.id.toString() === form.product_id.toString());
  }, [form.product_id, inventoryBatches]);

  const selectedBatchDetails = useMemo(() => {
    if (!form.inventory_batch_id) return null;
    return inventoryBatches.find(b => b.id.toString() === form.inventory_batch_id.toString());
  }, [form.inventory_batch_id, inventoryBatches]);

  const qty = parseMoneyInput(form.quantity_liters);
  const salePrice = parseMoneyInput(form.sale_price_per_liter);
  const purchasePrice = parseMoneyInput(form.purchase_price_per_liter);
  const paidAmount = parseMoneyInput(form.paid_amount);

  const totalSale = qty * salePrice;
  const totalCost = qty * purchasePrice;
  const profitPerLiter = salePrice - purchasePrice;
  const totalProfit = profitPerLiter * qty;
  const remainingDebt = Math.max(0, totalSale - paidAmount);

  const isLoss = salePrice > 0 && purchasePrice > 0 && salePrice < purchasePrice;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!form.customer_id || !form.product_id || !form.inventory_batch_id) {
      setError("Mijoz, mahsulot va ombor partiyasini tanlang");
      return;
    }
    if (qty <= 0) {
      setError("Miqdor 0 dan katta bo'lishi kerak");
      return;
    }
    if (salePrice <= 0) {
      setError("Sotish narxi 0 dan katta bo'lishi kerak");
      return;
    }
    if (paidAmount > totalSale + 0.01) {
      setError("To'langan summa umumiy sotuv summasidan katta bo'lishi mumkin emas.");
      return;
    }
    if (selectedBatchDetails && qty > selectedBatchDetails.remaining_quantity_liters) {
      setError(`Ombordagi qoldiq yetarli emas. Maksimal: ${selectedBatchDetails.remaining_quantity_liters} L`);
      return;
    }

    setSaving(true);
    try {
      const payload = {
        date: form.date,
        customer_id: parseInt(form.customer_id),
        product_id: parseInt(form.product_id),
        inventory_batch_id: parseInt(form.inventory_batch_id),
        quantity_liters: qty,
        purchase_price_per_liter: purchasePrice,
        sale_price_per_liter: salePrice,
        note: form.note || null,
        payments: []
      };

      if (paidAmount > 0) {
        payload.payments.push({
          payment_type: form.payment_type,
          amount: paidAmount
        });
      }

      await createSale(payload);
      setModalOpen(false);
      fetchData();
    } catch (err) {
      setError(err.response?.data?.detail || "Xatolik yuz berdi");
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = async (id) => {
    if (!window.confirm("Haqiqatan ham bu sotuvni bekor qilmoqchimisiz?")) return;
    try {
      await cancelSale(id);
      setDetailSale(null);
      fetchData();
    } catch (err) {
      alert(err.response?.data?.detail || "Bekor qilishda xatolik");
    }
  };

  if (loading && sales.length === 0) {
    return (
      <div className="page-loading">
        <div className="loading-spinner" />
      </div>
    );
  }

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Sotuv</h1>
        <div className="action-buttons">
          <button
            className="btn btn-secondary"
            onClick={() => downloadExcel('sales', {}, 'natural_oil_sales.xlsx')}
          >
            ⬇ Excel
          </button>
          <button className="btn btn--primary" onClick={openCreateModal}>
            + Yangi sotuv
          </button>
        </div>
      </div>

      <div className="card">
        <div className="table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>Sana</th>
                <th>Mijoz</th>
                <th>Mahsulot</th>
                <th className="text-right">Miqdor</th>
                <th className="text-right">Sotish narxi</th>
                <th className="text-right">Umumiy sotuv</th>
                <th className="text-right">To'langan</th>
                <th className="text-right">Qarz</th>
                <th>To'lov turi</th>
                <th>Status</th>
                <th style={{ textAlign: 'center' }}>Amal</th>
              </tr>
            </thead>
            <tbody>
              {sales.length === 0 ? (
                <tr>
                  <td colSpan={11}>
                    <p className="empty-message">Sotuvlar mavjud emas</p>
                  </td>
                </tr>
              ) : (
                sales.map((s) => (
                  <tr key={s.id} className={s.status === 'cancelled' ? 'row-inactive' : ''}>
                    <td>{s.date}</td>
                    <td className="font-medium">{s.customer.name}</td>
                    <td>{s.product.name}</td>
                    <td className="text-right">{formatNumber(s.quantity_liters)} L</td>
                    <td className="text-right">{formatCurrency(s.sale_price_per_liter)}</td>
                    <td className="text-right font-medium">{formatCurrency(s.total_sale_amount)}</td>
                    <td className="text-right" style={{ color: 'var(--success)' }}>
                      {formatCurrency(s.paid_amount)}
                    </td>
                    <td className="text-right" style={{ color: s.debt_amount > 0 ? 'var(--danger)' : 'var(--text-muted)', fontWeight: 600 }}>
                      {formatCurrency(s.debt_amount)}
                    </td>
                    <td>
                      {s.payments && s.payments.length > 0
                        ? s.payments.map(p => p.payment_type === 'cash' ? 'Naqd' : 'Perechisleniya').join(', ')
                        : '—'}
                    </td>
                    <td>
                      <span className={`badge badge--${s.status === 'active' ? 'active' : 'cancelled'}`}>
                        {s.status === 'active' ? 'Faol' : 'Bekor qilingan'}
                      </span>
                    </td>
                    <td style={{ textAlign: 'center' }}>
                      <button
                        className="row-action-btn"
                        onClick={() => setDetailSale(s)}
                        title="Batafsil"
                      >
                        <Eye size={16} strokeWidth={2.2} />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* CREATE MODAL */}
      <Modal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        title="Yangi sotuv"
        width={700}
      >
        <form onSubmit={handleSubmit}>
          {error && <div className="alert alert--error">{error}</div>}

          {isLoss && (
            <div className="alert alert--error" style={{ marginBottom: '16px', fontWeight: 'bold' }}>
              Sotish narxi kirim narxidan past. Bu sotuv zarar bilan amalga oshadi.
            </div>
          )}

          <div className="form-row">
            <div className="form-group">
              <label>Sana *</label>
              <input type="date" value={form.date} onChange={(e) => updateField('date', e.target.value)} required />
            </div>
            <div className="form-group">
              <label>Mijoz *</label>
              <select value={form.customer_id} onChange={(e) => updateField('customer_id', e.target.value)} required>
                <option value="">Tanlang...</option>
                {customers.map(c => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Mahsulot *</label>
              <select value={form.product_id} onChange={(e) => updateField('product_id', e.target.value)} required>
                <option value="">Tanlang...</option>
                {products.map(p => (
                  <option key={p.id} value={p.id}>{p.name}</option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label>Ombor partiyasi *</label>
              <select
                value={form.inventory_batch_id}
                onChange={(e) => updateField('inventory_batch_id', e.target.value)}
                required
                disabled={!form.product_id || availableBatches.length === 0}
              >
                <option value="">Tanlang...</option>
                {availableBatches.map(b => (
                  <option key={b.id} value={b.id}>
                    Qoldiq: {b.remaining_quantity_liters} L (Kirim: {formatCurrency(b.purchase_price_per_liter)})
                  </option>
                ))}
              </select>
            </div>
          </div>

          {selectedBatchDetails && (
            <div className="modal-section">
              <div className="modal-section-title">Partiya ma'lumotlari</div>
              <div className="modal-section-row">
                <span className="label">Kirim narxi</span>
                <span className="value">{formatCurrency(selectedBatchDetails.purchase_price_per_liter)}</span>
              </div>
              <div className="modal-section-row">
                <span className="label">Qolgan miqdor</span>
                <span className="value">{selectedBatchDetails.remaining_quantity_liters} L</span>
              </div>
              <div className="modal-section-row">
                <span className="label">Yetkazib beruvchi</span>
                <span className="value">{selectedBatchDetails.supplier?.name}</span>
              </div>
            </div>
          )}

          <div className="form-row">
            <div className="form-group">
              <label>Miqdor, litrda *</label>
              <input
                type="text"
                value={form.quantity_liters}
                onChange={(e) => updateField('quantity_liters', formatMoneyInput(e.target.value))}
                placeholder="0.00" required
              />
            </div>
            <div className="form-group">
              <label>Sotish narxi *</label>
              <input
                type="text"
                value={form.sale_price_per_liter}
                onChange={(e) => updateField('sale_price_per_liter', formatMoneyInput(e.target.value))}
                placeholder="0.00" required
              />
            </div>
          </div>

          <div className="modal-section">
            <div className="modal-section-title">Hisob-kitob (jonli)</div>
            <div className="modal-section-row">
              <span className="label">1 litr foyda</span>
              <span className={`value ${profitPerLiter >= 0 ? 'value--green' : 'value--red'}`}>
                {formatCurrency(profitPerLiter)}
              </span>
            </div>
            <div className="modal-section-row">
              <span className="label">Umumiy tannarx</span>
              <span className="value">{formatCurrency(totalCost)}</span>
            </div>
            <div className="modal-section-row">
              <span className="label">Umumiy sotuv</span>
              <span className="value value--gold">{formatCurrency(totalSale)}</span>
            </div>
            <div className="modal-section-row">
              <span className="label">Umumiy foyda</span>
              <span className={`value ${totalProfit >= 0 ? 'value--green' : 'value--red'}`}>
                {formatCurrency(totalProfit)}
              </span>
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>To'langan summa</label>
              <input
                type="text"
                value={form.paid_amount}
                onChange={(e) => updateField('paid_amount', formatMoneyInput(e.target.value))}
                placeholder="0.00"
              />
              <div style={{ marginTop: '8px', fontSize: '13px', color: 'var(--text-secondary)' }}>
                Qolgan qarz: <strong style={{ color: 'var(--danger)' }}>{formatCurrency(remainingDebt)} UZS</strong>
              </div>
            </div>
            <div className="form-group">
              <label>To'lov turi</label>
              <select value={form.payment_type} onChange={(e) => updateField('payment_type', e.target.value)}>
                <option value="cash">Naqd</option>
                <option value="bank_transfer">Perechisleniya</option>
              </select>
            </div>
          </div>

          <div className="form-group">
            <label>Izoh</label>
            <input
              type="text" value={form.note}
              onChange={(e) => updateField('note', e.target.value)}
              placeholder="Qo'shimcha ma'lumot..."
            />
          </div>

          <div className="form-actions">
            <button type="button" className="btn btn--outline" onClick={() => setModalOpen(false)}>
              Bekor qilish
            </button>
            <button type="submit" className="btn btn--primary" disabled={saving}>
              {saving ? 'Saqlanmoqda...' : 'Saqlash'}
            </button>
          </div>
        </form>
      </Modal>

      {/* DETAIL MODAL */}
      <Modal
        isOpen={!!detailSale}
        onClose={() => setDetailSale(null)}
        title={detailSale ? `Sotuv #${detailSale.id} — batafsil` : ''}
        width={620}
      >
        {detailSale && (
          <>
            {/* Asosiy ma'lumotlar */}
            <div className="modal-section">
              <div className="modal-section-title">Asosiy ma'lumotlar</div>
              <div className="modal-section-row">
                <span className="label">Sana</span>
                <span className="value">{detailSale.date}</span>
              </div>
              <div className="modal-section-row">
                <span className="label">Mijoz</span>
                <span className="value">{detailSale.customer?.name}</span>
              </div>
              <div className="modal-section-row">
                <span className="label">Mahsulot</span>
                <span className="value">{detailSale.product?.name}</span>
              </div>
              <div className="modal-section-row">
                <span className="label">Miqdor</span>
                <span className="value">{formatNumber(detailSale.quantity_liters)} L</span>
              </div>
              <div className="modal-section-row">
                <span className="label">Status</span>
                <span className="value">
                  <span className={`badge badge--${detailSale.status === 'active' ? 'active' : 'cancelled'}`}>
                    {detailSale.status === 'active' ? 'Faol' : 'Bekor qilingan'}
                  </span>
                </span>
              </div>
            </div>

            {/* Narx va foyda */}
            <div className="modal-section">
              <div className="modal-section-title">Narx va foyda</div>
              <div className="modal-section-row">
                <span className="label">Kirim narxi (1 L)</span>
                <span className="value">{formatCurrency(detailSale.purchase_price_per_liter)}</span>
              </div>
              <div className="modal-section-row">
                <span className="label">Sotish narxi (1 L)</span>
                <span className="value">{formatCurrency(detailSale.sale_price_per_liter)}</span>
              </div>
              <div className="modal-section-row">
                <span className="label">1 litr foyda</span>
                <span className={`value ${detailSale.profit_per_liter >= 0 ? 'value--green' : 'value--red'}`}>
                  {formatCurrency(detailSale.profit_per_liter)}
                </span>
              </div>
              <div className="modal-section-row">
                <span className="label">Umumiy tannarx</span>
                <span className="value">{formatCurrency(detailSale.total_cost)}</span>
              </div>
              <div className="modal-section-row">
                <span className="label">Umumiy sotuv</span>
                <span className="value value--gold">{formatCurrency(detailSale.total_sale_amount)}</span>
              </div>
              <div className="modal-section-row">
                <span className="label">Umumiy foyda</span>
                <span className={`value ${detailSale.total_profit >= 0 ? 'value--green' : 'value--red'}`}>
                  {formatCurrency(detailSale.total_profit)}
                </span>
              </div>
            </div>

            {/* To'lov */}
            <div className="modal-section">
              <div className="modal-section-title">To'lov</div>
              <div className="modal-section-row">
                <span className="label">To'langan summa</span>
                <span className="value value--green">{formatCurrency(detailSale.paid_amount)}</span>
              </div>
              <div className="modal-section-row">
                <span className="label">Qolgan qarz</span>
                <span className={`value ${detailSale.debt_amount > 0 ? 'value--red' : ''}`}>
                  {formatCurrency(detailSale.debt_amount)}
                </span>
              </div>
              {detailSale.payments && detailSale.payments.length > 0 && (
                <div className="modal-section-row">
                  <span className="label">To'lov turi</span>
                  <span className="value">
                    {detailSale.payments.map(p =>
                      `${p.payment_type === 'cash' ? 'Naqd' : 'Perechisleniya'} (${formatCurrency(p.amount)})`
                    ).join(', ')}
                  </span>
                </div>
              )}
            </div>

            {detailSale.note && (
              <div className="modal-section">
                <div className="modal-section-title">Izoh</div>
                <div style={{ fontSize: 13, color: 'var(--text-primary)' }}>{detailSale.note}</div>
              </div>
            )}

            <div className="form-actions">
              <button className="btn btn--outline" onClick={() => setDetailSale(null)}>
                Yopish
              </button>
              {detailSale.status === 'active' && (
                <button
                  className="btn btn--danger"
                  onClick={() => handleCancel(detailSale.id)}
                >
                  Sotuvni bekor qilish
                </button>
              )}
            </div>
          </>
        )}
      </Modal>
    </div>
  );
}