# Sprint 1 — API Test Cases
## Workforce & Payroll Management System
**Team:** 097 — JAN2026 | **Date:** 2026-04-05

---

## Section A: APIs Integrated (Third-Party Libraries)

| Library | Version | Purpose |
|---------|---------|---------|
| **Flask** | 2.3.3 | HTTP server framework; provides routing, request/response handling, `jsonify()` |
| **Flask-CORS** | 4.0.0 | Cross-Origin Resource Sharing headers — allows frontend (port 5000) to call backend (port 5001) |
| **requests** | 2.31.0 | Frontend → Backend HTTP calls; used in frontend `api_call()` helper |
| **sqlite3** | stdlib | Built-in Python SQLite driver; database layer for all persistence |
| **calendar** | stdlib | `calendar.monthrange()` — computes total days in a given month for per-day salary |

---

## Section B: APIs Created (Dev Team)

| # | Method | Endpoint | Description |
|---|--------|----------|-------------|
| 1 | POST | `/api/login` | Authenticate user, return role & user_id |
| 2 | POST | `/api/change_password` | Change password after verifying old one |
| 3 | GET | `/api/stores` | List all active stores |
| 4 | POST | `/api/stores` | Create a new store |
| 5 | GET | `/api/settings` | Get all global settings |
| 6 | PUT | `/api/settings/paid_leaves` | Update paid leaves per month |
| 7 | GET | `/api/employees` | List employees (with archive/store filters) |
| 8 | POST | `/api/employees` | Create employee + auto user account |
| 9 | GET | `/api/employees/<id>` | Get single employee |
| 10 | PUT | `/api/employees/<id>` | Update employee details |
| 11 | POST | `/api/employees/<id>/archive` | Archive or unarchive employee |
| 12 | POST | `/api/employees/<id>/reset_password` | Generate and set new random password |
| 13 | GET | `/api/attendance` | Fetch attendance (filterable) |
| 14 | POST | `/api/attendance` | Mark/update attendance (upsert) |
| 15 | GET | `/api/incentives` | Fetch incentives (filterable) |
| 16 | POST | `/api/incentives` | Add incentive |
| 17 | DELETE | `/api/incentives/<id>` | Delete incentive |
| 18 | GET | `/api/penalties` | Fetch penalties (filterable) |
| 19 | POST | `/api/penalties` | Add penalty |
| 20 | DELETE | `/api/penalties/<id>` | Delete penalty |
| 21 | GET | `/api/advance/eligibility` | Check 7-day rule advance eligibility |
| 22 | POST | `/api/advance` | Request salary advance |
| 23 | GET | `/api/advance` | Fetch advances (filterable) |
| 24 | POST | `/api/payroll/compute` | Compute payroll for all employees in a month |
| 25 | GET | `/api/payroll` | Fetch payroll records |
| 26 | GET | `/api/payroll/<id>/details` | Fetch payroll line-item breakdown |
| 27 | POST | `/api/payroll/<id>/finalize` | Finalize payroll; mark advances as deducted |
| 28 | GET | `/api/payroll/<id>/payslip` | Get payslip data for PDF generation |
| 29 | GET | `/api/dashboard/stats` | Aggregated stats (employees, attendance, advances) |

---

## Section C: Test Cases

> **Format:** API Endpoint | Input | Expected Output | Actual Output | Result

---

### TC-01 to TC-05 — POST /api/login

---

**TC-01**
| Field | Value |
|-------|-------|
| **API** | `POST /api/login` |
| **Input** | `{"username": "admin", "password": "admin123"}` |
| **Expected Output** | HTTP 200; `{"success": true, "role": "admin", "user_id": <int>}` |
| **Actual Output** | HTTP 200; `{"success": true, "user_id": 1, "username": "admin", "role": "admin", "email": "admin@company.com"}` |
| **Result** | ✅ Success |

---

**TC-02**
| Field | Value |
|-------|-------|
| **API** | `POST /api/login` |
| **Input** | `{"username": "admin", "password": "wrongpassword"}` |
| **Expected Output** | HTTP 401; `{"success": false, "message": "Invalid credentials"}` |
| **Actual Output** | HTTP 401; `{"success": false, "message": "Invalid credentials"}` |
| **Result** | ✅ Success |

---

**TC-03**
| Field | Value |
|-------|-------|
| **API** | `POST /api/login` |
| **Input** | `{"username": "ghost_user", "password": "anything"}` |
| **Expected Output** | HTTP 401; `success: false` |
| **Actual Output** | HTTP 401; `{"success": false, "message": "Invalid credentials"}` |
| **Result** | ✅ Success |

---

**TC-04**
| Field | Value |
|-------|-------|
| **API** | `POST /api/login` |
| **Input** | `{"username": "admin"}` *(password field omitted)* |
| **Expected Output** | HTTP 401; login fails gracefully |
| **Actual Output** | HTTP 401; `{"success": false, "message": "Invalid credentials"}` |
| **Result** | ✅ Success |

---

**TC-05**
| Field | Value |
|-------|-------|
| **API** | `POST /api/login` |
| **Input** | `{"username": "", "password": ""}` |
| **Expected Output** | HTTP 401; `success: false` |
| **Actual Output** | HTTP 401; `{"success": false, "message": "Invalid credentials"}` |
| **Result** | ✅ Success |

---

### TC-06 to TC-08 — POST /api/change_password

---

**TC-06**
| Field | Value |
|-------|-------|
| **API** | `POST /api/change_password` |
| **Input** | `{"user_id": 1, "old_password": "admin123", "new_password": "newpass456"}` |
| **Expected Output** | HTTP 200; `{"success": true, "message": "Password updated successfully"}` |
| **Actual Output** | HTTP 200; `{"success": true, "message": "Password updated successfully"}` |
| **Result** | ✅ Success |

---

**TC-07**
| Field | Value |
|-------|-------|
| **API** | `POST /api/change_password` |
| **Input** | `{"user_id": 1, "old_password": "wrongold", "new_password": "newpass"}` |
| **Expected Output** | HTTP 400; `{"success": false, "message": "Invalid old password"}` |
| **Actual Output** | HTTP 400; `{"success": false, "message": "Invalid old password"}` |
| **Result** | ✅ Success |

---

**TC-08**
| Field | Value |
|-------|-------|
| **API** | `POST /api/change_password` |
| **Input** | `{"user_id": 9999, "old_password": "admin123", "new_password": "new"}` |
| **Expected Output** | HTTP 400; `success: false` (no such user) |
| **Actual Output** | HTTP 400; `{"success": false, "message": "Invalid old password"}` |
| **Result** | ✅ Success |

---

### TC-09 to TC-11 — GET/POST /api/stores

---

**TC-09**
| Field | Value |
|-------|-------|
| **API** | `GET /api/stores` |
| **Input** | *(none)* |
| **Expected Output** | HTTP 200; `{"success": true, "stores": [...]}` with at least the default Main Store |
| **Actual Output** | HTTP 200; `{"success": true, "stores": [{"id": 1, "name": "Main Store", ...}]}` |
| **Result** | ✅ Success |

---

**TC-10**
| Field | Value |
|-------|-------|
| **API** | `POST /api/stores` |
| **Input** | `{"name": "North Warehouse", "address": "12 Industrial Road"}` |
| **Expected Output** | HTTP 200; `{"success": true, "store_id": <int>}` |
| **Actual Output** | HTTP 200; `{"success": true, "store_id": 2, "message": "Store created successfully"}` |
| **Result** | ✅ Success |

---

**TC-11**
| Field | Value |
|-------|-------|
| **API** | `POST /api/stores` |
| **Input** | `{"name": "Minimal Store"}` *(address omitted)* |
| **Expected Output** | HTTP 200; store created without address |
| **Actual Output** | HTTP 200; `{"success": true, "store_id": 3, "message": "Store created successfully"}` |
| **Result** | ✅ Success |

---

### TC-12 to TC-14 — GET/PUT /api/settings

---

**TC-12**
| Field | Value |
|-------|-------|
| **API** | `GET /api/settings` |
| **Input** | *(none)* |
| **Expected Output** | HTTP 200; `{"success": true, "settings": {"paid_leaves_per_month": "4"}}` |
| **Actual Output** | HTTP 200; `{"success": true, "settings": {"paid_leaves_per_month": "4"}}` |
| **Result** | ✅ Success |

---

**TC-13**
| Field | Value |
|-------|-------|
| **API** | `PUT /api/settings/paid_leaves` |
| **Input** | `{"paid_leaves": 6}` |
| **Expected Output** | HTTP 200; setting updated; subsequent GET returns `"6"` |
| **Actual Output** | HTTP 200; `{"success": true, "message": "Paid leaves setting updated"}`; GET confirms value `"6"` |
| **Result** | ✅ Success |

---

**TC-14**
| Field | Value |
|-------|-------|
| **API** | `PUT /api/settings/paid_leaves` |
| **Input** | `{"paid_leaves": 0}` |
| **Expected Output** | HTTP 200; zero leaves is valid |
| **Actual Output** | HTTP 200; `{"success": true, "message": "Paid leaves setting updated"}` |
| **Result** | ✅ Success |

---

### TC-15 to TC-26 — Employee APIs

---

**TC-15**
| Field | Value |
|-------|-------|
| **API** | `GET /api/employees` |
| **Input** | *(empty database)* |
| **Expected Output** | HTTP 200; `{"success": true, "employees": []}` |
| **Actual Output** | HTTP 200; `{"success": true, "employees": []}` |
| **Result** | ✅ Success |

---

**TC-16**
| Field | Value |
|-------|-------|
| **API** | `POST /api/employees` |
| **Input** | `{"name": "Ravi Kumar", "phone": "9876543210", "date_of_joining": "2024-01-15", "role_type": "Picking", "base_monthly_salary": 28000, "store_id": 1, ...}` |
| **Expected Output** | HTTP 200; `{"success": true, "employee_id": <int>, "username": "9876543210", "password": <str>}` |
| **Actual Output** | HTTP 200; `{"success": true, "employee_id": 1, "user_id": 2, "username": "9876543210", "password": "aB3xK9mZ", "message": "Employee created successfully"}` |
| **Result** | ✅ Success |

---

**TC-17**
| Field | Value |
|-------|-------|
| **API** | `POST /api/employees` |
| **Input** | Same phone number used twice: `{"phone": "9876543210", ...}` |
| **Expected Output** | HTTP 400; `{"success": false, "message": "UNIQUE constraint failed: users.username"}` |
| **Actual Output** | HTTP 400; `{"success": false, "message": "UNIQUE constraint failed: users.username"}` *(after Bug 2 fix)* |
| **Result** | ✅ Success *(was unhandled 500 before fix)* |

---

**TC-18**
| Field | Value |
|-------|-------|
| **API** | `GET /api/employees/<id>` |
| **Input** | `employee_id = 1` (existing employee) |
| **Expected Output** | HTTP 200; employee object with name, salary, store_name |
| **Actual Output** | HTTP 200; `{"success": true, "employee": {"id": 1, "name": "Ravi Kumar", ...}}` |
| **Result** | ✅ Success |

---

**TC-19**
| Field | Value |
|-------|-------|
| **API** | `GET /api/employees/<id>` |
| **Input** | `employee_id = 9999` |
| **Expected Output** | HTTP 404; `{"success": false, "message": "Employee not found"}` |
| **Actual Output** | HTTP 404; `{"success": false, "message": "Employee not found"}` |
| **Result** | ✅ Success |

---

**TC-20**
| Field | Value |
|-------|-------|
| **API** | `PUT /api/employees/<id>` |
| **Input** | `{"name": "Ravi Kumar Updated", "base_monthly_salary": 32000, "role_type": "Audit", ...}` |
| **Expected Output** | HTTP 200; GET confirms updated fields |
| **Actual Output** | HTTP 200; subsequent GET shows `base_monthly_salary: 32000` and `role_type: "Audit"` |
| **Result** | ✅ Success |

---

**TC-21**
| Field | Value |
|-------|-------|
| **API** | `POST /api/employees/<id>/archive` |
| **Input** | `{"is_archived": 1}` |
| **Expected Output** | HTTP 200; employee absent from `GET /api/employees` but visible with `?include_archived=true` |
| **Actual Output** | HTTP 200; `{"success": true, "message": "Employee archived successfully"}`; list confirms absence |
| **Result** | ✅ Success |

---

**TC-22**
| Field | Value |
|-------|-------|
| **API** | `POST /api/employees/<id>/archive` |
| **Input** | `{"is_archived": 0}` (unarchive) |
| **Expected Output** | HTTP 200; employee reappears in `GET /api/employees` |
| **Actual Output** | HTTP 200; `{"success": true, "message": "Employee activated successfully"}` |
| **Result** | ✅ Success |

---

**TC-23**
| Field | Value |
|-------|-------|
| **API** | `GET /api/employees?include_archived=true` |
| **Input** | After archiving one employee |
| **Expected Output** | Both active and archived employees returned |
| **Actual Output** | Response includes archived employee with `is_archived: 1` |
| **Result** | ✅ Success |

---

**TC-24**
| Field | Value |
|-------|-------|
| **API** | `GET /api/employees?store_id=2` |
| **Input** | Two employees in store 2, one in store 3 |
| **Expected Output** | Only employees with `store_id = 2` returned |
| **Actual Output** | Response contains exactly the 2 employees from store 2 |
| **Result** | ✅ Success |

---

**TC-25**
| Field | Value |
|-------|-------|
| **API** | `POST /api/employees/<id>/reset_password` |
| **Input** | `employee_id = 1` |
| **Expected Output** | HTTP 200; `{"success": true, "new_password": <8-char string>}` |
| **Actual Output** | HTTP 200; `{"success": true, "new_password": "mN5pQxR2", "message": "Password reset successfully"}` |
| **Result** | ✅ Success |

---

**TC-26**
| Field | Value |
|-------|-------|
| **API** | `POST /api/employees/<id>/reset_password` |
| **Input** | `employee_id = 9999` |
| **Expected Output** | HTTP 404; `success: false` |
| **Actual Output** | HTTP 404; `{"success": false, "message": "Employee user account not found"}` |
| **Result** | ✅ Success |

---

### TC-27 to TC-34 — Attendance APIs

---

**TC-27**
| Field | Value |
|-------|-------|
| **API** | `POST /api/attendance` |
| **Input** | `{"employee_id": 1, "date": "2024-03-15", "status": "Present", "overtime_hours": 0}` |
| **Expected Output** | HTTP 200; `{"success": true, "message": "Attendance marked successfully"}` |
| **Actual Output** | HTTP 200; `{"success": true, "message": "Attendance marked successfully"}` |
| **Result** | ✅ Success |

---

**TC-28**
| Field | Value |
|-------|-------|
| **API** | `POST /api/attendance` |
| **Input** | `{"employee_id": 1, "date": "2024-03-16", "status": "Absent", "overtime_hours": 0}` |
| **Expected Output** | HTTP 200; record stored with status Absent |
| **Actual Output** | HTTP 200; `{"success": true, "message": "Attendance marked successfully"}` |
| **Result** | ✅ Success |

---

**TC-29**
| Field | Value |
|-------|-------|
| **API** | `POST /api/attendance` |
| **Input** | `{"employee_id": 1, "date": "2024-03-17", "status": "Half-day", "overtime_hours": 0}` |
| **Expected Output** | HTTP 200; Half-day stored |
| **Actual Output** | HTTP 200; `{"success": true, "message": "Attendance marked successfully"}` |
| **Result** | ✅ Success |

---

**TC-30**
| Field | Value |
|-------|-------|
| **API** | `POST /api/attendance` *(upsert test)* |
| **Input** | First call: `{"date": "2024-03-19", "status": "Present", ...}`, Second call: same date with `"status": "Absent"` |
| **Expected Output** | GET for that date returns 1 record with status Absent |
| **Actual Output** | GET returns exactly 1 record; `status: "Absent"` |
| **Result** | ✅ Success |

---

**TC-31**
| Field | Value |
|-------|-------|
| **API** | `POST /api/attendance` |
| **Input** | `{"status": "Present", "overtime_hours": 3.5, ...}` |
| **Expected Output** | HTTP 200; `overtime_hours: 3.5` stored |
| **Actual Output** | HTTP 200; GET confirms `overtime_hours: 3.5` |
| **Result** | ✅ Success |

---

**TC-32**
| Field | Value |
|-------|-------|
| **API** | `GET /api/attendance?employee_id=1` |
| **Input** | After marking 3 attendance records for employee 1 |
| **Expected Output** | 3 records all with `employee_id: 1` |
| **Actual Output** | 3 records returned, all filtered to employee 1 |
| **Result** | ✅ Success |

---

**TC-33**
| Field | Value |
|-------|-------|
| **API** | `GET /api/attendance?start_date=2024-03-10&end_date=2024-03-20` |
| **Input** | Records exist on 2024-03-01, 2024-03-15, 2024-03-31 |
| **Expected Output** | Only 2024-03-15 returned |
| **Actual Output** | Response contains 2024-03-15 only |
| **Result** | ✅ Success |

---

**TC-34**
| Field | Value |
|-------|-------|
| **API** | `GET /api/attendance` *(no filters, empty DB)* |
| **Input** | Empty database |
| **Expected Output** | `{"success": true, "attendance": []}` |
| **Actual Output** | `{"success": true, "attendance": []}` |
| **Result** | ✅ Success |

---

### TC-35 to TC-41 — Incentive APIs

---

**TC-35**
| Field | Value |
|-------|-------|
| **API** | `POST /api/incentives` |
| **Input** | `{"employee_id": 1, "amount": 500, "incentive_type": "daily_performance", "month": 3, "year": 2024, "description": "Exceeded target"}` |
| **Expected Output** | HTTP 200; `{"success": true, "incentive_id": <int>}` |
| **Actual Output** | HTTP 200; `{"success": true, "incentive_id": 1, "message": "Incentive added successfully"}` |
| **Result** | ✅ Success |

---

**TC-36**
| Field | Value |
|-------|-------|
| **API** | `POST /api/incentives` |
| **Input** | `{"incentive_type": "monthly_bonus", "amount": 2000, ...}` |
| **Expected Output** | HTTP 200; monthly_bonus stored |
| **Actual Output** | HTTP 200; `{"success": true, "incentive_id": 2, ...}` |
| **Result** | ✅ Success |

---

**TC-37**
| Field | Value |
|-------|-------|
| **API** | `GET /api/incentives?employee_id=1&month=3&year=2024` |
| **Input** | After adding 2 incentives |
| **Expected Output** | Returns both incentives for employee 1 in March 2024 |
| **Actual Output** | 2 incentives returned, both with `employee_id: 1, month: 3, year: 2024` |
| **Result** | ✅ Success |

---

**TC-38**
| Field | Value |
|-------|-------|
| **API** | `DELETE /api/incentives/<id>` |
| **Input** | `incentive_id = 1` |
| **Expected Output** | HTTP 200; subsequent GET no longer contains that record |
| **Actual Output** | HTTP 200; `{"success": true, "message": "Incentive deleted successfully"}`; GET confirms deletion |
| **Result** | ✅ Success |

---

**TC-39**
| Field | Value |
|-------|-------|
| **API** | `DELETE /api/incentives/<id>` *(non-existent ID)* |
| **Input** | `incentive_id = 9999` |
| **Expected Output** | HTTP 200 (idempotent delete) |
| **Actual Output** | HTTP 200; `{"success": true, "message": "Incentive deleted successfully"}` |
| **Result** | ✅ Success |

---

**TC-40**
| Field | Value |
|-------|-------|
| **API** | `GET /api/incentives?month=4&year=2024` |
| **Input** | Incentives added for month 3 and month 4 |
| **Expected Output** | Only month 4 incentives returned |
| **Actual Output** | All returned records have `month: 4` |
| **Result** | ✅ Success |

---

**TC-41**
| Field | Value |
|-------|-------|
| **API** | `GET /api/incentives` *(empty DB)* |
| **Input** | Empty database |
| **Expected Output** | `{"success": true, "incentives": []}` |
| **Actual Output** | `{"success": true, "incentives": []}` |
| **Result** | ✅ Success |

---

### TC-42 to TC-46 — Penalty APIs

---

**TC-42**
| Field | Value |
|-------|-------|
| **API** | `POST /api/penalties` |
| **Input** | `{"employee_id": 1, "amount": 200, "penalty_type": "daily", "date": "2024-03-10", "month": 3, "year": 2024, "description": "Late arrival"}` |
| **Expected Output** | HTTP 200; `{"success": true, "penalty_id": <int>}` |
| **Actual Output** | HTTP 200; `{"success": true, "penalty_id": 1, "message": "Penalty added successfully"}` |
| **Result** | ✅ Success |

---

**TC-43**
| Field | Value |
|-------|-------|
| **API** | `POST /api/penalties` |
| **Input** | `{"penalty_type": "monthly", "amount": 1000, ...}` |
| **Expected Output** | HTTP 200; monthly penalty stored |
| **Actual Output** | HTTP 200; `{"success": true, "penalty_id": 2, ...}` |
| **Result** | ✅ Success |

---

**TC-44**
| Field | Value |
|-------|-------|
| **API** | `GET /api/penalties?employee_id=1` |
| **Input** | After adding 2 penalties |
| **Expected Output** | Both penalty records returned |
| **Actual Output** | 2 records returned with `employee_id: 1` |
| **Result** | ✅ Success |

---

**TC-45**
| Field | Value |
|-------|-------|
| **API** | `DELETE /api/penalties/<id>` |
| **Input** | `penalty_id = 1` |
| **Expected Output** | HTTP 200; record gone from GET |
| **Actual Output** | HTTP 200; GET confirms deletion |
| **Result** | ✅ Success |

---

**TC-46**
| Field | Value |
|-------|-------|
| **API** | `GET /api/penalties` *(empty DB)* |
| **Input** | Empty database |
| **Expected Output** | `{"success": true, "penalties": []}` |
| **Actual Output** | `{"success": true, "penalties": []}` |
| **Result** | ✅ Success |

---

### TC-47 to TC-54 — Salary Advance APIs

---

**TC-47**
| Field | Value |
|-------|-------|
| **API** | `GET /api/advance/eligibility` *(missing params)* |
| **Input** | No query parameters |
| **Expected Output** | HTTP 400; `{"success": false, "message": "Missing required parameters"}` |
| **Actual Output** | HTTP 400; `{"success": false, "message": "Missing required parameters"}` |
| **Result** | ✅ Success |

---

**TC-48**
| Field | Value |
|-------|-------|
| **API** | `GET /api/advance/eligibility` *(non-existent employee)* |
| **Input** | `?employee_id=9999&day=15&month=3&year=2024` |
| **Expected Output** | HTTP 404; `success: false` |
| **Actual Output** | HTTP 404; `{"success": false, "message": "Employee not found"}` |
| **Result** | ✅ Success |

---

**TC-49**
| Field | Value |
|-------|-------|
| **API** | `GET /api/advance/eligibility` *(day ≤ 7)* |
| **Input** | `?employee_id=1&day=5&month=3&year=2024` |
| **Expected Output** | `{"eligible_days": 0, "max_advance_amount": 0.0}` |
| **Actual Output** | `{"success": true, "eligible_days": 0, "per_day_salary": 967.74, "max_advance_amount": 0.0}` |
| **Result** | ✅ Success |

---

**TC-50**
| Field | Value |
|-------|-------|
| **API** | `GET /api/advance/eligibility` *(day > 7)* |
| **Input** | Employee with salary ₹30,000; `?day=15&month=3&year=2024` (March = 31 days) |
| **Expected Output** | `eligible_days = 8`, `per_day_salary ≈ 967.74`, `max_advance_amount ≈ 7741.92` |
| **Actual Output** | `{"eligible_days": 8, "per_day_salary": 967.74, "max_advance_amount": 7741.94}` |
| **Result** | ✅ Success |

---

**TC-51**
| Field | Value |
|-------|-------|
| **API** | `GET /api/advance/eligibility` *(7-day boundary)* |
| **Input** | `?day=7&month=3&year=2024` |
| **Expected Output** | `eligible_days = 0`, `max_advance_amount = 0.0` |
| **Actual Output** | `{"eligible_days": 0, "max_advance_amount": 0.0}` |
| **Result** | ✅ Success |

---

**TC-52**
| Field | Value |
|-------|-------|
| **API** | `POST /api/advance` |
| **Input** | `{"employee_id": 1, "amount": 5000, "request_date": "2024-03-15", "month": 3, "year": 2024, "day_of_month": 15, "eligible_days": 8}` |
| **Expected Output** | HTTP 200; `{"success": true, "advance_id": <int>}` |
| **Actual Output** | HTTP 200; `{"success": true, "advance_id": 1, "message": "Advance requested successfully"}` |
| **Result** | ✅ Success |

---

**TC-53**
| Field | Value |
|-------|-------|
| **API** | `GET /api/advance?employee_id=1&month=3&year=2024` |
| **Input** | After creating one advance |
| **Expected Output** | One record with `status: "approved"` |
| **Actual Output** | `[{"id": 1, "amount": 5000, "status": "approved", ...}]` |
| **Result** | ✅ Success |

---

**TC-54**
| Field | Value |
|-------|-------|
| **API** | `GET /api/advance` *(empty)* |
| **Input** | Empty database |
| **Expected Output** | `{"success": true, "advances": []}` |
| **Actual Output** | `{"success": true, "advances": []}` |
| **Result** | ✅ Success |

---

### TC-55 to TC-67 — Payroll APIs

---

**TC-55**
| Field | Value |
|-------|-------|
| **API** | `POST /api/payroll/compute` *(missing params)* |
| **Input** | `{}` |
| **Expected Output** | HTTP 400; `{"success": false, "message": "Month and year required"}` |
| **Actual Output** | HTTP 400; `{"success": false, "message": "Month and year required"}` |
| **Result** | ✅ Success |

---

**TC-56**
| Field | Value |
|-------|-------|
| **API** | `POST /api/payroll/compute` *(no employees)* |
| **Input** | `{"month": 3, "year": 2024}` with empty employee table |
| **Expected Output** | HTTP 200; `{"success": true, "computed": []}` |
| **Actual Output** | HTTP 200; `{"success": true, "message": "Payroll computed for 0 employees", "computed": []}` |
| **Result** | ✅ Success |

---

**TC-57**
| Field | Value |
|-------|-------|
| **API** | `POST /api/payroll/compute` *(basic salary)* |
| **Input** | Employee with ₹30,000 salary; 20 Present days; `{"month": 3, "year": 2024}` |
| **Expected Output** | `net_salary > 0` |
| **Actual Output** | `{"net_salary": 30000.0}` *(all days present, no deductions)* |
| **Result** | ✅ Success |

---

**TC-58** ⚠️ *Bug discovered and fixed*
| Field | Value |
|-------|-------|
| **API** | `POST /api/payroll/compute` *(with incentive)* |
| **Input** | Employee with ₹30,000 salary + ₹1,000 monthly_bonus incentive |
| **Expected Output** | `net_salary = 31000.0` |
| **Actual Output (BEFORE FIX)** | HTTP 500; `sqlite3.IntegrityError: CHECK constraint failed: detail_type IN ('incentive_daily', 'incentive_monthly', ...)` |
| **Actual Output (AFTER FIX)** | HTTP 200; `net_salary = 31000.0` |
| **Result** | ✅ Success *(after fix)* |

---

**TC-59**
| Field | Value |
|-------|-------|
| **API** | `POST /api/payroll/compute` *(with penalty)* |
| **Input** | Employee with ₹30,000 salary + ₹500 monthly penalty |
| **Expected Output** | `net_salary = 29500.0` (reduced by penalty) |
| **Actual Output** | `net_salary = 29500.0` |
| **Result** | ✅ Success |

---

**TC-60**
| Field | Value |
|-------|-------|
| **API** | `POST /api/payroll/compute` *(with salary advance)* |
| **Input** | Employee with ₹30,000 salary + ₹2,000 approved advance |
| **Expected Output** | `net_salary` reduced by exactly ₹2,000 |
| **Actual Output** | Difference between salary with/without advance is exactly 2000.0 |
| **Result** | ✅ Success |

---

**TC-61**
| Field | Value |
|-------|-------|
| **API** | `POST /api/payroll/compute` *(unpaid leave deduction)* |
| **Input** | Employee with 4 paid leaves allowed; 9 absent days marked in March |
| **Expected Output** | `unpaid_leaves > 0`, `leave_deduction > 0` |
| **Actual Output** | `unpaid_leaves: 5`, `leave_deduction: 4838.71` |
| **Result** | ✅ Success |

---

**TC-62**
| Field | Value |
|-------|-------|
| **API** | `GET /api/payroll?employee_id=1&month=3&year=2024` |
| **Input** | After computing payroll |
| **Expected Output** | One payroll record returned |
| **Actual Output** | `[{"id": 1, "employee_name": "...", "net_salary": ..., "status": "draft"}]` |
| **Result** | ✅ Success |

---

**TC-63**
| Field | Value |
|-------|-------|
| **API** | `GET /api/payroll/<id>/details` |
| **Input** | `payroll_id = 1` (payroll with advance) |
| **Expected Output** | Array of detail lines including `detail_type: "advance"` |
| **Actual Output** | `[{"detail_type": "advance", "amount": 1000.0, ...}]` |
| **Result** | ✅ Success |

---

**TC-64**
| Field | Value |
|-------|-------|
| **API** | `POST /api/payroll/<id>/finalize` |
| **Input** | `payroll_id = 1` |
| **Expected Output** | HTTP 200; payroll `status = "finalized"` |
| **Actual Output** | HTTP 200; GET confirms `status: "finalized"` |
| **Result** | ✅ Success |

---

**TC-65**
| Field | Value |
|-------|-------|
| **API** | `POST /api/payroll/<id>/finalize` *(advance status update)* |
| **Input** | Payroll with an associated approved advance |
| **Expected Output** | After finalize, advance `status = "deducted"` |
| **Actual Output** | GET `/api/advance` confirms all advances for that employee/month have `status: "deducted"` |
| **Result** | ✅ Success |

---

**TC-66**
| Field | Value |
|-------|-------|
| **API** | `GET /api/payroll/<id>/payslip` |
| **Input** | `payroll_id = 1` (valid) |
| **Expected Output** | HTTP 200; payslip with `employee_name`, `base_salary: 30000`, `net_salary > 0` |
| **Actual Output** | HTTP 200; `{"success": true, "payslip": {"employee_name": "Test Employee", "base_salary": 30000, ...}}` |
| **Result** | ✅ Success |

---

**TC-67**
| Field | Value |
|-------|-------|
| **API** | `GET /api/payroll/<id>/payslip` *(not found)* |
| **Input** | `payroll_id = 9999` |
| **Expected Output** | HTTP 404; `{"success": false, "message": "Payroll not found"}` |
| **Actual Output** | HTTP 404; `{"success": false, "message": "Payroll not found"}` |
| **Result** | ✅ Success |

---

### TC-68 to TC-70 — Dashboard API

---

**TC-68**
| Field | Value |
|-------|-------|
| **API** | `GET /api/dashboard/stats` *(empty DB)* |
| **Input** | Empty employee/attendance/advance tables |
| **Expected Output** | HTTP 200; all counts = 0; all 4 keys present |
| **Actual Output** | `{"success": true, "active_employees": 0, "archived_employees": 0, "today_attendance": 0, "pending_advances": 0}` |
| **Result** | ✅ Success |

---

**TC-69**
| Field | Value |
|-------|-------|
| **API** | `GET /api/dashboard/stats` *(with data)* |
| **Input** | 1 active employee created |
| **Expected Output** | `active_employees >= 1` |
| **Actual Output** | `{"active_employees": 1, "archived_employees": 0, ...}` |
| **Result** | ✅ Success |

---

**TC-70**
| Field | Value |
|-------|-------|
| **API** | `GET /api/dashboard/stats?store_id=1` |
| **Input** | `store_id = 1` |
| **Expected Output** | HTTP 200; stats scoped to store 1 |
| **Actual Output** | HTTP 200; returns valid counts for store 1 |
| **Result** | ✅ Success |

---

## Section D: Test Cases Showing Initial Failures (Bugs Found via Testing)

### Failed TC — Payroll compute with incentives (Bug 1 — CRITICAL)

| Field | Value |
|-------|-------|
| **API** | `POST /api/payroll/compute` |
| **Input** | Employee with `monthly_bonus` incentive of ₹1000; `{"month": 3, "year": 2024}` |
| **Expected Output** | HTTP 200; `net_salary = base_salary + 1000` |
| **Actual Output (First Run)** | HTTP 500 Internal Server Error: `sqlite3.IntegrityError: CHECK constraint failed: detail_type IN ('incentive_daily', 'incentive_monthly', 'penalty_daily', 'penalty_monthly', 'advance')` |
| **Root Cause** | `compute_payroll` inserted `f"incentive_{inc['incentive_type']}"` = `"incentive_daily_performance"` which violates the DB constraint. Allowed values are `"incentive_daily"` and `"incentive_monthly"`. |
| **Fix Applied** | Mapped incentive_type strings: `'daily_performance'` → `'incentive_daily'`, `'monthly_bonus'` → `'incentive_monthly'`. Also corrected the filter strings in `generate_payslip`. |
| **Result After Fix** | ✅ HTTP 200; correct net_salary returned |

---

### Failed TC — Create duplicate employee (Bug 2 — DB lock cascade)

| Field | Value |
|-------|-------|
| **API** | `POST /api/employees` *(then subsequent calls)* |
| **Input** | `{"phone": "9876543210", ...}` used twice (duplicate username) |
| **Expected Output** | HTTP 400 on second call; `success: false`; all subsequent API calls work normally |
| **Actual Output (Before Fix)** | First duplicate call: HTTP 500 (unhandled exception). All following requests to any endpoint: `503/500 — database is locked` |
| **Root Cause** | No try/finally in `create_employee` — on UNIQUE constraint failure, `conn.close()` was never called, leaving SQLite write-locked |
| **Fix Applied** | Wrapped INSERT block in `try/except/finally` to guarantee `conn.rollback()` + `conn.close()` and return a structured 400 error |
| **Result After Fix** | ✅ HTTP 400 on duplicate; all subsequent requests unaffected |

---

## Section E: Test Execution Summary

| Suite | Total | Passed | Failed (Before Fix) | Final Status |
|-------|-------|--------|---------------------|-------------|
| Unit Tests (test_unit.py) | 71 | 71 | 2 | ✅ 71/71 |
| Integration Tests (test_integration.py) | 24 | 24 | 10 | ✅ 24/24 |
| **Total** | **95** | **95** | **12** | **✅ 95/95** |
