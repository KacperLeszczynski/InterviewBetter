from fastapi import APIRouter
import uuid
from redis_client import r
import json

router = APIRouter(prefix="/interview", tags=["chat"])
SESSION_TTL = 60 * 30


@router.post("/start_session")
async def start_session():
    session_id = str(uuid.uuid4())
    r.setex(f"session:{session_id}", SESSION_TTL, json.dumps({
        "history": []
    }))
    return {"session_id": session_id}
