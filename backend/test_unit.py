"""
Unit Tests for Workforce & Payroll Management Backend API
Tests all API endpoints in isolation using a temporary in-memory database.
"""
import pytest
import json
import sqlite3
import os
import sys
import tempfile

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import app as backend_app


# ============================================================
# FIXTURES
# ============================================================

@pytest.fixture
def client():
    """Create a test client with a fresh in-memory database for each test."""
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    backend_app.app.config['TESTING'] = True
    backend_app.DB_PATH = db_path

    # Initialize fresh schema
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.executescript("""
        PRAGMA foreign_keys = ON;

        CREATE TABLE IF NOT EXISTS stores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS global_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            setting_key TEXT UNIQUE NOT NULL,
            setting_value TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        INSERT OR IGNORE INTO global_settings (setting_key, setting_value)
        VALUES ('paid_leaves_per_month', '4');

        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('admin', 'manager', 'employee')),
            email TEXT,
            phone TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            name TEXT NOT NULL,
            address TEXT,
            email TEXT,
            phone TEXT,
            date_of_joining DATE NOT NULL,
            role_type TEXT NOT NULL CHECK(role_type IN ('Picking', 'Put-away', 'Audit')),
            base_monthly_salary REAL NOT NULL,
            store_id INTEGER,
            is_archived INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
            FOREIGN KEY (store_id) REFERENCES stores(id) ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            date DATE NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('Present', 'Absent', 'Half-day')),
            overtime_hours REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
            UNIQUE(employee_id, date)
        );

        CREATE TABLE IF NOT EXISTS incentives (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            incentive_type TEXT NOT NULL CHECK(incentive_type IN ('daily_performance', 'monthly_bonus')),
            date DATE,
            month INTEGER,
            year INTEGER,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS penalties (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            penalty_type TEXT NOT NULL CHECK(penalty_type IN ('daily', 'monthly')),
            date DATE,
            month INTEGER,
            year INTEGER,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS salary_advances (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            request_date DATE NOT NULL,
            month INTEGER NOT NULL,
            year INTEGER NOT NULL,
            day_of_month INTEGER NOT NULL,
            eligible_days INTEGER NOT NULL,
            status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'approved', 'rejected', 'deducted')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS payroll (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            month INTEGER NOT NULL,
            year INTEGER NOT NULL,
            base_salary REAL NOT NULL,
            per_day_salary REAL NOT NULL,
            total_days_in_month INTEGER NOT NULL,
            days_present INTEGER DEFAULT 0,
            days_absent INTEGER DEFAULT 0,
            days_half_day INTEGER DEFAULT 0,
            paid_leaves_allowed INTEGER NOT NULL,
            unpaid_leaves INTEGER DEFAULT 0,
            leave_deduction REAL DEFAULT 0,
            total_overtime_hours REAL DEFAULT 0,
            overtime_pay REAL DEFAULT 0,
            total_incentives REAL DEFAULT 0,
            total_penalties REAL DEFAULT 0,
            salary_advances_deducted REAL DEFAULT 0,
            net_salary REAL NOT NULL,
            status TEXT DEFAULT 'draft' CHECK(status IN ('draft', 'finalized')),
            payslip_pdf_path TEXT,
            qr_code_path TEXT,
            drive_link TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            finalized_at TIMESTAMP,
            FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
            UNIQUE(employee_id, month, year)
        );

        CREATE TABLE IF NOT EXISTS payroll_details (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            payroll_id INTEGER NOT NULL,
            detail_type TEXT NOT NULL CHECK(detail_type IN ('incentive_daily', 'incentive_monthly', 'penalty_daily', 'penalty_monthly', 'advance')),
            description TEXT,
            amount REAL NOT NULL,
            date DATE,
            FOREIGN KEY (payroll_id) REFERENCES payroll(id) ON DELETE CASCADE
        );

        INSERT OR IGNORE INTO users (username, password, role, email)
        VALUES ('admin', 'admin123', 'admin', 'admin@company.com');

        INSERT OR IGNORE INTO stores (name, address)
        VALUES ('Main Store', '123 Main Street');
    """)
    conn.commit()
    conn.close()

    with backend_app.app.test_client() as client:
        yield client

    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def seeded_client(client):
    """Test client with a seeded employee for tests that need existing data."""
    # Create a store
    client.post('/api/stores', json={'name': 'Test Store', 'address': '1 Test Ave'})

    # Create an employee
    resp = client.post('/api/employees', json={
        'name': 'Test Employee',
        'address': '99 Test St',
        'email': 'test@example.com',
        'phone': '9876543210',
        'date_of_joining': '2024-01-01',
        'role_type': 'Picking',
        'base_monthly_salary': 30000,
        'store_id': 1
    })
    data = json.loads(resp.data)
    return client, data


# ============================================================
# 1. AUTHENTICATION API TESTS
# ============================================================

class TestLogin:
    def test_login_valid_credentials(self, client):
        """POST /api/login – valid admin credentials returns success."""
        resp = client.post('/api/login', json={'username': 'admin', 'password': 'admin123'})
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert data['success'] is True
        assert data['role'] == 'admin'
        assert 'user_id' in data

    def test_login_invalid_password(self, client):
        """POST /api/login – wrong password returns 401."""
        resp = client.post('/api/login', json={'username': 'admin', 'password': 'wrong'})
        data = json.loads(resp.data)
        assert resp.status_code == 401
        assert data['success'] is False

    def test_login_nonexistent_user(self, client):
        """POST /api/login – unknown user returns 401."""
        resp = client.post('/api/login', json={'username': 'ghost', 'password': 'nope'})
        assert resp.status_code == 401

    def test_login_missing_fields(self, client):
        """POST /api/login – missing password should fail gracefully."""
        resp = client.post('/api/login', json={'username': 'admin'})
        assert resp.status_code == 401

    def test_login_empty_credentials(self, client):
        """POST /api/login – empty strings should fail."""
        resp = client.post('/api/login', json={'username': '', 'password': ''})
        assert resp.status_code == 401


class TestChangePassword:
    def test_change_password_success(self, client):
        """POST /api/change_password – correct old password updates successfully."""
        # Login first to get user_id
        login_resp = client.post('/api/login', json={'username': 'admin', 'password': 'admin123'})
        user_id = json.loads(login_resp.data)['user_id']

        resp = client.post('/api/change_password', json={
            'user_id': user_id,
            'old_password': 'admin123',
            'new_password': 'newpassword'
        })
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert data['success'] is True

        # Verify new password works
        login_resp2 = client.post('/api/login', json={'username': 'admin', 'password': 'newpassword'})
        assert json.loads(login_resp2.data)['success'] is True

    def test_change_password_wrong_old_password(self, client):
        """POST /api/change_password – wrong old password returns 400."""
        resp = client.post('/api/change_password', json={
            'user_id': 1,
            'old_password': 'wrongold',
            'new_password': 'newpass'
        })
        data = json.loads(resp.data)
        assert resp.status_code == 400
        assert data['success'] is False

    def test_change_password_invalid_user_id(self, client):
        """POST /api/change_password – non-existent user_id returns 400."""
        resp = client.post('/api/change_password', json={
            'user_id': 9999,
            'old_password': 'admin123',
            'new_password': 'new'
        })
        assert resp.status_code == 400


# ============================================================
# 2. STORE API TESTS
# ============================================================

class TestStores:
    def test_get_stores_empty(self, client):
        """GET /api/stores – returns list (has default Main Store)."""
        resp = client.get('/api/stores')
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert data['success'] is True
        assert isinstance(data['stores'], list)
        assert len(data['stores']) >= 1

    def test_create_store(self, client):
        """POST /api/stores – creates store and returns store_id."""
        resp = client.post('/api/stores', json={'name': 'North Store', 'address': '5 North Rd'})
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert data['success'] is True
        assert 'store_id' in data

    def test_create_store_no_address(self, client):
        """POST /api/stores – address is optional."""
        resp = client.post('/api/stores', json={'name': 'Minimal Store'})
        data = json.loads(resp.data)
        assert data['success'] is True

    def test_get_stores_after_creation(self, client):
        """GET /api/stores – newly created store appears in list."""
        client.post('/api/stores', json={'name': 'East Store', 'address': '10 East'})
        resp = client.get('/api/stores')
        names = [s['name'] for s in json.loads(resp.data)['stores']]
        assert 'East Store' in names


# ============================================================
# 3. GLOBAL SETTINGS API TESTS
# ============================================================

class TestSettings:
    def test_get_settings(self, client):
        """GET /api/settings – returns paid_leaves_per_month."""
        resp = client.get('/api/settings')
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert data['success'] is True
        assert 'paid_leaves_per_month' in data['settings']

    def test_update_paid_leaves(self, client):
        """PUT /api/settings/paid_leaves – updates setting value."""
        resp = client.put('/api/settings/paid_leaves', json={'paid_leaves': 6})
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert data['success'] is True

        # Verify persisted
        get_resp = client.get('/api/settings')
        settings = json.loads(get_resp.data)['settings']
        assert settings['paid_leaves_per_month'] == '6'

    def test_update_paid_leaves_to_zero(self, client):
        """PUT /api/settings/paid_leaves – zero is a valid value."""
        resp = client.put('/api/settings/paid_leaves', json={'paid_leaves': 0})
        assert json.loads(resp.data)['success'] is True


# ============================================================
# 4. EMPLOYEE API TESTS
# ============================================================

class TestEmployees:
    def test_get_employees_empty(self, client):
        """GET /api/employees – empty DB returns empty list."""
        resp = client.get('/api/employees')
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert data['success'] is True
        assert data['employees'] == []

    def test_create_employee_success(self, client):
        """POST /api/employees – creates employee and linked user account."""
        resp = client.post('/api/employees', json={
            'name': 'Alice Smith',
            'address': '1 Alice Lane',
            'email': 'alice@example.com',
            'phone': '1234567890',
            'date_of_joining': '2024-03-01',
            'role_type': 'Picking',
            'base_monthly_salary': 25000,
            'store_id': 1
        })
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert data['success'] is True
        assert 'employee_id' in data
        assert 'user_id' in data
        assert 'username' in data
        assert 'password' in data

    def test_create_employee_all_role_types(self, client):
        """POST /api/employees – accepts all valid role_type values."""
        for i, role in enumerate(['Picking', 'Put-away', 'Audit']):
            resp = client.post('/api/employees', json={
                'name': f'Employee {i}',
                'address': 'Test',
                'email': f'e{i}@test.com',
                'phone': f'100000000{i}',
                'date_of_joining': '2024-01-01',
                'role_type': role,
                'base_monthly_salary': 20000,
                'store_id': 1
            })
            assert json.loads(resp.data)['success'] is True, f"Failed for role: {role}"

    def test_get_employee_by_id(self, seeded_client):
        """GET /api/employees/<id> – returns specific employee data."""
        client, seed_data = seeded_client
        emp_id = seed_data['employee_id']
        resp = client.get(f'/api/employees/{emp_id}')
        data = json.loads(resp.data)
        assert data['success'] is True
        assert data['employee']['name'] == 'Test Employee'

    def test_get_employee_not_found(self, client):
        """GET /api/employees/<id> – non-existent id returns 404."""
        resp = client.get('/api/employees/9999')
        assert resp.status_code == 404

    def test_update_employee(self, seeded_client):
        """PUT /api/employees/<id> – updates employee fields."""
        client, seed_data = seeded_client
        emp_id = seed_data['employee_id']
        resp = client.put(f'/api/employees/{emp_id}', json={
            'name': 'Updated Name',
            'address': 'New Address',
            'email': 'updated@test.com',
            'phone': '9999999999',
            'role_type': 'Audit',
            'base_monthly_salary': 35000,
            'store_id': 1
        })
        data = json.loads(resp.data)
        assert data['success'] is True

        # Verify update persisted
        get_resp = client.get(f'/api/employees/{emp_id}')
        emp = json.loads(get_resp.data)['employee']
        assert emp['name'] == 'Updated Name'
        assert emp['base_monthly_salary'] == 35000

    def test_archive_employee(self, seeded_client):
        """POST /api/employees/<id>/archive – archives employee."""
        client, seed_data = seeded_client
        emp_id = seed_data['employee_id']

        resp = client.post(f'/api/employees/{emp_id}/archive', json={'is_archived': 1})
        assert json.loads(resp.data)['success'] is True

        # Should not appear in default listing
        list_resp = client.get('/api/employees')
        employees = json.loads(list_resp.data)['employees']
        ids = [e['id'] for e in employees]
        assert emp_id not in ids

    def test_unarchive_employee(self, seeded_client):
        """POST /api/employees/<id>/archive – can unarchive employee."""
        client, seed_data = seeded_client
        emp_id = seed_data['employee_id']

        client.post(f'/api/employees/{emp_id}/archive', json={'is_archived': 1})
        client.post(f'/api/employees/{emp_id}/archive', json={'is_archived': 0})

        list_resp = client.get('/api/employees')
        employees = json.loads(list_resp.data)['employees']
        ids = [e['id'] for e in employees]
        assert emp_id in ids

    def test_include_archived_param(self, seeded_client):
        """GET /api/employees?include_archived=true – includes archived employees."""
        client, seed_data = seeded_client
        emp_id = seed_data['employee_id']
        client.post(f'/api/employees/{emp_id}/archive', json={'is_archived': 1})

        resp = client.get('/api/employees?include_archived=true')
        employees = json.loads(resp.data)['employees']
        ids = [e['id'] for e in employees]
        assert emp_id in ids

    def test_filter_employees_by_store(self, client):
        """GET /api/employees?store_id=X – filters by store."""
        client.post('/api/stores', json={'name': 'Store A', 'address': 'A'})
        client.post('/api/stores', json={'name': 'Store B', 'address': 'B'})

        client.post('/api/employees', json={
            'name': 'EmpA', 'address': 'a', 'email': 'a@a.com', 'phone': '111',
            'date_of_joining': '2024-01-01', 'role_type': 'Picking',
            'base_monthly_salary': 10000, 'store_id': 2
        })
        client.post('/api/employees', json={
            'name': 'EmpB', 'address': 'b', 'email': 'b@b.com', 'phone': '222',
            'date_of_joining': '2024-01-01', 'role_type': 'Picking',
            'base_monthly_salary': 10000, 'store_id': 3
        })

        resp = client.get('/api/employees?store_id=2')
        employees = json.loads(resp.data)['employees']
        assert all(e['store_id'] == 2 for e in employees)

    def test_reset_employee_password(self, seeded_client):
        """POST /api/employees/<id>/reset_password – returns new password."""
        client, seed_data = seeded_client
        emp_id = seed_data['employee_id']

        resp = client.post(f'/api/employees/{emp_id}/reset_password')
        data = json.loads(resp.data)
        assert data['success'] is True
        assert 'new_password' in data
        assert len(data['new_password']) > 0

    def test_reset_password_nonexistent_employee(self, client):
        """POST /api/employees/<id>/reset_password – 404 for non-existent."""
        resp = client.post('/api/employees/9999/reset_password')
        assert resp.status_code == 404


# ============================================================
# 5. ATTENDANCE API TESTS
# ============================================================

class TestAttendance:
    def test_get_attendance_empty(self, client):
        """GET /api/attendance – returns empty list initially."""
        resp = client.get('/api/attendance')
        data = json.loads(resp.data)
        assert data['success'] is True
        assert data['attendance'] == []

    def test_mark_attendance_present(self, seeded_client):
        """POST /api/attendance – marks employee as Present."""
        client, seed_data = seeded_client
        emp_id = seed_data['employee_id']

        resp = client.post('/api/attendance', json={
            'employee_id': emp_id,
            'date': '2024-03-15',
            'status': 'Present',
            'overtime_hours': 0
        })
        assert json.loads(resp.data)['success'] is True

    def test_mark_attendance_absent(self, seeded_client):
        """POST /api/attendance – marks employee as Absent."""
        client, seed_data = seeded_client
        emp_id = seed_data['employee_id']

        resp = client.post('/api/attendance', json={
            'employee_id': emp_id,
            'date': '2024-03-16',
            'status': 'Absent',
            'overtime_hours': 0
        })
        assert json.loads(resp.data)['success'] is True

    def test_mark_attendance_half_day(self, seeded_client):
        """POST /api/attendance – marks employee as Half-day."""
        client, seed_data = seeded_client
        emp_id = seed_data['employee_id']

        resp = client.post('/api/attendance', json={
            'employee_id': emp_id,
            'date': '2024-03-17',
            'status': 'Half-day',
            'overtime_hours': 0
        })
        assert json.loads(resp.data)['success'] is True

    def test_mark_attendance_with_overtime(self, seeded_client):
        """POST /api/attendance – records overtime hours."""
        client, seed_data = seeded_client
        emp_id = seed_data['employee_id']

        resp = client.post('/api/attendance', json={
            'employee_id': emp_id,
            'date': '2024-03-18',
            'status': 'Present',
            'overtime_hours': 3.5
        })
        assert json.loads(resp.data)['success'] is True

    def test_update_existing_attendance(self, seeded_client):
        """POST /api/attendance – updating same date overwrites the record."""
        client, seed_data = seeded_client
        emp_id = seed_data['employee_id']

        client.post('/api/attendance', json={
            'employee_id': emp_id, 'date': '2024-03-19', 'status': 'Present', 'overtime_hours': 0
        })
        client.post('/api/attendance', json={
            'employee_id': emp_id, 'date': '2024-03-19', 'status': 'Absent', 'overtime_hours': 0
        })

        resp = client.get(f'/api/attendance?employee_id={emp_id}&start_date=2024-03-19&end_date=2024-03-19')
        records = json.loads(resp.data)['attendance']
        assert len(records) == 1
        assert records[0]['status'] == 'Absent'

    def test_get_attendance_filter_by_employee(self, seeded_client):
        """GET /api/attendance?employee_id=X – filters by employee."""
        client, seed_data = seeded_client
        emp_id = seed_data['employee_id']

        client.post('/api/attendance', json={
            'employee_id': emp_id, 'date': '2024-03-20', 'status': 'Present', 'overtime_hours': 0
        })
        resp = client.get(f'/api/attendance?employee_id={emp_id}')
        records = json.loads(resp.data)['attendance']
        assert all(r['employee_id'] == emp_id for r in records)

    def test_get_attendance_filter_by_date_range(self, seeded_client):
        """GET /api/attendance – date range filter works correctly."""
        client, seed_data = seeded_client
        emp_id = seed_data['employee_id']

        for day in ['2024-03-01', '2024-03-15', '2024-03-31']:
            client.post('/api/attendance', json={
                'employee_id': emp_id, 'date': day, 'status': 'Present', 'overtime_hours': 0
            })

        resp = client.get(f'/api/attendance?start_date=2024-03-10&end_date=2024-03-20')
        records = json.loads(resp.data)['attendance']
        dates = [r['date'] for r in records]
        assert '2024-03-15' in dates
        assert '2024-03-01' not in dates
        assert '2024-03-31' not in dates


# ============================================================
# 6. INCENTIVES API TESTS
# ============================================================

class TestIncentives:
    def test_get_incentives_empty(self, client):
        """GET /api/incentives – returns empty list initially."""
        resp = client.get('/api/incentives')
        data = json.loads(resp.data)
        assert data['success'] is True
        assert data['incentives'] == []

    def test_add_daily_performance_incentive(self, seeded_client):
        """POST /api/incentives – adds daily_performance incentive."""
        client, seed_data = seeded_client
        emp_id = seed_data['employee_id']

        resp = client.post('/api/incentives', json={
            'employee_id': emp_id,
            'amount': 500,
            'incentive_type': 'daily_performance',
            'date': '2024-03-10',
            'month': 3,
            'year': 2024,
            'description': 'Great performance'
        })
        data = json.loads(resp.data)
        assert data['success'] is True
        assert 'incentive_id' in data

    def test_add_monthly_bonus_incentive(self, seeded_client):
        """POST /api/incentives – adds monthly_bonus incentive."""
        client, seed_data = seeded_client
        emp_id = seed_data['employee_id']

        resp = client.post('/api/incentives', json={
            'employee_id': emp_id,
            'amount': 2000,
            'incentive_type': 'monthly_bonus',
            'month': 3,
            'year': 2024,
            'description': 'Monthly bonus'
        })
        assert json.loads(resp.data)['success'] is True

    def test_get_incentives_filter_by_employee(self, seeded_client):
        """GET /api/incentives?employee_id=X – filters correctly."""
        client, seed_data = seeded_client
        emp_id = seed_data['employee_id']

        client.post('/api/incentives', json={
            'employee_id': emp_id, 'amount': 300, 'incentive_type': 'daily_performance',
            'month': 4, 'year': 2024
        })
        resp = client.get(f'/api/incentives?employee_id={emp_id}')
        incentives = json.loads(resp.data)['incentives']
        assert all(i['employee_id'] == emp_id for i in incentives)

    def test_get_incentives_filter_by_month_year(self, seeded_client):
        """GET /api/incentives?month=X&year=Y – filters by month and year."""
        client, seed_data = seeded_client
        emp_id = seed_data['employee_id']

        client.post('/api/incentives', json={
            'employee_id': emp_id, 'amount': 100, 'incentive_type': 'daily_performance',
            'month': 3, 'year': 2024
        })
        client.post('/api/incentives', json={
            'employee_id': emp_id, 'amount': 200, 'incentive_type': 'monthly_bonus',
            'month': 4, 'year': 2024
        })

        resp = client.get('/api/incentives?month=3&year=2024')
        incentives = json.loads(resp.data)['incentives']
        assert all(i['month'] == 3 for i in incentives)

    def test_delete_incentive(self, seeded_client):
        """DELETE /api/incentives/<id> – deletes the incentive."""
        client, seed_data = seeded_client
        emp_id = seed_data['employee_id']

        create_resp = client.post('/api/incentives', json={
            'employee_id': emp_id, 'amount': 100, 'incentive_type': 'daily_performance',
            'month': 3, 'year': 2024
        })
        inc_id = json.loads(create_resp.data)['incentive_id']

        del_resp = client.delete(f'/api/incentives/{inc_id}')
        assert json.loads(del_resp.data)['success'] is True

        # Should no longer exist
        get_resp = client.get(f'/api/incentives?employee_id={emp_id}')
        incentives = json.loads(get_resp.data)['incentives']
        assert not any(i['id'] == inc_id for i in incentives)

    def test_delete_nonexistent_incentive(self, client):
        """DELETE /api/incentives/<id> – deleting non-existent is still 200."""
        resp = client.delete('/api/incentives/9999')
        assert resp.status_code == 200


# ============================================================
# 7. PENALTIES API TESTS
# ============================================================

class TestPenalties:
    def test_get_penalties_empty(self, client):
        """GET /api/penalties – returns empty list initially."""
        resp = client.get('/api/penalties')
        data = json.loads(resp.data)
        assert data['success'] is True
        assert data['penalties'] == []

    def test_add_daily_penalty(self, seeded_client):
        """POST /api/penalties – adds daily penalty."""
        client, seed_data = seeded_client
        emp_id = seed_data['employee_id']

        resp = client.post('/api/penalties', json={
            'employee_id': emp_id,
            'amount': 200,
            'penalty_type': 'daily',
            'date': '2024-03-10',
            'month': 3,
            'year': 2024,
            'description': 'Late arrival'
        })
        data = json.loads(resp.data)
        assert data['success'] is True
        assert 'penalty_id' in data

    def test_add_monthly_penalty(self, seeded_client):
        """POST /api/penalties – adds monthly penalty."""
        client, seed_data = seeded_client
        emp_id = seed_data['employee_id']

        resp = client.post('/api/penalties', json={
            'employee_id': emp_id,
            'amount': 1000,
            'penalty_type': 'monthly',
            'month': 3,
            'year': 2024,
            'description': 'Policy violation'
        })
        assert json.loads(resp.data)['success'] is True

    def test_get_penalties_filter_by_employee(self, seeded_client):
        """GET /api/penalties?employee_id=X – filters by employee."""
        client, seed_data = seeded_client
        emp_id = seed_data['employee_id']

        client.post('/api/penalties', json={
            'employee_id': emp_id, 'amount': 100, 'penalty_type': 'daily',
            'month': 3, 'year': 2024
        })
        resp = client.get(f'/api/penalties?employee_id={emp_id}')
        penalties = json.loads(resp.data)['penalties']
        assert all(p['employee_id'] == emp_id for p in penalties)

    def test_delete_penalty(self, seeded_client):
        """DELETE /api/penalties/<id> – deletes penalty record."""
        client, seed_data = seeded_client
        emp_id = seed_data['employee_id']

        create_resp = client.post('/api/penalties', json={
            'employee_id': emp_id, 'amount': 150, 'penalty_type': 'daily',
            'month': 3, 'year': 2024
        })
        pen_id = json.loads(create_resp.data)['penalty_id']

        del_resp = client.delete(f'/api/penalties/{pen_id}')
        assert json.loads(del_resp.data)['success'] is True

        get_resp = client.get(f'/api/penalties?employee_id={emp_id}')
        penalties = json.loads(get_resp.data)['penalties']
        assert not any(p['id'] == pen_id for p in penalties)


# ============================================================
# 8. SALARY ADVANCE API TESTS
# ============================================================

class TestSalaryAdvance:
    def test_check_eligibility_missing_params(self, client):
        """GET /api/advance/eligibility – missing params returns 400."""
        resp = client.get('/api/advance/eligibility')
        assert resp.status_code == 400

    def test_check_eligibility_nonexistent_employee(self, client):
        """GET /api/advance/eligibility – non-existent employee returns 404."""
        resp = client.get('/api/advance/eligibility?employee_id=9999&day=15&month=3&year=2024')
        assert resp.status_code == 404

    def test_check_eligibility_within_7_days(self, seeded_client):
        """GET /api/advance/eligibility – day <= 7 gives zero eligible days."""
        client, seed_data = seeded_client
        emp_id = seed_data['employee_id']

        resp = client.get(f'/api/advance/eligibility?employee_id={emp_id}&day=5&month=3&year=2024')
        data = json.loads(resp.data)
        assert data['success'] is True
        assert data['eligible_days'] == 0
        assert data['max_advance_amount'] == 0.0

    def test_check_eligibility_after_7_days(self, seeded_client):
        """GET /api/advance/eligibility – day > 7 gives correct eligible_days."""
        client, seed_data = seeded_client
        emp_id = seed_data['employee_id']

        resp = client.get(f'/api/advance/eligibility?employee_id={emp_id}&day=15&month=3&year=2024')
        data = json.loads(resp.data)
        assert data['success'] is True
        assert data['eligible_days'] == 8   # 15 - 7
        assert data['max_advance_amount'] > 0

    def test_check_eligibility_correct_amount(self, seeded_client):
        """GET /api/advance/eligibility – amount = eligible_days * per_day_salary."""
        client, seed_data = seeded_client
        emp_id = seed_data['employee_id']

        # base_monthly_salary = 30000, March has 31 days → per_day = 30000/31 ≈ 967.74
        resp = client.get(f'/api/advance/eligibility?employee_id={emp_id}&day=10&month=3&year=2024')
        data = json.loads(resp.data)
        import calendar
        total_days = calendar.monthrange(2024, 3)[1]
        expected_per_day = round(30000 / total_days, 2)
        eligible = 10 - 7
        expected_max = round(eligible * expected_per_day, 2)
        assert data['eligible_days'] == eligible
        assert abs(data['max_advance_amount'] - expected_max) <= 0.02

    def test_request_advance(self, seeded_client):
        """POST /api/advance – creates advance record."""
        client, seed_data = seeded_client
        emp_id = seed_data['employee_id']

        resp = client.post('/api/advance', json={
            'employee_id': emp_id,
            'amount': 5000,
            'request_date': '2024-03-15',
            'month': 3,
            'year': 2024,
            'day_of_month': 15,
            'eligible_days': 8
        })
        data = json.loads(resp.data)
        assert data['success'] is True
        assert 'advance_id' in data

    def test_get_advances_filter_by_employee(self, seeded_client):
        """GET /api/advance?employee_id=X – returns advances for employee."""
        client, seed_data = seeded_client
        emp_id = seed_data['employee_id']

        client.post('/api/advance', json={
            'employee_id': emp_id, 'amount': 3000, 'request_date': '2024-03-10',
            'month': 3, 'year': 2024, 'day_of_month': 10, 'eligible_days': 3
        })
        resp = client.get(f'/api/advance?employee_id={emp_id}')
        advances = json.loads(resp.data)['advances']
        assert len(advances) >= 1
        assert all(a['employee_id'] == emp_id for a in advances)

    def test_advance_default_status_is_approved(self, seeded_client):
        """POST /api/advance – new advance status defaults to 'approved'."""
        client, seed_data = seeded_client
        emp_id = seed_data['employee_id']

        client.post('/api/advance', json={
            'employee_id': emp_id, 'amount': 1000, 'request_date': '2024-03-12',
            'month': 3, 'year': 2024, 'day_of_month': 12, 'eligible_days': 5
        })
        resp = client.get(f'/api/advance?employee_id={emp_id}&month=3&year=2024')
        advances = json.loads(resp.data)['advances']
        assert advances[0]['status'] == 'approved'


# ============================================================
# 9. PAYROLL API TESTS
# ============================================================

class TestPayroll:
    def _setup_full_month(self, client, emp_id):
        """Helper: mark 20 Present days for March 2024."""
        for day in range(1, 21):
            client.post('/api/attendance', json={
                'employee_id': emp_id,
                'date': f'2024-03-{day:02d}',
                'status': 'Present',
                'overtime_hours': 0
            })

    def test_compute_payroll_missing_params(self, client):
        """POST /api/payroll/compute – missing month/year returns 400."""
        resp = client.post('/api/payroll/compute', json={})
        assert resp.status_code == 400

    def test_compute_payroll_no_employees(self, client):
        """POST /api/payroll/compute – no employees gives empty computed list."""
        resp = client.post('/api/payroll/compute', json={'month': 3, 'year': 2024})
        data = json.loads(resp.data)
        assert data['success'] is True
        assert data['computed'] == []

    def test_compute_payroll_basic(self, seeded_client):
        """POST /api/payroll/compute – computes net salary for employee."""
        client, seed_data = seeded_client
        emp_id = seed_data['employee_id']
        self._setup_full_month(client, emp_id)

        resp = client.post('/api/payroll/compute', json={'month': 3, 'year': 2024})
        data = json.loads(resp.data)
        assert data['success'] is True
        assert len(data['computed']) == 1
        assert data['computed'][0]['net_salary'] > 0

    def test_compute_payroll_with_incentives(self, seeded_client):
        """POST /api/payroll/compute – incentives increase net salary."""
        client, seed_data = seeded_client
        emp_id = seed_data['employee_id']
        self._setup_full_month(client, emp_id)

        client.post('/api/incentives', json={
            'employee_id': emp_id, 'amount': 1000,
            'incentive_type': 'monthly_bonus', 'month': 3, 'year': 2024
        })

        resp_base = client.post('/api/payroll/compute', json={'month': 3, 'year': 2024})
        salary_with_bonus = json.loads(resp_base.data)['computed'][0]['net_salary']

        # Remove incentive
        inc_resp = client.get(f'/api/incentives?employee_id={emp_id}')
        inc_id = json.loads(inc_resp.data)['incentives'][0]['id']
        client.delete(f'/api/incentives/{inc_id}')

        resp_no_bonus = client.post('/api/payroll/compute', json={'month': 3, 'year': 2024})
        salary_without_bonus = json.loads(resp_no_bonus.data)['computed'][0]['net_salary']

        assert salary_with_bonus > salary_without_bonus

    def test_compute_payroll_with_penalty(self, seeded_client):
        """POST /api/payroll/compute – penalties reduce net salary."""
        client, seed_data = seeded_client
        emp_id = seed_data['employee_id']
        self._setup_full_month(client, emp_id)

        resp_no_pen = client.post('/api/payroll/compute', json={'month': 3, 'year': 2024})
        salary_no_penalty = json.loads(resp_no_pen.data)['computed'][0]['net_salary']

        client.post('/api/penalties', json={
            'employee_id': emp_id, 'amount': 500,
            'penalty_type': 'monthly', 'month': 3, 'year': 2024
        })
        resp_with_pen = client.post('/api/payroll/compute', json={'month': 3, 'year': 2024})
        salary_with_penalty = json.loads(resp_with_pen.data)['computed'][0]['net_salary']

        assert salary_with_penalty < salary_no_penalty

    def test_compute_payroll_with_advance(self, seeded_client):
        """POST /api/payroll/compute – advance is deducted from net salary."""
        client, seed_data = seeded_client
        emp_id = seed_data['employee_id']
        self._setup_full_month(client, emp_id)

        resp_no_adv = client.post('/api/payroll/compute', json={'month': 3, 'year': 2024})
        salary_no_advance = json.loads(resp_no_adv.data)['computed'][0]['net_salary']

        client.post('/api/advance', json={
            'employee_id': emp_id, 'amount': 2000, 'request_date': '2024-03-15',
            'month': 3, 'year': 2024, 'day_of_month': 15, 'eligible_days': 8
        })
        resp_with_adv = client.post('/api/payroll/compute', json={'month': 3, 'year': 2024})
        salary_with_advance = json.loads(resp_with_adv.data)['computed'][0]['net_salary']

        assert abs((salary_no_advance - salary_with_advance) - 2000) < 0.01

    def test_get_payroll_records(self, seeded_client):
        """GET /api/payroll – returns computed payroll records."""
        client, seed_data = seeded_client
        emp_id = seed_data['employee_id']
        self._setup_full_month(client, emp_id)

        client.post('/api/payroll/compute', json={'month': 3, 'year': 2024})

        resp = client.get('/api/payroll?month=3&year=2024')
        data = json.loads(resp.data)
        assert data['success'] is True
        assert len(data['payroll']) >= 1

    def test_get_payroll_details(self, seeded_client):
        """GET /api/payroll/<id>/details – returns payroll detail breakdown."""
        client, seed_data = seeded_client
        emp_id = seed_data['employee_id']
        self._setup_full_month(client, emp_id)

        client.post('/api/advance', json={
            'employee_id': emp_id, 'amount': 1000, 'request_date': '2024-03-10',
            'month': 3, 'year': 2024, 'day_of_month': 10, 'eligible_days': 3
        })
        client.post('/api/payroll/compute', json={'month': 3, 'year': 2024})

        payroll_resp = client.get(f'/api/payroll?employee_id={emp_id}&month=3&year=2024')
        payroll_id = json.loads(payroll_resp.data)['payroll'][0]['id']

        resp = client.get(f'/api/payroll/{payroll_id}/details')
        data = json.loads(resp.data)
        assert data['success'] is True
        assert isinstance(data['details'], list)

    def test_finalize_payroll(self, seeded_client):
        """POST /api/payroll/<id>/finalize – marks payroll as finalized."""
        client, seed_data = seeded_client
        emp_id = seed_data['employee_id']
        self._setup_full_month(client, emp_id)

        client.post('/api/advance', json={
            'employee_id': emp_id, 'amount': 1000, 'request_date': '2024-03-10',
            'month': 3, 'year': 2024, 'day_of_month': 10, 'eligible_days': 3
        })
        client.post('/api/payroll/compute', json={'month': 3, 'year': 2024})

        payroll_resp = client.get(f'/api/payroll?employee_id={emp_id}&month=3&year=2024')
        payroll_id = json.loads(payroll_resp.data)['payroll'][0]['id']

        resp = client.post(f'/api/payroll/{payroll_id}/finalize')
        data = json.loads(resp.data)
        assert data['success'] is True

        # Check status is finalized
        get_resp = client.get(f'/api/payroll?employee_id={emp_id}&month=3&year=2024')
        payroll_record = json.loads(get_resp.data)['payroll'][0]
        assert payroll_record['status'] == 'finalized'

    def test_finalize_payroll_marks_advances_deducted(self, seeded_client):
        """POST /api/payroll/<id>/finalize – advances move to status 'deducted'."""
        client, seed_data = seeded_client
        emp_id = seed_data['employee_id']
        self._setup_full_month(client, emp_id)

        client.post('/api/advance', json={
            'employee_id': emp_id, 'amount': 1000, 'request_date': '2024-03-10',
            'month': 3, 'year': 2024, 'day_of_month': 10, 'eligible_days': 3
        })
        client.post('/api/payroll/compute', json={'month': 3, 'year': 2024})

        payroll_resp = client.get(f'/api/payroll?employee_id={emp_id}&month=3&year=2024')
        payroll_id = json.loads(payroll_resp.data)['payroll'][0]['id']
        client.post(f'/api/payroll/{payroll_id}/finalize')

        adv_resp = client.get(f'/api/advance?employee_id={emp_id}&month=3&year=2024')
        advances = json.loads(adv_resp.data)['advances']
        assert all(a['status'] == 'deducted' for a in advances)

    def test_generate_payslip(self, seeded_client):
        """GET /api/payroll/<id>/payslip – returns payslip data."""
        client, seed_data = seeded_client
        emp_id = seed_data['employee_id']
        self._setup_full_month(client, emp_id)

        client.post('/api/payroll/compute', json={'month': 3, 'year': 2024})

        payroll_resp = client.get(f'/api/payroll?employee_id={emp_id}&month=3&year=2024')
        payroll_id = json.loads(payroll_resp.data)['payroll'][0]['id']

        resp = client.get(f'/api/payroll/{payroll_id}/payslip')
        data = json.loads(resp.data)
        assert data['success'] is True
        assert 'payslip' in data
        ps = data['payslip']
        assert ps['employee_name'] == 'Test Employee'
        assert ps['base_salary'] == 30000
        assert ps['net_salary'] is not None

    def test_generate_payslip_not_found(self, client):
        """GET /api/payroll/<id>/payslip – non-existent returns 404."""
        resp = client.get('/api/payroll/9999/payslip')
        assert resp.status_code == 404

    def test_payroll_unpaid_leave_deduction(self, seeded_client):
        """POST /api/payroll/compute – unpaid leaves are correctly deducted."""
        client, seed_data = seeded_client
        emp_id = seed_data['employee_id']

        # Mark only 10 Present days; 4 paid leaves allowed → some absent days become unpaid
        for day in range(1, 11):
            client.post('/api/attendance', json={
                'employee_id': emp_id, 'date': f'2024-03-{day:02d}',
                'status': 'Present', 'overtime_hours': 0
            })
        for day in range(11, 20):
            client.post('/api/attendance', json={
                'employee_id': emp_id, 'date': f'2024-03-{day:02d}',
                'status': 'Absent', 'overtime_hours': 0
            })

        resp = client.post('/api/payroll/compute', json={'month': 3, 'year': 2024})
        computed = json.loads(resp.data)['computed'][0]

        payroll_resp = client.get(f'/api/payroll?employee_id={emp_id}&month=3&year=2024')
        record = json.loads(payroll_resp.data)['payroll'][0]
        assert record['unpaid_leaves'] > 0
        assert record['leave_deduction'] > 0


# ============================================================
# 10. DASHBOARD API TESTS
# ============================================================

class TestDashboard:
    def test_get_dashboard_stats_empty(self, client):
        """GET /api/dashboard/stats – returns correct zero counts on empty DB."""
        resp = client.get('/api/dashboard/stats')
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert data['success'] is True
        assert 'active_employees' in data
        assert 'archived_employees' in data
        assert 'today_attendance' in data
        assert 'pending_advances' in data
        assert data['active_employees'] == 0

    def test_get_dashboard_stats_with_data(self, seeded_client):
        """GET /api/dashboard/stats – reflects real employee count."""
        client, seed_data = seeded_client
        resp = client.get('/api/dashboard/stats')
        data = json.loads(resp.data)
        assert data['active_employees'] >= 1

    def test_get_dashboard_stats_filter_by_store(self, seeded_client):
        """GET /api/dashboard/stats?store_id=X – scoped to store."""
        client, seed_data = seeded_client
        resp = client.get('/api/dashboard/stats?store_id=1')
        data = json.loads(resp.data)
        assert data['success'] is True
        assert 'active_employees' in data
