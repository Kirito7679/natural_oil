/**
 * Reports — hisobot sahifasi.
 */
import { useState, useEffect } from 'react';
import client from '../api/client';
import { downloadExcel } from '../utils/excelDownload';

const formatMoney = (n = 0) =>
    new Intl.NumberFormat('uz-UZ').format(Math.round(n)) + " so'm";

const firstOfMonth = () => {
    const d = new Date();
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-01`;
};

const todayStr = () => new Date().toISOString().slice(0, 10);

export default function Reports() {
    const [dateFrom, setDateFrom] = useState(firstOfMonth());
    const [dateTo, setDateTo] = useState(todayStr());
    const [paymentType, setPaymentType] = useState('');
    const [report, setReport] = useState(null);
    const [loading, setLoading] = useState(false);

    // Daily transactions
    const [dailyDate, setDailyDate] = useState(todayStr());
    const [dailyTx, setDailyTx] = useState(null);
    const [dailyLoading, setDailyLoading] = useState(false);

    useEffect(() => {
        fetchReport();
        fetchDailyTx();
    }, []);

    async function fetchReport() {
        setLoading(true);
        try {
            const params = { date_from: dateFrom, date_to: dateTo };
            if (paymentType) params.payment_type = paymentType;

            const res = await client.get(`/reports/summary`, {
                params,
            });

            setReport(res.data);
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    }

    async function fetchDailyTx() {
        setDailyLoading(true);
        try {
            const res = await client.get(`/reports/daily-transactions`, {
                params: { date: dailyDate },
            });
            setDailyTx(res.data);
        } catch (e) {
            console.error(e);
        } finally {
            setDailyLoading(false);
        }
    }

    function handleExcelDownload() {
        const params = {
            date_from: dateFrom,
            date_to: dateTo,
        };

        if (paymentType) {
            params.payment_type = paymentType;
        }

        downloadExcel(
            'general-report',
            params,
            `natural_oil_report_${dateFrom}_${dateTo}.xlsx`
        );
    }

    return (
        <div className="page">
            <div className="page-header">
                <h1 className="page-title">Hisobot</h1>

                <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
                    <button
                        className="btn btn-secondary"
                        onClick={handleExcelDownload}
                    >
                        ⬇ Excelga yuklash
                    </button>

                    <button
                        className="btn btn-primary"
                        onClick={fetchReport}
                        disabled={loading}
                    >
                        {loading ? 'Yuklanmoqda...' : 'Yangilash'}
                    </button>
                </div>
            </div>

            {/* Filters */}
            <div
                className="card"
                style={{
                    marginBottom: '1.5rem',
                    padding: '1rem',
                    display: 'flex',
                    gap: '1rem',
                    alignItems: 'flex-end',
                    flexWrap: 'wrap',
                }}
            >
                <div className="form-group" style={{ margin: 0 }}>
                    <label>Dan</label>
                    <input
                        type="date"
                        className="form-control"
                        value={dateFrom}
                        onChange={(e) => setDateFrom(e.target.value)}
                    />
                </div>

                <div className="form-group" style={{ margin: 0 }}>
                    <label>Gacha</label>
                    <input
                        type="date"
                        className="form-control"
                        value={dateTo}
                        onChange={(e) => setDateTo(e.target.value)}
                    />
                </div>

                <div className="form-group" style={{ margin: 0 }}>
                    <label>To'lov turi</label>
                    <select
                        className="form-control"
                        value={paymentType}
                        onChange={(e) => setPaymentType(e.target.value)}
                    >
                        <option value="">Barchasi</option>
                        <option value="cash">Naqd</option>
                        <option value="bank_transfer">Perechisleniya</option>
                    </select>
                </div>

                <button
                    className="btn btn-primary"
                    onClick={fetchReport}
                    style={{ marginBottom: '0' }}
                >
                    Ko'rish
                </button>
            </div>

            {!report ? (
                <p className="empty-message">Ma'lumot yuklanmoqda...</p>
            ) : (
                <>
                    {/* Main stats */}
                    <div
                        style={{
                            display: 'grid',
                            gridTemplateColumns: 'repeat(3, 1fr)',
                            gap: '1rem',
                            marginBottom: '1.5rem',
                        }}
                    >
                        {[
                            {
                                label: 'Jami sotuv',
                                value: report.sales.total_sale_amount,
                                sub: `${report.sales.count} ta sotuv`,
                                color: 'var(--success)',
                            },
                            {
                                label: 'Jami foyda',
                                value: report.net_profit,
                                sub: 'Sof foyda',
                                color: report.net_profit >= 0 ? 'var(--accent)' : 'var(--danger)',
                            },
                            {
                                label: 'Jami xarajat',
                                value: report.expenses.total_amount,
                                sub: `${report.expenses.count} ta xarajat`,
                                color: 'var(--danger)',
                            },
                        ].map((c) => (
                            <div key={c.label} className="card" style={{ padding: '1rem' }}>
                                <div
                                    style={{
                                        color: 'var(--text-secondary)',
                                        fontSize: '0.82rem',
                                        marginBottom: '0.3rem',
                                    }}
                                >
                                    {c.label}
                                </div>

                                <div
                                    style={{
                                        fontSize: '1.4rem',
                                        fontWeight: 700,
                                        color: c.color,
                                    }}
                                >
                                    {formatMoney(c.value)}
                                </div>

                                <div
                                    style={{
                                        color: 'var(--text-secondary)',
                                        fontSize: '0.78rem',
                                        marginTop: '0.2rem',
                                    }}
                                >
                                    {c.sub}
                                </div>
                            </div>
                        ))}
                    </div>

                    <div
                        style={{
                            display: 'grid',
                            gridTemplateColumns: '1fr 1fr',
                            gap: '1rem',
                            marginBottom: '1.5rem',
                        }}
                    >
                        {/* Sales detail */}
                        <div className="card" style={{ padding: '1rem' }}>
                            <h3 style={{ marginBottom: '0.75rem', fontSize: '0.95rem' }}>
                                Sotuvlar
                            </h3>

                            {[
                                { label: 'Sotuvlar soni', value: `${report.sales.count} ta` },
                                {
                                    label: 'Sotuv summasi',
                                    value: formatMoney(report.sales.total_sale_amount),
                                },
                                {
                                    label: 'Tannarx',
                                    value: formatMoney(report.sales.total_cost),
                                },
                                {
                                    label: 'Yalpi foyda',
                                    value: formatMoney(report.sales.total_profit),
                                },
                            ].map((r) => (
                                <div
                                    key={r.label}
                                    style={{
                                        display: 'flex',
                                        justifyContent: 'space-between',
                                        padding: '6px 0',
                                        borderBottom: '1px solid var(--border)',
                                    }}
                                >
                                    <span
                                        style={{
                                            color: 'var(--text-secondary)',
                                            fontSize: '0.88rem',
                                        }}
                                    >
                                        {r.label}
                                    </span>

                                    <span style={{ fontWeight: 600, fontSize: '0.88rem' }}>
                                        {r.value}
                                    </span>
                                </div>
                            ))}
                        </div>

                        {/* Cash flow */}
                        <div className="card" style={{ padding: '1rem' }}>
                            <h3 style={{ marginBottom: '0.75rem', fontSize: '0.95rem' }}>
                                Pul oqimi
                            </h3>

                            {[
                                {
                                    label: 'Naqd kirim',
                                    value: formatMoney(report.cash_flow.cash_income),
                                    color: 'var(--success)',
                                },
                                {
                                    label: 'Naqd chiqim',
                                    value: formatMoney(report.cash_flow.cash_outgoing),
                                    color: 'var(--danger)',
                                },
                                {
                                    label: 'Naqd balans (Hisoblangan)',
                                    value: formatMoney(report.cash_flow.cash_net),
                                    color:
                                        report.cash_flow.cash_net >= 0
                                            ? 'var(--success)'
                                            : 'var(--danger)',
                                },
                                {
                                    label: 'Perechisleniya kirim',
                                    value: formatMoney(report.cash_flow.bank_income),
                                    color: 'var(--success)',
                                },
                                {
                                    label: 'Perechisleniya chiqim',
                                    value: formatMoney(report.cash_flow.bank_outgoing),
                                    color: 'var(--danger)',
                                },
                                {
                                    label: 'Perechisleniya balans (Hisoblangan)',
                                    value: formatMoney(report.cash_flow.bank_net),
                                    color:
                                        report.cash_flow.bank_net >= 0
                                            ? 'var(--success)'
                                            : 'var(--danger)',
                                },
                                {
                                    label: 'Jami balans (Hisoblangan)',
                                    value: formatMoney(report.cash_flow.cash_net + report.cash_flow.bank_net),
                                    color:
                                        (report.cash_flow.cash_net + report.cash_flow.bank_net) >= 0
                                            ? 'var(--success)'
                                            : 'var(--danger)',
                                },
                            ].map((r) => (
                                <div
                                    key={r.label}
                                    style={{
                                        display: 'flex',
                                        justifyContent: 'space-between',
                                        padding: '6px 0',
                                        borderBottom: '1px solid var(--border)',
                                    }}
                                >
                                    <span
                                        style={{
                                            color: 'var(--text-secondary)',
                                            fontSize: '0.88rem',
                                        }}
                                    >
                                        {r.label}
                                    </span>

                                    <span
                                        style={{
                                            fontWeight: 600,
                                            fontSize: '0.88rem',
                                            color: r.color,
                                        }}
                                    >
                                        {r.value}
                                    </span>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Expenses by category */}
                    {Object.keys(report.expenses.by_category).length > 0 && (
                        <div className="card" style={{ padding: '1rem' }}>
                            <h3 style={{ marginBottom: '0.75rem', fontSize: '0.95rem' }}>
                                Xarajatlar (kategoriya bo'yicha)
                            </h3>

                            <table className="data-table">
                                <thead>
                                    <tr>
                                        <th>Kategoriya</th>
                                        <th style={{ textAlign: 'right' }}>Summa</th>
                                    </tr>
                                </thead>

                                <tbody>
                                    {Object.entries(report.expenses.by_category)
                                        .sort((a, b) => b[1] - a[1])
                                        .map(([cat, amount]) => (
                                            <tr key={cat}>
                                                <td>{cat}</td>
                                                <td
                                                    style={{
                                                        textAlign: 'right',
                                                        color: 'var(--danger)',
                                                        fontWeight: 600,
                                                    }}
                                                >
                                                    {formatMoney(amount)}
                                                </td>
                                            </tr>
                                        ))}

                                    <tr style={{ borderTop: '2px solid var(--border)' }}>
                                        <td style={{ fontWeight: 700 }}>Jami</td>
                                        <td
                                            style={{
                                                textAlign: 'right',
                                                fontWeight: 700,
                                                color: 'var(--danger)',
                                            }}
                                        >
                                            {formatMoney(report.expenses.total_amount)}
                                        </td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    )}
                    
                    {/* Daily Transactions Section */}
                    <div className="card" style={{ padding: '1.5rem', marginTop: '2rem' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
                            <h2 style={{ margin: 0, fontSize: '1.25rem' }}>Kunlik tranzaksiyalar</h2>
                            <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                                <input
                                    type="date"
                                    className="form-control"
                                    value={dailyDate}
                                    onChange={(e) => setDailyDate(e.target.value)}
                                    style={{ margin: 0 }}
                                />
                                <button
                                    className="btn btn-primary"
                                    onClick={fetchDailyTx}
                                    disabled={dailyLoading}
                                >
                                    {dailyLoading ? '...' : "Ko'rish / Yangilash"}
                                </button>
                            </div>
                        </div>

                        {!dailyTx ? (
                            <p>Yuklanmoqda...</p>
                        ) : (
                            <div>
                                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem', marginBottom: '1.5rem', background: 'var(--bg-input)', padding: '1rem', borderRadius: '8px' }}>
                                    <div>
                                        <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>KUN BOSHI BALANSI</div>
                                        <div style={{ fontWeight: 'bold' }}>Jami: {formatMoney(dailyTx.opening_balance.total)}</div>
                                        <div style={{ fontSize: '0.85rem' }}>Naqd: {formatMoney(dailyTx.opening_balance.cash)}</div>
                                        <div style={{ fontSize: '0.85rem' }}>Perechisleniya: {formatMoney(dailyTx.opening_balance.bank_transfer)}</div>
                                    </div>
                                    <div>
                                        <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>KUNLIK PUL AYLANMASI</div>
                                        <div style={{ color: 'var(--success)', fontWeight: 'bold' }}>Kirim: +{formatMoney(dailyTx.totals.total_income)}</div>
                                        <div style={{ color: 'var(--danger)', fontWeight: 'bold' }}>Chiqim: -{formatMoney(dailyTx.totals.total_outgoing)}</div>
                                    </div>
                                    <div>
                                        <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>KUN YAKUNI BALANSI</div>
                                        <div style={{ fontWeight: 'bold', color: dailyTx.closing_balance.total >= 0 ? 'var(--success)' : 'var(--danger)' }}>
                                            Jami: {formatMoney(dailyTx.closing_balance.total)}
                                        </div>
                                        <div style={{ fontSize: '0.85rem', color: dailyTx.closing_balance.cash >= 0 ? 'var(--success)' : 'var(--danger)' }}>
                                            Naqd: {formatMoney(dailyTx.closing_balance.cash)}
                                        </div>
                                        <div style={{ fontSize: '0.85rem', color: dailyTx.closing_balance.bank_transfer >= 0 ? 'var(--success)' : 'var(--danger)' }}>
                                            Perechisleniya: {formatMoney(dailyTx.closing_balance.bank_transfer)}
                                        </div>
                                    </div>
                                </div>

                                <div className="table-wrapper">
                                    <table className="data-table">
                                        <thead>
                                            <tr>
                                                <th>Vaqt</th>
                                                <th>Tur</th>
                                                <th>Hamkor</th>
                                                <th>Mahsulot</th>
                                                <th className="text-right">Miqdor</th>
                                                <th>To'lov turi</th>
                                                <th className="text-right">Kirim</th>
                                                <th className="text-right">Chiqim</th>
                                                <th>Izoh</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {dailyTx.transactions.length === 0 ? (
                                                <tr>
                                                    <td colSpan={9} className="text-center">Bu kunda tranzaksiyalar yo'q</td>
                                                </tr>
                                            ) : (
                                                dailyTx.transactions.map((t, idx) => (
                                                    <tr key={idx}>
                                                        <td>{t.time}</td>
                                                        <td>{t.title}</td>
                                                        <td>{t.partner_name}</td>
                                                        <td>{t.product_name}</td>
                                                        <td className="text-right">{t.quantity ? `${t.quantity} L` : '—'}</td>
                                                        <td>{t.payment_type}</td>
                                                        <td className="text-right text-success font-medium">
                                                            {t.direction === 'income' ? `+${formatMoney(t.amount)}` : (t.direction === 'stock_only' && t.type === 'sale' ? formatMoney(t.amount) : '')}
                                                        </td>
                                                        <td className="text-right text-danger font-medium">
                                                            {t.direction === 'outgoing' ? `-${formatMoney(t.amount)}` : (t.direction === 'stock_only' && (t.type === 'purchase' || t.type === 'initial_stock') ? formatMoney(t.amount) : '')}
                                                        </td>
                                                        <td style={{ maxWidth: '150px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }} title={t.note}>{t.note}</td>
                                                    </tr>
                                                ))
                                            )}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        )}
                    </div>
                </>
            )}
        </div>
    );
}