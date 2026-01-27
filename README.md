# neonatology_db

Neonatology — Medical data management system for neonatal care. Built with Django.

## Features

- **Newborn Registration**: Add newborns with basic information (name, date of birth, gender, mother PESEL).
- **Parameter Recording**: Record external measurements (weight, height, head circumference, breathing, oxygen saturation).
- **APGAR Scores**: Record APGAR scores at 1, 5, and 10 minutes.
- **Automated Verification**: Built-in logic to check parameters and provide medical recommendations.
- **Doctor Dashboard**: View all recorded newborns and their measurements.
- **User Authentication**: Login/logout for doctors.
- **Admin Interface**: Full Django admin to manage records.

## Quick Start (Windows CMD/PowerShell)

### Option A: Using .bat wrapper (recommended for Windows)

1. Create a superuser (admin account):
   ```cmd
   create-admin.bat --username myadmin --email admin@example.com --password MySecurePass123
   ```

2. Run migrations:
   ```cmd
   venv-cmd.bat migrate
   ```

3. Start the development server:
   ```cmd
   venv-cmd.bat runserver
   ```

4. Access the app:
   - Home: http://127.0.0.1:8000/
   - Admin: http://127.0.0.1:8000/admin/
   - Login with: username `myadmin`, password `MySecurePass123`

### Option B: Using PowerShell scripts

1. Activate the virtual environment:
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```
   If you get an execution policy error, run:
   ```powershell
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   .\.venv\Scripts\Activate.ps1
   ```

2. Create a superuser:
   ```powershell
   powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\create_superuser_noninteractive.ps1 --username myadmin --email admin@example.com --password MySecurePass123
   ```

3. Run migrations:
   ```powershell
   powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\migrate.ps1
   ```

4. Start the server:
   ```powershell
   powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\runserver.ps1
   ```

### Option C: Direct venv Python (most reliable)

1. Run a command with the venv Python directly:
   ```powershell
   C:\Users\User\Desktop\neonatology_db\.venv\Scripts\python.exe manage.py migrate
   C:\Users\User\Desktop\neonatology_db\.venv\Scripts\python.exe manage.py runserver
   ```

2. Create a superuser:
   ```powershell
   C:\Users\User\Desktop\neonatology_db\.venv\Scripts\python.exe scripts\create_superuser.py --username myadmin --email admin@example.com --password MySecurePass123
   ```

## Setup (Detailed)

1. Create a virtual environment (if not created):
   ```cmd
   python -m venv .venv
   ```

2. Install dependencies:
   ```cmd
   .venv\Scripts\pip.exe install --upgrade pip
   .venv\Scripts\pip.exe install -r requirements.txt
   ```

3. Verify Django is installed:
   ```cmd
   .venv\Scripts\python.exe -c "import django; print(django.get_version())"
   ```

## Project Structure

- `neonatology/` — Django app with models, views, forms, URLs, and admin.
- `neonatology_project/` — Django project settings.
- `scripts/` — Helper scripts (migrations, superuser creation).
- `templates/` — HTML templates for the web interface.
- `requirements.txt` — Python dependencies.

## Models

- **Dziecko (Baby)** — Name, date of birth, gender, mother's PESEL (unique identifier).
- **ParametryZewnetrzne (Parameters)** — Weight, height, head circumference, breathing, O2 saturation.
- **APGARScore** — APGAR scores at 1, 5, and 10 minutes.

## Usage

1. **Login**: Navigate to http://127.0.0.1:8000/login/ and log in with your superuser credentials.
2. **Add Newborn**: Click "Add New Newborn" and fill out the form.
3. **View Reports**: Click "Reports" to see all recorded newborns and their measurements.
4. **Admin**: Visit http://127.0.0.1:8000/admin/ to manage data directly.

## Notes

- The `sprawdz_parametry()` function checks parameters and provides medical recommendations.
- Doctor information is recorded automatically for each entry (assigned to logged-in user).
- All timestamps are recorded automatically.
- The system uses Django's built-in authentication system.

## Future Enhancements

- Export reports to PDF or Excel.
- More sophisticated APGAR and parameter validation rules.
- Graphs and statistics dashboard.
- Multi-language support.
- Integration with electronic health records (EHR).


