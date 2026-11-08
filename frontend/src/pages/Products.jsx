/**
 * Products page — full CRUD with modal form.
 * All UI labels in Uzbek.
 */
import { useState, useEffect } from 'react';
import { getProducts, createProduct, updateProduct, toggleProduct } from '../api/products';
import { formatDateTime } from '../utils/formatters';
import Modal from '../components/Modal';

export default function Products() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingProduct, setEditingProduct] = useState(null);
  const [form, setForm] = useState({ name: '', note: '' });
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);

  const fetchProducts = async () => {
    try {
      const res = await getProducts();
      setProducts(res.data.items);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchProducts(); }, []);

  const openCreateModal = () => {
    setEditingProduct(null);
    setForm({ name: '', note: '' });
    setError('');
    setModalOpen(true);
  };

  const openEditModal = (product) => {
    setEditingProduct(product);
    setForm({ name: product.name, note: product.note || '' });
    setError('');
    setModalOpen(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSaving(true);
    try {
      if (editingProduct) {
        await updateProduct(editingProduct.id, form);
      } else {
        await createProduct(form);
      }
      setModalOpen(false);
      fetchProducts();
    } catch (err) {
      setError(
        err.response?.data?.detail || "Хатолик юз берди"
      );
    } finally {
      setSaving(false);
    }
  };

  const handleToggle = async (product) => {
    try {
      await toggleProduct(product.id);
      fetchProducts();
    } catch (err) {
      console.error(err);
    }
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
        <h1 className="page-title">Маҳсулотлар</h1>
        <button className="write-action btn btn--primary" onClick={openCreateModal}>
          + Янги маҳсулот
        </button>
      </div>

      <div className="card">
        <div className="table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>#</th>
                <th>Номи</th>
                <th>Бирлик</th>
                <th>Ҳолат</th>
                <th>Изоҳ</th>
                <th>Яратилган</th>
                <th>Амаллар</th>
              </tr>
            </thead>
            <tbody>
              {products.length === 0 ? (
                <tr>
                  <td colSpan={7}>
                    <p className="empty-message">Маҳсулотлар йўқ</p>
                  </td>
                </tr>
              ) : (
                products.map((p, idx) => (
                  <tr key={p.id} className={!p.is_active ? 'row-inactive' : ''}>
                    <td>{idx + 1}</td>
                    <td className="font-medium">{p.name}</td>
                    <td>{p.unit === 'liter' ? 'Литр' : p.unit}</td>
                    <td>
                      <span className={`badge badge--${p.is_active ? 'active' : 'cancelled'}`}>
                        {p.is_active ? 'Фаол' : 'Нофаол'}
                      </span>
                    </td>
                    <td>{p.note || '—'}</td>
                    <td>{formatDateTime(p.created_at)}</td>
                    <td>
                      <div className="action-buttons">
                        <button
                          className="write-action btn btn--outline btn--sm"
                          onClick={() => openEditModal(p)}
                        >
                          Таҳрирлаш
                        </button>
                        <button
                          className={"write-action " + `btn btn--sm ${p.is_active ? 'btn--danger-outline' : 'btn--success-outline'}`}
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

      {/* Create/Edit Modal */}
      <Modal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        title={editingProduct ? "Маҳсулотни таҳрирлаш" : "Янги маҳсулот"}
      >
        <form onSubmit={handleSubmit}>
          {error && <div className="alert alert--error">{error}</div>}
          <div className="form-group">
            <label htmlFor="product-name">Номи *</label>
            <input
              id="product-name"
              type="text"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              placeholder="Масалан: AI-95"
              required
            />
          </div>
          <div className="form-group">
            <label htmlFor="product-note">Изоҳ</label>
            <textarea
              id="product-note"
              value={form.note}
              onChange={(e) => setForm({ ...form, note: e.target.value })}
              placeholder="Қўшимча маълумот..."
              rows={3}
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
    </div>
  );
}
