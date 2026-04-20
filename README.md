# Workforce & Payroll Management System

A comprehensive web-based application for managing workforce, payroll, attendance, incentives, penalties, and salary advances. Features an AI-powered chatbot assistant for querying employee data using natural language.

## Features

- **Employee Management**: Add, update, archive employees; manage roles and store assignments
- **Attendance Tracking**: Daily attendance logging with present/absent/overtime status
- **Payroll Processing**: Automated monthly payroll calculation with incentives, penalties, and deductions
- **Incentives & Penalties**: Track daily performance incentives and penalties
- **Salary Advances**: Manage employee salary advance requests with eligibility checks
- **Store Management**: Multi-store support with employee distribution
- **AI Chatbot Assistant**: Natural language queries for employee, attendance, and payroll data using TF-IDF vector search
- **User Authentication**: Role-based access (Admin, Manager, Employee)

## Technology Stack

- **Backend**: Flask (Python), SQLite Database
- **Frontend**: Flask (Python), Bootstrap 5, Jinja2 Templates
- **AI/NLP**: TF-IDF Vector Search for query matching
- **Authentication**: Session-based with Flask

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

## Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/21f1006319/JAN2026-Team-097.git
cd JAN2026-Team-097
```

### 2. Backend Setup

Navigate to the backend directory and install dependencies:

```bash
cd backend
pip3 install -r requirements.txt
```

#### Initialize Database

Run the database initialization script:

```bash
python3 initialize_db.py
```

This creates the main database with all required tables and default data.

#### Run Database Migrations (for AI Chatbot)

```bash
python3 chatbot_migrations.py
```

This creates the `prompt_sql_pairs` and `chat_history` tables.

#### Populate Vector Database

```bash
python3 populate_vector_db.py
```

This populates the vector database with 25 predefined prompt-SQL pairs for the AI chatbot.

#### Start Backend Server

```bash
python3 app.py
```

The backend API server will start at `http://localhost:5001`

### 3. Frontend Setup

Open a new terminal and navigate to the frontend directory:

```bash
cd frontend
pip3 install -r requirements.txt
```

#### Start Frontend Server

```bash
python3 app.py
```

The frontend application will start at `http://localhost:5000`

### Alternative Port for Frontend

If port 5000 is in use, edit `frontend/app.py` and change the port:

```python
app.run(host='0.0.0.0', port=5002, debug=True)
```

## Accessing the Application

Once both servers are running:

1. Open your browser and go to: `http://localhost:5000`
2. Default login credentials:
   - **Admin**: username `admin`, password `admin123`
   - **Manager/Employee**: Created through admin panel

## AI Chatbot Feature

The AI Assistant allows users to ask natural language questions about workforce data. Examples:

- "Show me all active employees"
- "What is the total payroll amount for March 2026?"
- "Show attendance for today"
- "List all stores"
- "Show pending salary advances"
- "Find employees with salary above 30000"

### How AI Chatbot Works

1. **TF-IDF Vector Search**: Matches user queries against stored prompt-SQL pairs
2. **Multi-Strategy Matching**: Uses keyword overlap, template matching, phrase containment, and TF-IDF similarity
3. **Parameter Extraction**: Automatically extracts month, year, and amount from queries
4. **SQL Execution**: Executes the matched SQL query on the database
5. **Chat History**: Persists conversations per user across sessions

## Project Structure

```
JAN2026-Team-097/
├── backend/
│   ├── app.py                 # Main Flask backend API
│   ├── app_database.db        # SQLite database
│   ├── initialize_db.py       # Database initialization script
│   ├── chatbot_migrations.py  # Chatbot table migrations
│   ├── chatbot_utils.py       # Vector search engine
│   ├── populate_vector_db.py  # Seed prompt-SQL pairs
│   └── requirements.txt       # Python dependencies
├── frontend/
│   ├── app.py                 # Main Flask frontend application
│   ├── templates/             # HTML templates
│   │   ├── chatbot.html       # AI chatbot interface
│   │   ├── navbar.html        # Navigation bar
│   │   └── ...
│   ├── static/                # CSS, JS, images
│   └── requirements.txt       # Python dependencies
└── README.md                  # This file
```

## Database Schema

### Main Tables
- `users`: Authentication and user accounts
- `employees`: Employee details and salary information
- `stores`: Store locations and details
- `attendance`: Daily attendance records
- `payroll`: Monthly payroll summaries
- `payroll_details`: Detailed payroll line items
- `incentives`: Performance incentives
- `penalties`: Penalty records
- `salary_advances`: Advance requests and approvals
- `global_settings`: Application configuration

### Chatbot Tables
- `prompt_sql_pairs`: Stores prompt-SQL mappings for RAG
- `chat_history`: User chat sessions and messages

## API Endpoints

### Authentication
- `POST /api/login` - User login
- `POST /api/logout` - User logout
- `GET /api/session` - Get current session info

### Employees
- `GET /api/employees` - List all employees
- `POST /api/employees` - Create new employee
- `PUT /api/employees/<id>` - Update employee
- `DELETE /api/employees/<id>` - Archive employee

### Attendance
- `GET /api/attendance` - List attendance records
- `POST /api/attendance` - Add attendance record

### Payroll
- `GET /api/payroll` - List payroll records
- `POST /api/payroll/generate` - Generate monthly payroll
- `GET /api/payroll/<id>` - Get payroll details

### AI Chatbot
- `POST /api/chatbot/query` - Process chatbot query
- `GET /api/chatbot/history` - Get chat history
- `GET /api/chatbot/sessions` - Get chat sessions
- `POST /api/chatbot/history/clear` - Clear chat history

## Troubleshooting

### Port Already in Use
If you get "Address already in use" error:

**For Frontend:**
1. Edit `frontend/app.py`
2. Change `port=5000` to `port=5002` (or any available port)
3. Update `BACKEND_URL` if necessary

**Kill existing processes:**
```bash
# Find process using port 5000
lsof -i :5000

# Kill the process
kill -9 <PID>
```

### Module Not Found Error
If you see `ModuleNotFoundError`:
```bash
pip3 install -r requirements.txt
```

### Database Issues
To reset the database:
```bash
cd backend
rm app_database.db
python3 initialize_db.py
python3 chatbot_migrations.py
python3 populate_vector_db.py
```

### macOS AirPlay Receiver
On macOS, if port 5000 is used by AirPlay:
1. Go to System Preferences → Sharing
2. Disable "AirPlay Receiver"
3. Or use a different port as described above

## Development

### Adding New Prompt-SQL Pairs

Edit `backend/populate_vector_db.py` and add entries to the `prompt_sql_pairs` list:

```python
{
    'prompt_template': 'Your question variations|Separated by pipes',
    'prompt_keywords': 'space separated keywords for matching',
    'sql_query': 'SELECT * FROM table WHERE condition',
    'description': 'Description of what this query does',
    'category': 'category_name'
}
```

Then run:
```bash
python3 populate_vector_db.py
```

## Contributing

1. Create a feature branch
2. Make your changes
3. Test thoroughly
4. Submit a pull request

## License

This project is for educational purposes.

## Contact

For issues or questions, please contact the development team.
