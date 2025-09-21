# Sprint 11-12: Facturación & Conciliación Bancaria

## Modelos
- Invoice(id, project_id, dte_number, status[pending|accepted|rejected|paid], amount, currency, xml_ref, created_at, paid_at)
- InvoicePayment(id, invoice_id, amount, method, reference, created_at)
- BankTransaction(id, project_id, date, description, amount, balance, source, raw(JSON), matched_invoice_id)

## Endpoints (prefijo `/api/v1`)
### Facturas
- POST `/invoices/` crear factura
- GET `/invoices/?project_id=...` listar
- POST `/invoices/{id}/send_sii` simula envío y cambia a `accepted`
- POST `/invoices/{id}/payments` registra pago y si total >= amount => `paid`

### Banco / Conciliación
- POST `/invoices/bank/import` importa transacciones (conversión automática de fecha YYYY-MM-DD)
- POST `/invoices/bank/reconcile` vincula transacción a factura y si montos coinciden marca `paid`

## Dashboard
Se añaden métricas en clave `finance`:
```json
{
  "finance": {
    "invoiced_total": 1000.0,
    "paid_total": 400.0,
    "pending_total": 600.0,
    "paid_ratio": 0.4
  }
}
```

## Índices
- `ix_invoices_project_status(project_id, status)`
- `ix_bank_txn_project_matched(project_id, matched_invoice_id)`

## Auditoría
Acciones registradas: `invoice_create`, `invoice_send_sii`, `invoice_payment`, `bank_import`, `bank_reconcile`.

## Reglas de negocio
1. Sólo facturas `pending` pueden enviarse a SII (simulado) => pasan a `accepted` y se les asigna `dte_number` si no existe.
2. Suma de pagos >= monto => estado `paid`.
3. Conciliación banco: si diferencia absoluta entre transacción y monto factura < 0.01 y estado previo `pending|accepted` => `paid`.

## Tests
- `test_invoice_lifecycle` y `test_bank_import_and_reconcile` cubren ciclo completo de factura y conciliación.

## Futuras extensiones
- Validación real SII / DTE.
- Soporte multi-moneda y FX.
- Reglas de matching inteligente (monto aproximado, referencia textual, clustering por fecha).
