"""
Initialize Database Script for Workforce & Payroll Management System
Run this script once to create all database tables.
"""
import sqlite3
import os

def init_database():
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app_database.db')
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Enable foreign key support
    cursor.execute("PRAGMA foreign_keys = ON")
    
    # 1. Stores table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active INTEGER DEFAULT 1
        )
    ''')
    
    # 2. Global Settings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS global_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            setting_key TEXT UNIQUE NOT NULL,
            setting_value TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insert default paid leaves setting
    cursor.execute('''
        INSERT OR IGNORE INTO global_settings (setting_key, setting_value)
        VALUES ('paid_leaves_per_month', '4')
    ''')
    
    # 3. Users table (for authentication)
    cursor.execute('''
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
        )
    ''')
    
    # 4. Employees table
    cursor.execute('''
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
        )
    ''')
    
    # 5. Attendance table
    cursor.execute('''
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
        )
    ''')
    
    # 6. Incentives table
    cursor.execute('''
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
        )
    ''')
    
    # 7. Penalties table
    cursor.execute('''
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
        )
    ''')
    
    # 8. Salary Advances table
    cursor.execute('''
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
        )
    ''')
    
    # 9. Payroll table (final computed salaries)
    cursor.execute('''
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
        )
    ''')
    
    # 10. Payroll Details table (breakdown of incentives and penalties)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payroll_details (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            payroll_id INTEGER NOT NULL,
            detail_type TEXT NOT NULL CHECK(detail_type IN ('incentive_daily', 'incentive_monthly', 'penalty_daily', 'penalty_monthly', 'advance')),
            description TEXT,
            amount REAL NOT NULL,
            date DATE,
            FOREIGN KEY (payroll_id) REFERENCES payroll(id) ON DELETE CASCADE
        )
    ''')
    
    # Create default admin user (password: admin123)
    cursor.execute('''
        INSERT OR IGNORE INTO users (username, password, role, email)
        VALUES ('admin', 'admin123', 'admin', 'admin@company.com')
    ''')
    
    # Create a default store
    cursor.execute('''
        INSERT OR IGNORE INTO stores (name, address)
        VALUES ('Main Store', '123 Main Street, City')
    ''')
    
    conn.commit()
    conn.close()
    print(f"Database initialized successfully at: {db_path}")
    print("Default admin created: username='admin', password='admin123'")
    print("Default store created: 'Main Store'")

if __name__ == '__main__':
    init_database()
