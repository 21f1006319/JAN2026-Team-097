"""
Backend Flask Application for Workforce & Payroll Management System
API Server running on port 5001
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import os
import random
import string
import calendar
from datetime import datetime, date
from functools import wraps
import json

# Import chatbot utilities
from chatbot_utils import VectorSearchEngine, get_chat_history, save_chat_message, get_or_create_session

app = Flask(__name__)
CORS(app)

# Configuration
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app_database.db')
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')

# Helper Functions
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def generate_random_password(length=8):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def calculate_per_day_salary(base_salary, month, year):
    """Calculate per-day salary based on total days in month"""
    total_days = calendar.monthrange(year, month)[1]
    return base_salary / total_days, total_days

def get_paid_leaves_limit():
    """Get configured paid leaves per month"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT setting_value FROM global_settings WHERE setting_key = 'paid_leaves_per_month'")
    result = cursor.fetchone()
    conn.close()
    return int(result['setting_value']) if result else 4

# ==================== AUTHENTICATION APIs ====================

@app.route('/api/login', methods=['POST'])
def login():
    """Authenticate user and return role"""
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ? AND password = ? AND is_active = 1", 
                   (username, password))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        return jsonify({
            'success': True,
            'user_id': user['id'],
            'username': user['username'],
            'role': user['role'],
            'email': user['email']
        })
    return jsonify({'success': False, 'message': 'Employee not found'}), 404    #updated after client feedback

@app.route('/api/change_password', methods=['POST'])
def change_password():
    """Change user password"""
    data = request.json
    user_id = data.get('user_id')
    old_password = data.get('old_password')
    new_password = data.get('new_password')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verify old password
    cursor.execute("SELECT * FROM users WHERE id = ? AND password = ?", (user_id, old_password))
    if not cursor.fetchone():
        conn.close()
        return jsonify({'success': False, 'message': 'Invalid old password'}), 400
    
    # Update password
    cursor.execute("UPDATE users SET password = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                   (new_password, user_id))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Password updated successfully'})

# ==================== STORE APIs ====================

@app.route('/api/stores', methods=['GET'])
def get_stores():
    """Get all stores"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM stores WHERE is_active = 1")
    stores = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify({'success': True, 'stores': stores})

@app.route('/api/stores', methods=['POST'])
def create_store():
    """Create new store"""
    data = request.json
    name = data.get('name')
    address = data.get('address')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO stores (name, address) VALUES (?, ?)", (name, address))
    conn.commit()
    store_id = cursor.lastrowid
    conn.close()
    
    return jsonify({'success': True, 'store_id': store_id, 'message': 'Store created successfully'})

# ==================== GLOBAL SETTINGS APIs ====================

@app.route('/api/settings', methods=['GET'])
def get_settings():
    """Get all global settings"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM global_settings")
    settings = {row['setting_key']: row['setting_value'] for row in cursor.fetchall()}
    conn.close()
    return jsonify({'success': True, 'settings': settings})

@app.route('/api/settings/paid_leaves', methods=['PUT'])
def update_paid_leaves():
    """Update paid leaves per month setting"""
    data = request.json
    paid_leaves = data.get('paid_leaves')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE global_settings SET setting_value = ?, updated_at = CURRENT_TIMESTAMP WHERE setting_key = 'paid_leaves_per_month'",
                   (str(paid_leaves),))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Paid leaves setting updated'})

# ==================== EMPLOYEE APIs ====================

@app.route('/api/employees', methods=['GET'])
def get_employees():
    """Get all employees (optionally filter by store_id)"""
    store_id = request.args.get('store_id', type=int)
    include_archived = request.args.get('include_archived', 'false').lower() == 'true'
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = """
        SELECT e.*, u.username, s.name as store_name 
        FROM employees e 
        LEFT JOIN users u ON e.user_id = u.id 
        LEFT JOIN stores s ON e.store_id = s.id
        WHERE 1=1
    """
    params = []
    
    if not include_archived:
        query += " AND e.is_archived = 0"
    
    if store_id:
        query += " AND e.store_id = ?"
        params.append(store_id)
    
    cursor.execute(query, params)
    employees = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify({'success': True, 'employees': employees})

@app.route('/api/employees/<int:employee_id>', methods=['GET'])
def get_employee(employee_id):
    """Get specific employee details"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT e.*, u.username, u.password as user_password, s.name as store_name 
        FROM employees e 
        LEFT JOIN users u ON e.user_id = u.id 
        LEFT JOIN stores s ON e.store_id = s.id
        WHERE e.id = ?
    """, (employee_id,))
    employee = cursor.fetchone()
    conn.close()
    
    if employee:
        return jsonify({'success': True, 'employee': dict(employee)})
    return jsonify({'success': False, 'message': 'Employee not found'}), 404

@app.route('/api/employees', methods=['POST'])
def create_employee():
    """Create new employee with user account"""
    data = request.json
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create user account first
    username = data.get('phone') or generate_random_password(6)
    password = generate_random_password()
    
    cursor.execute("""
        INSERT INTO users (username, password, role, email, phone)
        VALUES (?, ?, 'employee', ?, ?)
    """, (username, password, data.get('email'), data.get('phone')))
    
    user_id = cursor.lastrowid
    
    # Create employee record
    cursor.execute("""
        INSERT INTO employees (user_id, name, address, email, phone, date_of_joining, role_type, base_monthly_salary, store_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_id, data.get('name'), data.get('address'), data.get('email'),
          data.get('phone'), data.get('date_of_joining'), data.get('role_type'),
          data.get('base_monthly_salary'), data.get('store_id')))
    
    employee_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return jsonify({
        'success': True, 
        'employee_id': employee_id, 
        'user_id': user_id,
        'username': username,
        'password': password,
        'message': 'Employee created successfully'
    })

@app.route('/api/employees/<int:employee_id>', methods=['PUT'])
def update_employee(employee_id):
    """Update employee details"""
    data = request.json
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Update employee
    cursor.execute("""
        UPDATE employees 
        SET name = ?, address = ?, email = ?, phone = ?, 
            role_type = ?, base_monthly_salary = ?, store_id = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (data.get('name'), data.get('address'), data.get('email'), data.get('phone'),
          data.get('role_type'), data.get('base_monthly_salary'), data.get('store_id'), employee_id))
    
    # Update user email if changed
    if data.get('email'):
        cursor.execute("SELECT user_id FROM employees WHERE id = ?", (employee_id,))
        result = cursor.fetchone()
        if result and result['user_id']:
            cursor.execute("UPDATE users SET email = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                           (data.get('email'), result['user_id']))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Employee updated successfully'})

@app.route('/api/employees/<int:employee_id>/archive', methods=['POST'])
def archive_employee(employee_id):
    """Archive or unarchive employee"""
    data = request.json
    is_archived = data.get('is_archived', 1)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE employees SET is_archived = ? WHERE id = ?", (is_archived, employee_id))
    conn.commit()
    conn.close()
    
    status = 'archived' if is_archived else 'activated'
    return jsonify({'success': True, 'message': f'Employee {status} successfully'})

@app.route('/api/employees/<int:employee_id>/reset_password', methods=['POST'])
def reset_employee_password(employee_id):
    """Reset employee password (Admin only)"""
    new_password = generate_random_password()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM employees WHERE id = ?", (employee_id,))
    result = cursor.fetchone()
    
    if result and result['user_id']:
        cursor.execute("UPDATE users SET password = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                       (new_password, result['user_id']))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'new_password': new_password, 'message': 'Password reset successfully'})
    
    conn.close()
    return jsonify({'success': False, 'message': 'Employee user account not found'}), 404

# ==================== ATTENDANCE APIs ====================

@app.route('/api/attendance', methods=['GET'])
def get_attendance():
    """Get attendance for employees by date range"""
    employee_id = request.args.get('employee_id', type=int)
    store_id = request.args.get('store_id', type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = """
        SELECT a.*, e.name as employee_name 
        FROM attendance a 
        JOIN employees e ON a.employee_id = e.id
        WHERE 1=1
    """
    params = []
    
    if employee_id:
        query += " AND a.employee_id = ?"
        params.append(employee_id)
    
    if store_id:
        query += " AND e.store_id = ?"
        params.append(store_id)
    
    if start_date:
        query += " AND a.date >= ?"
        params.append(start_date)
    
    if end_date:
        query += " AND a.date <= ?"
        params.append(end_date)
    
    query += " ORDER BY a.date DESC"
    
    cursor.execute(query, params)
    attendance = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify({'success': True, 'attendance': attendance})

@app.route('/api/attendance', methods=['POST'])
def mark_attendance():
    """Mark attendance for an employee"""
    data = request.json
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if attendance already exists for this date
    cursor.execute("""
        SELECT id FROM attendance WHERE employee_id = ? AND date = ?
    """, (data.get('employee_id'), data.get('date')))
    
    existing = cursor.fetchone()
    
    if existing:
        # Update existing
        cursor.execute("""
            UPDATE attendance 
            SET status = ?, overtime_hours = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (data.get('status'), data.get('overtime_hours', 0), existing['id']))
    else:
        # Insert new
        cursor.execute("""
            INSERT INTO attendance (employee_id, date, status, overtime_hours)
            VALUES (?, ?, ?, ?)
        """, (data.get('employee_id'), data.get('date'), data.get('status'), data.get('overtime_hours', 0)))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Attendance marked successfully'})

# ==================== INCENTIVES APIs ====================

@app.route('/api/incentives', methods=['GET'])
def get_incentives():
    """Get incentives for employees"""
    employee_id = request.args.get('employee_id', type=int)
    month = request.args.get('month', type=int)
    year = request.args.get('year', type=int)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = """
        SELECT i.*, e.name as employee_name 
        FROM incentives i 
        JOIN employees e ON i.employee_id = e.id
        WHERE 1=1
    """
    params = []
    
    if employee_id:
        query += " AND i.employee_id = ?"
        params.append(employee_id)
    
    if month:
        query += " AND i.month = ?"
        params.append(month)
    
    if year:
        query += " AND i.year = ?"
        params.append(year)
    
    cursor.execute(query, params)
    incentives = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify({'success': True, 'incentives': incentives})

@app.route('/api/incentives', methods=['POST'])
def add_incentive():
    """Add incentive for an employee"""
    data = request.json
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO incentives (employee_id, amount, incentive_type, date, month, year, description)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (data.get('employee_id'), data.get('amount'), data.get('incentive_type'),
          data.get('date'), data.get('month'), data.get('year'), data.get('description')))
    
    conn.commit()
    incentive_id = cursor.lastrowid
    conn.close()
    
    return jsonify({'success': True, 'incentive_id': incentive_id, 'message': 'Incentive added successfully'})

@app.route('/api/incentives/<int:incentive_id>', methods=['DELETE'])
def delete_incentive(incentive_id):
    """Delete incentive"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM incentives WHERE id = ?", (incentive_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Incentive deleted successfully'})

# ==================== PENALTIES APIs ====================

@app.route('/api/penalties', methods=['GET'])
def get_penalties():
    """Get penalties for employees"""
    employee_id = request.args.get('employee_id', type=int)
    month = request.args.get('month', type=int)
    year = request.args.get('year', type=int)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = """
        SELECT p.*, e.name as employee_name 
        FROM penalties p 
        JOIN employees e ON p.employee_id = e.id
        WHERE 1=1
    """
    params = []
    
    if employee_id:
        query += " AND p.employee_id = ?"
        params.append(employee_id)
    
    if month:
        query += " AND p.month = ?"
        params.append(month)
    
    if year:
        query += " AND p.year = ?"
        params.append(year)
    
    cursor.execute(query, params)
    penalties = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify({'success': True, 'penalties': penalties})

@app.route('/api/penalties', methods=['POST'])
def add_penalty():
    """Add penalty for an employee"""
    data = request.json
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO penalties (employee_id, amount, penalty_type, date, month, year, description)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (data.get('employee_id'), data.get('amount'), data.get('penalty_type'),
          data.get('date'), data.get('month'), data.get('year'), data.get('description')))
    
    conn.commit()
    penalty_id = cursor.lastrowid
    conn.close()
    
    return jsonify({'success': True, 'penalty_id': penalty_id, 'message': 'Penalty added successfully'})

@app.route('/api/penalties/<int:penalty_id>', methods=['DELETE'])
def delete_penalty(penalty_id):
    """Delete penalty"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM penalties WHERE id = ?", (penalty_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Penalty deleted successfully'})

# ==================== SALARY ADVANCE APIs ====================

@app.route('/api/advance/eligibility', methods=['GET'])
def check_advance_eligibility():
    """Check 7-day rule eligibility for salary advance"""
    employee_id = request.args.get('employee_id', type=int)
    day_of_month = request.args.get('day', type=int)
    month = request.args.get('month', type=int)
    year = request.args.get('year', type=int)
    
    if not all([employee_id, day_of_month, month, year]):
        return jsonify({'success': False, 'message': 'Missing required parameters'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get employee base salary
    cursor.execute("SELECT base_monthly_salary FROM employees WHERE id = ?", (employee_id,))
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        return jsonify({'success': False, 'message': 'Employee not found'}), 404
    
    base_salary = result['base_monthly_salary']
    per_day_salary, _ = calculate_per_day_salary(base_salary, month, year)
    
    # Calculate eligible days (7-day rule)
    eligible_days = max(0, day_of_month - 7)
    max_advance_amount = eligible_days * per_day_salary
    
    return jsonify({
        'success': True,
        'day_of_month': day_of_month,
        'eligible_days': eligible_days,
        'per_day_salary': round(per_day_salary, 2),
        'max_advance_amount': round(max_advance_amount, 2)
    })

@app.route('/api/advance', methods=['POST'])
def request_advance():
    """Request salary advance"""
    data = request.json
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO salary_advances (employee_id, amount, request_date, month, year, day_of_month, eligible_days, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'approved')
    """, (data.get('employee_id'), data.get('amount'), data.get('request_date'),
          data.get('month'), data.get('year'), data.get('day_of_month'), data.get('eligible_days')))
    
    conn.commit()
    advance_id = cursor.lastrowid
    conn.close()
    
    return jsonify({'success': True, 'advance_id': advance_id, 'message': 'Advance requested successfully'})

@app.route('/api/advance', methods=['GET'])
def get_advances():
    """Get salary advances"""
    employee_id = request.args.get('employee_id', type=int)
    month = request.args.get('month', type=int)
    year = request.args.get('year', type=int)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = """
        SELECT sa.*, e.name as employee_name 
        FROM salary_advances sa 
        JOIN employees e ON sa.employee_id = e.id
        WHERE 1=1
    """
    params = []
    
    if employee_id:
        query += " AND sa.employee_id = ?"
        params.append(employee_id)
    
    if month:
        query += " AND sa.month = ?"
        params.append(month)
    
    if year:
        query += " AND sa.year = ?"
        params.append(year)
    
    cursor.execute(query, params)
    advances = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify({'success': True, 'advances': advances})

# ==================== PAYROLL APIs ====================

@app.route('/api/payroll/compute', methods=['POST'])
def compute_payroll():
    """Compute payroll for all active employees for a given month/year"""
    data = request.json
    month = data.get('month')
    year = data.get('year')
    store_id = data.get('store_id')
    
    if not month or not year:
        return jsonify({'success': False, 'message': 'Month and year required'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get all active employees
    query = "SELECT * FROM employees WHERE is_archived = 0"
    params = []
    if store_id:
        query += " AND store_id = ?"
        params.append(store_id)
    
    cursor.execute(query, params)
    employees = cursor.fetchall()
    
    paid_leaves_limit = get_paid_leaves_limit()
    total_days_in_month = calendar.monthrange(year, month)[1]
    
    computed = []
    
    for emp in employees:
        base_salary = emp['base_monthly_salary']
        per_day_salary = base_salary / total_days_in_month
        
        # Count attendance for the month
        cursor.execute("""
            SELECT status, COUNT(*) as count, SUM(overtime_hours) as ot_hours
            FROM attendance 
            WHERE employee_id = ? AND strftime('%m', date) = ? AND strftime('%Y', date) = ?
            GROUP BY status
        """, (emp['id'], f"{month:02d}", str(year)))
        
        attendance_summary = {row['status']: {'count': row['count'], 'ot_hours': row['ot_hours'] or 0} 
                             for row in cursor.fetchall()}
        
        days_present = attendance_summary.get('Present', {}).get('count', 0)
        days_absent = attendance_summary.get('Absent', {}).get('count', 0)
        days_half_day = attendance_summary.get('Half-day', {}).get('count', 0)
        total_ot_hours = sum(row['ot_hours'] or 0 for row in attendance_summary.values())
        
        # Calculate effective present days (half day counts as 0.5)
        effective_present_days = days_present + (days_half_day * 0.5)
        
        # Leave calculation
        total_leaves_taken = days_absent + (days_half_day * 0.5)
        unpaid_leaves = max(0, total_leaves_taken - paid_leaves_limit)
        leave_deduction = unpaid_leaves * per_day_salary
        
        # Overtime pay (assumed 1.5x per hour based on per day / 8 hours)
        hourly_rate = per_day_salary / 8
        overtime_pay = total_ot_hours * hourly_rate * 1.5
        
        # Get incentives for the month
        cursor.execute("""
            SELECT * FROM incentives 
            WHERE employee_id = ? AND month = ? AND year = ?
        """, (emp['id'], month, year))
        incentives = cursor.fetchall()
        total_incentives = sum(inc['amount'] for inc in incentives)
        
        # Get penalties for the month
        cursor.execute("""
            SELECT * FROM penalties 
            WHERE employee_id = ? AND month = ? AND year = ?
        """, (emp['id'], month, year))
        penalties = cursor.fetchall()
        total_penalties = sum(pen['amount'] for pen in penalties)
        
        # Get approved advances for the month
        cursor.execute("""
            SELECT SUM(amount) as total FROM salary_advances 
            WHERE employee_id = ? AND month = ? AND year = ? AND status = 'approved'
        """, (emp['id'], month, year))
        advance_result = cursor.fetchone()
        total_advances = advance_result['total'] or 0
        
        # Calculate net salary
        net_salary = (base_salary + overtime_pay + total_incentives - 
                     total_penalties - leave_deduction - total_advances)
        
        # Insert or update payroll record
        cursor.execute("""
            SELECT id FROM payroll WHERE employee_id = ? AND month = ? AND year = ?
        """, (emp['id'], month, year))
        
        existing = cursor.fetchone()
        
        if existing:
            cursor.execute("""
                UPDATE payroll SET
                    base_salary = ?, per_day_salary = ?, total_days_in_month = ?,
                    days_present = ?, days_absent = ?, days_half_day = ?,
                    paid_leaves_allowed = ?, unpaid_leaves = ?, leave_deduction = ?,
                    total_overtime_hours = ?, overtime_pay = ?, total_incentives = ?,
                    total_penalties = ?, salary_advances_deducted = ?, net_salary = ?,
                    status = 'draft'
                WHERE id = ?
            """, (base_salary, per_day_salary, total_days_in_month,
                  days_present, days_absent, days_half_day,
                  paid_leaves_limit, unpaid_leaves, leave_deduction,
                  total_ot_hours, overtime_pay, total_incentives,
                  total_penalties, total_advances, net_salary, existing['id']))
            payroll_id = existing['id']
        else:
            cursor.execute("""
                INSERT INTO payroll (
                    employee_id, month, year, base_salary, per_day_salary, total_days_in_month,
                    days_present, days_absent, days_half_day, paid_leaves_allowed, unpaid_leaves,
                    leave_deduction, total_overtime_hours, overtime_pay, total_incentives,
                    total_penalties, salary_advances_deducted, net_salary, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'draft')
            """, (emp['id'], month, year, base_salary, per_day_salary, total_days_in_month,
                  days_present, days_absent, days_half_day, paid_leaves_limit, unpaid_leaves,
                  leave_deduction, total_ot_hours, overtime_pay, total_incentives,
                  total_penalties, total_advances, net_salary))
            payroll_id = cursor.lastrowid
        
        # Clear and re-insert payroll details
        cursor.execute("DELETE FROM payroll_details WHERE payroll_id = ?", (payroll_id,))
        
        # Add incentive details
        for inc in incentives:
            cursor.execute("""
                INSERT INTO payroll_details (payroll_id, detail_type, description, amount, date)
                VALUES (?, ?, ?, ?, ?)
            """, (payroll_id, f"incentive_{inc['incentive_type']}", inc['description'], 
                  inc['amount'], inc['date']))
        
        # Add penalty details
        for pen in penalties:
            cursor.execute("""
                INSERT INTO payroll_details (payroll_id, detail_type, description, amount, date)
                VALUES (?, ?, ?, ?, ?)
            """, (payroll_id, f"penalty_{pen['penalty_type']}", pen['description'], 
                  pen['amount'], pen['date']))
        
        # Add advance details
        if total_advances > 0:
            cursor.execute("""
                INSERT INTO payroll_details (payroll_id, detail_type, description, amount, date)
                VALUES (?, 'advance', 'Salary Advance Deduction', ?, ?)
            """, (payroll_id, total_advances, date.today()))
        
        computed.append({
            'employee_id': emp['id'],
            'employee_name': emp['name'],
            'payroll_id': payroll_id,
            'net_salary': round(net_salary, 2)
        })
    
    conn.commit()
    conn.close()
    
    return jsonify({
        'success': True, 
        'message': f'Payroll computed for {len(computed)} employees',
        'computed': computed
    })

@app.route('/api/payroll', methods=['GET'])
def get_payroll():
    """Get payroll records"""
    employee_id = request.args.get('employee_id', type=int)
    month = request.args.get('month', type=int)
    year = request.args.get('year', type=int)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = """
        SELECT p.*, e.name as employee_name, e.email, e.phone
        FROM payroll p 
        JOIN employees e ON p.employee_id = e.id
        WHERE 1=1
    """
    params = []
    
    if employee_id:
        query += " AND p.employee_id = ?"
        params.append(employee_id)
    
    if month:
        query += " AND p.month = ?"
        params.append(month)
    
    if year:
        query += " AND p.year = ?"
        params.append(year)
    
    query += " ORDER BY p.year DESC, p.month DESC"
    
    cursor.execute(query, params)
    payroll = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify({'success': True, 'payroll': payroll})

@app.route('/api/payroll/<int:payroll_id>/details', methods=['GET'])
def get_payroll_details(payroll_id):
    """Get detailed breakdown of payroll"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM payroll_details WHERE payroll_id = ?
    """, (payroll_id,))
    details = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify({'success': True, 'details': details})

@app.route('/api/payroll/<int:payroll_id>/finalize', methods=['POST'])
def finalize_payroll(payroll_id):
    """Finalize payroll and mark advances as deducted"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get payroll info
    cursor.execute("SELECT employee_id, month, year FROM payroll WHERE id = ?", (payroll_id,))
    payroll = cursor.fetchone()
    
    if payroll:
        # Update advances status to deducted
        cursor.execute("""
            UPDATE salary_advances SET status = 'deducted' 
            WHERE employee_id = ? AND month = ? AND year = ?
        """, (payroll['employee_id'], payroll['month'], payroll['year']))
        
        # Mark payroll as finalized
        cursor.execute("""
            UPDATE payroll SET status = 'finalized', finalized_at = CURRENT_TIMESTAMP 
            WHERE id = ?
        """, (payroll_id,))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Payroll finalized successfully'})

@app.route('/api/payroll/<int:payroll_id>/payslip', methods=['GET'])
def generate_payslip(payroll_id):
    """Generate payslip data for PDF"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get payroll with employee details
    cursor.execute("""
        SELECT p.*, e.name as employee_name, e.address, e.email, e.phone, e.role_type,
               s.name as store_name
        FROM payroll p 
        JOIN employees e ON p.employee_id = e.id
        LEFT JOIN stores s ON e.store_id = s.id
        WHERE p.id = ?
    """, (payroll_id,))
    payroll = cursor.fetchone()
    
    if not payroll:
        conn.close()
        return jsonify({'success': False, 'message': 'Payroll not found'}), 404
    
    # Get details
    cursor.execute("SELECT * FROM payroll_details WHERE payroll_id = ?", (payroll_id,))
    details = cursor.fetchall()
    
    # Organize details
    incentives_daily = [d for d in details if d['detail_type'] == 'incentive_daily_performance']
    incentives_monthly = [d for d in details if d['detail_type'] == 'incentive_monthly_bonus']
    penalties_daily = [d for d in details if d['detail_type'] == 'penalty_daily']
    penalties_monthly = [d for d in details if d['detail_type'] == 'penalty_monthly']
    advances = [d for d in details if d['detail_type'] == 'advance']
    
    conn.close()
    
    payslip_data = {
        'payroll_id': payroll_id,
        'employee_name': payroll['employee_name'],
        'employee_address': payroll['address'],
        'employee_email': payroll['email'],
        'employee_phone': payroll['phone'],
        'role_type': payroll['role_type'],
        'store_name': payroll['store_name'],
        'month': payroll['month'],
        'year': payroll['year'],
        'base_salary': payroll['base_salary'],
        'per_day_salary': payroll['per_day_salary'],
        'total_days_in_month': payroll['total_days_in_month'],
        'days_present': payroll['days_present'],
        'days_half_day': payroll['days_half_day'],
        'days_absent': payroll['days_absent'],
        'paid_leaves_allowed': payroll['paid_leaves_allowed'],
        'unpaid_leaves': payroll['unpaid_leaves'],
        'leave_deduction': payroll['leave_deduction'],
        'total_overtime_hours': payroll['total_overtime_hours'],
        'overtime_pay': payroll['overtime_pay'],
        'incentives_daily': incentives_daily,
        'incentives_monthly': incentives_monthly,
        'penalties_daily': penalties_daily,
        'penalties_monthly': penalties_monthly,
        'advances': advances,
        'total_incentives': payroll['total_incentives'],
        'total_penalties': payroll['total_penalties'],
        'salary_advances_deducted': payroll['salary_advances_deducted'],
        'net_salary': payroll['net_salary'],
        'status': payroll['status'],
        'qr_code_url': payroll['drive_link'] or 'https://drive.google.com'
    }
    
    return jsonify({'success': True, 'payslip': payslip_data})

# ==================== DASHBOARD APIs ====================

@app.route('/api/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    """Get dashboard statistics"""
    store_id = request.args.get('store_id', type=int)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Employee count
    query = "SELECT COUNT(*) as count FROM employees WHERE is_archived = 0"
    params = []
    if store_id:
        query += " AND store_id = ?"
        params.append(store_id)
    cursor.execute(query, params)
    active_employees = cursor.fetchone()['count']
    
    # Archived count
    query = "SELECT COUNT(*) as count FROM employees WHERE is_archived = 1"
    params = []
    if store_id:
        query += " AND store_id = ?"
        params.append(store_id)
    cursor.execute(query, params)
    archived_employees = cursor.fetchone()['count']
    
    # Today's attendance
    today = date.today().isoformat()
    query = """
        SELECT COUNT(*) as count FROM attendance a 
        JOIN employees e ON a.employee_id = e.id 
        WHERE a.date = ?
    """
    params = [today]
    if store_id:
        query += " AND e.store_id = ?"
        params.append(store_id)
    cursor.execute(query, params)
    today_attendance = cursor.fetchone()['count']
    
    # Pending advances
    query = """
        SELECT COUNT(*) as count FROM salary_advances sa 
        JOIN employees e ON sa.employee_id = e.id 
        WHERE sa.status = 'pending'
    """
    params = []
    if store_id:
        query += " AND e.store_id = ?"
        params.append(store_id)
    cursor.execute(query, params)
    pending_advances = cursor.fetchone()['count']
    
    conn.close()
    
    return jsonify({
        'success': True,
        'active_employees': active_employees,
        'archived_employees': archived_employees,
        'today_attendance': today_attendance,
        'pending_advances': pending_advances
    })

# ==================== CHATBOT APIs ====================

# Initialize vector search engine
vector_engine = VectorSearchEngine(DB_PATH)

@app.route('/api/chatbot/query', methods=['POST'])
def chatbot_query():
    """Process a user query using RAG - match to prompt-SQL pair, execute query, return results"""
    data = request.json
    user_query = data.get('query', '').strip()
    user_id = data.get('user_id')
    session_id = data.get('session_id')
    
    if not user_query:
        return jsonify({'success': False, 'message': 'Query is required'}), 400
    
    if not user_id:
        return jsonify({'success': False, 'message': 'User ID is required'}), 400
    
    # Get or create session
    session_id = get_or_create_session(DB_PATH, user_id, session_id)
    
    # Save user message
    save_chat_message(DB_PATH, user_id, session_id, 'user', user_query)
    
    # Find best matching prompt-SQL pair
    match, params, score = vector_engine.find_best_match(user_query)
    
    if not match:
        # No relevant match found
        bot_message = "This question is beyond the scope of the application. Kindly ask questions related to the application."
        save_chat_message(DB_PATH, user_id, session_id, 'bot', bot_message)
        return jsonify({
            'success': True,
            'matched': False,
            'message': bot_message,
            'session_id': session_id
        })
    
    # Format SQL query with extracted parameters
    sql_query = vector_engine.format_sql_query(match['sql_query'], params)
    
    # Execute the SQL query
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(sql_query)
        columns = [description[0] for description in cursor.description] if cursor.description else []
        rows = cursor.fetchall()
        
        # Convert to list of dicts
        results = []
        for row in rows:
            row_dict = {}
            for i, col in enumerate(columns):
                row_dict[col] = row[i]
            results.append(row_dict)
        
        conn.close()
        
        # Format the response
        if len(results) == 0:
            bot_message = f"No results found for your query about '{match['description']}'."
        elif len(results) == 1:
            # Single result - show details
            bot_message = f"**{match['description']}**\n\n"
            for key, value in results[0].items():
                bot_message += f"• {key.replace('_', ' ').title()}: {value}\n"
        else:
            # Multiple results - create summary
            bot_message = f"**{match['description']}** ({len(results)} records)\n\n"
            
            # Show first 5 results
            for i, row in enumerate(results[:5], 1):
                # Try to find a name field for the header
                name_fields = [k for k in row.keys() if 'name' in k.lower()]
                if name_fields:
                    header = row.get(name_fields[0], f"Record {i}")
                else:
                    header = f"Record {i}"
                
                bot_message += f"**{header}**\n"
                for key, value in row.items():
                    if value and key != name_fields[0] if name_fields else True:
                        bot_message += f"  • {key.replace('_', ' ').title()}: {value}\n"
                bot_message += "\n"
            
            if len(results) > 5:
                bot_message += f"... and {len(results) - 5} more records.\n"
        
        # Save bot response
        save_chat_message(DB_PATH, user_id, session_id, 'bot', bot_message, sql_query, json.dumps(results))
        
        return jsonify({
            'success': True,
            'matched': True,
            'category': match['category'],
            'description': match['description'],
            'message': bot_message,
            'sql_query': sql_query,
            'results': results,
            'session_id': session_id,
            'match_score': round(score, 3)
        })
        
    except Exception as e:
        conn.close()
        error_message = f"I found a matching query pattern, but there was an error executing it: {str(e)}"
        save_chat_message(DB_PATH, user_id, session_id, 'bot', error_message)
        return jsonify({
            'success': False,
            'message': error_message,
            'session_id': session_id
        }), 500


@app.route('/api/chatbot/history', methods=['GET'])
def get_chatbot_history():
    """Get chat history for a user"""
    user_id = request.args.get('user_id', type=int)
    session_id = request.args.get('session_id')
    
    if not user_id:
        return jsonify({'success': False, 'message': 'User ID is required'}), 400
    
    history = get_chat_history(DB_PATH, user_id, session_id)
    
    return jsonify({
        'success': True,
        'history': history,
        'session_id': session_id
    })


@app.route('/api/chatbot/sessions', methods=['GET'])
def get_chatbot_sessions():
    """Get all chat sessions for a user"""
    user_id = request.args.get('user_id', type=int)
    
    if not user_id:
        return jsonify({'success': False, 'message': 'User ID is required'}), 400
    
    sessions = get_chat_history(DB_PATH, user_id, session_id=None)
    
    return jsonify({
        'success': True,
        'sessions': sessions
    })


@app.route('/api/chatbot/prompts', methods=['GET'])
def get_chatbot_prompts():
    """Get available prompt-SQL pairs (for help/documentation)"""
    category = request.args.get('category')
    
    prompts = vector_engine.get_all_prompts(category)
    
    # Don't expose the actual SQL queries, just the templates and descriptions
    safe_prompts = []
    for p in prompts:
        templates = p['prompt_template'].split('|')
        safe_prompts.append({
            'id': p['id'],
            'examples': templates[:3],  # Show first 3 examples
            'description': p['description'],
            'category': p['category']
        })
    
    return jsonify({
        'success': True,
        'prompts': safe_prompts
    })


@app.route('/api/chatbot/history/clear', methods=['POST'])
def clear_chatbot_history():
    """Clear chat history for a user or specific session"""
    data = request.json
    user_id = data.get('user_id')
    session_id = data.get('session_id')
    
    if not user_id:
        return jsonify({'success': False, 'message': 'User ID is required'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if session_id:
        cursor.execute('DELETE FROM chat_history WHERE user_id = ? AND session_id = ?',
                      (user_id, session_id))
    else:
        cursor.execute('DELETE FROM chat_history WHERE user_id = ?', (user_id,))
    
    conn.commit()
    conn.close()
    
    return jsonify({
        'success': True,
        'message': 'Chat history cleared successfully'
    })


if __name__ == '__main__':
    # Create uploads directory if not exists
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    
    print("Starting Workforce & Payroll Management Backend Server...")
    print(f"Database: {DB_PATH}")
    print("API Documentation:")
    print("  - Auth: POST /api/login")
    print("  - Employees: GET/POST /api/employees")
    print("  - Attendance: GET/POST /api/attendance")
    print("  - Incentives: GET/POST /api/incentives")
    print("  - Penalties: GET/POST /api/penalties")
    print("  - Advances: GET/POST /api/advance")
    print("  - Payroll: POST /api/payroll/compute")
    print("  - Chatbot: POST /api/chatbot/query")
    print("  - Chatbot History: GET /api/chatbot/history")
    print("")
    app.run(host='0.0.0.0', port=5001, debug=True)
