from fastapi import FastAPI, Request, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import subprocess
import os

app = FastAPI()

# IMPORTANT: Allow the frontend (port 7001) to talk to the backend (port 7002)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to http://localhost:7001
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.state.status = "Idle"

def run_script(prompt: str, query: str, table_name: str, topic: str, subtopic: str, rag_category: str, rag_userid: str):
    app.state.status = "Running background automation..."
    try:
        process = subprocess.Popen(
            [
                "python", "playwright_worker.py", 
                "--prompt", prompt, 
                "--query", query,
                "--table", table_name,
                "--topic", topic,
                "--subtopic", subtopic,
                "--rag_category", rag_category,
                "--rag_userid", rag_userid
            ],
            stderr=subprocess.PIPE,
            text=True
        )
        _, stderr = process.communicate()
        if process.returncode == 0:
            app.state.status = "Completed Successfully. Check automation_status_worker.log for details."
        else:
            app.state.status = f"Failed. Error: {stderr}"
    except Exception as e:
        app.state.status = f"Error starting process: {str(e)}"

@app.post("/start")
async def start_generation(
    background_tasks: BackgroundTasks,
    prompt: str = Form(...),
    query: str = Form(...),
    table_name: str = Form(...),
    topic: str = Form(...),
    subtopic: str = Form(...),
    rag_category: str = Form(...)
):
    rag_userid = "1559"
    if app.state.status == "Running background automation...":
        return JSONResponse({"message": "Already running! Please wait."})
    
    # CLEAR PREVIOUS LOGS
    if os.path.exists("automation_status_worker.log"):
        try:
            os.remove("automation_status_worker.log")
        except:
            pass

    app.state.status = "Starting..."
    background_tasks.add_task(run_script, prompt, query, table_name, topic, subtopic, rag_category, rag_userid)
    return JSONResponse({"message": "Batch Generation Started in Background!"})

@app.get("/categories")
async def get_categories():
    import urllib.request
    import json
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
    logs = ""
    if os.path.exists("automation_status_worker.log"):
        try:
            with open("automation_status_worker.log", "r", encoding="utf-8") as f:
                logs = "".join(f.readlines()[-15:])
        except:
            pass
    return {
        "status": app.state.status,
        "logs": logs
    }
