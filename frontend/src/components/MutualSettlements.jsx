/**
 * MutualSettlements — o'zaro hisob-kitob.
 *
 * Bitta hamkor ham mijoz, ham yetkazib beruvchi bo'lishi mumkin: undan mol
 * olamiz va unga sotamiz ham. Qarzlar alohida ko'rsatilsa haqiqiy holat
 * ko'rinmaydi, shuning uchun bu yerda ular bir-biridan ayiriladi.
 */
import { useState, useEffect } from 'react';
import { ArrowLeftRight } from 'lucide-react';
import client from '../api/client';

const formatMoney = (n) =>
    new Intl.NumberFormat('uz-UZ').format(Math.round(n)) + ' сўм';

export default function MutualSettlements({ refreshKey }) {
    const [rows, setRows] = useState([]);
    const [loading, setLoading] = useState(true);
    const [open, setOpen] = useState(true);

    useEffect(() => {
        let alive = true;
        (async () => {
            setLoading(true);
            try {
                const res = await client.get('/debts/net');
                if (alive) setRows((res.data.items || []).filter((r) => r.mutual));
            } catch (e) {
                if (alive) setRows([]);
            } finally {
                if (alive) setLoading(false);
            }
        })();
        return () => { alive = false; };
    }, [refreshKey]);

    // O'zaro qarzi bo'lgan hamkor bo'lmasa — bu blok umuman kerak emas
    if (loading || rows.length === 0) return null;

    return (
        <div className="card" style={{ marginBottom: '1rem' }}>
            <div
                style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', cursor: 'pointer' }}
                onClick={() => setOpen(!open)}
            >
                <ArrowLeftRight size={16} strokeWidth={2.4} style={{ color: 'var(--accent)' }} />
                <strong>Ўзаро ҳисоб-китоб</strong>
                <span style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
                    ({rows.length} та ҳамкор билан икки томонлама қарз)
                </span>
                <span style={{ marginLeft: 'auto', color: 'var(--text-secondary)' }}>
                    {open ? '▾' : '▸'}
                </span>
            </div>

            {open && (
                <>
                    <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', margin: '0.6rem 0 0.9rem' }}>
                        Бу ҳамкорлардан мол оламиз ва уларга сотамиз ҳам. Қуйида қарзларнинг
                        айирмаси — ҳақиқий ҳолат.
                    </p>
                    <div className="table-wrapper">
                        <table className="data-table" style={{ fontSize: '0.88rem' }}>
                            <thead>
                                <tr>
                                    <th>Ҳамкор</th>
                                    <th className="text-right">У бизга қарз</th>
                                    <th className="text-right">Биз унга қарз</th>
                                    <th className="text-right">Натижа</th>
                                </tr>
                            </thead>
                            <tbody>
                                {rows.map((r) => (
                                    <tr key={r.partner_id}>
                                        <td><strong>{r.partner_name}</strong></td>
                                        <td className="text-right" style={{ color: 'var(--success)' }}>
                                            {formatMoney(r.they_owe_us)}
                                        </td>
                                        <td className="text-right" style={{ color: 'var(--danger)' }}>
                                            {formatMoney(r.we_owe_them)}
                                        </td>
                                        <td
                                            className="text-right"
                                            style={{
                                                fontWeight: 700,
                                                color: r.net >= 0 ? 'var(--success)' : 'var(--danger)',
                                            }}
                                        >
                                            {r.net >= 0
                                                ? `${formatMoney(r.net)} — у бизга`
                                                : `${formatMoney(Math.abs(r.net))} — биз унга`}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </>
            )}
        </div>
    );
}
