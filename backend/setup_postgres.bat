@echo off
REM Quick Start Script for PostgreSQL + RBAC Setup (Windows)

echo ==================================================
echo SupaQuery PostgreSQL + RBAC Quick Setup
echo ==================================================
echo.

REM Check if PostgreSQL is installed
where psql >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] PostgreSQL not found
    echo Please install PostgreSQL from: https://www.postgresql.org/download/windows/
    echo After installation, add PostgreSQL bin directory to PATH
    pause
    exit /b 1
)
echo [OK] PostgreSQL found

REM Check if Python is installed
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python not found
    echo Please install Python from: https://www.python.org/downloads/
    pause
    exit /b 1
)
echo [OK] Python found

REM Create database
echo.
echo Creating database...
psql -U postgres -c "CREATE DATABASE supaquery;" 2>nul
if %errorlevel% equ 0 (
    echo [OK] Database created
) else (
    echo [WARNING] Database might already exist
)

REM Install Python dependencies
echo.
echo Installing Python dependencies...
python -m pip install psycopg2-binary asyncpg sqlalchemy alembic python-jose[cryptography] passlib[bcrypt]
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)
echo [OK] Dependencies installed

REM Configure environment
echo.
if exist .env (
    echo [WARNING] .env file already exists
    set /p overwrite="Overwrite? (y/N): "
    if /i "%overwrite%"=="y" (
        copy /y .env.example .env >nul
        echo [OK] .env file updated
    )
) else (
    copy .env.example .env >nul
    echo [OK] Created .env file
)

REM Generate SECRET_KEY (simple version for Windows)
echo.
echo Generating SECRET_KEY...
echo Please generate a secure random key and add it to .env manually:
echo   SECRET_KEY=your-secret-key-here
echo.
echo You can generate one online at: https://randomkeygen.com/
echo Or use Python:
echo   python -c "import secrets; print(secrets.token_hex(32))"
echo.
pause

REM Initialize database
echo.
echo ==================================================
echo Database Initialization
echo ==================================================
echo This will create tables, roles, and admin user
echo.
set /p init="Initialize database now? (Y/n): "
if /i not "%init%"=="n" (
    python init_db.py
)

REM Backup old main.py if exists
echo.
if exist main.py (
    echo Backing up existing main.py...
    copy /y main.py main_sqlite.py.bak >nul
    echo [OK] Backed up to main_sqlite.py.bak
)

REM Replace main.py
if exist main_postgres.py (
    echo Activating PostgreSQL version...
    copy /y main_postgres.py main.py >nul
    echo [OK] main.py updated with PostgreSQL version
)

echo.
echo ==================================================
echo Setup Complete!
echo ==================================================
echo.
echo Next steps:
echo 1. Edit .env and set SECRET_KEY to a secure random value
echo 2. Start the server: python main.py
echo 3. Test registration with curl or Postman
echo.
echo Documentation:
echo   - POSTGRES_SETUP.md - Setup guide
echo   - MIGRATION_GUIDE.md - Migration instructions
echo   - IMPLEMENTATION_SUMMARY.md - Features overview
echo.
echo To rollback to SQLite: copy main_sqlite.py.bak main.py
echo.
pause
