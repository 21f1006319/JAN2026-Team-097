# Tools and Technologies

This document provides a comprehensive overview of all tools, technologies, libraries, and frameworks used in the Workforce & Payroll Management System project.

## Core Technologies

### Programming Language
- **Python 3.8+** - Primary programming language for both backend and frontend

### Web Framework
- **Flask 2.3.3** - Micro web framework for Python
  - Lightweight and flexible
  - Used for both backend API and frontend server
  - Jinja2 templating engine for HTML rendering

### Database
- **SQLite 3** - Embedded relational database
  - Zero configuration
  - Serverless, self-contained
  - Stored in `app_database.db` file

## Backend Dependencies

### Core Flask Extensions
| Package | Version | Purpose |
|---------|---------|---------|
| Flask | 2.3.3 | Web framework |
| Flask-Cors | 4.0.0 | Cross-Origin Resource Sharing (CORS) handling |

### HTTP & API
| Package | Version | Purpose |
|---------|---------|---------|
| requests | 2.31.0 | HTTP library for API communication between frontend and backend |

### Standard Library Modules
| Module | Purpose |
|--------|---------|
| `sqlite3` | Database connectivity and operations |
| `json` | JSON data serialization/deserialization |
| `datetime` | Date and time handling for payroll, attendance |
| `re` | Regular expressions for parameter extraction |
| `math` | Mathematical operations for TF-IDF calculations |
| `os` | Operating system interface for file paths |
| `random` | Random password generation |
| `hashlib` | Password hashing |
| `functools` | Higher-order functions (wraps, reduce) |

## Frontend Dependencies

### Core Framework
| Package | Version | Purpose |
|---------|---------|---------|
| Flask | 2.3.3 | Frontend server and templating |

### UI Libraries
| Library | Version | Purpose |
|---------|---------|---------|
| Bootstrap 5.3.0 | CSS Framework | Responsive grid system, components |
| Font Awesome 6.4.0 | Icon Library | Icons for UI elements |

### JavaScript
- **Vanilla JavaScript** - No external JS frameworks
- **Bootstrap JS 5.3.0** - For interactive components (modals, dropdowns)

## AI / NLP Technologies

### Vector Search Implementation
Custom implementation using:

| Component | Technology | Purpose |
|-----------|------------|---------|
| Tokenization | Python `re` + custom logic | Text preprocessing |
| TF (Term Frequency) | Custom algorithm | Word frequency calculation |
| IDF (Inverse Document Frequency) | Custom algorithm | Document importance weighting |
| Cosine Similarity | Mathematical formula | Vector similarity measurement |
| Multi-strategy Matching | Custom algorithm | Enhanced query matching |

### Matching Strategies
1. **Keyword Overlap** - Direct token matching
2. **Template Matching** - Compare against prompt variations
3. **Phrase Containment** - Substring matching
4. **TF-IDF Similarity** - Statistical vector comparison

## Development Tools

### Version Control
- **Git** - Distributed version control system
- **GitHub** - Remote repository hosting

### IDE / Editors
- Any Python-compatible IDE (VS Code, PyCharm, etc.)

### Package Management
- **pip** - Python package installer
- **requirements.txt** - Dependency specification files

### Browser Tools
- Modern web browsers (Chrome, Firefox, Safari)
- Developer tools for debugging

## Project Structure Tools

### Directory Organization
```
JAN2026-Team-097/
├── backend/          # API server (Port 5001)
├── frontend/         # UI server (Port 5000)
├── documentation/    # Project documentation
└── README.md         # Main project readme
```

## External Services

### CDNs (Content Delivery Networks)
- **jsDelivr** - Bootstrap CSS/JS delivery
- **cdnjs** - Font Awesome icon delivery

## Security Tools

### Authentication
- **Flask Sessions** - Server-side session management
- **Password Hashing** - SHA-256 with salt

### CORS
- **Flask-Cors** - Handles cross-origin requests between frontend and backend

## Math & Statistics

### Algorithms Implemented
- **TF-IDF Vectorization** - For text similarity
- **Cosine Similarity** - For vector comparison
- **Cosine Similarity Formula**: 
  ```
  similarity = (A · B) / (||A|| × ||B||)
  ```

## Data Processing

### Parameter Extraction
- **Regex Patterns**:
  - Month/Year: `r'(\d{1,2})\s*/\s*(\d{4})'`
  - Month Names: `r'(?:january|jan|february|feb|...)'`
  - Amount: `r'(?:\$|₹|Rs\.?\s*)?(\d+(?:,\d{3})*(?:\.\d{2})?)'`

### Tokenization
- Lowercase conversion
- Non-alphanumeric character removal
- Stop word filtering (basic)

## Testing & Debugging

### Debug Mode
- Flask Debug Mode enabled (`debug=True`)
- Auto-reload on code changes
- Detailed error pages

### Logging
- Console output for server status
- Print statements for debugging

## Browser Compatibility

### Supported Browsers
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

### Responsive Breakpoints
- Desktop: > 992px
- Tablet: 768px - 992px
- Mobile: < 768px

## Installation Requirements

### System Requirements
- **OS**: macOS, Linux, or Windows
- **RAM**: 4GB minimum
- **Storage**: 1GB free space
- **Python**: 3.8 or higher

### Python Packages (Backend)
```
Flask==2.3.3
Flask-Cors==4.0.0
requests==2.31.0
```

### Python Packages (Frontend)
```
Flask==2.3.3
```

## Technology Stack Summary

| Layer | Technology |
|-------|------------|
| Language | Python 3.8+ |
| Backend Framework | Flask |
| Frontend Framework | Flask + Jinja2 |
| CSS Framework | Bootstrap 5 |
| Icons | Font Awesome 6 |
| Database | SQLite 3 |
| AI/NLP | Custom TF-IDF |
| HTTP Client | requests |
| Version Control | Git |

## Key Technical Decisions

### Why Flask?
- Lightweight and easy to learn
- Sufficient for project scope
- Single language (Python) for full stack

### Why SQLite?
- No separate database server needed
- Easy setup and deployment
- Suitable for single-instance applications

### Why Custom TF-IDF?
- No external ML libraries required
- Fast and lightweight
- Easy to customize matching logic
- No model training needed

### Why Separate Frontend/Backend?
- Clean separation of concerns
- API can be consumed by other clients
- Easier to scale/maintain
