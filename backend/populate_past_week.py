"""
Populate Past Week Data Script for Workforce & Payroll Management System
Inserts realistic sample data (employees, attendance, incentives, penalties,
salary advances) covering the last 7 days, then verifies every row.

Usage:
    python populate_past_week.py           # populate + verify
    python populate_past_week.py --verify  # verify only (skip inserts)
"""

import sqlite3
import os
import sys
import random
from datetime import date, timedelta
import calendar

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app_database.db')

# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def last_7_days():
    today = date.today()
    return [today - timedelta(days=i) for i in range(6, -1, -1)]  # oldest → newest


# ──────────────────────────────────────────────
# Seed data definitions
# ──────────────────────────────────────────────

STORES = [
    {"name": "Main Store",  "address": "123 Main Street, City"},
    {"name": "North Depot", "address": "456 North Avenue, City"},
]

EMPLOYEES = [
    {"name": "Arjun Sharma",   "email": "arjun@company.com",   "phone": "9000000001",
     "role_type": "Picking",  "base_monthly_salary": 28000, "store_idx": 0},
    {"name": "Priya Patel",    "email": "priya@company.com",   "phone": "9000000002",
     "role_type": "Put-away", "base_monthly_salary": 30000, "store_idx": 0},
    {"name": "Ravi Kumar",     "email": "ravi@company.com",    "phone": "9000000003",
     "role_type": "Audit",    "base_monthly_salary": 35000, "store_idx": 1},
    {"name": "Sneha Mehta",    "email": "sneha@company.com",   "phone": "9000000004",
     "role_type": "Picking",  "base_monthly_salary": 26000, "store_idx": 1},
    {"name": "Deepak Singh",   "email": "deepak@company.com",  "phone": "9000000005",
     "role_type": "Put-away", "base_monthly_salary": 32000, "store_idx": 0},
]

# Per-employee attendance pattern for the 7-day window (index 0 = oldest day)
# Each tuple: (status, overtime_hours)
ATTENDANCE_PATTERNS = [
    [("Present", 0),   ("Present", 2.0), ("Present", 0),   ("Absent",  0),   ("Present", 1.5), ("Present", 0),   ("Present", 0)],
    [("Present", 0),   ("Half-day", 0),  ("Present", 0),   ("Present", 0),   ("Present", 0),   ("Absent",  0),   ("Present", 0)],
    [("Present", 3.0), ("Present", 0),   ("Present", 0),   ("Present", 2.5), ("Present", 0),   ("Present", 0),   ("Present", 1.0)],
    [("Absent",  0),   ("Present", 0),   ("Present", 0),   ("Half-day", 0),  ("Present", 0),   ("Present", 0),   ("Present", 0)],
    [("Present", 0),   ("Present", 1.0), ("Present", 0),   ("Present", 0),   ("Half-day", 0),  ("Present", 2.0), ("Present", 0)],
]

# (emp_idx, amount, incentive_type, day_offset_from_week_start, description)
INCENTIVES = [
    (0, 500,  "daily_performance", 1, "Exceeded picking quota"),
    (1, 800,  "daily_performance", 3, "Accurate put-away record"),
    (2, 1200, "daily_performance", 0, "Zero audit discrepancies"),
    (2, 2000, "monthly_bonus",     0, "Best auditor of the month"),
    (3, 400,  "daily_performance", 4, "Picked extra 50 items"),
    (4, 600,  "daily_performance", 5, "Overtime efficiency bonus"),
]

# (emp_idx, amount, penalty_type, day_offset_from_week_start, description)
PENALTIES = [
    (0, 200,  "daily",   3, "Late arrival"),
    (1, 150,  "daily",   5, "Incomplete task"),
    (3, 300,  "monthly", 0, "Safety violation"),
]

# (emp_idx, amount, day_offset_from_week_start)
ADVANCES = [
    (0, 5000,  4),
    (2, 8000,  5),
]


# ──────────────────────────────────────────────
# Populate
# ──────────────────────────────────────────────

def ensure_stores(cursor):
    """Insert stores if missing; return list of store ids."""
    store_ids = []
    for s in STORES:
        cursor.execute("SELECT id FROM stores WHERE name = ?", (s["name"],))
        row = cursor.fetchone()
        if row:
            store_ids.append(row["id"])
        else:
            cursor.execute(
                "INSERT INTO stores (name, address) VALUES (?, ?)",
                (s["name"], s["address"])
            )
            store_ids.append(cursor.lastrowid)
    return store_ids


def ensure_employees(cursor, store_ids):
    """Insert employees (+ linked users) if missing; return list of employee ids."""
    joining_date = (date.today() - timedelta(days=90)).isoformat()
    emp_ids = []
    for emp in EMPLOYEES:
        cursor.execute("SELECT id FROM employees WHERE email = ?", (emp["email"],))
        row = cursor.fetchone()
        if row:
            emp_ids.append(row["id"])
            print(f"  [skip] Employee already exists: {emp['name']}")
            continue

        username = emp["email"].split("@")[0]
        password = "pass" + emp["phone"][-4:]
        store_id = store_ids[emp["store_idx"]]

        # Create user account
        cursor.execute(
            "INSERT OR IGNORE INTO users (username, password, role, email, phone) "
            "VALUES (?, ?, 'employee', ?, ?)",
            (username, password, emp["email"], emp["phone"])
        )
        user_id = cursor.lastrowid or cursor.execute(
            "SELECT id FROM users WHERE username = ?", (username,)
        ).fetchone()["id"]

        # Create employee record
        cursor.execute(
            "INSERT INTO employees (user_id, name, email, phone, date_of_joining, "
            "role_type, base_monthly_salary, store_id) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (user_id, emp["name"], emp["email"], emp["phone"],
             joining_date, emp["role_type"], emp["base_monthly_salary"], store_id)
        )
        eid = cursor.lastrowid
        emp_ids.append(eid)
        print(f"  [add]  Employee: {emp['name']} (id={eid})")

    return emp_ids


def populate_attendance(cursor, emp_ids, days):
    inserted = 0
    for emp_idx, pattern in enumerate(ATTENDANCE_PATTERNS):
        eid = emp_ids[emp_idx]
        for day_idx, (status, ot) in enumerate(pattern):
            d = days[day_idx].isoformat()
            cursor.execute(
                "INSERT OR REPLACE INTO attendance "
                "(employee_id, date, status, overtime_hours) VALUES (?, ?, ?, ?)",
                (eid, d, status, ot)
            )
            inserted += 1
    return inserted


def populate_incentives(cursor, emp_ids, days):
    inserted = 0
    today = date.today()
    month, year = today.month, today.year
    for emp_idx, amount, itype, day_offset, desc in INCENTIVES:
        eid = emp_ids[emp_idx]
        d = days[day_offset].isoformat()
        cursor.execute(
            "INSERT INTO incentives "
            "(employee_id, amount, incentive_type, date, month, year, description) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (eid, amount, itype, d, month, year, desc)
        )
        inserted += 1
    return inserted


def populate_penalties(cursor, emp_ids, days):
    inserted = 0
    today = date.today()
    month, year = today.month, today.year
    for emp_idx, amount, ptype, day_offset, desc in PENALTIES:
        eid = emp_ids[emp_idx]
        d = days[day_offset].isoformat()
        cursor.execute(
            "INSERT INTO penalties "
            "(employee_id, amount, penalty_type, date, month, year, description) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (eid, amount, ptype, d, month, year, desc)
        )
        inserted += 1
    return inserted


def populate_advances(cursor, emp_ids, days):
    inserted = 0
    today = date.today()
    month, year = today.month, today.year
    total_days = calendar.monthrange(year, month)[1]
    for emp_idx, amount, day_offset in ADVANCES:
        eid = emp_ids[emp_idx]
        d = days[day_offset]
        day_of_month = d.day
        eligible_days = max(0, day_of_month - 7)

        # Check for existing advance for this employee in this month
        cursor.execute(
            "SELECT id FROM salary_advances WHERE employee_id = ? AND month = ? AND year = ?",
            (eid, month, year)
        )
        if cursor.fetchone():
            print(f"  [skip] Advance already exists for employee_id={eid} in {month}/{year}")
            continue

        cursor.execute(
            "INSERT INTO salary_advances "
            "(employee_id, amount, request_date, month, year, day_of_month, eligible_days, status) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, 'approved')",
            (eid, amount, d.isoformat(), month, year, day_of_month, eligible_days)
        )
        inserted += 1
    return inserted


def run_populate():
    days = last_7_days()
    print(f"\n=== Populating past 7 days: {days[0]} → {days[-1]} ===\n")

    conn = get_conn()
    cursor = conn.cursor()

    print("[Stores]")
    store_ids = ensure_stores(cursor)
    print(f"  Store ids: {store_ids}")

    print("\n[Employees]")
    emp_ids = ensure_employees(cursor, store_ids)
    print(f"  Employee ids: {emp_ids}")

    print("\n[Attendance]")
    n = populate_attendance(cursor, emp_ids, days)
    print(f"  Inserted/replaced {n} attendance records")

    print("\n[Incentives]")
    n = populate_incentives(cursor, emp_ids, days)
    print(f"  Inserted {n} incentive records")

    print("\n[Penalties]")
    n = populate_penalties(cursor, emp_ids, days)
    print(f"  Inserted {n} penalty records")

    print("\n[Salary Advances]")
    n = populate_advances(cursor, emp_ids, days)
    print(f"  Inserted {n} advance records")

    conn.commit()
    conn.close()
    print("\n[Done] All data committed.\n")
    return emp_ids, days


# ──────────────────────────────────────────────
# Verify
# ──────────────────────────────────────────────

PASS = "\033[32mPASS\033[0m"
FAIL = "\033[31mFAIL\033[0m"

def check(label, condition, detail=""):
    status = PASS if condition else FAIL
    suffix = f" — {detail}" if detail else ""
    print(f"  [{status}] {label}{suffix}")
    return condition


def run_verify():
    days = last_7_days()
    today = date.today()
    month, year = today.month, today.year
    week_dates = [d.isoformat() for d in days]

    conn = get_conn()
    cur = conn.cursor()
    failures = 0

    print(f"\n=== Verification (week {week_dates[0]} → {week_dates[-1]}, month={month}/{year}) ===\n")

    # 1. Stores
    print("[Stores]")
    cur.execute("SELECT count(*) AS n FROM stores")
    n = cur.fetchone()["n"]
    failures += 0 if check("At least 2 stores exist", n >= 2, f"found {n}") else 1

    # 2. Employees
    print("\n[Employees]")
    cur.execute("SELECT count(*) AS n FROM employees WHERE is_archived = 0")
    n = cur.fetchone()["n"]
    failures += 0 if check("At least 5 active employees", n >= 5, f"found {n}") else 1

    # Fetch only the employees this script manages (matched by email)
    our_emails = tuple(e["email"] for e in EMPLOYEES)
    placeholders = ",".join("?" * len(our_emails))
    cur.execute(
        f"SELECT id FROM employees WHERE email IN ({placeholders}) AND is_archived = 0",
        our_emails
    )
    emp_ids = [r["id"] for r in cur.fetchall()]

    # 3. Attendance — every seeded employee has ≥1 record in the past week
    print("\n[Attendance]")
    for eid in emp_ids:
        cur.execute(
            "SELECT count(*) AS n FROM attendance WHERE employee_id = ? AND date >= ? AND date <= ?",
            (eid, week_dates[0], week_dates[-1])
        )
        n = cur.fetchone()["n"]
        failures += 0 if check(f"  emp_id={eid} has attendance records", n > 0, f"{n} records") else 1

    # All statuses are valid
    cur.execute(
        "SELECT count(*) AS n FROM attendance "
        "WHERE date >= ? AND date <= ? AND status NOT IN ('Present','Absent','Half-day')",
        (week_dates[0], week_dates[-1])
    )
    bad = cur.fetchone()["n"]
    failures += 0 if check("No invalid attendance statuses", bad == 0, f"{bad} bad rows") else 1

    # Overtime hours >= 0
    cur.execute(
        "SELECT count(*) AS n FROM attendance WHERE date >= ? AND date <= ? AND overtime_hours < 0",
        (week_dates[0], week_dates[-1])
    )
    bad = cur.fetchone()["n"]
    failures += 0 if check("No negative overtime values", bad == 0) else 1

    # Total attendance rows = 5 employees * 7 days
    cur.execute(
        "SELECT count(*) AS n FROM attendance WHERE date >= ? AND date <= ?",
        (week_dates[0], week_dates[-1])
    )
    n = cur.fetchone()["n"]
    failures += 0 if check("Total attendance rows = 35 (5 × 7)", n == 35, f"found {n}") else 1

    # 4. Incentives
    print("\n[Incentives]")
    cur.execute(
        "SELECT count(*) AS n FROM incentives WHERE month = ? AND year = ?",
        (month, year)
    )
    n = cur.fetchone()["n"]
    failures += 0 if check(f"At least {len(INCENTIVES)} incentive records this month", n >= len(INCENTIVES), f"found {n}") else 1

    cur.execute(
        "SELECT count(*) AS n FROM incentives WHERE month = ? AND year = ? "
        "AND incentive_type NOT IN ('daily_performance','monthly_bonus')",
        (month, year)
    )
    bad = cur.fetchone()["n"]
    failures += 0 if check("No invalid incentive types", bad == 0) else 1

    cur.execute(
        "SELECT count(*) AS n FROM incentives WHERE month = ? AND year = ? AND amount <= 0",
        (month, year)
    )
    bad = cur.fetchone()["n"]
    failures += 0 if check("All incentive amounts > 0", bad == 0) else 1

    # Verify a specific incentive (Ravi Kumar / emp_idx=2 gets the 2000 monthly bonus)
    cur.execute(
        "SELECT e.name, i.amount, i.incentive_type FROM incentives i "
        "JOIN employees e ON i.employee_id = e.id "
        "WHERE i.incentive_type = 'monthly_bonus' AND i.month = ? AND i.year = ?",
        (month, year)
    )
    bonus_rows = cur.fetchall()
    has_monthly = any(r["amount"] == 2000 for r in bonus_rows)
    failures += 0 if check("2000 monthly_bonus incentive exists", has_monthly) else 1

    # 5. Penalties
    print("\n[Penalties]")
    cur.execute(
        "SELECT count(*) AS n FROM penalties WHERE month = ? AND year = ?",
        (month, year)
    )
    n = cur.fetchone()["n"]
    failures += 0 if check(f"At least {len(PENALTIES)} penalty records this month", n >= len(PENALTIES), f"found {n}") else 1

    cur.execute(
        "SELECT count(*) AS n FROM penalties WHERE month = ? AND year = ? "
        "AND penalty_type NOT IN ('daily','monthly')",
        (month, year)
    )
    bad = cur.fetchone()["n"]
    failures += 0 if check("No invalid penalty types", bad == 0) else 1

    cur.execute(
        "SELECT count(*) AS n FROM penalties WHERE month = ? AND year = ? AND amount <= 0",
        (month, year)
    )
    bad = cur.fetchone()["n"]
    failures += 0 if check("All penalty amounts > 0", bad == 0) else 1

    # 6. Salary Advances
    print("\n[Salary Advances]")
    cur.execute(
        "SELECT count(*) AS n FROM salary_advances WHERE month = ? AND year = ?",
        (month, year)
    )
    n = cur.fetchone()["n"]
    failures += 0 if check(f"At least {len(ADVANCES)} advance records this month", n >= len(ADVANCES), f"found {n}") else 1

    cur.execute(
        "SELECT count(*) AS n FROM salary_advances WHERE month = ? AND year = ? "
        "AND status NOT IN ('pending','approved','rejected','deducted')",
        (month, year)
    )
    bad = cur.fetchone()["n"]
    failures += 0 if check("No invalid advance statuses", bad == 0) else 1

    cur.execute(
        "SELECT count(*) AS n FROM salary_advances WHERE month = ? AND year = ? AND amount <= 0",
        (month, year)
    )
    bad = cur.fetchone()["n"]
    failures += 0 if check("All advance amounts > 0", bad == 0) else 1

    # Eligible days must be >= 0
    cur.execute(
        "SELECT count(*) AS n FROM salary_advances WHERE month = ? AND year = ? AND eligible_days < 0",
        (month, year)
    )
    bad = cur.fetchone()["n"]
    failures += 0 if check("No negative eligible_days", bad == 0) else 1

    # 7. Referential integrity — no orphan rows
    print("\n[Referential Integrity]")
    for tbl in ("attendance", "incentives", "penalties", "salary_advances"):
        cur.execute(
            f"SELECT count(*) AS n FROM {tbl} "
            f"WHERE employee_id NOT IN (SELECT id FROM employees)"
        )
        bad = cur.fetchone()["n"]
        failures += 0 if check(f"No orphan rows in {tbl}", bad == 0) else 1

    # 8. Summary counts
    print("\n[Summary]")
    cur.execute("SELECT count(*) AS n FROM attendance WHERE date >= ? AND date <= ?", (week_dates[0], week_dates[-1]))
    print(f"  Attendance rows this week : {cur.fetchone()['n']}")
    cur.execute("SELECT count(*) AS n FROM incentives WHERE month = ? AND year = ?", (month, year))
    print(f"  Incentive rows this month : {cur.fetchone()['n']}")
    cur.execute("SELECT count(*) AS n FROM penalties WHERE month = ? AND year = ?", (month, year))
    print(f"  Penalty rows this month   : {cur.fetchone()['n']}")
    cur.execute("SELECT count(*) AS n FROM salary_advances WHERE month = ? AND year = ?", (month, year))
    print(f"  Advance rows this month   : {cur.fetchone()['n']}")

    cur.execute(
        "SELECT e.name, "
        "  COUNT(CASE WHEN a.status='Present'  THEN 1 END) AS present, "
        "  COUNT(CASE WHEN a.status='Absent'   THEN 1 END) AS absent, "
        "  COUNT(CASE WHEN a.status='Half-day' THEN 1 END) AS halfday, "
        "  SUM(a.overtime_hours) AS ot "
        "FROM employees e "
        "LEFT JOIN attendance a ON a.employee_id = e.id "
        "  AND a.date >= ? AND a.date <= ? "
        "WHERE e.is_archived = 0 "
        "GROUP BY e.id ORDER BY e.name",
        (week_dates[0], week_dates[-1])
    )
    print("\n  Per-employee attendance breakdown (this week):")
    print(f"  {'Name':<20} {'Present':>7} {'Absent':>7} {'Half-day':>9} {'OT hrs':>7}")
    print("  " + "-" * 56)
    for r in cur.fetchall():
        print(f"  {r['name']:<20} {r['present']:>7} {r['absent']:>7} {r['halfday']:>9} {(r['ot'] or 0):>7.1f}")

    conn.close()

    print(f"\n{'='*50}")
    if failures == 0:
        print(f"  All checks passed!")
    else:
        print(f"  {failures} check(s) FAILED.")
    print(f"{'='*50}\n")
    return failures


# ──────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────

if __name__ == "__main__":
    verify_only = "--verify" in sys.argv

    if not os.path.exists(DB_PATH):
        print(f"ERROR: Database not found at {DB_PATH}")
        print("Run initialize_db.py first.")
        sys.exit(1)

    if not verify_only:
        run_populate()

    failures = run_verify()
    sys.exit(0 if failures == 0 else 1)
