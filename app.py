from fastapi import FastAPI

app = FastAPI(title="Pi Agent Server", version="0.1.0")

@app.get("/health")
def health() -> dict:
    return {"status": "ok"}

@app.get("/agents")
def list_agents() -> dict:
    # Static for Phase 0; we’ll wire real agents later
    return {"agents": ["general", "code"]}