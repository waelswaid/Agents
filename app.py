from fastapi import FastAPI

#creates an instance called app
app = FastAPI(title="Pi Agent Server", version="0.1.0")

# When an HTTP GET request comes in at the path /health, run the function below
@app.get("/health")
def health() -> dict:
    return {"status": "ok"}

@app.get("/agents")
def list_agents() -> dict:
    # Static for Phase 0; we’ll wire real agents later
    return {"agents": ["general", "code"]}