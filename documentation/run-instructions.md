# Instructions to Run the Application

This guide provides step-by-step instructions to set up and run the Workforce & Payroll Management System with AI Chatbot.

## Prerequisites

Before starting, ensure you have:
- **Python 3.8 or higher** installed
- **pip** (Python package manager) installed
- **Git** installed (for cloning)
- A modern web browser (Chrome, Firefox, Safari, or Edge)

### Verify Python Installation

```bash
python3 --version
```

Should output something like `Python 3.9.x` or higher.

### Verify pip Installation

```bash
pip3 --version
```

## Step 1: Clone the Repository

```bash
git clone https://github.com/21f1006319/JAN2026-Team-097.git
cd JAN2026-Team-097
```

## Step 2: Backend Setup

### 2.1 Navigate to Backend Directory

```bash
cd backend
```

### 2.2 Install Dependencies

```bash
pip3 install -r requirements.txt
```

Expected output:
```
Requirement already satisfied: Flask==2.3.3
Collecting Flask-Cors==4.0.0
Collecting requests==2.31.0
Successfully installed Flask-Cors-4.0.0 requests-2.31.0
```

### 2.3 Initialize the Database

```bash
python3 initialize_db.py
```

This creates:
- All database tables (users, employees, stores, attendance, payroll, etc.)
- Default admin user
- Default store

Expected output:
```
Database initialized successfully!
Default admin user created.
Default store created.
```

### 2.4 Run Chatbot Migrations

```bash
python3 chatbot_migrations.py
```

This creates AI chatbot tables:
- `prompt_sql_pairs` - Stores prompt-SQL mappings
- `chat_history` - Stores user conversations

Expected output:
```
Chatbot migrations completed successfully!
Created table: prompt_sql_pairs
Created table: chat_history
Created index: idx_chat_history_user_session
```

### 2.5 Populate Vector Database

```bash
python3 populate_vector_db.py
```

This populates the vector database with 25 predefined prompt-SQL pairs for the AI chatbot.

Expected output:
```
Vector database populated successfully!
Added 25 prompt-SQL pairs

Categories breakdown:
  - advances: 2 queries
  - attendance: 4 queries
  - employee: 8 queries
  - general: 1 queries
  - incentives: 3 queries
  - payroll: 3 queries
  - penalties: 3 queries
  - stores: 1 queries
```

### 2.6 Start Backend Server

```bash
python3 app.py
```

Expected output:
```
Starting Workforce & Payroll Management Backend API Server...
Backend API running at: http://localhost:5001/api
Database: backend/app_database.db

Available Endpoints:
- Auth: /api/login, /api/logout, /api/session
- Users: /api/users, /api/users/<id>
- Employees: /api/employees, /api/employees/<id>
- Stores: /api/stores, /api/stores/<id>
- Attendance: /api/attendance
- Incentives: /api/incentives
- Penalties: /api/penalties
- Salary Advances: /api/advances
- Payroll: /api/payroll, /api/payroll/generate, /api/payroll/finalize
- Reports: /api/reports/dashboard, /api/reports/payroll
- Chatbot: /api/chatbot/query, /api/chatbot/history, /api/chatbot/sessions

 * Serving Flask app 'app'
 * Debug mode: on
```

**Leave this terminal running.** The backend server must stay active.

## Step 3: Frontend Setup

Open a **new terminal window/tab** and navigate to the frontend directory.

### 3.1 Navigate to Frontend Directory

```bash
cd /path/to/JAN2026-Team-097/frontend
```

Example on macOS:
```bash
cd ~/Documents/IIT\ Madras/SE/JAN2026-Team-097/frontend
```

### 3.2 Install Dependencies

```bash
pip3 install -r requirements.txt
```

Expected output:
```
Requirement already satisfied: Flask==2.3.3
```

### 3.3 Start Frontend Server

```bash
python3 app.py
```

Expected output:
```
Starting Workforce & Payroll Management Frontend Server...
Connecting to Backend at: http://localhost:5001/api

Access the application at: http://localhost:5000

 * Serving Flask app 'app'
 * Debug mode: on
```

**Leave this terminal running.** The frontend server must stay active.

## Step 4: Access the Application

1. Open your web browser
2. Navigate to: `http://localhost:5000`
3. You should see the login page

### Default Login Credentials

| Role | Username | Password |
|------|----------|----------|
| Admin | `admin` | `admin123` |

**Note:** Manager and Employee accounts are created through the admin panel after logging in as admin.

## Verifying the Setup

### Test Backend API

Visit in browser or use curl:
```bash
curl http://localhost:5001/api/session
```

Should return:
```json
{"logged_in": false}
```

### Test AI Chatbot

1. Log in to the application
2. Click on "AI Assistant" in the navigation bar
3. Try asking: "Show me all active employees"
4. The chatbot should respond with a table of employees

## Common Issues and Solutions

### Issue: "Address already in use" - Port 5000

**Cause:** Another program (like macOS AirPlay Receiver) is using port 5000.

**Solution 1: Use a different port**

Edit `frontend/app.py` and change the port:

```python
# Find this line at the end of the file
app.run(host='0.0.0.0', port=5000, debug=True)

# Change to:
app.run(host='0.0.0.0', port=5002, debug=True)
```

Then access at `http://localhost:5002`

**Solution 2: Kill the process using port 5000**

On macOS/Linux:
```bash
# Find the process
lsof -i :5000

# Kill it (replace <PID> with the process ID)
kill -9 <PID>
```

On Windows:
```cmd
netstat -ano | findstr :5000
taskkill /PID <PID> /F
```

**Solution 3: Disable macOS AirPlay Receiver**
1. Go to System Preferences → Sharing
2. Uncheck "AirPlay Receiver"

### Issue: "ModuleNotFoundError: No module named 'flask_cors'"

**Cause:** Dependencies not installed.

**Solution:**
```bash
pip3 install -r requirements.txt
```

### Issue: "Database is locked"

**Cause:** Multiple processes accessing the database.

**Solution:**
1. Stop all running Python processes
2. Restart the backend server

### Issue: Chatbot returns "beyond scope" for valid queries

**Cause:** Vector database not populated.

**Solution:**
```bash
cd backend
python3 populate_vector_db.py
```

### Issue: Frontend can't connect to backend

**Cause:** Backend server not running or wrong URL.

**Solution:**
1. Ensure backend is running on port 5001
2. Check `BACKEND_URL` in `frontend/app.py`:
   ```python
   BACKEND_URL = 'http://localhost:5001/api'
   ```
3. If using a different port, update accordingly

## Quick Start Commands Summary

```bash
# Terminal 1 - Backend
cd backend
pip3 install -r requirements.txt
python3 initialize_db.py          # First time only
python3 chatbot_migrations.py     # First time only
python3 populate_vector_db.py     # First time only
python3 app.py                    # Start server

# Terminal 2 - Frontend
cd frontend
pip3 install -r requirements.txt
python3 app.py                    # Start server

# Browser
open http://localhost:5000
```

## Database Reset (If Needed)

If you need to reset the database:

```bash
cd backend
rm app_database.db
python3 initialize_db.py
python3 chatbot_migrations.py
python3 populate_vector_db.py
```

**Warning:** This deletes all data including users, employees, and payroll records.

## Development Mode

Both servers run with `debug=True`, which means:
- Auto-reload when code changes
- Detailed error messages
- Do NOT use in production

## Production Deployment Notes

For production deployment:
1. Set `debug=False` in both backend and frontend
2. Use a production WSGI server (Gunicorn, uWSGI)
3. Use a production database (PostgreSQL, MySQL)
4. Enable HTTPS
5. Set proper environment variables for secrets

## Support

For issues or questions:
1. Check the Troubleshooting section above
2. Review the error messages in the terminal
3. Contact the development team
