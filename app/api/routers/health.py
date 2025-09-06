from fastapi import APIRouter

router = APIRouter(tags=["meta"])

@router.get("/health")
def health():
    return {"status": "ok"}
