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
        err.response?.data?.detail || "Xatolik yuz berdi"
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
        <h1 className="page-title">Mahsulotlar</h1>
        <button className="btn btn--primary" onClick={openCreateModal}>
          + Yangi mahsulot
        </button>
      </div>

      <div className="card">
        <div className="table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>#</th>
                <th>Nomi</th>
                <th>Birlik</th>
                <th>Holat</th>
                <th>Izoh</th>
                <th>Yaratilgan</th>
                <th>Amallar</th>
              </tr>
            </thead>
            <tbody>
              {products.length === 0 ? (
                <tr>
                  <td colSpan={7}>
                    <p className="empty-message">Mahsulotlar yo'q</p>
                  </td>
                </tr>
              ) : (
                products.map((p, idx) => (
                  <tr key={p.id} className={!p.is_active ? 'row-inactive' : ''}>
                    <td>{idx + 1}</td>
                    <td className="font-medium">{p.name}</td>
                    <td>{p.unit === 'liter' ? 'Litr' : p.unit}</td>
                    <td>
                      <span className={`badge badge--${p.is_active ? 'active' : 'cancelled'}`}>
                        {p.is_active ? 'Faol' : 'Nofaol'}
                      </span>
                    </td>
                    <td>{p.note || '—'}</td>
                    <td>{formatDateTime(p.created_at)}</td>
                    <td>
                      <div className="action-buttons">
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

      {/* Create/Edit Modal */}
      <Modal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        title={editingProduct ? "Mahsulotni tahrirlash" : "Yangi mahsulot"}
      >
        <form onSubmit={handleSubmit}>
          {error && <div className="alert alert--error">{error}</div>}
          <div className="form-group">
            <label htmlFor="product-name">Nomi *</label>
            <input
              id="product-name"
              type="text"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              placeholder="Masalan: AI-95"
              required
            />
          </div>
          <div className="form-group">
            <label htmlFor="product-note">Izoh</label>
            <textarea
              id="product-note"
              value={form.note}
              onChange={(e) => setForm({ ...form, note: e.target.value })}
              placeholder="Qo'shimcha ma'lumot..."
              rows={3}
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
