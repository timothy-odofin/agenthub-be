from fastapi import FastAPI
from app.api.v1 import chat, health

app = FastAPI(title="Chatbot Backend")

# Routers
app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])
app.include_router(health.router, prefix="/api/v1/health", tags=["health"])

@app.get("/")
def root():
    return {"status": "ok", "message": "Chatbot backend is running 🚀"}
