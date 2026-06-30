uvicorn backend:app --host 0.0.0.0 --port 7901 --reload
uvicorn frontend:app --host 0.0.0.0 --port 7900 --reload



sudo journalctl -u book-backend -f

journalctl -u book-frontend -n 100 --no-pager