# AI Budget Tracker — Frontend (React + Vite)

## Run
```bash
npm install
npm run dev        # http://localhost:5173
```
Start the FastAPI backend on **http://localhost:8000**. Vite proxies `/api/*` to it, so no CORS setup is needed in dev.
Production build: `npm run build` (set `VITE_API_URL` to the real API URL, and enable CORS on the backend).

## Structure
- `src/api.js` – every backend call (one place to fix if a route changes)
- `src/App.jsx` – navigation, auth gate, field config for expenses / income / budgets
- `src/pages/Resource.jsx` – reusable list/create/edit/delete page
- `src/pages/` – Login, Dashboard, Reports, Analysis, Receipts, Assistant
- `src/components.jsx` – `DataView` (renders any JSON), form field, helpers

## Contract to confirm with the backend owner
These were not in the spec, so the frontend **assumes** them. Change `api.js` / the field lists if they differ.
| Item | Assumed |
|---|---|
| Register | `POST /auth/register` `{username,email,password}` |
| Login | `POST /auth/login` form-encoded `username,password` → `{access_token}` |
| Auth header | `Authorization: Bearer <token>` |
| Expense fields | `amount, category, merchant, description, expense_date` |
| Income fields | `amount, source, date` |
| Budget fields | `category, budget_amount, budget_period, start_date, end_date` |
| Receipt upload | `POST /receipts/upload` multipart `file` → `{receipt_id}` |
| Receipt extract | `POST /receipts/extract` `{receipt_id}` → `{merchant,date,total}` (+ optional `warnings`) |
| Receipt confirm | `POST /receipts/confirm` `{receipt_id,merchant,expense_date,amount,category}` |
| AI chat | `POST /ai/chat` `{question}` → `{answer}` |
| Forecast window | `GET /analysis/forecast?window=5` |
| Report filters | `?date=`, `?start_date=&end_date=` |

Report, analysis and budget-check responses are shown with a generic `DataView`, so they render whatever JSON the backend returns. Once schemas are final, swap in custom tables or charts.
