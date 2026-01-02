"""
Servizio per comunicare con Google Gemini AI.
"""
import google.generativeai as genai
from typing import Optional
import os

from config import SYSTEM_PROMPT, MODEL_NAME, GENERATION_CONFIG
from sessions import ChatSession


class GeminiService:
    """Gestisce la comunicazione con Google Gemini."""

    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key or api_key == "your-api-key-here":
            raise ValueError(
                "GOOGLE_API_KEY non configurata. "
                "Ottieni una API key da https://makersuite.google.com/app/apikey "
                "e inseriscila nel file .env"
            )
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(
            model_name=MODEL_NAME,
            generation_config=GENERATION_CONFIG,
            system_instruction=SYSTEM_PROMPT,
        )

    async def chat(self, session: ChatSession, user_message: str) -> str:
        """
        Invia un messaggio e ottiene la risposta dall'AI.
        Mantiene il contesto della conversazione.
        """
        # Aggiungi il messaggio utente alla sessione
        session.add_message("user", user_message)

        try:
            # Prepara la history per Gemini (escludi ultimo messaggio, lo inviamo ora)
            history = session.get_history_for_gemini()[:-1]

            # Crea una chat con la history
            chat = self.model.start_chat(history=history)

            # Invia il messaggio
            response = chat.send_message(user_message)

            # Estrai la risposta
            assistant_response = response.text.strip()

            # Salva la risposta nella sessione
            session.add_message("assistant", assistant_response)

            return assistant_response

        except Exception as e:
            error_msg = f"Mi dispiace, si è verificato un errore: {str(e)}"
            session.add_message("assistant", error_msg)
            raise Exception(error_msg)


# Singleton del servizio (lazy init)
_gemini_service: Optional[GeminiService] = None


def get_gemini_service() -> GeminiService:
    global _gemini_service
    if _gemini_service is None:
        _gemini_service = GeminiService()
    return _gemini_service
