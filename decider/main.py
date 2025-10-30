import os
import uvicorn
from fastapi import FastAPI
from google.adk.cli.fast_api import get_fast_api_app

# Get the directory where main.py is located
AGENT_DIR = os.path.dirname(os.path.abspath(__file__))

# Session service URI - using in-memory for simplicity
# For production, consider using a database session service
SESSION_SERVICE_URI = os.getenv("DB_CONNECTION", "postgresql://testgen_user:testgen_pass@localhost:5432/testgen_db")

# Allowed origins for CORS
ALLOWED_ORIGINS = ["*"]

# Enable web interface for testing
SERVE_WEB_INTERFACE = True

# Create the FastAPI app
app: FastAPI = get_fast_api_app(
    agents_dir=AGENT_DIR,
    session_service_uri=SESSION_SERVICE_URI,
    allow_origins=ALLOWED_ORIGINS,
    web=SERVE_WEB_INTERFACE,
)

if __name__ == "__main__":
    # Use PORT environment variable provided by Cloud Run
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
