# 💬 ATM Chat Backend

Backend per l'assistente virtuale del simulatore ATM, sviluppato con **FastAPI** e **Google Gemini AI**.

## 🛠️ Tecnologie

- **Python 3.11+**
- **FastAPI** - Framework web async
- **Google Gemini AI** - LLM per chat
- **Uvicorn** - ASGI server
- **httpx** - Client HTTP async

## 📋 Prerequisiti

- Python 3.11+
- Account Google AI Studio (per API key Gemini)

## ⚙️ Configurazione

### 1. Virtual Environment

```bash
# Crea virtual environment
python -m venv venv

# Attiva (Windows)
.\venv\Scripts\Activate

# Attiva (Linux/Mac)
source venv/bin/activate

# Installa dipendenze
pip install -r requirements.txt
```

### 2. Google Gemini API Key

1. Vai su [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Crea una nuova API key
3. Copiala nel file `.env`

### 3. File .env

Crea un file `.env` nella root del progetto:

```env
# Ambiente
PRODUCTION=false

# Google Gemini API Key (obbligatoria)
GOOGLE_API_KEY=AIza...tua_api_key

# Server
PORT=8081
HOST=0.0.0.0
DEBUG=true

# Backend Java - URL e API Key
BE_URL=http://localhost:8080
BE_API_KEY=una-api-key-sicura

# CORS - origini permesse (comma-separated)
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

> ⚠️ **IMPORTANTE**: Il file `.env` contiene la tua API key e **NON deve essere committato** su Git. È già incluso nel `.gitignore`.

## 🚀 Avvio

### Sviluppo locale

```bash
# Attiva venv
.\venv\Scripts\Activate  # Windows
source venv/bin/activate  # Linux/Mac

# Avvia server
uvicorn main:app --host 0.0.0.0 --port 8081 --reload
```

L'applicazione sarà disponibile su: `http://localhost:8081`

Documentazione API interattiva: `http://localhost:8081/docs`

### Docker

```bash
# Build immagine
docker build -t atm-chat .

# Run container
docker run -p 8081:8081 --env-file .env atm-chat
```

## 📡 API Endpoints

| Metodo | Endpoint | Descrizione |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/api/chat` | Invia messaggio alla chat |
| `GET` | `/api/chat/history` | Cronologia chat sessione |
| `DELETE` | `/api/chat` | Cancella sessione chat |

### Esempio richiesta chat

```bash
curl -X POST http://localhost:8081/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Come faccio a sbloccare la mia carta?"}'
```

## 🤖 Funzionalità AI

L'assistente può:

- ✅ Rispondere a domande sul simulatore ATM
- ✅ Guidare l'utente nelle operazioni (deposito, prelievo)
- ✅ **Sbloccare carte bloccate** - L'utente dice "sblocca la carta 1111222233334444" e l'AI chiama il backend Java

### Sblocco Carta

Quando l'utente chiede di sbloccare una carta:

1. L'AI riconosce la richiesta
2. Genera un comando speciale `[UNLOCK_CARD:numero]`
3. Il backend intercetta il comando
4. Chiama `POST /api/internal/unlock-card` sul BE Java
5. Risponde all'utente con il risultato

## 🔐 Sicurezza

- **API Key** - Comunicazione sicura con BE Java tramite header `X-API-Key`
- **Cookie HttpOnly** - Sessioni chat protette
- **SameSite** - In produzione usa `none` + `secure` per cross-origin
- **CORS** - Configurabile via environment

## 📁 Struttura Progetto

```
BE.CHAT/
├── main.py              # FastAPI app e endpoints
├── gemini_service.py    # Integrazione Google Gemini
├── sessions.py          # Gestione sessioni chat
├── config.py            # System prompt e configurazione AI
├── requirements.txt     # Dipendenze Python
├── Dockerfile
├── .env.example         # Template environment
└── .gitignore
```

## 🧠 System Prompt

Il comportamento dell'AI è configurato in `config.py`. L'assistente:

- Parla italiano
- È conciso (max 2-3 frasi)
- Conosce i dati demo (carta: `1111222233334444`, PIN: `1234`)
- Può sbloccare carte bloccate

## 🌐 Deploy

### Render / Railway / Fly.io

1. Collega il repository GitHub
2. Configura le variabili d'ambiente nella dashboard
3. Il Dockerfile verrà usato automaticamente

### Variabili richieste in produzione

```
PRODUCTION=true
GOOGLE_API_KEY=tua_api_key_gemini
BE_URL=https://tuo-backend-java.render.com
BE_API_KEY=api-key-condivisa-con-be
CORS_ORIGINS=https://tuodominio.github.io
PORT=8081
DEBUG=false
```

## 📄 Licenza

MIT License

## 👤 Autore

Sviluppato come progetto portfolio - Simulatore ATM Full Stack
