/**
 * Ҳисобот — таблар билан тафсилий ҳисоботлар.
 * Ҳар бир таб /api/reports/tabs/<tab> дан маълумот олади.
 */
import { useEffect, useMemo, useState } from 'react';
import {
  ArrowLeftRight, Wallet, TrendingUp, Receipt, Upload, Download, Users, Warehouse, RefreshCw, BarChart3,
  Trophy, Coins, TrendingDown, AlertTriangle, ArrowUpRight, ArrowDownRight,
} from 'lucide-react';
import client from '../api/client';
import { downloadExcel, downloadFile } from '../utils/excelDownload';

const money = (n = 0) => new Intl.NumberFormat('uz-UZ').format(Math.round(n || 0)) + ' сўм';
const num = (n = 0, d = 1) => new Intl.NumberFormat('uz-UZ', { maximumFractionDigits: d }).format(n || 0);
const liters = (n = 0) => num(n, 1) + ' л';
const pct = (n = 0) => num(n, 1) + '%';

const iso = (d) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
const PRESETS = [
  { key: 'today', label: 'Бугун', range: () => { const t = new Date(); return [t, t]; } },
  { key: 'yesterday', label: 'Кеча', range: () => { const t = new Date(); t.setDate(t.getDate() - 1); return [t, t]; } },
  { key: 'week', label: '7 кун', range: () => { const t = new Date(); const f = new Date(); f.setDate(t.getDate() - 6); return [f, t]; } },
  { key: 'month', label: 'Шу ой', range: () => { const t = new Date(); return [new Date(t.getFullYear(), t.getMonth(), 1), t]; } },
  { key: 'prev', label: 'Ўтган ой', range: () => { const t = new Date(); return [new Date(t.getFullYear(), t.getMonth() - 1, 1), new Date(t.getFullYear(), t.getMonth(), 0)]; } },
  { key: 'year', label: 'Шу йил', range: () => { const t = new Date(); return [new Date(t.getFullYear(), 0, 1), t]; } },
];

const TABS = [
  { key: 'transactions', label: 'Транзакциялар', icon: ArrowLeftRight },
  { key: 'cashflow', label: 'Кирим-чиқим', icon: Wallet },
  { key: 'profit', label: 'Фойда / зарар', icon: TrendingUp },
  { key: 'products', label: 'Маҳсулот статистикаси', icon: BarChart3 },
  { key: 'expenses', label: 'Харажатлар', icon: Receipt },
  { key: 'sales', label: 'Сотувлар', icon: Upload },
  { key: 'purchases', label: 'Приходлар', icon: Download },
  { key: 'debts', label: 'Қарздорлик', icon: Users },
  { key: 'inventory', label: 'Омбор', icon: Warehouse },
];

function getInitialTab() {
  try {
    const t = localStorage.getItem('reports-tab');
    if (TABS.some((x) => x.key === t)) return t;
  } catch { /* ignore */ }
  return 'transactions';
}

export default function Reports() {
  const [tab, setTab] = useState(getInitialTab);
  const [preset, setPreset] = useState('month');
  const initial = PRESETS.find((p) => p.key === 'month').range();
  const [dateFrom, setDateFrom] = useState(iso(initial[0]));
  const [dateTo, setDateTo] = useState(iso(initial[1]));
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [reloadKey, setReloadKey] = useState(0);
  // Транзакциялар таби филтрлари (Excel ҳам шунга қараб чиқади)
  const [txDir, setTxDir] = useState('');
  const [txPay, setTxPay] = useState('');
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    try { localStorage.setItem('reports-tab', tab); } catch { /* ignore */ }
  }, [tab]);

  useEffect(() => {
    let alive = true;
    setLoading(true);
    setError('');
    client.get(`/reports/tabs/${tab}`, { params: { date_from: dateFrom, date_to: dateTo } })
      .then((res) => { if (alive) setData({ tab, ...res.data }); })
      .catch((e) => { if (alive) setError(e.response?.data?.detail || 'Маълумот юкланмади'); })
      .finally(() => { if (alive) setLoading(false); });
    return () => { alive = false; };
  }, [tab, dateFrom, dateTo, reloadKey]);

  const applyPreset = (p) => {
    const [f, t] = p.range();
    setPreset(p.key);
    setDateFrom(iso(f));
    setDateTo(iso(t));
  };

  const ready = data && data.tab === tab;

  async function exportTab() {
    const params = { date_from: dateFrom, date_to: dateTo };
    if (tab === 'transactions') {
      if (txDir) params.direction = txDir;
      if (txPay) params.payment_type = txPay;
    }
    const suffix = tab === 'transactions' && txDir ? `_${txDir === 'income' ? 'kirim' : 'chiqim'}` : '';
    setExporting(true);
    await downloadFile(`/reports/tabs/${tab}/excel`, params, `natural_oil_${tab}${suffix}_${dateFrom}_${dateTo}.xlsx`);
    setExporting(false);
  }

  return (
    <div className="page reports-page">
      <div className="page-header">
        <h1 className="page-title">Ҳисобот</h1>
        <div className="action-buttons">
          <button className="btn btn-secondary" onClick={() => setReloadKey((k) => k + 1)}>
            <RefreshCw size={16} /> Янгилаш
          </button>
          <button
            className="btn btn-secondary"
            title="Барча бўлимлар битта файлда"
            onClick={() => downloadExcel('general-report', { date_from: dateFrom, date_to: dateTo }, `umumiy_hisobot_${dateFrom}_${dateTo}.xlsx`)}
          >
            ⬇ Умумий Excel
          </button>
          <button className="btn btn-primary" disabled={exporting} onClick={exportTab}>
            ⬇ {exporting ? 'Тайёрланмоқда...' : `Excel: ${TABS.find((t) => t.key === tab).label}`}
          </button>
        </div>
      </div>

      <div className="card report-filter">
        <div className="report-presets">
          {PRESETS.map((p) => (
            <button key={p.key} className={`chip ${preset === p.key ? 'chip--active' : ''}`} onClick={() => applyPreset(p)}>
              {p.label}
            </button>
          ))}
        </div>
        <div className="report-dates">
          <label>Дан<input type="date" value={dateFrom} onChange={(e) => { setPreset(''); setDateFrom(e.target.value); }} /></label>
          <label>Гача<input type="date" value={dateTo} onChange={(e) => { setPreset(''); setDateTo(e.target.value); }} /></label>
        </div>
      </div>

      <h2 className="report-section-title">Тафсилий ҳисоботлар</h2>
      <div className="card report-tabs">
        {TABS.map((t) => {
          const Icon = t.icon;
          return (
            <button key={t.key} className={`report-tab ${tab === t.key ? 'report-tab--active' : ''}`} onClick={() => setTab(t.key)}>
              <Icon size={17} strokeWidth={2.2} /> {t.label}
            </button>
          );
        })}
      </div>

      {error && <div className="alert alert--error">{error}</div>}
      {loading && !ready && <div className="card"><p className="empty-message">Юкланмоқда...</p></div>}
      {ready && (
        <div className={loading ? 'report-body report-body--loading' : 'report-body'}>
          {tab === 'transactions' && <TransactionsTab d={data} dir={txDir} setDir={setTxDir} pay={txPay} setPay={setTxPay} />}
          {tab === 'cashflow' && <CashflowTab d={data} />}
          {tab === 'profit' && <ProfitTab d={data} />}
          {tab === 'products' && <ProductStatsTab d={data} />}
          {tab === 'expenses' && <ExpensesTab d={data} />}
          {tab === 'sales' && <SalesTab d={data} />}
          {tab === 'purchases' && <PurchasesTab d={data} />}
          {tab === 'debts' && <DebtsTab d={data} />}
          {tab === 'inventory' && <InventoryTab d={data} />}
        </div>
      )}
    </div>
  );
}

/* ── Umumiy komponentlar ─────────────────────────────────────────────── */

function Kpis({ items }) {
  return (
    <div className="kpi-grid">
      {items.map((k) => (
        <div key={k.label} className={`kpi ${k.hero ? 'kpi--hero' : ''}`}>
          <div className="kpi-label">{k.label}</div>
          <div className={`kpi-value ${k.tone ? `kpi-value--${k.tone}` : ''}`}>{k.value}</div>
          {k.sub && <div className="kpi-sub">{k.sub}</div>}
        </div>
      ))}
    </div>
  );
}

function Table({ title, columns, rows, empty = 'Маълумот йўқ', footer }) {
  return (
    <div className="card">
      {title && <h3 className="card-title">{title}</h3>}
      {rows.length === 0 ? (
        <p className="empty-message">{empty}</p>
      ) : (
        <div className="table-wrapper">
          <table className="data-table">
            <thead>
              <tr>{columns.map((c) => <th key={c.key} className={c.right ? 'text-right' : ''}>{c.label}</th>)}</tr>
            </thead>
            <tbody>
              {rows.map((r, i) => (
                <tr key={r.id ?? `${r.name ?? r.product ?? r.category ?? r.date}-${i}`}>
                  {columns.map((c) => (
                    <td key={c.key} className={`${c.right ? 'text-right' : ''} ${c.tone ? c.tone(r) : ''}`}>
                      {c.render ? c.render(r) : r[c.key]}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
            {footer && (
              <tfoot>
                <tr>{columns.map((c) => <td key={c.key} className={c.right ? 'text-right' : ''}>{footer[c.key] ?? ''}</td>)}</tr>
              </tfoot>
            )}
          </table>
        </div>
      )}
    </div>
  );
}

function ShareBar({ value }) {
  return (
    <div className="share-bar"><i className="share-track"><span style={{ width: `${Math.min(100, Math.max(0, value))}%` }} /></i><em>{pct(value)}</em></div>
  );
}

const signTone = (v) => (v < 0 ? 'text-danger' : v > 0 ? 'text-success' : '');

/* ── Tablar ──────────────────────────────────────────────────────────── */

function TransactionsTab({ d, dir, setDir, pay, setPay }) {
  const rows = useMemo(
    () => d.rows.filter((r) => (!dir || r.direction === dir) && (!pay || r.payment_type === pay)),
    [d.rows, dir, pay],
  );
  return (
    <>
      <Kpis items={[
        { label: 'Жами кирим', value: money(d.totals.income), tone: 'green' },
        { label: 'Жами чиқим', value: money(d.totals.outgoing), tone: 'red' },
        { label: 'Соф пул оқими', value: money(d.totals.net), tone: d.totals.net < 0 ? 'red' : 'green', hero: true },
        { label: 'Операциялар сони', value: `${d.totals.count} та` },
      ]} />
      <div className="card report-subfilter">
        <div className="report-presets">
          {[['', 'Барчаси'], ['income', 'Кирим'], ['outgoing', 'Чиқим']].map(([k, l]) => (
            <button key={k} className={`chip ${dir === k ? 'chip--active' : ''}`} onClick={() => setDir(k)}>{l}</button>
          ))}
          <span className="chip-sep" />
          {[['', 'Ҳамма ҳисоб'], ['cash', 'Нақд'], ['bank_transfer', 'Перечисления']].map(([k, l]) => (
            <button key={k} className={`chip ${pay === k ? 'chip--active' : ''}`} onClick={() => setPay(k)}>{l}</button>
          ))}
        </div>
      </div>
      <Table
        title={`Транзакциялар (${rows.length} та)`}
        rows={rows}
        empty="Бу даврда транзакциялар йўқ"
        columns={[
          { key: 'datetime', label: 'Сана / вақт' },
          { key: 'type_label', label: 'Тур' },
          { key: 'partner', label: 'Ҳамкор' },
          { key: 'item', label: 'Маҳсулот / категория' },
          { key: 'payment_label', label: 'Ҳисоб' },
          {
            key: 'amount', label: 'Сумма', right: true,
            tone: (r) => (r.direction === 'income' ? 'text-success' : 'text-danger'),
            render: (r) => `${r.direction === 'income' ? '+' : '−'}${money(r.amount)}`,
          },
          { key: 'description', label: 'Изоҳ', render: (r) => <span className="cell-muted">{r.description}</span> },
        ]}
      />
    </>
  );
}

function CashflowTab({ d }) {
  return (
    <>
      <Kpis items={[
        { label: 'Давр боши қолдиғи', value: money(d.opening.total), sub: `Нақд ${money(d.opening.cash)} · Перечисления ${money(d.opening.bank_transfer)}` },
        { label: 'Кирим', value: money(d.totals.income), tone: 'green', sub: `Нақд ${money(d.totals.cash_in)} · Банк ${money(d.totals.bank_in)}` },
        { label: 'Чиқим', value: money(d.totals.outgoing), tone: 'red', sub: `Нақд ${money(d.totals.cash_out)} · Банк ${money(d.totals.bank_out)}` },
        { label: 'Давр охири қолдиғи', value: money(d.closing.total), hero: true, tone: d.closing.total < 0 ? 'red' : '', sub: `Нақд ${money(d.closing.cash)} · Перечисления ${money(d.closing.bank_transfer)}` },
      ]} />
      <Table
        title="Кунлар бўйича"
        rows={d.rows}
        empty="Бу даврда пул ҳаракати йўқ"
        columns={[
          { key: 'date', label: 'Сана' },
          { key: 'cash_in', label: 'Нақд кирим', right: true, render: (r) => money(r.cash_in), tone: () => 'text-success' },
          { key: 'cash_out', label: 'Нақд чиқим', right: true, render: (r) => money(r.cash_out), tone: () => 'text-danger' },
          { key: 'bank_in', label: 'Банк кирим', right: true, render: (r) => money(r.bank_in), tone: () => 'text-success' },
          { key: 'bank_out', label: 'Банк чиқим', right: true, render: (r) => money(r.bank_out), tone: () => 'text-danger' },
          { key: 'net', label: 'Кунлик натижа', right: true, render: (r) => money(r.net), tone: (r) => signTone(r.net) },
          { key: 'closing_total', label: 'Кун охири қолдиқ', right: true, render: (r) => <b>{money(r.closing_total)}</b> },
        ]}
      />
      <Table
        title="Операция турлари бўйича"
        rows={d.by_type}
        columns={[
          { key: 'label', label: 'Тур' },
          { key: 'income', label: 'Кирим', right: true, render: (r) => money(r.income), tone: () => 'text-success' },
          { key: 'outgoing', label: 'Чиқим', right: true, render: (r) => money(r.outgoing), tone: () => 'text-danger' },
        ]}
      />
    </>
  );
}

function ProfitTab({ d }) {
  const t = d.totals;
  return (
    <>
      <Kpis items={[
        { label: 'Жами савдо', value: money(t.revenue), sub: `${t.sale_count} та сотув · ${liters(t.liters)}` },
        { label: 'Ёқилғи таннархи', value: money(t.cost) },
        { label: 'Ялпи фойда', value: money(t.gross_profit), tone: t.gross_profit < 0 ? 'red' : 'green', sub: `Маржа ${pct(t.gross_margin)} · 1 л ${money(t.profit_per_liter)}` },
        { label: 'Харажатлар', value: money(t.expenses), tone: 'red' },
        { label: t.net_profit < 0 ? 'Соф зарар' : 'Соф фойда', value: money(t.net_profit), hero: true, tone: t.net_profit < 0 ? 'red' : '', sub: `Соф маржа ${pct(t.net_margin)}` },
      ]} />
      <div className="profit-formula card">
        <span>Савдо <b>{money(t.revenue)}</b></span>
        <i>−</i><span>Таннарх <b>{money(t.cost)}</b></span>
        <i>=</i><span>Ялпи фойда <b>{money(t.gross_profit)}</b></span>
        <i>−</i><span>Харажат <b>{money(t.expenses)}</b></span>
        <i>=</i><span className="profit-formula-result">Соф натижа <b>{money(t.net_profit)}</b></span>
      </div>
      <Table
        title="Маҳсулотлар бўйича"
        rows={d.by_product}
        empty="Бу даврда сотув йўқ"
        columns={[
          { key: 'product', label: 'Маҳсулот', render: (r) => <b>{r.product}</b> },
          { key: 'liters', label: 'Сотилди', right: true, render: (r) => liters(r.liters) },
          { key: 'avg_cost_price', label: 'Ўрт. кирим нархи', right: true, render: (r) => money(r.avg_cost_price) },
          { key: 'avg_sale_price', label: 'Ўрт. сотиш нархи', right: true, render: (r) => money(r.avg_sale_price) },
          { key: 'revenue', label: 'Савдо', right: true, render: (r) => money(r.revenue) },
          { key: 'profit', label: 'Фойда', right: true, render: (r) => money(r.profit), tone: (r) => signTone(r.profit) },
          { key: 'margin', label: 'Маржа', right: true, render: (r) => pct(r.margin) },
        ]}
      />
      <Table
        title="Кунлар бўйича"
        rows={d.by_day}
        columns={[
          { key: 'date', label: 'Сана' },
          { key: 'revenue', label: 'Савдо', right: true, render: (r) => money(r.revenue) },
          { key: 'gross', label: 'Ялпи фойда', right: true, render: (r) => money(r.gross), tone: (r) => signTone(r.gross) },
          { key: 'expenses', label: 'Харажат', right: true, render: (r) => money(r.expenses), tone: () => 'text-danger' },
          { key: 'net', label: 'Соф натижа', right: true, render: (r) => <b>{money(r.net)}</b>, tone: (r) => signTone(r.net) },
        ]}
      />
      {d.loss_sales.length > 0 && (
        <Table
          title={`⚠ Зарар билан сотилганлар (${d.loss_sales.length} та)`}
          rows={d.loss_sales}
          columns={[
            { key: 'date', label: 'Сана' },
            { key: 'customer', label: 'Мижоз' },
            { key: 'product', label: 'Маҳсулот' },
            { key: 'liters', label: 'Миқдор', right: true, render: (r) => liters(r.liters) },
            { key: 'cost_price', label: 'Кирим нархи', right: true, render: (r) => money(r.cost_price) },
            { key: 'sale_price', label: 'Сотиш нархи', right: true, render: (r) => money(r.sale_price) },
            { key: 'profit', label: 'Зарар', right: true, render: (r) => money(r.profit), tone: () => 'text-danger' },
          ]}
        />
      )}
    </>
  );
}

function ExpensesTab({ d }) {
  return (
    <>
      <Kpis items={[
        { label: 'Жами харажат', value: money(d.totals.amount), tone: 'red', hero: true, sub: `${d.totals.count} та операция` },
        { label: 'Нақддан', value: money(d.totals.cash) },
        { label: 'Перечислениядан', value: money(d.totals.bank_transfer) },
        { label: 'Кунига ўртача', value: money(d.totals.daily_avg) },
      ]} />
      <Table
        title="Категориялар бўйича"
        rows={d.by_category}
        empty="Бу даврда харажат йўқ"
        columns={[
          { key: 'category', label: 'Категория', render: (r) => <b>{r.category}</b> },
          { key: 'count', label: 'Сони', right: true },
          { key: 'amount', label: 'Сумма', right: true, render: (r) => money(r.amount), tone: () => 'text-danger' },
          { key: 'share', label: 'Улуши', render: (r) => <ShareBar value={r.share} /> },
        ]}
      />
      <Table
        title="Барча харажатлар"
        rows={d.rows}
        columns={[
          { key: 'date', label: 'Сана' },
          { key: 'category', label: 'Категория' },
          { key: 'payment_label', label: 'Ҳисоб' },
          { key: 'amount', label: 'Сумма', right: true, render: (r) => money(r.amount), tone: () => 'text-danger' },
          { key: 'note', label: 'Изоҳ', render: (r) => <span className="cell-muted">{r.note || '—'}</span> },
        ]}
      />
    </>
  );
}

const groupColumns = (nameLabel, extra = []) => [
  { key: 'name', label: nameLabel, render: (r) => <b>{r.name}</b> },
  { key: 'count', label: 'Сони', right: true },
  { key: 'liters', label: 'Миқдор', right: true, render: (r) => liters(r.liters) },
  { key: 'amount', label: 'Сумма', right: true, render: (r) => money(r.amount) },
  { key: 'paid', label: 'Тўланган', right: true, render: (r) => money(r.paid), tone: () => 'text-success' },
  { key: 'debt', label: 'Қарз', right: true, render: (r) => money(r.debt), tone: (r) => (r.debt > 0 ? 'text-danger' : '') },
  ...extra,
];

function SalesTab({ d }) {
  const t = d.totals;
  return (
    <>
      <Kpis items={[
        { label: 'Сотув суммаси', value: money(t.amount), hero: true, sub: `${t.count} та сотув` },
        { label: 'Сотилган ёқилғи', value: liters(t.liters), sub: `Ўртача нарх ${money(t.avg_price)}` },
        { label: 'Тўланган', value: money(t.paid), tone: 'green' },
        { label: 'Қарзга кетди', value: money(t.debt), tone: 'red' },
        { label: 'Фойда', value: money(t.profit), tone: t.profit < 0 ? 'red' : 'green' },
      ]} />
      <Table title="Маҳсулотлар бўйича" rows={d.by_product} empty="Бу даврда сотув йўқ"
        columns={groupColumns('Маҳсулот', [{ key: 'profit', label: 'Фойда', right: true, render: (r) => money(r.profit), tone: (r) => signTone(r.profit) }])} />
      <Table title="Мижозлар бўйича" rows={d.by_customer}
        columns={groupColumns('Мижоз', [{ key: 'profit', label: 'Фойда', right: true, render: (r) => money(r.profit), tone: (r) => signTone(r.profit) }])} />
      <Table
        title="Барча сотувлар"
        rows={d.rows}
        columns={[
          { key: 'date', label: 'Сана' },
          { key: 'customer', label: 'Мижоз' },
          { key: 'product', label: 'Маҳсулот' },
          { key: 'liters', label: 'Миқдор', right: true, render: (r) => liters(r.liters) },
          { key: 'price', label: 'Нарх', right: true, render: (r) => money(r.price) },
          { key: 'amount', label: 'Сумма', right: true, render: (r) => money(r.amount) },
          { key: 'debt', label: 'Қарз', right: true, render: (r) => money(r.debt), tone: (r) => (r.debt > 0 ? 'text-danger' : '') },
          { key: 'profit', label: 'Фойда', right: true, render: (r) => money(r.profit), tone: (r) => signTone(r.profit) },
        ]}
      />
    </>
  );
}

function PurchasesTab({ d }) {
  const t = d.totals;
  const avg = { key: 'avg_price', label: 'Ўрт. нарх', right: true, render: (r) => money(r.avg_price) };
  return (
    <>
      <Kpis items={[
        { label: 'Приход суммаси', value: money(t.amount), hero: true, sub: `${t.count} та приход` },
        { label: 'Келган ёқилғи', value: liters(t.liters), sub: `Ўртача нарх ${money(t.avg_price)}` },
        { label: 'Тўланган', value: money(t.paid), tone: 'green' },
        { label: 'Қарзга олинди', value: money(t.debt), tone: 'red' },
      ]} />
      <Table title="Маҳсулотлар бўйича" rows={d.by_product} empty="Бу даврда приход йўқ" columns={groupColumns('Маҳсулот', [avg])} />
      <Table title="Етказиб берувчилар бўйича" rows={d.by_supplier} columns={groupColumns('Етказиб берувчи', [avg])} />
      <Table
        title="Барча приходлар"
        rows={d.rows}
        columns={[
          { key: 'date', label: 'Сана' },
          { key: 'supplier', label: 'Етказиб берувчи' },
          { key: 'product', label: 'Маҳсулот' },
          { key: 'liters', label: 'Миқдор', right: true, render: (r) => liters(r.liters) },
          { key: 'price', label: '1 л нархи', right: true, render: (r) => money(r.price) },
          { key: 'amount', label: 'Сумма', right: true, render: (r) => money(r.amount) },
          { key: 'paid', label: 'Тўланган', right: true, render: (r) => money(r.paid), tone: () => 'text-success' },
          { key: 'debt', label: 'Қарз', right: true, render: (r) => money(r.debt), tone: (r) => (r.debt > 0 ? 'text-danger' : '') },
        ]}
      />
    </>
  );
}

function DebtsTab({ d }) {
  const t = d.totals;
  const cols = (who) => [
    { key: 'name', label: who, render: (r) => <><b>{r.name}</b>{r.phone ? <div className="cell-muted">{r.phone}</div> : null}</> },
    { key: 'count', label: 'Қарзлар', right: true },
    { key: 'original', label: 'Дастлабки', right: true, render: (r) => money(r.original) },
    { key: 'paid', label: 'Тўланган', right: true, render: (r) => money(r.paid), tone: () => 'text-success' },
    { key: 'remaining', label: 'Қолган', right: true, render: (r) => <b>{money(r.remaining)}</b>, tone: () => 'text-danger' },
    { key: 'oldest_date', label: 'Энг эски' },
    { key: 'days', label: 'Кун', right: true, render: (r) => <span className={`age-badge ${r.days > 30 ? 'age-badge--old' : r.days > 7 ? 'age-badge--mid' : ''}`}>{r.days} кун</span> },
  ];
  return (
    <>
      <Kpis items={[
        { label: 'Мижозлар бизга қарз', value: money(t.customer_total), tone: 'green', sub: `Даврда: +${money(t.period_new_customer)} янги · ${money(t.period_received)} қайтарилди` },
        { label: 'Бизнинг қарзимиз', value: money(t.supplier_total), tone: 'red', sub: `Даврда: +${money(t.period_new_supplier)} янги · ${money(t.period_paid_out)} тўладик` },
        { label: 'Соф қарз ҳолати', value: money(t.net), hero: true, tone: t.net < 0 ? 'red' : '', sub: t.net < 0 ? 'Биз кўпроқ қарздормиз' : 'Бизга кўпроқ қарздор' },
      ]} />
      <Table title="Мижозлар қарзи (ҳозирги ҳолат)" rows={d.customers} empty="Мижозлардан қарз йўқ" columns={cols('Мижоз')} />
      <Table title="Етказиб берувчиларга қарзимиз (ҳозирги ҳолат)" rows={d.suppliers} empty="Қарзимиз йўқ" columns={cols('Етказиб берувчи')} />
    </>
  );
}

function InventoryTab({ d }) {
  const t = d.totals;
  return (
    <>
      <Kpis items={[
        { label: 'Омбордаги ёқилғи', value: liters(t.liters), hero: true, sub: `${t.batches} та фаол партия` },
        { label: 'Омбор қиймати (таннархда)', value: money(t.value) },
        { label: 'Даврда кирди', value: liters(t.period_in), tone: 'green' },
        { label: 'Даврда чиқди', value: liters(t.period_out), tone: 'red' },
      ]} />
      <Table
        title="Маҳсулотлар бўйича"
        rows={d.by_product}
        empty="Омбор бўш"
        columns={[
          { key: 'product', label: 'Маҳсулот', render: (r) => <b>{r.product}</b> },
          { key: 'liters', label: 'Қолдиқ', right: true, render: (r) => <b>{liters(r.liters)}</b> },
          { key: 'avg_cost', label: 'Ўрт. таннарх', right: true, render: (r) => money(r.avg_cost) },
          { key: 'value', label: 'Қиймати', right: true, render: (r) => money(r.value) },
          { key: 'period_in', label: 'Даврда кирди', right: true, render: (r) => liters(r.period_in), tone: () => 'text-success' },
          { key: 'period_out', label: 'Даврда чиқди', right: true, render: (r) => liters(r.period_out), tone: () => 'text-danger' },
          { key: 'batches', label: 'Партиялар', right: true },
        ]}
      />
      <Table
        title="Фаол партиялар"
        rows={d.batches}
        columns={[
          { key: 'id', label: '№', render: (r) => `#${r.id}` },
          { key: 'created', label: 'Келган' },
          { key: 'product', label: 'Маҳсулот' },
          { key: 'supplier', label: 'Етказиб берувчи' },
          { key: 'price', label: '1 л нархи', right: true, render: (r) => money(r.price) },
          { key: 'remaining', label: 'Қолдиқ', right: true, render: (r) => `${liters(r.remaining)} / ${liters(r.initial)}` },
          { key: 'used_pct', label: 'Сотилди', render: (r) => <ShareBar value={r.used_pct} /> },
          { key: 'value', label: 'Қиймати', right: true, render: (r) => money(r.value) },
        ]}
      />
    </>
  );
}

/* ── Маҳсулот статистикаси ───────────────────────────────────────────── */

function Growth({ value }) {
  if (value === null || value === undefined) return <span className="cell-muted">—</span>;
  const up = value >= 0;
  const Icon = up ? ArrowUpRight : ArrowDownRight;
  return (
    <span className={`growth ${up ? 'growth--up' : 'growth--down'}`}>
      <Icon size={14} strokeWidth={2.6} /> {num(Math.abs(value), 1)}%
    </span>
  );
}

function Highlight({ icon: Icon, title, item, metric, tone }) {
  return (
    <div className={`highlight highlight--${tone}`}>
      <div className="highlight-head"><span className="highlight-icon"><Icon size={18} strokeWidth={2.4} /></span>{title}</div>
      {item ? (
        <>
          <div className="highlight-product">{item.product}</div>
          <div className="highlight-metric">{metric(item)}</div>
          <div className="highlight-sub">{liters(item.liters)} · фойда {money(item.profit)} · маржа {pct(item.margin)}</div>
        </>
      ) : (
        <div className="highlight-empty">Солиштириш учун камида 2 та маҳсулот сотилган бўлиши керак</div>
      )}
    </div>
  );
}

const GRAIN_LABEL = { day: 'кунлар', week: 'ҳафталар', month: 'ойлар' };
const METRICS = [
  { key: 'liters', label: 'Литр', fmt: (v) => liters(v) },
  { key: 'profit', label: 'Фойда', fmt: (v) => money(v) },
  { key: 'revenue', label: 'Савдо', fmt: (v) => money(v) },
];

function BarChart({ labels, values, fmt, title }) {
  const [hover, setHover] = useState(null);
  const W = 900, H = 260, padL = 8, padR = 8, padT = 16, padB = 28;
  const max = Math.max(0, ...values);
  const min = Math.min(0, ...values);
  const span = max - min || 1;
  const innerW = W - padL - padR, innerH = H - padT - padB;
  const step = innerW / Math.max(1, values.length);
  const barW = Math.max(3, Math.min(42, step - 4));
  const y = (v) => padT + ((max - v) / span) * innerH;
  const base = y(0);
  const every = Math.ceil(values.length / 12);
  const hasData = values.some((v) => v !== 0);
  return (
    <div className="chart" onMouseLeave={() => setHover(null)}>
      <div className="chart-title">{title}</div>
      {!hasData ? <p className="empty-message">Бу даврда сотув йўқ</p> : (
        <div className="chart-box">
          <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" role="img" aria-label={title}>
            {[0.25, 0.5, 0.75].map((f) => (
              <line key={f} x1={padL} x2={W - padR} y1={padT + innerH * f} y2={padT + innerH * f} className="chart-grid" />
            ))}
            <line x1={padL} x2={W - padR} y1={base} y2={base} className="chart-axis" />
            {values.map((v, i) => {
              const x = padL + i * step + (step - barW) / 2;
              const top = Math.min(y(v), base);
              const h = Math.max(v === 0 ? 0 : 2, Math.abs(base - y(v)));
              return (
                <g key={i} onMouseEnter={() => setHover(i)}>
                  <rect x={padL + i * step} y={padT} width={step} height={innerH} fill="transparent" />
                  <rect x={x} y={top} width={barW} height={h} rx={Math.min(4, barW / 2)}
                    className={`chart-bar ${v < 0 ? 'chart-bar--neg' : ''} ${hover === i ? 'chart-bar--hover' : ''}`} />
                </g>
              );
            })}
          </svg>
          <div className="chart-xlabels">
            {labels.map((l, i) => <span key={i} style={{ visibility: i % every === 0 ? 'visible' : 'hidden' }}>{l}</span>)}
          </div>
          {hover !== null && (
            <div className="chart-tip" style={{ left: `${((hover + 0.5) / values.length) * 100}%` }}>
              <b>{labels[hover]}</b>
              <span>{fmt(values[hover])}</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function ProductStatsTab({ d }) {
  const h = d.highlights;
  const [productId, setProductId] = useState('all');
  const [metric, setMetric] = useState('liters');
  const m = METRICS.find((x) => x.key === metric);
  const sold = d.ranking.filter((r) => r.count > 0);
  const series = d.timeline.series[productId] || [];
  const values = d.timeline.labels.map((_, i) => (series[i] ? series[i][metric] : 0));
  const productName = productId === 'all' ? 'Барча маҳсулотлар' : d.ranking.find((r) => String(r.product_id) === productId)?.product;

  return (
    <>
      <div className="highlight-grid">
        <Highlight icon={Trophy} tone="gold" title="Энг кўп сотилган" item={h.most_sold} metric={(i) => liters(i.liters)} />
        <Highlight icon={Coins} tone="green" title="Энг кўп фойда келтирган" item={h.most_profit} metric={(i) => money(i.profit)} />
        <Highlight icon={TrendingDown} tone="gray" title="Энг кам сотилган" item={h.least_sold} metric={(i) => liters(i.liters)} />
        <Highlight icon={AlertTriangle} tone="red" title="Энг кам фойда келтирган" item={h.least_profit} metric={(i) => money(i.profit)} />
      </div>
      {d.unsold.length > 0 && (
        <div className="alert alert--warning-soft">Бу даврда умуман сотилмаган: <b>{d.unsold.join(', ')}</b></div>
      )}

      <div className="card">
        <div className="chart-controls">
          <div className="report-presets">
            <button className={`chip ${productId === 'all' ? 'chip--active' : ''}`} onClick={() => setProductId('all')}>Барчаси</button>
            {sold.map((r) => (
              <button key={r.product_id} className={`chip ${productId === String(r.product_id) ? 'chip--active' : ''}`}
                onClick={() => setProductId(String(r.product_id))}>{r.product}</button>
            ))}
          </div>
          <div className="segmented">
            {METRICS.map((x) => (
              <button key={x.key} className={metric === x.key ? 'is-active' : ''} onClick={() => setMetric(x.key)}>{x.label}</button>
            ))}
          </div>
        </div>
        <BarChart
          title={`${productName} — ${m.label.toLowerCase()}, ${GRAIN_LABEL[d.period.grain]} бўйича`}
          labels={d.timeline.labels}
          values={values}
          fmt={m.fmt}
        />
      </div>

      <Table
        title="Маҳсулотлар рейтинги"
        rows={d.ranking}
        empty="Маҳсулотлар йўқ"
        columns={[
          { key: 'rank', label: '№', render: (r) => <span className="rank">{d.ranking.indexOf(r) + 1}</span> },
          { key: 'product', label: 'Маҳсулот', render: (r) => <b>{r.product}</b> },
          { key: 'liters', label: 'Сотилди', right: true, render: (r) => liters(r.liters) },
          { key: 'liters_share', label: 'Ҳажм улуши', render: (r) => <ShareBar value={r.liters_share} /> },
          { key: 'liters_growth', label: 'Ўсиш (л)', right: true, render: (r) => <Growth value={r.liters_growth} /> },
          { key: 'revenue', label: 'Савдо', right: true, render: (r) => money(r.revenue) },
          { key: 'profit', label: 'Фойда', right: true, render: (r) => money(r.profit), tone: (r) => signTone(r.profit) },
          { key: 'profit_share', label: 'Фойда улуши', render: (r) => <ShareBar value={r.profit_share} /> },
          { key: 'profit_growth', label: 'Ўсиш (фойда)', right: true, render: (r) => <Growth value={r.profit_growth} /> },
          { key: 'profit_per_liter', label: '1 л фойда', right: true, render: (r) => money(r.profit_per_liter) },
          { key: 'avg_daily_liters', label: 'Кунига', right: true, render: (r) => liters(r.avg_daily_liters) },
          { key: 'best_period', label: 'Энг яхши давр', render: (r) => r.best_period || '—' },
          { key: 'last_sale', label: 'Охирги сотув', render: (r) => r.last_sale || '—' },
        ]}
      />
      <p className="report-note">Ўсиш — олдинги шунча кунлик давр ({d.period.prev_from} — {d.period.prev_to}) билан солиштирилган.</p>
    </>
  );
}
