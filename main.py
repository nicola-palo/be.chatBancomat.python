"""
ATM Chat Backend - API con FastAPI e Google Gemini.
"""
import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Carica le variabili d'ambiente PRIMA di tutto
load_dotenv()

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn
import httpx
import re

from sessions import session_manager
from gemini_service import get_gemini_service


# Backend URL per chiamate API
BE_URL = os.getenv("BE_URL", "http://localhost:8080")
BE_API_KEY = os.getenv("BE_API_KEY", "atm-internal-secret-key-change-in-prod")

# Environment
IS_PRODUCTION = os.getenv("PRODUCTION", "false").lower() == "true"
ALLOWED_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173").split(",")


# --- Pydantic Models ---

class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str
    session_id: str


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None


# --- App Setup ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestisce startup e shutdown dell'app."""
    # Startup
    print("🚀 ATM Chat Backend starting...")
    try:
        # Verifica che Gemini sia configurato correttamente
        get_gemini_service()
        print("✅ Google Gemini configurato correttamente")
    except ValueError as e:
        print(f"⚠️  {e}")
        print("   Il server partirà ma le richieste chat falliranno finché non configuri la API key.")

    yield

    # Shutdown
    print("👋 ATM Chat Backend shutting down...")


app = FastAPI(
    title="ATM Chat Backend",
    description="Backend per la chat di assistenza con Google Gemini AI",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS - permetti richieste dal FE
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Endpoints ---

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "atm-chat-backend"}


async def process_card_unlock(card_number: str) -> str:
    """Chiama il BE per sbloccare una carta."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BE_URL}/api/internal/unlock-card",
                json={"cardNumber": card_number},
                headers={"X-API-Key": BE_API_KEY},
                timeout=10.0
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("message", "Operazione completata.")
            else:
                return f"Errore durante lo sblocco: {response.text}"
    except httpx.TimeoutException:
        return "Timeout: il server principale non risponde. Riprova più tardi."
    except httpx.ConnectError:
        return "Impossibile connettersi al server principale. Assicurati che sia in esecuzione."
    except Exception as e:
        return f"Errore imprevisto: {str(e)}"


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, req: Request, response: Response):
    """
    Invia un messaggio alla chat e ricevi la risposta dell'AI.
    La sessione è mantenuta tramite cookie.
    """
    # Recupera o crea sessione
    session_id = req.cookies.get("chat_session_id")
    session = session_manager.get_or_create_session(session_id)

    # Imposta il cookie della sessione
    # In produzione: secure=True e samesite="none" per cross-origin
    response.set_cookie(
        key="chat_session_id",
        value=session.id,
        httponly=True,
        samesite="none" if IS_PRODUCTION else "lax",
        secure=IS_PRODUCTION,
        max_age=1800,  # 30 minuti
    )

    # Valida il messaggio
    message = request.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Il messaggio non può essere vuoto")

    if len(message) > 1000:
        raise HTTPException(status_code=400, detail="Il messaggio è troppo lungo (max 1000 caratteri)")

    try:
        # Ottieni risposta da Gemini
        gemini = get_gemini_service()
        ai_response = await gemini.chat(session, message)

        # Controlla se l'AI vuole sbloccare una carta
        unlock_match = re.search(r'\[UNLOCK_CARD:(\d{16})\]', ai_response)
        if unlock_match:
            card_number = unlock_match.group(1)
            ai_response = await process_card_unlock(card_number)

        return ChatResponse(response=ai_response, session_id=session.id)

    except ValueError as e:
        # API key non configurata
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore nella generazione della risposta: {str(e)}")


@app.delete("/api/chat")
async def clear_chat(req: Request, response: Response):
    """Cancella la sessione di chat corrente."""
    session_id = req.cookies.get("chat_session_id")

    if session_id:
        session_manager.delete_session(session_id)

    # Rimuovi il cookie
    response.delete_cookie("chat_session_id")

    return {"status": "ok", "message": "Chat cancellata"}


@app.get("/api/chat/history")
async def get_history(req: Request):
    """Recupera la history della chat corrente."""
    session_id = req.cookies.get("chat_session_id")

    if not session_id:
        return {"messages": []}

    session = session_manager.get_session(session_id)
    if not session:
        return {"messages": []}

    messages = [
        {
            "role": msg.role,
            "content": msg.content,
            "timestamp": msg.timestamp.isoformat(),
        }
        for msg in session.messages
    ]

    return {"messages": messages, "session_id": session.id}


# --- Main ---

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8081))
    host = os.getenv("HOST", "0.0.0.0")
    debug = os.getenv("DEBUG", "true").lower() == "true"

    print(f"\n🏦 ATM Chat Backend")
    print(f"   URL: http://localhost:{port}")
    print(f"   Docs: http://localhost:{port}/docs")
    print()

    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=debug,
    )
