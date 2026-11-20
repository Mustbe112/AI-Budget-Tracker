import { useState } from 'react';
import { api } from '../api.js';
import { Err, Field } from '../components.jsx';

const FIELDS = (cats) => [
  { name: 'merchant', label: 'Merchant' },
  { name: 'expense_date', label: 'Date', type: 'date' },
  { name: 'amount', label: 'Total (฿)', type: 'number', required: true },
  { name: 'category', label: 'Category', options: cats, required: true },
  { name: 'description', label: 'Description (optional)' },
];

// Three steps: upload -> OCR extract -> user reviews -> confirm. Nothing is saved until step 3.
export default function Receipts({ categories, onSaved }) {
  const [file, setFile] = useState(null);
  const [receiptId, setReceiptId] = useState(null);
  const [form, setForm] = useState(null);
  const [warn, setWarn] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const extract = async (e) => {
    e.preventDefault(); setError(''); setWarn('');
    if (!file) return setError('Choose a receipt image first.');
    if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) return setError('Use a JPG, PNG or WebP image.');
    if (file.size > 5 * 1024 * 1024) return setError('Image must be under 5 MB.');
    setBusy(true);
    let step = 'Upload (POST /receipts/upload)';
    try {
      const up = await api.receiptUpload(file);
      const id = up.receipt_id ?? up.id; setReceiptId(id);
      step = 'Reading (POST /receipts/extract)';
      const ex = await api.receiptExtract({ receipt_id: id });
      // Backend: { status, merchant, transaction_date, total_amount, ... } (a DRAFT: nothing is saved yet)
      const r = ex.data || ex;
      setForm({
        merchant: r.merchant ?? '',
        expense_date: r.transaction_date ?? r.expense_date ?? r.date ?? '',
        amount: r.total_amount ?? r.total ?? r.amount ?? '',
        category: r.category ?? '',
        description: '',
      });
      const issues = [r.message, ...(Array.isArray(r.warnings) ? r.warnings : [])].filter((x) => typeof x === 'string' && x);
      const missing = !r.merchant || !(r.transaction_date ?? r.date) || !(r.total_amount ?? r.total);
      if ((r.status && r.status !== 'ok') || missing || issues.length)
        setWarn(issues.join(' ') || 'Some fields could not be read clearly. Please check and complete them before saving.');
    } catch (err) { setError(`${step} failed: ${err.message}. You can still add this expense manually.`); } finally { setBusy(false); }
  };

  const confirm = async (e) => {
    e.preventDefault(); setError('');
    try {
      await api.receiptConfirm({ receipt_id: receiptId, ...Object.fromEntries(Object.entries(form).filter(([, v]) => v !== '')) });
      onSaved();
    } catch (err) { setError(err.message); }
  };

  return (
    <>
      <h1>Scan receipt</h1>
      <form className="panel grid" onSubmit={extract}>
        <label className="field span"><span>Receipt image</span><input type="file" accept="image/jpeg,image/png,image/webp" onChange={(e) => setFile(e.target.files[0])} /></label>
        <div className="actions span"><button className="btn" disabled={busy}>{busy ? 'Reading receipt…' : 'Read receipt'}</button></div>
      </form>
      <Err msg={error} />
      {form && (
        <form className="panel grid" onSubmit={confirm}>
          <h2 className="span">Check the details</h2>
          {warn && <p className="note span">{warn}</p>}
          {FIELDS(categories).map((f) => <Field key={f.name} f={f} value={form[f.name]} onChange={(k, v) => setForm({ ...form, [k]: v })} />)}
          <div className="actions span">
            <button className="btn">Save expense</button>
            <button type="button" className="btn ghost" onClick={() => setForm(null)}>Discard</button>
          </div>
        </form>
      )}
    </>
  );
}