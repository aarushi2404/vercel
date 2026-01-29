# api/index.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import numpy as np
from typing import List, Dict
import os

# Path to telemetry file (same folder as this file)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "../q-vercel-latency.json")

with open(DATA_PATH, "r") as f:
    TELEMETRY = json.load(f)

app = FastAPI()

# Allow CORS from any origin for POST
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # allow all origins
    allow_credentials=True,
    allow_methods=["POST"],       # only POST is needed
    allow_headers=["*"],
)

class LatencyRequest(BaseModel):
    regions: List[str]
    threshold_ms: int

def compute_region_metrics(region: str, threshold_ms: int) -> Dict:
    # Filter telemetry for this region
    rows = [row for row in TELEMETRY if row.get("region") == region]

    if not rows:
        # If no data for this region, return zeros
        return {
            "region": region,
            "avg_latency": 0,
            "p95_latency": 0,
            "avg_uptime": 0,
            "breaches": 0,
        }

    latencies = [row.get("latency_ms", 0) for row in rows]
    uptimes = [row.get("uptime", 0) for row in rows]

    # avg latency
    avg_latency = float(np.mean(latencies))

    # 95th percentile latency
    p95_latency = float(np.percentile(latencies, 95))

    # avg uptime
    avg_uptime = float(np.mean(uptimes))

    # breaches: latency above threshold
    breaches = sum(1 for v in latencies if v > threshold_ms)

    return {
        "region": region,
        "avg_latency": avg_latency,
        "p95_latency": p95_latency,
        "avg_uptime": avg_uptime,
        "breaches": breaches,
    }
@app.post("/analytics")
def analytics(request: LatencyRequest):
    regions = request.regions
    threshold = request.threshold_ms

    results = []
    for r in regions:
        metrics = compute_region_metrics(r, threshold)
        results.append(metrics)

    # You can choose the exact response shape; simplest:
    return {"regions": results}

