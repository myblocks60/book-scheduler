# Bulk Book Generation System - Developer Handover

This system automates the generation of 100-question career guidebooks using Playwright and uploads them to a RAG (Retrieval-Augmented Generation) server.

## 📁 Project Structure
- `frontend.py`: The FastAPI server for the UI (Port 7900).
- `backend.py`: The FastAPI server for the API and background task runner (Port 7901).
- `playwright_worker.py`: The core automation logic using Playwright.
- `templates/index.html`: The frontend dashboard with live logs.
- `C index book prompt.txt`: The master prompt template for the books.

## 🛠 Setup Instructions

### 1. Install Dependencies
Ensure you have Python 3.10+ installed, then run:
```bash
pip install fastapi uvicorn playwright jinja2 python-multipart mysql-connector-python pandas
playwright install chromium
```

### 2. Database Configuration
The system requires a MySQL table (default: `aia_job_roles`).
**Important:** You MUST add status columns to your table so the script can track progress:
```sql
ALTER TABLE aia_job_roles 
ADD COLUMN processed VARCHAR(20) DEFAULT 'NO', 
ADD COLUMN processed_date DATETIME;
```

Update your credentials in `playwright_worker.py` (Lines 34-39):
```python
DB_CONFIG = {
    'host': 'your_ip',
    'user': 'root',
    'password': 'your_password',
    'database': 'your_db'
}
```

### 3. Running the App
You must start both the frontend and backend in separate terminals:

**Terminal 1 (Backend):**
```bash
uvicorn backend:app --host 0.0.0.0 --port 7901 --reload
```

**Terminal 2 (Frontend):**
```bash
uvicorn frontend:app --host 0.0.0.0 --port 7900 --reload
```

### 4. Usage
- Open `http://localhost:7900` in your browser.
- Use the default SQL query: `SELECT job_role_id as id, role_name as career_name FROM aia_job_roles WHERE processed != 'YES' LIMIT 50`.
- The `{{career_name}}` placeholder in the prompt will be replaced automatically for every job role.

## ⚡ Troubleshooting
- **Timeouts**: For 100-question books, generation can take 5+ minutes. Timeouts in `playwright_worker.py` are already set to 7 minutes.
- **Logs**: Real-time logs are visible in the UI, or check `automation_status_worker.log` for full details.
