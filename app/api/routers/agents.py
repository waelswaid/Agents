from fastapi import APIRouter

router = APIRouter(tags=["agents"])

@router.get("/agents")
def list_agents() -> dict:
    # Single built-in agent for now; easy to extend later
    return {"agents": ["general"]}
