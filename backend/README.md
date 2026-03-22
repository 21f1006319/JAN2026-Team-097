# Backend API Server

Flask-based REST API server for the Workforce & Payroll Management System.

---

## Overview

The backend server handles all business logic, database operations, and serves as the API layer for the frontend application. It runs on **Port 5001** and uses SQLite for data persistence.

---

## File Structure

```
backend/
├── app.py              # Main Flask application with all API endpoints
├── initialize_db.py    # Database initialization script
├── requirements.txt    # Python dependencies
└── app_database.db     # SQLite database (generated after init)
```

---

## Installation

```bash
pip install -r requirements.txt
```

### Dependencies
- Flask==2.3.3
- Flask-Cors==4.0.0
- requests==2.31.0

---

## Database Initialization

Run this once to create the database and tables:

```bash
python initialize_db.py
```

This creates:
- 10 database tables (stores, users, employees, attendance, incentives, penalties, salary_advances, payroll, payroll_details, global_settings)
- Default admin user: `admin` / `admin123`
- Default store: "Main Store"

---

## Running the Server

```bash
python app.py
```

Server will start at: `http://localhost:5001`

---

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/login` | Authenticate user, returns role and token |
| POST | `/api/change_password` | Change user password |

### Stores
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/stores` | List all stores |
| POST | `/api/stores` | Create new store |

### Settings
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/settings` | Get all settings |
| PUT | `/api/settings/paid_leaves` | Update paid leaves limit |

### Employees
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/employees` | List employees (with filters) |
| GET | `/api/employees/<id>` | Get specific employee |
| POST | `/api/employees` | Create employee with user account |
| PUT | `/api/employees/<id>` | Update employee |
| POST | `/api/employees/<id>/archive` | Archive/unarchive |
| POST | `/api/employees/<id>/reset_password` | Reset to random password |

### Attendance
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/attendance` | Get attendance records |
| POST | `/api/attendance` | Mark/update attendance |

### Incentives
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/incentives` | List incentives |
| POST | `/api/incentives` | Add incentive |
| DELETE | `/api/incentives/<id>` | Delete incentive |

### Penalties
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/penalties` | List penalties |
| POST | `/api/penalties` | Add penalty |
| DELETE | `/api/penalties/<id>` | Delete penalty |

### Salary Advances
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/advance/eligibility` | Check 7-day rule eligibility |
| GET | `/api/advance` | List advances |
| POST | `/api/advance` | Create advance request |

### Payroll
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/payroll/compute` | Compute payroll for month |
| GET | `/api/payroll` | Get payroll records |
| GET | `/api/payroll/<id>/details` | Get detailed breakdown |
| POST | `/api/payroll/<id>/finalize` | Finalize payroll |
| GET | `/api/payroll/<id>/payslip` | Get payslip data |

### Dashboard
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/dashboard/stats` | Get dashboard statistics |

---

## Database Schema

### Tables

1. **stores** - Store/locations management
2. **users** - Authentication accounts (admin, manager, employee)
3. **global_settings** - System configuration (paid leaves, etc.)
4. **employees** - Employee profiles with salary info
5. **attendance** - Daily attendance records
6. **incentives** - Employee incentives (daily/monthly)
7. **penalties** - Employee penalties (daily/monthly)
8. **salary_advances** - Advance requests with 7-day rule tracking
9. **payroll** - Monthly computed salaries
10. **payroll_details** - Detailed breakdown of incentives/penalties/advances

---

## Payroll Calculation Formula

```python
# Per-day calculation (dynamic by month)
total_days = days_in_month(year, month)
per_day_salary = base_salary / total_days

# Leave calculation
unpaid_leaves = max(0, leaves_taken - paid_leaves_allowed)
leave_deduction = unpaid_leaves * per_day_salary

# Overtime (1.5x rate)
hourly_rate = per_day_salary / 8
overtime_pay = overtime_hours * hourly_rate * 1.5

# Net salary
net_salary = (base_salary + 
              overtime_pay + 
              total_incentives - 
              total_penalties - 
              leave_deduction - 
              salary_advances)
```

---

## 7-Day Advance Rule

```python
eligible_days = max(0, day_of_month - 7)
max_advance = eligible_days * per_day_salary
```

Example: On day 15, employee can withdraw up to 8 days' salary (15 - 7 = 8).

---

## Key Functions

### `get_db_connection()`
Returns SQLite connection with Row factory for dict-like access.

### `generate_random_password(length=8)`
Generates secure random password for employee accounts.

### `calculate_per_day_salary(base_salary, month, year)`
Returns per-day salary based on actual days in month.

### `get_paid_leaves_limit()`
Retrieves configured paid leaves from settings.

---

## Error Handling

All endpoints return JSON responses:

```json
{
  "success": true/false,
  "message": "Error description if failed",
  "data": { ... }
}
```

---

## CORS Configuration

The API is configured with `Flask-CORS` to accept cross-origin requests from the frontend:

```python
from flask_cors import CORS
CORS(app)
```

---

## Development Notes

### Adding New Endpoints

1. Define route with appropriate HTTP method
2. Extract parameters from `request.json` or `request.args`
3. Use `get_db_connection()` for database access
4. Return JSON response with `success` flag

### Database Migrations

SQLite is schema-flexible. For schema changes:
1. Modify `initialize_db.py` CREATE TABLE statements
2. Delete existing `app_database.db`
3. Re-run `initialize_db.py`

---

## Testing API Endpoints

Using curl:

```bash
# Login
curl -X POST http://localhost:5001/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# Get employees
curl http://localhost:5001/api/employees

# Create employee
curl -X POST http://localhost:5001/api/employees \
  -H "Content-Type: application/json" \
  -d '{"name":"John Doe","phone":"1234567890","role_type":"Picking","base_monthly_salary":30000,"date_of_joining":"2024-01-15"}'
```

---

## Security Considerations

- Passwords stored in plain text (for demo purposes - use hashing in production)
- No JWT tokens implemented (session-based in frontend)
- SQLite file permissions should be restricted
- CORS allows all origins (restrict in production)

---

## Troubleshooting

### Port 5001 Already in Use
```bash
# Windows
netstat -ano | findstr :5001
taskkill /PID <PID> /F
```

### Database Locked
- Ensure no other process is using `app_database.db`
- Check file permissions

### Import Errors
```bash
pip install -r requirements.txt --force-reinstall
```

---

## Environment Variables (Optional)

Create `.env` file for customization:

```
FLASK_PORT=5001
DATABASE_PATH=./app_database.db
PAID_LEAVES_DEFAULT=4
OVERTIME_MULTIPLIER=1.5
```

---

## API Server Lifecycle

```
Initialize DB (once)
    ↓
Start Backend (python app.py)
    ↓
Frontend Connects (http://localhost:5001/api/*)
    ↓
Process Requests
    ↓
SQLite Operations
    ↓
JSON Responses
```
