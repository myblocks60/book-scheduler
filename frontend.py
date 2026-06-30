from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, Response, JSONResponse
from fastapi.templating import Jinja2Templates
import urllib.request
import urllib.parse
import json
import os

app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    return Response(content=b"", media_type="image/x-icon")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/categories")
async def get_categories():
    url = "https://dev.myblocks.in:12095/api/rag/categories"
    data = json.dumps({"username": "1559", "userid": "1559"}).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as response:
            res_body = response.read()
            return JSONResponse(json.loads(res_body))
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)})

@app.get("/status")
async def get_status():
    try:
        with urllib.request.urlopen("http://127.0.0.1:7901/status") as response:
            res_body = response.read()
            return JSONResponse(json.loads(res_body))
    except Exception as e:
        return {"status": f"Backend Offline (Error: {str(e)})", "logs": ""}

@app.post("/start")
async def proxy_start(request: Request):
    # Proxy the form data to backend
    form_data = await request.form()
    data = urllib.parse.urlencode(form_data).encode('utf-8')
    req = urllib.request.Request("http://127.0.0.1:7901/start", data=data, headers={'Content-Type': 'application/x-www-form-urlencoded'})
    try:
        with urllib.request.urlopen(req) as response:
            res_body = response.read()
            return JSONResponse(json.loads(res_body))
    except Exception as e:
        return JSONResponse({"message": f"Failed to start: {str(e)}"})