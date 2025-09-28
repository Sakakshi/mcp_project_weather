# server.py - FastAPI MCP-style server
import json
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import httpx
import os

# Config
PORT = int(os.environ.get("PORT", 4200))
MANIFEST_PATH = "tool_manifest.json"

# Create app
app = FastAPI(title="mcp-python-mini")

# Load manifest at startup
@app.on_event("startup")
async def load_manifest():
    if not os.path.exists(MANIFEST_PATH):
        raise RuntimeError(f"Manifest file not found: {MANIFEST_PATH}")
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        app.state.manifest = json.load(f)

# Root endpoint
@app.get("/")
async def root():
    return {"status": "Server running", "manifest": "/.well-known/mcp-manifest"}

# Manifest endpoint
@app.get("/.well-known/mcp-manifest")
async def manifest():
    return JSONResponse(content=app.state.manifest)

# Main tool handler
@app.post("/call")
async def call_tool(request: Request):
    body: Dict[str, Any] = await request.json()
    tool: Optional[str] = body.get("tool")
    args: Dict[str, Any] = body.get("args", {})

    if not tool:
        raise HTTPException(status_code=400, detail="Missing 'tool' in request body")

    try:
        # Tool: get current UTC date/time
        if tool == "get_datetime":
            now = datetime.utcnow()
            return {"ok": True, "result": {
                "iso_utc": now.isoformat() + "Z",
                "human_utc": now.strftime("%Y-%m-%d %H:%M:%S (UTC)")
            }}

        # Tool: simple ping
        if tool == "ping":
            return {"ok": True, "result": "pong"}

        # Tool: fetch weather
        if tool == "get_weather":
            loc = args.get("location")
            lat = args.get("lat")
            lon = args.get("lon")

            if loc:
                query = loc
            elif lat is not None and lon is not None:
                query = f"{lat},{lon}"
            else:
                query = "auto"

            url = f"https://wttr.in/{httpx.utils.requote_uri(query)}?format=j1"
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                data = resp.json()

            current = (data.get("current_condition") or [{}])[0]
            return {"ok": True, "result": {
                "location": query,
                "temp_C": current.get("temp_C"),
                "feels_like_C": current.get("FeelsLikeC"),
                "desc": (current.get("weatherDesc") or [{}])[0].get("value")
            }}

        # Unknown tool
        return {"ok": False, "error": f"Unknown tool '{tool}'"}

    except httpx.HTTPError as e:
        return {"ok": False, "error": f"HTTP error: {str(e)}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

# Entry point if running directly
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=PORT, reload=True)
