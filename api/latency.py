from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
import json
import statistics
from pathlib import Path

app = FastAPI()

# ✅ CORS (checker-safe)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],   # includes OPTIONS
    allow_headers=["*"],
)

DATA_FILE = Path(__file__).parent.parent / "q-vercel-latency.json"

# ✅ Explicit OPTIONS handler (CRITICAL for Vercel)
@app.options("/")
async def options_handler():
    return Response(status_code=200)

# ✅ POST handler (route is /api/latency automatically)
@app.post("/")
async def latency(request: Request):
    body = await request.json()
    regions = body["regions"]
    threshold = body["threshold_ms"]

    with open(DATA_FILE, "r") as f:
        data = json.load(f)

    response = {}

    for region in regions:
        records = [r for r in data if r["region"] == region]

        latencies = [r["latency_ms"] for r in records]
        uptimes = [r["uptime_pct"] for r in records]

        response[region] = {
            "avg_latency": round(statistics.mean(latencies), 2),
            "p95_latency": round(statistics.quantiles(latencies, n=20)[18], 2),
            "avg_uptime": round(statistics.mean(uptimes), 2),
            "breaches": sum(1 for l in latencies if l > threshold),
        }

    return response


