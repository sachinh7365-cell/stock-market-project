@echo off
REM Local development setup script for Windows

echo Setting up Stock Market Prediction application for local development...

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Create .env file if it doesn't exist
if not exist ".env" (
    echo Creating .env file from template...
    copy .env.example .env
    echo.
    echo WARNING: Please update .env with your MongoDB connection string and SECRET_KEY
    echo   Edit .env and set:
    echo   - MONGO_URI=your_mongodb_uri
    echo   - SECRET_KEY=your_secret_key
)

echo.
echo Setup complete! To start the development server:
echo   1. Update .env with your MongoDB URI and SECRET_KEY
echo   2. Run: python app.py
echo.
pause
