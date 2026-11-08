/**
 * Sales (Sotuv) page.
 * All UI labels in Uzbek.
 */
import { useState, useEffect, useMemo } from 'react';
import { Eye } from 'lucide-react';
import { getSales, createSale, cancelSale } from '../api/sales';
import { getProducts } from '../api/products';
import { getPartners } from '../api/partners';
import PartnerPicker from '../components/PartnerPicker';
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
      setError("Мижоз, маҳсулот ва омбор партиясини танланг");
      return;
    }
    if (qty <= 0) {
      setError("Миқдор 0 дан катта бўлиши керак");
      return;
    }
    if (salePrice <= 0) {
      setError("Сотиш нархи 0 дан катта бўлиши керак");
      return;
    }
    if (paidAmount > totalSale + 0.01) {
      setError("Тўланган сумма умумий сотув суммасидан катта бўлиши мумкин эмас.");
      return;
    }
    if (selectedBatchDetails && qty > selectedBatchDetails.remaining_quantity_liters) {
      setError(`Омбордаги қолдиқ етарли эмас. Максимал: ${selectedBatchDetails.remaining_quantity_liters} Л`);
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
      setError(err.response?.data?.detail || "Хатолик юз берди");
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = async (id) => {
    if (!window.confirm("Ҳақиқатан ҳам бу сотувни бекор қилмоқчимисиз?")) return;
    try {
      await cancelSale(id);
      setDetailSale(null);
      fetchData();
    } catch (err) {
      alert(err.response?.data?.detail || "Бекор қилишда хатолик");
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
        <h1 className="page-title">Сотув</h1>
        <div className="action-buttons">
          <button
            className="btn btn-secondary"
            onClick={() => downloadExcel('sales', {}, 'natural_oil_sales.xlsx')}
          >
            ⬇ Excel
          </button>
          <button className="btn btn--primary" onClick={openCreateModal}>
            + Янги сотув
          </button>
        </div>
      </div>

      <div className="card">
        <div className="table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>Сана</th>
                <th>Мижоз</th>
                <th>Маҳсулот</th>
                <th className="text-right">Миқдор</th>
                <th className="text-right">Сотиш нархи</th>
                <th className="text-right">Умумий сотув</th>
                <th className="text-right">Тўланган</th>
                <th className="text-right">Қарз</th>
                <th>Тўлов тури</th>
                <th>Статус</th>
                <th style={{ textAlign: 'center' }}>Амал</th>
              </tr>
            </thead>
            <tbody>
              {sales.length === 0 ? (
                <tr>
                  <td colSpan={11}>
                    <p className="empty-message">Сотувлар мавжуд эмас</p>
                  </td>
                </tr>
              ) : (
                sales.map((s) => (
                  <tr key={s.id} className={s.status === 'cancelled' ? 'row-inactive' : ''}>
                    <td>{s.date}</td>
                    <td className="font-medium">{s.customer.name}</td>
                    <td>{s.product.name}</td>
                    <td className="text-right">{formatNumber(s.quantity_liters)} Л</td>
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
                        ? s.payments.map(p => p.payment_type === 'cash' ? 'Нақд' : 'Перечисления').join(', ')
                        : '—'}
                    </td>
                    <td>
                      <span className={`badge badge--${s.status === 'active' ? 'active' : 'cancelled'}`}>
                        {s.status === 'active' ? 'Фаол' : 'Бекор қилинган'}
                      </span>
                    </td>
                    <td style={{ textAlign: 'center' }}>
                      <button
                        className="row-action-btn"
                        onClick={() => setDetailSale(s)}
                        title="Батафсил"
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
        title="Янги сотув"
        width={700}
      >
        <form onSubmit={handleSubmit}>
          {error && <div className="alert alert--error">{error}</div>}

          {isLoss && (
            <div className="alert alert--error" style={{ marginBottom: '16px', fontWeight: 'bold' }}>
              Сотиш нархи кирим нархидан паст. Бу сотув зарар билан амалга ошади.
            </div>
          )}

          <div className="form-row">
            <div className="form-group">
              <label>Сана *</label>
              <input type="date" value={form.date} onChange={(e) => updateField('date', e.target.value)} required />
            </div>
            <PartnerPicker
              type="customer"
              label="Мижоз"
              partners={customers}
              onPartnersChange={setCustomers}
              value={form.customer_id}
              onChange={(v) => updateField('customer_id', v)}
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Маҳсулот *</label>
              <select value={form.product_id} onChange={(e) => updateField('product_id', e.target.value)} required>
                <option value="">Танланг...</option>
                {products.map(p => (
                  <option key={p.id} value={p.id}>{p.name}</option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label>Омбор партияси *</label>
              <select
                value={form.inventory_batch_id}
                onChange={(e) => updateField('inventory_batch_id', e.target.value)}
                required
                disabled={!form.product_id || availableBatches.length === 0}
              >
                <option value="">Танланг...</option>
                {availableBatches.map(b => (
                  <option key={b.id} value={b.id}>
                    Қолдиқ: {b.remaining_quantity_liters} Л (Кирим: {formatCurrency(b.purchase_price_per_liter)})
                  </option>
                ))}
              </select>
            </div>
          </div>

          {selectedBatchDetails && (
            <div className="modal-section">
              <div className="modal-section-title">Партия маълумотлари</div>
              <div className="modal-section-row">
                <span className="label">Кирим нархи</span>
                <span className="value">{formatCurrency(selectedBatchDetails.purchase_price_per_liter)}</span>
              </div>
              <div className="modal-section-row">
                <span className="label">Қолган миқдор</span>
                <span className="value">{selectedBatchDetails.remaining_quantity_liters} Л</span>
              </div>
              <div className="modal-section-row">
                <span className="label">Етказиб берувчи</span>
                <span className="value">{selectedBatchDetails.supplier?.name}</span>
              </div>
            </div>
          )}

          <div className="form-row">
            <div className="form-group">
              <label>Миқдор, литрда *</label>
              <input
                type="text"
                value={form.quantity_liters}
                onChange={(e) => updateField('quantity_liters', formatMoneyInput(e.target.value))}
                placeholder="0.00" required
              />
            </div>
            <div className="form-group">
              <label>Сотиш нархи *</label>
              <input
                type="text"
                value={form.sale_price_per_liter}
                onChange={(e) => updateField('sale_price_per_liter', formatMoneyInput(e.target.value))}
                placeholder="0.00" required
              />
            </div>
          </div>

          <div className="modal-section">
            <div className="modal-section-title">Ҳисоб-китоб (жонли)</div>
            <div className="modal-section-row">
              <span className="label">1 литр фойда</span>
              <span className={`value ${profitPerLiter >= 0 ? 'value--green' : 'value--red'}`}>
                {formatCurrency(profitPerLiter)}
              </span>
            </div>
            <div className="modal-section-row">
              <span className="label">Умумий таннарх</span>
              <span className="value">{formatCurrency(totalCost)}</span>
            </div>
            <div className="modal-section-row">
              <span className="label">Умумий сотув</span>
              <span className="value value--gold">{formatCurrency(totalSale)}</span>
            </div>
            <div className="modal-section-row">
              <span className="label">Умумий фойда</span>
              <span className={`value ${totalProfit >= 0 ? 'value--green' : 'value--red'}`}>
                {formatCurrency(totalProfit)}
              </span>
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Тўланган сумма</label>
              <input
                type="text"
                value={form.paid_amount}
                onChange={(e) => updateField('paid_amount', formatMoneyInput(e.target.value))}
                placeholder="0.00"
              />
              <div style={{ marginTop: '8px', fontSize: '13px', color: 'var(--text-secondary)' }}>
                Қолган қарз: <strong style={{ color: 'var(--danger)' }}>{formatCurrency(remainingDebt)} UZS</strong>
              </div>
            </div>
            <div className="form-group">
              <label>Тўлов тури</label>
              <select value={form.payment_type} onChange={(e) => updateField('payment_type', e.target.value)}>
                <option value="cash">Нақд</option>
                <option value="bank_transfer">Перечисления</option>
              </select>
            </div>
          </div>

          <div className="form-group">
            <label>Изоҳ</label>
            <input
              type="text" value={form.note}
              onChange={(e) => updateField('note', e.target.value)}
              placeholder="Қўшимча маълумот..."
            />
          </div>

          <div className="form-actions">
            <button type="button" className="btn btn--outline" onClick={() => setModalOpen(false)}>
              Бекор қилиш
            </button>
            <button type="submit" className="btn btn--primary" disabled={saving}>
              {saving ? 'Сақланмоқда...' : 'Сақлаш'}
            </button>
          </div>
        </form>
      </Modal>

      {/* DETAIL MODAL */}
      <Modal
        isOpen={!!detailSale}
        onClose={() => setDetailSale(null)}
        title={detailSale ? `Сотув #${detailSale.id} — батафсил` : ''}
        width={620}
      >
        {detailSale && (
          <>
            {/* Asosiy ma'lumotlar */}
            <div className="modal-section">
              <div className="modal-section-title">Асосий маълумотлар</div>
              <div className="modal-section-row">
                <span className="label">Сана</span>
                <span className="value">{detailSale.date}</span>
              </div>
              <div className="modal-section-row">
                <span className="label">Мижоз</span>
                <span className="value">{detailSale.customer?.name}</span>
              </div>
              <div className="modal-section-row">
                <span className="label">Маҳсулот</span>
                <span className="value">{detailSale.product?.name}</span>
              </div>
              <div className="modal-section-row">
                <span className="label">Миқдор</span>
                <span className="value">{formatNumber(detailSale.quantity_liters)} Л</span>
              </div>
              <div className="modal-section-row">
                <span className="label">Статус</span>
                <span className="value">
                  <span className={`badge badge--${detailSale.status === 'active' ? 'active' : 'cancelled'}`}>
                    {detailSale.status === 'active' ? 'Фаол' : 'Бекор қилинган'}
                  </span>
                </span>
              </div>
            </div>

            {/* Narx va foyda */}
            <div className="modal-section">
              <div className="modal-section-title">Нарх ва фойда</div>
              <div className="modal-section-row">
                <span className="label">Кирим нархи (1 Л)</span>
                <span className="value">{formatCurrency(detailSale.purchase_price_per_liter)}</span>
              </div>
              <div className="modal-section-row">
                <span className="label">Сотиш нархи (1 Л)</span>
                <span className="value">{formatCurrency(detailSale.sale_price_per_liter)}</span>
              </div>
              <div className="modal-section-row">
                <span className="label">1 литр фойда</span>
                <span className={`value ${detailSale.profit_per_liter >= 0 ? 'value--green' : 'value--red'}`}>
                  {formatCurrency(detailSale.profit_per_liter)}
                </span>
              </div>
              <div className="modal-section-row">
                <span className="label">Умумий таннарх</span>
                <span className="value">{formatCurrency(detailSale.total_cost)}</span>
              </div>
              <div className="modal-section-row">
                <span className="label">Умумий сотув</span>
                <span className="value value--gold">{formatCurrency(detailSale.total_sale_amount)}</span>
              </div>
              <div className="modal-section-row">
                <span className="label">Умумий фойда</span>
                <span className={`value ${detailSale.total_profit >= 0 ? 'value--green' : 'value--red'}`}>
                  {formatCurrency(detailSale.total_profit)}
                </span>
              </div>
            </div>

            {/* To'lov */}
            <div className="modal-section">
              <div className="modal-section-title">Тўлов</div>
              <div className="modal-section-row">
                <span className="label">Тўланган сумма</span>
                <span className="value value--green">{formatCurrency(detailSale.paid_amount)}</span>
              </div>
              <div className="modal-section-row">
                <span className="label">Қолган қарз</span>
                <span className={`value ${detailSale.debt_amount > 0 ? 'value--red' : ''}`}>
                  {formatCurrency(detailSale.debt_amount)}
                </span>
              </div>
              {detailSale.payments && detailSale.payments.length > 0 && (
                <div className="modal-section-row">
                  <span className="label">Тўлов тури</span>
                  <span className="value">
                    {detailSale.payments.map(p =>
                      `${p.payment_type === 'cash' ? 'Нақд' : 'Перечисления'} (${formatCurrency(p.amount)})`
                    ).join(', ')}
                  </span>
                </div>
              )}
            </div>

            {detailSale.note && (
              <div className="modal-section">
                <div className="modal-section-title">Изоҳ</div>
                <div style={{ fontSize: 13, color: 'var(--text-primary)' }}>{detailSale.note}</div>
              </div>
            )}

            <div className="form-actions">
              <button className="btn btn--outline" onClick={() => setDetailSale(null)}>
                Ёпиш
              </button>
              {detailSale.status === 'active' && (
                <button
                  className="btn btn--danger"
                  onClick={() => handleCancel(detailSale.id)}
                >
                  Сотувни бекор қилиш
                </button>
              )}
            </div>
          </>
        )}
      </Modal>
    </div>
  );
}