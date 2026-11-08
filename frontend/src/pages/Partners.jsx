/**
 * Partners page — full CRUD + premium stats detail modal.
 */
import { useState, useEffect } from 'react';
import client from '../api/client';
import { Eye } from 'lucide-react';
import { getPartners, createPartner, updatePartner, togglePartner } from '../api/partners';
import { formatCurrency, formatNumber } from '../utils/formatters';
import Modal from '../components/Modal';

const PARTNER_TYPE_LABELS = {
  customer: 'Мижоз',
  supplier: 'Етказиб берувчи',
  both: 'Иккаласи ҳам',
};

const TYPE_OPTIONS = [
  { value: '', label: 'Барчаси' },
  { value: 'customer', label: 'Мижозлар' },
  { value: 'supplier', label: 'Етказиб берувчилар' },
  { value: 'both', label: 'Иккаласи ҳам' },
];

const TYPE_FORM_OPTIONS = [
  { value: 'customer', label: 'Мижоз' },
  { value: 'supplier', label: 'Етказиб берувчи' },
  { value: 'both', label: 'Иккаласи ҳам' },
];

export default function Partners() {
  const [partners, setPartners] = useState([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingPartner, setEditingPartner] = useState(null);
  const [filterType, setFilterType] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);

  // Detail modal
  const [detailPartner, setDetailPartner] = useState(null);
  const [stats, setStats] = useState(null);
  const [statsLoading, setStatsLoading] = useState(false);

  const emptyForm = {
    name: '', phone: '', company_name: '', address: '',
    type: 'customer', note: '',
  };
  const [form, setForm] = useState(emptyForm);

  const fetchPartners = async () => {
    try {
      const params = {};
      if (filterType) params.partner_type = filterType;
      if (searchQuery) params.search = searchQuery;
      const res = await getPartners(params);
      setPartners(res.data.items);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchPartners(); }, [filterType, searchQuery]);

  const openCreateModal = () => {
    setEditingPartner(null);
    setForm(emptyForm);
    setError('');
    setModalOpen(true);
  };

  const openEditModal = (partner) => {
    setEditingPartner(partner);
    setForm({
      name: partner.name,
      phone: partner.phone || '',
      company_name: partner.company_name || '',
      address: partner.address || '',
      type: partner.type,
      note: partner.note || '',
    });
    setError('');
    setModalOpen(true);
  };

  const openDetailModal = async (partner) => {
    setDetailPartner(partner);
    setStats(null);
    setStatsLoading(true);
    try {
      const res = await client.get(`/partners/${partner.id}/stats`);
      setStats(res.data);
    } catch (err) {
      console.error(err);
      alert("Статистика юклаб бўлмади.");
    } finally {
      setStatsLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSaving(true);
    try {
      const payload = { ...form };
      if (!payload.phone) payload.phone = null;
      if (!payload.company_name) payload.company_name = null;
      if (!payload.address) payload.address = null;
      if (!payload.note) payload.note = null;

      if (editingPartner) {
        await updatePartner(editingPartner.id, payload);
      } else {
        await createPartner(payload);
      }
      setModalOpen(false);
      fetchPartners();
    } catch (err) {
      setError(err.response?.data?.detail || "Хатолик юз берди");
    } finally {
      setSaving(false);
    }
  };

  const handleToggle = async (partner) => {
    try {
      await togglePartner(partner.id);
      fetchPartners();
    } catch (err) {
      console.error(err);
    }
  };

  const updateField = (field, value) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  if (loading) {
    return (
      <div className="page-loading">
        <div className="loading-spinner" />
      </div>
    );
  }

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Ҳамкорлар</h1>
        <button className="btn btn--primary" onClick={openCreateModal}>
          + Янги ҳамкор
        </button>
      </div>

      {/* Filters */}
      <div className="filter-bar">
        <div className="filter-group">
          <label>Тури:</label>
          <select value={filterType} onChange={(e) => setFilterType(e.target.value)}>
            {TYPE_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        </div>
        <div className="filter-group">
          <label>Қидириш:</label>
          <input
            type="text"
            placeholder="Номи, компания ёки телефон..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
      </div>

      <div className="card">
        <div className="table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>#</th>
                <th>Номи</th>
                <th>Телефон</th>
                <th>Компания</th>
                <th>Тури</th>
                <th>Ҳолат</th>
                <th>Манзил</th>
                <th>Амаллар</th>
              </tr>
            </thead>
            <tbody>
              {partners.length === 0 ? (
                <tr>
                  <td colSpan={8}>
                    <p className="empty-message">Ҳамкорлар топилмади</p>
                  </td>
                </tr>
              ) : (
                partners.map((p, idx) => (
                  <tr key={p.id} className={!p.is_active ? 'row-inactive' : ''}>
                    <td>{idx + 1}</td>
                    <td className="font-medium">{p.name}</td>
                    <td>{p.phone || '—'}</td>
                    <td>{p.company_name || '—'}</td>
                    <td>
                      <span className={`badge badge--type-${p.type}`}>
                        {PARTNER_TYPE_LABELS[p.type] || p.type}
                      </span>
                    </td>
                    <td>
                      <span className={`badge badge--${p.is_active ? 'active' : 'cancelled'}`}>
                        {p.is_active ? 'Фаол' : 'Нофаол'}
                      </span>
                    </td>
                    <td>{p.address || '—'}</td>
                    <td>
                      <div className="action-buttons">
                        <button
                          className="row-action-btn"
                          onClick={() => openDetailModal(p)}
                          title="Батафсил"
                        >
                          <Eye size={16} strokeWidth={2.2} />
                        </button>
                        <button
                          className="btn btn--outline btn--sm"
                          onClick={() => openEditModal(p)}
                        >
                          Таҳрирлаш
                        </button>
                        <button
                          className={`btn btn--sm ${p.is_active ? 'btn--danger-outline' : 'btn--success-outline'}`}
                          onClick={() => handleToggle(p)}
                        >
                          {p.is_active ? "Ўчириш" : 'Фаоллаштириш'}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* CREATE / EDIT MODAL */}
      <Modal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        title={editingPartner ? "Ҳамкорни таҳрирлаш" : "Янги ҳамкор"}
        width={560}
      >
        <form onSubmit={handleSubmit}>
          {error && <div className="alert alert--error">{error}</div>}

          <div className="form-group">
            <label htmlFor="partner-name">Номи *</label>
            <input
              id="partner-name" type="text" value={form.name}
              onChange={(e) => updateField('name', e.target.value)}
              placeholder="Ҳамкор номи" required
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="partner-phone">Телефон</label>
              <input
                id="partner-phone" type="text" value={form.phone}
                onChange={(e) => updateField('phone', e.target.value)}
                placeholder="+998..."
              />
            </div>
            <div className="form-group">
              <label htmlFor="partner-type">Тури *</label>
              <select
                id="partner-type" value={form.type}
                onChange={(e) => updateField('type', e.target.value)}
              >
                {TYPE_FORM_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="partner-company">Компания номи</label>
            <input
              id="partner-company" type="text" value={form.company_name}
              onChange={(e) => updateField('company_name', e.target.value)}
              placeholder="Компания номи"
            />
          </div>

          <div className="form-group">
            <label htmlFor="partner-address">Манзил</label>
            <input
              id="partner-address" type="text" value={form.address}
              onChange={(e) => updateField('address', e.target.value)}
              placeholder="Манзил"
            />
          </div>

          <div className="form-group">
            <label htmlFor="partner-note">Изоҳ</label>
            <textarea
              id="partner-note" value={form.note}
              onChange={(e) => updateField('note', e.target.value)}
              placeholder="Қўшимча маълумот..." rows={3}
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

      {/* DETAIL / STATS MODAL */}
      <Modal
        isOpen={!!detailPartner}
        onClose={() => { setDetailPartner(null); setStats(null); }}
        title={detailPartner ? `${detailPartner.name} — батафсил` : ''}
        width={760}
      >
        {statsLoading ? (
          <p className="empty-message">Юкланмоқда...</p>
        ) : stats ? (
          <>
            {/* Asosiy ma'lumot */}
            <div className="modal-section">
              <div className="modal-section-title">Ҳамкор маълумоти</div>
              <div className="modal-section-row">
                <span className="label">Номи</span>
                <span className="value">{stats.partner.name}</span>
              </div>
              <div className="modal-section-row">
                <span className="label">Тури</span>
                <span className="value">
                  <span className={`badge badge--type-${stats.partner.type}`}>
                    {PARTNER_TYPE_LABELS[stats.partner.type]}
                  </span>
                </span>
              </div>
              {stats.partner.phone && (
                <div className="modal-section-row">
                  <span className="label">Телефон</span>
                  <span className="value">{stats.partner.phone}</span>
                </div>
              )}
              {stats.partner.company_name && (
                <div className="modal-section-row">
                  <span className="label">Компания</span>
                  <span className="value">{stats.partner.company_name}</span>
                </div>
              )}
              {stats.partner.address && (
                <div className="modal-section-row">
                  <span className="label">Манзил</span>
                  <span className="value">{stats.partner.address}</span>
                </div>
              )}
            </div>

            {/* Sotuv statistikasi (mijoz bo'lsa) */}
            {(stats.partner.type === 'customer' || stats.partner.type === 'both') && (
              <div className="modal-section">
                <div className="modal-section-title">Сотув (мижоз сифатида)</div>
                <div className="modal-section-row">
                  <span className="label">Жами сотилган миқдор</span>
                  <span className="value">{formatNumber(stats.as_customer.total_quantity)} Л</span>
                </div>
                <div className="modal-section-row">
                  <span className="label">Жами сотув суммаси</span>
                  <span className="value value--gold">{formatCurrency(stats.as_customer.total_amount)}</span>
                </div>
                <div className="modal-section-row">
                  <span className="label">Операциялар сони</span>
                  <span className="value">{stats.as_customer.total_count} та</span>
                </div>
                <div className="modal-section-row">
                  <span className="label">Охирги сотув санаси</span>
                  <span className="value">{stats.as_customer.last_date || '—'}</span>
                </div>
                <div className="modal-section-row">
                  <span className="label">Жорий қарз (мижоздан)</span>
                  <span className={`value ${stats.as_customer.active_debt > 0 ? 'value--red' : 'value--green'}`}>
                    {formatCurrency(stats.as_customer.active_debt)}
                  </span>
                </div>
              </div>
            )}

            {/* Xarid statistikasi (yetkazib beruvchi bo'lsa) */}
            {(stats.partner.type === 'supplier' || stats.partner.type === 'both') && (
              <div className="modal-section">
                <div className="modal-section-title">Харид (етказиб берувчи сифатида)</div>
                <div className="modal-section-row">
                  <span className="label">Жами олинган миқдор</span>
                  <span className="value">{formatNumber(stats.as_supplier.total_quantity)} Л</span>
                </div>
                <div className="modal-section-row">
                  <span className="label">Жами харид суммаси</span>
                  <span className="value value--gold">{formatCurrency(stats.as_supplier.total_amount)}</span>
                </div>
                <div className="modal-section-row">
                  <span className="label">Операциялар сони</span>
                  <span className="value">{stats.as_supplier.total_count} та</span>
                </div>
                <div className="modal-section-row">
                  <span className="label">Охирги харид санаси</span>
                  <span className="value">{stats.as_supplier.last_date || '—'}</span>
                </div>
                <div className="modal-section-row">
                  <span className="label">Бизнинг қарз (унга)</span>
                  <span className={`value ${stats.as_supplier.active_debt > 0 ? 'value--red' : 'value--green'}`}>
                    {formatCurrency(stats.as_supplier.active_debt)}
                  </span>
                </div>
              </div>
            )}

            {/* Tranzaksiyalar tarixi */}
            <div className="modal-section">
              <div className="modal-section-title">Охирги транзакциялар ({stats.transactions.length} та)</div>
              {stats.transactions.length === 0 ? (
                <p className="empty-message" style={{ padding: '12px 0' }}>Транзакциялар йўқ</p>
              ) : (
                <div style={{ overflowX: 'auto' }}>
                  <table className="data-table" style={{ fontSize: 12.5 }}>
                    <thead>
                      <tr>
                        <th>Сана</th>
                        <th>Тур</th>
                        <th>Маҳсулот</th>
                        <th className="text-right">Миқдор</th>
                        <th className="text-right">Сумма</th>
                      </tr>
                    </thead>
                    <tbody>
                      {stats.transactions.map((t, i) => (
                        <tr key={`${t.type}-${t.id}-${i}`}>
                          <td>{t.date}</td>
                          <td>
                            <span className={`badge ${t.direction === 'in' ? 'badge--income' : t.direction === 'out' ? 'badge--type-customer' : 'badge--paid'}`}>
                              {t.type_label}
                            </span>
                          </td>
                          <td>{t.product}</td>
                          <td className="text-right">
                            {t.quantity > 0 ? `${formatNumber(t.quantity)} Л` : '—'}
                          </td>
                          <td className="text-right" style={{ fontWeight: 700 }}>
                            {formatCurrency(t.amount)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            <div className="form-actions">
              <button className="btn btn--outline" onClick={() => { setDetailPartner(null); setStats(null); }}>
                Ёпиш
              </button>
            </div>
          </>
        ) : (
          <p className="empty-message">Маълумот топилмади</p>
        )}
      </Modal>
    </div>
  );
}