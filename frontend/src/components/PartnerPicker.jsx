/**
 * PartnerPicker — mijoz / yetkazib beruvchini tanlash.
 * Ro'yxatda yo'q bo'lsa, shu joyning o'zida yangisini qo'shib, darhol tanlab ketadi.
 */
import { useState } from 'react';
import { UserPlus, X } from 'lucide-react';
import { createPartner } from '../api/partners';

const NEW = '__new__';

export default function PartnerPicker({ type, label, partners, onPartnersChange, value, onChange, required = true }) {
  const [adding, setAdding] = useState(false);
  const [name, setName] = useState('');
  const [phone, setPhone] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const who = type === 'supplier' ? 'етказиб берувчи' : 'мижоз';

  const handleSelect = (v) => {
    if (v === NEW) {
      setAdding(true);
      setError('');
      return;
    }
    onChange(v);
  };

  const save = async () => {
    if (!name.trim()) {
      setError('Исмини киритинг');
      return;
    }
    setSaving(true);
    setError('');
    try {
      const res = await createPartner({ name: name.trim(), phone: phone.trim() || null, type });
      onPartnersChange([...partners, res.data].sort((a, b) => a.name.localeCompare(b.name)));
      onChange(String(res.data.id));
      setAdding(false);
      setName('');
      setPhone('');
    } catch (e) {
      setError(e.response?.data?.detail || 'Сақлаб бўлмади');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="form-group partner-picker">
      <label>{label}{required ? ' *' : ''}</label>
      {!adding ? (
        <select value={value} onChange={(e) => handleSelect(e.target.value)} required={required}>
          <option value="">Танланг...</option>
          <option value={NEW}>➕ Янги {who} қўшиш</option>
          {partners.map((p) => (
            <option key={p.id} value={p.id}>{p.name}{p.phone ? ` (${p.phone})` : ''}</option>
          ))}
        </select>
      ) : (
        <div className="partner-new">
          <div className="partner-new-head">
            <UserPlus size={16} strokeWidth={2.4} /> Янги {who}
            <button type="button" className="partner-new-close" onClick={() => setAdding(false)} aria-label="Ёпиш"><X size={16} /></button>
          </div>
          <input autoFocus placeholder="Исми ёки номи *" value={name} onChange={(e) => setName(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); save(); } }} />
          <input placeholder="Телефон (ихтиёрий)" value={phone} onChange={(e) => setPhone(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); save(); } }} />
          {error && <div className="partner-new-error">{error}</div>}
          <button type="button" className="btn btn-primary btn--sm" onClick={save} disabled={saving}>
            {saving ? 'Сақланмоқда...' : `Қўшиш ва танлаш`}
          </button>
        </div>
      )}
    </div>
  );
}
