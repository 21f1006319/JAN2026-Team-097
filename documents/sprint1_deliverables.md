# Sprint 1 Deliverables
## Workforce & Payroll Management System — Team 097

**Sprint Duration:** JAN 2026 — Sprint 1
**Date of Review:** 2026-04-05
**System URL:** http://localhost:5000 (Frontend) | http://localhost:5001/api (Backend)

---

## 1. Sprint 1 User Stories Implemented

| ID | User Story | Status |
|----|-----------|--------|
| US-01 | As an **admin**, I can log in securely and see a role-based dashboard | ✅ Done |
| US-02 | As an **admin/manager**, I can add, view, edit, and archive employees | ✅ Done |
| US-03 | As an **admin/manager**, I can mark daily attendance (Present/Absent/Half-day + overtime) | ✅ Done |
| US-04 | As an **admin/manager**, I can add/delete performance incentives for employees | ✅ Done |
| US-05 | As an **admin/manager**, I can add/delete penalties for employees | ✅ Done |
| US-06 | As an **admin**, I can check salary advance eligibility using the 7-day rule | ✅ Done |
| US-07 | As an **admin**, I can approve salary advances | ✅ Done |
| US-08 | As an **admin**, I can compute monthly payroll automatically (base + OT + incentives − penalties − advances − unpaid leaves) | ✅ Done |
| US-09 | As an **admin**, I can finalize payroll and generate payslip data | ✅ Done |
| US-10 | As an **admin**, I can configure paid leaves per month globally | ✅ Done |
| US-11 | As an **employee**, I can log in with my phone number as username and view my portal | ✅ Done |
| US-12 | As any user, I can change my password after verifying the old one | ✅ Done |

---

## 2. APIs Integrated (Third-Party Libraries)

| Library | Version | Role in Sprint 1 |
|---------|---------|-----------------|
| **Flask** | 2.3.3 | Backend REST framework; all 29 custom endpoints |
| **Flask-CORS** | 4.0.0 | Allows frontend (port 5000) to make XHR calls to backend (port 5001) |
| **requests** | 2.31.0 | Frontend service layer: all HTML routes call the backend JSON API via `requests` |
| **sqlite3** | stdlib | Embedded database engine; zero external DB dependency |
| **calendar** | stdlib | `monthrange()` for per-day salary calculation |

---

## 3. APIs Created (Dev Team — Sprint 1)

> Full Swagger YAML: `documents/api_swagger.yaml`
> Full test cases: `documents/sprint1_api_test_cases.md`

### 3.1 Authentication Module

| Method | Endpoint | Summary |
|--------|----------|---------|
| POST | `/api/login` | Authenticate user; return role, user_id |
| POST | `/api/change_password` | Change password after verifying old one |

**Key Design Decisions:**
- Passwords stored as plain text (development phase — to be hashed with bcrypt in Sprint 2)
- `is_active` flag allows soft-disabling users without deletion
- No JWT tokens in Sprint 1; session management handled by Flask frontend session

### 3.2 Store Module

| Method | Endpoint | Summary |
|--------|----------|---------|
| GET | `/api/stores` | List all active stores |
| POST | `/api/stores` | Create new store |

### 3.3 Settings Module

| Method | Endpoint | Summary |
|--------|----------|---------|
| GET | `/api/settings` | Retrieve global configuration |
| PUT | `/api/settings/paid_leaves` | Update paid leaves per month |

**Business Rule:** Default = 4 paid leaves/month. Any absence beyond this limit incurs per-day deduction from salary.

### 3.4 Employee Module

| Method | Endpoint | Summary |
|--------|----------|---------|
| GET | `/api/employees` | List employees (filterable by store, archived status) |
| POST | `/api/employees` | Create employee + auto user account |
| GET | `/api/employees/<id>` | Fetch single employee |
| PUT | `/api/employees/<id>` | Update employee details |
| POST | `/api/employees/<id>/archive` | Archive or restore employee |
| POST | `/api/employees/<id>/reset_password` | Admin resets employee password |

**Key Design Decisions:**
- Employee phone number auto-becomes the login username
- A random 8-character password is generated on creation and surfaced to the admin once
- Archiving is soft delete — payroll history is preserved

### 3.5 Attendance Module

| Method | Endpoint | Summary |
|--------|----------|---------|
| GET | `/api/attendance` | Retrieve attendance with filters |
| POST | `/api/attendance` | Mark or update attendance (upsert on employee_id + date) |

**Business Rules:**
- Half-day = 0.5 effective working days
- Overtime stored in hours; payroll computes at 1.5× hourly rate
- Duplicate mark on same date → updates the existing record (no duplicates)

### 3.6 Incentives Module

| Method | Endpoint | Summary |
|--------|----------|---------|
| GET | `/api/incentives` | List incentives (filterable) |
| POST | `/api/incentives` | Add incentive (`daily_performance` or `monthly_bonus`) |
| DELETE | `/api/incentives/<id>` | Remove incentive |

### 3.7 Penalties Module

| Method | Endpoint | Summary |
|--------|----------|---------|
| GET | `/api/penalties` | List penalties (filterable) |
| POST | `/api/penalties` | Add penalty (`daily` or `monthly`) |
| DELETE | `/api/penalties/<id>` | Remove penalty |

### 3.8 Salary Advance Module

| Method | Endpoint | Summary |
|--------|----------|---------|
| GET | `/api/advance/eligibility` | Check 7-day rule: returns eligible days and max amount |
| POST | `/api/advance` | Submit advance request (auto-approved in Sprint 1) |
| GET | `/api/advance` | List advances for employee/month |

**Business Rule (7-Day Rule):**
```
eligible_days = day_of_month − 7
max_advance   = eligible_days × (base_monthly_salary ÷ days_in_month)
```

### 3.9 Payroll Module

| Method | Endpoint | Summary |
|--------|----------|---------|
| POST | `/api/payroll/compute` | Compute payroll for all employees in a month |
| GET | `/api/payroll` | Retrieve payroll records |
| GET | `/api/payroll/<id>/details` | Line-item breakdown |
| POST | `/api/payroll/<id>/finalize` | Finalize payroll; mark advances as deducted |
| GET | `/api/payroll/<id>/payslip` | Get payslip data |

**Payroll Formula:**
```
net_salary = base_salary
           + overtime_pay          (OT hours × per_hour × 1.5)
           + total_incentives
           − total_penalties
           − leave_deduction       (unpaid_leaves × per_day_salary)
           − salary_advances
```

### 3.10 Dashboard Module

| Method | Endpoint | Summary |
|--------|----------|---------|
| GET | `/api/dashboard/stats` | Live counts: employees, today's attendance, pending advances |

---

## 4. API Description (Per Problem Statement)

### Problem Statement Alignment

The system is designed for **warehouse workforce management** with the following requirements mapped to APIs:

| Requirement | API(s) |
|-------------|--------|
| Multi-role access (admin / manager / employee) | `POST /api/login` — returns `role` field |
| Employee onboarding with auto credentials | `POST /api/employees` — creates user + employee |
| Daily attendance tracking with overtime | `POST /api/attendance` |
| Performance-based incentives | `POST /api/incentives` (daily_performance type) |
| Monthly bonuses | `POST /api/incentives` (monthly_bonus type) |
| Disciplinary penalties | `POST /api/penalties` |
| Salary advance with 7-day rule | `GET /api/advance/eligibility` + `POST /api/advance` |
| Automated payroll computation | `POST /api/payroll/compute` |
| Paid leave configuration | `PUT /api/settings/paid_leaves` |
| Payslip generation | `GET /api/payroll/<id>/payslip` |
| Multi-store support | Store filters on employees, attendance, dashboard |

---

## 5. Bugs Found and Fixed During Testing

### Bug 1 — Payroll `detail_type` constraint violation (Critical)

- **Where:** `backend/app.py`, `compute_payroll()`, line ~747
- **Impact:** ANY payroll run for an employee with incentives crashes with HTTP 500. Payslip incentive breakdowns always empty.
- **Root Cause:** String mismatch: code inserted `"incentive_daily_performance"` but DB constraint requires `"incentive_daily"`
- **Fix:** Map `incentive_type` → correct `detail_type`:
  - `'daily_performance'` → `'incentive_daily'`
  - `'monthly_bonus'` → `'incentive_monthly'`
- **Files changed:** `backend/app.py` (lines 747–751, 888–889)

### Bug 2 — Missing DB connection cleanup on error (Stability)

- **Where:** `backend/app.py`, `create_employee()`
- **Impact:** After any failed employee creation, SQLite became locked for ALL subsequent requests until Python GC ran.
- **Root Cause:** No `try/finally` — `conn.close()` never called when INSERT threw an exception.
- **Fix:** Added `try/except/finally` block; `conn.rollback()` + `conn.close()` on any exception; returns structured 400 JSON error.

---

## 6. User Testing Feedback

### Tester Profiles
- **Admin User (Warehouse Manager):** Can add employees, mark attendance, run payroll
- **Employee User:** Can view own portal, change password

### Feedback Collected

| Feature | Feedback | Priority |
|---------|----------|----------|
| Login page | Clean and functional; wants "forgot password" option | Medium |
| Employee creation | Auto-generated password is hard to communicate — wants email/SMS notification | High |
| Attendance marking | Works but tedious for 30+ employees daily — wants bulk mark / "Mark All Present" button | High |
| Payroll compute | Works correctly; wants to download payslip as PDF directly from UI | High |
| Dashboard stats | Good overview but wants a chart (bar/pie) for attendance trends | Low |
| Password (plain text) | Admin concerned that passwords are stored as plain text | Critical |
| Advance eligibility | 7-day rule logic is correct; user found it intuitive | ✅ Positive |
| Penalty/incentive | Users want to edit (not just delete-and-recreate) existing records | Medium |

---

## 7. Sprint 2 Planning

Based on test outcomes and user feedback:

### Sprint 2 Backlog

| Priority | Story | Description |
|----------|-------|-------------|
| 🔴 Critical | Password hashing | Replace plain-text passwords with bcrypt hashing |
| 🔴 Critical | Input validation | Add server-side validation for all required fields; return 400 with clear messages |
| 🟠 High | Bulk attendance | POST `/api/attendance/bulk` — mark attendance for all employees in one request |
| 🟠 High | PDF payslip download | Generate PDF from payslip data; store in `uploads/` folder |
| 🟠 High | Employee edit incentive/penalty | PUT `/api/incentives/<id>` and PUT `/api/penalties/<id>` endpoints |
| 🟡 Medium | JWT authentication | Replace session-based auth with JWT tokens for stateless API design |
| 🟡 Medium | Email notifications | Send credentials to employee email on creation / password reset |
| 🟡 Medium | Attendance dashboard chart | Frontend chart showing weekly attendance distribution |
| 🟢 Low | Role-based API guard | Middleware to restrict endpoints by role (e.g., only admin can finalize payroll) |
| 🟢 Low | Pagination | Add `page` / `limit` params to list endpoints for large datasets |

### Sprint 2 API Endpoints Planned

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/attendance/bulk` | Mark attendance for all employees in a store at once |
| PUT | `/api/incentives/<id>` | Edit existing incentive |
| PUT | `/api/penalties/<id>` | Edit existing penalty |
| GET | `/api/payroll/<id>/payslip/pdf` | Download payslip as PDF file |
| GET | `/api/employees/<id>/payroll` | Full payroll history for an employee |
| POST | `/api/auth/refresh` | Refresh JWT token |

---

## 8. Swagger YAML Location

```
documents/api_swagger.yaml
```

Swagger UI can be loaded at:
- https://editor.swagger.io — paste contents of `api_swagger.yaml`
- Or run locally with `swagger-ui-express` / `spectral`

**Validation command:**
```bash
# Install swagger-codegen or use npx
npx @apidevtools/swagger-parser validate documents/api_swagger.yaml
```

---

## 9. Running Tests

```bash
# Activate virtualenv
source ~/venv/bin/activate

# Unit tests (isolated, no servers needed)
python -m pytest backend/test_unit.py -v

# Integration tests (requires both servers running)
# Start backend:
python backend/app.py &
# Start frontend:
python frontend/app.py &
python -m pytest backend/test_integration.py -v

# Run all
python -m pytest backend/test_unit.py backend/test_integration.py -v
```

**Expected result:** `95 passed` in ~14 seconds.
