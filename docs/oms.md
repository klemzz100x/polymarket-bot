# OMS

The Order Management System tracks future real orders without enabling live trading by default.

## States

- `pending`
- `submitted`
- `open`
- `partially_filled`
- `filled`
- `cancelled`
- `rejected`
- `expired`

## Modules

- `order_manager.py`
- `order_state_machine.py`
- `fill_tracker.py`
- `execution_tracker.py`
- `reconciliation.py`
- `storage.py`

## Responsibilities

- prepare and track orders
- prevent duplicate order intent
- apply execution reports
- track fills
- detect exchange-vs-DB inconsistencies
- store OMS state for dashboard review

## Dashboard

The dashboard page `OMS` is read-only and shows orders, fills, risk gate events, and reconciliation reports.
