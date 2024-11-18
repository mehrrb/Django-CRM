# Django-CRM

A simple CRM system built with Django.

## Features
- Accounts Management
- Contacts Management
- Email Communications
- Team Management
- Invoice Generation
- Dashboard & Reports

## Installation

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Setup environment variables:
- Copy `.env.example` to `.env`
- Update the variables as needed

4. Run migrations:
```bash
python manage.py migrate
```

5. Create superuser:
```bash
python manage.py createsuperuser
```

6. Run the development server:
```bash
python manage.py runserver
```

Visit http://localhost:8000/

## License
MIT License - see LICENSE file for details
