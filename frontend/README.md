# Frontend UI Server

Flask-based web interface for the Workforce & Payroll Management System. Provides blue-themed, responsive UI for Admin, Manager, and Employee roles.

---

## Overview

The frontend server renders HTML templates and proxies API requests to the backend server (Port 5001). It handles user sessions, form submissions, and presents data in an intuitive interface.

- **Port**: 5000
- **Theme**: Shades of Blue (Navy, Dark Blue, Sky Blue, Light Blue)
- **Framework**: Flask + Jinja2 Templates + Bootstrap 5

---

## File Structure

```
frontend/
├── app.py                      # Main Flask application with routes
├── requirements.txt            # Python dependencies
├── templates/                  # Jinja2 HTML templates
│   ├── login.html             # Authentication page
│   ├── navbar.html            # Navigation component
│   ├── dashboard.html         # Main dashboard
│   ├── employees.html         # Employee list
│   ├── add_employee.html      # Add employee form
│   ├── edit_employee.html     # Edit employee form
│   ├── attendance.html        # Attendance management
│   ├── incentives.html        # Incentives entry
│   ├── penalties.html         # Penalties entry
│   ├── advances.html          # Salary advances (7-day rule)
│   ├── payroll.html           # Payroll computation
│   ├── payslip.html           # Payslip display/print
│   ├── settings.html          # System settings
│   └── employee_portal.html   # Employee self-service
└── static/
    └── css/
        └── style.css          # Blue-themed stylesheet
```

---

## Installation

```bash
pip install -r requirements.txt
```

### Dependencies
- Flask==2.3.3
- requests==2.31.0

---

## Running the Server

**Prerequisite**: Backend server must be running on Port 5001

```bash
python app.py
```

Access the application at: **http://localhost:5000**

---

## Routes Reference

### Authentication
| Route | Method | Description |
|-------|--------|-------------|
| `/` | GET | Redirects to login or dashboard |
| `/login` | GET/POST | User login page |
| `/logout` | GET | Clear session and logout |

### Dashboard
| Route | Method | Access | Description |
|-------|--------|--------|-------------|
| `/dashboard` | GET | Admin, Manager | Main dashboard with stats |

### Employee Management
| Route | Method | Access | Description |
|-------|--------|--------|-------------|
| `/employees` | GET | Admin, Manager | List all employees |
| `/employees/add` | GET/POST | Manager | Add new employee |
| `/employees/<id>/edit` | GET/POST | Manager | Edit employee |
| `/employees/<id>/archive` | POST | Admin | Archive/unarchive |
| `/employees/<id>/reset_password` | POST | Admin | Reset password |

### Operations
| Route | Method | Access | Description |
|-------|--------|--------|-------------|
| `/attendance` | GET/POST | Manager | Mark/view attendance |
| `/incentives` | GET/POST | Manager | Add/view incentives |
| `/incentives/<id>/delete` | POST | Manager | Delete incentive |
| `/penalties` | GET/POST | Manager | Add/view penalties |
| `/penalties/<id>/delete` | POST | Manager | Delete penalty |
| `/advances` | GET/POST | Manager | Process salary advances |

### Payroll (Admin Only)
| Route | Method | Description |
|-------|--------|-------------|
| `/payroll` | GET | View payroll records |
| `/payroll/compute` | POST | Compute monthly payroll |
| `/payroll/<id>/finalize` | POST | Finalize payroll |
| `/payroll/<id>/payslip` | GET | View payslip |

### Settings (Admin Only)
| Route | Method | Description |
|-------|--------|-------------|
| `/settings` | GET | System settings |
| `/settings/paid_leaves` | POST | Update paid leaves |
| `/settings/stores` | POST | Add store |

### Employee Portal
| Route | Method | Description |
|-------|--------|-------------|
| `/employee/portal` | GET | Employee dashboard |
| `/employee/payslip/<id>` | GET | View own payslip |
| `/employee/change_password` | POST | Change password |

---

## User Interface

### Blue Theme Color Palette

```css
--primary-blue: #1a56db;    /* Main actions */
--dark-blue: #1e3a8a;       /* Headers, navbar */
--navy-blue: #0f172a;       /* Deep accents */
--light-blue: #3b82f6;      /* Secondary buttons */
--sky-blue: #60a5fa;        /* Highlights */
--pale-blue: #dbeafe;       /* Backgrounds */
--very-light-blue: #eff6ff; /* Card backgrounds */
```

### Page Layouts

**Login Page**
- Centered card with gradient background
- Company logo in circular blue container
- Username/password form

**Dashboard**
- 4 stat cards (Active, Archived, Attendance, Advances)
- Quick action grid
- Store list sidebar

**Employee Management**
- Filterable table with store filter
- Archive/activate toggle
- Inline password reset

**Attendance**
- Split view: Entry form + Records table
- Date filtering
- Status badges (Present=green, Absent=red, Half-day=yellow)

**Adjustments (Incentives/Penalties)**
- Left: Entry form
- Right: Records table with delete action
- Month/year filtering

**Advances**
- 7-day rule eligibility calculator
- Auto-fill advance form from calculation
- Advance history with status badges

**Payroll**
- Compute form with store selector
- Detailed breakdown table
- Finalize action
- Payslip preview link

**Payslip**
- Print-ready format
- Company header with QR placeholder
- Two-column: Earnings/Deductions
- Net salary highlight box
- CSS media query for print hiding buttons

**Settings**
- Global settings panel
- Store management
- System info panel

**Employee Portal**
- Profile card with avatar
- Detail rows
- Password change form
- Salary history table
- Payslip links

---

## API Communication

The frontend uses the `api_call()` helper to communicate with the backend:

```python
def api_call(method, endpoint, data=None, params=None):
    url = f"http://localhost:5001/api{endpoint}"
    # Makes HTTP request to backend
    # Returns parsed JSON
```

### Example Usage

```python
# GET request
result = api_call('GET', '/employees', params={'store_id': 1})
employees = result.get('employees', [])

# POST request
result = api_call('POST', '/employees', data={
    'name': 'John Doe',
    'phone': '1234567890',
    'role_type': 'Picking',
    'base_monthly_salary': 30000
})
```

---

## Session Management

Flask sessions track user state:

```python
session['user_id']      # User's database ID
session['username']     # Login username
session['role']         # admin/manager/employee
session['email']        # User email
```

### Decorators

```python
@login_required    # Ensures user is logged in
@admin_required    # Ensures role is 'admin'
@manager_required  # Ensures role is 'admin' or 'manager'
```

---

## Template Features

### Bootstrap 5 Components
- Navigation bar with dropdowns
- Cards for content sections
- Tables with hover effects
- Forms with validation
- Alert notifications
- Badges for status

### Font Awesome Icons
All pages use Font Awesome 6 icons:
- Navigation: `fa-users-cog`, `fa-tachometer-alt`, etc.
- Actions: `fa-plus`, `fa-edit`, `fa-trash`, `fa-save`
- Status: `fa-check-circle`, `fa-times-circle`

### Responsive Design
- Mobile-friendly with Bootstrap grid
- Tables scroll horizontally on small screens
- Cards stack vertically on mobile

---

## Flash Messages

The frontend displays flash messages for user feedback:

```python
flash('Employee created successfully!', 'success')
flash('Error: Invalid credentials', 'danger')
flash('Please log in first', 'warning')
flash('Information updated', 'info')
```

Categories map to Bootstrap alert classes:
- `success` → Green alert
- `danger` → Red alert
- `warning` → Yellow alert
- `info` → Blue alert

---

## JavaScript Functions

### Advances Page - Eligibility Calculator

```javascript
function checkEligibility() {
    // Gets employee ID and date
    // Calls /api/advance/eligibility
    // Displays: day of month, eligible days, per-day salary, max advance
    // Auto-fills the advance form
}
```

---

## Print Styles

Payslip page has special print CSS:

```css
@media print {
    .no-print { display: none !important; }
    .main-content { margin: 0; padding: 0; }
    .payslip-container { box-shadow: none; border: 1px solid #ddd; }
}
```

This hides navigation and buttons when printing.

---

## Form Patterns

### Standard Form Layout
```html
<div class="content-card">
    <h5>Page Title</h5>
    <form method="POST" class="row g-3">
        <div class="col-md-6">
            <label class="form-label">Field Name</label>
            <input type="text" name="field_name" class="form-control" required>
        </div>
        <!-- More fields... -->
        <div class="col-12">
            <button type="submit" class="btn btn-primary">Save</button>
            <a href="..." class="btn btn-outline-secondary">Cancel</a>
        </div>
    </form>
</div>
```

### Filter Form Pattern
```html
<form method="GET" class="row g-3">
    <div class="col-md-3">
        <select name="store_id" class="form-select">
            <!-- Options -->
        </select>
    </div>
    <div class="col-md-3">
        <button type="submit" class="btn btn-outline-primary">Filter</button>
    </div>
</form>
```

---

## Troubleshooting

### "Cannot connect to backend" Error
- Verify backend is running: `http://localhost:5001`
- Check `BACKEND_URL` in `app.py`
- Check firewall settings

### Session Issues
- Clear browser cookies
- Check `app.secret_key` is set
- Verify session is being saved

### Template Not Found
- Ensure templates are in `templates/` folder
- Check template filename matches
- Verify file permissions

### CSS Not Loading
- Check browser console for 404 errors
- Verify `static/css/style.css` exists
- Check `url_for('static', filename='...')` paths

---

## Customization

### Changing Theme Colors

Edit `static/css/style.css`:

```css
:root {
    --primary-blue: #your-color;
    --dark-blue: #your-color;
    /* ... */
}
```

### Adding New Pages

1. Create HTML template in `templates/`
2. Add route in `app.py`:

```python
@app.route('/new-page')
@login_required
def new_page():
    return render_template('new_page.html')
```

3. Add navigation link in `templates/navbar.html`

### Adding API Endpoints

Update both backend and frontend:
1. Add endpoint in `backend/app.py`
2. Add route in `frontend/app.py` using `api_call()`

---

## Browser Compatibility

- Chrome 90+
- Firefox 88+
- Edge 90+
- Safari 14+

Requires JavaScript enabled for advance calculator functionality.

---

## Performance Notes

- No server-side caching implemented
- API calls happen on every page load
- For large datasets, consider:
  - Pagination
  - API response caching
  - AJAX loading

---

## Security Notes

- Session cookie is not HTTPS-only (development mode)
- No CSRF tokens implemented (for demo)
- Backend validates all inputs
- Frontend role checks are UI-only; backend enforces authorization

---

## Development Workflow

1. Make template changes → Refresh browser
2. Make CSS changes → Hard refresh (Ctrl+F5)
3. Make Python changes → Server auto-reloads (debug mode)
4. Database changes → Restart both servers

---

## Integration with Backend

Frontend expects backend running at `http://localhost:5001`. To change:

```python
# In frontend/app.py
BACKEND_URL = 'http://your-backend-url:5001/api'
```
