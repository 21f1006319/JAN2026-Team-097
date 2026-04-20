"""
Populate Vector Database with Prompt-SQL Pairs
Pre-populates the prompt_sql_pairs table with common queries for the Workforce & Payroll system
"""
import sqlite3
import os

def populate_vector_db():
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app_database.db')
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Define prompt-SQL pairs based on the database schema
    prompt_sql_pairs = [
        # Employee-related queries
        {
            'prompt_template': 'Show me all active employees|List all employees|Who are the active employees|Display employee list',
            'prompt_keywords': 'employees active list all show display who',
            'sql_query': "SELECT e.id, e.name, e.email, e.phone, e.role_type, e.base_monthly_salary, s.name as store_name, e.date_of_joining FROM employees e LEFT JOIN stores s ON e.store_id = s.id WHERE e.is_archived = 0 ORDER BY e.name",
            'description': 'List all active employees with their details and store information',
            'category': 'employee'
        },
        {
            'prompt_template': 'How many employees are in each store|Employee count by store|Number of employees per store|Store wise employee count',
            'prompt_keywords': 'employees count store number per wise each how many',
            'sql_query': "SELECT s.name as store_name, COUNT(e.id) as employee_count FROM stores s LEFT JOIN employees e ON s.id = e.store_id AND e.is_archived = 0 GROUP BY s.id, s.name ORDER BY employee_count DESC",
            'description': 'Get employee count grouped by store',
            'category': 'employee'
        },
        {
            'prompt_template': 'Find employees with salary greater than {amount}|Show employees earning more than {amount}|Employees with salary above {amount}|High salary employees',
            'prompt_keywords': 'salary greater than above more earning high employees',
            'sql_query': "SELECT e.id, e.name, e.email, e.base_monthly_salary, s.name as store_name FROM employees e LEFT JOIN stores s ON e.store_id = s.id WHERE e.is_archived = 0 AND e.base_monthly_salary > {amount} ORDER BY e.base_monthly_salary DESC",
            'description': 'Find employees with salary greater than a specified amount',
            'category': 'employee'
        },
        
        # Attendance-related queries
        {
            'prompt_template': 'Show attendance for today|Who is present today|Today attendance|Present employees today|Today\'s attendance report',
            'prompt_keywords': 'attendance today present who today current date',
            'sql_query': "SELECT e.name as employee_name, a.status, a.overtime_hours, e.role_type FROM attendance a JOIN employees e ON a.employee_id = e.id WHERE a.date = date('now') ORDER BY e.name",
            'description': 'Show attendance records for today',
            'category': 'attendance'
        },
        {
            'prompt_template': 'Show attendance for {month}/{year}|Attendance report for {month} {year}|Monthly attendance for {month}/{year}|Who was present in {month} {year}',
            'prompt_keywords': 'attendance month year report monthly date',
            'sql_query': "SELECT e.name as employee_name, COUNT(CASE WHEN a.status = 'Present' THEN 1 END) as days_present, COUNT(CASE WHEN a.status = 'Absent' THEN 1 END) as days_absent, SUM(a.overtime_hours) as total_overtime FROM attendance a JOIN employees e ON a.employee_id = e.id WHERE strftime('%m', a.date) = '{month:02d}' AND strftime('%Y', a.date) = '{year}' GROUP BY e.id, e.name ORDER BY e.name",
            'description': 'Show monthly attendance summary for a specific month and year',
            'category': 'attendance'
        },
        
        # Payroll-related queries
        {
            'prompt_template': 'Show payroll for {month}/{year}|Payroll report for {month} {year}|Salary details for {month}/{year}|Monthly payroll {month} {year}',
            'prompt_keywords': 'payroll salary report month year monthly details',
            'sql_query': "SELECT e.name as employee_name, p.base_salary, p.days_present, p.days_absent, p.total_incentives, p.total_penalties, p.net_salary, p.status FROM payroll p JOIN employees e ON p.employee_id = e.id WHERE p.month = {month} AND p.year = {year} ORDER BY p.net_salary DESC",
            'description': 'Show payroll details for a specific month and year',
            'category': 'payroll'
        },
        {
            'prompt_template': 'What is the total payroll amount for {month}/{year}|Total salary paid in {month} {year}|Sum of all salaries for {month}/{year}|Total payroll cost {month} {year}',
            'prompt_keywords': 'total payroll amount salary sum cost paid',
            'sql_query': "SELECT COUNT(*) as total_employees, SUM(p.net_salary) as total_payroll_amount, AVG(p.net_salary) as average_salary FROM payroll p WHERE p.month = {month} AND p.year = {year} AND p.status = 'finalized'",
            'description': 'Get total payroll amount for a specific month and year',
            'category': 'payroll'
        },
        
        # Incentives-related queries
        {
            'prompt_template': 'Show incentives for {month}/{year}|List all incentives in {month} {year}|Incentive report for {month}/{year}|Who received incentives in {month} {year}',
            'prompt_keywords': 'incentives bonus rewards month year report list',
            'sql_query': "SELECT e.name as employee_name, i.amount, i.incentive_type, i.description, i.date FROM incentives i JOIN employees e ON i.employee_id = e.id WHERE i.month = {month} AND i.year = {year} ORDER BY i.amount DESC",
            'description': 'Show all incentives for a specific month and year',
            'category': 'incentives'
        },
        {
            'prompt_template': 'Total incentives given in {month}/{year}|Sum of all incentives for {month} {year}|How much incentives paid in {month}/{year}|Incentive total {month} {year}',
            'prompt_keywords': 'total incentives sum amount paid how much',
            'sql_query': "SELECT COUNT(*) as total_incentive_records, SUM(i.amount) as total_incentive_amount, AVG(i.amount) as average_incentive FROM incentives i WHERE i.month = {month} AND i.year = {year}",
            'description': 'Get total incentives paid for a specific month and year',
            'category': 'incentives'
        },
        
        # Penalties-related queries
        {
            'prompt_template': 'Show penalties for {month}/{year}|List all penalties in {month} {year}|Penalty report for {month}/{year}|Who got penalties in {month} {year}',
            'prompt_keywords': 'penalties fines deductions month year report list',
            'sql_query': "SELECT e.name as employee_name, p.amount, p.penalty_type, p.description, p.date FROM penalties p JOIN employees e ON p.employee_id = e.id WHERE p.month = {month} AND p.year = {year} ORDER BY p.amount DESC",
            'description': 'Show all penalties for a specific month and year',
            'category': 'penalties'
        },
        
        # Salary Advances queries
        {
            'prompt_template': 'Show salary advances for {month}/{year}|List all advances in {month} {year}|Advance report {month}/{year}|Who took salary advances in {month} {year}',
            'prompt_keywords': 'salary advances loans month year report list',
            'sql_query': "SELECT e.name as employee_name, sa.amount, sa.request_date, sa.day_of_month, sa.eligible_days, sa.status FROM salary_advances sa JOIN employees e ON sa.employee_id = e.id WHERE sa.month = {month} AND sa.year = {year} ORDER BY sa.request_date DESC",
            'description': 'Show all salary advances for a specific month and year',
            'category': 'advances'
        },
        {
            'prompt_template': 'Show pending salary advances|List pending advances|Advances awaiting approval|Pending advance requests',
            'prompt_keywords': 'pending advances salary awaiting approval requests',
            'sql_query': "SELECT e.name as employee_name, sa.amount, sa.request_date, sa.month, sa.year FROM salary_advances sa JOIN employees e ON sa.employee_id = e.id WHERE sa.status = 'pending' ORDER BY sa.request_date DESC",
            'description': 'Show all pending salary advance requests',
            'category': 'advances'
        },
        
        # Store-related queries
        {
            'prompt_template': 'List all stores|Show all stores|What stores do we have|Store locations',
            'prompt_keywords': 'stores list all show locations what',
            'sql_query': "SELECT s.id, s.name, s.address, s.created_at, COUNT(e.id) as employee_count FROM stores s LEFT JOIN employees e ON s.id = e.store_id AND e.is_archived = 0 WHERE s.is_active = 1 GROUP BY s.id, s.name, s.address, s.created_at ORDER BY s.name",
            'description': 'List all active stores with employee count',
            'category': 'stores'
        },
        
        # General/System queries
        {
            'prompt_template': 'What is the current paid leaves setting|How many paid leaves per month|Paid leaves configuration|Leave settings',
            'prompt_keywords': 'paid leaves setting configuration how many per month',
            'sql_query': "SELECT setting_key, setting_value, updated_at FROM global_settings WHERE setting_key = 'paid_leaves_per_month'",
            'description': 'Get the current paid leaves per month setting',
            'category': 'general'
        },
        {
            'prompt_template': 'Show archived employees|List inactive employees|Who are the archived employees|Former employees list',
            'prompt_keywords': 'archived inactive employees former list who',
            'sql_query': "SELECT e.id, e.name, e.email, e.phone, e.role_type, e.base_monthly_salary, s.name as store_name, e.date_of_joining FROM employees e LEFT JOIN stores s ON e.store_id = s.id WHERE e.is_archived = 1 ORDER BY e.name",
            'description': 'List all archived (inactive) employees',
            'category': 'employee'
        },
        
        # Additional Employee queries
        {
            'prompt_template': 'Find employee by name {name}|Search employee {name}|Get details of {name}|Who is {name}',
            'prompt_keywords': 'find search employee name who details',
            'sql_query': "SELECT e.id, e.name, e.email, e.phone, e.role_type, e.base_monthly_salary, e.date_of_joining, s.name as store_name FROM employees e LEFT JOIN stores s ON e.store_id = s.id WHERE e.name LIKE '%{name}%' AND e.is_archived = 0",
            'description': 'Find employee by name',
            'category': 'employee'
        },
        {
            'prompt_template': 'Show employees by role {role_type}|List all {role_type} staff|Who works as {role_type}|Employees with role {role_type}',
            'prompt_keywords': 'employees role staff works picking put-away audit',
            'sql_query': "SELECT e.id, e.name, e.email, e.phone, e.base_monthly_salary, s.name as store_name, e.date_of_joining FROM employees e LEFT JOIN stores s ON e.store_id = s.id WHERE e.role_type = '{role_type}' AND e.is_archived = 0 ORDER BY e.name",
            'description': 'Show employees filtered by role type (Picking, Put-away, Audit)',
            'category': 'employee'
        },
        {
            'prompt_template': 'Highest paid employees|Top earners|Who earns the most|Employees with highest salary',
            'prompt_keywords': 'highest paid top earners salary most earning',
            'sql_query': "SELECT e.id, e.name, e.email, e.base_monthly_salary, s.name as store_name, e.role_type FROM employees e LEFT JOIN stores s ON e.store_id = s.id WHERE e.is_archived = 0 ORDER BY e.base_monthly_salary DESC LIMIT 10",
            'description': 'Show top 10 highest paid employees',
            'category': 'employee'
        },
        {
            'prompt_template': 'Newest employees|Recently joined employees|Who joined last|Latest employees joined',
            'prompt_keywords': 'newest recently joined latest employees date',
            'sql_query': "SELECT e.id, e.name, e.email, e.date_of_joining, e.role_type, e.base_monthly_salary, s.name as store_name FROM employees e LEFT JOIN stores s ON e.store_id = s.id WHERE e.is_archived = 0 ORDER BY e.date_of_joining DESC LIMIT 10",
            'description': 'Show recently joined employees',
            'category': 'employee'
        },
        
        # Additional Attendance queries
        {
            'prompt_template': 'Who is absent today|Show absent employees today|Today absent list|Absent staff today',
            'prompt_keywords': 'absent today employees staff list who',
            'sql_query': "SELECT e.name as employee_name, e.role_type, s.name as store_name FROM attendance a JOIN employees e ON a.employee_id = e.id LEFT JOIN stores s ON e.store_id = s.id WHERE a.date = date('now') AND a.status = 'Absent' ORDER BY e.name",
            'description': 'Show employees who are absent today',
            'category': 'attendance'
        },
        {
            'prompt_template': 'Overtime report for {month}/{year}|Who worked overtime in {month} {year}|Overtime hours {month}/{year}|Extra hours worked {month} {year}',
            'prompt_keywords': 'overtime hours extra worked report month year',
            'sql_query': "SELECT e.name as employee_name, SUM(a.overtime_hours) as total_overtime_hours, COUNT(*) as days_with_overtime FROM attendance a JOIN employees e ON a.employee_id = e.id WHERE strftime('%m', a.date) = '{month:02d}' AND strftime('%Y', a.date) = '{year}' AND a.overtime_hours > 0 GROUP BY e.id, e.name ORDER BY total_overtime_hours DESC",
            'description': 'Show overtime report for a specific month',
            'category': 'attendance'
        },
        
        # Additional Payroll queries
        {
            'prompt_template': 'Highest net salary in {month}/{year}|Top paid employees {month} {year}|Who got highest salary {month}/{year}|Best earners {month} {year}',
            'prompt_keywords': 'highest net salary top paid earners month year',
            'sql_query': "SELECT e.name as employee_name, p.net_salary, p.base_salary, p.total_incentives, p.total_penalties FROM payroll p JOIN employees e ON p.employee_id = e.id WHERE p.month = {month} AND p.year = {year} ORDER BY p.net_salary DESC LIMIT 10",
            'description': 'Show employees with highest net salary for a month',
            'category': 'payroll'
        },
        
        # Additional Incentives queries
        {
            'prompt_template': 'Top incentives receiver in {month}/{year}|Who got highest incentive {month} {year}|Best performing employee incentives {month}/{year}',
            'prompt_keywords': 'top incentives highest receiver performing employee',
            'sql_query': "SELECT e.name as employee_name, SUM(i.amount) as total_incentives, COUNT(*) as incentive_count, i.incentive_type FROM incentives i JOIN employees e ON i.employee_id = e.id WHERE i.month = {month} AND i.year = {year} GROUP BY e.id, e.name ORDER BY total_incentives DESC LIMIT 10",
            'description': 'Show employees who received highest incentives',
            'category': 'incentives'
        },
        
        # Additional Penalties queries
        {
            'prompt_template': 'Total penalties in {month}/{year}|Sum of all penalties for {month} {year}|Penalty cost {month}/{year}|How much penalties deducted {month} {year}',
            'prompt_keywords': 'total penalties sum cost deducted amount month year',
            'sql_query': "SELECT COUNT(*) as total_penalty_records, SUM(p.amount) as total_penalty_amount, AVG(p.amount) as average_penalty FROM penalties p WHERE p.month = {month} AND p.year = {year}",
            'description': 'Get total penalties deducted for a specific month',
            'category': 'penalties'
        },
        {
            'prompt_template': 'Employees with most penalties {month}/{year}|Who got maximum penalties {month} {year}|Top penalty receivers {month}/{year}',
            'prompt_keywords': 'employees most penalties maximum receivers top',
            'sql_query': "SELECT e.name as employee_name, SUM(p.amount) as total_penalties, COUNT(*) as penalty_count FROM penalties p JOIN employees e ON p.employee_id = e.id WHERE p.month = {month} AND p.year = {year} GROUP BY e.id, e.name ORDER BY total_penalties DESC LIMIT 10",
            'description': 'Show employees with highest penalties',
            'category': 'penalties'
        },
    ]
    
    # Insert prompt-SQL pairs
    for pair in prompt_sql_pairs:
        cursor.execute('''
            INSERT OR IGNORE INTO prompt_sql_pairs (prompt_template, prompt_keywords, sql_query, description, category)
            VALUES (?, ?, ?, ?, ?)
        ''', (pair['prompt_template'], pair['prompt_keywords'], pair['sql_query'], pair['description'], pair['category']))
    
    conn.commit()
    conn.close()
    print(f"Vector database populated successfully!")
    print(f"Added {len(prompt_sql_pairs)} prompt-SQL pairs")
    print("\nCategories breakdown:")
    categories = {}
    for pair in prompt_sql_pairs:
        categories[pair['category']] = categories.get(pair['category'], 0) + 1
    for cat, count in sorted(categories.items()):
        print(f"  - {cat}: {count} queries")

if __name__ == '__main__':
    populate_vector_db()
