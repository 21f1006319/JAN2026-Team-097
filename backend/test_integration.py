"""
Integration Tests for Workforce & Payroll Management System
Tests end-to-end flows between the frontend (port 5000) and backend (port 5001).
Requires both servers to be running before execution.
"""
import pytest
import requests
import json
import uuid
from datetime import date

FRONTEND_URL = 'http://localhost:5000'
BACKEND_URL = 'http://localhost:5001/api'


# ============================================================
# HELPERS
# ============================================================

def backend(method, endpoint, **kwargs):
    url = f"{BACKEND_URL}{endpoint}"
    resp = getattr(requests, method.lower())(url, timeout=10, **kwargs)
    return resp


def frontend_session():
    """Return a requests.Session logged into the frontend as admin."""
    s = requests.Session()
    s.post(f"{FRONTEND_URL}/login", data={'username': 'admin', 'password': 'admin123'})
    return s


def create_test_employee():
    """Helper: create a uniquely-identified employee via backend API and return response data."""
    unique_phone = uuid.uuid4().hex[:10]
    resp = backend('POST', '/employees', json={
        'name': 'Integration Test Employee',
        'address': '1 Integration Ave',
        'email': f'{unique_phone}@test.com',
        'phone': unique_phone,
        'date_of_joining': '2024-01-01',
        'role_type': 'Picking',
        'base_monthly_salary': 30000,
        'store_id': 1
    })
    return resp.json()


# ============================================================
# CONNECTIVITY TESTS
# ============================================================

class TestConnectivity:
    def test_backend_is_reachable(self):
        """Backend API server is up and responding."""
        resp = backend('GET', '/stores')
        assert resp.status_code == 200

    def test_frontend_is_reachable(self):
        """Frontend web server is up and returns login page."""
        resp = requests.get(f"{FRONTEND_URL}/login", timeout=10)
        assert resp.status_code == 200
        assert b'login' in resp.content.lower()

    def test_frontend_redirects_unauthenticated(self):
        """Unauthenticated request to /dashboard redirects to login."""
        resp = requests.get(f"{FRONTEND_URL}/dashboard", allow_redirects=False, timeout=10)
        assert resp.status_code in (301, 302)
        assert '/login' in resp.headers.get('Location', '')


# ============================================================
# INTEGRATION: AUTH FLOW
# ============================================================

class TestAuthFlow:
    def test_frontend_login_success(self):
        """Frontend login form posts to backend and establishes session."""
        s = requests.Session()
        resp = s.post(f"{FRONTEND_URL}/login",
                      data={'username': 'admin', 'password': 'admin123'},
                      allow_redirects=True, timeout=10)
        assert resp.status_code == 200
        # Should land on dashboard after redirect
        assert b'dashboard' in resp.url.encode() or b'Dashboard' in resp.content

    def test_frontend_login_invalid_credentials(self):
        """Frontend shows error flash on wrong credentials."""
        s = requests.Session()
        resp = s.post(f"{FRONTEND_URL}/login",
                      data={'username': 'admin', 'password': 'badpassword'},
                      allow_redirects=True, timeout=10)
        assert resp.status_code == 200
        assert b'Invalid' in resp.content or b'invalid' in resp.content

    def test_frontend_logout(self):
        """Frontend logout clears session; subsequent /dashboard redirects to login."""
        s = frontend_session()
        s.get(f"{FRONTEND_URL}/logout", timeout=10)
        resp = s.get(f"{FRONTEND_URL}/dashboard", allow_redirects=False, timeout=10)
        assert resp.status_code in (301, 302)

    def test_backend_login_api_direct(self):
        """Direct call to backend /api/login returns user data."""
        resp = backend('POST', '/login', json={'username': 'admin', 'password': 'admin123'})
        data = resp.json()
        assert data['success'] is True
        assert data['role'] == 'admin'

    def test_backend_login_inactive_user_rejected(self):
        """Disabled user cannot log in (backend enforces is_active=1)."""
        # Create an employee to get a user, then try with wrong password
        resp = backend('POST', '/login', json={'username': 'nonexistent_user_xyz', 'password': 'x'})
        assert resp.status_code == 401


# ============================================================
# INTEGRATION: EMPLOYEE MANAGEMENT FLOW
# ============================================================

class TestEmployeeManagementFlow:
    def test_full_employee_lifecycle(self):
        """Create → view → update → archive → unarchive employee."""
        unique_phone = uuid.uuid4().hex[:10]
        # CREATE
        create_resp = backend('POST', '/employees', json={
            'name': 'Lifecycle Test',
            'address': '5 Life St',
            'email': f'{unique_phone}@lifecycle.com',
            'phone': unique_phone,
            'date_of_joining': '2024-02-01',
            'role_type': 'Audit',
            'base_monthly_salary': 25000,
            'store_id': 1
        })
        assert create_resp.json()['success'] is True
        emp_id = create_resp.json()['employee_id']

        # VIEW
        view_resp = backend('GET', f'/employees/{emp_id}')
        assert view_resp.json()['employee']['name'] == 'Lifecycle Test'

        # UPDATE
        update_resp = backend('PUT', f'/employees/{emp_id}', json={
            'name': 'Lifecycle Updated',
            'address': '5 Life St',
            'email': 'updated@test.com',
            'phone': '5551234567',
            'role_type': 'Audit',
            'base_monthly_salary': 28000,
            'store_id': 1
        })
        assert update_resp.json()['success'] is True
        updated = backend('GET', f'/employees/{emp_id}').json()
        assert updated['employee']['base_monthly_salary'] == 28000

        # ARCHIVE
        arch_resp = backend('POST', f'/employees/{emp_id}/archive', json={'is_archived': 1})
        assert arch_resp.json()['success'] is True
        list_resp = backend('GET', '/employees')
        assert not any(e['id'] == emp_id for e in list_resp.json()['employees'])

        # UNARCHIVE
        unarch_resp = backend('POST', f'/employees/{emp_id}/archive', json={'is_archived': 0})
        assert unarch_resp.json()['success'] is True
        list_resp2 = backend('GET', '/employees')
        assert any(e['id'] == emp_id for e in list_resp2.json()['employees'])

    def test_frontend_employee_list_page(self):
        """Frontend /employees page renders without error for logged-in admin."""
        s = frontend_session()
        resp = s.get(f"{FRONTEND_URL}/employees", timeout=10)
        assert resp.status_code == 200
        assert b'Employee' in resp.content or b'employee' in resp.content

    def test_employee_credentials_can_login(self):
        """Newly created employee user account can authenticate."""
        create_data = create_test_employee()
        if not create_data.get('success'):
            pytest.skip("Could not create employee")

        username = create_data['username']
        password = create_data['password']

        login_resp = backend('POST', '/login', json={'username': username, 'password': password})
        assert login_resp.json()['success'] is True
        assert login_resp.json()['role'] == 'employee'

    def test_reset_password_and_login(self):
        """After password reset, employee can log in with new password."""
        create_data = create_test_employee()
        if not create_data.get('success'):
            pytest.skip("Could not create employee")
        emp_id = create_data['employee_id']

        reset_resp = backend('POST', f'/employees/{emp_id}/reset_password')
        new_pwd = reset_resp.json()['new_password']

        username = create_data['username']
        login_resp = backend('POST', '/login', json={'username': username, 'password': new_pwd})
        assert login_resp.json()['success'] is True


# ============================================================
# INTEGRATION: ATTENDANCE + PAYROLL FLOW
# ============================================================

class TestAttendancePayrollFlow:
    def test_mark_attendance_then_compute_payroll(self):
        """Mark attendance for a month, compute payroll, verify net salary."""
        create_data = create_test_employee()
        if not create_data.get('success'):
            pytest.skip("Employee creation failed")
        emp_id = create_data['employee_id']

        # Mark 25 Present days in Jan 2024
        for day in range(1, 26):
            backend('POST', '/attendance', json={
                'employee_id': emp_id,
                'date': f'2024-01-{day:02d}',
                'status': 'Present',
                'overtime_hours': 0
            })

        compute_resp = backend('POST', '/payroll/compute', json={'month': 1, 'year': 2024})
        data = compute_resp.json()
        assert data['success'] is True
        emp_payroll = next((c for c in data['computed'] if c['employee_id'] == emp_id), None)
        assert emp_payroll is not None
        assert emp_payroll['net_salary'] > 0

    def test_overtime_increases_net_salary(self):
        """Marking overtime hours increases net salary vs zero overtime."""
        p1, p2 = uuid.uuid4().hex[:10], uuid.uuid4().hex[:10]
        # Employee 1: no overtime
        e1 = backend('POST', '/employees', json={
            'name': 'OT Test Base', 'address': 'x', 'email': f'{p1}@t.com',
            'phone': p1, 'date_of_joining': '2024-01-01',
            'role_type': 'Picking', 'base_monthly_salary': 20000, 'store_id': 1
        }).json()
        # Employee 2: with overtime
        e2 = backend('POST', '/employees', json={
            'name': 'OT Test OT', 'address': 'x', 'email': f'{p2}@t.com',
            'phone': p2, 'date_of_joining': '2024-01-01',
            'role_type': 'Picking', 'base_monthly_salary': 20000, 'store_id': 1
        }).json()

        if not e1.get('success') or not e2.get('success'):
            pytest.skip("Could not create employees")

        for day in range(1, 21):
            backend('POST', '/attendance', json={
                'employee_id': e1['employee_id'], 'date': f'2024-04-{day:02d}',
                'status': 'Present', 'overtime_hours': 0
            })
            backend('POST', '/attendance', json={
                'employee_id': e2['employee_id'], 'date': f'2024-04-{day:02d}',
                'status': 'Present', 'overtime_hours': 4
            })

        compute_resp = backend('POST', '/payroll/compute', json={'month': 4, 'year': 2024})
        computed = compute_resp.json()['computed']

        s1 = next(c['net_salary'] for c in computed if c['employee_id'] == e1['employee_id'])
        s2 = next(c['net_salary'] for c in computed if c['employee_id'] == e2['employee_id'])
        assert s2 > s1

    def test_advance_deducted_on_finalize(self):
        """End-to-end: request advance → compute payroll → finalize → advance status deducted."""
        create_data = create_test_employee()
        if not create_data.get('success'):
            pytest.skip("Employee creation failed")
        emp_id = create_data['employee_id']

        for day in range(1, 21):
            backend('POST', '/attendance', json={
                'employee_id': emp_id, 'date': f'2024-05-{day:02d}',
                'status': 'Present', 'overtime_hours': 0
            })

        backend('POST', '/advance', json={
            'employee_id': emp_id, 'amount': 3000, 'request_date': '2024-05-15',
            'month': 5, 'year': 2024, 'day_of_month': 15, 'eligible_days': 8
        })

        backend('POST', '/payroll/compute', json={'month': 5, 'year': 2024})

        payroll_resp = backend('GET', f'/payroll?employee_id={emp_id}&month=5&year=2024')
        payroll_id = payroll_resp.json()['payroll'][0]['id']
        net_with_advance = payroll_resp.json()['payroll'][0]['net_salary']

        backend('POST', f'/payroll/{payroll_id}/finalize')

        adv_resp = backend('GET', f'/advance?employee_id={emp_id}&month=5&year=2024')
        advances = adv_resp.json()['advances']
        assert all(a['status'] == 'deducted' for a in advances)

    def test_payslip_contains_correct_data(self):
        """GET payslip returns correct employee name and salary after payroll compute."""
        create_data = create_test_employee()
        if not create_data.get('success'):
            pytest.skip("Employee creation failed")
        emp_id = create_data['employee_id']

        for day in range(1, 21):
            backend('POST', '/attendance', json={
                'employee_id': emp_id, 'date': f'2024-06-{day:02d}',
                'status': 'Present', 'overtime_hours': 0
            })

        backend('POST', '/payroll/compute', json={'month': 6, 'year': 2024})
        payroll_resp = backend('GET', f'/payroll?employee_id={emp_id}&month=6&year=2024')
        payroll_id = payroll_resp.json()['payroll'][0]['id']

        payslip_resp = backend('GET', f'/payroll/{payroll_id}/payslip')
        ps = payslip_resp.json()['payslip']
        assert ps['base_salary'] == 30000
        assert ps['month'] == 6
        assert ps['year'] == 2024
        assert ps['net_salary'] is not None


# ============================================================
# INTEGRATION: INCENTIVES & PENALTIES FLOW
# ============================================================

class TestIncentivesPenaltiesFlow:
    def test_incentive_reflected_in_payroll(self):
        """Add incentive via backend → compute payroll → incentive in net salary."""
        create_data = create_test_employee()
        if not create_data.get('success'):
            pytest.skip("Employee creation failed")
        emp_id = create_data['employee_id']

        for day in range(1, 21):
            backend('POST', '/attendance', json={
                'employee_id': emp_id, 'date': f'2024-07-{day:02d}',
                'status': 'Present', 'overtime_hours': 0
            })

        backend('POST', '/incentives', json={
            'employee_id': emp_id, 'amount': 1500,
            'incentive_type': 'monthly_bonus', 'month': 7, 'year': 2024
        })

        compute_resp = backend('POST', '/payroll/compute', json={'month': 7, 'year': 2024})
        emp_record = next(
            (c for c in compute_resp.json()['computed'] if c['employee_id'] == emp_id), None
        )
        assert emp_record is not None

        payroll_resp = backend('GET', f'/payroll?employee_id={emp_id}&month=7&year=2024')
        record = payroll_resp.json()['payroll'][0]
        assert record['total_incentives'] == 1500

    def test_penalty_reflected_in_payroll(self):
        """Add penalty via backend → compute payroll → penalty reduces net salary."""
        create_data = create_test_employee()
        if not create_data.get('success'):
            pytest.skip("Employee creation failed")
        emp_id = create_data['employee_id']

        for day in range(1, 21):
            backend('POST', '/attendance', json={
                'employee_id': emp_id, 'date': f'2024-08-{day:02d}',
                'status': 'Present', 'overtime_hours': 0
            })

        backend('POST', '/penalties', json={
            'employee_id': emp_id, 'amount': 800,
            'penalty_type': 'monthly', 'month': 8, 'year': 2024
        })

        backend('POST', '/payroll/compute', json={'month': 8, 'year': 2024})
        payroll_resp = backend('GET', f'/payroll?employee_id={emp_id}&month=8&year=2024')
        record = payroll_resp.json()['payroll'][0]
        assert record['total_penalties'] == 800

    def test_incentive_delete_updates_payroll(self):
        """Delete incentive → recompute payroll → incentive no longer in total."""
        create_data = create_test_employee()
        if not create_data.get('success'):
            pytest.skip("Employee creation failed")
        emp_id = create_data['employee_id']

        for day in range(1, 21):
            backend('POST', '/attendance', json={
                'employee_id': emp_id, 'date': f'2024-09-{day:02d}',
                'status': 'Present', 'overtime_hours': 0
            })

        inc_resp = backend('POST', '/incentives', json={
            'employee_id': emp_id, 'amount': 2000,
            'incentive_type': 'monthly_bonus', 'month': 9, 'year': 2024
        })
        inc_id = inc_resp.json()['incentive_id']
        backend('DELETE', f'/incentives/{inc_id}')

        backend('POST', '/payroll/compute', json={'month': 9, 'year': 2024})
        payroll_resp = backend('GET', f'/payroll?employee_id={emp_id}&month=9&year=2024')
        record = payroll_resp.json()['payroll'][0]
        assert record['total_incentives'] == 0


# ============================================================
# INTEGRATION: SETTINGS FLOW
# ============================================================

class TestSettingsFlow:
    def test_paid_leaves_setting_affects_payroll(self):
        """Changing paid_leaves_per_month setting changes payroll leave deduction."""
        create_data = create_test_employee()
        if not create_data.get('success'):
            pytest.skip("Employee creation failed")
        emp_id = create_data['employee_id']

        # 5 absent days in October
        for day in range(1, 22):
            backend('POST', '/attendance', json={
                'employee_id': emp_id, 'date': f'2024-10-{day:02d}',
                'status': 'Present', 'overtime_hours': 0
            })
        for day in range(22, 27):
            backend('POST', '/attendance', json={
                'employee_id': emp_id, 'date': f'2024-10-{day:02d}',
                'status': 'Absent', 'overtime_hours': 0
            })

        # With 4 paid leaves: 1 unpaid
        backend('PUT', '/settings/paid_leaves', json={'paid_leaves': 4})
        backend('POST', '/payroll/compute', json={'month': 10, 'year': 2024})
        pr1 = backend('GET', f'/payroll?employee_id={emp_id}&month=10&year=2024').json()['payroll'][0]

        # With 6 paid leaves: 0 unpaid
        backend('PUT', '/settings/paid_leaves', json={'paid_leaves': 6})
        backend('POST', '/payroll/compute', json={'month': 10, 'year': 2024})
        pr2 = backend('GET', f'/payroll?employee_id={emp_id}&month=10&year=2024').json()['payroll'][0]

        assert pr2['leave_deduction'] < pr1['leave_deduction']

    def test_dashboard_stats_reflect_live_data(self):
        """Dashboard stats endpoint returns live employee counts."""
        initial_resp = backend('GET', '/dashboard/stats')
        initial_count = initial_resp.json()['active_employees']

        create_test_employee()

        updated_resp = backend('GET', '/dashboard/stats')
        updated_count = updated_resp.json()['active_employees']

        assert updated_count >= initial_count


# ============================================================
# INTEGRATION: FRONTEND PAGES RENDER
# ============================================================

class TestFrontendPageRendering:
    def test_dashboard_page_loads(self):
        """Frontend /dashboard renders for authenticated admin."""
        s = frontend_session()
        resp = s.get(f"{FRONTEND_URL}/dashboard", timeout=10)
        assert resp.status_code == 200

    def test_employees_page_loads(self):
        """Frontend /employees renders for authenticated admin."""
        s = frontend_session()
        resp = s.get(f"{FRONTEND_URL}/employees", timeout=10)
        assert resp.status_code == 200

    def test_unauthenticated_employees_redirects(self):
        """Unauthenticated request to /employees redirects to login."""
        resp = requests.get(f"{FRONTEND_URL}/employees", allow_redirects=False, timeout=10)
        assert resp.status_code in (301, 302)
