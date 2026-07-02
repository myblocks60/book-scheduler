from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, Response, JSONResponse, FileResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import urllib.request
import urllib.parse
import json
import os
import ssl

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Determine backend base URL and SSL context for local requests
hostname = os.socket.gethostname().upper() if hasattr(os, "socket") else ""
import socket
hostname = socket.gethostname().upper()
dev_keywords = ['MSI', 'I3ADMIN-PRECISION-TOWER-5810', 'DESKTOP-KAL0REJ']
is_local = any(kw in hostname for kw in dev_keywords)
production_domain = os.getenv("PRODUCTION_DOMAIN", "myblocks.in")
is_production = (production_domain.upper() in hostname) or not is_local

ssl_key_path = f"/etc/letsencrypt/live/{production_domain}/privkey.pem"
ssl_cert_path = f"/etc/letsencrypt/live/{production_domain}/fullchain.pem"
has_ssl = is_production and not is_local and os.path.exists(ssl_key_path) and os.path.exists(ssl_cert_path)

if has_ssl:
    BACKEND_URL_BASE = "https://127.0.0.1:7901"
    ssl_context = ssl._create_unverified_context()
else:
    BACKEND_URL_BASE = "http://127.0.0.1:7901"
    ssl_context = None


@app.get("/localhost_settings.js")
async def get_localhost_settings():
    return FileResponse("templates/localhost_settings.js")

@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    return Response(content=b"", media_type="image/x-icon")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    import socket
    hostname = socket.gethostname().upper()
    dev_keywords = ['MSI', 'I3ADMIN-PRECISION-TOWER-5810', 'DESKTOP-KAL0REJ']
    is_local = any(kw in hostname for kw in dev_keywords)
    production_domain = os.getenv("PRODUCTION_DOMAIN", "myblocks.in")
    is_production = (production_domain.upper() in hostname) or not is_local

    if is_production:
        userid = request.query_params.get("userid") or request.cookies.get("userid")
        firmid = request.query_params.get("firmid") or request.cookies.get("firmid")
        if not userid or not firmid:
            return RedirectResponse("https://myblocks.in/login")

    try:
        response = templates.TemplateResponse(request=request, name="index.html")
    except TypeError:
        response = templates.TemplateResponse("index.html", {"request": request})

    if is_production:
        query_userid = request.query_params.get("userid")
        query_firmid = request.query_params.get("firmid")
        if query_userid:
            response.set_cookie("userid", query_userid)
        if query_firmid:
            response.set_cookie("firmid", query_firmid)

    return response

@app.get("/categories")
def get_categories():
    url = "https://dev.myblocks.in:12095/api/rag/categories"
    data = json.dumps({"username": "1559", "userid": "1559"}).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            res_body = response.read()
            return JSONResponse(json.loads(res_body))
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)})

@app.get("/api/mcp/keys")
def get_mcp_keys(userid: str, firmid: str):
    url = f"{BACKEND_URL_BASE}/api/mcp/keys?userid={urllib.parse.quote(userid)}&firmid={urllib.parse.quote(firmid)}"
    try:
        with urllib.request.urlopen(url, context=ssl_context, timeout=10) as response:
            res_body = response.read()
            return JSONResponse(json.loads(res_body))
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)})

@app.get("/status")
def get_status(userid: str = "919", firmid: str = "5"):
    try:
        url = f"{BACKEND_URL_BASE}/status?userid={urllib.parse.quote(userid)}&firmid={urllib.parse.quote(firmid)}"
        with urllib.request.urlopen(url, context=ssl_context, timeout=10) as response:
            res_body = response.read()
            return JSONResponse(json.loads(res_body))
    except Exception as e:
        return {"status": f"Backend Offline (Error: {str(e)})", "logs": ""}

@app.post("/start")
async def proxy_start(request: Request):
    # Proxy the form data to backend
    form_data = await request.form()
    data = urllib.parse.urlencode(form_data).encode('utf-8')
    req = urllib.request.Request(f"{BACKEND_URL_BASE}/start", data=data, headers={'Content-Type': 'application/x-www-form-urlencoded'})
    try:
        with urllib.request.urlopen(req, context=ssl_context, timeout=10) as response:
            res_body = response.read()
            return JSONResponse(json.loads(res_body))
    except Exception as e:
        return JSONResponse({"message": f"Failed to start: {str(e)}"})

if __name__ == "__main__":
    def run_server(port: int, app_import_str: str):
        import socket
        import os
        import uvicorn
        
        hostname = socket.gethostname().upper()
        dev_keywords = ['MSI', 'I3ADMIN-PRECISION-TOWER-5810', 'DESKTOP-KAL0REJ']
        is_local = any(kw in hostname for kw in dev_keywords)
        
        production_domain = os.getenv("PRODUCTION_DOMAIN", "myblocks.in")
        is_production = (production_domain.upper() in hostname) or not is_local
        
        config = {
            "host": "0.0.0.0",
            "port": port
        }
        
        if is_production and not is_local:
            ssl_key_path = f"/etc/letsencrypt/live/{production_domain}/privkey.pem"
            ssl_cert_path = f"/etc/letsencrypt/live/{production_domain}/fullchain.pem"
            
            if os.path.exists(ssl_key_path) and os.path.exists(ssl_cert_path):
                print(f"[SSL] Enabled - Running in PRODUCTION mode with HTTPS")
                print(f"   Certificate: {ssl_cert_path}")
                print(f"   Private Key: {ssl_key_path}")
                config["ssl_keyfile"] = ssl_key_path
                config["ssl_certfile"] = ssl_cert_path
            else:
                print(f"[WARNING] SSL certificates not found at expected paths:")
                print(f"   Key: {ssl_key_path}")
                print(f"   Cert: {ssl_cert_path}")
                print(f"   Falling back to HTTP mode")
        else:
            print(f"[HTTP] Running in LOCAL/DEV mode with HTTP (no SSL)")
            
        uvicorn.run(app_import_str, **config)

    run_server(7900, "frontend:app")