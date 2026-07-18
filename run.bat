@echo off
echo Starting ArenaPulse-AI Server...

if not exist venv\ (
    echo Creating virtual environment...
    python -m venv venv
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Installing dependencies...
pip install -r requirements.txt

echo Launching FastAPI Application...
start http://localhost:8000/
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
