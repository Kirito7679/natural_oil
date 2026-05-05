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
  customer: 'Mijoz',
  supplier: 'Yetkazib beruvchi',
  both: 'Ikkalasi ham',
};

const TYPE_OPTIONS = [
  { value: '', label: 'Barchasi' },
  { value: 'customer', label: 'Mijozlar' },
  { value: 'supplier', label: 'Yetkazib beruvchilar' },
  { value: 'both', label: 'Ikkalasi ham' },
];

const TYPE_FORM_OPTIONS = [
  { value: 'customer', label: 'Mijoz' },
  { value: 'supplier', label: 'Yetkazib beruvchi' },
  { value: 'both', label: 'Ikkalasi ham' },
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
      alert("Statistika yuklab bo'lmadi.");
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
      setError(err.response?.data?.detail || "Xatolik yuz berdi");
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
        <h1 className="page-title">Hamkorlar</h1>
        <button className="btn btn--primary" onClick={openCreateModal}>
          + Yangi hamkor
        </button>
      </div>

      {/* Filters */}
      <div className="filter-bar">
        <div className="filter-group">
          <label>Turi:</label>
          <select value={filterType} onChange={(e) => setFilterType(e.target.value)}>
            {TYPE_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        </div>
        <div className="filter-group">
          <label>Qidirish:</label>
          <input
            type="text"
            placeholder="Nomi, kompaniya yoki telefon..."
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
                <th>Nomi</th>
                <th>Telefon</th>
                <th>Kompaniya</th>
                <th>Turi</th>
                <th>Holat</th>
                <th>Manzil</th>
                <th>Amallar</th>
              </tr>
            </thead>
            <tbody>
              {partners.length === 0 ? (
                <tr>
                  <td colSpan={8}>
                    <p className="empty-message">Hamkorlar topilmadi</p>
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
                        {p.is_active ? 'Faol' : 'Nofaol'}
                      </span>
                    </td>
                    <td>{p.address || '—'}</td>
                    <td>
                      <div className="action-buttons">
                        <button
                          className="row-action-btn"
                          onClick={() => openDetailModal(p)}
                          title="Batafsil"
                        >
                          <Eye size={16} strokeWidth={2.2} />
                        </button>
                        <button
                          className="btn btn--outline btn--sm"
                          onClick={() => openEditModal(p)}
                        >
                          Tahrirlash
                        </button>
                        <button
                          className={`btn btn--sm ${p.is_active ? 'btn--danger-outline' : 'btn--success-outline'}`}
                          onClick={() => handleToggle(p)}
                        >
                          {p.is_active ? "O'chirish" : 'Faollashtirish'}
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
        title={editingPartner ? "Hamkorni tahrirlash" : "Yangi hamkor"}
        width={560}
      >
        <form onSubmit={handleSubmit}>
          {error && <div className="alert alert--error">{error}</div>}

          <div className="form-group">
            <label htmlFor="partner-name">Nomi *</label>
            <input
              id="partner-name" type="text" value={form.name}
              onChange={(e) => updateField('name', e.target.value)}
              placeholder="Hamkor nomi" required
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="partner-phone">Telefon</label>
              <input
                id="partner-phone" type="text" value={form.phone}
                onChange={(e) => updateField('phone', e.target.value)}
                placeholder="+998..."
              />
            </div>
            <div className="form-group">
              <label htmlFor="partner-type">Turi *</label>
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
            <label htmlFor="partner-company">Kompaniya nomi</label>
            <input
              id="partner-company" type="text" value={form.company_name}
              onChange={(e) => updateField('company_name', e.target.value)}
              placeholder="Kompaniya nomi"
            />
          </div>

          <div className="form-group">
            <label htmlFor="partner-address">Manzil</label>
            <input
              id="partner-address" type="text" value={form.address}
              onChange={(e) => updateField('address', e.target.value)}
              placeholder="Manzil"
            />
          </div>

          <div className="form-group">
            <label htmlFor="partner-note">Izoh</label>
            <textarea
              id="partner-note" value={form.note}
              onChange={(e) => updateField('note', e.target.value)}
              placeholder="Qo'shimcha ma'lumot..." rows={3}
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

      {/* DETAIL / STATS MODAL */}
      <Modal
        isOpen={!!detailPartner}
        onClose={() => { setDetailPartner(null); setStats(null); }}
        title={detailPartner ? `${detailPartner.name} — batafsil` : ''}
        width={760}
      >
        {statsLoading ? (
          <p className="empty-message">Yuklanmoqda...</p>
        ) : stats ? (
          <>
            {/* Asosiy ma'lumot */}
            <div className="modal-section">
              <div className="modal-section-title">Hamkor ma'lumoti</div>
              <div className="modal-section-row">
                <span className="label">Nomi</span>
                <span className="value">{stats.partner.name}</span>
              </div>
              <div className="modal-section-row">
                <span className="label">Turi</span>
                <span className="value">
                  <span className={`badge badge--type-${stats.partner.type}`}>
                    {PARTNER_TYPE_LABELS[stats.partner.type]}
                  </span>
                </span>
              </div>
              {stats.partner.phone && (
                <div className="modal-section-row">
                  <span className="label">Telefon</span>
                  <span className="value">{stats.partner.phone}</span>
                </div>
              )}
              {stats.partner.company_name && (
                <div className="modal-section-row">
                  <span className="label">Kompaniya</span>
                  <span className="value">{stats.partner.company_name}</span>
                </div>
              )}
              {stats.partner.address && (
                <div className="modal-section-row">
                  <span className="label">Manzil</span>
                  <span className="value">{stats.partner.address}</span>
                </div>
              )}
            </div>

            {/* Sotuv statistikasi (mijoz bo'lsa) */}
            {(stats.partner.type === 'customer' || stats.partner.type === 'both') && (
              <div className="modal-section">
                <div className="modal-section-title">Sotuv (mijoz sifatida)</div>
                <div className="modal-section-row">
                  <span className="label">Jami sotilgan miqdor</span>
                  <span className="value">{formatNumber(stats.as_customer.total_quantity)} L</span>
                </div>
                <div className="modal-section-row">
                  <span className="label">Jami sotuv summasi</span>
                  <span className="value value--gold">{formatCurrency(stats.as_customer.total_amount)}</span>
                </div>
                <div className="modal-section-row">
                  <span className="label">Operatsiyalar soni</span>
                  <span className="value">{stats.as_customer.total_count} ta</span>
                </div>
                <div className="modal-section-row">
                  <span className="label">Oxirgi sotuv sanasi</span>
                  <span className="value">{stats.as_customer.last_date || '—'}</span>
                </div>
                <div className="modal-section-row">
                  <span className="label">Joriy qarz (mijozdan)</span>
                  <span className={`value ${stats.as_customer.active_debt > 0 ? 'value--red' : 'value--green'}`}>
                    {formatCurrency(stats.as_customer.active_debt)}
                  </span>
                </div>
              </div>
            )}

            {/* Xarid statistikasi (yetkazib beruvchi bo'lsa) */}
            {(stats.partner.type === 'supplier' || stats.partner.type === 'both') && (
              <div className="modal-section">
                <div className="modal-section-title">Xarid (yetkazib beruvchi sifatida)</div>
                <div className="modal-section-row">
                  <span className="label">Jami olingan miqdor</span>
                  <span className="value">{formatNumber(stats.as_supplier.total_quantity)} L</span>
                </div>
                <div className="modal-section-row">
                  <span className="label">Jami xarid summasi</span>
                  <span className="value value--gold">{formatCurrency(stats.as_supplier.total_amount)}</span>
                </div>
                <div className="modal-section-row">
                  <span className="label">Operatsiyalar soni</span>
                  <span className="value">{stats.as_supplier.total_count} ta</span>
                </div>
                <div className="modal-section-row">
                  <span className="label">Oxirgi xarid sanasi</span>
                  <span className="value">{stats.as_supplier.last_date || '—'}</span>
                </div>
                <div className="modal-section-row">
                  <span className="label">Bizning qarz (unga)</span>
                  <span className={`value ${stats.as_supplier.active_debt > 0 ? 'value--red' : 'value--green'}`}>
                    {formatCurrency(stats.as_supplier.active_debt)}
                  </span>
                </div>
              </div>
            )}

            {/* Tranzaksiyalar tarixi */}
            <div className="modal-section">
              <div className="modal-section-title">Oxirgi tranzaksiyalar ({stats.transactions.length} ta)</div>
              {stats.transactions.length === 0 ? (
                <p className="empty-message" style={{ padding: '12px 0' }}>Tranzaksiyalar yo'q</p>
              ) : (
                <div style={{ overflowX: 'auto' }}>
                  <table className="data-table" style={{ fontSize: 12.5 }}>
                    <thead>
                      <tr>
                        <th>Sana</th>
                        <th>Tur</th>
                        <th>Mahsulot</th>
                        <th className="text-right">Miqdor</th>
                        <th className="text-right">Summa</th>
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
                            {t.quantity > 0 ? `${formatNumber(t.quantity)} L` : '—'}
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
                Yopish
              </button>
            </div>
          </>
        ) : (
          <p className="empty-message">Ma'lumot topilmadi</p>
        )}
      </Modal>
    </div>
  );
}