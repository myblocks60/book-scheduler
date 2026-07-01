from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, Response, JSONResponse, FileResponse
from fastapi.templating import Jinja2Templates
import urllib.request
import urllib.parse
import json
import os

app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.get("/localhost_settings.js")
async def get_localhost_settings():
    return FileResponse("templates/localhost_settings.js")

@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    return Response(content=b"", media_type="image/x-icon")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    try:
        return templates.TemplateResponse(request=request, name="index.html")
    except TypeError:
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

@app.get("/api/mcp/keys")
async def get_mcp_keys(userid: str, firmid: str):
    url = f"http://127.0.0.1:7901/api/mcp/keys?userid={urllib.parse.quote(userid)}&firmid={urllib.parse.quote(firmid)}"
    try:
        with urllib.request.urlopen(url) as response:
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