from fastapi import APIRouter
from app.schemas.chat import ChatRequest, ChatResponse

router = APIRouter()

@router.post("/", response_model=ChatResponse)
async def chat(req: ChatRequest):
    # TODO: integrate agent + retriever here
    return ChatResponse(reply="This is a placeholder response.")
