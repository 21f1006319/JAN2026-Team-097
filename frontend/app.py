"""
Frontend Flask Application for Workforce & Payroll Management System
UI Server running on port 5000
Connects to Backend API Server on port 5001
"""
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import requests
import json
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your-secret-key-here-change-in-production'

# Backend API Configuration
BACKEND_URL = 'http://localhost:5001/api'

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'admin':
            flash('Admin access required', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def manager_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') not in ['admin', 'manager']:
            flash('Manager access required', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# Helper function for API calls
def api_call(method, endpoint, data=None, params=None):
    url = f"{BACKEND_URL}{endpoint}"
    try:
        if method == 'GET':
            response = requests.get(url, params=params, timeout=10)
        elif method == 'POST':
            response = requests.post(url, json=data, timeout=10)
        elif method == 'PUT':
            response = requests.put(url, json=data, timeout=10)
        elif method == 'DELETE':
            response = requests.delete(url, timeout=10)
        
        if response.status_code == 200:
            return response.json()
        else:
            return {'success': False, 'message': f'API Error: {response.status_code}'}
    except requests.exceptions.RequestException as e:
        return {'success': False, 'message': f'Connection error: {str(e)}'}

# ==================== AUTHENTICATION ROUTES ====================

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        result = api_call('POST', '/login', {'username': username, 'password': password})
        
        if result.get('success'):
            session['user_id'] = result['user_id']
            session['username'] = result['username']
            session['role'] = result['role']
            session['email'] = result['email']
            
            flash(f'Welcome, {result["username"]}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

# ==================== DASHBOARD ROUTES ====================

@app.route('/dashboard')
@login_required
def dashboard():
    role = session.get('role')
    
    if role == 'employee':
        return redirect(url_for('employee_portal'))
    
    # Get dashboard stats
    stats = api_call('GET', '/dashboard/stats')
    stores = api_call('GET', '/stores')
    
    return render_template('dashboard.html', 
                          stats=stats.get('data', {}) if not stats.get('success') else stats, 
                          stores=stores.get('stores', []) if stores.get('success') else [],
                          role=role)

# ==================== EMPLOYEE MANAGEMENT ROUTES (Admin/Manager) ====================

@app.route('/employees')
@login_required
@manager_required
def employees():
    include_archived = request.args.get('include_archived') == '1'
    store_id = request.args.get('store_id', type=int)
    
    params = {'include_archived': 'true' if include_archived else 'false'}
    if store_id:
        params['store_id'] = store_id
    
    result = api_call('GET', '/employees', params=params)
    stores = api_call('GET', '/stores')
    
    return render_template('employees.html', 
                          employees=result.get('employees', []) if result.get('success') else [],
                          stores=stores.get('stores', []) if stores.get('success') else [],
                          include_archived=include_archived,
                          selected_store=store_id)

@app.route('/employees/add', methods=['GET', 'POST'])
@login_required
@manager_required
def add_employee():
    if request.method == 'POST':
        data = {
            'name': request.form.get('name'),
            'address': request.form.get('address'),
            'email': request.form.get('email'),
            'phone': request.form.get('phone'),
            'date_of_joining': request.form.get('date_of_joining'),
            'role_type': request.form.get('role_type'),
            'base_monthly_salary': float(request.form.get('base_monthly_salary')),
            'store_id': request.form.get('store_id', type=int)
        }
        
        result = api_call('POST', '/employees', data=data)
        
        if result.get('success'):
            flash(f'Employee added successfully! Username: {result.get("username")}, Password: {result.get("password")}', 'success')
            return redirect(url_for('employees'))
        else:
            flash(f'Error adding employee: {result.get("message")}', 'danger')
    
    stores = api_call('GET', '/stores')
    return render_template('add_employee.html', 
                          stores=stores.get('stores', []) if stores.get('success') else [])

@app.route('/employees/<int:employee_id>/edit', methods=['GET', 'POST'])
@login_required
@manager_required
def edit_employee(employee_id):
    if request.method == 'POST':
        data = {
            'name': request.form.get('name'),
            'address': request.form.get('address'),
            'email': request.form.get('email'),
            'phone': request.form.get('phone'),
            'role_type': request.form.get('role_type'),
            'base_monthly_salary': float(request.form.get('base_monthly_salary')),
            'store_id': request.form.get('store_id', type=int)
        }
        
        result = api_call('PUT', f'/employees/{employee_id}', data=data)
        
        if result.get('success'):
            flash('Employee updated successfully!', 'success')
            return redirect(url_for('employees'))
        else:
            flash(f'Error updating employee: {result.get("message")}', 'danger')
    
    result = api_call('GET', f'/employees/{employee_id}')
    stores = api_call('GET', '/stores')
    
    return render_template('edit_employee.html', 
                          employee=result.get('employee', {}) if result.get('success') else {},
                          stores=stores.get('stores', []) if stores.get('success') else [])

@app.route('/employees/<int:employee_id>/archive', methods=['POST'])
@login_required
@admin_required
def archive_employee(employee_id):
    is_archived = request.form.get('is_archived', '1') == '1'
    result = api_call('POST', f'/employees/{employee_id}/archive', {'is_archived': 1 if is_archived else 0})
    
    if result.get('success'):
        status = 'archived' if is_archived else 'activated'
        flash(f'Employee {status} successfully!', 'success')
    else:
        flash('Error updating employee status', 'danger')
    
    return redirect(url_for('employees'))

@app.route('/employees/<int:employee_id>/reset_password', methods=['POST'])
@login_required
@admin_required
def reset_password(employee_id):
    result = api_call('POST', f'/employees/{employee_id}/reset_password')
    
    if result.get('success'):
        flash(f'Password reset successfully! New password: {result.get("new_password")}', 'success')
    else:
        flash('Error resetting password', 'danger')
    
    return redirect(url_for('employees'))

# ==================== ATTENDANCE ROUTES ====================

@app.route('/attendance', methods=['GET', 'POST'])
@login_required
@manager_required
def attendance():
    if request.method == 'POST':
        data = {
            'employee_id': request.form.get('employee_id', type=int),
            'date': request.form.get('date'),
            'status': request.form.get('status'),
            'overtime_hours': float(request.form.get('overtime_hours', 0))
        }
        
        result = api_call('POST', '/attendance', data=data)
        
        if result.get('success'):
            flash('Attendance marked successfully!', 'success')
        else:
            flash(f'Error marking attendance: {result.get("message")}', 'danger')
    
    # Get employees and attendance data
    employees_result = api_call('GET', '/employees')
    date_filter = request.args.get('date') or None
    
    attendance_params = {}
    if date_filter:
        attendance_params['start_date'] = date_filter
        attendance_params['end_date'] = date_filter
    
    attendance_result = api_call('GET', '/attendance', params=attendance_params)
    
    return render_template('attendance.html',
                          employees=employees_result.get('employees', []) if employees_result.get('success') else [],
                          attendance=attendance_result.get('attendance', []) if attendance_result.get('success') else [],
                          selected_date=date_filter)

# ==================== INCENTIVES & PENALTIES ROUTES ====================

@app.route('/incentives', methods=['GET', 'POST'])
@login_required
@manager_required
def incentives():
    if request.method == 'POST':
        data = {
            'employee_id': request.form.get('employee_id', type=int),
            'amount': float(request.form.get('amount')),
            'incentive_type': request.form.get('incentive_type'),
            'date': request.form.get('date'),
            'month': request.form.get('month', type=int),
            'year': request.form.get('year', type=int),
            'description': request.form.get('description')
        }
        
        result = api_call('POST', '/incentives', data=data)
        
        if result.get('success'):
            flash('Incentive added successfully!', 'success')
        else:
            flash(f'Error adding incentive: {result.get("message")}', 'danger')
    
    employees_result = api_call('GET', '/employees')
    month = request.args.get('month', type=int) or 3
    year = request.args.get('year', type=int) or 2026
    
    incentives_result = api_call('GET', '/incentives', params={'month': month, 'year': year})
    
    return render_template('incentives.html',
                          employees=employees_result.get('employees', []) if employees_result.get('success') else [],
                          incentives=incentives_result.get('incentives', []) if incentives_result.get('success') else [],
                          month=month, year=year)

@app.route('/incentives/<int:incentive_id>/delete', methods=['POST'])
@login_required
@manager_required
def delete_incentive(incentive_id):
    result = api_call('DELETE', f'/incentives/{incentive_id}')
    
    if result.get('success'):
        flash('Incentive deleted successfully!', 'success')
    else:
        flash('Error deleting incentive', 'danger')
    
    return redirect(url_for('incentives'))

@app.route('/penalties', methods=['GET', 'POST'])
@login_required
@manager_required
def penalties():
    if request.method == 'POST':
        data = {
            'employee_id': request.form.get('employee_id', type=int),
            'amount': float(request.form.get('amount')),
            'penalty_type': request.form.get('penalty_type'),
            'date': request.form.get('date'),
            'month': request.form.get('month', type=int),
            'year': request.form.get('year', type=int),
            'description': request.form.get('description')
        }
        
        result = api_call('POST', '/penalties', data=data)
        
        if result.get('success'):
            flash('Penalty added successfully!', 'success')
        else:
            flash(f'Error adding penalty: {result.get("message")}', 'danger')
    
    employees_result = api_call('GET', '/employees')
    month = request.args.get('month', type=int) or 3
    year = request.args.get('year', type=int) or 2026
    
    penalties_result = api_call('GET', '/penalties', params={'month': month, 'year': year})
    
    return render_template('penalties.html',
                          employees=employees_result.get('employees', []) if employees_result.get('success') else [],
                          penalties=penalties_result.get('penalties', []) if penalties_result.get('success') else [],
                          month=month, year=year)

@app.route('/penalties/<int:penalty_id>/delete', methods=['POST'])
@login_required
@manager_required
def delete_penalty(penalty_id):
    result = api_call('DELETE', f'/penalties/{penalty_id}')
    
    if result.get('success'):
        flash('Penalty deleted successfully!', 'success')
    else:
        flash('Error deleting penalty', 'danger')
    
    return redirect(url_for('penalties'))

# ==================== SALARY ADVANCE ROUTES ====================

@app.route('/advances', methods=['GET', 'POST'])
@login_required
@manager_required
def advances():
    if request.method == 'POST':
        data = {
            'employee_id': request.form.get('employee_id', type=int),
            'amount': float(request.form.get('amount')),
            'request_date': request.form.get('request_date'),
            'month': request.form.get('month', type=int),
            'year': request.form.get('year', type=int),
            'day_of_month': request.form.get('day_of_month', type=int),
            'eligible_days': request.form.get('eligible_days', type=int)
        }
        
        result = api_call('POST', '/advance', data=data)
        
        if result.get('success'):
            flash('Advance processed successfully!', 'success')
        else:
            flash(f'Error processing advance: {result.get("message")}', 'danger')
    
    employees_result = api_call('GET', '/employees')
    month = request.args.get('month', type=int) or 3
    year = request.args.get('year', type=int) or 2026
    
    advances_result = api_call('GET', '/advance', params={'month': month, 'year': year})
    
    return render_template('advances.html',
                          employees=employees_result.get('employees', []) if employees_result.get('success') else [],
                          advances=advances_result.get('advances', []) if advances_result.get('success') else [],
                          month=month, year=year)

@app.route('/api/advance/eligibility')
@login_required
def check_advance_eligibility():
    """Proxy for advance eligibility check"""
    try:
        employee_id = request.args.get('employee_id', type=int)
        day = request.args.get('day', type=int)
        month = request.args.get('month', type=int)
        year = request.args.get('year', type=int)
        
        print(f"Eligibility check requested: employee_id={employee_id}, day={day}, month={month}, year={year}")
        
        result = api_call('GET', '/advance/eligibility', 
                         params={'employee_id': employee_id, 'day': day, 'month': month, 'year': year})
        
        print(f"Backend response: {result}")
        return jsonify(result)
    except Exception as e:
        print(f"Error in check_advance_eligibility: {str(e)}")
        return jsonify({'success': False, 'message': f'Server error: {str(e)}'}), 500

# ==================== PAYROLL ROUTES ====================

@app.route('/payroll')
@login_required
@admin_required
def payroll():
    month = request.args.get('month', type=int) or 3
    year = request.args.get('year', type=int) or 2026
    store_id = request.args.get('store_id', type=int)
    
    result = api_call('GET', '/payroll', params={'month': month, 'year': year})
    stores = api_call('GET', '/stores')
    
    return render_template('payroll.html',
                          payroll=result.get('payroll', []) if result.get('success') else [],
                          stores=stores.get('stores', []) if stores.get('success') else [],
                          month=month, year=year, selected_store=store_id)

@app.route('/payroll/compute', methods=['POST'])
@login_required
@admin_required
def compute_payroll():
    month = request.form.get('month', type=int)
    year = request.form.get('year', type=int)
    store_id = request.form.get('store_id', type=int)
    
    result = api_call('POST', '/payroll/compute', {'month': month, 'year': year, 'store_id': store_id})
    
    if result.get('success'):
        flash(f'Payroll computed for {len(result.get("computed", []))} employees!', 'success')
    else:
        flash(f'Error computing payroll: {result.get("message")}', 'danger')
    
    return redirect(url_for('payroll', month=month, year=year))

@app.route('/payroll/<int:payroll_id>/finalize', methods=['POST'])
@login_required
@admin_required
def finalize_payroll(payroll_id):
    result = api_call('POST', f'/payroll/{payroll_id}/finalize')
    
    if result.get('success'):
        flash('Payroll finalized successfully!', 'success')
    else:
        flash('Error finalizing payroll', 'danger')
    
    return redirect(url_for('payroll'))

@app.route('/payroll/<int:payroll_id>/payslip')
@login_required
def view_payslip(payroll_id):
    result = api_call('GET', f'/payroll/{payroll_id}/payslip')
    
    if result.get('success'):
        return render_template('payslip.html', payslip=result.get('payslip', {}))
    else:
        flash('Error loading payslip', 'danger')
        return redirect(url_for('payroll'))

# ==================== SETTINGS ROUTES ====================

@app.route('/settings')
@login_required
@admin_required
def settings():
    result = api_call('GET', '/settings')
    stores = api_call('GET', '/stores')
    
    return render_template('settings.html',
                          settings=result.get('settings', {}) if result.get('success') else {},
                          stores=stores.get('stores', []) if stores.get('success') else [])

@app.route('/settings/paid_leaves', methods=['POST'])
@login_required
@admin_required
def update_paid_leaves():
    paid_leaves = request.form.get('paid_leaves', type=int)
    
    result = api_call('PUT', '/settings/paid_leaves', {'paid_leaves': paid_leaves})
    
    if result.get('success'):
        flash('Paid leaves setting updated!', 'success')
    else:
        flash('Error updating setting', 'danger')
    
    return redirect(url_for('settings'))

@app.route('/settings/stores', methods=['POST'])
@login_required
@admin_required
def add_store():
    name = request.form.get('name')
    address = request.form.get('address')
    
    result = api_call('POST', '/stores', {'name': name, 'address': address})
    
    if result.get('success'):
        flash('Store added successfully!', 'success')
    else:
        flash('Error adding store', 'danger')
    
    return redirect(url_for('settings'))

# ==================== EMPLOYEE PORTAL ROUTES ====================

@app.route('/employee/portal')
@login_required
def employee_portal():
    # Get employee profile by user_id
    result = api_call('GET', '/employees')
    employees = result.get('employees', []) if result.get('success') else []
    
    employee = None
    for emp in employees:
        if emp.get('user_id') == session.get('user_id'):
            employee = emp
            break
    
    if not employee:
        flash('Employee profile not found', 'danger')
        return redirect(url_for('logout'))
    
    # Get payroll history
    payroll_result = api_call('GET', '/payroll', params={'employee_id': employee['id']})
    payroll_history = payroll_result.get('payroll', []) if payroll_result.get('success') else []
    
    return render_template('employee_portal.html',
                          employee=employee,
                          payroll_history=payroll_history)

@app.route('/employee/payslip/<int:payroll_id>')
@login_required
def employee_payslip(payroll_id):
    result = api_call('GET', f'/payroll/{payroll_id}/payslip')
    
    if result.get('success'):
        return render_template('payslip.html', payslip=result.get('payslip', {}), is_employee=True)
    else:
        flash('Error loading payslip', 'danger')
        return redirect(url_for('employee_portal'))

@app.route('/employee/change_password', methods=['POST'])
@login_required
def employee_change_password():
    old_password = request.form.get('old_password')
    new_password = request.form.get('new_password')
    
    result = api_call('POST', '/change_password', {
        'user_id': session.get('user_id'),
        'old_password': old_password,
        'new_password': new_password
    })
    
    if result.get('success'):
        flash('Password changed successfully!', 'success')
    else:
        flash(f'Error: {result.get("message")}', 'danger')
    
    return redirect(url_for('employee_portal'))

if __name__ == '__main__':
    print("Starting Workforce & Payroll Management Frontend Server...")
    print("Connecting to Backend at:", BACKEND_URL)
    print("")
    print("Access the application at: http://localhost:5000")
    print("")
    app.run(host='0.0.0.0', port=5000, debug=True)
