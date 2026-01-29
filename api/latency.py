from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import json
import statistics
from pathlib import Path

app = FastAPI()

# Enable CORS for POST from anywhere
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST"],
    allow_headers=["*"],
)

DATA_FILE = Path(__file__).parent.parent / "q-vercel-latency.json"

@app.post("/api/latency")
async def latency(req: Request):
    body = await req.json()
    regions = body["regions"]
    threshold = body["threshold_ms"]

    with open(DATA_FILE) as f:
        data = json.load(f)

    result = {}

    for region in regions:
        records = [r for r in data if r["region"] == region]

        latencies = [r["latency_ms"] for r in records]
        uptimes = [r["uptime_pct"] for r in records]

        result[region] = {
            "avg_latency": round(statistics.mean(latencies), 2),
            "p95_latency": round(statistics.quantiles(latencies, n=20)[18], 2),
            "avg_uptime": round(statistics.mean(uptimes), 2),
            "breaches": sum(1 for l in latencies if l > threshold)
        }

    return result
