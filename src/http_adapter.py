# src/http_adapter.py
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from core.nlp_utils import parse_nlp
from core.command_generator import generate_command, list_supported_services
from core.validator import validate_command_safe
from core.telemetry import telemetry_log_event

app = FastAPI(title="MCP AWS CLI Adapter")

class GenerateRequest(BaseModel):
    query: str

@app.post("/generate")
async def generate(req: GenerateRequest):
    telemetry_log_event("http.request", {"path": "/generate", "query": req.query})
    intent, entities = parse_nlp(req.query)
    command, explanation = generate_command(intent, entities)
    validation = validate_command_safe(intent, entities)
    return {"command": command, "explanation": explanation, "validation": validation}

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/services")
async def services():
    return {"services": list_supported_services()}

def run_http_app(app: FastAPI, host: str="127.0.0.1", port: int=8000):
    uvicorn.run(app, host=host, port=port)
