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
        <h1 className="page-title">Омбор қолдиғи</h1>
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
          <div className="stat-card-label">Жами маҳсулот ҳажми (Литр)</div>
          <div className="stat-card-value">{formatNumber(totalLiters)} Л</div>
        </div>
        <div className="stat-card stat-card--success">
          <div className="stat-card-label">Жами омбор қиймати (UZS)</div>
          <div className="stat-card-value">{formatCurrency(totalValue)}</div>
        </div>
      </div>

      {/* Summary Table */}
      <div className="card" style={{ marginBottom: '32px' }}>
        <h2 className="card-title">Маҳсулотлар бўйича қолдиқ</h2>
        <div className="table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>Маҳсулот</th>
                <th className="text-right">Умумий миқдор (Л)</th>
                <th className="text-right">Ўртача нарх (UZS)</th>
                <th className="text-right">Умумий қиймат (UZS)</th>
              </tr>
            </thead>
            <tbody>
              {summary.length === 0 ? (
                <tr>
                  <td colSpan={4}>
                    <p className="empty-message">Омборда маҳсулот йўқ</p>
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
        <h2 className="card-title" style={{ marginBottom: 0 }}>Партиялар тарихи</h2>

        <div className="filter-group" style={{ background: 'var(--bg-card)', padding: '8px 16px', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
          <label style={{ marginBottom: 0 }}>Ҳолат:</label>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            style={{ border: 'none', background: 'transparent' }}
          >
            <option value="">Барчаси</option>
            <option value="active">Фаол</option>
            <option value="finished">Тугаган</option>
          </select>
        </div>
      </div>

      {/* Batches Table */}
      <div className="card">
        <div className="table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>Сана</th>
                <th>Маҳсулот</th>
                <th>Етказиб берувчи</th>
                <th className="text-right">Нарх (UZS)</th>
                <th className="text-right">Дастлабки (Л)</th>
                <th className="text-right">Қолдиқ (Л)</th>
                <th className="text-right">Қолдиқ қиймати</th>
                <th>Ҳолат</th>
              </tr>
            </thead>
            <tbody>
              {batches.length === 0 ? (
                <tr>
                  <td colSpan={8}>
                    <p className="empty-message">Партиялар топилмади</p>
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
                        {b.status === 'active' ? 'Фаол' : 'Тугаган'}
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