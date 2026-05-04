/**
 * Inventory (Ombor) page.
 * All UI labels in Uzbek.
 */
import { useState, useEffect } from 'react';
import { getInventoryBatches, getInventorySummary } from '../api/inventory';
import { formatDateTime, formatCurrency, formatNumber } from '../utils/formatters';
import { downloadExcel } from '../utils/excelDownload';

export default function Inventory() {
  const [batches, setBatches] = useState([]);
  const [summary, setSummary] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('active');

  const fetchData = async () => {
    try {
      setLoading(true);
      const [batchesRes, summaryRes] = await Promise.all([
        getInventoryBatches(statusFilter || undefined),
        getInventorySummary()
      ]);
      setBatches(batchesRes.data.items);
      setSummary(summaryRes.data.items);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, [statusFilter]);

  if (loading && batches.length === 0) {
    return (
      <div className="page-loading">
        <div className="loading-spinner" />
      </div>
    );
  }

  // Calculate totals for summary cards
  const totalLiters = summary.reduce((acc, curr) => acc + curr.total_quantity_liters, 0);
  const totalValue = summary.reduce((acc, curr) => acc + curr.total_cost, 0);

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Ombor qoldig'i</h1>
        <button
          className="btn btn-secondary"
          onClick={() => downloadExcel('inventory', {}, 'natural_oil_inventory.xlsx')}
        >
          ⬇ Excel
        </button>
      </div>

      {/* Summary Stats */}
      <div className="stat-grid">
        <div className="stat-card stat-card--info">
          <div className="stat-card-label">Jami mahsulot hajmi (Litr)</div>
          <div className="stat-card-value">{formatNumber(totalLiters)} L</div>
        </div>
        <div className="stat-card stat-card--success">
          <div className="stat-card-label">Jami ombor qiymati (UZS)</div>
          <div className="stat-card-value">{formatCurrency(totalValue)}</div>
        </div>
      </div>

      {/* Summary Table */}
      <div className="card" style={{ marginBottom: '32px' }}>
        <h2 className="card-title">Mahsulotlar bo'yicha qoldiq</h2>
        <div className="table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>Mahsulot</th>
                <th className="text-right">Umumiy miqdor (L)</th>
                <th className="text-right">O'rtacha narx (UZS)</th>
                <th className="text-right">Umumiy qiymat (UZS)</th>
              </tr>
            </thead>
            <tbody>
              {summary.length === 0 ? (
                <tr>
                  <td colSpan={4}>
                    <p className="empty-message">Omborda mahsulot yo'q</p>
                  </td>
                </tr>
              ) : (
                summary.map(s => (
                  <tr key={s.product_id}>
                    <td className="font-medium">{s.product_name}</td>
                    <td className="text-right">{formatNumber(s.total_quantity_liters)}</td>
                    <td className="text-right">{formatCurrency(s.average_price_per_liter)}</td>
                    <td className="text-right font-medium">{formatCurrency(s.total_cost)}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      <div className="page-header">
        <h2 className="card-title" style={{ marginBottom: 0 }}>Partiyalar (Batch) tarixi</h2>

        <div className="filter-group" style={{ background: 'var(--bg-card)', padding: '8px 16px', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
          <label style={{ marginBottom: 0 }}>Holat:</label>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            style={{ border: 'none', background: 'transparent' }}
          >
            <option value="">Barchasi</option>
            <option value="active">Faol</option>
            <option value="finished">Tugagan</option>
          </select>
        </div>
      </div>

      {/* Batches Table */}
      <div className="card">
        <div className="table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>Sana</th>
                <th>Mahsulot</th>
                <th>Yetkazib beruvchi</th>
                <th className="text-right">Narx (UZS)</th>
                <th className="text-right">Dastlabki (L)</th>
                <th className="text-right">Qoldiq (L)</th>
                <th className="text-right">Qoldiq qiymati</th>
                <th>Holat</th>
              </tr>
            </thead>
            <tbody>
              {batches.length === 0 ? (
                <tr>
                  <td colSpan={8}>
                    <p className="empty-message">Partiyalar topilmadi</p>
                  </td>
                </tr>
              ) : (
                batches.map((b) => (
                  <tr key={b.id} className={b.status === 'finished' ? 'row-inactive' : ''}>
                    <td>{formatDateTime(b.created_at)}</td>
                    <td className="font-medium">{b.product.name}</td>
                    <td>{b.supplier.name}</td>
                    <td className="text-right">{formatCurrency(b.purchase_price_per_liter)}</td>
                    <td className="text-right">{formatNumber(b.initial_quantity_liters)}</td>
                    <td className="text-right font-medium">{formatNumber(b.remaining_quantity_liters)}</td>
                    <td className="text-right">
                      {formatCurrency(b.remaining_quantity_liters * b.purchase_price_per_liter)}
                    </td>
                    <td>
                      <span className={`badge badge--${b.status === 'active' ? 'active' : 'closed'}`}>
                        {b.status === 'active' ? 'Faol' : 'Tugagan'}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}