# Restaurant POS MVP

Restaurant POS MVP built with Django for single-outlet restaurant operations.

## Included modules

- Role-based auth for admin, manager, cashier, captain, and kitchen staff
- 3-click style POS billing screen
- Tables and dine-in order tracking
- KOT generation and KDS screen
- Recipe-based raw inventory deduction
- Customer lookup and loyalty points
- Sales and stock summary reports
- Mock aggregator webhook ingestion for Swiggy, Zomato, and ONDC
- Offline action queue endpoints and browser-side retry helper
- Demo data seed command

## Local demo run

```powershell
cd restaurant_pos
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py seed_demo_data
.\.venv\Scripts\python.exe manage.py runserver
```

Login:

- `admin / admin123`
- `cashier / cash123`

## XAMPP MySQL setup

This project now loads `.env` automatically. The included `.env` is already set for a default XAMPP install:

```env
MYSQL_DATABASE=restaurant_pos
MYSQL_USER=root
MYSQL_PASSWORD=
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
```

This project uses `Django 4.2` so it stays compatible with the MariaDB version bundled in common XAMPP installs such as `10.4.x`.

If needed, update `.env` and then run:

```powershell
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py seed_demo_data
.\.venv\Scripts\python.exe manage.py runserver
```

If you want SQLite demo mode instead, set `USE_SQLITE=1`.

## Key URLs

- `/` dashboard
- `/pos/` cashier POS
- `/kitchen/` kitchen display
- `/reports/` summary reports
- `/admin/` Django admin

## Mock integration example

POST sample order to:

`/api/integrations/swiggy/orders/`

Example JSON:

```json
{
  "order_id": "SW-1001",
  "items": [
    {"name": "Paneer Tikka", "quantity": 1},
    {"name": "Cold Drink", "quantity": 2}
  ]
}
```
