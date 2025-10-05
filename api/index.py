from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
import json
import os
import numpy as np

# Initialize FastAPI app
app = FastAPI()

# Enable CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["GET", "POST"],  # Allow both GET and POST requests
    allow_headers=["*"],
)

# Request model for POST endpoint
class LatencyRequest(BaseModel):
    regions: List[str]
    threshold_ms: float

# Get the directory of the current file
current_dir = os.path.dirname(os.path.abspath(__file__))
# Load telemetry data from the parent directory
with open(os.path.join(os.path.dirname(current_dir), 'q-vercel-latency.json')) as f:
    telemetry_data = json.load(f)

@app.post("/api")
async def analyze_latency(request: LatencyRequest):
    """
    Analyze latency metrics for specified regions.
    Accepts: {"regions": [...], "threshold_ms": 180}
    Returns per-region metrics: avg_latency, p95_latency, avg_uptime, breaches
    """
    results = {}
    
    for region in request.regions:
        # Filter data for this region
        region_data = [record for record in telemetry_data if record["region"] == region]
        
        if not region_data:
            results[region] = {
                "avg_latency": None,
                "p95_latency": None,
                "avg_uptime": None,
                "breaches": 0
            }
            continue
        
        # Extract latency and uptime values
        latencies = [record["latency_ms"] for record in region_data]
        uptimes = [record["uptime_pct"] for record in region_data]
        
        # Calculate metrics
        avg_latency = sum(latencies) / len(latencies)
        p95_latency = np.percentile(latencies, 95)
        avg_uptime = sum(uptimes) / len(uptimes)
        breaches = sum(1 for latency in latencies if latency > request.threshold_ms)
        
        results[region] = {
            "avg_latency": round(avg_latency, 2),
            "p95_latency": round(p95_latency, 2),
            "avg_uptime": round(avg_uptime, 3),
            "breaches": breaches
        }
    
    return results

@app.get("/")
async def root():
    return {"message": "Latency Analysis API. POST to /api with {\"regions\": [...], \"threshold_ms\": 180} to get metrics."}

# This allows running the app with Uvicorn directly
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("index:app", host="0.0.0.0", port=8000, reload=True)