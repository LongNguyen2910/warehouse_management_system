# Warehouse Management System (WMS)

## Requirements

- Flask
- Flask-Cors
- Flasgger
- pyodbc
- python-dotenv
- Flask-JWT-Extended

Install dependencies with:

```bash
pip install -r requirements.txt
```

## Database Setup

1. Read `database.txt` for database details.
2. Check `.env.example` and create your own `.env` file.
3. Test the database connection:

```bash
python test_db.py
```

## Project Structure

```text
wms
|
|- app.py            # Main entry file (registers and connects all blueprints)
|- db_helper.py      # Core SQL Server connection helper
|- auth_api.py       # Authentication and authorization
|- inventory_api.py  # Inventory in/out operations
|- logistics_api.py  # Transfer and delivery operations
|- roles_api.py      # CRUD Role
|- users_api.py      # registration, change password, delete, update role user
|- warehouses_api.py # CRUD warehouses
`- reports_api.py    # Reporting endpoints (export file, statistics)
```
